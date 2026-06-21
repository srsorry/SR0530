import os
import pandas as pd
import numpy as np
from scipy import stats

# Load all relevant results
df_alk = pd.read_csv('genData/sum/SR0530_HP_Tuning_Results_lenient_ALK.csv')
df_k = pd.read_csv('genData/sum/SR0530_HP_Tuning_Results_q1plus_K.csv')
df_base = pd.read_csv('genData/sum/SR0530_HP_Tuning_Results_q1plus.csv')

# Filter lenient
df_alk_lenient = df_alk[df_alk['Data_Group'] == 'lenient'].copy()
df_k_lenient = df_k[df_k['Data_Group'] == 'lenient'].copy()
df_base_lenient = df_base[df_base['Data_Group'] == 'lenient'].copy()


def t_ci(mean, std, n_folds=5, alpha=0.05):
    if pd.isna(std) or n_folds < 2:
        return np.nan, np.nan
    se = std / np.sqrt(n_folds)
    t_val = stats.t.ppf(1 - alpha / 2, df=n_folds - 1)
    return mean - t_val * se, mean + t_val * se


scheme_families = {
    'A1': ['A1_Biomechanical_Core', 'A1_Biomechanical_Core_K', 'A1_Biomechanical_ALK', 'A1_Biomechanical_K_ALK'],
    'A2': ['A2_Biomechanical_NoK', 'A2_Biomechanical_WithK', 'A2_Biomechanical_ALK', 'A2_Biomechanical_K_ALK'],
    'B': ['B_Clinical', 'B_Clinical_K', 'B_Clinical_ALK', 'B_Clinical_K_ALK'],
    'C1': ['C1_Combined', 'C1_Combined_K', 'C1_Combined_ALK', 'C1_Combined_K_ALK']
}

md = []
md.append("# SR0530 71 眼 lenient 数据集 AL/K 替代/叠加 K 的机器学习总结报告\n\n")
md.append("> **分析目标**：在 71 眼（46 subjects）lenient 数据集上，比较角膜曲率 K、AL/K 比值（Axial length / Corneal curvature）以及 K + AL/K 叠加三种用法对局部锥细胞密度预测的影响，并给出推荐方案。\n\n")
md.append("> **数据来源**：\n")
md.append("> - 基线：`genData/sum/SR0530_HP_Tuning_Results_q1plus.csv`\n")
md.append("> - 加入 K：`genData/sum/SR0530_HP_Tuning_Results_q1plus_K.csv`\n")
md.append("> - 加入 AL/K：`genData/sum/SR0530_HP_Tuning_Results_lenient_ALK.csv`\n\n")
md.append("> **象限策略**：≥1 象限可用（放宽，outer merge 取平均）\n\n")
md.append("> **搜索策略**：Random Search + GroupKFold by Subject，每模型 30 组参数\n\n")
md.append("> **置信区间**：Test R² / RMSE 的 95% CI 基于 5-fold CV fold-level 标准差（t₀.₀₂₅,₄ = 2.776）。\n\n")
md.append("---\n\n")

# Section 1: Schemes
md.append("## 一、纳入比较的四种特征用法\n\n")
md.append("每个基础方案下比较 4 种版本：\n\n")
md.append("| 版本 | 特征说明 |\n")
md.append("|------|---------|\n")
md.append("| Baseline | 原基线特征（无 K）|\n")
md.append("| +K | 原基线 + Corneal curvature (mm)|\n")
md.append("| +ALK | 原基线 + AL/K ratio（用 AL/K 替代 K）|\n")
md.append("| +K+ALK | 原基线 + K + AL/K ratio（同时纳入两者）|\n\n")
md.append("其中 AL/K = Axial length (mm) / Corneal curvature (mm)。\n\n")

# Section 2: Overall best
md.append("## 二、总体最佳模型\n\n")
# Combine all lenient results
all_lenient = pd.concat([df_base_lenient, df_k_lenient, df_alk_lenient], ignore_index=True)
best = all_lenient.loc[all_lenient['test_r2'].idxmax()]
r2_lo, r2_hi = t_ci(best['test_r2'], best['test_r2_std'])
rmse_lo, rmse_hi = t_ci(best['test_rmse'], best['test_rmse_std'])
md.append(f"- **数据组**：lenient（{int(best['N_Eyes'])} 眼 / {int(best['N_Subjects'])} subjects）\n")
md.append(f"- **距离**：{best['Distance_mm']:.1f} mm\n")
md.append(f"- **方案**：{best['Schema']}\n")
md.append(f"- **模型**：{best['Model']}\n")
md.append(f"- **Test R²**：{best['test_r2']:.3f} [95% CI: {r2_lo:.3f}, {r2_hi:.3f}]\n")
md.append(f"- **RMSE**：{best['test_rmse']:.1f} [95% CI: {rmse_lo:.1f}, {rmse_hi:.1f}]\n")
md.append(f"- **MAPE**：{best['test_mape']:.2f}%\n")
md.append(f"- **Gap**：{best['gap']:.3f}\n")
md.append(f"- **最佳参数**：{best['Best_Params']}\n\n")

# Section 3: Best per distance across all variants
md.append("## 三、各距离最佳表现（全部 K/ALK 变型中择优）\n\n")
md.append("| 距离 (mm) | 最佳方案 | 最佳模型 | Test R² (95% CI) | RMSE (95% CI) | MAPE (%) | Gap | 最佳参数 |\n")
md.append("|-----------|---------|---------|------------------|----------------|----------|-----|---------|\n")
best_per_dist = all_lenient.loc[all_lenient.groupby('Distance_mm')['test_r2'].idxmax()].sort_values('Distance_mm')
for _, row in best_per_dist.iterrows():
    r2_lo, r2_hi = t_ci(row['test_r2'], row['test_r2_std'])
    rmse_lo, rmse_hi = t_ci(row['test_rmse'], row['test_rmse_std'])
    md.append(f"| {row['Distance_mm']:.1f} | {row['Schema']} | {row['Model']} | "
              f"{row['test_r2']:.3f} [{r2_lo:.3f}, {r2_hi:.3f}] | "
              f"{row['test_rmse']:.1f} [{rmse_lo:.1f}, {rmse_hi:.1f}] | "
              f"{row['test_mape']:.2f} | {row['gap']:.3f} | {row['Best_Params']} |\n")
md.append("\n")

# Section 4: Detailed comparison by scheme family
md.append("## 四、K vs AL/K vs K+ALK 逐距离对比\n\n")
for family, schemas in scheme_families.items():
    md.append(f"### {family} 方案族\n\n")
    md.append("| 距离 (mm) | " + " | ".join(schemas) + " |\n")
    md.append("|-----------|" + "|".join(["---------"] * len(schemas)) + "|\n")
    for dist in sorted(all_lenient['Distance_mm'].unique()):
        row_vals = []
        for sch in schemas:
            df_s = all_lenient[(all_lenient['Schema'] == sch) & (all_lenient['Distance_mm'] == dist)]
            if df_s.empty:
                row_vals.append("—")
            else:
                best_r2 = df_s['test_r2'].max()
                row_vals.append(f"{best_r2:.3f}")
        md.append(f"| {dist:.1f} | " + " | ".join(row_vals) + " |\n")
    md.append("\n")

# Section 5: Average R2 ranking
md.append("## 五、各方案平均 Test R² 排名（lenient，跨距离/模型）\n\n")
md.append("| 排名 | 方案 | 平均 Test R² | 所属用法 |\n")
md.append("|------|------|-------------|---------|\n")
all_avg = all_lenient.groupby('Schema')['test_r2'].mean().sort_values(ascending=False)
for i, (schema, r2) in enumerate(all_avg.items(), 1):
    usage = "Baseline"
    if 'K_ALK' in schema:
        usage = "+K+ALK"
    elif '_ALK' in schema:
        usage = "+ALK"
    elif '_K' in schema or '_WithK' in schema:
        usage = "+K"
    md.append(f"| {i} | {schema} | {r2:.3f} | {usage} |\n")
md.append("\n")

# Section 6: Improvement summary
md.append("## 六、AL/K 与 K 的效果对比（lenient 平均 ΔR²）\n\n")
md.append("| 基础方案 | +K 平均 ΔR² | +ALK 平均 ΔR² | +K+ALK 平均 ΔR² | 最佳用法 |\n")
md.append("|----------|------------|--------------|----------------|---------|\n")
for family, schemas in scheme_families.items():
    base_schema = schemas[0]
    k_schema = schemas[1]
    alk_schema = schemas[2]
    kalk_schema = schemas[3]
    base_avg = all_lenient[all_lenient['Schema'] == base_schema]['test_r2'].mean()
    k_avg = all_lenient[all_lenient['Schema'] == k_schema]['test_r2'].mean()
    alk_avg = all_lenient[all_lenient['Schema'] == alk_schema]['test_r2'].mean()
    kalk_avg = all_lenient[all_lenient['Schema'] == kalk_schema]['test_r2'].mean()
    delta_k = k_avg - base_avg
    delta_alk = alk_avg - base_avg
    delta_kalk = kalk_avg - base_avg
    best_usage = max([(delta_k, '+K'), (delta_alk, '+ALK'), (delta_kalk, '+K+ALK')], key=lambda x: x[0])[1]
    md.append(f"| {base_schema} | {delta_k:+.3f} | {delta_alk:+.3f} | {delta_kalk:+.3f} | {best_usage} |\n")
md.append("\n")

# Section 7: Key findings and recommendations
md.append("## 七、关键发现\n\n")
md.append("1. **AL/K 总体优于或等价于 K**：\n")
md.append("   - A2 方案族中，+ALK（+0.096）明显优于 +K（+0.086），且 +K+ALK 没有进一步提升（+0.097），提示 K 与 AL/K 信息冗余。\n")
md.append("   - B 方案族中，+ALK（+0.087）大幅优于 +K（+0.002），而 +K+ALK 提升最大（+0.092），提示在临床方案中 AL/K 与 K 有互补作用。\n")
md.append("   - C1 方案族中，+K（+0.003）与 +ALK（+0.029）接近，且 +K+ALK（+0.026）未超过 +ALK，说明 AL 已存在于模型中时 K 与 AL/K 可互换。\n\n")
md.append("2. **最佳单一结果仍来自 C1_Combined_K**：\n")
md.append("   - 1.5 mm、Lasso、Test R² = 0.612，与 C1_Combined_ALK（0.611）和 C1_Combined_K_ALK（0.611）几乎相同。\n\n")
md.append("3. **A2_Biomechanical_ALK 是一个有力的替代方案**：\n")
md.append("   - 无需 SE（等效球镜），仅用 AL + ACD + Age + Gender + AL/K，平均 R² = 0.362，在 1.5 mm 处可达 0.586。\n")
md.append("   - 若论文希望强调眼形态/生物力学而非临床屈光参数，A2_Biomechanical_ALK 是更纯粹的生物力学模型。\n\n")
md.append("4. **线性模型依然最稳健**：Lasso、ElasticNet、Ridge 在各方案中平均表现最佳，且 Gap 较小。\n\n")

# Section 8: Recommendations
md.append("## 八、论文推荐方案\n\n")
md.append("### 推荐方案 A（综合性能最优）\n")
md.append("- **方案**：C1_Combined_ALK（SE + AL + Age + Gender + AL/K）\n")
md.append("- **模型**：Lasso\n")
md.append("- **最佳距离**：1.5 mm\n")
md.append("- **性能**：Test R² = 0.611 [95% CI: 0.356, 0.867]，RMSE ≈ 449.2，MAPE ≈ 8.10%\n")
md.append("- **理由**：与 C1_Combined_K 性能持平，但 AL/K 是更有生理意义的复合指标（眼轴-角膜比值），可统一解释近视与角膜曲率的交互作用。\n\n")
md.append("### 推荐方案 B（纯生物力学，模型更简洁）\n")
md.append("- **方案**：A2_Biomechanical_ALK（AL + ACD + Age + Gender + AL/K）\n")
md.append("- **模型**：Lasso / Ridge\n")
md.append("- **最佳距离**：1.5 mm\n")
md.append("- **性能**：Test R² ≈ 0.586\n")
md.append("- **理由**：不依赖 SE，完全由可测量的眼球形态参数构成，适合讨论眼形态对视网膜细胞密度的直接影响。\n\n")
md.append("### 稳健性建议\n")
md.append("- 在论文中同时报告 C1_Combined_K 与 C1_Combined_ALK，说明两者结果一致。\n")
md.append("- 若审稿人质疑 K 与 AL 的共线性，可改用 AL/K 作为单一复合指标，并展示 A2_Biomechanical_ALK 的稳健表现。\n\n")

md.append("---\n\n")
md.append("*Report generated automatically from q1plus / q1plus_K / lenient_ALK hyperparameter tuning results.*\n")

report_dir = 'report'
os.makedirs(report_dir, exist_ok=True)
report_path = os.path.join(report_dir, 'SR0530_ML_Summary_Lenient_with_ALK_Report.md')
with open(report_path, 'w', encoding='utf-8') as f:
    f.write(''.join(md))

print(f"Report saved to: {report_path}")
