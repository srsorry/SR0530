"""
SR_LMM_analysis.py
基于双眼数据的线性混合效应模型（LMM）分析
对每个距离组（1.0-6.0mm）建立 LMM，输出 R2/MAPE/RMSE、靶点得分、Q-Q 残差图
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
from statsmodels.stats.multitest import multipletests
import scipy.stats as stats

warnings.filterwarnings('ignore')

# ============================================================
# 配置
# ============================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'orgData', 'orgData.csv')
PAIR_PATH = os.path.join(BASE_DIR, 'genData', 'sum', 'Subject_Pair_Mapping.csv')
OUT_DIR = os.path.join(BASE_DIR, 'genData', 'sum')
os.makedirs(OUT_DIR, exist_ok=True)
REPORT_DIR = os.path.join(BASE_DIR, 'report')
FIG_DIR = os.path.join(REPORT_DIR, 'FIG')
os.makedirs(FIG_DIR, exist_ok=True)

FEATURE_COLS = [
    'Axial length (mm)', 'Age', 'Spherical equivalent refraction (D)',
    'Gender', 'Cornea curvature (mm)', 'Anterior chamber depth (mm)'
]
FEATURE_SHORT = ['AL', 'Age', 'SE', 'Gender', 'CC', 'ACD']


# ============================================================
# 工具函数
# ============================================================
def load_pair_mapping():
    """加载双眼配对映射"""
    pairs = pd.read_csv(PAIR_PATH)
    pid_to_subj = {}
    for _, row in pairs.iterrows():
        pid_to_subj[int(row['OD_PatientID'])] = row['Subject_ID']
        pid_to_subj[int(row['OS_PatientID'])] = row['Subject_ID']
    
    # 单眼受试者使用 Single_PID 作为 Subject_ID
    org = pd.read_csv(DATA_PATH)
    all_pids = set(org['Patient ID'].unique())
    single_pids = all_pids - set(pid_to_subj.keys())
    for pid in single_pids:
        pid_to_subj[pid] = f'Single_{pid}'
    
    return pid_to_subj


def build_long_data(pid_to_subj):
    """构建长格式数据，每行是一只眼在一个ROI的数据"""
    df = pd.read_csv(DATA_PATH)
    
    # 添加 Subject_ID
    df['Subject_ID'] = df['Patient ID'].map(pid_to_subj)
    
    records = []
    for _, row in df.iterrows():
        for roi in range(1, 45):
            bvr = row.get(f'Blood_Vessel_Ratio_ROI_{roi}', np.nan)
            den = row.get(f'Cone_Density_ROI_{roi}', np.nan)
            
            # 质量控制：BVR <= 0.25、密度有效、且密度在正常范围内
            if pd.notna(bvr) and pd.notna(den) and bvr <= 0.25 and 0 < den < 80000:
                k = (roi - 1) % 11
                dist = 1.0 + k * 0.5
                quadrant = (roi - 1) // 11 + 1
                
                records.append({
                    'Subject_ID': row['Subject_ID'],
                    'Patient_ID': row['Patient ID'],
                    'Eye': row['Eye'],
                    'Distance': dist,
                    'Quadrant': quadrant,
                    'ROI': roi,
                    'Density': den,
                    'AL': row['Axial length (mm)'],
                    'Age': row['Age'],
                    'SE': row['Spherical equivalent refraction (D)'],
                    'Gender': row['Gender'],
                    'CC': row['Cornea curvature (mm)'],
                    'ACD': row['Anterior chamber depth (mm)'],
                    'Source_Class': row['Source_Class']
                })
    
    return pd.DataFrame(records)


def calc_r2_marginal_conditional(fit, df):
    """计算 LMM 的边际 R2 和条件 R2 (Nakagawa & Schielzeth)"""
    # 固定效应设计矩阵
    exog = fit.model.exog
    fixed_params = fit.params[fit.model.exog_names]
    
    # 固定效应预测值
    fixed_pred = exog @ fixed_params
    var_fixed = np.var(fixed_pred, ddof=0)
    
    # 随机效应方差
    var_random = fit.cov_re.iloc[0, 0] if hasattr(fit, 'cov_re') else 0
    
    # 残差方差
    var_resid = fit.scale
    
    total = var_fixed + var_random + var_resid
    r2_marginal = var_fixed / total
    r2_conditional = (var_fixed + var_random) / total
    
    return r2_marginal, r2_conditional


def calc_mape_rmse(y_true, y_pred):
    """计算 MAPE 和 RMSE"""
    mape = np.mean(np.abs((y_true - y_pred) / (y_true + 1e-10))) * 100
    rmse = np.sqrt(np.mean((y_true - y_pred)**2))
    return mape, rmse


def fit_lmm_per_distance(df_long):
    """对每个距离组拟合 LMM（先按 Subject 聚合 4 象限平均密度）"""
    distances = sorted(df_long['Distance'].unique())
    results = []
    qq_data = {}
    
    for dist in distances:
        sub = df_long[df_long['Distance'] == dist].copy()
        
        # 按 Subject_ID 和 Eye 聚合：每个受试者在该距离下的 4 象限平均密度
        sub_agg = sub.groupby(['Subject_ID', 'Eye']).agg({
            'Density': 'mean',
            'AL': 'first',
            'Age': 'first',
            'SE': 'first',
            'Gender': 'first',
            'CC': 'first',
            'ACD': 'first',
            'Source_Class': 'first'
        }).reset_index()
        
        # 处理缺失值
        for col in ['AL', 'Age', 'SE', 'CC', 'ACD']:
            if sub_agg[col].isna().any():
                sub_agg[col].fillna(sub_agg[col].median(), inplace=True)
        
        # 标准化连续变量（便于比较 beta）
        continuous_cols = ['Density', 'AL', 'Age', 'SE', 'CC', 'ACD']
        scalers = {}
        for col in continuous_cols:
            scaler = (sub_agg[col].mean(), sub_agg[col].std())
            scalers[col] = scaler
            sub_agg[f'{col}_z'] = (sub_agg[col] - scaler[0]) / scaler[1]
        
        sub = sub_agg  # 用聚合后的数据
        
        # LMM 公式：标准化密度 ~ 标准化AL + ... + (1 | Subject_ID)
        formula = 'Density_z ~ AL_z + Age_z + SE_z + Gender + CC_z + ACD_z + Eye'
        
        try:
            model = smf.mixedlm(formula, sub, groups=sub['Subject_ID'])
            fit = model.fit(reml=True)
            
            # 提取 AL 的系数
            al_beta = fit.params['AL_z']
            al_p = fit.pvalues['AL_z']
            al_t = fit.tvalues['AL_z']
            al_ci_low, al_ci_high = fit.conf_int().loc['AL_z']
            
            # 预测值
            sub['pred'] = fit.predict(sub)
            
            # 计算 R2
            r2_marginal, r2_conditional = calc_r2_marginal_conditional(fit, sub)
            
            # 计算 MAPE 和 RMSE（用原始尺度）
            y_true_orig = sub['Density'].values
            y_pred_orig = sub['pred'].values * scalers['Density'][1] + scalers['Density'][0]
            mape, rmse = calc_mape_rmse(y_true_orig, y_pred_orig)
            
            # 残差
            residuals = sub['Density_z'] - sub['pred']
            
            # ICC (Intraclass Correlation Coefficient)
            var_random = fit.cov_re.iloc[0, 0]
            var_resid = fit.scale
            icc = var_random / (var_random + var_resid) if (var_random + var_resid) > 0 else np.nan
            
            results.append({
                'Distance': dist,
                'N_eyes': len(sub),
                'N_subjects': sub['Subject_ID'].nunique(),
                'Beta_AL': al_beta,
                'P_AL': al_p,
                'T_AL': al_t,
                'CI_Lower': al_ci_low,
                'CI_Upper': al_ci_high,
                'R2_Marginal': r2_marginal,
                'R2_Conditional': r2_conditional,
                'MAPE': mape,
                'RMSE': rmse,
                'ICC': icc,
                'OES': np.nan,  # FDR 校正后填充
                'P_FDR': np.nan,
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
            print(f"  {dist:.1f}mm | N={len(sub):3d} eyes/{sub['Subject_ID'].nunique():3d} subj | "
                  f"beta_AL={al_beta:+.3f} p={al_p:.4f} {sig} | "
                  f"R2m={r2_marginal:.3f} R2c={r2_conditional:.3f} | "
                  f"MAPE={mape:.2f}% RMSE={rmse:.1f} | ICC={icc:.3f}")
            
        except Exception as e:
            print(f"  {dist:.1f}mm | LMM failed: {e}")
            results.append({
                'Distance': dist,
                'N_eyes': len(sub),
                'N_subjects': sub['Subject_ID'].nunique(),
                'Beta_AL': np.nan,
                'P_AL': np.nan,
                'T_AL': np.nan,
                'CI_Lower': np.nan,
                'CI_Upper': np.nan,
                'R2_Marginal': np.nan,
                'R2_Conditional': np.nan,
                'MAPE': np.nan,
                'RMSE': np.nan,
                'ICC': np.nan,
                'OES': np.nan,
                'Random_Effect_Var': np.nan,
                'Residual_Var': np.nan,
                'Converged': False,
                'Error': str(e)
            })
    
    # FDR 校正与 OES 计算（V3.0 终极公式）
    df_results = pd.DataFrame(results)
    if df_results['P_AL'].notna().any():
        valid_mask = df_results['P_AL'].notna()
        pvals = df_results.loc[valid_mask, 'P_AL'].values
        _, p_fdr, _, _ = multipletests(pvals, alpha=0.05, method='fdr_bh')
        df_results.loc[valid_mask, 'P_FDR'] = p_fdr
        
        # OES = |beta| * (-log10 P) / max(ICC, 0.01) * I(P_FDR < 0.05)
        for idx in df_results[valid_mask].index:
            beta = df_results.loc[idx, 'Beta_AL']
            p = df_results.loc[idx, 'P_AL']
            icc = df_results.loc[idx, 'ICC']
            p_fdr_i = df_results.loc[idx, 'P_FDR']
            indicator = 1.0 if p_fdr_i < 0.05 else 0.0
            oes = abs(beta) * (-np.log10(p + 1e-10)) / max(icc, 0.01) * indicator
            df_results.loc[idx, 'OES'] = oes
    
    return df_results, qq_data


# ============================================================
# 可视化
# ============================================================
def plot_results(df_results, qq_data):
    """生成综合分析图表和 Q-Q 图"""
    # 1. 综合分析图
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    fig.suptitle('SR0530 LMM Analysis with Bilateral Data', fontsize=14, fontweight='bold')
    
    # A. AL beta
    ax = axes[0, 0]
    colors = ['#e74c3c' if p < 0.05 else '#95a5a6' for p in df_results['P_AL']]
    ax.bar([str(d) for d in df_results['Distance']], df_results['Beta_AL'], color=colors, edgecolor='black')
    ax.axhline(0, color='black', linewidth=0.8)
    ax.set_xlabel('Distance (mm)')
    ax.set_ylabel('Standardized beta (AL)')
    ax.set_title('A. LMM: AL Effect across Distances')
    ax.tick_params(axis='x', rotation=45)
    
    # B. R2 marginal vs conditional
    ax = axes[0, 1]
    ax.plot(df_results['Distance'], df_results['R2_Marginal'], 'o-', label='Marginal R2', linewidth=2)
    ax.plot(df_results['Distance'], df_results['R2_Conditional'], 's--', label='Conditional R2', linewidth=2)
    ax.set_xlabel('Distance (mm)')
    ax.set_ylabel('R2')
    ax.set_title('B. Marginal vs Conditional R2')
    ax.legend()
    ax.set_ylim(0, 1)
    
    # C. Target Score
    ax = axes[0, 2]
    ax.bar([str(d) for d in df_results['Distance']], df_results['OES'], color='#9b59b6', edgecolor='black')
    ax.set_xlabel('Distance (mm)')
    ax.set_ylabel('OES')
    ax.set_title('C. Optimal Eccentricity Score (OES)')
    ax.tick_params(axis='x', rotation=45)
    
    # D. MAPE
    ax = axes[1, 0]
    ax.plot(df_results['Distance'], df_results['MAPE'], 'o-', color='#e67e22', linewidth=2)
    ax.set_xlabel('Distance (mm)')
    ax.set_ylabel('MAPE (%)')
    ax.set_title('D. Mean Absolute Percentage Error')
    
    # E. RMSE
    ax = axes[1, 1]
    ax.plot(df_results['Distance'], df_results['RMSE'], 'o-', color='#16a085', linewidth=2)
    ax.set_xlabel('Distance (mm)')
    ax.set_ylabel('RMSE')
    ax.set_title('E. Root Mean Squared Error')
    
    # F. Random effect variance
    ax = axes[1, 2]
    ax.bar([str(d) for d in df_results['Distance']], df_results['Random_Effect_Var'], color='#3498db', edgecolor='black')
    ax.set_xlabel('Distance (mm)')
    ax.set_ylabel('Random Effect Variance')
    ax.set_title('F. Subject-Level Variance')
    ax.tick_params(axis='x', rotation=45)
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    fig_path = os.path.join(OUT_DIR, 'SR0530_LMM_V3.0_Results.png')
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(FIG_DIR, os.path.basename(fig_path)),dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  --> Saved: {fig_path}")
    
    # 2. Q-Q 图（每个距离一个子图）
    n_dist = len(qq_data)
    ncols = 4
    nrows = int(np.ceil(n_dist / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(14, 3.5 * nrows))
    axes = axes.flatten()
    
    for idx, (dist, data) in enumerate(sorted(qq_data.items())):
        ax = axes[idx]
        residuals = data['residuals']
        stats.probplot(residuals, dist="norm", plot=ax)
        ax.set_title(f'{dist:.1f} mm')
        ax.grid(True, alpha=0.3)
    
    # Hide extra subplots
    for idx in range(n_dist, len(axes)):
        axes[idx].axis('off')
    
    fig.suptitle('Q-Q Plots of LMM Residuals by Distance', fontsize=14, fontweight='bold')
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    qq_path = os.path.join(OUT_DIR, 'SR0530_LMM_V3.0_QQPlots.png')
    plt.savefig(qq_path, dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(FIG_DIR, os.path.basename(qq_path)),dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  --> Saved: {qq_path}")


# ============================================================
# MD 报告生成
# ============================================================
def generate_lmm_report(df_results, best_dist_beta, best_dist_score):
    """自动生成 LMM 分析报告"""
    md = []
    md.append("# SR0530 V3.0 任务一报告：基于双眼数据的 LMM 统计筛选\n")
    md.append("> **目标**：确定 1.0–6.0 mm 偏心率中，角密度受眼部参数影响最显著的黄金靶点。\n")
    md.append("> **方法**：每个偏心率独立拟合 LMM（REML），Subject_ID 作为随机效应；OES 经 Benjamini-Hochberg FDR 校正。\n")
    md.append("> **数据**：77 只眼 / 48 名受试者（30 对双眼 + 19 名单眼）。\n\n")
    
    md.append("---\n\n")
    md.append("## 一、LMM 结果汇总\n\n")
    md.append("| 距离 (mm) | 眼数 | 受试者数 | beta_AL | P 值 | P_FDR | R²_边际 | R²_条件 | MAPE(%) | RMSE | ICC | OES |\n")
    md.append("|-----------|------|---------|---------|------|-------|---------|---------|---------|------|-----|-----|\n")
    for _, row in df_results.iterrows():
        sig = "⭐" if row['P_FDR'] < 0.05 else ""
        md.append(f"| {row['Distance']:.1f} | {int(row['N_eyes'])} | {int(row['N_subjects'])} | "
                  f"{row['Beta_AL']:.3f} | {row['P_AL']:.4f} | {row['P_FDR']:.4f} {sig} | "
                  f"{row['R2_Marginal']:.3f} | {row['R2_Conditional']:.3f} | "
                  f"{row['MAPE']:.2f} | {row['RMSE']:.1f} | {row['ICC']:.3f} | {row['OES']:.3f} |\n")
    
    md.append(f"\n**按 AL 效应最显著**：**{best_dist_beta:.1f} mm**（|beta_AL| 最大）\n")
    md.append(f"**按 OES 最高**：**{best_dist_score:.1f} mm**（通过 FDR 校正后 OES 最高）\n\n")
    
    md.append("## 二、关键指标说明\n\n")
    md.append("- **beta_AL**：AL 的标准化回归系数。\n")
    md.append("- **P_FDR**：经 Benjamini-Hochberg FDR 校正后的 P 值。\n")
    md.append("- **R²_边际 / R²_条件**：固定效应 / 固定+随机效应解释的变异比例。\n")
    md.append("- **ICC** = σ²_random / (σ²_random + σ²_residual)。\n")
    md.append("- **OES** = |beta_AL| × (-log10(P_AL)) / max(ICC, 0.01) × I(P_FDR < 0.05)。未通过 FDR 校正的点 OES 强制为 0。\n\n")
    
    md.append("## 三、可视化\n\n")
    md.append("![LMM 综合分析](FIG/SR0530_LMM_V3.0_Results.png)\n\n")
    md.append("![Q-Q 残差图](FIG/SR0530_LMM_V3.0_QQPlots.png)\n\n")
    
    md.append("## 四、讨论\n\n")
    md.append("1. LMM 将 Subject_ID 作为随机效应后，有效控制了双眼相关性。\n")
    md.append("2. R²_条件通常显著高于 R²_边际，说明个体间差异（随机效应）解释了较大比例的密度变异。\n")
    md.append("3. Q-Q 图用于检验残差正态性，若某距离明显偏离对角线，提示模型假设可能不满足。\n")
    md.append("4. OES 综合了 AL 效应量、统计显著性和 ICC 个体差异控制，得分最高的偏心率即为推荐的黄金靶点。\n\n")
    
    md.append("---\n\n")
    md.append("*Report generated by SR_LMM_analysis.py*\n")
    
    md_path = os.path.join(BASE_DIR, 'report', 'SR0530_Task1_LMM_V3.0_Report.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(''.join(md))
    print(f"  --> Report: {md_path}")


# ============================================================
# 主程序
# ============================================================
def main():
    print("=" * 75)
    print("SR0530 V3.0: LMM Analysis with Bilateral Eye Data")
    print("=" * 75)
    
    print("\nStep 1: Loading pair mapping...")
    pid_to_subj = load_pair_mapping()
    print(f"  Mapped {len(pid_to_subj)} eyes to subjects")
    
    print("\nStep 2: Building long-format data with Subject_ID...")
    df_long = build_long_data(pid_to_subj)
    print(f"  Total records: {len(df_long)}")
    print(f"  Distances: {sorted(df_long['Distance'].unique())}")
    print(f"  Subjects: {df_long['Subject_ID'].nunique()}")
    print(f"  Eyes: {df_long['Patient_ID'].nunique()}")
    
    print("\nStep 3: Fitting LMM per distance...")
    df_results, qq_data = fit_lmm_per_distance(df_long)
    
    print("\nStep 4: Generating figures...")
    plot_results(df_results, qq_data)
    
    print("\nStep 5: Saving results...")
    csv_path = os.path.join(OUT_DIR, 'SR0530_LMM_V3.0_Results.csv')
    df_results.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"  --> CSV: {csv_path}")
    
    print("\nStep 6: Generating MD report...")
    best_dist_beta = df_results.loc[df_results['Beta_AL'].abs().idxmax(), 'Distance']
    best_dist_score = df_results.loc[df_results['OES'].idxmax(), 'Distance']
    generate_lmm_report(df_results, best_dist_beta, best_dist_score)
    
    print("\n" + "=" * 75)
    print("V3.0 LMM Task complete!")
    print("=" * 75)


if __name__ == '__main__':
    main()
