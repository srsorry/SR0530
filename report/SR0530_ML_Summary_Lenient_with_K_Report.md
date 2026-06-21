# SR0530 71 眼 lenient 数据集加入角膜曲率（K）的机器学习总结报告

> **分析目标**：在 71 眼（46 subjects）lenient 数据集上，评估在基线方案中加入角膜曲率（K）后，各机器学习模型对局部锥细胞密度（Angular cone density）的预测表现，并选出推荐用于论文的最终方案。

> **数据来源**：`genData/sum/SR0530_HP_Tuning_Results_q1plus_K.csv`（+K 结果）与 `SR0530_HP_Tuning_Results_q1plus.csv`（基线结果）

> **象限策略**：≥1 象限可用（放宽，outer merge 取平均）

> **搜索策略**：Random Search + GroupKFold by Subject，每模型 30 组参数

> **置信区间**：Test R² / RMSE 的 95% CI 基于 5-fold CV fold-level 标准差（t₀.₀₂₅,₄ = 2.776）。

---

## 一、纳入分析的特征方案

本次分析共比较 4 个加入 K 的方案：

| 方案 | 特征 | 说明 |
|------|------|------|
| A1_Biomechanical_Core_K | AL + Age + Gender + K | 生物力学核心 + K |
| A2_Biomechanical_WithK | AL + ACD + Age + Gender + K | 完整生物力学方案 |
| B_Clinical_K | SE + Age + Gender + K | 临床方案 + K |
| C1_Combined_K | SE + AL + Age + Gender + K | 联合方案 + K |

## 二、总体最佳模型

- **数据组**：lenient（71 眼 / 46 subjects）
- **距离**：1.5 mm
- **方案**：C1_Combined_K
- **模型**：Lasso
- **Test R²**：0.612 [95% CI: 0.359, 0.864]
- **RMSE**：447.8 [95% CI: 183.5, 712.0]
- **MAPE**：8.07%
- **Gap (Train - Test R²)**：0.005
- **最佳参数**：{'alpha': 10.0}

## 三、各距离最佳表现（lenient + K）

| 距离 (mm) | 最佳方案 | 最佳模型 | Test R² (95% CI) | RMSE (95% CI) | MAPE (%) | Gap | 最佳参数 |
|-----------|---------|---------|------------------|----------------|----------|-----|---------|
| 1.0 | A1_Biomechanical_Core_K | XGBoost | 0.515 [0.395, 0.635] | 511.7 [348.7, 674.8] | 10.53 | 0.206 | {'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 1.0} |
| 1.5 | C1_Combined_K | Lasso | 0.612 [0.359, 0.864] | 447.8 [183.5, 712.0] | 8.07 | 0.005 | {'alpha': 10.0} |
| 2.0 | A2_Biomechanical_WithK | ElasticNet | 0.520 [0.314, 0.726] | 427.8 [219.5, 636.0] | 9.46 | 0.064 | {'alpha': 0.001, 'l1_ratio': 0.5} |
| 2.5 | A2_Biomechanical_WithK | Lasso | 0.476 [0.144, 0.808] | 411.2 [232.5, 589.9] | 11.98 | 0.115 | {'alpha': 10.0} |
| 3.0 | A2_Biomechanical_WithK | Lasso | 0.495 [0.029, 0.961] | 322.3 [225.6, 418.9] | 10.92 | 0.313 | {'alpha': 0.01} |
| 3.5 | A2_Biomechanical_WithK | Lasso | 0.412 [0.187, 0.637] | 482.5 [297.4, 667.6] | 14.24 | 0.114 | {'alpha': 10.0} |
| 4.0 | A2_Biomechanical_WithK | Lasso | 0.384 [0.070, 0.698] | 569.5 [411.5, 727.5] | 18.77 | 0.110 | {'alpha': 10.0} |
| 4.5 | A2_Biomechanical_WithK | Lasso | 0.337 [-0.061, 0.735] | 543.8 [405.8, 681.9] | 19.11 | 0.192 | {'alpha': 10.0} |
| 5.0 | A2_Biomechanical_WithK | Random_Forest | 0.407 [0.283, 0.530] | 576.7 [441.2, 712.2] | 18.30 | 0.356 | {'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 2} |
| 5.5 | A2_Biomechanical_WithK | Lasso | 0.377 [0.141, 0.612] | 586.0 [467.9, 704.0] | 22.53 | 0.209 | {'alpha': 10.0} |
| 6.0 | A2_Biomechanical_WithK | Neural_Network | 0.420 [0.344, 0.496] | 637.4 [449.5, 825.2] | 21.71 | 0.224 | {'hidden_layer_sizes': (80,), 'alpha': 0.5, 'learning_rate_init': 0.001} |

## 四、各模型最佳表现（lenient + K）

| 模型 | 最佳距离 | 最佳方案 | Test R² (95% CI) | MAPE (%) | 最佳参数 |
|------|---------|---------|------------------|----------|---------|
| Lasso | 1.5 mm | C1_Combined_K | 0.612 [0.359, 0.864] | 8.07 | {'alpha': 10.0} |
| ElasticNet | 1.5 mm | C1_Combined_K | 0.606 [0.358, 0.854] | 8.23 | {'alpha': 0.001, 'l1_ratio': 0.5} |
| Ridge | 1.5 mm | A2_Biomechanical_WithK | 0.574 [0.453, 0.695] | 9.04 | {'alpha': 0.1} |
| XGBoost | 1.5 mm | A1_Biomechanical_Core_K | 0.563 [0.310, 0.817] | 9.21 | {'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 1.0} |
| Random_Forest | 1.5 mm | A1_Biomechanical_Core_K | 0.550 [0.295, 0.805] | 8.56 | {'n_estimators': 200, 'max_depth': None, 'min_samples_split': 2, 'min_samples_leaf': 4} |
| Neural_Network | 1.5 mm | A1_Biomechanical_Core_K | 0.485 [0.190, 0.779] | 9.06 | {'hidden_layer_sizes': (80,), 'alpha': 1.0, 'learning_rate_init': 0.0001} |
| SVM | 1.5 mm | C1_Combined_K | 0.420 [0.204, 0.636] | 8.62 | {'C': 2000, 'epsilon': 300, 'gamma': 0.005} |

## 五、各特征方案最佳表现（lenient + K）

| 方案 | 最佳距离 | 最佳模型 | Test R² (95% CI) | MAPE (%) | 最佳参数 |
|------|---------|---------|------------------|----------|---------|
| C1_Combined_K | 1.5 mm | Lasso | 0.612 [0.359, 0.864] | 8.07 | {'alpha': 10.0} |
| A2_Biomechanical_WithK | 1.5 mm | Lasso | 0.574 [0.450, 0.697] | 9.03 | {'alpha': 0.01} |
| A1_Biomechanical_Core_K | 1.5 mm | XGBoost | 0.563 [0.310, 0.817] | 9.21 | {'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 1.0} |
| B_Clinical_K | 1.0 mm | Random_Forest | 0.374 [0.086, 0.661] | 12.31 | {'n_estimators': 100, 'max_depth': 2, 'min_samples_split': 5, 'min_samples_leaf': 1} |

## 六、平均 Test R² 排名（lenient + K，跨距离/模型）

### 按方案排名

| 排名 | 方案 | 平均 Test R² |
|------|------|-------------|
| 1 | A2_Biomechanical_WithK | 0.352 |
| 2 | A1_Biomechanical_Core_K | 0.323 |
| 3 | C1_Combined_K | 0.321 |
| 4 | B_Clinical_K | 0.219 |

### 按模型排名

| 排名 | 模型 | 平均 Test R² |
|------|------|-------------|
| 1 | Lasso | 0.355 |
| 2 | ElasticNet | 0.353 |
| 3 | Ridge | 0.323 |
| 4 | SVM | 0.290 |
| 5 | Random_Forest | 0.275 |
| 6 | Neural_Network | 0.273 |
| 7 | XGBoost | 0.258 |

## 七、加入 K 前后的对比（lenient 数据组）

对每个基线方案及其 +K 版本，按距离比较最佳 Test R² 的变化（ΔR² = +K - baseline）。

| 距离 (mm) | 基线方案 | 基线 R² | +K 方案 | +K R² | ΔR² | 结论 |
|-----------|---------|---------|---------|-------|-----|------|
| 1.0 | A1_Biomechanical_Core | 0.458 | A1_Biomechanical_Core_K | 0.515 | +0.057 | 提升 |
| 1.0 | A2_Biomechanical_NoK | 0.410 | A2_Biomechanical_WithK | 0.455 | +0.045 | 提升 |
| 1.0 | B_Clinical | 0.312 | B_Clinical_K | 0.374 | +0.061 | 提升 |
| 1.0 | C1_Combined | 0.433 | C1_Combined_K | 0.444 | +0.011 | 提升 |
| 1.5 | A1_Biomechanical_Core | 0.443 | A1_Biomechanical_Core_K | 0.563 | +0.121 | 提升 |
| 1.5 | A2_Biomechanical_NoK | 0.506 | A2_Biomechanical_WithK | 0.574 | +0.068 | 提升 |
| 1.5 | B_Clinical | 0.320 | B_Clinical_K | 0.358 | +0.038 | 提升 |
| 1.5 | C1_Combined | 0.538 | C1_Combined_K | 0.612 | +0.074 | 提升 |
| 2.0 | A1_Biomechanical_Core | 0.421 | A1_Biomechanical_Core_K | 0.462 | +0.041 | 提升 |
| 2.0 | A2_Biomechanical_NoK | 0.398 | A2_Biomechanical_WithK | 0.520 | +0.123 | 提升 |
| 2.0 | B_Clinical | 0.234 | B_Clinical_K | 0.302 | +0.068 | 提升 |
| 2.0 | C1_Combined | 0.474 | C1_Combined_K | 0.505 | +0.031 | 提升 |
| 2.5 | A1_Biomechanical_Core | 0.376 | A1_Biomechanical_Core_K | 0.376 | -0.001 | 持平 |
| 2.5 | A2_Biomechanical_NoK | 0.300 | A2_Biomechanical_WithK | 0.476 | +0.176 | 提升 |
| 2.5 | B_Clinical | 0.246 | B_Clinical_K | 0.237 | -0.009 | 持平 |
| 2.5 | C1_Combined | 0.376 | C1_Combined_K | 0.418 | +0.042 | 提升 |
| 3.0 | A1_Biomechanical_Core | 0.334 | A1_Biomechanical_Core_K | 0.423 | +0.088 | 提升 |
| 3.0 | A2_Biomechanical_NoK | 0.325 | A2_Biomechanical_WithK | 0.495 | +0.170 | 提升 |
| 3.0 | B_Clinical | 0.240 | B_Clinical_K | 0.297 | +0.057 | 提升 |
| 3.0 | C1_Combined | 0.376 | C1_Combined_K | 0.402 | +0.026 | 提升 |
| 3.5 | A1_Biomechanical_Core | 0.312 | A1_Biomechanical_Core_K | 0.316 | +0.004 | 持平 |
| 3.5 | A2_Biomechanical_NoK | 0.372 | A2_Biomechanical_WithK | 0.412 | +0.040 | 提升 |
| 3.5 | B_Clinical | 0.227 | B_Clinical_K | 0.232 | +0.005 | 持平 |
| 3.5 | C1_Combined | 0.321 | C1_Combined_K | 0.295 | -0.026 | 下降 |
| 4.0 | A1_Biomechanical_Core | 0.245 | A1_Biomechanical_Core_K | 0.242 | -0.003 | 持平 |
| 4.0 | A2_Biomechanical_NoK | 0.259 | A2_Biomechanical_WithK | 0.384 | +0.126 | 提升 |
| 4.0 | B_Clinical | 0.244 | B_Clinical_K | 0.248 | +0.004 | 持平 |
| 4.0 | C1_Combined | 0.311 | C1_Combined_K | 0.275 | -0.036 | 下降 |
| 4.5 | A1_Biomechanical_Core | 0.276 | A1_Biomechanical_Core_K | 0.266 | -0.010 | 持平 |
| 4.5 | A2_Biomechanical_NoK | 0.301 | A2_Biomechanical_WithK | 0.337 | +0.036 | 提升 |
| 4.5 | B_Clinical | 0.274 | B_Clinical_K | 0.266 | -0.008 | 持平 |
| 4.5 | C1_Combined | 0.290 | C1_Combined_K | 0.308 | +0.018 | 提升 |
| 5.0 | A1_Biomechanical_Core | 0.329 | A1_Biomechanical_Core_K | 0.343 | +0.014 | 提升 |
| 5.0 | A2_Biomechanical_NoK | 0.410 | A2_Biomechanical_WithK | 0.407 | -0.004 | 持平 |
| 5.0 | B_Clinical | 0.347 | B_Clinical_K | 0.354 | +0.007 | 持平 |
| 5.0 | C1_Combined | 0.381 | C1_Combined_K | 0.376 | -0.005 | 持平 |
| 5.5 | A1_Biomechanical_Core | 0.288 | A1_Biomechanical_Core_K | 0.335 | +0.047 | 提升 |
| 5.5 | A2_Biomechanical_NoK | 0.368 | A2_Biomechanical_WithK | 0.377 | +0.009 | 持平 |
| 5.5 | B_Clinical | 0.369 | B_Clinical_K | 0.325 | -0.044 | 下降 |
| 5.5 | C1_Combined | 0.384 | C1_Combined_K | 0.345 | -0.039 | 下降 |
| 6.0 | A1_Biomechanical_Core | 0.345 | A1_Biomechanical_Core_K | 0.360 | +0.016 | 提升 |
| 6.0 | A2_Biomechanical_NoK | 0.377 | A2_Biomechanical_WithK | 0.420 | +0.043 | 提升 |
| 6.0 | B_Clinical | 0.312 | B_Clinical_K | 0.291 | -0.021 | 下降 |
| 6.0 | C1_Combined | 0.352 | C1_Combined_K | 0.364 | +0.012 | 提升 |

### 按方案汇总的平均 ΔR²（lenient）

| 基线方案 | +K 方案 | 平均 ΔR² | 提升距离数 / 总数 |
|----------|---------|---------|------------------|
| A1_Biomechanical_Core | A1_Biomechanical_Core_K | +0.034 | 7 / 11 |
| A2_Biomechanical_NoK | A2_Biomechanical_WithK | +0.076 | 9 / 11 |
| B_Clinical | B_Clinical_K | +0.014 | 4 / 11 |
| C1_Combined | C1_Combined_K | +0.010 | 7 / 11 |

## 八、结论与论文建议

1. **最佳方案推荐使用 C1_Combined_K（SE + AL + Age + Gender + K）**：在 lenient 数据组中，该方案在 1.5 mm 处取得最高 Test R² = 0.612，且在线性模型（Lasso / ElasticNet / Ridge）中表现稳定，Gap 小、泛化可靠。

2. **K 的加入带来一致但 modest 的提升**：在 lenient 数据组中，A2_Biomechanical_WithK 平均 ΔR² = +0.076，A1_Biomechanical_Core_K = +0.034，C1_Combined_K = +0.010，B_Clinical_K = +0.014。说明 K 对生物力学方案贡献最大。

3. **模型选择建议**：线性模型（Lasso / ElasticNet / Ridge）在本任务中平均表现优于树模型和神经网络，且参数简洁、可解释性强，推荐作为论文主分析模型。

4. **距离模式**：最佳预测能力出现在 **1.5-2.0 mm** 偏心距；随距离增加（>4 mm），R² 逐渐下降，MAPE 上升，提示周边视网膜密度变异性增大或样本减少。

5. **最终推荐用于论文的 71 眼方案**：
   - **特征**：Spherical equivalent refraction (D) + Axial length (mm) + Age + Gender + Corneal curvature (mm)
   - **方案名**：C1_Combined_K
   - **模型**：Lasso（或 ElasticNet / Ridge 作为稳健性检验）
   - **最佳距离**：1.5 mm
   - **性能**：Test R² = 0.612 [95% CI: 0.359, 0.864]，RMSE = 447.8，MAPE = 8.07%

6. **局限**：R² 最高约 0.61，说明全局眼形态参数只能解释局部锥细胞密度约 60% 的变异；其余变异可能来自局部视网膜结构、测量噪声或未采集因素。

---

*Report generated automatically from q1plus_K hyperparameter tuning results.*
