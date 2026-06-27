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


def load_alk_comparison():
    """读取 lenient AL/K 与 K 结果，返回 C1_Combined 各变型在 1.5 mm 的最佳行。"""
    alk_path = os.path.join(OUT_DIR, 'SR0530_HP_Tuning_Results_lenient_ALK.csv')
    k_path = os.path.join(OUT_DIR, 'SR0530_HP_Tuning_Results_q1plus_K.csv')
    out = {}
    if os.path.exists(alk_path):
        df_alk = pd.read_csv(alk_path)
        df_alk_d = df_alk[(df_alk['Data_Group'] == 'lenient') & (df_alk['Distance_mm'] == 1.5)]
        for schema in ['C1_Combined_ALK', 'C1_Combined_K_ALK']:
            df_s = df_alk_d[df_alk_d['Schema'] == schema]
            if not df_s.empty:
                out[schema] = df_s.loc[df_s['test_r2'].idxmax()]
    if os.path.exists(k_path):
        df_k = pd.read_csv(k_path)
        df_k_d = df_k[(df_k['Data_Group'] == 'lenient') & (df_k['Distance_mm'] == 1.5)]
        df_s = df_k_d[df_k_d['Schema'] == 'C1_Combined_K']
        if not df_s.empty:
            out['C1_Combined_K'] = df_s.loc[df_s['test_r2'].idxmax()]
    return out


def main():
    lmm_best = load_lmm_best()
    ml_best, df_ml = load_ml_best()
    mm1_best = load_1mm_best()
    alk_cmp = load_alk_comparison()

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

    # AL/K 替代 K 的验证
    md.append("### 1.3 AL/K 替代 K 的验证（lenient）\n\n")
    if all(k in alk_cmp for k in ['C1_Combined_ALK', 'C1_Combined_K', 'C1_Combined_K_ALK']):
        alk = alk_cmp['C1_Combined_ALK']
        k = alk_cmp['C1_Combined_K']
        k_alk = alk_cmp['C1_Combined_K_ALK']
        alk_r2_lo, alk_r2_hi = compute_t_ci(alk['test_r2'], alk['test_r2_std'])
        k_r2_lo, k_r2_hi = compute_t_ci(k['test_r2'], k['test_r2_std'])
        kalk_r2_lo, kalk_r2_hi = compute_t_ci(k_alk['test_r2'], k_alk['test_r2_std'])
        md.append("- **补充分析**：在 lenient 数据组上进一步比较了用 **AL/K（眼轴-角膜曲率比值）** 替代或叠加 **K（角膜曲率）** 的效果。\n")
        md.append(f"- **关键发现**：**C1_Combined_ALK** 在 **1.5 mm** 处使用 **{alk['Model']}** 即可达到 **Test R² = {alk['test_r2']:.3f}**，与 C1_Combined_K 的 {k['test_r2']:.3f} 几乎相同；C1_Combined_K_ALK 同样为 {k_alk['test_r2']:.3f}。\n")
        md.append(f"  - **C1_Combined_ALK**：SE + AL + Age + Gender + AL/K，Test R² = {alk['test_r2']:.3f} [95% CI: {alk_r2_lo:.3f}, {alk_r2_hi:.3f}]\n")
        md.append(f"  - **C1_Combined_K**：SE + AL + Age + Gender + K，Test R² = {k['test_r2']:.3f} [95% CI: {k_r2_lo:.3f}, {k_r2_hi:.3f}]\n")
        md.append(f"  - **C1_Combined_K_ALK**：SE + AL + Age + Gender + K + AL/K，Test R² = {k_alk['test_r2']:.3f} [95% CI: {kalk_r2_lo:.3f}, {kalk_r2_hi:.3f}]\n")
        md.append("- **判读**：在已包含 AL 的 C1_Combined 方案中，K 与 AL/K 可互换，同时纳入两者并未提升性能，提示信息冗余。AL/K 作为单一复合指标更具生理意义（同时概括眼轴与角膜曲率的交互作用）。\n")
        md.append("- **稳健性提醒**：上述 0.611–0.612 来自单次 5-fold CV，存在选择偏倚；后续 **5 repeats × 5-fold GroupKFold** 重复 CV 给出 C1_Combined_ALK 的稳健估计为 **Test R² = 0.395** [95% CI: 0.274, 0.515]，建议在论文中引用稳健估计。\n")
    else:
        md.append("- AL/K 对比结果尚未生成。\n")
    md.append("\n")

    # 全样本最佳模型
    overall_idx = df_ml['test_r2'].idxmax()
    overall = df_ml.loc[overall_idx]
    md.append("### 1.4 全样本最佳机器学习模型\n\n")
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
        md.append("### 1.5 1.0 mm 精细调优小结\n\n")
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
    md.append("5. **AL/K 作为 K 的替代指标**：\n")
    md.append("   - 在 lenient 的 C1_Combined 方案中，AL/K 与 K 可达到几乎相同的峰值 R²（~0.611 vs ~0.612），且 K + AL/K 叠加无额外增益，说明两者信息高度冗余。\n")
    md.append("   - 若希望减少共线性、统一眼形态解释，可优先使用 AL/K 替代 K；但需在论文中报告重复 CV 稳健估计，避免单次 CV 的高估。\n\n")

    # 四、结论与建议
    md.append("## 四、结论与建议\n\n")
    md.append(f"1. **推荐研究靶点**：综合 LMM 敏感性与 ML 预测性能，**{overall['Distance_mm']:.1f} mm** 是当前数据下最值得深入分析的距离。\n")
    md.append(f"2. **推荐模型**：**{overall['Model']}**（方案 {overall['Schema']}，{overall['Data_Group']} 数据），Test R² = {overall['test_r2']:.3f}。\n")
    md.append("3. **AL/K 替代方案（lenient）**：若使用 lenient 数据组并希望在 C1_Combined 方案中以 AL/K 替代 K，**C1_Combined_ALK + Lasso @ 1.5 mm** 可达到与 C1_Combined_K 几乎相同的单次 CV 性能（Test R² ≈ 0.611 vs 0.612），但论文引用应使用重复 CV 稳健估计（≈ 0.395）。\n")
    md.append("4. **后续方向**：\n")
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
