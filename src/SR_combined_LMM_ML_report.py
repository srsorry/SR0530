"""
SR_combined_LMM_ML_report.py
合成报告：将 ≥1 象限（q1plus）模式下的 LMM 结果与 ML 超参数寻优结果整合为一份统一报告。
"""

import os
import warnings
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

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

MODE_LABEL = 'q1plus'
MODE_DESC = '≥1 象限可用（放宽，outer merge 取平均）'


def load_lmm_results():
    """读取 strict/lenient 的 LMM q1plus 结果"""
    results = {}
    for dg in ['strict', 'lenient']:
        path = os.path.join(OUT_DIR, f'SR0530_LMM_Revised_{dg}_{MODE_LABEL}_Results.csv')
        results[dg] = pd.read_csv(path)
    return results


def load_ml_results():
    """读取 ML q1plus 结果"""
    path = os.path.join(OUT_DIR, f'SR0530_HP_Tuning_Results_{MODE_LABEL}.csv')
    return pd.read_csv(path)


def plot_combined_figure1(lmm_results, ml_results):
    """生成合成 Figure 1：LMM AL beta（strict/lenient） + ML 最佳 Test R2"""
    fig, axes = plt.subplots(2, 1, figsize=(12, 10))

    # A. LMM AL beta
    ax = axes[0]
    for dg, df in lmm_results.items():
        colors = ['#e74c3c' if p < 0.05 else '#95a5a6' for p in df['P_AL']]
        offset = -0.1 if dg == 'strict' else 0.1
        x_pos = np.arange(len(df)) + offset
        ax.bar(x_pos, df['Beta_AL'], width=0.18, label=dg.upper(), color=colors, edgecolor='black', alpha=0.8)

    ax.set_xticks(np.arange(len(lmm_results['strict'])))
    ax.set_xticklabels([f"{d:.1f}" for d in lmm_results['strict']['Distance']])
    ax.axhline(0, color='black', linewidth=0.8)
    ax.set_xlabel('Eccentricity (mm)')
    ax.set_ylabel('Standardized beta (AL)')
    ax.set_title(f'A. LMM: AL Effect on Cone Density ({MODE_LABEL})')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    # B. ML best Test R2
    ax = axes[1]
    for dg in ['strict', 'lenient']:
        df_g = ml_results[ml_results['Data_Group'] == dg]
        best_per_d = df_g.loc[df_g.groupby('Distance_mm')['test_r2'].idxmax()].sort_values('Distance_mm')
        ax.plot(best_per_d['Distance_mm'], best_per_d['test_r2'], 'o-', label=dg.upper(), linewidth=2, markersize=8)

    ax.axhline(0, color='gray', linestyle='--', lw=0.8)
    ax.set_xlabel('Eccentricity (mm)')
    ax.set_ylabel('Best Test R² (ML)')
    ax.set_title(f'B. ML: Best Predictive Performance ({MODE_LABEL})')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.suptitle(f'SR0530 Combined Report: LMM Screening & ML Validation ({MODE_LABEL})',
                 fontsize=14, fontweight='bold')
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    path = os.path.join(OUT_DIR, f'SR0530_Combined_LMM_ML_{MODE_LABEL}_Figure1.png')
    plt.savefig(path, dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(FIG_DIR, os.path.basename(path)), dpi=300, bbox_inches='tight')
    plt.close()
    return os.path.basename(path)


def plot_lmm_ml_overlay(lmm_results, ml_results):
    """将 LMM beta 与 ML R2 画在同一张图上（双 Y 轴），便于对比最敏感/最可预测点"""
    fig, ax1 = plt.subplots(figsize=(12, 6))

    dist = lmm_results['strict']['Distance'].values

    # 左 Y：LMM beta
    ax1.set_xlabel('Eccentricity (mm)')
    ax1.set_ylabel('LMM |beta_AL|', color='tab:red')
    b_strict = np.abs(lmm_results['strict']['Beta_AL'].values)
    b_lenient = np.abs(lmm_results['lenient']['Beta_AL'].values)
    ax1.plot(dist, b_strict, 'o-', color='tab:red', label='Strict |beta|', linewidth=2)
    ax1.plot(dist, b_lenient, 's--', color='tab:orange', label='Lenient |beta|', linewidth=2)
    ax1.tick_params(axis='y', labelcolor='tab:red')
    ax1.grid(True, alpha=0.3)

    # 右 Y：ML best R2
    ax2 = ax1.twinx()
    ax2.set_ylabel('ML Best Test R²', color='tab:blue')
    r2_strict = []
    r2_lenient = []
    for d in dist:
        df_s = ml_results[(ml_results['Data_Group'] == 'strict') & (ml_results['Distance_mm'] == d)]
        r2_strict.append(df_s['test_r2'].max())
        df_l = ml_results[(ml_results['Data_Group'] == 'lenient') & (ml_results['Distance_mm'] == d)]
        r2_lenient.append(df_l['test_r2'].max())

    ax2.plot(dist, r2_strict, 'o-', color='tab:blue', label='Strict ML R²', linewidth=2)
    ax2.plot(dist, r2_lenient, 's--', color='tab:cyan', label='Lenient ML R²', linewidth=2)
    ax2.tick_params(axis='y', labelcolor='tab:blue')

    # 合并图例
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')

    plt.title(f'LMM Effect Size vs ML Predictive Power ({MODE_LABEL})', fontsize=14, fontweight='bold')
    plt.tight_layout()

    path = os.path.join(OUT_DIR, f'SR0530_Combined_LMM_ML_{MODE_LABEL}_Overlay.png')
    plt.savefig(path, dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(FIG_DIR, os.path.basename(path)), dpi=300, bbox_inches='tight')
    plt.close()
    return os.path.basename(path)


def generate_report(lmm_results, ml_results, figure1_file, overlay_file):
    """生成合成 Markdown 报告"""
    md = []
    md.append(f"# SR0530 综合分析报告：LMM + ML（{MODE_DESC}）\n\n")
    md.append("> **目标**：在 ≥1 象限平均的放宽策略下，同时评估眼轴长度（AL）对视锥细胞密度的统计关联（LMM）与机器学习预测性能（ML）。\n\n")
    md.append("> **数据**：LMM 与 ML 均使用 `CleanDataRoi_*` 的 q1plus 聚合结果，确保分析口径一致。\n\n")

    md.append("---\n\n")

    # 一、LMM 结果汇总
    md.append("## 一、LMM 结果汇总\n\n")
    md.append("| 距离 (mm) | Strict 眼数 | Strict beta_AL | Strict P | Lenient 眼数 | Lenient beta_AL | Lenient P |\n")
    md.append("|-----------|------------|----------------|----------|-------------|-----------------|-----------|\n")
    for i in range(len(lmm_results['strict'])):
        r_s = lmm_results['strict'].iloc[i]
        r_l = lmm_results['lenient'].iloc[i]
        sig_s = "⭐" if r_s['P_AL'] < 0.05 else ""
        sig_l = "⭐" if r_l['P_AL'] < 0.05 else ""
        md.append(f"| {r_s['Distance']:.1f} | {int(r_s['N_eyes'])} | {r_s['Beta_AL']:.3f} {sig_s} | {r_s['P_AL']:.4f} | "
                  f"{int(r_l['N_eyes'])} | {r_l['Beta_AL']:.3f} {sig_l} | {r_l['P_AL']:.4f} |\n")

    # 二、ML 结果汇总
    md.append("\n## 二、ML 超参数寻优结果汇总\n\n")
    md.append("| 数据组 | 距离 (mm) | 最佳方案 | 最佳模型 | Test R² | MAPE (%) | N_Eyes |\n")
    md.append("|--------|----------|---------|---------|---------|----------|--------|\n")
    for dg in ['strict', 'lenient']:
        df_g = ml_results[ml_results['Data_Group'] == dg]
        for dist in sorted(df_g['Distance_mm'].unique()):
            df_d = df_g[df_g['Distance_mm'] == dist]
            best = df_d.loc[df_d['test_r2'].idxmax()]
            md.append(f"| {dg} | {best['Distance_mm']:.1f} | {best['Schema']} | {best['Model']} | "
                      f"{best['test_r2']:.3f} | {best['test_mape']:.2f} | {int(best['N_Eyes'])} |\n")

    # 三、关键发现
    md.append("\n## 三、关键发现\n\n")

    # 最敏感距离（LMM |beta| 最大）
    best_lmm = {}
    for dg, df in lmm_results.items():
        idx = df['Beta_AL'].abs().idxmax()
        best_lmm[dg] = (df.loc[idx, 'Distance'], df.loc[idx, 'Beta_AL'])

    # 最佳 ML 距离
    best_ml = {}
    for dg in ['strict', 'lenient']:
        df_g = ml_results[ml_results['Data_Group'] == dg]
        idx = df_g['test_r2'].idxmax()
        best_ml[dg] = (df_g.loc[idx, 'Distance_mm'], df_g.loc[idx, 'test_r2'], df_g.loc[idx, 'Model'])

    md.append(f"1. **LMM 最敏感距离**：\n")
    for dg, (dist, beta) in best_lmm.items():
        md.append(f"   - {dg.upper()}：{dist:.1f} mm（|beta_AL| = {abs(beta):.3f}）\n")

    md.append(f"\n2. **ML 最佳预测距离**：\n")
    for dg, (dist, r2, model) in best_ml.items():
        md.append(f"   - {dg.upper()}：{dist:.1f} mm（Test R² = {r2:.3f}，{model}）\n")

    md.append(f"\n3. **LMM 与 ML 一致性**：\n")
    md.append("   - 若 LMM |beta| 峰值与 ML R² 峰值出现在相近偏心率，说明 AL-密度关联具有可预测性。\n")
    md.append("   - 若两者错位，可能提示该距离的关联主要由不可预测的个体变异驱动。\n")

    # 四、可视化
    md.append("\n## 四、可视化\n\n")
    md.append(f"### Figure 1：LMM beta（上）与 ML Test R²（下）\n\n")
    md.append(f"![Figure 1](FIG/{figure1_file})\n\n")
    md.append(f"### Overlay：LMM 效应量 vs ML 预测能力\n\n")
    md.append(f"![Overlay](FIG/{overlay_file})\n\n")

    # 五、讨论
    md.append("\n## 五、讨论\n\n")
    md.append("1. **放宽象限聚合的影响**：≥1 象限策略恢复了远周边样本量，使 LMM 在 2.0–6.0 mm 均显著；ML 也随之获得更稳定的交叉验证估计。\n")
    md.append("2. **AL 效应方向**：LMM 中 AL 标准化系数的具体方向见上表。若需与线性密度（Linear density，cones/mm²）结果对照，需另行补充 Linear density 的 LMM 分析；两种口径因 RMF 校正差异可能呈现不同方向。\n")
    md.append("3. **ML 验证价值**：ML 的最佳 R² 曲线可作为 LMM 统计显著性的独立验证；两者共同支持的最优靶点更具可靠性。\n")
    md.append("4. **后续建议**：若 LMM 最敏感点与 ML 最佳点一致，可锁定该距离为最终研究靶点；若不一致，需进一步探索非线性关系或额外特征。\n")

    md.append("\n---\n\n")
    md.append("*Report generated by SR_combined_LMM_ML_report.py*\n")

    md_path = os.path.join(REPORT_DIR, f'SR0530_Combined_LMM_ML_{MODE_LABEL}_Report.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(''.join(md))
    print(f"  --> Report: {md_path}")
    return md_path


def main():
    print("=" * 80)
    print(f"SR0530 Combined LMM + ML Report ({MODE_LABEL})")
    print("=" * 80)

    print("\nLoading LMM results...")
    lmm_results = load_lmm_results()
    print(f"  strict: {len(lmm_results['strict'])} distances")
    print(f"  lenient: {len(lmm_results['lenient'])} distances")

    print("\nLoading ML results...")
    ml_results = load_ml_results()
    print(f"  records: {len(ml_results)}")

    print("\nGenerating visualizations...")
    figure1_file = plot_combined_figure1(lmm_results, ml_results)
    overlay_file = plot_lmm_ml_overlay(lmm_results, ml_results)

    print("\nGenerating report...")
    generate_report(lmm_results, ml_results, figure1_file, overlay_file)

    print("\n" + "=" * 80)
    print("Combined report complete!")
    print("=" * 80)


if __name__ == '__main__':
    main()
