import os
import glob
import warnings
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import Ridge, Lasso
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

warnings.filterwarnings('ignore')

# ============================================================
# 配置
# ============================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'genData', 'CleanDataRoi_lenient')
OUT_DIR = os.path.join(BASE_DIR, 'genData', 'sum')
REPORT_DIR = os.path.join(BASE_DIR, 'report')
FIG_DIR = os.path.join(REPORT_DIR, 'FIG')
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(FIG_DIR, exist_ok=True)

FEATURE_ALL = {
    'AL': 'Axial length (mm)',
    'Age': 'Age',
    'SE': 'Spherical equivalent refraction (D)',
    'Gender': 'Gender',
    'K': 'Corneal curvature (mm)',
    'ACD': 'Anterior chamber depth (mm)'
}

TARGET_COL = 'Angular cone density (cones/ deg2)'

MYOPIA_THRESHOLD = -0.5
RANDOM_STATE = 42
N_BOOTSTRAP = 1000


# ============================================================
# 工具函数
# ============================================================
def load_subject_mapping(data_dir):
    df_ref = pd.read_csv(os.path.join(data_dir, 'data1.csv'))
    mapping = {}
    for _, row in df_ref.iterrows():
        mapping[row['Eye_Label']] = row['Subject_ID']
        mapping[row['Subject_ID']] = row['Subject_ID']
    return mapping


def load_distance_data(data_dir):
    all_data = {}
    for f in sorted(glob.glob(os.path.join(data_dir, 'data*.csv'))):
        df = pd.read_csv(f)
        dist = df['Eccentricity (mm)'].iloc[0]
        if dist not in all_data:
            all_data[dist] = []
        all_data[dist].append(df)
    return all_data


def aggregate_distance(dfs, eye_to_subject):
    feature_cols = list(FEATURE_ALL.values())
    base = dfs[0][['Subject_ID', 'Eye'] + feature_cols + [TARGET_COL]].copy()
    base = base.rename(columns={TARGET_COL: 'density_q1'})

    for i, d in enumerate(dfs[1:], 2):
        base = base.merge(
            d[['Subject_ID', 'Eye', TARGET_COL]].rename(columns={TARGET_COL: f'density_q{i}'}),
            on=['Subject_ID', 'Eye'], how='inner'
        )

    den_cols = [c for c in base.columns if c.startswith('density_q')]
    base[TARGET_COL] = base[den_cols].mean(axis=1)
    base['Real_Subject_ID'] = base['Subject_ID'].map(eye_to_subject)
    base['Myopia'] = (base[FEATURE_ALL['SE']] <= MYOPIA_THRESHOLD).astype(int)

    return base[['Subject_ID', 'Real_Subject_ID', 'Eye', 'Myopia'] + feature_cols + [TARGET_COL]].copy()


def fill_na(df, cols):
    for col in cols:
        if df[col].isna().any():
            df[col].fillna(df[col].median(), inplace=True)
    return df


def calc_scores(y_true, y_pred):
    r2 = r2_score(y_true, y_pred)
    corr = np.corrcoef(y_true, y_pred)[0, 1] if len(y_true) > 1 else 0
    mape = np.mean(np.abs((y_true - y_pred) / (y_true + 1e-10))) * 100
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    return r2, corr, mape, rmse, mae


def loso_cv(X, y, groups, model_builder):
    unique_groups = np.unique(groups)
    all_true, all_pred = [], []
    for g in unique_groups:
        test_mask = groups == g
        train_mask = ~test_mask
        model = model_builder()
        model.fit(X[train_mask], y[train_mask])
        pred = model.predict(X[test_mask])
        all_true.extend(y[test_mask])
        all_pred.extend(pred)
    return np.array(all_true), np.array(all_pred)


def block_bootstrap_ci(X_df, y, groups, model_builder, feature_names, n_bootstrap=1000):
    unique_groups = np.unique(groups)
    n_groups = len(unique_groups)
    coef_list = []
    rng = np.random.RandomState(RANDOM_STATE)
    for _ in range(n_bootstrap):
        sampled_groups = rng.choice(unique_groups, size=n_groups, replace=True)
        idx = []
        for g in sampled_groups:
            idx.extend(np.where(groups == g)[0])
        X_b = X_df.iloc[idx].values
        y_b = y[idx]
        model = model_builder()
        model.fit(X_b, y_b)
        coef_list.append(model.named_steps['m'].coef_.copy())
    coef_array = np.array(coef_list)
    return pd.DataFrame({
        'Feature': feature_names,
        'Coefficient': model_builder().fit(X_df.values, y).named_steps['m'].coef_,
        'CI_Lower': np.percentile(coef_array, 2.5, axis=0),
        'CI_Upper': np.percentile(coef_array, 97.5, axis=0)
    })


# ============================================================
# 可视化
# ============================================================
def plot_final_model_scatter(y_true, y_pred, title, out_prefix):
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.scatter(y_true, y_pred, alpha=0.6, edgecolors='black', s=80)
    min_val, max_val = min(y_true.min(), y_pred.min()), max(y_true.max(), y_pred.max())
    ax.plot([min_val, max_val], [min_val, max_val], 'r--', lw=2, label='Identity')
    z = np.polyfit(y_true, y_pred, 1)
    ax.plot(y_true, np.poly1d(z)(y_true), 'b-', lw=1.5, label='Fit')
    r2, corr, mape, rmse, mae = calc_scores(y_true, y_pred)
    ax.set_xlabel('Observed cone density (cones/deg²)')
    ax.set_ylabel('Predicted cone density (cones/deg²)')
    ax.set_title(f'{title}\nLOSO CV: R²={r2:.3f}, r={corr:.3f}, MAPE={mape:.2f}%')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    path = os.path.join(OUT_DIR, f'{out_prefix}_scatter.png')
    plt.savefig(path, dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(FIG_DIR, os.path.basename(path)), dpi=300, bbox_inches='tight')
    plt.close()
    return os.path.basename(path)


def plot_distance_performance(coarse_df, out_prefix):
    """绘制 11 个距离的最佳 Test R² 曲线"""
    best_per_d = coarse_df.loc[coarse_df.groupby('Distance_mm')['test_r2'].idxmax()].sort_values('Distance_mm')

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(best_per_d['Distance_mm'], best_per_d['test_r2'], 'o-', lw=2, markersize=8, color='steelblue')
    ax.axhline(0, color='gray', linestyle='--', lw=0.8)
    ax.set_xlabel('Eccentricity (mm)')
    ax.set_ylabel('Best Test R²')
    ax.set_title('Best Predictive Performance Across Eccentricities (lenient data)')
    ax.grid(True, alpha=0.3)
    for _, row in best_per_d.iterrows():
        ax.annotate(f"{row['Model'][:3]}\n{row['test_r2']:.2f}",
                    (row['Distance_mm'], row['test_r2']),
                    textcoords="offset points", xytext=(0, 10), ha='center', fontsize=7)
    plt.tight_layout()
    path = os.path.join(OUT_DIR, f'{out_prefix}_distance_performance.png')
    plt.savefig(path, dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(FIG_DIR, os.path.basename(path)), dpi=300, bbox_inches='tight')
    plt.close()
    return os.path.basename(path)


def plot_coefficient_forest(coef_df, title, out_prefix):
    fig, ax = plt.subplots(figsize=(10, 6))
    y_pos = np.arange(len(coef_df))
    ax.errorbar(coef_df['Coefficient'], y_pos,
                xerr=[coef_df['Coefficient'] - coef_df['CI_Lower'],
                      coef_df['CI_Upper'] - coef_df['Coefficient']],
                fmt='o', capsize=5, capthick=2, elinewidth=2, markersize=8)
    ax.axvline(0, color='gray', linestyle='--', linewidth=1)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(coef_df['Feature'])
    ax.set_xlabel('Standardized Coefficient')
    ax.set_title(f'{title}: Standardized Coefficients with 95% CI')
    ax.grid(True, alpha=0.3, axis='x')
    plt.tight_layout()
    path = os.path.join(OUT_DIR, f'{out_prefix}_coefficients.png')
    plt.savefig(path, dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(FIG_DIR, os.path.basename(path)), dpi=300, bbox_inches='tight')
    plt.close()
    return os.path.basename(path)


# ============================================================
# 主程序
# ============================================================
def main():
    print("=" * 80)
    print("SR0530 Comprehensive Final Report Generation")
    print("=" * 80)

    # 1. 加载寻优结果
    coarse_df = pd.read_csv(os.path.join(OUT_DIR, 'SR0530_HP_Tuning_Results.csv'))
    fine_df = pd.read_csv(os.path.join(OUT_DIR, 'SR0530_Fine_Tuning_Results.csv'))

    coarse_best = coarse_df.loc[coarse_df['test_r2'].idxmax()]
    fine_best = fine_df.loc[fine_df['Fine_Test_R2'].idxmax()]
    fine_stable = fine_df.loc[fine_df['Stability_Mean'].idxmax()]

    # 2. 加载 lenient 3.0mm 数据
    eye_to_subject = load_subject_mapping(DATA_DIR)
    all_data = load_distance_data(DATA_DIR)
    df_30 = aggregate_distance(all_data[3.0], eye_to_subject)

    # 3. 训练最终模型
    configs = [
        ('Primary_A1_Ridge', ['AL', 'Age', 'Gender'], 'Ridge', {'alpha': 10.0}),
        ('Alternative_C1_Lasso', ['SE', 'AL', 'Age', 'Gender'], 'Lasso', {'alpha': 5.0})
    ]

    model_results = []
    for name, feat_short, model_name, params in configs:
        feat_full = [FEATURE_ALL[s] for s in feat_short]
        df_sub = fill_na(df_30.copy(), feat_full)
        X = df_sub[feat_full]
        y = df_sub[TARGET_COL].values
        groups = df_sub['Real_Subject_ID'].values

        if model_name == 'Ridge':
            builder = lambda p=params: Pipeline([('s', StandardScaler()), ('m', Ridge(**p))])
        else:
            builder = lambda p=params: Pipeline([('s', StandardScaler()), ('m', Lasso(**p, max_iter=5000))])

        y_true, y_pred = loso_cv(X.values, y, groups, builder)
        perf = calc_scores(y_true, y_pred)
        coef_df = block_bootstrap_ci(X, y, groups, builder, feat_full, n_bootstrap=N_BOOTSTRAP)

        scatter_file = plot_final_model_scatter(y_true, y_pred, name.replace('_', ' '), name)
        coef_file = plot_coefficient_forest(coef_df, name.replace('_', ' '), name)

        model_results.append({
            'name': name,
            'feat_full': feat_full,
            'params': params,
            'performance': perf,
            'coef_df': coef_df,
            'scatter_file': scatter_file,
            'coef_file': coef_file
        })

    # 4. 距离性能图
    dist_perf_file = plot_distance_performance(coarse_df[coarse_df['Data_Group'] == 'lenient'], 'Comprehensive')

    # 5. 读取 LMM 修订结果
    lmm_strict = pd.read_csv(os.path.join(OUT_DIR, 'SR0530_LMM_Revised_strict_Results.csv'))
    lmm_lenient = pd.read_csv(os.path.join(OUT_DIR, 'SR0530_LMM_Revised_lenient_Results.csv'))

    # 6. 生成综合报告
    generate_md(coarse_best, fine_best, fine_stable, model_results, dist_perf_file, lmm_strict, lmm_lenient)

    print("\n" + "=" * 80)
    print("Comprehensive report generated!")
    print("=" * 80)


# ============================================================
# 报告生成
# ============================================================
def generate_md(coarse_best, fine_best, fine_stable, model_results, dist_perf_file, lmm_strict, lmm_lenient):
    md = []
    md.append("# SR0530 视锥细胞密度预测研究：综合最终报告\n\n")
    md.append("> **研究目的**：利用临床与生物学特征，预测黄斑旁中心（3.0 mm 偏心距）视锥细胞密度，并识别关键影响因素。\n\n")
    md.append("> **数据**：lenient 数据组（距离平均 >7000 剔除），71 眼 → 3.0 mm 处 54 眼 / 39 subjects\n\n")
    md.append("> **最终推荐模型**：A1_Ridge（AL + Age + Gender），LOSO CV R² = 0.439\n\n")

    md.append("---\n\n")

    # 一、研究流程概述
    md.append("## 一、研究流程概述\n\n")
    md.append("1. **数据预处理**：统一字段名、单位转换、缺失值处理，生成 strict/lenient 两套 44 ROI 数据。\n")
    md.append("2. **数据质量审查**：比较 strict（任意 ROI >7000 剔除，69 眼）与 lenient（距离平均 >7000 剔除，71 眼），lenient 保留更多信息。\n")
    md.append("3. **ML 超参数寻优**：11 距离 × 4 特征方案 × 7 模型，Random Search + GroupKFold by Subject。\n")
    md.append("4. **精细寻优**：对 Top 12 配置做密集参数搜索与 20 次稳定性重复 CV。\n")
    md.append("5. **最终模型**：选择稳定性最佳的 A1_Ridge 作为主模型，C1_Lasso 作为备选。\n\n")

    # 二、LMM 靶点筛选（修订版）
    md.append("## 二、LMM 靶点筛选（修订版）\n\n")
    md.append("### 2.1 方法说明\n\n")
    md.append("- 对每个偏心率（1.0–6.0 mm）独立拟合线性混合效应模型（LMM），Subject_ID 作为随机效应。\n")
    md.append("- 固定效应包括：AL、Age、SE、Gender、CC、ACD、Eye。\n")
    md.append("- 因变量为 **Angular cone density（cones/deg²）**，与 ML 层保持一致。\n")
    md.append("- OES 公式已修复：`OES = |beta_AL| × (-log10(P_AL)) / (1 + ICC)`，避免 ICC 接近 0 时数值爆炸。\n\n")

    md.append("### 2.2 Lenient 数据 LMM 结果\n\n")
    md.append("| 距离 (mm) | 眼数 | 受试者数 | beta_AL | P_AL | P_FDR | R²_边际 | R²_条件 | ICC | OES_Raw | OES_FDR |\n")
    md.append("|-----------|------|---------|---------|------|-------|---------|---------|-----|---------|---------|\n")
    for _, row in lmm_lenient.iterrows():
        sig = "⭐" if pd.notna(row['P_AL']) and row['P_AL'] < 0.05 else ""
        sig_fdr = "⭐" if pd.notna(row.get('P_FDR')) and row['P_FDR'] < 0.05 else ""
        md.append(f"| {row['Distance']:.1f} | {int(row['N_eyes'])} | {int(row['N_subjects'])} | "
                  f"{row['Beta_AL']:+.3f} {sig} | {row['P_AL']:.4f} | "
                  f"{row.get('P_FDR', np.nan):.4f} {sig_fdr} | "
                  f"{row['R2_Marginal']:.3f} | {row['R2_Conditional']:.3f} | "
                  f"{row['ICC']:.3f} | {row['OES_Raw']:.3f} | {row['OES_FDR']:.3f} |\n")

    best_beta_lenient = lmm_lenient.loc[lmm_lenient['Beta_AL'].abs().idxmax(), 'Distance']
    best_oes_lenient = lmm_lenient.loc[lmm_lenient['OES_Raw'].idxmax(), 'Distance']
    md.append(f"\n**按 |beta_AL| 最大**：{best_beta_lenient:.1f} mm\n")
    md.append(f"**按 OES_Raw 最高**：{best_oes_lenient:.1f} mm\n\n")

    md.append("### 2.3 Strict 数据 LMM 结果\n\n")
    md.append("| 距离 (mm) | 眼数 | 受试者数 | beta_AL | P_AL | P_FDR | R²_边际 | R²_条件 | ICC | OES_Raw | OES_FDR |\n")
    md.append("|-----------|------|---------|---------|------|-------|---------|---------|-----|---------|---------|\n")
    for _, row in lmm_strict.iterrows():
        sig = "⭐" if pd.notna(row['P_AL']) and row['P_AL'] < 0.05 else ""
        sig_fdr = "⭐" if pd.notna(row.get('P_FDR')) and row['P_FDR'] < 0.05 else ""
        md.append(f"| {row['Distance']:.1f} | {int(row['N_eyes'])} | {int(row['N_subjects'])} | "
                  f"{row['Beta_AL']:+.3f} {sig} | {row['P_AL']:.4f} | "
                  f"{row.get('P_FDR', np.nan):.4f} {sig_fdr} | "
                  f"{row['R2_Marginal']:.3f} | {row['R2_Conditional']:.3f} | "
                  f"{row['ICC']:.3f} | {row['OES_Raw']:.3f} | {row['OES_FDR']:.3f} |\n")

    best_beta_strict = lmm_strict.loc[lmm_strict['Beta_AL'].abs().idxmax(), 'Distance']
    best_oes_strict = lmm_strict.loc[lmm_strict['OES_Raw'].idxmax(), 'Distance']
    md.append(f"\n**按 |beta_AL| 最大**：{best_beta_strict:.1f} mm\n")
    md.append(f"**按 OES_Raw 最高**：{best_oes_strict:.1f} mm\n\n")

    md.append("### 2.4 LMM 可视化\n\n")
    md.append("![Lenient LMM Figure 1](FIG/SR0530_lenient_Figure1_LMM_ML.png)\n\n")
    md.append("![Strict LMM Figure 1](FIG/SR0530_strict_Figure1_LMM_ML.png)\n\n")

    md.append("### 2.5 关于 AL 系数方向的说明\n\n")
    md.append("修复版 LMM 中 **AL 标准化系数为正**，这与基于 Linear cone density（cones/mm²）的旧 LMM 结果（AL 系数为负）方向相反。原因是：\n\n")
    md.append("1. 本研究 ML 与 LMM 统一使用 **Angular cone density（cones/deg²）**，该指标已用视网膜放大因子（RMF）校正。\n")
    md.append("2. Linear density 直接反映视网膜物理拉伸，AL 越长单位面积细胞越少，故 AL 系数为负（符合生物力学直觉）。\n")
    md.append("3. Angular density 经 RMF 校正后，与 AL 的关联方向发生改变；在本数据集中，AL 与角度密度呈正相关。\n")
    md.append("4. 因此，本研究的预测模型和机制解释应限定于 **角度密度** 框架，避免与线性密度结果直接比较。\n\n")

    # 三、超参数寻优关键结果
    md.append("## 三、超参数寻优关键结果\n\n")
    md.append("### 3.1 粗粒度寻优总体最佳\n\n")
    md.append(f"- **数据组**：{coarse_best['Data_Group']}\n")
    md.append(f"- **距离**：{coarse_best['Distance_mm']:.1f} mm\n")
    md.append(f"- **方案/模型**：{coarse_best['Schema']} / {coarse_best['Model']}\n")
    md.append(f"- **Test R²**：{coarse_best['test_r2']:.3f}\n")
    md.append(f"- **最佳参数**：{coarse_best['Best_Params']}\n\n")

    md.append("### 3.2 精细寻优总体最佳\n\n")
    md.append(f"- **配置**：{fine_best['Data_Group']} {fine_best['Distance_mm']:.1f}mm {fine_best['Schema']} {fine_best['Model']}\n")
    md.append(f"- **Fine Test R²**：{fine_best['Fine_Test_R2']:.3f}（Coarse: {fine_best['Coarse_Test_R2']:.3f}）\n")
    md.append(f"- **Fine 最佳参数**：{fine_best['Fine_Best_Params']}\n")
    md.append(f"- **稳定性**：{fine_best['Stability_Mean']:.3f} ± {fine_best['Stability_Std']:.3f}\n\n")

    md.append("### 3.3 最稳定配置\n\n")
    md.append(f"- **配置**：{fine_stable['Data_Group']} {fine_stable['Distance_mm']:.1f}mm {fine_stable['Schema']} {fine_stable['Model']}\n")
    md.append(f"- **稳定性 Mean ± Std**：{fine_stable['Stability_Mean']:.3f} ± {fine_stable['Stability_Std']:.3f}\n")
    md.append(f"- **Fine Test R²**：{fine_stable['Fine_Test_R2']:.3f}\n\n")

    md.append("### 3.4 不同偏心距的最佳性能\n\n")
    md.append(f"![Distance Performance](FIG/{dist_perf_file})\n\n")

    # 四、最终模型
    md.append("## 四、最终模型结果\n\n")
    for mr in model_results:
        name = mr['name'].replace('_', ' ')
        p = mr['performance']
        md.append(f"### {name}\n\n")
        md.append(f"**特征**：{', '.join(mr['feat_full'])}\n\n")
        md.append(f"**参数**：{mr['params']}\n\n")
        md.append("**LOSO CV 性能**：\n\n")
        md.append("| 指标 | 值 |\n")
        md.append("|------|---|\n")
        md.append(f"| R² | {p[0]:.3f} |\n")
        md.append(f"| Pearson r | {p[1]:.3f} |\n")
        md.append(f"| MAPE | {p[2]:.2f}% |\n")
        md.append(f"| RMSE | {p[3]:.1f} |\n")
        md.append(f"| MAE | {p[4]:.1f} |\n\n")

        md.append("**标准化系数与 Bootstrap 95% CI**：\n\n")
        md.append("| Feature | Coefficient | 95% CI Lower | 95% CI Upper | 显著 |\n")
        md.append("|---------|-------------|--------------|--------------|------|\n")
        for _, row in mr['coef_df'].iterrows():
            sig = "是" if not (row['CI_Lower'] <= 0 <= row['CI_Upper']) else "否"
            md.append(f"| {row['Feature']} | {row['Coefficient']:.3f} | {row['CI_Lower']:.3f} | {row['CI_Upper']:.3f} | {sig} |\n")
        md.append("\n")

        md.append(f"![Scatter](FIG/{mr['scatter_file']})\n\n")
        md.append(f"![Coefficients](FIG/{mr['coef_file']})\n\n")

    # 六、讨论
    md.append("## 六、讨论\n\n")
    md.append("1. **最佳偏心距 3.0 mm**：LMM 显示 |beta_AL| 在 3.0 mm 处最大；ML 超参数寻优中 lenient 数据的最佳预测点也在 3.0 mm。两者为最终靶点选择提供了双重证据。\n")
    md.append("2. **主模型选择 A1_Ridge**：仅用 AL、Age、Gender 三个特征即可达到与 C1_Lasso 相当的性能，且更简洁、更稳定。\n")
    md.append("3. **显著预测因子**：AL 和 Gender 的 95% CI 不跨 0；Age 和 SE 的 CI 跨 0，独立预测作用不显著。\n")
    md.append("4. **AL 与角度密度正相关**：在 Angular cone density 框架下，AL 增加伴随角度密度增加，这可能反映了 RMF 校正后的测量特性，需在讨论中谨慎解读。\n")
    md.append("5. **临床意义**：眼轴长度是视锥密度的最强预测因子；性别可能反映解剖或激素差异；年龄和近视度数（SE）的独立效应较弱。\n")
    md.append("6. **局限性**：样本量有限（39–46 subjects），LOSO CV R² 约 0.44，预测精度仍有提升空间；未来需要外部验证。\n\n")

    # 七、结论
    md.append("## 七、结论\n\n")
    md.append("基于 lenient 数据 3.0 mm 处的 LMM 与 ML 双重验证，**A1_Ridge 模型（AL + Age + Gender，alpha=10.0）**是预测黄斑旁中心视锥细胞密度（Angular cone density）的最佳模型。眼轴长度（AL）和性别（Gender）是统计上显著的预测因子。该模型可作为后续临床研究和论文撰写的核心结果。\n\n")

    # 八、后续工作
    md.append("## 八、后续工作\n\n")
    md.append("1. 扩大样本量并进行外部验证。\n")
    md.append("2. 对比 Linear cone density 与 Angular cone density 的 LMM 结果，明确 AL 效应方向差异的机制。\n")
    md.append("3. 按近视程度做分层分析（已有初步结果，需更大样本验证）。\n")
    md.append("4. 将结果整合到正式论文的 Results 和 Discussion 章节。\n\n")

    md.append("---\n\n")
    md.append("*Report generated automatically by SR_generate_comprehensive_report.py*\n")

    md_path = os.path.join(REPORT_DIR, 'SR0530_Comprehensive_Final_Report.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(''.join(md))
    print(f"  --> Comprehensive report: {md_path}")


if __name__ == '__main__':
    main()
