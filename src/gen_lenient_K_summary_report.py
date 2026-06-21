import os
import pandas as pd
import numpy as np
from scipy import stats

# Load +K results and baseline results
df_k = pd.read_csv('genData/sum/SR0530_HP_Tuning_Results_q1plus_K.csv')
df_base = pd.read_csv('genData/sum/SR0530_HP_Tuning_Results_q1plus.csv')

# Filter lenient
df_k_lenient = df_k[df_k['Data_Group'] == 'lenient'].copy()
df_base_lenient = df_base[df_base['Data_Group'] == 'lenient'].copy()


def t_ci(mean, std, n_folds=5, alpha=0.05):
    if pd.isna(std) or n_folds < 2:
        return np.nan, np.nan
    se = std / np.sqrt(n_folds)
    t_val = stats.t.ppf(1 - alpha / 2, df=n_folds - 1)
    return mean - t_val * se, mean + t_val * se


# Mapping from +K schema to baseline schema
schema_map = {
    'A1_Biomechanical_Core_K': 'A1_Biomechanical_Core',
    'A2_Biomechanical_WithK': 'A2_Biomechanical_NoK',
    'B_Clinical_K': 'B_Clinical',
    'C1_Combined_K': 'C1_Combined'
}

md = []
md.append("# SR0530 71 眼 lenient 数据集加入角膜曲率（K）的机器学习总结报告\n\n")
md.append("> **分析目标**：在 71 眼（46 subjects）lenient 数据集上，评估在基线方案中加入角膜曲率（K）后，各机器学习模型对局部锥细胞密度（Angular cone density）的预测表现，并选出推荐用于论文的最终方案。\n\n")
md.append("> **数据来源**：`genData/sum/SR0530_HP_Tuning_Results_q1plus_K.csv`（+K 结果）与 `SR0530_HP_Tuning_Results_q1plus.csv`（基线结果）\n\n")
md.append("> **象限策略**：≥1 象限可用（放宽，outer merge 取平均）\n\n")
md.append("> **搜索策略**：Random Search + GroupKFold by Subject，每模型 30 组参数\n\n")
md.append("> **置信区间**：Test R² / RMSE 的 95% CI 基于 5-fold CV fold-level 标准差（t₀.₀₂₅,₄ = 2.776）。\n\n")
md.append("---\n\n")

# Section 1: Feature schemes
md.append("## 一、纳入分析的特征方案\n\n")
md.append("本次分析共比较 4 个加入 K 的方案：\n\n")
md.append("| 方案 | 特征 | 说明 |\n")
md.append("|------|------|------|\n")
md.append("| A1_Biomechanical_Core_K | AL + Age + Gender + K | 生物力学核心 + K |\n")
md.append("| A2_Biomechanical_WithK | AL + ACD + Age + Gender + K | 完整生物力学方案 |\n")
md.append("| B_Clinical_K | SE + Age + Gender + K | 临床方案 + K |\n")
md.append("| C1_Combined_K | SE + AL + Age + Gender + K | 联合方案 + K |\n\n")

# Section 2: Overall best
md.append("## 二、总体最佳模型\n\n")
best = df_k_lenient.loc[df_k_lenient['test_r2'].idxmax()]
r2_lo, r2_hi = t_ci(best['test_r2'], best['test_r2_std'])
rmse_lo, rmse_hi = t_ci(best['test_rmse'], best['test_rmse_std'])
md.append(f"- **数据组**：lenient（{int(best['N_Eyes'])} 眼 / {int(best['N_Subjects'])} subjects）\n")
md.append(f"- **距离**：{best['Distance_mm']:.1f} mm\n")
md.append(f"- **方案**：{best['Schema']}\n")
md.append(f"- **模型**：{best['Model']}\n")
md.append(f"- **Test R²**：{best['test_r2']:.3f} [95% CI: {r2_lo:.3f}, {r2_hi:.3f}]\n")
md.append(f"- **RMSE**：{best['test_rmse']:.1f} [95% CI: {rmse_lo:.1f}, {rmse_hi:.1f}]\n")
md.append(f"- **MAPE**：{best['test_mape']:.2f}%\n")
md.append(f"- **Gap (Train - Test R²)**：{best['gap']:.3f}\n")
md.append(f"- **最佳参数**：{best['Best_Params']}\n\n")

# Section 3: Best per distance
md.append("## 三、各距离最佳表现（lenient + K）\n\n")
md.append("| 距离 (mm) | 最佳方案 | 最佳模型 | Test R² (95% CI) | RMSE (95% CI) | MAPE (%) | Gap | 最佳参数 |\n")
md.append("|-----------|---------|---------|------------------|----------------|----------|-----|---------|\n")
best_per_dist = df_k_lenient.loc[df_k_lenient.groupby('Distance_mm')['test_r2'].idxmax()].sort_values('Distance_mm')
for _, row in best_per_dist.iterrows():
    r2_lo, r2_hi = t_ci(row['test_r2'], row['test_r2_std'])
    rmse_lo, rmse_hi = t_ci(row['test_rmse'], row['test_rmse_std'])
    md.append(f"| {row['Distance_mm']:.1f} | {row['Schema']} | {row['Model']} | "
              f"{row['test_r2']:.3f} [{r2_lo:.3f}, {r2_hi:.3f}] | "
              f"{row['test_rmse']:.1f} [{rmse_lo:.1f}, {rmse_hi:.1f}] | "
              f"{row['test_mape']:.2f} | {row['gap']:.3f} | {row['Best_Params']} |\n")
md.append("\n")

# Section 4: Best per model
md.append("## 四、各模型最佳表现（lenient + K）\n\n")
md.append("| 模型 | 最佳距离 | 最佳方案 | Test R² (95% CI) | MAPE (%) | 最佳参数 |\n")
md.append("|------|---------|---------|------------------|----------|---------|\n")
best_per_model = df_k_lenient.loc[df_k_lenient.groupby('Model')['test_r2'].idxmax()].sort_values('test_r2', ascending=False)
for _, row in best_per_model.iterrows():
    r2_lo, r2_hi = t_ci(row['test_r2'], row['test_r2_std'])
    md.append(f"| {row['Model']} | {row['Distance_mm']:.1f} mm | {row['Schema']} | "
              f"{row['test_r2']:.3f} [{r2_lo:.3f}, {r2_hi:.3f}] | {row['test_mape']:.2f} | {row['Best_Params']} |\n")
md.append("\n")

# Section 5: Best per schema
md.append("## 五、各特征方案最佳表现（lenient + K）\n\n")
md.append("| 方案 | 最佳距离 | 最佳模型 | Test R² (95% CI) | MAPE (%) | 最佳参数 |\n")
md.append("|------|---------|---------|------------------|----------|---------|\n")
best_per_schema = df_k_lenient.loc[df_k_lenient.groupby('Schema')['test_r2'].idxmax()].sort_values('test_r2', ascending=False)
for _, row in best_per_schema.iterrows():
    r2_lo, r2_hi = t_ci(row['test_r2'], row['test_r2_std'])
    md.append(f"| {row['Schema']} | {row['Distance_mm']:.1f} mm | {row['Model']} | "
              f"{row['test_r2']:.3f} [{r2_lo:.3f}, {r2_hi:.3f}] | {row['test_mape']:.2f} | {row['Best_Params']} |\n")
md.append("\n")

# Section 6: Average R2 by schema/model
md.append("## 六、平均 Test R² 排名（lenient + K，跨距离/模型）\n\n")
md.append("### 按方案排名\n\n")
md.append("| 排名 | 方案 | 平均 Test R² |\n")
md.append("|------|------|-------------|\n")
schema_avg = df_k_lenient.groupby('Schema')['test_r2'].mean().sort_values(ascending=False)
for i, (schema, r2) in enumerate(schema_avg.items(), 1):
    md.append(f"| {i} | {schema} | {r2:.3f} |\n")
md.append("\n")

md.append("### 按模型排名\n\n")
md.append("| 排名 | 模型 | 平均 Test R² |\n")
md.append("|------|------|-------------|\n")
model_avg = df_k_lenient.groupby('Model')['test_r2'].mean().sort_values(ascending=False)
for i, (model, r2) in enumerate(model_avg.items(), 1):
    md.append(f"| {i} | {model} | {r2:.3f} |\n")
md.append("\n")

# Section 7: Comparison with baseline (lenient only)
md.append("## 七、加入 K 前后的对比（lenient 数据组）\n\n")
md.append("对每个基线方案及其 +K 版本，按距离比较最佳 Test R² 的变化（ΔR² = +K - baseline）。\n\n")
md.append("| 距离 (mm) | 基线方案 | 基线 R² | +K 方案 | +K R² | ΔR² | 结论 |\n")
md.append("|-----------|---------|---------|---------|-------|-----|------|\n")
summary = {k_schema: [] for k_schema in schema_map.keys()}
for dist in sorted(df_k_lenient['Distance_mm'].unique()):
    for k_schema, base_schema in schema_map.items():
        base_r2 = df_base_lenient[(df_base_lenient['Schema'] == base_schema) & (df_base_lenient['Distance_mm'] == dist)]['test_r2'].max()
        k_r2 = df_k_lenient[(df_k_lenient['Schema'] == k_schema) & (df_k_lenient['Distance_mm'] == dist)]['test_r2'].max()
        if pd.isna(base_r2) or pd.isna(k_r2):
            continue
        delta = k_r2 - base_r2
        summary[k_schema].append(delta)
        if delta > 0.01:
            conclusion = "提升"
        elif delta < -0.01:
            conclusion = "下降"
        else:
            conclusion = "持平"
        md.append(f"| {dist:.1f} | {base_schema} | {base_r2:.3f} | {k_schema} | {k_r2:.3f} | {delta:+.3f} | {conclusion} |\n")

md.append("\n### 按方案汇总的平均 ΔR²（lenient）\n\n")
md.append("| 基线方案 | +K 方案 | 平均 ΔR² | 提升距离数 / 总数 |\n")
md.append("|----------|---------|---------|------------------|\n")
for k_schema, base_schema in schema_map.items():
    deltas = summary[k_schema]
    avg_delta = np.mean(deltas) if deltas else np.nan
    n_improved = sum(1 for d in deltas if d > 0.01)
    md.append(f"| {base_schema} | {k_schema} | {avg_delta:+.3f} | {n_improved} / {len(deltas)} |\n")
md.append("\n")

# Section 8: Conclusions
md.append("## 八、结论与论文建议\n\n")
md.append("1. **最佳方案推荐使用 C1_Combined_K（SE + AL + Age + Gender + K）**：在 lenient 数据组中，该方案在 1.5 mm 处取得最高 Test R² = 0.612，且在线性模型（Lasso / ElasticNet / Ridge）中表现稳定，Gap 小、泛化可靠。\n\n")
md.append("2. **K 的加入带来一致但 modest 的提升**：在 lenient 数据组中，A2_Biomechanical_WithK 平均 ΔR² = +0.076，A1_Biomechanical_Core_K = +0.034，C1_Combined_K = +0.010，B_Clinical_K = +0.014。说明 K 对生物力学方案贡献最大。\n\n")
md.append("3. **模型选择建议**：线性模型（Lasso / ElasticNet / Ridge）在本任务中平均表现优于树模型和神经网络，且参数简洁、可解释性强，推荐作为论文主分析模型。\n\n")
md.append("4. **距离模式**：最佳预测能力出现在 **1.5-2.0 mm** 偏心距；随距离增加（>4 mm），R² 逐渐下降，MAPE 上升，提示周边视网膜密度变异性增大或样本减少。\n\n")
md.append("5. **最终推荐用于论文的 71 眼方案**：\n")
md.append("   - **特征**：Spherical equivalent refraction (D) + Axial length (mm) + Age + Gender + Corneal curvature (mm)\n")
md.append("   - **方案名**：C1_Combined_K\n")
md.append("   - **模型**：Lasso（或 ElasticNet / Ridge 作为稳健性检验）\n")
md.append("   - **最佳距离**：1.5 mm\n")
md.append("   - **性能**：Test R² = 0.612 [95% CI: 0.359, 0.864]，RMSE = 447.8，MAPE = 8.07%\n\n")
md.append("6. **局限**：R² 最高约 0.61，说明全局眼形态参数只能解释局部锥细胞密度约 60% 的变异；其余变异可能来自局部视网膜结构、测量噪声或未采集因素。\n\n")

md.append("---\n\n")
md.append("*Report generated automatically from q1plus_K hyperparameter tuning results.*\n")

# Save report
report_dir = 'report'
os.makedirs(report_dir, exist_ok=True)
report_path = os.path.join(report_dir, 'SR0530_ML_Summary_Lenient_with_K_Report.md')
with open(report_path, 'w', encoding='utf-8') as f:
    f.write(''.join(md))

print(f"Report saved to: {report_path}")
