"""
SR_LMM_revised.py
修复版 LMM 分析：
1. 使用 CleanDataRoi 数据，与 ML 层保持一致
2. 修复 R2 计算（保护性处理）
3. 调整 OES 公式避免 ICC 爆炸：OES_raw = |beta| * (-log10 P) / (1 + ICC)
4. 同时输出未校正 OES 和 FDR 校正 OES（作为敏感性分析）
5. 生成 Figure 1：LMM beta 图 + ML Test R2 曲线
"""

import os
import glob
import warnings
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests
import scipy.stats as stats

warnings.filterwarnings('ignore')

# ============================================================
# 配置
# ============================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE_DIR, 'genData', 'sum')
REPORT_DIR = os.path.join(BASE_DIR, 'report')
FIG_DIR = os.path.join(REPORT_DIR, 'FIG')
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(FIG_DIR, exist_ok=True)

DATA_DIRS = {
    'strict': os.path.join(BASE_DIR, 'genData', 'CleanDataRoi_strict'),
    'lenient': os.path.join(BASE_DIR, 'genData', 'CleanDataRoi_lenient')
}

FEATURE_ALL = {
    'AL': 'Axial length (mm)',
    'Age': 'Age',
    'SE': 'Spherical equivalent refraction (D)',
    'Gender': 'Gender',
    'CC': 'Corneal curvature (mm)',
    'ACD': 'Anterior chamber depth (mm)'
}

TARGET_COL = 'Angular cone density (cones/ deg2)'
RANDOM_STATE = 42


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


def aggregate_distance(dfs, eye_to_subject, min_quadrants=4):
    """
    按 Subject_ID + Eye 聚合象限密度。

    参数:
        min_quadrants: 纳入某只眼所需的最少有效象限数。
                       - 4 = 传统 inner merge，必须 4 个象限完整（不放宽）
                       - 1 = 只要有 ≥1 个象限即可纳入（放宽为 ≥1 象限平均）
    """
    feature_cols = list(FEATURE_ALL.values())

    # 1. 合并 4 个象限的密度（outer merge 保留所有可用象限）
    merged = dfs[0][['Subject_ID', 'Eye', TARGET_COL]].copy()
    merged = merged.rename(columns={TARGET_COL: 'density_q1'})

    for i, d in enumerate(dfs[1:], 2):
        merged = merged.merge(
            d[['Subject_ID', 'Eye', TARGET_COL]].rename(columns={TARGET_COL: f'density_q{i}'}),
            on=['Subject_ID', 'Eye'], how='outer'
        )

    den_cols = [c for c in merged.columns if c.startswith('density_q')]
    merged['N_Quadrants'] = merged[den_cols].notna().sum(axis=1)
    merged[TARGET_COL] = merged[den_cols].mean(axis=1, skipna=True)

    # 2. 按最少象限数过滤
    if min_quadrants == 4:
        merged = merged[merged['N_Quadrants'] == 4].copy()
    else:
        merged = merged[merged['N_Quadrants'] >= min_quadrants].copy()

    # 3. 从第一个包含该眼的象限提取固定协变量（各象限协变量一致）
    features = None
    for d in dfs:
        df_feat = d[['Subject_ID', 'Eye'] + feature_cols].drop_duplicates(['Subject_ID', 'Eye'])
        if features is None:
            features = df_feat
        else:
            features = pd.concat([features, df_feat], ignore_index=True)
            features = features.drop_duplicates(['Subject_ID', 'Eye'], keep='first')

    base = merged.merge(features, on=['Subject_ID', 'Eye'], how='left')
    base['Real_Subject_ID'] = base['Subject_ID'].map(eye_to_subject)

    return base[['Subject_ID', 'Real_Subject_ID', 'Eye'] + feature_cols + ['N_Quadrants', TARGET_COL]].copy()


def fill_na(df, cols):
    for col in cols:
        if df[col].isna().any():
            df[col].fillna(df[col].median(), inplace=True)
    return df


def calc_r2_marginal_conditional(fit):
    """计算 LMM 的边际 R2 和条件 R2，带保护性处理"""
    try:
        exog = fit.model.exog
        fixed_params = fit.params[fit.model.exog_names]
        fixed_pred = exog @ fixed_params
        var_fixed = np.var(fixed_pred, ddof=0)

        var_random = fit.cov_re.iloc[0, 0] if hasattr(fit, 'cov_re') else 0.0
        var_resid = fit.scale

        total = var_fixed + var_random + var_resid
        if total <= 0 or var_resid < 0 or var_fixed < 0 or var_random < 0:
            return np.nan, np.nan

        r2_marginal = var_fixed / total
        r2_conditional = (var_fixed + var_random) / total
        return r2_marginal, r2_conditional
    except Exception:
        return np.nan, np.nan


def calc_mape_rmse(y_true, y_pred):
    mape = np.mean(np.abs((y_true - y_pred) / (y_true + 1e-10))) * 100
    rmse = np.sqrt(np.mean((y_true - y_pred)**2))
    return mape, rmse


def fit_lmm_per_distance(df_agg):
    """对每个距离组拟合 LMM"""
    distances = sorted(df_agg['Distance'].unique())
    results = []
    qq_data = {}

    feature_cols = list(FEATURE_ALL.values())
    zscore_cols = [TARGET_COL] + [FEATURE_ALL[c] for c in ['AL', 'Age', 'SE', 'CC', 'ACD']]

    for dist in distances:
        sub = df_agg[df_agg['Distance'] == dist].copy()
        sub = fill_na(sub, feature_cols)

        # 标准化连续变量
        scalers = {}
        for col in zscore_cols:
            mu, sd = sub[col].mean(), sub[col].std()
            scalers[col] = (mu, sd)
            sub[f'{col}_z'] = (sub[col] - mu) / sd if sd > 0 else 0

        # 构建 formula
        # 注意：statsmodels 中列名含空格或括号需要用 Q() 包裹
        formula = ("Q('Angular cone density (cones/ deg2)_z') ~ "
                   "Q('Axial length (mm)_z') + Q('Age_z') + "
                   "Q('Spherical equivalent refraction (D)_z') + "
                   "Q('Gender') + Q('Corneal curvature (mm)_z') + "
                   "Q('Anterior chamber depth (mm)_z') + Eye")

        try:
            model = smf.mixedlm(formula, sub, groups=sub['Real_Subject_ID'])
            fit = model.fit(reml=False)

            al_beta = fit.params["Q('Axial length (mm)_z')"]
            al_p = fit.pvalues["Q('Axial length (mm)_z')"]
            al_ci_low, al_ci_high = fit.conf_int().loc["Q('Axial length (mm)_z')"]

            sub['pred'] = fit.predict(sub)
            r2_marginal, r2_conditional = calc_r2_marginal_conditional(fit)

            y_true_orig = sub[TARGET_COL].values
            y_pred_orig = sub['pred'].values * scalers[TARGET_COL][1] + scalers[TARGET_COL][0]
            mape, rmse = calc_mape_rmse(y_true_orig, y_pred_orig)

            residuals = sub[f"{TARGET_COL}_z"] - sub['pred']

            var_random = fit.cov_re.iloc[0, 0]
            var_resid = fit.scale
            icc = var_random / (var_random + var_resid) if (var_random + var_resid) > 0 else np.nan

            results.append({
                'Distance': dist,
                'N_eyes': len(sub),
                'N_subjects': sub['Real_Subject_ID'].nunique(),
                'Beta_AL': al_beta,
                'P_AL': al_p,
                'CI_Lower': al_ci_low,
                'CI_Upper': al_ci_high,
                'R2_Marginal': r2_marginal,
                'R2_Conditional': r2_conditional,
                'MAPE': mape,
                'RMSE': rmse,
                'ICC': icc,
                'Random_Effect_Var': var_random,
                'Residual_Var': var_resid,
                'Converged': True
            })

            qq_data[dist] = {
                'residuals': residuals.values,
                'y_true': y_true_orig,
                'y_pred': y_pred_orig
            }

            sig = "*" if al_p < 0.05 else ""
            print(f"  {dist:.1f}mm | N={len(sub):3d} eyes/{sub['Real_Subject_ID'].nunique():3d} subj | "
                  f"beta_AL={al_beta:+.3f} p={al_p:.4f} {sig} | "
                  f"R2m={r2_marginal:.3f} R2c={r2_conditional:.3f} | "
                  f"MAPE={mape:.2f}% RMSE={rmse:.1f} | ICC={icc:.3f}")

        except Exception as e:
            print(f"  {dist:.1f}mm | LMM failed: {e}")
            results.append({
                'Distance': dist,
                'N_eyes': len(sub),
                'N_subjects': sub['Real_Subject_ID'].nunique(),
                'Beta_AL': np.nan,
                'P_AL': np.nan,
                'CI_Lower': np.nan,
                'CI_Upper': np.nan,
                'R2_Marginal': np.nan,
                'R2_Conditional': np.nan,
                'MAPE': np.nan,
                'RMSE': np.nan,
                'ICC': np.nan,
                'OES_Raw': np.nan,
                'OES_FDR': np.nan,
                'Random_Effect_Var': np.nan,
                'Residual_Var': np.nan,
                'Converged': False,
                'Error': str(e)
            })

    df_results = pd.DataFrame(results)

    # 计算 OES
    if df_results['P_AL'].notna().any():
        valid_mask = df_results['P_AL'].notna()
        pvals = df_results.loc[valid_mask, 'P_AL'].values
        _, p_fdr, _, _ = multipletests(pvals, alpha=0.05, method='fdr_bh')
        df_results.loc[valid_mask, 'P_FDR'] = p_fdr

        for idx in df_results[valid_mask].index:
            beta = df_results.loc[idx, 'Beta_AL']
            p = df_results.loc[idx, 'P_AL']
            icc = df_results.loc[idx, 'ICC']
            p_fdr_i = df_results.loc[idx, 'P_FDR']

            # 新版 OES_raw：避免 ICC 接近 0 时爆炸
            oes_raw = abs(beta) * (-np.log10(p + 1e-10)) / (1 + icc)
            df_results.loc[idx, 'OES_Raw'] = oes_raw

            # OES_fdr：仅当 FDR 通过时非零（作为敏感性分析）
            indicator = 1.0 if p_fdr_i < 0.05 else 0.0
            df_results.loc[idx, 'OES_FDR'] = oes_raw * indicator

    return df_results, qq_data


def prepare_lmm_data(data_group, min_quadrants=4):
    """从 CleanDataRoi 准备 LMM 长格式数据"""
    data_dir = DATA_DIRS[data_group]
    eye_to_subject = load_subject_mapping(data_dir)
    all_data = load_distance_data(data_dir)

    records = []
    for dist, dfs in all_data.items():
        df = aggregate_distance(dfs, eye_to_subject, min_quadrants=min_quadrants)
        df['Distance'] = dist
        records.append(df)

    df_all = pd.concat(records, ignore_index=True)
    return df_all


def plot_figure1(df_lmm, df_ml, data_group, out_prefix):
    """生成 Figure 1：LMM AL beta + ML Test R2 曲线"""
    fig, axes = plt.subplots(2, 1, figsize=(12, 10))

    # A. LMM AL beta
    ax = axes[0]
    colors = ['#e74c3c' if p < 0.05 else '#95a5a6' for p in df_lmm['P_AL']]
    ax.bar([f"{d:.1f}" for d in df_lmm['Distance']], df_lmm['Beta_AL'], color=colors, edgecolor='black')
    ax.axhline(0, color='black', linewidth=0.8)
    ax.set_xlabel('Eccentricity (mm)')
    ax.set_ylabel('Standardized beta (AL)')
    ax.set_title('A. LMM: AL Effect on Cone Density Across Eccentricities')
    ax.grid(True, alpha=0.3, axis='y')

    # B. ML best Test R2
    ax = axes[1]
    best_per_d = df_ml.loc[df_ml.groupby('Distance_mm')['test_r2'].idxmax()].sort_values('Distance_mm')
    ax.plot(best_per_d['Distance_mm'], best_per_d['test_r2'], 'o-', color='steelblue', lw=2, markersize=8)
    ax.axhline(0, color='gray', linestyle='--', lw=0.8)
    ax.set_xlabel('Eccentricity (mm)')
    ax.set_ylabel('Best Test R² (ML)')
    ax.set_title('B. ML: Best Predictive Performance Across Eccentricities')
    ax.grid(True, alpha=0.3)
    for _, row in best_per_d.iterrows():
        ax.annotate(f"{row['Model'][:3]}\n{row['test_r2']:.2f}",
                    (row['Distance_mm'], row['test_r2']),
                    textcoords="offset points", xytext=(0, 10), ha='center', fontsize=7)

    plt.suptitle(f'SR0530 Figure 1: LMM Target Screening & ML Validation ({data_group} data)',
                 fontsize=14, fontweight='bold')
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    path = os.path.join(OUT_DIR, f'{out_prefix}_Figure1_LMM_ML.png')
    plt.savefig(path, dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(FIG_DIR, os.path.basename(path)), dpi=300, bbox_inches='tight')
    plt.close()
    return os.path.basename(path)


def plot_qq(qq_data, out_prefix):
    n_dist = len(qq_data)
    if n_dist == 0:
        return None
    ncols = 4
    nrows = max(1, int(np.ceil(n_dist / ncols)))
    fig, axes = plt.subplots(nrows, ncols, figsize=(14, 3.5 * nrows))
    axes = axes.flatten()

    for idx, (dist, data) in enumerate(sorted(qq_data.items())):
        ax = axes[idx]
        stats.probplot(data['residuals'], dist="norm", plot=ax)
        ax.set_title(f'{dist:.1f} mm')
        ax.grid(True, alpha=0.3)

    for idx in range(n_dist, len(axes)):
        axes[idx].axis('off')

    fig.suptitle('Q-Q Plots of LMM Residuals by Distance', fontsize=14, fontweight='bold')
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    path = os.path.join(OUT_DIR, f'{out_prefix}_QQPlots.png')
    plt.savefig(path, dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(FIG_DIR, os.path.basename(path)), dpi=300, bbox_inches='tight')
    plt.close()
    return os.path.basename(path)


def generate_report(df_lmm, df_ml, data_group, figure1_file, qq_file, mode_label):
    md = []
    mode_desc = {
        'q4': '≥4 象限完整（不放宽，inner merge）',
        'q1plus': '≥1 象限可用（放宽，outer merge 取平均）'
    }.get(mode_label, mode_label)
    md.append(f"# SR0530 修复版 LMM 分析报告（{data_group.upper()} 数据 | {mode_desc}）\n\n")
    md.append("> **目标**：确定 1.0–6.0 mm 偏心率中，视锥细胞密度受眼部参数影响最显著的点。\n\n")
    md.append("> **方法**：每个偏心率独立拟合 LMM，Subject_ID 作为随机效应；OES 公式已调整以避免 ICC 接近 0 时的数值爆炸。\n\n")
    md.append("> **数据**：从 CleanDataRoi 读取，与 ML 层保持一致。\n\n")

    md.append("---\n\n")

    md.append("## 一、LMM 结果汇总\n\n")
    md.append("| 距离 (mm) | 眼数 | 受试者数 | beta_AL | P 值 | P_FDR | R²_边际 | R²_条件 | MAPE(%) | RMSE | ICC | OES_Raw | OES_FDR |\n")
    md.append("|-----------|------|---------|---------|------|-------|---------|---------|---------|------|-----|---------|---------|\n")
    for _, row in df_lmm.iterrows():
        sig = "⭐" if row['P_AL'] < 0.05 else ""
        sig_fdr = "⭐" if (pd.notna(row.get('P_FDR')) and row['P_FDR'] < 0.05) else ""
        md.append(f"| {row['Distance']:.1f} | {int(row['N_eyes'])} | {int(row['N_subjects'])} | "
                  f"{row['Beta_AL']:.3f} {sig} | {row['P_AL']:.4f} | "
                  f"{row.get('P_FDR', np.nan):.4f} {sig_fdr} | "
                  f"{row['R2_Marginal']:.3f} | {row['R2_Conditional']:.3f} | "
                  f"{row['MAPE']:.2f} | {row['RMSE']:.1f} | {row['ICC']:.3f} | "
                  f"{row['OES_Raw']:.3f} | {row['OES_FDR']:.3f} |\n")

    # 关键点计算（带 NaN 保护）
    best_beta = df_lmm.loc[df_lmm['Beta_AL'].abs().idxmax(), 'Distance'] if df_lmm['Beta_AL'].notna().any() else np.nan
    best_raw = df_lmm.loc[df_lmm['OES_Raw'].idxmax(), 'Distance'] if df_lmm['OES_Raw'].notna().any() else np.nan
    best_fdr = df_lmm.loc[df_lmm['OES_FDR'].idxmax(), 'Distance'] if df_lmm['OES_FDR'].notna().any() else np.nan

    md.append(f"\n**按 |beta_AL| 最大**：{best_beta:.1f} mm\n" if pd.notna(best_beta) else "\n**按 |beta_AL| 最大**：无有效结果\n")
    md.append(f"**按 OES_Raw 最高**：{best_raw:.1f} mm\n" if pd.notna(best_raw) else "**按 OES_Raw 最高**：无有效结果\n")
    if pd.notna(best_fdr) and df_lmm['OES_FDR'].max() > 0:
        md.append(f"**按 OES_FDR 最高**：{best_fdr:.1f} mm\n\n")
    else:
        md.append("**按 OES_FDR 最高**：FDR 校正后无显著点\n\n")

    # 动态提取未通过 FDR 的距离
    fdr_fail = df_lmm[(df_lmm['P_FDR'].notna()) & (df_lmm['P_FDR'] >= 0.05)]['Distance'].tolist()
    fdr_fail_str = ', '.join([f"{d:.1f} mm" for d in fdr_fail]) if fdr_fail else "无"

    md.append("## 二、关键指标说明\n\n")
    md.append("- **beta_AL**：AL 的标准化回归系数。\n")
    md.append("- **P_FDR**：Benjamini-Hochberg FDR 校正后的 P 值。\n")
    md.append("- **R²_边际 / R²_条件**：固定效应 / 固定+随机效应解释的变异比例。\n")
    md.append("- **ICC** = σ²_random / (σ²_random + σ²_residual)。\n")
    md.append("- **OES_Raw** = |beta_AL| × (-log10(P_AL)) / (1 + ICC)，避免 ICC 接近 0 时爆炸。\n")
    md.append("- **OES_FDR** = OES_Raw × I(P_FDR < 0.05)，作为敏感性分析。\n\n")

    md.append("## 三、可视化\n\n")
    md.append(f"![Figure 1](FIG/{figure1_file})\n\n")
    md.append(f"![Q-Q Plots](FIG/{qq_file})\n\n")

    md.append("## 四、讨论\n\n")
    md.append("1. 本修复版 LMM 从 CleanDataRoi 读取数据，与 ML 层使用完全一致的数据集（Angular cone density，单位 cones/deg²）。\n")
    md.append("2. **AL 标准化系数方向**：在本数据中，眼轴长度（AL）与角度密度（Angular density）的关联方向见上表。若需要与线性密度（Linear density，cones/mm²）结果对照，需另行补充 Linear density 的 LMM 分析；两种口径因视网膜放大因子（RMF）校正差异，AL 的系数方向可能不同。\n")
    md.append("3. R² 计算已加入保护性处理，避免方差非正时的数值异常。\n")
    md.append(f"4. OES_FDR 作为敏感性分析：未通过 FDR 校正的距离为 {fdr_fail_str}。对这些距离的结果需谨慎解读。\n")
    md.append(f"5. LMM 效应最敏感点（按 |beta_AL| 最大）位于 **{best_beta:.1f} mm**，为靶点选择提供了 LMM 层面的证据。\n\n")

    md.append("---\n\n")
    md.append("*Report generated by SR_LMM_revised.py*\n")

    md_path = os.path.join(REPORT_DIR, f'SR0530_LMM_Revised_{data_group}_{mode_label}_Report.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(''.join(md))
    print(f"  --> Report: {md_path}")


def main():
    print("=" * 80)
    print("SR0530 Revised LMM Analysis")
    print("=" * 80)

    # 读取 ML q1plus 结果用于 Figure 1
    ml_results = pd.read_csv(os.path.join(OUT_DIR, 'SR0530_HP_Tuning_Results_q1plus.csv'))

    # 只保留 q1plus 模式
    mode_label = 'q1plus'
    mode_desc = '放宽：≥1 个象限可用即纳入'
    min_q = 1

    print(f"\n{'='*80}")
    print(f"MODE: {mode_desc} (min_quadrants={min_q})")
    print(f"{'='*80}")

    for data_group in ['strict', 'lenient']:
        print(f"\n{'='*80}")
        print(f"Processing {data_group.upper()} data")
        print(f"{'='*80}")

        df_agg = prepare_lmm_data(data_group, min_quadrants=min_q)
        print(f"  Total records: {len(df_agg)}")
        print(f"  Distances: {sorted(df_agg['Distance'].unique())}")
        print(f"  Subjects: {df_agg['Real_Subject_ID'].nunique()}")
        print(f"  Eyes: {df_agg['Subject_ID'].nunique()}")
        print(f"  Quadrant policy: min={min_q}, mean available quadrants per record = {df_agg['N_Quadrants'].mean():.2f}")

        print("\n  Fitting LMM per distance...")
        df_lmm, qq_data = fit_lmm_per_distance(df_agg)

        # 保存 CSV
        csv_path = os.path.join(OUT_DIR, f'SR0530_LMM_Revised_{data_group}_{mode_label}_Results.csv')
        df_lmm.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"  --> CSV: {csv_path}")

        # 生成图
        df_ml_g = ml_results[ml_results['Data_Group'] == data_group]
        figure1_file = plot_figure1(df_lmm, df_ml_g, data_group, f'SR0530_{data_group}_{mode_label}')
        qq_file = plot_qq(qq_data, f'SR0530_{data_group}_{mode_label}')

        # 生成报告
        generate_report(df_lmm, df_ml_g, data_group, figure1_file, qq_file, mode_label)

    print("\n" + "=" * 80)
    print("Revised LMM analysis complete!")
    print("=" * 80)


if __name__ == '__main__':
    main()
