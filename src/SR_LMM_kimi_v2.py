"""
SR_LMM_kimi_v2.py
Kimi 方案 v2.0：单模型多层 LMM 靶点筛选
- 长格式数据：一只眼在一个偏心率上的平均角密度
- 全局 Z-score 标准化 Density
- 模型：Density_z ~ C(Distance) * AL_z + Age_z + Gender + Eye + (1 | Subject_ID)
- 计算每个偏心率处 AL 的边际效应、95% CI、FDR 校正 P 值、ICC、OES
"""

import os
import glob
import warnings
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

import statsmodels.formula.api as smf
import scipy.stats as stats
from statsmodels.stats.multitest import multipletests

warnings.filterwarnings('ignore')

# ============================================================
# 配置
# ============================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORG_PATH = os.path.join(BASE_DIR, 'orgData', 'orgData.csv')
DATA_DIR = os.path.join(BASE_DIR, 'genData', 'CleanDataRoi')
PAIR_PATH = os.path.join(BASE_DIR, 'genData', 'sum', 'Subject_Pair_Mapping.csv')
OUT_DIR = os.path.join(BASE_DIR, 'genData', 'sum')
os.makedirs(OUT_DIR, exist_ok=True)

TARGET_COL = 'Angular cone density (cones/ deg2)'
FEATURE_MAP = {
    'AL': 'Axial length (mm)',
    'Age': 'Age',
    'SE': 'Spherical equivalent refraction (D)',
    'Gender': 'Gender',
    'K': 'Corneal curvature (mm)',
    'ACD': 'Anterior chamber depth (mm)'
}


# ============================================================
# 工具函数
# ============================================================
def load_subject_mapping():
    """建立 CleanDataRoi 的 Eye_xxx -> 真实 Subject_ID 映射"""
    pairs = pd.read_csv(PAIR_PATH)
    pid_to_subject = {}
    for _, row in pairs.iterrows():
        pid_to_subject[int(row['OD_PatientID'])] = row['Subject_ID']
        pid_to_subject[int(row['OS_PatientID'])] = row['Subject_ID']

    df_org = pd.read_csv(ORG_PATH)
    df_ref = pd.read_csv(os.path.join(DATA_DIR, 'data1.csv'))

    eye_to_pid = {}
    for _, row in df_ref.iterrows():
        eye = row['Eye']
        al = row['Axial length (mm)']
        age = row['Age']
        se = row['Spherical equivalent refraction (D)']
        gender = row['Gender']
        mask = (df_org['Eye'] == eye) & \
               (df_org['Axial length (mm)'] == al) & \
               (df_org['Age'] == age) & \
               (df_org['Spherical equivalent refraction (D)'] == se) & \
               (df_org['Gender'] == gender)
        matches = df_org[mask]
        if len(matches) == 1:
            eye_to_pid[row['Subject_ID']] = int(matches.iloc[0]['Patient ID'])
        else:
            raise ValueError(f"Cannot uniquely map {row['Subject_ID']}: {len(matches)} matches")

    eye_to_subject = {}
    for eye_id, pid in eye_to_pid.items():
        eye_to_subject[eye_id] = pid_to_subject.get(pid, f'Single_{pid}')

    return eye_to_subject


def load_and_aggregate():
    """读取 44 个 ROI 文件，按 Distance 聚合 4 象限"""
    eye_to_subject = load_subject_mapping()
    all_data = {}
    for f in sorted(glob.glob(os.path.join(DATA_DIR, 'data*.csv'))):
        df = pd.read_csv(f)
        dist = df['Eccentricity (mm)'].iloc[0]
        if dist not in all_data:
            all_data[dist] = []
        all_data[dist].append(df)

    long_records = []
    for dist, dfs in sorted(all_data.items()):
        base = dfs[0][['Subject_ID', 'Eye'] + list(FEATURE_MAP.values()) + [TARGET_COL]].copy()
        base = base.rename(columns={TARGET_COL: 'density_q1'})

        for i, d in enumerate(dfs[1:], 2):
            base = base.merge(
                d[['Subject_ID', TARGET_COL]].rename(columns={TARGET_COL: f'density_q{i}'}),
                on='Subject_ID', how='inner'
            )

        den_cols = [c for c in base.columns if c.startswith('density_q')]
        base['Density'] = base[den_cols].mean(axis=1)
        base['Distance'] = dist
        base['Real_Subject_ID'] = base['Subject_ID'].map(eye_to_subject)

        long_records.append(base[['Subject_ID', 'Real_Subject_ID', 'Eye', 'Distance', 'Density'] +
                                list(FEATURE_MAP.values())])

    df_long = pd.concat(long_records, ignore_index=True)
    df_long = df_long.rename(columns={
        'Real_Subject_ID': 'Subject_ID',
        'Subject_ID': 'Eye_ID'
    })
    return df_long


def fill_na(df, cols):
    for col in cols:
        if df[col].isna().any():
            df[col].fillna(df[col].median(), inplace=True)
    return df


def zscore_global(s):
    return (s - s.mean()) / s.std()


# ============================================================
# LMM 拟合
# ============================================================
def fit_lmm(df_long):
    """拟合单一 LMM，并返回每个偏心率处 AL 的边际效应"""
    # 只保留需要的列，处理缺失值
    cols = ['Subject_ID', 'Eye_ID', 'Eye', 'Distance', 'Density', FEATURE_MAP['AL'],
            FEATURE_MAP['Age'], FEATURE_MAP['Gender']]
    df = df_long[cols].copy()
    df = fill_na(df, [FEATURE_MAP['AL'], FEATURE_MAP['Age']])

    # 全局 Z-score 标准化 Density、AL、Age
    df['Density_z'] = zscore_global(df['Density'])
    df['AL_z'] = zscore_global(df[FEATURE_MAP['AL']])
    df['Age_z'] = zscore_global(df[FEATURE_MAP['Age']])

    distances = sorted(df['Distance'].unique())
    print(f"  Distances: {distances}")
    print(f"  Records: {len(df)}, Subjects: {df['Subject_ID'].nunique()}, Eyes: {df['Eye_ID'].nunique()}")

    # 拟合单一 LMM（REML）
    formula = 'Density_z ~ C(Distance) * AL_z + Age_z + Gender + Eye'
    try:
        model = smf.mixedlm(formula, df, groups=df['Subject_ID'])
        fit = model.fit(reml=True)
        print("  LMM fitted successfully (REML)")
    except Exception as e:
        raise RuntimeError(f"LMM fitting failed: {e}")

    params = fit.params
    pvalues = fit.pvalues
    exog_names = list(fit.model.exog_names)

    # 计算每个距离的 AL 边际效应
    results = []
    raw_pvals = []
    for dist in distances:
        # 构造对比：AL_z + C(Distance)[T.dist]:AL_z
        al_main = 'AL_z'
        inter_name = f'C(Distance)[T.{dist}]:AL_z'

        contrast = np.zeros(len(exog_names))
        contrast[exog_names.index(al_main)] = 1.0
        if inter_name in exog_names:
            contrast[exog_names.index(inter_name)] = 1.0

        tt = fit.t_test(contrast.reshape(1, -1))
        beta = float(tt.effect)
        pval = float(tt.pvalue)
        ci_low, ci_high = tt.conf_int()[0]

        results.append({
            'Distance': dist,
            'Beta_AL': beta,
            'P_AL': pval,
            'CI_Lower': ci_low,
            'CI_Upper': ci_high
        })
        raw_pvals.append(pval)

    # FDR 校正
    _, fdr_pvals, _, _ = multipletests(raw_pvals, alpha=0.05, method='fdr_bh')
    for i, r in enumerate(results):
        r['P_AL_FDR'] = fdr_pvals[i]

    # ICC（整体模型）
    var_random = fit.cov_re.iloc[0, 0] if hasattr(fit, 'cov_re') else 0.0
    var_resid = fit.scale
    icc = var_random / (var_random + var_resid) if (var_random + var_resid) > 0 else np.nan

    # OES
    for r in results:
        sig = 1.0 if r['P_AL_FDR'] < 0.05 else 0.0
        r['ICC'] = icc
        r['OES'] = abs(r['Beta_AL']) / max(icc, 0.01) * sig

    # 模型 R2
    r2_marginal, r2_conditional = calc_r2_marginal_conditional(fit)

    # 残差用于 Q-Q
    df['pred'] = fit.predict(df)
    residuals = df['Density_z'] - df['pred']

    return pd.DataFrame(results), fit, icc, r2_marginal, r2_conditional, residuals.values


def calc_r2_marginal_conditional(fit):
    """Nakagawa & Schielzeth R2"""
    exog = fit.model.exog
    fixed_params = fit.params[fit.model.exog_names]
    fixed_pred = exog @ fixed_params
    var_fixed = np.var(fixed_pred, ddof=0)
    var_random = fit.cov_re.iloc[0, 0] if hasattr(fit, 'cov_re') else 0.0
    var_resid = fit.scale
    total = var_fixed + var_random + var_resid
    r2_marginal = var_fixed / total if total > 0 else np.nan
    r2_conditional = (var_fixed + var_random) / total if total > 0 else np.nan
    return r2_marginal, r2_conditional


# ============================================================
# 可视化
# ============================================================
def plot_results(df_res, residuals):
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    fig.suptitle('SR0530 LMM Kimi v2.0: Single LMM with Distance x AL Interaction', fontsize=14, fontweight='bold')

    colors = ['#e74c3c' if p < 0.05 else '#95a5a6' for p in df_res['P_AL_FDR']]

    # A. Marginal AL beta
    ax = axes[0, 0]
    ax.bar([str(d) for d in df_res['Distance']], df_res['Beta_AL'], color=colors, edgecolor='black')
    ax.axhline(0, color='black', linewidth=0.8)
    ax.set_xlabel('Distance (mm)')
    ax.set_ylabel('Standardized beta (AL)')
    ax.set_title('A. Marginal AL Effect by Distance')
    ax.tick_params(axis='x', rotation=45)

    # B. 95% CI
    ax = axes[0, 1]
    x = np.arange(len(df_res))
    ax.errorbar(x, df_res['Beta_AL'],
                yerr=[df_res['Beta_AL'] - df_res['CI_Lower'],
                      df_res['CI_Upper'] - df_res['Beta_AL']],
                fmt='o', color='#3498db', ecolor='#95a5a6', capsize=4, linewidth=2)
    ax.axhline(0, color='black', linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{d:.1f}" for d in df_res['Distance']], rotation=45)
    ax.set_xlabel('Distance (mm)')
    ax.set_ylabel('Standardized beta (AL)')
    ax.set_title('B. 95% CI of Marginal AL Effect')

    # C. OES
    ax = axes[0, 2]
    ax.bar([str(d) for d in df_res['Distance']], df_res['OES'], color='#9b59b6', edgecolor='black')
    ax.set_xlabel('Distance (mm)')
    ax.set_ylabel('OES')
    ax.set_title('C. Optimal Eccentricity Score (OES)')
    ax.tick_params(axis='x', rotation=45)

    # D. -log10 FDR P
    ax = axes[1, 0]
    ax.bar([str(d) for d in df_res['Distance']], -np.log10(df_res['P_AL_FDR'] + 1e-10), color='#e67e22', edgecolor='black')
    ax.axhline(-np.log10(0.05), color='red', linestyle='--', linewidth=0.8, label='FDR=0.05')
    ax.set_xlabel('Distance (mm)')
    ax.set_ylabel('-log10(FDR P)')
    ax.set_title('D. FDR-corrected Significance')
    ax.legend()
    ax.tick_params(axis='x', rotation=45)

    # E. ICC
    ax = axes[1, 1]
    ax.bar([str(d) for d in df_res['Distance']], df_res['ICC'], color='#16a085', edgecolor='black')
    ax.set_xlabel('Distance (mm)')
    ax.set_ylabel('ICC')
    ax.set_title('E. Intraclass Correlation Coefficient')
    ax.tick_params(axis='x', rotation=45)

    # F. Q-Q plot of residuals
    ax = axes[1, 2]
    stats.probplot(residuals, dist="norm", plot=ax)
    ax.set_title('F. Q-Q Plot of Residuals')
    ax.grid(True, alpha=0.3)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    fig_path = os.path.join(OUT_DIR, 'SR0530_LMM_kimi_v2_Results.png')
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  --> Saved: {fig_path}")


# ============================================================
# MD 报告
# ============================================================
def generate_report(df_res, icc, r2_marginal, r2_conditional):
    best_dist_oes = df_res.loc[df_res['OES'].idxmax(), 'Distance']
    best_dist_beta = df_res.loc[df_res['Beta_AL'].abs().idxmax(), 'Distance']

    md = []
    md.append("# SR0530 Task 1 LMM Report (Kimi v2.0)\n\n")
    md.append("> **目标**：使用单一多水平 LMM（Distance x AL 交互）筛选 1.0-6.0 mm 中最优靶点偏心率。\n")
    md.append("> **模型**：Density_z ~ C(Distance) * AL_z + Age_z + Gender + Eye + (1 | Subject_ID)，REML。\n")
    md.append("> **数据**：genData/CleanDataRoi（44 ROI，聚合为 11 个距离，每距离 4 象限取平均）。\n\n")

    md.append("---\n\n")
    md.append("## 一、模型整体信息\n\n")
    md.append(f"- **整体 ICC**: {icc:.4f}\n")
    md.append(f"- **Marginal R2**: {r2_marginal:.4f}\n")
    md.append(f"- **Conditional R2**: {r2_conditional:.4f}\n\n")

    md.append("## 二、各偏心率 AL 边际效应\n\n")
    md.append("| 距离 (mm) | beta_AL* | P_raw | P_FDR | 95% CI Lower | 95% CI Upper | ICC | OES | Significant |\n")
    md.append("|-----------|----------|-------|-------|--------------|--------------|-----|-----|-------------|\n")
    for _, row in df_res.iterrows():
        sig = "⭐" if row['P_AL_FDR'] < 0.05 else ""
        md.append(f"| {row['Distance']:.1f} | {row['Beta_AL']:.3f} | {row['P_AL']:.4f} | "
                  f"{row['P_AL_FDR']:.4f} | {row['CI_Lower']:.3f} | {row['CI_Upper']:.3f} | "
                  f"{row['ICC']:.3f} | {row['OES']:.3f} | {sig} |\n")

    md.append(f"\n**按 |beta_AL| 最大**: **{best_dist_beta:.1f} mm**\n")
    md.append(f"**按 OES 最高**: **{best_dist_oes:.1f} mm**\n\n")

    md.append("## 三、OES 计算说明\n\n")
    md.append("OES_j = |beta_AL,j*| / max(ICC_j, 0.01) * I(P_FDR,j < 0.05)\n\n")
    md.append("- beta_AL* 为全局标准化后的 AL 边际效应系数。\n")
    md.append("- ICC 采用整体模型的随机效应方差与残差方差计算。\n")
    md.append("- P 值经 Benjamini-Hochberg FDR 校正，alpha=0.05。\n\n")

    md.append("## 四、可视化\n\n")
    md.append("![LMM Results](genData/sum/SR0530_LMM_kimi_v2_Results.png)\n\n")

    md.append("---\n\n")
    md.append("*Report generated by SR_LMM_kimi_v2.py*\n")

    md_path = os.path.join(BASE_DIR, 'SR0530_Task1_LMM_kimi_v2_Report.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(''.join(md))
    print(f"  --> Report: {md_path}")


# ============================================================
# 主程序
# ============================================================
def main():
    print("=" * 75)
    print("SR0530 Task 1: LMM Analysis (Kimi v2.0)")
    print("Single LMM with Distance x AL Interaction + FDR + OES")
    print("=" * 75)

    print("\nStep 1: Loading and aggregating data...")
    df_long = load_and_aggregate()

    print("\nStep 2: Fitting single LMM...")
    df_res, fit, icc, r2_marginal, r2_conditional, residuals = fit_lmm(df_long)

    print("\nStep 3: Results by distance:")
    for _, row in df_res.iterrows():
        sig = "*" if row['P_AL_FDR'] < 0.05 else ""
        print(f"  {row['Distance']:.1f}mm | beta={row['Beta_AL']:+.3f} | "
              f"P_raw={row['P_AL']:.4f} P_fdr={row['P_AL_FDR']:.4f} {sig} | "
              f"CI=[{row['CI_Lower']:.3f}, {row['CI_Upper']:.3f}] | OES={row['OES']:.3f}")

    print(f"\n  Overall ICC={icc:.4f}, Marginal R2={r2_marginal:.4f}, Conditional R2={r2_conditional:.4f}")

    print("\nStep 4: Saving results...")
    csv_path = os.path.join(OUT_DIR, 'SR0530_LMM_kimi_v2_Results.csv')
    df_res.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"  --> CSV: {csv_path}")

    print("\nStep 5: Generating figures...")
    plot_results(df_res, residuals)

    print("\nStep 6: Generating MD report...")
    generate_report(df_res, icc, r2_marginal, r2_conditional)

    print("\n" + "=" * 75)
    print("Task 1 complete!")
    print("=" * 75)


if __name__ == '__main__':
    main()
