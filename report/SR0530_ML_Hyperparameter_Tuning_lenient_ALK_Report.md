# SR0530 ML 超参数寻优报告：AL/K 替代与叠加 K（lenient，lenient_ALK）

> **目标**：在 71 眼 lenient 数据集上，比较用 AL/K 替代 K、以及在 K 基础上再叠加 AL/K 后，局部锥细胞密度预测能力的变化。

> **搜索策略**：Random Search + GroupKFold by Subject，每模型 30 组参数

> **象限策略**：≥1 象限可用（放宽，outer merge 取平均）

> **数据组**：lenient（71 眼 / 46 subjects）

> **置信区间说明**：Test R² 与 RMSE 后的 95% CI 基于 5-fold CV 的 fold-level 标准差，使用 t 分布近似（t₀.₀₂₅,₄ = 2.776）。

---

## 一、参数搜索空间

| 模型 | 参数 | 搜索范围 |
|------|------|---------|
| SVM | C | 100, 500, 1000, 2000, 5000 |
| SVM | epsilon | 100, 300, 500, 800, 1000 |
| SVM | gamma | 0.001, 0.005, 0.01, 0.03, 0.05, 0.1 |
| Random_Forest | n_estimators | 50, 100, 200, 300 |
| Random_Forest | max_depth | 2, 3, 4, 5, None |
| Random_Forest | min_samples_split | 2, 5, 10 |
| Random_Forest | min_samples_leaf | 1, 2, 4 |
| XGBoost | learning_rate | 0.001, 0.005, 0.01, 0.05, 0.1 |
| XGBoost | max_depth | 1, 2, 3, 4 |
| XGBoost | n_estimators | 30, 50, 100, 200 |
| XGBoost | reg_alpha | 0.1, 0.5, 1.0, 2.0 |
| XGBoost | reg_lambda | 0.1, 0.5, 1.0, 2.0 |
| Neural_Network | hidden_layer_sizes | (40,), (60,), (80,), (100,), (80, 40) |
| Neural_Network | alpha | 0.1, 0.3, 0.5, 1.0 |
| Neural_Network | learning_rate_init | 0.0001, 0.0005, 0.001 |
| Lasso | alpha | 0.001, 0.01, 0.1, 1.0, 10.0 |
| ElasticNet | alpha | 0.001, 0.01, 0.1, 1.0 |
| ElasticNet | l1_ratio | 0.1, 0.3, 0.5, 0.7, 0.9 |
| Ridge | alpha | 0.01, 0.1, 1.0, 10.0, 100.0 |

## 二、总体最佳配置

- **数据组**：lenient
- **距离**：1.5 mm
- **方案**：C1_Combined_K
- **模型**：Lasso
- **最佳 Test R²**：0.612 [95% CI: 0.359, 0.864]
- **最佳 RMSE**：447.8 [95% CI: 183.5, 712.0]
- **最佳参数**：{'alpha': 10.0}
- **样本量**：71 眼 / 46 subjects

## 三、各距离最佳结果

| 距离 (mm) | 最佳方案 | 最佳模型 | Test R² (95% CI) | MAPE (%) | RMSE (95% CI) | Gap | 最佳参数 |
|-----------|---------|---------|------------------|----------|----------------|-----|---------|
| 1.0 | A1_Biomechanical_Core_K | XGBoost | 0.515 [0.395, 0.635] | 10.53 | 511.7 [348.7, 674.8] | 0.206 | {'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 1.0} |
| 1.5 | C1_Combined_K | Lasso | 0.612 [0.359, 0.864] | 8.07 | 447.8 [183.5, 712.0] | 0.005 | {'alpha': 10.0} |
| 2.0 | A2_Biomechanical_ALK | ElasticNet | 0.527 [0.321, 0.733] | 9.39 | 424.8 [217.2, 632.5] | 0.060 | {'alpha': 0.001, 'l1_ratio': 0.5} |
| 2.5 | A2_Biomechanical_ALK | Lasso | 0.485 [0.147, 0.823] | 11.85 | 406.3 [223.4, 589.1] | 0.111 | {'alpha': 10.0} |
| 3.0 | A2_Biomechanical_ALK | Ridge | 0.498 [0.031, 0.965] | 10.89 | 321.0 [225.0, 417.0] | 0.312 | {'alpha': 0.1} |
| 3.5 | A2_Biomechanical_K_ALK | Lasso | 0.418 [0.195, 0.640] | 14.22 | 480.5 [291.4, 669.6] | 0.108 | {'alpha': 10.0} |
| 4.0 | A2_Biomechanical_ALK | Lasso | 0.387 [0.073, 0.702] | 18.69 | 567.4 [411.2, 723.5] | 0.109 | {'alpha': 10.0} |
| 4.5 | A2_Biomechanical_WithK | Lasso | 0.337 [-0.061, 0.735] | 19.11 | 543.8 [405.8, 681.9] | 0.192 | {'alpha': 10.0} |
| 5.0 | A2_Biomechanical_ALK | Random_Forest | 0.458 [0.254, 0.662] | 17.43 | 476.3 [343.3, 609.2] | 0.448 | {'n_estimators': 100, 'max_depth': 5, 'min_samples_split': 2, 'min_samples_leaf': 1} |
| 5.5 | C1_Combined | XGBoost | 0.384 [0.146, 0.621] | 25.10 | 646.1 [450.3, 842.0] | 0.285 | {'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 50, 'reg_alpha': 2.0, 'reg_lambda': 0.1} |
| 6.0 | A2_Biomechanical_ALK | Neural_Network | 0.466 [0.291, 0.642] | 20.74 | 604.9 [404.7, 805.1] | 0.190 | {'hidden_layer_sizes': (80,), 'alpha': 0.5, 'learning_rate_init': 0.001} |

## 四、每个模型最佳结果

| 模型 | 最佳距离 | 最佳方案 | Test R² (95% CI) | MAPE (%) | 最佳参数 |
|------|---------|---------|------------------|----------|---------|
| ElasticNet | 1.5 mm | B_Clinical_K_ALK | 0.608 [0.355, 0.861] | 8.12 | {'alpha': 0.001, 'l1_ratio': 0.5} |
| Lasso | 1.5 mm | C1_Combined_K | 0.612 [0.359, 0.864] | 8.07 | {'alpha': 10.0} |
| Neural_Network | 1.5 mm | C1_Combined_K_ALK | 0.514 [0.247, 0.781] | 9.24 | {'hidden_layer_sizes': (80,), 'alpha': 1.0, 'learning_rate_init': 0.0001} |
| Random_Forest | 1.5 mm | A2_Biomechanical_ALK | 0.567 [0.285, 0.848] | 8.89 | {'n_estimators': 200, 'max_depth': None, 'min_samples_split': 2, 'min_samples_leaf': 4} |
| Ridge | 1.5 mm | A2_Biomechanical_ALK | 0.585 [0.456, 0.715] | 8.87 | {'alpha': 0.1} |
| SVM | 1.0 mm | A1_Biomechanical_Core | 0.458 [0.305, 0.610] | 10.83 | {'C': 5000, 'epsilon': 100, 'gamma': 0.05} |
| XGBoost | 1.5 mm | A1_Biomechanical_Core_K | 0.563 [0.310, 0.817] | 9.21 | {'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 1.0} |

## 五、每个特征方案最佳结果

| 方案 | 最佳距离 | 最佳模型 | Test R² (95% CI) |
|------|---------|---------|------------------|
| A1_Biomechanical_Core | 1.0 mm | SVM | 0.458 [0.305, 0.610] |
| A2_Biomechanical_NoK | 1.5 mm | Random_Forest | 0.506 [0.301, 0.711] |
| B_Clinical | 5.5 mm | XGBoost | 0.369 [0.165, 0.572] |
| C1_Combined | 1.5 mm | Lasso | 0.538 [0.312, 0.764] |
| A1_Biomechanical_Core_K | 1.5 mm | XGBoost | 0.563 [0.310, 0.817] |
| A2_Biomechanical_WithK | 1.5 mm | Lasso | 0.574 [0.450, 0.697] |
| B_Clinical_K | 1.0 mm | Random_Forest | 0.374 [0.086, 0.661] |
| C1_Combined_K | 1.5 mm | Lasso | 0.612 [0.359, 0.864] |
| A1_Biomechanical_ALK | 1.5 mm | Random_Forest | 0.544 [0.437, 0.652] |
| A1_Biomechanical_K_ALK | 1.5 mm | Random_Forest | 0.553 [0.306, 0.800] |
| A2_Biomechanical_ALK | 1.5 mm | Lasso | 0.586 [0.454, 0.718] |
| A2_Biomechanical_K_ALK | 1.5 mm | Ridge | 0.577 [0.435, 0.720] |
| B_Clinical_ALK | 1.5 mm | Lasso | 0.537 [0.285, 0.788] |
| B_Clinical_K_ALK | 1.5 mm | ElasticNet | 0.608 [0.355, 0.861] |
| C1_Combined_ALK | 1.5 mm | Lasso | 0.611 [0.356, 0.867] |
| C1_Combined_K_ALK | 1.5 mm | Lasso | 0.611 [0.356, 0.867] |

## 六、Baseline vs K vs AL/K vs K+ALK 对比

按方案族比较同一基础方案下加入 K、AL/K、K+AL/K 后的最佳 Test R²。

### A1 方案族

| 距离 (mm) | A1_Biomechanical_Core | A1_Biomechanical_Core_K | A1_Biomechanical_ALK | A1_Biomechanical_K_ALK |
|-----------|---------|---------|---------|---------|
| 1.0 | 0.458 | 0.515 | 0.437 | 0.451 |
| 1.5 | 0.443 | 0.563 | 0.544 | 0.553 |
| 2.0 | 0.421 | 0.462 | 0.481 | 0.470 |
| 2.5 | 0.376 | 0.376 | 0.379 | 0.379 |
| 3.0 | 0.334 | 0.423 | 0.426 | 0.422 |
| 3.5 | 0.312 | 0.316 | 0.304 | 0.300 |
| 4.0 | 0.245 | 0.242 | 0.258 | 0.247 |
| 4.5 | 0.276 | 0.266 | 0.286 | 0.267 |
| 5.0 | 0.329 | 0.343 | 0.428 | 0.415 |
| 5.5 | 0.288 | 0.335 | 0.373 | 0.375 |
| 6.0 | 0.345 | 0.360 | 0.385 | 0.396 |

### A2 方案族

| 距离 (mm) | A2_Biomechanical_NoK | A2_Biomechanical_WithK | A2_Biomechanical_ALK | A2_Biomechanical_K_ALK |
|-----------|---------|---------|---------|---------|
| 1.0 | 0.410 | 0.455 | 0.450 | 0.445 |
| 1.5 | 0.506 | 0.574 | 0.586 | 0.577 |
| 2.0 | 0.398 | 0.520 | 0.527 | 0.524 |
| 2.5 | 0.300 | 0.476 | 0.485 | 0.485 |
| 3.0 | 0.325 | 0.495 | 0.498 | 0.495 |
| 3.5 | 0.372 | 0.412 | 0.418 | 0.418 |
| 4.0 | 0.259 | 0.384 | 0.387 | 0.387 |
| 4.5 | 0.301 | 0.337 | 0.335 | 0.335 |
| 5.0 | 0.410 | 0.407 | 0.458 | 0.446 |
| 5.5 | 0.368 | 0.377 | 0.376 | 0.376 |
| 6.0 | 0.377 | 0.420 | 0.466 | 0.418 |

### B 方案族

| 距离 (mm) | B_Clinical | B_Clinical_K | B_Clinical_ALK | B_Clinical_K_ALK |
|-----------|---------|---------|---------|---------|
| 1.0 | 0.312 | 0.374 | 0.439 | 0.417 |
| 1.5 | 0.320 | 0.358 | 0.537 | 0.608 |
| 2.0 | 0.234 | 0.302 | 0.442 | 0.486 |
| 2.5 | 0.246 | 0.237 | 0.283 | 0.411 |
| 3.0 | 0.240 | 0.297 | 0.321 | 0.383 |
| 3.5 | 0.227 | 0.232 | 0.266 | 0.267 |
| 4.0 | 0.244 | 0.248 | 0.285 | 0.291 |
| 4.5 | 0.274 | 0.266 | 0.286 | 0.300 |
| 5.0 | 0.347 | 0.354 | 0.395 | 0.386 |
| 5.5 | 0.369 | 0.325 | 0.374 | 0.364 |
| 6.0 | 0.312 | 0.291 | 0.413 | 0.347 |

### C1 方案族

| 距离 (mm) | C1_Combined | C1_Combined_K | C1_Combined_ALK | C1_Combined_K_ALK |
|-----------|---------|---------|---------|---------|
| 1.0 | 0.433 | 0.444 | 0.446 | 0.451 |
| 1.5 | 0.538 | 0.612 | 0.611 | 0.611 |
| 2.0 | 0.474 | 0.505 | 0.500 | 0.500 |
| 2.5 | 0.376 | 0.418 | 0.421 | 0.421 |
| 3.0 | 0.376 | 0.402 | 0.399 | 0.399 |
| 3.5 | 0.321 | 0.295 | 0.331 | 0.312 |
| 4.0 | 0.311 | 0.275 | 0.296 | 0.277 |
| 4.5 | 0.290 | 0.308 | 0.312 | 0.310 |
| 5.0 | 0.381 | 0.376 | 0.370 | 0.380 |
| 5.5 | 0.384 | 0.345 | 0.363 | 0.359 |
| 6.0 | 0.352 | 0.364 | 0.390 | 0.363 |

## 七、各方案平均 Test R²（跨距离/模型）

| 方案 | 平均 Test R² |
|------|-------------|
| A2_Biomechanical_K_ALK | 0.363 |
| A2_Biomechanical_ALK | 0.362 |
| A2_Biomechanical_WithK | 0.352 |
| C1_Combined_ALK | 0.347 |
| C1_Combined_K_ALK | 0.344 |
| A1_Biomechanical_ALK | 0.336 |
| A1_Biomechanical_K_ALK | 0.334 |
| A1_Biomechanical_Core_K | 0.323 |
| C1_Combined_K | 0.321 |
| C1_Combined | 0.318 |
| B_Clinical_K_ALK | 0.309 |
| B_Clinical_ALK | 0.304 |
| A1_Biomechanical_Core | 0.297 |
| A2_Biomechanical_NoK | 0.266 |
| B_Clinical_K | 0.219 |
| B_Clinical | 0.217 |

## 八、讨论

1. **AL/K 的替代效应**：若某基础方案的 AL/K 版本（*_ALK）R² 高于 K 版本（*_K），说明 AL/K 比 K 更能捕捉与局部密度相关的眼形态信息。
2. **AL/K 的叠加效应**：若 K+ALK 版本（*_K_ALK）高于单独 K 或 AL/K，说明两者提供互补信息。
3. **模型稳定性**：线性模型（Lasso/ElasticNet/Ridge）在本任务中通常更稳定，Gap 较小；树模型和神经网络可能过拟合。
4. **距离模式**：最佳预测通常出现在 1.5–2.0 mm，随距离增加 R² 下降。
5. **论文建议**：选择 R² 最高且跨距离稳定的方案作为最终模型；若 AL/K 与 K 高度相关，则优先选择更简洁的单一特征版本。

---

*Report generated automatically by SR_ML_hyperparameter_tuning_with_ALK.py*
