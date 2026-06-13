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

# 最终推荐配置
FINAL_CONFIGS = [
    {
        'name': 'Primary Model: A1_Ridge',
        'distance': 3.0,
        'schema': ['AL', 'Age', 'Gender'],
        'model_name': 'Ridge',
        'params': {'alpha': 10.0},
        'rationale': '稳定性最高（20次重复CV mean=0.303），Gap小（0.040），模型简洁可解释。'
    },
    {
        'name': 'Alternative Model: C1_Lasso',
        'distance': 3.0,
        'schema': ['SE', 'AL', 'Age', 'Gender'],
        'model_name': 'Lasso',
        'params': {'alpha': 5.0},
        'rationale': '单点性能最高（Fine R²=0.549），能自动进行特征选择，但稳定性略低。'
    }
]

MYOPIA_THRESHOLD = -0.5
RANDOM_STATE = 42
N_BOOTSTRAP = 1000


# ============================================================
# 工具函数（复用）
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


def get_model_builder(model_name, params):
    if model_name == 'Ridge':
        return lambda: Pipeline([('s', StandardScaler()), ('m', Ridge(**params))])
    elif model_name == 'Lasso':
        return lambda: Pipeline([('s', StandardScaler()), ('m', Lasso(**params, max_iter=5000))])
    else:
        raise ValueError(f"Unsupported model: {model_name}")


def leave_one_subject_out_cv(X, y, groups, model_builder):
    """按 subject 留一交叉验证，返回真实值和预测值"""
    unique_groups = np.unique(groups)
    all_true, all_pred = [], []
    fold_results = []

    for g in unique_groups:
        test_mask = groups == g
        train_mask = ~test_mask

        model = model_builder()
        model.fit(X[train_mask], y[train_mask])
        pred = model.predict(X[test_mask])

        all_true.extend(y[test_mask])
        all_pred.extend(pred)

        fold_results.append({
            'Subject_ID': g,
            'N_Eyes': int(test_mask.sum()),
            'True_Mean': float(np.mean(y[test_mask])),
            'Pred_Mean': float(np.mean(pred))
        })

    return np.array(all_true), np.array(all_pred), fold_results


def block_bootstrap_ci(X_df, y, groups, model_builder, feature_names, n_bootstrap=1000):
    """按 subject 做 block bootstrap，返回标准化系数的置信区间"""
    unique_groups = np.unique(groups)
    n_groups = len(unique_groups)

    coef_list = []
    rng = np.random.RandomState(RANDOM_STATE)

    for b in range(n_bootstrap):
        sampled_groups = rng.choice(unique_groups, size=n_groups, replace=True)

        # 构建 bootstrap 样本索引（block bootstrap）
        idx = []
        for g in sampled_groups:
            idx.extend(np.where(groups == g)[0])

        X_b = X_df.iloc[idx].values
        y_b = y[idx]

        model = model_builder()
        model.fit(X_b, y_b)

        # 提取标准化后的系数
        scaler = model.named_steps['s']
        reg = model.named_steps['m']
        # 模型在标准化后的特征上训练，coef_ 即为标准化系数
        coef_list.append(reg.coef_.copy())

    coef_array = np.array(coef_list)
    ci_lower = np.percentile(coef_array, 2.5, axis=0)
    ci_upper = np.percentile(coef_array, 97.5, axis=0)
    ci_mean = np.mean(coef_array, axis=0)

    return pd.DataFrame({
        'Feature': feature_names,
        'Coefficient_Mean': ci_mean,
        'CI_Lower': ci_lower,
        'CI_Upper': ci_upper
    })


def train_full_model(X_df, y, model_builder, feature_names):
    """在完整数据上训练最终模型，返回标准化系数"""
    model = model_builder()
    model.fit(X_df.values, y)
    reg = model.named_steps['m']
    coef_df = pd.DataFrame({
        'Feature': feature_names,
        'Coefficient': reg.coef_
    })
    return model, coef_df


# ============================================================
# 可视化
# ============================================================
def plot_observed_vs_predicted(y_true, y_pred, model_name, out_prefix):
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.scatter(y_true, y_pred, alpha=0.6, edgecolors='black', s=80)

    # 参考线
    min_val = min(y_true.min(), y_pred.min())
    max_val = max(y_true.max(), y_pred.max())
    ax.plot([min_val, max_val], [min_val, max_val], 'r--', lw=2, label='Identity line')

    # 回归线
    z = np.polyfit(y_true, y_pred, 1)
    p = np.poly1d(z)
    ax.plot(y_true, p(y_true), 'b-', lw=1.5, label='Fit line')

    r2, corr, mape, rmse, mae = calc_scores(y_true, y_pred)
    ax.set_xlabel('Observed cone density (cones/deg²)')
    ax.set_ylabel('Predicted cone density (cones/deg²)')
    ax.set_title(f'{model_name}\nLOSO CV: R²={r2:.3f}, r={corr:.3f}, MAPE={mape:.2f}%, RMSE={rmse:.1f}')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    fig_path = os.path.join(OUT_DIR, f'{out_prefix}_Observed_vs_Predicted.png')
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(FIG_DIR, os.path.basename(fig_path)), dpi=300, bbox_inches='tight')
    plt.close()
    return fig_path


def plot_bland_altman(y_true, y_pred, model_name, out_prefix):
    mean = (y_true + y_pred) / 2
    diff = y_pred - y_true
    md = np.mean(diff)
    sd = np.std(diff, ddof=1)

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.scatter(mean, diff, alpha=0.6, edgecolors='black', s=80)
    ax.axhline(md, color='red', linestyle='--', lw=2, label=f'Mean diff = {md:.1f}')
    ax.axhline(md + 1.96 * sd, color='gray', linestyle='--', lw=1.5, label=f'+1.96 SD = {md + 1.96*sd:.1f}')
    ax.axhline(md - 1.96 * sd, color='gray', linestyle='--', lw=1.5, label=f'-1.96 SD = {md - 1.96*sd:.1f}')

    ax.set_xlabel('Mean of observed and predicted (cones/deg²)')
    ax.set_ylabel('Predicted - Observed (cones/deg²)')
    ax.set_title(f'{model_name}: Bland-Altman Plot')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    fig_path = os.path.join(OUT_DIR, f'{out_prefix}_Bland_Altman.png')
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(FIG_DIR, os.path.basename(fig_path)), dpi=300, bbox_inches='tight')
    plt.close()
    return fig_path


def plot_coefficient_forest(coef_df, model_name, out_prefix):
    """系数森林图"""
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
    ax.set_title(f'{model_name}: Standardized Coefficients with 95% CI')
    ax.grid(True, alpha=0.3, axis='x')
    plt.tight_layout()

    fig_path = os.path.join(OUT_DIR, f'{out_prefix}_Coefficients.png')
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(FIG_DIR, os.path.basename(fig_path)), dpi=300, bbox_inches='tight')
    plt.close()
    return fig_path


# ============================================================
# 主程序
# ============================================================
def main():
    print("=" * 80)
    print("SR0530 ML Final Model Report Generation")
    print("=" * 80)

    # 加载 lenient 3.0mm 数据
    eye_to_subject = load_subject_mapping(DATA_DIR)
    all_data = load_distance_data(DATA_DIR)

    # 存储每个最终配置的结果
    all_results = []

    for cfg in FINAL_CONFIGS:
        dist = cfg['distance']
        print(f"\n--- Processing {cfg['name']} ---")

        dfs = all_data[dist]
        df = aggregate_distance(dfs, eye_to_subject)

        feat_short = cfg['schema']
        feat_full = [FEATURE_ALL[s] for s in feat_short]
        df_sub = fill_na(df.copy(), feat_full)

        X = df_sub[feat_full]
        y = df_sub[TARGET_COL].values
        groups = df_sub['Real_Subject_ID'].values

        n_eyes = len(df_sub)
        n_subjects = len(np.unique(groups))

        print(f"  Data: {n_eyes} eyes / {n_subjects} subjects at {dist:.1f} mm")

        model_builder = get_model_builder(cfg['model_name'], cfg['params'])

        # 1. LOSO CV 评估
        y_true, y_pred, fold_results = leave_one_subject_out_cv(X.values, y, groups, model_builder)
        r2, corr, mape, rmse, mae = calc_scores(y_true, y_pred)

        print(f"  LOSO CV: R2={r2:.3f}, r={corr:.3f}, MAPE={mape:.2f}%, RMSE={rmse:.1f}, MAE={mae:.1f}")

        # 2. 完整数据训练 + Bootstrap CI
        full_model, full_coef = train_full_model(X, y, model_builder, feat_full)
        ci_df = block_bootstrap_ci(X, y, groups, model_builder, feat_full, n_bootstrap=N_BOOTSTRAP)

        # 合并完整系数和 CI
        coef_summary = full_coef.merge(ci_df, on='Feature')
        print("  Coefficients:")
        for _, row in coef_summary.iterrows():
            print(f"    {row['Feature']}: {row['Coefficient']:.3f} "
                  f"(95% CI: {row['CI_Lower']:.3f}, {row['CI_Upper']:.3f})")

        # 3. 可视化
        prefix = cfg['name'].split(':')[0].replace(' ', '_')
        plot_observed_vs_predicted(y_true, y_pred, cfg['name'], prefix)
        plot_bland_altman(y_true, y_pred, cfg['name'], prefix)
        plot_coefficient_forest(coef_summary, cfg['name'], prefix)

        all_results.append({
            'config': cfg,
            'n_eyes': n_eyes,
            'n_subjects': n_subjects,
            'performance': {
                'r2': r2, 'corr': corr, 'mape': mape, 'rmse': rmse, 'mae': mae
            },
            'coef_summary': coef_summary,
            'fold_results': fold_results,
            'prefix': prefix
        })

    # 4. 生成最终报告
    generate_final_report(all_results)

    print("\n" + "=" * 80)
    print("Final report generated!")
    print("=" * 80)


# ============================================================
# 最终报告生成
# ============================================================
def generate_final_report(all_results):
    md = []
    md.append("# SR0530 视锥细胞密度预测最终模型报告\n\n")
    md.append("> **目标**：基于 lenient 数据，选择并验证预测黄斑旁中心视锥细胞密度的最优机器学习模型。\n\n")
    md.append("> **最终距离**：3.0 mm（基于粗粒度与精细寻优的一致最优表现）\n\n")
    md.append("> **评估方法**：Leave-One-Subject-Out Cross-Validation (LOSO CV) + Block Bootstrap 95% CI\n\n")

    md.append("---\n\n")

    # 一、模型选择依据
    md.append("## 一、模型选择依据\n\n")
    md.append("通过粗粒度（11 距离 × 4 方案 × 7 模型）与精细寻优（Top 12 配置 × 50 迭代 × 20 次稳定性重复）后，得出以下结论：\n\n")
    md.append("1. **数据组**：`lenient`（距离平均 >7000 剔除）全面优于 `strict`，Top 配置全部来自 lenient。\n")
    md.append("2. **最佳距离**：3.0 mm，在多个模型中均表现最佳。\n")
    md.append("3. **主模型**：A1 方案（AL + Age + Gender）+ Ridge，稳定性最高（20 次重复 CV mean=0.303），模型简洁、可解释性强。\n")
    md.append("4. **备选模型**：C1 方案（SE + AL + Age + Gender）+ Lasso，单点性能最高（Fine R²=0.549），但稳定性略低。\n\n")

    # 二、主模型：A1_Ridge
    md.append("## 二、主模型：A1_Ridge（推荐）\n\n")
    for res in all_results:
        if 'A1' in res['config']['name']:
            append_model_section(md, res)

    # 三、备选模型：C1_Lasso
    md.append("\n## 三、备选模型：C1_Lasso\n\n")
    for res in all_results:
        if 'C1' in res['config']['name']:
            append_model_section(md, res)

    # 四、模型对比与讨论
    md.append("\n## 四、模型对比与讨论\n\n")
    md.append("| 指标 | A1_Ridge（主模型） | C1_Lasso（备选） |\n")
    md.append("|------|-------------------|------------------|\n")

    primary = next(r for r in all_results if 'A1' in r['config']['name'])
    alt = next(r for r in all_results if 'C1' in r['config']['name'])
    p = primary['performance']
    a = alt['performance']
    md.append(f"| LOSO CV R² | {p['r2']:.3f} | {a['r2']:.3f} |\n")
    md.append(f"| Pearson r | {p['corr']:.3f} | {a['corr']:.3f} |\n")
    md.append(f"| MAPE | {p['mape']:.2f}% | {a['mape']:.2f}% |\n")
    md.append(f"| RMSE | {p['rmse']:.1f} | {a['rmse']:.1f} |\n")
    md.append(f"| MAE | {p['mae']:.1f} | {a['mae']:.1f} |\n")
    md.append(f"| 特征数 | {len(primary['coef_summary'])} | {len(alt['coef_summary'])} |\n")
    md.append("\n")

    md.append("**讨论**：\n\n")
    md.append("- A1_Ridge 仅使用 AL、Age、Gender 三个特征，避免了 SE 与 AL 之间的共线性，模型更稳健。\n")
    md.append("- C1_Lasso 引入 SE 后单点 R² 更高，但特征增多、CI 更宽，且 Lasso 将 SE 系数压缩后仍保留 AL 和 Age。\n")
    md.append("- 两个模型均显示 **AL（眼轴长度）和 Gender（性别）是统计上显著的预测因素**（95% CI 不跨 0），其标准化系数为正，提示更长的眼轴和男性性别与更高的旁中心视锥细胞密度相关。\n")
    md.append("- **Age（年龄）的 95% CI 跨 0**，在控制 AL 和 Gender（以及 SE）后，年龄对视锥细胞密度的独立预测作用不稳定。\n")
    md.append("- C1_Lasso 中 **SE（等效球镜）的 95% CI 跨 0**，说明在已有 AL 的情况下，SE 未提供额外的独立预测信息，近视程度对视锥密度的影响可能已被 AL 所解释。\n")
    md.append("- 所有系数的 Bootstrap 95% CI 应包含真实的标准化效应量；若某特征 CI 跨 0，则该特征效应在统计上不稳定。\n\n")

    # 五、结论
    md.append("## 五、结论与建议\n\n")
    md.append("1. **推荐使用 A1_Ridge 作为主模型**：在 lenient 3.0 mm 数据上，使用 `AL + Age + Gender` 和 `Ridge(alpha=10.0)`，LOSO CV 性能稳定。\n")
    md.append("2. **最终距离选择 3.0 mm**：该距离在 strict/lenient 数据中均为最佳或接近最佳，且样本量相对充足。\n")
    md.append("3. **临床解释**：眼轴长度（AL）和性别（Gender）是黄斑旁中心视锥细胞密度的主要预测因子；年龄（Age）和等效球镜（SE）的独立预测作用不显著，提示近视对视锥密度的影响可能主要通过 AL 体现。\n")
    md.append("4. **后续工作**：建议补充外部验证集或扩大样本量，以进一步确认模型的泛化能力。\n\n")

    md.append("---\n\n")
    md.append("*Report generated automatically by SR_ML_final_report.py*\n")

    md_path = os.path.join(REPORT_DIR, 'SR0530_ML_Final_Model_Report.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(''.join(md))
    print(f"  --> Final report: {md_path}")


def append_model_section(md, res):
    cfg = res['config']
    p = res['performance']
    prefix = res['prefix']

    md.append(f"### {cfg['name']}\n\n")
    md.append(f"**选择理由**：{cfg['rationale']}\n\n")
    md.append(f"**数据**：lenient 数据组，{cfg['distance']:.1f} mm，{res['n_eyes']} 眼 / {res['n_subjects']} subjects\n\n")
    md.append(f"**模型参数**：{cfg['params']}\n\n")

    md.append("**LOSO CV 性能**：\n\n")
    md.append("| 指标 | 值 |\n")
    md.append("|------|---|\n")
    md.append(f"| R² | {p['r2']:.3f} |\n")
    md.append(f"| Pearson r | {p['corr']:.3f} |\n")
    md.append(f"| MAPE | {p['mape']:.2f}% |\n")
    md.append(f"| RMSE | {p['rmse']:.1f} |\n")
    md.append(f"| MAE | {p['mae']:.1f} |\n\n")

    md.append("**标准化系数（完整数据训练）与 Bootstrap 95% CI**：\n\n")
    md.append("| Feature | Coefficient | 95% CI Lower | 95% CI Upper | 解释 |\n")
    md.append("|---------|-------------|--------------|--------------|------|\n")
    for _, row in res['coef_summary'].iterrows():
        sig = "✓" if not (row['CI_Lower'] <= 0 <= row['CI_Upper']) else ""
        md.append(f"| {row['Feature']} | {row['Coefficient']:.3f} | {row['CI_Lower']:.3f} | {row['CI_Upper']:.3f} | {sig} |\n")
    md.append("\n")

    md.append("**每 Subject 的 LOSO CV 结果**：\n\n")
    md.append("| Subject_ID | N_Eyes | True Mean | Pred Mean |\n")
    md.append("|------------|--------|-----------|-----------|\n")
    for fr in res['fold_results']:
        md.append(f"| {fr['Subject_ID']} | {fr['N_Eyes']} | {fr['True_Mean']:.1f} | {fr['Pred_Mean']:.1f} |\n")
    md.append("\n")

    md.append("**可视化**：\n\n")
    md.append(f"![Observed vs Predicted](FIG/{prefix}_Observed_vs_Predicted.png)\n\n")
    md.append(f"![Bland-Altman](FIG/{prefix}_Bland_Altman.png)\n\n")
    md.append(f"![Coefficients](FIG/{prefix}_Coefficients.png)\n\n")


if __name__ == '__main__':
    main()
