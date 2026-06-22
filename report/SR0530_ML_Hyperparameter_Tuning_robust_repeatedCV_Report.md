# SR0530 稳健性超参数寻优报告（robust_repeatedCV）

> **目标**：使用重复交叉验证（Repeated GroupKFold）重新评估各方案，降低 fold split 随机性带来的选择偏倚。

> **方法**：Random Search + 5-fold GroupKFold × 5 repeats，每模型 15 组参数

> **数据**：lenient（71 眼 / 46 subjects），Distance = 1.5 mm

> **置信区间**：基于 25 个 fold-level R²（5 seeds × 5 folds）估算 95% CI。

---

## 一、总体最佳配置（稳健性评估）

- **距离**：1.5 mm
- **方案**：C1_Combined_ALK
- **模型**：ElasticNet
- **Mean Test R²**：0.395 [95% CI: 0.274, 0.515]
- **Std Test R²**：0.292
- **Mean Gap**：0.196
- **最佳参数**：{'alpha': 1.0, 'l1_ratio': 0.7}
- **样本量**：71 眼 / 46 subjects

## 二、每个方案的最佳模型（按 Mean Test R²）

| 方案 | 最佳模型 | Mean Test R² (95% CI) | Std | Gap | 最佳参数 |
|------|---------|----------------------|-----|-----|---------|
| A1_Biomechanical_Core | ElasticNet | 0.269 [0.132, 0.406] | 0.331 | 0.216 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| A1_Biomechanical_Core_K | Neural_Network | 0.384 [0.279, 0.490] | 0.256 | 0.180 | {'hidden_layer_sizes': (100,), 'alpha': 1.0, 'learning_rate_init': 0.001} |
| A1_Biomechanical_ALK | ElasticNet | 0.387 [0.271, 0.503] | 0.281 | 0.182 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| A1_Biomechanical_K_ALK | ElasticNet | 0.382 [0.269, 0.496] | 0.275 | 0.190 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| A2_Biomechanical_NoK | Random_Forest | 0.283 [0.144, 0.422] | 0.336 | 0.417 | {'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 4} |
| A2_Biomechanical_WithK | ElasticNet | 0.374 [0.258, 0.489] | 0.279 | 0.210 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| A2_Biomechanical_ALK | ElasticNet | 0.368 [0.233, 0.503] | 0.328 | 0.225 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| A2_Biomechanical_K_ALK | ElasticNet | 0.393 [0.279, 0.508] | 0.278 | 0.206 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| B_Clinical | Random_Forest | 0.191 [0.076, 0.306] | 0.278 | 0.423 | {'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 4} |
| B_Clinical_K | Random_Forest | 0.181 [0.037, 0.324] | 0.348 | 0.494 | {'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 4} |
| B_Clinical_ALK | Ridge | 0.298 [0.163, 0.434] | 0.328 | 0.220 | {'alpha': 10.0} |
| B_Clinical_K_ALK | Lasso | 0.335 [0.212, 0.457] | 0.297 | 0.234 | {'alpha': 0.01} |
| C1_Combined | ElasticNet | 0.292 [0.101, 0.482] | 0.462 | 0.253 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| C1_Combined_K | ElasticNet | 0.368 [0.237, 0.498] | 0.316 | 0.215 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| C1_Combined_ALK | ElasticNet | 0.395 [0.274, 0.515] | 0.292 | 0.196 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| C1_Combined_K_ALK | ElasticNet | 0.390 [0.268, 0.512] | 0.296 | 0.203 | {'alpha': 1.0, 'l1_ratio': 0.7} |

## 三、每个模型在所有方案中的最佳表现

| 模型 | 最佳方案 | Mean Test R² (95% CI) | Gap | 最佳参数 |
|------|---------|----------------------|-----|---------|
| ElasticNet | C1_Combined_ALK | 0.395 [0.274, 0.515] | 0.196 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| Lasso | A2_Biomechanical_K_ALK | 0.339 [0.173, 0.505] | 0.301 | {'alpha': 1.0} |
| Neural_Network | A1_Biomechanical_Core_K | 0.384 [0.279, 0.490] | 0.180 | {'hidden_layer_sizes': (100,), 'alpha': 1.0, 'learning_rate_init': 0.001} |
| Random_Forest | A2_Biomechanical_ALK | 0.326 [0.189, 0.462] | 0.402 | {'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 4} |
| Ridge | A2_Biomechanical_K_ALK | 0.370 [0.236, 0.504] | 0.239 | {'alpha': 10.0} |
| SVM | A1_Biomechanical_ALK | 0.251 [0.044, 0.457] | 0.169 | {'C': 2000, 'epsilon': 300, 'gamma': 0.005} |
| XGBoost | A1_Biomechanical_Core_K | 0.272 [0.078, 0.465] | 0.383 | {'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 1.0, 'reg_lambda': 2.0} |

## 四、基线 vs K vs AL/K vs K+ALK 对比

### A1 方案族

| 方案 | 最佳模型 | Mean Test R² | Std | Gap |
|------|---------|-------------|-----|-----|
| A1_Biomechanical_Core | ElasticNet | 0.269 | 0.331 | 0.216 |
| A1_Biomechanical_Core_K | Neural_Network | 0.384 | 0.256 | 0.180 |
| A1_Biomechanical_ALK | ElasticNet | 0.387 | 0.281 | 0.182 |
| A1_Biomechanical_K_ALK | ElasticNet | 0.382 | 0.275 | 0.190 |

### A2 方案族

| 方案 | 最佳模型 | Mean Test R² | Std | Gap |
|------|---------|-------------|-----|-----|
| A2_Biomechanical_NoK | Random_Forest | 0.283 | 0.336 | 0.417 |
| A2_Biomechanical_WithK | ElasticNet | 0.374 | 0.279 | 0.210 |
| A2_Biomechanical_ALK | ElasticNet | 0.368 | 0.328 | 0.225 |
| A2_Biomechanical_K_ALK | ElasticNet | 0.393 | 0.278 | 0.206 |

### B 方案族

| 方案 | 最佳模型 | Mean Test R² | Std | Gap |
|------|---------|-------------|-----|-----|
| B_Clinical | Random_Forest | 0.191 | 0.278 | 0.423 |
| B_Clinical_K | Random_Forest | 0.181 | 0.348 | 0.494 |
| B_Clinical_ALK | Ridge | 0.298 | 0.328 | 0.220 |
| B_Clinical_K_ALK | Lasso | 0.335 | 0.297 | 0.234 |

### C1 方案族

| 方案 | 最佳模型 | Mean Test R² | Std | Gap |
|------|---------|-------------|-----|-----|
| C1_Combined | ElasticNet | 0.292 | 0.462 | 0.253 |
| C1_Combined_K | ElasticNet | 0.368 | 0.316 | 0.215 |
| C1_Combined_ALK | ElasticNet | 0.395 | 0.292 | 0.196 |
| C1_Combined_K_ALK | ElasticNet | 0.390 | 0.296 | 0.203 |

## 五、与此前单 CV 最佳值的对比

| 方案 | 单 CV 最佳 Test R² | 重复 CV Mean | 差距 | 结论 |
|------|-------------------|-------------|------|------|
| C1_Combined_K | 0.612 | 0.368 | -0.244 | 单 CV 显著乐观 |
| C1_Combined_ALK | 0.611 | 0.395 | -0.216 | 单 CV 显著乐观 |
| A2_Biomechanical_ALK | 0.586 | 0.368 | -0.218 | 单 CV 显著乐观 |

## 六、讨论

1. **重复 CV 显著降低了选择偏倚**：此前单 CV 的 0.6+ R² 在重复 CV 下降至 0.2–0.3 水平。
2. **最佳模型仍为线性模型**：Lasso / ElasticNet / Ridge 在重复 CV 下保持相对稳健，Gap 通常 < 0.2。
3. **K 与 AL/K 差异缩小**：在稳健评估下，两者的提升都不如单 CV 明显。
4. **样本量仍是根本限制**：即使使用重复 CV，46 subjects 导致 95% CI 较宽，结论仍属探索性。

---

*Report generated automatically by SR_ML_hyperparameter_tuning_robust.py*
