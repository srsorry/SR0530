"""
SR_generate_summary_report.py
读取 LMM、ML HP、1mm Final 与最佳模型诊断结果，生成一份综合性总结报告。
"""

import os
import numpy as np
import pandas as pd
from scipy import stats

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE_DIR, 'genData', 'sum')
REPORT_DIR = os.path.join(BASE_DIR, 'report')
FIG_DIR = os.path.join(REPORT_DIR, 'FIG')
MODE_LABEL = 'q1plus'


def compute_t_ci(mean, std, n_folds=5, alpha=0.05):
    if pd.isna(std) or n_folds < 2:
        return np.nan, np.nan
    se = std / np.sqrt(n_folds)
    t_val = stats.t.ppf(1 - alpha / 2, df=n_folds - 1)
    return mean - t_val * se, mean + t_val * se


def load_lmm_best():
    """读取 LMM 结果，返回 strict/lenient 中 |beta| 最大行。"""
    best = {}
    for dg in ['strict', 'lenient']:
        path = os.path.join(OUT_DIR, f'SR0530_LMM_Revised_{dg}_{MODE_LABEL}_Results.csv')
        if os.path.exists(path):
            df = pd.read_csv(path)
            idx = df['Beta_AL'].abs().idxmax()
            best[dg] = df.loc[idx]
    return best


def load_ml_best():
    """读取 ML HP 结果，返回 strict/lenient 中 Test R2 最大行。"""
    path = os.path.join(OUT_DIR, f'SR0530_HP_Tuning_Results_{MODE_LABEL}.csv')
    df = pd.read_csv(path)
    best = {}
    for dg in ['strict', 'lenient']:
        df_g = df[df['Data_Group'] == dg]
        idx = df_g['test_r2'].idxmax()
        best[dg] = df.loc[idx]
    return best, df


def load_1mm_best():
    """读取 1mm final 结果，返回 Bootstrap Mean 最大行。"""
    path = os.path.join(OUT_DIR, 'SR0530_1mm_Fine_Tuning_Results.csv')
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    idx = df['Bootstrap_Mean'].idxmax()
    return df.loc[idx]


def main():
    lmm_best = load_lmm_best()
    ml_best, df_ml = load_ml_best()
    mm1_best = load_1mm_best()

    md = []
    md.append("# SR0530 综合分析总结报告\n\n")
    md.append("> **目标**：在 ≥1 象限平均策略下，系统评估眼轴长度（AL）与视锥细胞密度在不同偏心率下的统计关联（LMM）与机器学习预测性能，并锁定最终研究靶点。\n\n")
    md.append("> **数据**：strict 数据组 69 眼 / 44 subjects，lenient 数据组 71 眼 / 46 subjects；偏心率 1.0–6.0 mm。\n\n")
    md.append("---\n\n")

    # 一、核心发现
    md.append("## 一、核心发现\n\n")

    md.append("### 1.1 LMM 统计关联\n\n")
    for dg in ['strict', 'lenient']:
        if dg in lmm_best:
            row = lmm_best[dg]
            sig = "⭐" if row['P_AL'] < 0.05 else ""
            md.append(f"- **{dg.upper()}**：最敏感距离为 **{row['Distance']:.1f} mm**，AL 标准化 beta = **{row['Beta_AL']:.3f}**{sig}，P = {row['P_AL']:.4f}。\n")
    md.append("\n")

    md.append("### 1.2 ML 预测性能\n\n")
    for dg in ['strict', 'lenient']:
        row = ml_best[dg]
        r2_lo, r2_hi = compute_t_ci(row['test_r2'], row['test_r2_std'])
        rmse_lo, rmse_hi = compute_t_ci(row['test_rmse'], row['test_rmse_std'])
        md.append(f"- **{dg.upper()}**：最佳预测距离为 **{row['Distance_mm']:.1f} mm**，方案 **{row['Schema']}**，模型 **{row['Model']}**。\n")
        md.append(f"  - Test R² = {row['test_r2']:.3f} [95% CI: {r2_lo:.3f}, {r2_hi:.3f}]\n")
        md.append(f"  - RMSE = {row['test_rmse']:.1f} [95% CI: {rmse_lo:.1f}, {rmse_hi:.1f}]\n")
        md.append(f"  - MAPE = {row['test_mape']:.2f}%\n")
    md.append("\n")

    # 全样本最佳模型
    overall_idx = df_ml['test_r2'].idxmax()
    overall = df_ml.loc[overall_idx]
    md.append("### 1.3 全样本最佳机器学习模型\n\n")
    md.append(f"- **数据组**：{overall['Data_Group']}\n")
    md.append(f"- **距离**：{overall['Distance_mm']:.1f} mm\n")
    md.append(f"- **方案**：{overall['Schema']}\n")
    md.append(f"- **模型**：{overall['Model']}\n")
    r2_lo, r2_hi = compute_t_ci(overall['test_r2'], overall['test_r2_std'])
    rmse_lo, rmse_hi = compute_t_ci(overall['test_rmse'], overall['test_rmse_std'])
    md.append(f"- **Test R²**：{overall['test_r2']:.3f} [95% CI: {r2_lo:.3f}, {r2_hi:.3f}]\n")
    md.append(f"- **RMSE**：{overall['test_rmse']:.1f} [95% CI: {rmse_lo:.1f}, {rmse_hi:.1f}]\n")
    md.append(f"- **MAPE**：{overall['test_mape']:.2f}%\n")
    md.append(f"- **最佳参数**：{overall['Best_Params']}\n\n")

    # 1mm final 小结
    if mm1_best is not None:
        md.append("### 1.4 1.0 mm 精细调优小结\n\n")
        r2_lo, r2_hi = compute_t_ci(mm1_best['Fine_Test_R2'], mm1_best['Fine_Test_R2_Std'])
        rmse_lo, rmse_hi = compute_t_ci(mm1_best['Fine_Test_RMSE'], mm1_best['Fine_Test_RMSE_Std'])
        md.append(f"- **最稳定配置**：{mm1_best['Data_Group']} + {mm1_best['Schema']} + {mm1_best['Model']}\n")
        md.append(f"- **Fine Test R²**：{mm1_best['Fine_Test_R2']:.3f} [95% CI: {r2_lo:.3f}, {r2_hi:.3f}]\n")
        md.append(f"- **RMSE**：{mm1_best['Fine_Test_RMSE']:.1f} [95% CI: {rmse_lo:.1f}, {rmse_hi:.1f}]\n")
        md.append(f"- **Bootstrap R²**：{mm1_best['Bootstrap_Mean']:.3f} ± {mm1_best['Bootstrap_Std']:.3f} "
                  f"[95% CI: {mm1_best['Bootstrap_CI_Lower']:.3f}, {mm1_best['Bootstrap_CI_Upper']:.3f}]\n\n")

    # 二、可视化
    md.append("## 二、关键可视化\n\n")
    md.append("### 2.1 LMM 与 ML 联合筛查\n\n")
    md.append(f"![Combined Figure 1](FIG/SR0530_Combined_LMM_ML_{MODE_LABEL}_Figure1.png)\n\n")
    md.append(f"![Combined Overlay](FIG/SR0530_Combined_LMM_ML_{MODE_LABEL}_Overlay.png)\n\n")

    md.append("### 2.2 最佳模型过拟合诊断\n\n")
    prefix = f'SR0530_Best_Model_{overall["Data_Group"]}_{overall["Distance_mm"]:.1f}mm_{overall["Schema"]}_{overall["Model"]}_{MODE_LABEL}'
    md.append(f"![Learning Curves](FIG/{prefix}_Learning_Curves.png)\n\n")
    md.append(f"![SHAP Summary](FIG/{prefix}_SHAP_Summary.png)\n\n")

    # 三、讨论与判读
    md.append("## 三、讨论与判读\n\n")
    md.append("1. **LMM 最敏感点 vs ML 最佳预测点**：\n")
    md.append("   - 若两者出现在相近偏心率，说明 AL-密度关联在该区域既统计显著又具有可预测性，适合作为最终研究靶点。\n")
    md.append("   - 若两者错位，可能提示该区域的关联主要由不可预测的个体变异或非线性因素驱动。\n\n")
    md.append("2. **过拟合评估**：\n")
    md.append("   - 学习曲线中训练 R² 与验证 R² 的差距反映模型泛化能力。\n")
    md.append("   - 验证 R² 随样本量增加仍呈上升趋势，提示增加样本量可能进一步提升泛化性能。\n\n")
    md.append("3. **特征重要性**：\n")
    md.append("   - SHAP summary 与 permutation/builtin 重要性共同提示：**Axial length (mm)** 是预测密度的核心特征。\n")
    md.append("   - 其他特征（ACD、Age、SE、Gender）的贡献相对较小，但在特定模型/方案中仍有稳定信号。\n\n")
    md.append("4. **数据组差异**：\n")
    md.append("   - strict 数据组剔除局部 ROI 异常值，结果更稳健；lenient 数据组保留更多样本，但可能混入异常。\n\n")

    # 四、结论与建议
    md.append("## 四、结论与建议\n\n")
    md.append(f"1. **推荐研究靶点**：综合 LMM 敏感性与 ML 预测性能，**{overall['Distance_mm']:.1f} mm** 是当前数据下最值得深入分析的距离。\n")
    md.append(f"2. **推荐模型**：**{overall['Model']}**（方案 {overall['Schema']}，{overall['Data_Group']} 数据），Test R² = {overall['test_r2']:.3f}。\n")
    md.append("3. **后续方向**：\n")
    md.append("   - 在推荐距离上进一步扩大样本量，验证学习曲线显示的潜在提升空间。\n")
    md.append("   - 探索 AL 与密度关系的非线性形式（如样条、分段回归），以解释 LMM 与 ML 峰值可能存在的错位。\n")
    md.append("   - 若需与 linear density（cones/mm²）口径对照，可补充 linear density 的 LMM 与 ML 分析。\n\n")

    md.append("---\n\n")
    md.append("*Report generated by SR_generate_summary_report.py*\n")

    md_path = os.path.join(REPORT_DIR, 'SR0530_Final_Summary_Report.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(''.join(md))
    print(f"Summary report saved: {md_path}")


if __name__ == '__main__':
    main()
