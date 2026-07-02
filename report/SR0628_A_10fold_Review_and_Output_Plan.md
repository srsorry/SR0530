# SR0628_A 10-fold ALK 方案族结果 Review 与后续输出计划

## 一、Review 目的

基于 `report/SR0530_ALK_10fold_Final_Tuning_Report.md`（8 个 ALK 方案 × 8 模型，10-fold GroupKFold by Subject，lenient 71 眼 / 46 subjects），结合已有的 `genData/sum/SR0530_HP_Tuning_Results_robust_repeatedCV_all_distances.csv`，梳理当前结果的核心结论与潜在偏差，为后续输出排优先级。

---

## 二、核心结果

### 1. 单次 10-fold 最优配置

| 项目 | 结果 |
|------|------|
| 数据组 | lenient |
| 距离 | **1.5 mm** |
| 方案 | **C1_Combined_ALK** |
| 模型 | **Robust_Linear_Regression (HuberRegressor)** |
| Test R² | **0.504** [95% CI: 0.326, 0.682] |
| Test RMSE | **458.0** [95% CI: 200.2, 715.8] |
| Gap | 0.081 |
| 最佳参数 | `epsilon=1.8, alpha=0.05` |

### 2. 各距离单次 10-fold 最佳结果

| 距离 (°) | 最佳方案 | 最佳模型 | Test R² (95% CI) | RMSE (95% CI) | Gap |
|-----------|----------|---------|------------------|----------------|-----|
| 1.0 | C1_Combined_ALK | ElasticNet | 0.355 [-0.010, 0.719] | 476.3 [278.8, 673.8] | 0.149 |
| 1.5 | C1_Combined_ALK | Robust_Linear_Regression | 0.504 [0.326, 0.682] | 458.0 [200.2, 715.8] | 0.081 |
| 2.0 | A2_Biomechanical_ALK | Robust_Linear_Regression | 0.466 [0.253, 0.679] | 401.1 [207.8, 594.4] | 0.042 |
| 2.5 | A2_Biomechanical_K_ALK | Robust_Linear_Regression | 0.266 [-0.018, 0.550] | 445.8 [330.7, 561.0] | 0.235 |
| 3.0 | A1_Biomechanical_ALK | Robust_Linear_Regression | 0.469 [0.217, 0.722] | 441.9 [221.5, 662.4] | -0.082 |
| 3.5 | A1_Biomechanical_ALK | Robust_Linear_Regression | 0.406 [0.160, 0.652] | 436.0 [232.7, 639.3] | -0.001 |
| 4.0 | A1_Biomechanical_ALK | Robust_Linear_Regression | 0.335 [0.076, 0.595] | 505.4 [282.1, 728.7] | 0.022 |
| 4.5 | C1_Combined_ALK | Robust_Linear_Regression | 0.236 [0.005, 0.467] | 535.4 [364.0, 706.8] | 0.184 |
| 5.0 | B_Clinical_ALK | Robust_Linear_Regression | 0.131 [-0.206, 0.468] | 551.1 [353.3, 749.0] | 0.308 |
| 5.5 | C1_Combined_K_ALK | SVM | 0.167 [-0.163, 0.497] | 618.7 [419.3, 818.1] | 0.220 |
| 6.0 | A2_Biomechanical_ALK | Neural_Network | 0.170 [-0.251, 0.591] | 622.6 [438.7, 806.4] | 0.459 |

### 3. 重复 CV 校正后的更稳健估计

从 `SR0530_HP_Tuning_Results_robust_repeatedCV_all_distances.csv` 看：

| 距离 (°) | 最佳方案（重复 CV） | 最佳模型 | 重复 CV Test R² | Test R² Std | Gap |
|-----------|---------------------|---------|----------------|-------------|-----|
| 1.0 | C1_Combined_ALK | ElasticNet | 0.362 | 0.307 | 0.146 |
| 1.5 | C1_Combined_ALK | ElasticNet | **0.395** | 0.292 | 0.196 |
| 2.0 | A2_Biomechanical_K_ALK | ElasticNet | 0.364 | 0.201 | 0.185 |
| 2.5 | A2_Biomechanical_K_ALK | ElasticNet | 0.206 | 0.309 | 0.241 |
| 3.0 | A2_Biomechanical_ALK | Lasso | 0.315 | 0.328 | 0.272 |
| 3.5 | A2_Biomechanical_K_ALK | ElasticNet | 0.219 | 0.417 | 0.253 |
| 4.0 | A2_Biomechanical_ALK | ElasticNet | 0.158 | 0.229 | 0.247 |
| 4.5 | A2_Biomechanical_K_ALK | ElasticNet | 0.124 | 0.316 | 0.282 |
| 5.0 | C1_Combined_ALK | ElasticNet | 0.195 | 0.295 | 0.233 |
| 5.5 | C1_Combined_ALK | ElasticNet | 0.216 | 0.256 | 0.215 |
| 6.0 | A1_Biomechanical_Core_K | Neural_Network | 0.194 | 0.204 | 0.313 |

- **重复 CV 整体最佳**：`C1_Combined_ALK / ElasticNet @ 1.5 mm`，Mean Test R² = **0.395**。
- **单次 10-fold 最佳 0.504 vs 重复 CV 最佳 0.395**：存在约 **0.11** 的乐观偏差，这是模型选择 + 单次 CV 带来的典型高估。

---

## 三、关键发现

1. **最佳距离仍是 1.5 mm**：无论是单次 10-fold 还是重复 CV，1.5 mm 都是峰值距离。
2. **Robust Linear Regression 在单次 10-fold 表现突出**：在 1.5、2.0、2.5、3.0、3.5、4.0、4.5、5.0 mm 均为最佳或次佳，且 Gap 普遍较小，模型简单、可解释性强。
3. **重复 CV 下 ElasticNet/Lasso 更稳健**：重复 CV 降低方差后，线性正则化模型的平均表现优于 RF/NN/SVM/XGBoost。
4. **ALK 与 K_ALK 性能接近**：多数距离下，ALK-only 与 K+ALK 方案互有胜负，再次支持用 AL/K 单一指标替代单独 K 的推论。
5. **远处距离（≥5.0 mm）预测能力显著下降**：R² 接近 0 甚至为负，RMSE 增大，提示远处象限数据噪声或样本量问题。
6. ** optimism 需要被正视**：论文主结果应优先报告重复 CV 的 0.395，而非单次 10-fold 的 0.504。

---

## 四、建议的后续输出

以下按“从结果解释到论文可用图表”的顺序排列，每个输出均可独立生成。

| 序号 | 文件命名 | 内容 | 优先级 | 预计耗时 |
|------|----------|------|--------|----------|
| A | `report/SR0628_A_10fold_Review_and_Output_Plan.md` | 本 Review 与计划文件 | 已完成 | - |
| B | `report/SR0628_B_Single_vs_Repeated_CV_Comparison.md` | 对比单次 10-fold 与重复 CV：各距离最佳 R²/RMSE、Gap、 optimism 量化；附折线/柱状图 | **高** | 中 |
| C | `report/SR0628_C_Best_RepeatedCV_Diagnostics.md` | 基于重复 CV 最佳配置（C1_Combined_ALK / ElasticNet @ 1.5 mm）生成学习曲线、Observed vs Predicted、残差 QQ、残差 vs 预测、SHAP summary | **高** | 高 |
| D | `report/SR0628_D_Distance_Performance_Summary.md` | 距离-性能汇总图：R² / RMSE 随距离变化（单次 10-fold vs 重复 CV），PDF 输出 | 中 | 中 |
| E | `report/SR0628_E_Model_Comparison_1.5mm.md` | 1.5° 处 8 模型箱线图/小提琴图比较 fold-level R²；附超参数敏感度简表 | 中 | 中 |
| F | `report/SR0628_F_Coefficient_Stability.md` | 最佳线性模型（ElasticNet/Robust LR）在重复 CV 下的系数/特征重要性稳定性，输出每个特征的均值 ± SD 及 95% CI | 中 | 高 |
| G | `report/SR0628_G_Updated_Lenient_ALK_Summary.md` | 在现有 lenient_ALK 总结报告中追加“重复 CV 稳健性说明”与推荐报告值 | 低 | 低 |

---

## 五、下一步建议

1. **优先完成 B + C**：先量化 optimism，再用重复 CV 最佳配置做完整诊断，这两份结果是论文结果部分的核心。
2. **论文主结果采用重复 CV 的 0.395**（C1_Combined_ALK / ElasticNet @ 1.5 mm），并在正文/补充材料中说明“单次 10-fold 峰值 0.504 存在选择偏倚”。
3. 若需要保留 Robust LR 的可解释性优势，可将 C1_Combined_ALK / Robust LR @ 1.5 mm 作为补充稳健性分析（单次 10-fold R²=0.504，重复 CV 待补充）。
4. 待 B/C 完成后，再决定是否继续 D/E/F/G。

---

*Review generated: SR0628_A*
