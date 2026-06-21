# SR0530 ML 超参数寻优报告：加入角膜曲率 K（q1plus_K）

> **目标**：在原有基线方案（A1/A2/B/C1）基础上加入角膜曲率（K），评估 K 对局部锥细胞密度预测能力的提升。

> **搜索策略**：Random Search + GroupKFold by Subject，每模型 30 组参数

> **象限策略**：q1plus_K

> **数据组**：`CleanDataRoi_strict/`（任意 ROI >7000 剔除）和 `CleanDataRoi_lenient/`（距离平均 >7000 剔除）

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

## 三、每个数据组的最佳结果（按距离）

### STRICT 数据组

| 距离 (mm) | 最佳方案 | 最佳模型 | Test R² (95% CI) | MAPE (%) | RMSE (95% CI) | Gap | 最佳参数 |
|-----------|---------|---------|------------------|----------|----------------|-----|---------|
| 1.0 | A1_Biomechanical_Core_K | Ridge | 0.502 [0.221, 0.783] | 8.32 | 386.4 [252.6, 520.2] | 0.066 | `{'alpha': 0.1}` |
| 1.5 | A2_Biomechanical_NoK | Random_Forest | 0.557 [0.375, 0.739] | 8.32 | 383.7 [210.7, 556.8] | 0.280 | `{'n_estimators': 100, 'max_depth': 3, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| 2.0 | A2_Biomechanical_WithK | Ridge | 0.497 [0.301, 0.694] | 9.12 | 369.1 [205.4, 532.7] | 0.033 | `{'alpha': 10.0}` |
| 2.5 | A2_Biomechanical_WithK | Neural_Network | 0.551 [0.297, 0.806] | 10.18 | 319.9 [222.9, 417.0] | 0.264 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.5, 'learning_rate_init': 0.0005}` |
| 3.0 | A2_Biomechanical_WithK | Neural_Network | 0.565 [0.321, 0.809] | 9.84 | 352.1 [185.8, 518.5] | 0.301 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.5, 'learning_rate_init': 0.0005}` |
| 3.5 | A2_Biomechanical_WithK | Ridge | 0.487 [0.185, 0.789] | 12.87 | 332.3 [187.1, 477.4] | 0.181 | `{'alpha': 0.01}` |
| 4.0 | C1_Combined | Ridge | 0.399 [0.191, 0.607] | 15.92 | 470.3 [361.0, 579.6] | 0.105 | `{'alpha': 10.0}` |
| 4.5 | C1_Combined | Ridge | 0.414 [0.164, 0.663] | 17.05 | 467.5 [359.0, 576.0] | 0.099 | `{'alpha': 10.0}` |
| 5.0 | A2_Biomechanical_WithK | ElasticNet | 0.428 [0.284, 0.572] | 20.95 | 569.8 [491.5, 648.0] | 0.152 | `{'alpha': 0.1, 'l1_ratio': 0.3}` |
| 5.5 | A2_Biomechanical_WithK | Ridge | 0.393 [0.220, 0.566] | 23.16 | 621.8 [451.1, 792.5] | 0.126 | `{'alpha': 10.0}` |
| 6.0 | C1_Combined_K | Neural_Network | 0.431 [0.195, 0.667] | 22.37 | 548.2 [342.1, 754.2] | 0.189 | `{'hidden_layer_sizes': (60,), 'alpha': 1.0, 'learning_rate_init': 0.001}` |

### LENIENT 数据组

| 距离 (mm) | 最佳方案 | 最佳模型 | Test R² (95% CI) | MAPE (%) | RMSE (95% CI) | Gap | 最佳参数 |
|-----------|---------|---------|------------------|----------|----------------|-----|---------|
| 1.0 | A1_Biomechanical_Core_K | XGBoost | 0.515 [0.395, 0.635] | 10.53 | 511.7 [348.7, 674.8] | 0.206 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 1.0}` |
| 1.5 | C1_Combined_K | Lasso | 0.612 [0.359, 0.864] | 8.07 | 447.8 [183.5, 712.0] | 0.005 | `{'alpha': 10.0}` |
| 2.0 | A2_Biomechanical_WithK | ElasticNet | 0.520 [0.314, 0.726] | 9.46 | 427.8 [219.5, 636.0] | 0.064 | `{'alpha': 0.001, 'l1_ratio': 0.5}` |
| 2.5 | A2_Biomechanical_WithK | Lasso | 0.476 [0.144, 0.808] | 11.98 | 411.2 [232.5, 589.9] | 0.115 | `{'alpha': 10.0}` |
| 3.0 | A2_Biomechanical_WithK | Lasso | 0.495 [0.029, 0.961] | 10.92 | 322.3 [225.6, 418.9] | 0.313 | `{'alpha': 0.01}` |
| 3.5 | A2_Biomechanical_WithK | Lasso | 0.412 [0.187, 0.637] | 14.24 | 482.5 [297.4, 667.6] | 0.114 | `{'alpha': 10.0}` |
| 4.0 | A2_Biomechanical_WithK | Lasso | 0.384 [0.070, 0.698] | 18.77 | 569.5 [411.5, 727.5] | 0.110 | `{'alpha': 10.0}` |
| 4.5 | A2_Biomechanical_WithK | Lasso | 0.337 [-0.061, 0.735] | 19.11 | 543.8 [405.8, 681.9] | 0.192 | `{'alpha': 10.0}` |
| 5.0 | A2_Biomechanical_NoK | Random_Forest | 0.410 [0.310, 0.511] | 18.30 | 578.4 [431.0, 725.9] | 0.331 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| 5.5 | C1_Combined | XGBoost | 0.384 [0.146, 0.621] | 25.10 | 646.1 [450.3, 842.0] | 0.285 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 50, 'reg_alpha': 2.0, 'reg_lambda': 0.1}` |
| 6.0 | A2_Biomechanical_WithK | Neural_Network | 0.420 [0.344, 0.496] | 21.71 | 637.4 [449.5, 825.2] | 0.224 | `{'hidden_layer_sizes': (80,), 'alpha': 0.5, 'learning_rate_init': 0.001}` |

## 四、每个模型在每个数据组的最佳结果

| 数据组 | 模型 | 最佳距离 | 最佳方案 | Test R² (95% CI) | MAPE (%) | 最佳参数 |
|--------|------|---------|---------|------------------|----------|---------|
| strict | ElasticNet | 1.5 mm | A1_Biomechanical_Core_K | 0.505 [0.391, 0.618] | 8.14 | `{'alpha': 0.001, 'l1_ratio': 0.1}` |
| strict | Lasso | 2.5 mm | A2_Biomechanical_WithK | 0.512 [0.221, 0.803] | 10.74 | `{'alpha': 0.001}` |
| strict | Neural_Network | 3.0 mm | A2_Biomechanical_WithK | 0.565 [0.321, 0.809] | 9.84 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.5, 'learning_rate_init': 0.0005}` |
| strict | Random_Forest | 1.5 mm | A2_Biomechanical_NoK | 0.557 [0.375, 0.739] | 8.32 | `{'n_estimators': 100, 'max_depth': 3, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| strict | Ridge | 2.5 mm | A2_Biomechanical_WithK | 0.512 [0.221, 0.803] | 10.74 | `{'alpha': 0.01}` |
| strict | SVM | 2.5 mm | A1_Biomechanical_Core_K | 0.449 [0.284, 0.615] | 11.85 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | XGBoost | 1.5 mm | A1_Biomechanical_Core_K | 0.439 [0.107, 0.771] | 9.47 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 50, 'reg_alpha': 2.0, 'reg_lambda': 0.1}` |
| lenient | ElasticNet | 1.5 mm | C1_Combined_K | 0.606 [0.358, 0.854] | 8.23 | `{'alpha': 0.001, 'l1_ratio': 0.5}` |
| lenient | Lasso | 1.5 mm | C1_Combined_K | 0.612 [0.359, 0.864] | 8.07 | `{'alpha': 10.0}` |
| lenient | Neural_Network | 1.5 mm | A1_Biomechanical_Core_K | 0.485 [0.190, 0.779] | 9.06 | `{'hidden_layer_sizes': (80,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| lenient | Random_Forest | 1.5 mm | A1_Biomechanical_Core_K | 0.550 [0.295, 0.805] | 8.56 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| lenient | Ridge | 1.5 mm | A2_Biomechanical_WithK | 0.574 [0.453, 0.695] | 9.04 | `{'alpha': 0.1}` |
| lenient | SVM | 1.0 mm | A1_Biomechanical_Core | 0.458 [0.305, 0.610] | 10.83 | `{'C': 5000, 'epsilon': 100, 'gamma': 0.05}` |
| lenient | XGBoost | 1.5 mm | A1_Biomechanical_Core_K | 0.563 [0.310, 0.817] | 9.21 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 1.0}` |

## 五、每个特征方案的最佳结果

| 方案 | 数据组 | 最佳距离 | 最佳模型 | Test R² (95% CI) |
|------|--------|---------|---------|------------------|
| A1_Biomechanical_Core | strict | 1.5 mm | Random_Forest | 0.512 [0.344, 0.679] |
| A2_Biomechanical_NoK | strict | 1.5 mm | Random_Forest | 0.557 [0.375, 0.739] |
| B_Clinical | lenient | 5.5 mm | XGBoost | 0.369 [0.165, 0.572] |
| C1_Combined | lenient | 1.5 mm | Lasso | 0.538 [0.312, 0.764] |
| A1_Biomechanical_Core_K | lenient | 1.5 mm | XGBoost | 0.563 [0.310, 0.817] |
| A2_Biomechanical_WithK | lenient | 1.5 mm | Lasso | 0.574 [0.450, 0.697] |
| B_Clinical_K | lenient | 1.0 mm | Random_Forest | 0.374 [0.086, 0.661] |
| C1_Combined_K | lenient | 1.5 mm | Lasso | 0.612 [0.359, 0.864] |

## 六、基线方案 vs 加入角膜曲率 (K) 的对比

对每个基线方案及其 +K 版本，按数据组和距离汇总最佳 Test R² 的变化（ΔR² = +K - baseline）。

| 基线方案 | +K 方案 | 数据组 | 距离 (mm) | 基线 R² | +K R² | ΔR² | 改善 ||----------|---------|--------|-----------|---------|-------|-----|------|| A1_Biomechanical_Core | A1_Biomechanical_Core_K | strict | 1.0 | 0.499 | 0.502 | +0.003 | 持平 || A1_Biomechanical_Core | A1_Biomechanical_Core_K | strict | 1.5 | 0.512 | 0.508 | -0.004 | 持平 || A1_Biomechanical_Core | A1_Biomechanical_Core_K | strict | 2.0 | 0.429 | 0.438 | +0.009 | 持平 || A1_Biomechanical_Core | A1_Biomechanical_Core_K | strict | 2.5 | 0.440 | 0.486 | +0.046 | 是 || A1_Biomechanical_Core | A1_Biomechanical_Core_K | strict | 3.0 | 0.446 | 0.488 | +0.041 | 是 || A1_Biomechanical_Core | A1_Biomechanical_Core_K | strict | 3.5 | 0.392 | 0.389 | -0.003 | 持平 || A1_Biomechanical_Core | A1_Biomechanical_Core_K | strict | 4.0 | 0.339 | 0.348 | +0.009 | 持平 || A1_Biomechanical_Core | A1_Biomechanical_Core_K | strict | 4.5 | 0.365 | 0.355 | -0.011 | 否 || A1_Biomechanical_Core | A1_Biomechanical_Core_K | strict | 5.0 | 0.347 | 0.384 | +0.037 | 是 || A1_Biomechanical_Core | A1_Biomechanical_Core_K | strict | 5.5 | 0.339 | 0.353 | +0.014 | 是 || A1_Biomechanical_Core | A1_Biomechanical_Core_K | strict | 6.0 | 0.351 | 0.357 | +0.006 | 持平 || A1_Biomechanical_Core | A1_Biomechanical_Core_K | lenient | 1.0 | 0.458 | 0.515 | +0.057 | 是 || A1_Biomechanical_Core | A1_Biomechanical_Core_K | lenient | 1.5 | 0.443 | 0.563 | +0.121 | 是 || A1_Biomechanical_Core | A1_Biomechanical_Core_K | lenient | 2.0 | 0.421 | 0.462 | +0.041 | 是 || A1_Biomechanical_Core | A1_Biomechanical_Core_K | lenient | 2.5 | 0.376 | 0.376 | -0.001 | 持平 || A1_Biomechanical_Core | A1_Biomechanical_Core_K | lenient | 3.0 | 0.334 | 0.423 | +0.088 | 是 || A1_Biomechanical_Core | A1_Biomechanical_Core_K | lenient | 3.5 | 0.312 | 0.316 | +0.004 | 持平 || A1_Biomechanical_Core | A1_Biomechanical_Core_K | lenient | 4.0 | 0.245 | 0.242 | -0.003 | 持平 || A1_Biomechanical_Core | A1_Biomechanical_Core_K | lenient | 4.5 | 0.276 | 0.266 | -0.010 | 持平 || A1_Biomechanical_Core | A1_Biomechanical_Core_K | lenient | 5.0 | 0.329 | 0.343 | +0.014 | 是 || A1_Biomechanical_Core | A1_Biomechanical_Core_K | lenient | 5.5 | 0.288 | 0.335 | +0.047 | 是 || A1_Biomechanical_Core | A1_Biomechanical_Core_K | lenient | 6.0 | 0.345 | 0.360 | +0.016 | 是 || A2_Biomechanical_NoK | A2_Biomechanical_WithK | strict | 1.0 | 0.492 | 0.486 | -0.006 | 持平 || A2_Biomechanical_NoK | A2_Biomechanical_WithK | strict | 1.5 | 0.557 | 0.492 | -0.065 | 否 || A2_Biomechanical_NoK | A2_Biomechanical_WithK | strict | 2.0 | 0.407 | 0.497 | +0.090 | 是 || A2_Biomechanical_NoK | A2_Biomechanical_WithK | strict | 2.5 | 0.434 | 0.551 | +0.117 | 是 || A2_Biomechanical_NoK | A2_Biomechanical_WithK | strict | 3.0 | 0.431 | 0.565 | +0.134 | 是 || A2_Biomechanical_NoK | A2_Biomechanical_WithK | strict | 3.5 | 0.372 | 0.487 | +0.115 | 是 || A2_Biomechanical_NoK | A2_Biomechanical_WithK | strict | 4.0 | 0.323 | 0.398 | +0.075 | 是 || A2_Biomechanical_NoK | A2_Biomechanical_WithK | strict | 4.5 | 0.337 | 0.389 | +0.053 | 是 || A2_Biomechanical_NoK | A2_Biomechanical_WithK | strict | 5.0 | 0.343 | 0.428 | +0.085 | 是 || A2_Biomechanical_NoK | A2_Biomechanical_WithK | strict | 5.5 | 0.355 | 0.393 | +0.038 | 是 || A2_Biomechanical_NoK | A2_Biomechanical_WithK | strict | 6.0 | 0.379 | 0.350 | -0.028 | 否 || A2_Biomechanical_NoK | A2_Biomechanical_WithK | lenient | 1.0 | 0.410 | 0.455 | +0.045 | 是 || A2_Biomechanical_NoK | A2_Biomechanical_WithK | lenient | 1.5 | 0.506 | 0.574 | +0.068 | 是 || A2_Biomechanical_NoK | A2_Biomechanical_WithK | lenient | 2.0 | 0.398 | 0.520 | +0.123 | 是 || A2_Biomechanical_NoK | A2_Biomechanical_WithK | lenient | 2.5 | 0.300 | 0.476 | +0.176 | 是 || A2_Biomechanical_NoK | A2_Biomechanical_WithK | lenient | 3.0 | 0.325 | 0.495 | +0.170 | 是 || A2_Biomechanical_NoK | A2_Biomechanical_WithK | lenient | 3.5 | 0.372 | 0.412 | +0.040 | 是 || A2_Biomechanical_NoK | A2_Biomechanical_WithK | lenient | 4.0 | 0.259 | 0.384 | +0.126 | 是 || A2_Biomechanical_NoK | A2_Biomechanical_WithK | lenient | 4.5 | 0.301 | 0.337 | +0.036 | 是 || A2_Biomechanical_NoK | A2_Biomechanical_WithK | lenient | 5.0 | 0.410 | 0.407 | -0.004 | 持平 || A2_Biomechanical_NoK | A2_Biomechanical_WithK | lenient | 5.5 | 0.368 | 0.377 | +0.009 | 持平 || A2_Biomechanical_NoK | A2_Biomechanical_WithK | lenient | 6.0 | 0.377 | 0.420 | +0.043 | 是 || B_Clinical | B_Clinical_K | strict | 1.0 | 0.356 | 0.308 | -0.048 | 否 || B_Clinical | B_Clinical_K | strict | 1.5 | 0.305 | 0.307 | +0.002 | 持平 || B_Clinical | B_Clinical_K | strict | 2.0 | 0.295 | 0.264 | -0.031 | 否 || B_Clinical | B_Clinical_K | strict | 2.5 | 0.119 | 0.216 | +0.097 | 是 || B_Clinical | B_Clinical_K | strict | 3.0 | 0.131 | 0.182 | +0.051 | 是 || B_Clinical | B_Clinical_K | strict | 3.5 | 0.105 | 0.114 | +0.009 | 持平 || B_Clinical | B_Clinical_K | strict | 4.0 | 0.292 | 0.209 | -0.083 | 否 || B_Clinical | B_Clinical_K | strict | 4.5 | 0.209 | 0.192 | -0.017 | 否 || B_Clinical | B_Clinical_K | strict | 5.0 | 0.222 | 0.288 | +0.066 | 是 || B_Clinical | B_Clinical_K | strict | 5.5 | 0.221 | 0.233 | +0.012 | 是 || B_Clinical | B_Clinical_K | strict | 6.0 | 0.216 | 0.221 | +0.005 | 持平 || B_Clinical | B_Clinical_K | lenient | 1.0 | 0.312 | 0.374 | +0.061 | 是 || B_Clinical | B_Clinical_K | lenient | 1.5 | 0.320 | 0.358 | +0.038 | 是 || B_Clinical | B_Clinical_K | lenient | 2.0 | 0.234 | 0.302 | +0.068 | 是 || B_Clinical | B_Clinical_K | lenient | 2.5 | 0.246 | 0.237 | -0.009 | 持平 || B_Clinical | B_Clinical_K | lenient | 3.0 | 0.240 | 0.297 | +0.057 | 是 || B_Clinical | B_Clinical_K | lenient | 3.5 | 0.227 | 0.232 | +0.005 | 持平 || B_Clinical | B_Clinical_K | lenient | 4.0 | 0.244 | 0.248 | +0.004 | 持平 || B_Clinical | B_Clinical_K | lenient | 4.5 | 0.274 | 0.266 | -0.008 | 持平 || B_Clinical | B_Clinical_K | lenient | 5.0 | 0.347 | 0.354 | +0.007 | 持平 || B_Clinical | B_Clinical_K | lenient | 5.5 | 0.369 | 0.325 | -0.044 | 否 || B_Clinical | B_Clinical_K | lenient | 6.0 | 0.312 | 0.291 | -0.021 | 否 || C1_Combined | C1_Combined_K | strict | 1.0 | 0.467 | 0.444 | -0.023 | 否 || C1_Combined | C1_Combined_K | strict | 1.5 | 0.468 | 0.510 | +0.042 | 是 || C1_Combined | C1_Combined_K | strict | 2.0 | 0.412 | 0.410 | -0.002 | 持平 || C1_Combined | C1_Combined_K | strict | 2.5 | 0.456 | 0.463 | +0.007 | 持平 || C1_Combined | C1_Combined_K | strict | 3.0 | 0.469 | 0.473 | +0.005 | 持平 || C1_Combined | C1_Combined_K | strict | 3.5 | 0.426 | 0.395 | -0.031 | 否 || C1_Combined | C1_Combined_K | strict | 4.0 | 0.399 | 0.336 | -0.063 | 否 || C1_Combined | C1_Combined_K | strict | 4.5 | 0.414 | 0.359 | -0.055 | 否 || C1_Combined | C1_Combined_K | strict | 5.0 | 0.331 | 0.368 | +0.037 | 是 || C1_Combined | C1_Combined_K | strict | 5.5 | 0.315 | 0.347 | +0.032 | 是 || C1_Combined | C1_Combined_K | strict | 6.0 | 0.371 | 0.431 | +0.061 | 是 || C1_Combined | C1_Combined_K | lenient | 1.0 | 0.433 | 0.444 | +0.011 | 是 || C1_Combined | C1_Combined_K | lenient | 1.5 | 0.538 | 0.612 | +0.074 | 是 || C1_Combined | C1_Combined_K | lenient | 2.0 | 0.474 | 0.505 | +0.031 | 是 || C1_Combined | C1_Combined_K | lenient | 2.5 | 0.376 | 0.418 | +0.042 | 是 || C1_Combined | C1_Combined_K | lenient | 3.0 | 0.376 | 0.402 | +0.026 | 是 || C1_Combined | C1_Combined_K | lenient | 3.5 | 0.321 | 0.295 | -0.026 | 否 || C1_Combined | C1_Combined_K | lenient | 4.0 | 0.311 | 0.275 | -0.036 | 否 || C1_Combined | C1_Combined_K | lenient | 4.5 | 0.290 | 0.308 | +0.018 | 是 || C1_Combined | C1_Combined_K | lenient | 5.0 | 0.381 | 0.376 | -0.005 | 持平 || C1_Combined | C1_Combined_K | lenient | 5.5 | 0.384 | 0.345 | -0.039 | 否 || C1_Combined | C1_Combined_K | lenient | 6.0 | 0.352 | 0.364 | +0.012 | 是 |
### 按方案汇总的平均 ΔR²

| 基线方案 | +K 方案 | strict 平均 ΔR² | lenient 平均 ΔR² | 总体平均 ΔR² ||----------|---------|-----------------|------------------|-------------|| A1_Biomechanical_Core | A1_Biomechanical_Core_K | +0.013 | +0.034 | +0.024 || A2_Biomechanical_NoK | A2_Biomechanical_WithK | +0.055 | +0.076 | +0.065 || B_Clinical | B_Clinical_K | +0.006 | +0.014 | +0.010 || C1_Combined | C1_Combined_K | +0.001 | +0.010 | +0.005 |
## 七、全部详细结果

| 数据组 | 距离 | 方案 | 模型 | N_Eyes | N_Subj | Train R² | Test R² (95% CI) | Corr | MAPE | RMSE (95% CI) | Gap | 最佳参数 |
|--------|------|------|------|--------|--------|----------|------------------|------|------|----------------|-----|---------|
| strict | 1.0 | A1_Biomechanical_Core | SVM | 69 | 44 | 0.359 | 0.262 [-0.067, 0.591] | 0.701 | 10.77 | 475.8 [312.4, 639.1] | 0.097 | `{'C': 500, 'epsilon': 800, 'gamma': 0.1}` |
| strict | 1.0 | A1_Biomechanical_Core | Random_Forest | 69 | 44 | 0.731 | 0.356 [-0.051, 0.763] | 0.667 | 10.92 | 509.8 [428.0, 591.5] | 0.375 | `{'n_estimators': 100, 'max_depth': 2, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| strict | 1.0 | A1_Biomechanical_Core | XGBoost | 69 | 44 | 0.764 | 0.408 [0.121, 0.695] | 0.684 | 9.24 | 422.2 [289.0, 555.4] | 0.355 | `{'learning_rate': 0.05, 'max_depth': 2, 'n_estimators': 100, 'reg_alpha': 2.0, 'reg_lambda': 1.0}` |
| strict | 1.0 | A1_Biomechanical_Core | Neural_Network | 69 | 44 | 0.576 | 0.436 [0.159, 0.713] | 0.683 | 9.17 | 413.6 [271.1, 556.2] | 0.140 | `{'hidden_layer_sizes': (100,), 'alpha': 0.5, 'learning_rate_init': 0.0001}` |
| strict | 1.0 | A1_Biomechanical_Core | Lasso | 69 | 44 | 0.552 | 0.499 [0.291, 0.707] | 0.721 | 8.51 | 391.2 [271.5, 510.8] | 0.053 | `{'alpha': 0.01}` |
| strict | 1.0 | A1_Biomechanical_Core | ElasticNet | 69 | 44 | 0.571 | 0.476 [0.263, 0.689] | 0.709 | 10.38 | 475.6 [301.3, 649.9] | 0.095 | `{'alpha': 0.001, 'l1_ratio': 0.3}` |
| strict | 1.0 | A1_Biomechanical_Core | Ridge | 69 | 44 | 0.552 | 0.499 [0.291, 0.707] | 0.721 | 8.51 | 391.2 [271.4, 511.0] | 0.053 | `{'alpha': 0.1}` |
| strict | 1.0 | A2_Biomechanical_NoK | SVM | 69 | 44 | 0.378 | 0.288 [0.041, 0.534] | 0.654 | 10.41 | 471.7 [311.0, 632.4] | 0.091 | `{'C': 500, 'epsilon': 800, 'gamma': 0.1}` |
| strict | 1.0 | A2_Biomechanical_NoK | Random_Forest | 69 | 44 | 0.810 | 0.336 [-0.026, 0.697] | 0.648 | 9.67 | 445.4 [340.0, 550.9] | 0.474 | `{'n_estimators': 100, 'max_depth': 3, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| strict | 1.0 | A2_Biomechanical_NoK | XGBoost | 69 | 44 | 0.820 | 0.357 [-0.015, 0.729] | 0.614 | 9.75 | 435.4 [289.6, 581.1] | 0.463 | `{'learning_rate': 0.05, 'max_depth': 2, 'n_estimators': 100, 'reg_alpha': 2.0, 'reg_lambda': 1.0}` |
| strict | 1.0 | A2_Biomechanical_NoK | Neural_Network | 69 | 44 | 0.480 | 0.355 [0.083, 0.628] | 0.629 | 9.31 | 441.7 [307.2, 576.2] | 0.125 | `{'hidden_layer_sizes': (100,), 'alpha': 0.5, 'learning_rate_init': 0.0001}` |
| strict | 1.0 | A2_Biomechanical_NoK | Lasso | 69 | 44 | 0.565 | 0.491 [0.258, 0.725] | 0.719 | 8.62 | 392.3 [275.7, 508.8] | 0.073 | `{'alpha': 0.01}` |
| strict | 1.0 | A2_Biomechanical_NoK | ElasticNet | 69 | 44 | 0.579 | 0.453 [0.197, 0.709] | 0.689 | 10.53 | 485.3 [293.3, 677.3] | 0.126 | `{'alpha': 0.001, 'l1_ratio': 0.3}` |
| strict | 1.0 | A2_Biomechanical_NoK | Ridge | 69 | 44 | 0.565 | 0.492 [0.258, 0.725] | 0.719 | 8.62 | 392.2 [275.5, 508.9] | 0.073 | `{'alpha': 0.1}` |
| strict | 1.0 | B_Clinical | SVM | 69 | 44 | 0.350 | 0.256 [0.040, 0.471] | 0.671 | 10.59 | 480.4 [343.3, 617.5] | 0.094 | `{'C': 500, 'epsilon': 800, 'gamma': 0.1}` |
| strict | 1.0 | B_Clinical | Random_Forest | 69 | 44 | 0.781 | 0.272 [0.022, 0.522] | 0.624 | 11.72 | 524.2 [385.9, 662.4] | 0.509 | `{'n_estimators': 300, 'max_depth': None, 'min_samples_split': 2, 'min_samples_leaf': 2}` |
| strict | 1.0 | B_Clinical | XGBoost | 69 | 44 | 0.528 | 0.356 [0.209, 0.504] | 0.667 | 11.39 | 494.1 [386.1, 602.2] | 0.172 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 50, 'reg_alpha': 2.0, 'reg_lambda': 0.1}` |
| strict | 1.0 | B_Clinical | Neural_Network | 69 | 44 | 0.509 | 0.263 [0.012, 0.515] | 0.618 | 12.44 | 567.6 [383.9, 751.4] | 0.246 | `{'hidden_layer_sizes': (60,), 'alpha': 1.0, 'learning_rate_init': 0.0005}` |
| strict | 1.0 | B_Clinical | Lasso | 69 | 44 | 0.489 | 0.300 [0.066, 0.533] | 0.665 | 11.67 | 550.5 [385.8, 715.2] | 0.189 | `{'alpha': 0.001}` |
| strict | 1.0 | B_Clinical | ElasticNet | 69 | 44 | 0.489 | 0.300 [0.067, 0.533] | 0.665 | 11.67 | 550.5 [385.6, 715.4] | 0.189 | `{'alpha': 0.001, 'l1_ratio': 0.3}` |
| strict | 1.0 | B_Clinical | Ridge | 69 | 44 | 0.552 | 0.308 [-0.176, 0.792] | 0.669 | 10.41 | 447.5 [298.3, 596.8] | 0.244 | `{'alpha': 10.0}` |
| strict | 1.0 | C1_Combined | SVM | 69 | 44 | 0.512 | 0.356 [0.079, 0.633] | 0.681 | 11.33 | 491.3 [332.7, 649.9] | 0.157 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 1.0 | C1_Combined | Random_Forest | 69 | 44 | 0.753 | 0.375 [0.057, 0.693] | 0.690 | 11.16 | 512.7 [422.9, 602.5] | 0.378 | `{'n_estimators': 100, 'max_depth': 2, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| strict | 1.0 | C1_Combined | XGBoost | 69 | 44 | 0.825 | 0.414 [0.036, 0.792] | 0.680 | 8.95 | 414.9 [246.4, 583.4] | 0.411 | `{'learning_rate': 0.05, 'max_depth': 2, 'n_estimators': 100, 'reg_alpha': 2.0, 'reg_lambda': 1.0}` |
| strict | 1.0 | C1_Combined | Neural_Network | 69 | 44 | 0.576 | 0.457 [0.289, 0.624] | 0.706 | 10.25 | 489.8 [320.3, 659.2] | 0.119 | `{'hidden_layer_sizes': (60,), 'alpha': 1.0, 'learning_rate_init': 0.0005}` |
| strict | 1.0 | C1_Combined | Lasso | 69 | 44 | 0.582 | 0.467 [0.229, 0.705] | 0.709 | 10.22 | 475.7 [299.2, 652.1] | 0.115 | `{'alpha': 0.001}` |
| strict | 1.0 | C1_Combined | ElasticNet | 69 | 44 | 0.582 | 0.467 [0.229, 0.705] | 0.709 | 10.22 | 475.6 [299.1, 652.1] | 0.115 | `{'alpha': 0.001, 'l1_ratio': 0.3}` |
| strict | 1.0 | C1_Combined | Ridge | 69 | 44 | 0.582 | 0.467 [0.229, 0.705] | 0.709 | 10.22 | 475.6 [299.2, 652.1] | 0.115 | `{'alpha': 0.01}` |
| strict | 1.5 | A1_Biomechanical_Core | SVM | 69 | 44 | 0.509 | 0.407 [0.135, 0.679] | 0.721 | 9.16 | 393.7 [193.1, 594.3] | 0.102 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.03}` |
| strict | 1.5 | A1_Biomechanical_Core | Random_Forest | 69 | 44 | 0.814 | 0.512 [0.344, 0.679] | 0.771 | 7.99 | 397.1 [242.5, 551.7] | 0.302 | `{'n_estimators': 100, 'max_depth': 3, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| strict | 1.5 | A1_Biomechanical_Core | XGBoost | 69 | 44 | 0.598 | 0.378 [0.024, 0.733] | 0.644 | 9.73 | 429.6 [243.8, 615.5] | 0.220 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 50, 'reg_alpha': 2.0, 'reg_lambda': 0.1}` |
| strict | 1.5 | A1_Biomechanical_Core | Neural_Network | 69 | 44 | 0.562 | 0.353 [0.153, 0.552] | 0.698 | 9.08 | 390.2 [284.5, 495.9] | 0.209 | `{'hidden_layer_sizes': (60,), 'alpha': 1.0, 'learning_rate_init': 0.001}` |
| strict | 1.5 | A1_Biomechanical_Core | Lasso | 69 | 44 | 0.573 | 0.408 [0.169, 0.648] | 0.685 | 8.57 | 368.2 [275.7, 460.7] | 0.165 | `{'alpha': 0.1}` |
| strict | 1.5 | A1_Biomechanical_Core | ElasticNet | 69 | 44 | 0.573 | 0.408 [0.168, 0.648] | 0.685 | 8.57 | 368.3 [275.8, 460.7] | 0.165 | `{'alpha': 0.001, 'l1_ratio': 0.1}` |
| strict | 1.5 | A1_Biomechanical_Core | Ridge | 69 | 44 | 0.573 | 0.406 [0.156, 0.656] | 0.683 | 8.60 | 368.4 [276.7, 460.0] | 0.167 | `{'alpha': 1.0}` |
| strict | 1.5 | A2_Biomechanical_NoK | SVM | 69 | 44 | 0.586 | 0.288 [-0.134, 0.709] | 0.532 | 9.87 | 429.7 [184.8, 674.6] | 0.299 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.03}` |
| strict | 1.5 | A2_Biomechanical_NoK | Random_Forest | 69 | 44 | 0.837 | 0.557 [0.375, 0.739] | 0.805 | 8.32 | 383.7 [210.7, 556.8] | 0.280 | `{'n_estimators': 100, 'max_depth': 3, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| strict | 1.5 | A2_Biomechanical_NoK | XGBoost | 69 | 44 | 0.816 | 0.385 [0.134, 0.637] | 0.713 | 8.37 | 370.7 [298.9, 442.6] | 0.431 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 2.0}` |
| strict | 1.5 | A2_Biomechanical_NoK | Neural_Network | 69 | 44 | 0.647 | 0.286 [-0.137, 0.710] | 0.642 | 10.60 | 485.3 [284.8, 685.8] | 0.360 | `{'hidden_layer_sizes': (60,), 'alpha': 0.3, 'learning_rate_init': 0.0005}` |
| strict | 1.5 | A2_Biomechanical_NoK | Lasso | 69 | 44 | 0.442 | 0.231 [-0.006, 0.469] | 0.549 | 11.75 | 545.4 [241.4, 849.4] | 0.211 | `{'alpha': 1.0}` |
| strict | 1.5 | A2_Biomechanical_NoK | ElasticNet | 69 | 44 | 0.486 | 0.237 [-0.154, 0.628] | 0.705 | 10.34 | 489.8 [366.4, 613.1] | 0.249 | `{'alpha': 0.01, 'l1_ratio': 0.1}` |
| strict | 1.5 | A2_Biomechanical_NoK | Ridge | 69 | 44 | 0.486 | 0.243 [-0.139, 0.625] | 0.705 | 10.32 | 488.6 [365.0, 612.2] | 0.243 | `{'alpha': 1.0}` |
| strict | 1.5 | B_Clinical | SVM | 69 | 44 | 0.260 | 0.091 [-0.119, 0.301] | 0.467 | 12.40 | 527.3 [422.5, 632.2] | 0.169 | `{'C': 2000, 'epsilon': 800, 'gamma': 0.05}` |
| strict | 1.5 | B_Clinical | Random_Forest | 69 | 44 | 0.679 | 0.173 [-0.232, 0.579] | 0.664 | 11.03 | 531.1 [325.6, 736.6] | 0.506 | `{'n_estimators': 100, 'max_depth': 3, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| strict | 1.5 | B_Clinical | XGBoost | 69 | 44 | 0.487 | 0.305 [-0.017, 0.626] | 0.589 | 11.23 | 458.2 [279.3, 637.1] | 0.183 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 50, 'reg_alpha': 2.0, 'reg_lambda': 0.1}` |
| strict | 1.5 | B_Clinical | Neural_Network | 69 | 44 | 0.576 | 0.232 [-0.135, 0.599] | 0.534 | 9.23 | 393.4 [314.5, 472.2] | 0.344 | `{'hidden_layer_sizes': (60,), 'alpha': 0.5, 'learning_rate_init': 0.0001}` |
| strict | 1.5 | B_Clinical | Lasso | 69 | 44 | 0.470 | 0.292 [-0.091, 0.675] | 0.552 | 8.99 | 379.3 [270.2, 488.4] | 0.177 | `{'alpha': 1.0}` |
| strict | 1.5 | B_Clinical | ElasticNet | 69 | 44 | 0.421 | 0.233 [-0.095, 0.560] | 0.535 | 9.57 | 399.3 [305.6, 492.9] | 0.188 | `{'alpha': 1.0, 'l1_ratio': 0.7}` |
| strict | 1.5 | B_Clinical | Ridge | 69 | 44 | 0.446 | 0.263 [-0.079, 0.605] | 0.541 | 9.31 | 389.7 [293.7, 485.8] | 0.183 | `{'alpha': 10.0}` |
| strict | 1.5 | C1_Combined | SVM | 69 | 44 | 0.527 | 0.366 [0.070, 0.662] | 0.689 | 9.74 | 406.1 [207.6, 604.7] | 0.161 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.03}` |
| strict | 1.5 | C1_Combined | Random_Forest | 69 | 44 | 0.740 | 0.468 [0.194, 0.742] | 0.750 | 8.09 | 341.7 [280.6, 402.8] | 0.272 | `{'n_estimators': 50, 'max_depth': 2, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| strict | 1.5 | C1_Combined | XGBoost | 69 | 44 | 0.611 | 0.400 [0.067, 0.733] | 0.662 | 9.81 | 422.2 [250.2, 594.2] | 0.211 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 50, 'reg_alpha': 2.0, 'reg_lambda': 0.1}` |
| strict | 1.5 | C1_Combined | Neural_Network | 69 | 44 | 0.612 | 0.294 [-0.083, 0.672] | 0.646 | 9.09 | 376.5 [277.5, 475.5] | 0.318 | `{'hidden_layer_sizes': (60,), 'alpha': 0.5, 'learning_rate_init': 0.0001}` |
| strict | 1.5 | C1_Combined | Lasso | 69 | 44 | 0.621 | 0.449 [0.315, 0.584] | 0.705 | 8.41 | 358.5 [280.1, 436.8] | 0.172 | `{'alpha': 0.1}` |
| strict | 1.5 | C1_Combined | ElasticNet | 69 | 44 | 0.621 | 0.450 [0.315, 0.584] | 0.705 | 8.41 | 358.3 [280.4, 436.3] | 0.171 | `{'alpha': 0.001, 'l1_ratio': 0.1}` |
| strict | 1.5 | C1_Combined | Ridge | 69 | 44 | 0.621 | 0.458 [0.312, 0.603] | 0.708 | 8.34 | 354.5 [283.0, 426.0] | 0.163 | `{'alpha': 1.0}` |
| strict | 2.0 | A1_Biomechanical_Core | SVM | 69 | 44 | 0.295 | 0.297 [0.019, 0.574] | 0.607 | 10.51 | 440.9 [234.5, 647.3] | -0.002 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 2.0 | A1_Biomechanical_Core | Random_Forest | 69 | 44 | 0.683 | 0.429 [0.293, 0.565] | 0.734 | 8.87 | 346.3 [233.9, 458.8] | 0.254 | `{'n_estimators': 50, 'max_depth': 2, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| strict | 2.0 | A1_Biomechanical_Core | XGBoost | 69 | 44 | 0.734 | 0.383 [0.208, 0.558] | 0.719 | 9.54 | 359.0 [249.2, 468.7] | 0.351 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 2.0}` |
| strict | 2.0 | A1_Biomechanical_Core | Neural_Network | 69 | 44 | 0.461 | 0.245 [-0.081, 0.571] | 0.541 | 11.81 | 440.1 [241.8, 638.3] | 0.216 | `{'hidden_layer_sizes': (80,), 'alpha': 0.3, 'learning_rate_init': 0.0001}` |
| strict | 2.0 | A1_Biomechanical_Core | Lasso | 69 | 44 | 0.492 | 0.339 [0.006, 0.672] | 0.615 | 9.43 | 365.9 [219.2, 512.5] | 0.153 | `{'alpha': 0.1}` |
| strict | 2.0 | A1_Biomechanical_Core | ElasticNet | 69 | 44 | 0.492 | 0.339 [0.006, 0.672] | 0.615 | 9.43 | 365.9 [219.3, 512.5] | 0.153 | `{'alpha': 0.001, 'l1_ratio': 0.1}` |
| strict | 2.0 | A1_Biomechanical_Core | Ridge | 69 | 44 | 0.450 | 0.339 [0.153, 0.526] | 0.696 | 10.44 | 375.8 [258.3, 493.2] | 0.111 | `{'alpha': 10.0}` |
| strict | 2.0 | A2_Biomechanical_NoK | SVM | 69 | 44 | 0.413 | 0.282 [0.007, 0.557] | 0.662 | 10.63 | 439.1 [350.1, 528.1] | 0.131 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 2.0 | A2_Biomechanical_NoK | Random_Forest | 69 | 44 | 0.783 | 0.407 [0.174, 0.640] | 0.664 | 10.55 | 406.8 [200.9, 612.6] | 0.376 | `{'n_estimators': 100, 'max_depth': 3, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| strict | 2.0 | A2_Biomechanical_NoK | XGBoost | 69 | 44 | 0.780 | 0.352 [0.116, 0.588] | 0.700 | 9.35 | 361.3 [265.8, 456.9] | 0.429 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 2.0}` |
| strict | 2.0 | A2_Biomechanical_NoK | Neural_Network | 69 | 44 | 0.559 | 0.188 [-0.094, 0.471] | 0.555 | 11.48 | 451.0 [276.2, 625.7] | 0.370 | `{'hidden_layer_sizes': (60,), 'alpha': 0.3, 'learning_rate_init': 0.0005}` |
| strict | 2.0 | A2_Biomechanical_NoK | Lasso | 69 | 44 | 0.432 | 0.296 [-0.051, 0.643] | 0.584 | 10.20 | 437.2 [223.4, 651.1] | 0.136 | `{'alpha': 1.0}` |
| strict | 2.0 | A2_Biomechanical_NoK | ElasticNet | 69 | 44 | 0.432 | 0.294 [-0.053, 0.641] | 0.580 | 10.22 | 438.0 [223.4, 652.7] | 0.138 | `{'alpha': 0.1, 'l1_ratio': 0.9}` |
| strict | 2.0 | A2_Biomechanical_NoK | Ridge | 69 | 44 | 0.421 | 0.295 [-0.011, 0.601] | 0.572 | 10.51 | 439.2 [231.5, 646.8] | 0.126 | `{'alpha': 10.0}` |
| strict | 2.0 | B_Clinical | SVM | 69 | 44 | 0.159 | 0.095 [-0.090, 0.280] | 0.611 | 11.69 | 447.4 [295.7, 599.1] | 0.065 | `{'C': 100, 'epsilon': 100, 'gamma': 0.03}` |
| strict | 2.0 | B_Clinical | Random_Forest | 69 | 44 | 0.707 | 0.116 [-0.293, 0.524] | 0.445 | 13.06 | 475.2 [254.3, 696.2] | 0.591 | `{'n_estimators': 300, 'max_depth': None, 'min_samples_split': 2, 'min_samples_leaf': 2}` |
| strict | 2.0 | B_Clinical | XGBoost | 69 | 44 | 0.320 | 0.160 [0.011, 0.308] | 0.455 | 12.05 | 431.6 [290.6, 572.6] | 0.161 | `{'learning_rate': 0.005, 'max_depth': 1, 'n_estimators': 200, 'reg_alpha': 1.0, 'reg_lambda': 0.1}` |
| strict | 2.0 | B_Clinical | Neural_Network | 69 | 44 | 0.376 | 0.163 [-0.010, 0.336] | 0.578 | 11.78 | 421.4 [319.8, 522.9] | 0.213 | `{'hidden_layer_sizes': (60,), 'alpha': 0.5, 'learning_rate_init': 0.0001}` |
| strict | 2.0 | B_Clinical | Lasso | 69 | 44 | 0.393 | 0.295 [0.086, 0.503] | 0.592 | 10.57 | 388.4 [264.9, 512.0] | 0.098 | `{'alpha': 1.0}` |
| strict | 2.0 | B_Clinical | ElasticNet | 69 | 44 | 0.350 | 0.264 [0.101, 0.428] | 0.570 | 10.72 | 399.4 [276.7, 522.2] | 0.086 | `{'alpha': 1.0, 'l1_ratio': 0.7}` |
| strict | 2.0 | B_Clinical | Ridge | 69 | 44 | 0.372 | 0.284 [0.106, 0.462] | 0.577 | 10.63 | 393.0 [271.3, 514.8] | 0.088 | `{'alpha': 10.0}` |
| strict | 2.0 | C1_Combined | SVM | 69 | 44 | 0.344 | 0.357 [0.047, 0.667] | 0.652 | 10.13 | 421.6 [204.7, 638.4] | -0.013 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 2.0 | C1_Combined | Random_Forest | 69 | 44 | 0.686 | 0.412 [0.261, 0.563] | 0.728 | 9.03 | 352.3 [228.1, 476.5] | 0.274 | `{'n_estimators': 50, 'max_depth': 2, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| strict | 2.0 | C1_Combined | XGBoost | 69 | 44 | 0.746 | 0.336 [0.214, 0.458] | 0.698 | 9.85 | 375.5 [260.1, 490.9] | 0.410 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 2.0}` |
| strict | 2.0 | C1_Combined | Neural_Network | 69 | 44 | 0.576 | 0.326 [0.003, 0.649] | 0.651 | 9.27 | 357.9 [263.0, 452.8] | 0.251 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.5, 'learning_rate_init': 0.0005}` |
| strict | 2.0 | C1_Combined | Lasso | 69 | 44 | 0.538 | 0.395 [0.177, 0.613] | 0.662 | 9.12 | 352.8 [226.4, 479.3] | 0.143 | `{'alpha': 0.1}` |
| strict | 2.0 | C1_Combined | ElasticNet | 69 | 44 | 0.538 | 0.395 [0.177, 0.613] | 0.662 | 9.12 | 352.8 [226.5, 479.2] | 0.143 | `{'alpha': 0.001, 'l1_ratio': 0.1}` |
| strict | 2.0 | C1_Combined | Ridge | 69 | 44 | 0.538 | 0.398 [0.178, 0.618] | 0.664 | 9.04 | 351.7 [226.8, 476.6] | 0.140 | `{'alpha': 1.0}` |
| strict | 2.5 | A1_Biomechanical_Core | SVM | 69 | 44 | 0.488 | 0.392 [0.186, 0.598] | 0.736 | 12.22 | 424.8 [390.0, 459.6] | 0.095 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 2.5 | A1_Biomechanical_Core | Random_Forest | 69 | 44 | 0.831 | 0.377 [0.083, 0.671] | 0.649 | 12.98 | 421.7 [221.6, 621.8] | 0.454 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| strict | 2.5 | A1_Biomechanical_Core | XGBoost | 69 | 44 | 0.871 | 0.384 [0.060, 0.708] | 0.652 | 12.81 | 416.5 [208.7, 624.3] | 0.487 | `{'learning_rate': 0.1, 'max_depth': 2, 'n_estimators': 100, 'reg_alpha': 0.1, 'reg_lambda': 2.0}` |
| strict | 2.5 | A1_Biomechanical_Core | Neural_Network | 69 | 44 | 0.646 | 0.362 [0.001, 0.724] | 0.724 | 11.67 | 383.5 [267.0, 499.9] | 0.283 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.5, 'learning_rate_init': 0.0005}` |
| strict | 2.5 | A1_Biomechanical_Core | Lasso | 69 | 44 | 0.561 | 0.430 [0.212, 0.649] | 0.750 | 11.88 | 410.8 [339.0, 482.5] | 0.130 | `{'alpha': 1.0}` |
| strict | 2.5 | A1_Biomechanical_Core | ElasticNet | 69 | 44 | 0.445 | 0.372 [0.203, 0.541] | 0.731 | 13.37 | 434.7 [390.7, 478.8] | 0.073 | `{'alpha': 1.0, 'l1_ratio': 0.1}` |
| strict | 2.5 | A1_Biomechanical_Core | Ridge | 69 | 44 | 0.548 | 0.440 [0.250, 0.630] | 0.745 | 11.77 | 408.0 [365.2, 450.8] | 0.108 | `{'alpha': 10.0}` |
| strict | 2.5 | A2_Biomechanical_NoK | SVM | 69 | 44 | 0.493 | 0.386 [0.188, 0.585] | 0.729 | 12.25 | 427.5 [394.3, 460.7] | 0.106 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 2.5 | A2_Biomechanical_NoK | Random_Forest | 69 | 44 | 0.879 | 0.370 [0.067, 0.674] | 0.669 | 12.49 | 423.8 [220.9, 626.6] | 0.508 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| strict | 2.5 | A2_Biomechanical_NoK | XGBoost | 69 | 44 | 0.779 | 0.347 [0.138, 0.555] | 0.660 | 12.53 | 392.4 [327.7, 457.1] | 0.432 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 2.0}` |
| strict | 2.5 | A2_Biomechanical_NoK | Neural_Network | 69 | 44 | 0.415 | 0.268 [0.033, 0.503] | 0.688 | 14.70 | 467.3 [427.2, 507.5] | 0.147 | `{'hidden_layer_sizes': (80,), 'alpha': 0.1, 'learning_rate_init': 0.001}` |
| strict | 2.5 | A2_Biomechanical_NoK | Lasso | 69 | 44 | 0.562 | 0.423 [0.196, 0.649] | 0.743 | 11.90 | 413.3 [338.0, 488.6] | 0.139 | `{'alpha': 1.0}` |
| strict | 2.5 | A2_Biomechanical_NoK | ElasticNet | 69 | 44 | 0.446 | 0.364 [0.201, 0.526] | 0.724 | 13.44 | 438.0 [395.4, 480.7] | 0.083 | `{'alpha': 1.0, 'l1_ratio': 0.1}` |
| strict | 2.5 | A2_Biomechanical_NoK | Ridge | 69 | 44 | 0.549 | 0.434 [0.240, 0.628] | 0.738 | 11.82 | 410.2 [365.0, 455.3] | 0.115 | `{'alpha': 10.0}` |
| strict | 2.5 | B_Clinical | SVM | 69 | 44 | 0.430 | 0.026 [-0.247, 0.298] | 0.528 | 12.76 | 468.2 [253.0, 683.4] | 0.404 | `{'C': 5000, 'epsilon': 100, 'gamma': 0.05}` |
| strict | 2.5 | B_Clinical | Random_Forest | 69 | 44 | 0.777 | 0.119 [-0.048, 0.286] | 0.512 | 13.81 | 444.0 [285.2, 602.8] | 0.658 | `{'n_estimators': 50, 'max_depth': 5, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| strict | 2.5 | B_Clinical | XGBoost | 69 | 44 | 0.340 | 0.082 [0.033, 0.132] | 0.334 | 14.24 | 464.8 [272.5, 657.2] | 0.258 | `{'learning_rate': 0.005, 'max_depth': 1, 'n_estimators': 200, 'reg_alpha': 1.0, 'reg_lambda': 0.1}` |
| strict | 2.5 | B_Clinical | Neural_Network | 69 | 44 | 0.253 | 0.092 [-0.081, 0.265] | 0.368 | 14.73 | 490.8 [403.6, 578.0] | 0.161 | `{'hidden_layer_sizes': (80,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| strict | 2.5 | B_Clinical | Lasso | 69 | 44 | 0.365 | 0.075 [-0.565, 0.715] | 0.524 | 12.82 | 426.8 [277.7, 575.9] | 0.290 | `{'alpha': 1.0}` |
| strict | 2.5 | B_Clinical | ElasticNet | 69 | 44 | 0.329 | 0.108 [-0.328, 0.545] | 0.504 | 12.59 | 434.4 [270.8, 598.0] | 0.221 | `{'alpha': 1.0, 'l1_ratio': 0.7}` |
| strict | 2.5 | B_Clinical | Ridge | 69 | 44 | 0.348 | 0.108 [-0.395, 0.610] | 0.510 | 12.58 | 429.4 [270.6, 588.1] | 0.240 | `{'alpha': 10.0}` |
| strict | 2.5 | C1_Combined | SVM | 69 | 44 | 0.512 | 0.369 [0.161, 0.577] | 0.731 | 12.73 | 434.5 [363.9, 505.1] | 0.142 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 2.5 | C1_Combined | Random_Forest | 69 | 44 | 0.844 | 0.357 [0.011, 0.703] | 0.632 | 13.51 | 428.0 [211.8, 644.3] | 0.488 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| strict | 2.5 | C1_Combined | XGBoost | 69 | 44 | 0.881 | 0.374 [0.013, 0.736] | 0.637 | 12.96 | 418.8 [200.2, 637.3] | 0.507 | `{'learning_rate': 0.1, 'max_depth': 2, 'n_estimators': 100, 'reg_alpha': 0.1, 'reg_lambda': 2.0}` |
| strict | 2.5 | C1_Combined | Neural_Network | 69 | 44 | 0.564 | 0.357 [0.083, 0.632] | 0.636 | 11.98 | 392.7 [274.6, 510.7] | 0.207 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.5, 'learning_rate_init': 0.0005}` |
| strict | 2.5 | C1_Combined | Lasso | 69 | 44 | 0.578 | 0.427 [0.230, 0.624] | 0.748 | 12.09 | 413.3 [338.0, 488.5] | 0.151 | `{'alpha': 1.0}` |
| strict | 2.5 | C1_Combined | ElasticNet | 69 | 44 | 0.507 | 0.356 [0.104, 0.608] | 0.676 | 12.60 | 404.1 [301.7, 506.5] | 0.151 | `{'alpha': 0.01, 'l1_ratio': 0.1}` |
| strict | 2.5 | C1_Combined | Ridge | 69 | 44 | 0.564 | 0.456 [0.286, 0.627] | 0.748 | 11.90 | 402.9 [362.8, 443.0] | 0.108 | `{'alpha': 10.0}` |
| strict | 3.0 | A1_Biomechanical_Core | SVM | 69 | 44 | 0.438 | 0.374 [0.173, 0.574] | 0.693 | 13.94 | 441.2 [323.9, 558.5] | 0.064 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 3.0 | A1_Biomechanical_Core | Random_Forest | 69 | 44 | 0.819 | 0.333 [0.090, 0.575] | 0.651 | 15.24 | 493.7 [168.9, 818.6] | 0.487 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| strict | 3.0 | A1_Biomechanical_Core | XGBoost | 69 | 44 | 0.908 | 0.376 [0.125, 0.627] | 0.678 | 14.00 | 477.5 [142.0, 813.1] | 0.532 | `{'learning_rate': 0.1, 'max_depth': 2, 'n_estimators': 100, 'reg_alpha': 0.1, 'reg_lambda': 2.0}` |
| strict | 3.0 | A1_Biomechanical_Core | Neural_Network | 69 | 44 | 0.609 | 0.357 [0.201, 0.513] | 0.672 | 13.09 | 452.1 [322.1, 582.1] | 0.253 | `{'hidden_layer_sizes': (80,), 'alpha': 0.1, 'learning_rate_init': 0.001}` |
| strict | 3.0 | A1_Biomechanical_Core | Lasso | 69 | 44 | 0.529 | 0.446 [0.154, 0.738] | 0.738 | 12.00 | 412.0 [238.9, 585.1] | 0.083 | `{'alpha': 1.0}` |
| strict | 3.0 | A1_Biomechanical_Core | ElasticNet | 69 | 44 | 0.421 | 0.360 [0.194, 0.527] | 0.724 | 14.46 | 447.9 [332.8, 563.0] | 0.060 | `{'alpha': 1.0, 'l1_ratio': 0.1}` |
| strict | 3.0 | A1_Biomechanical_Core | Ridge | 69 | 44 | 0.518 | 0.442 [0.199, 0.686] | 0.735 | 12.24 | 414.6 [268.1, 561.1] | 0.075 | `{'alpha': 10.0}` |
| strict | 3.0 | A2_Biomechanical_NoK | SVM | 69 | 44 | 0.439 | 0.370 [0.170, 0.570] | 0.688 | 14.00 | 442.8 [321.8, 563.9] | 0.068 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 3.0 | A2_Biomechanical_NoK | Random_Forest | 69 | 44 | 0.810 | 0.420 [0.180, 0.659] | 0.693 | 13.60 | 494.0 [192.3, 795.7] | 0.390 | `{'n_estimators': 100, 'max_depth': 3, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| strict | 3.0 | A2_Biomechanical_NoK | XGBoost | 69 | 44 | 0.922 | 0.238 [0.041, 0.435] | 0.549 | 15.65 | 521.0 [206.6, 835.5] | 0.684 | `{'learning_rate': 0.1, 'max_depth': 2, 'n_estimators': 100, 'reg_alpha': 0.1, 'reg_lambda': 2.0}` |
| strict | 3.0 | A2_Biomechanical_NoK | Neural_Network | 69 | 44 | 0.475 | 0.215 [-0.104, 0.533] | 0.500 | 15.21 | 464.2 [300.1, 628.4] | 0.260 | `{'hidden_layer_sizes': (60,), 'alpha': 0.3, 'learning_rate_init': 0.0005}` |
| strict | 3.0 | A2_Biomechanical_NoK | Lasso | 69 | 44 | 0.535 | 0.431 [0.123, 0.738] | 0.702 | 12.16 | 416.3 [243.6, 589.1] | 0.104 | `{'alpha': 1.0}` |
| strict | 3.0 | A2_Biomechanical_NoK | ElasticNet | 69 | 44 | 0.425 | 0.351 [0.186, 0.516] | 0.711 | 14.48 | 451.1 [337.9, 564.4] | 0.074 | `{'alpha': 1.0, 'l1_ratio': 0.1}` |
| strict | 3.0 | A2_Biomechanical_NoK | Ridge | 69 | 44 | 0.523 | 0.430 [0.174, 0.687] | 0.706 | 12.30 | 418.0 [272.3, 563.8] | 0.093 | `{'alpha': 10.0}` |
| strict | 3.0 | B_Clinical | SVM | 69 | 44 | 0.131 | 0.131 [-0.253, 0.515] | 0.476 | 15.77 | 529.0 [156.4, 901.6] | 0.000 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 3.0 | B_Clinical | Random_Forest | 69 | 44 | 0.761 | 0.102 [-0.153, 0.357] | 0.414 | 14.02 | 491.2 [201.1, 781.4] | 0.659 | `{'n_estimators': 50, 'max_depth': 5, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| strict | 3.0 | B_Clinical | XGBoost | 69 | 44 | 0.196 | 0.028 [-0.064, 0.120] | 0.231 | 19.09 | 622.7 [356.5, 888.9] | 0.168 | `{'learning_rate': 0.005, 'max_depth': 2, 'n_estimators': 50, 'reg_alpha': 0.5, 'reg_lambda': 0.5}` |
| strict | 3.0 | B_Clinical | Neural_Network | 69 | 44 | 0.351 | 0.076 [-0.169, 0.322] | 0.439 | 16.60 | 542.5 [298.4, 786.6] | 0.275 | `{'hidden_layer_sizes': (40,), 'alpha': 0.5, 'learning_rate_init': 0.001}` |
| strict | 3.0 | B_Clinical | Lasso | 69 | 44 | 0.157 | -0.148 [-0.539, 0.242] | 0.239 | 18.60 | 593.5 [231.7, 955.4] | 0.305 | `{'alpha': 10.0}` |
| strict | 3.0 | B_Clinical | ElasticNet | 69 | 44 | 0.152 | -0.044 [-0.380, 0.292] | 0.277 | 20.50 | 585.4 [355.5, 815.4] | 0.196 | `{'alpha': 1.0, 'l1_ratio': 0.1}` |
| strict | 3.0 | B_Clinical | Ridge | 69 | 44 | 0.075 | -0.044 [-0.260, 0.173] | 0.210 | 17.47 | 572.1 [423.9, 720.3] | 0.119 | `{'alpha': 100.0}` |
| strict | 3.0 | C1_Combined | SVM | 69 | 44 | 0.470 | 0.389 [0.154, 0.625] | 0.730 | 13.75 | 437.6 [283.8, 591.4] | 0.081 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 3.0 | C1_Combined | Random_Forest | 69 | 44 | 0.680 | 0.276 [-0.254, 0.805] | 0.536 | 13.80 | 451.5 [293.7, 609.3] | 0.405 | `{'n_estimators': 100, 'max_depth': 5, 'min_samples_split': 10, 'min_samples_leaf': 4}` |
| strict | 3.0 | C1_Combined | XGBoost | 69 | 44 | 0.597 | 0.275 [-0.064, 0.615] | 0.583 | 13.66 | 462.0 [188.7, 735.4] | 0.322 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 1.0}` |
| strict | 3.0 | C1_Combined | Neural_Network | 69 | 44 | 0.597 | 0.418 [0.058, 0.777] | 0.685 | 12.36 | 398.8 [231.0, 566.7] | 0.180 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.5, 'learning_rate_init': 0.0005}` |
| strict | 3.0 | C1_Combined | Lasso | 69 | 44 | 0.555 | 0.456 [0.220, 0.692] | 0.744 | 12.01 | 411.4 [257.5, 565.2] | 0.099 | `{'alpha': 1.0}` |
| strict | 3.0 | C1_Combined | ElasticNet | 69 | 44 | 0.443 | 0.370 [0.166, 0.573] | 0.746 | 14.70 | 445.9 [301.1, 590.7] | 0.073 | `{'alpha': 1.0, 'l1_ratio': 0.1}` |
| strict | 3.0 | C1_Combined | Ridge | 69 | 44 | 0.542 | 0.469 [0.249, 0.689] | 0.751 | 12.07 | 406.2 [266.0, 546.5] | 0.073 | `{'alpha': 10.0}` |
| strict | 3.5 | A1_Biomechanical_Core | SVM | 69 | 44 | 0.414 | 0.365 [0.148, 0.582] | 0.658 | 13.56 | 431.1 [301.7, 560.6] | 0.049 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 3.5 | A1_Biomechanical_Core | Random_Forest | 69 | 44 | 0.779 | 0.271 [0.087, 0.455] | 0.586 | 16.05 | 548.1 [385.4, 710.8] | 0.508 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| strict | 3.5 | A1_Biomechanical_Core | XGBoost | 69 | 44 | 0.525 | 0.134 [-0.210, 0.478] | 0.431 | 17.67 | 523.2 [296.7, 749.6] | 0.391 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 1.0}` |
| strict | 3.5 | A1_Biomechanical_Core | Neural_Network | 69 | 44 | 0.515 | 0.286 [0.072, 0.501] | 0.549 | 14.57 | 457.7 [332.2, 583.2] | 0.229 | `{'hidden_layer_sizes': (80,), 'alpha': 0.1, 'learning_rate_init': 0.001}` |
| strict | 3.5 | A1_Biomechanical_Core | Lasso | 69 | 44 | 0.478 | 0.391 [0.085, 0.696] | 0.663 | 12.57 | 416.8 [245.1, 588.6] | 0.088 | `{'alpha': 1.0}` |
| strict | 3.5 | A1_Biomechanical_Core | ElasticNet | 69 | 44 | 0.384 | 0.325 [0.162, 0.488] | 0.649 | 15.04 | 447.0 [328.5, 565.6] | 0.059 | `{'alpha': 1.0, 'l1_ratio': 0.1}` |
| strict | 3.5 | A1_Biomechanical_Core | Ridge | 69 | 44 | 0.469 | 0.392 [0.136, 0.648] | 0.659 | 12.64 | 419.3 [271.9, 566.8] | 0.077 | `{'alpha': 10.0}` |
| strict | 3.5 | A2_Biomechanical_NoK | SVM | 69 | 44 | 0.416 | 0.342 [0.121, 0.563] | 0.620 | 13.77 | 439.6 [310.3, 568.9] | 0.074 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 3.5 | A2_Biomechanical_NoK | Random_Forest | 69 | 44 | 0.775 | 0.294 [0.069, 0.519] | 0.553 | 15.87 | 519.9 [282.4, 757.3] | 0.482 | `{'n_estimators': 100, 'max_depth': 3, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| strict | 3.5 | A2_Biomechanical_NoK | XGBoost | 69 | 44 | 0.229 | 0.087 [0.003, 0.171] | 0.555 | 18.65 | 519.2 [352.3, 686.0] | 0.142 | `{'learning_rate': 0.001, 'max_depth': 4, 'n_estimators': 200, 'reg_alpha': 2.0, 'reg_lambda': 1.0}` |
| strict | 3.5 | A2_Biomechanical_NoK | Neural_Network | 69 | 44 | 0.497 | 0.211 [-0.125, 0.546] | 0.451 | 17.17 | 553.3 [286.2, 820.5] | 0.286 | `{'hidden_layer_sizes': (100,), 'alpha': 0.3, 'learning_rate_init': 0.0005}` |
| strict | 3.5 | A2_Biomechanical_NoK | Lasso | 69 | 44 | 0.483 | 0.369 [0.064, 0.674] | 0.639 | 12.76 | 426.2 [254.8, 597.6] | 0.114 | `{'alpha': 1.0}` |
| strict | 3.5 | A2_Biomechanical_NoK | ElasticNet | 69 | 44 | 0.388 | 0.309 [0.156, 0.461] | 0.632 | 15.15 | 453.8 [331.1, 576.5] | 0.079 | `{'alpha': 1.0, 'l1_ratio': 0.1}` |
| strict | 3.5 | A2_Biomechanical_NoK | Ridge | 69 | 44 | 0.473 | 0.372 [0.121, 0.623] | 0.638 | 12.80 | 428.1 [280.1, 576.2] | 0.101 | `{'alpha': 10.0}` |
| strict | 3.5 | B_Clinical | SVM | 69 | 44 | 0.126 | 0.056 [-0.330, 0.443] | 0.445 | 18.18 | 549.5 [245.5, 853.5] | 0.069 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 3.5 | B_Clinical | Random_Forest | 69 | 44 | 0.642 | 0.105 [-0.595, 0.804] | 0.472 | 17.39 | 477.0 [198.7, 755.3] | 0.537 | `{'n_estimators': 100, 'max_depth': 2, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| strict | 3.5 | B_Clinical | XGBoost | 69 | 44 | 0.203 | 0.011 [-0.111, 0.134] | 0.174 | 19.21 | 535.2 [383.0, 687.5] | 0.191 | `{'learning_rate': 0.001, 'max_depth': 4, 'n_estimators': 200, 'reg_alpha': 2.0, 'reg_lambda': 1.0}` |
| strict | 3.5 | B_Clinical | Neural_Network | 69 | 44 | 0.473 | 0.061 [-0.475, 0.597] | 0.415 | 16.43 | 534.7 [263.5, 805.9] | 0.412 | `{'hidden_layer_sizes': (80,), 'alpha': 0.1, 'learning_rate_init': 0.001}` |
| strict | 3.5 | B_Clinical | Lasso | 69 | 44 | 0.333 | -0.059 [-0.813, 0.695] | 0.433 | 16.53 | 522.3 [278.1, 766.5] | 0.393 | `{'alpha': 0.01}` |
| strict | 3.5 | B_Clinical | ElasticNet | 69 | 44 | 0.157 | -0.012 [-0.288, 0.263] | 0.294 | 20.23 | 557.4 [350.9, 764.0] | 0.170 | `{'alpha': 1.0, 'l1_ratio': 0.1}` |
| strict | 3.5 | B_Clinical | Ridge | 69 | 44 | 0.070 | -0.055 [-0.185, 0.076] | 0.220 | 18.06 | 544.2 [414.9, 673.5] | 0.125 | `{'alpha': 100.0}` |
| strict | 3.5 | C1_Combined | SVM | 69 | 44 | 0.431 | 0.355 [0.120, 0.590] | 0.667 | 13.37 | 434.7 [294.2, 575.2] | 0.077 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 3.5 | C1_Combined | Random_Forest | 69 | 44 | 0.612 | 0.193 [-0.047, 0.433] | 0.464 | 15.27 | 490.2 [300.9, 679.5] | 0.419 | `{'n_estimators': 200, 'max_depth': 4, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| strict | 3.5 | C1_Combined | XGBoost | 69 | 44 | 0.223 | 0.107 [0.021, 0.193] | 0.620 | 18.48 | 511.8 [354.3, 669.4] | 0.117 | `{'learning_rate': 0.001, 'max_depth': 4, 'n_estimators': 200, 'reg_alpha': 2.0, 'reg_lambda': 1.0}` |
| strict | 3.5 | C1_Combined | Neural_Network | 69 | 44 | 0.645 | 0.389 [0.059, 0.719] | 0.666 | 13.82 | 386.0 [211.3, 560.8] | 0.256 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.5, 'learning_rate_init': 0.0005}` |
| strict | 3.5 | C1_Combined | Lasso | 69 | 44 | 0.499 | 0.407 [0.095, 0.719] | 0.666 | 12.62 | 408.4 [237.4, 579.4] | 0.092 | `{'alpha': 1.0}` |
| strict | 3.5 | C1_Combined | ElasticNet | 69 | 44 | 0.403 | 0.337 [0.142, 0.532] | 0.668 | 14.86 | 443.4 [307.6, 579.2] | 0.066 | `{'alpha': 1.0, 'l1_ratio': 0.1}` |
| strict | 3.5 | C1_Combined | Ridge | 69 | 44 | 0.488 | 0.426 [0.161, 0.690] | 0.671 | 12.02 | 404.2 [258.6, 549.9] | 0.062 | `{'alpha': 10.0}` |
| strict | 4.0 | A1_Biomechanical_Core | SVM | 69 | 44 | 0.395 | 0.339 [0.078, 0.600] | 0.669 | 16.11 | 503.5 [337.8, 669.2] | 0.056 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 4.0 | A1_Biomechanical_Core | Random_Forest | 69 | 44 | 0.568 | 0.267 [0.086, 0.449] | 0.566 | 16.55 | 497.6 [270.2, 724.9] | 0.300 | `{'n_estimators': 200, 'max_depth': 4, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| strict | 4.0 | A1_Biomechanical_Core | XGBoost | 69 | 44 | 0.889 | 0.129 [-0.001, 0.259] | 0.515 | 21.05 | 602.8 [360.7, 844.9] | 0.760 | `{'learning_rate': 0.1, 'max_depth': 2, 'n_estimators': 100, 'reg_alpha': 0.1, 'reg_lambda': 2.0}` |
| strict | 4.0 | A1_Biomechanical_Core | Neural_Network | 69 | 44 | 0.526 | 0.278 [0.104, 0.451] | 0.589 | 17.80 | 527.4 [383.2, 671.7] | 0.248 | `{'hidden_layer_sizes': (80,), 'alpha': 0.1, 'learning_rate_init': 0.001}` |
| strict | 4.0 | A1_Biomechanical_Core | Lasso | 69 | 44 | 0.480 | 0.314 [0.068, 0.560] | 0.673 | 15.98 | 503.4 [367.8, 639.1] | 0.166 | `{'alpha': 1.0}` |
| strict | 4.0 | A1_Biomechanical_Core | ElasticNet | 69 | 44 | 0.386 | 0.297 [0.160, 0.435] | 0.652 | 18.30 | 521.1 [379.7, 662.6] | 0.089 | `{'alpha': 1.0, 'l1_ratio': 0.1}` |
| strict | 4.0 | A1_Biomechanical_Core | Ridge | 69 | 44 | 0.470 | 0.336 [0.139, 0.534] | 0.666 | 16.12 | 500.0 [371.3, 628.8] | 0.134 | `{'alpha': 10.0}` |
| strict | 4.0 | A2_Biomechanical_NoK | SVM | 69 | 44 | 0.393 | 0.323 [0.067, 0.579] | 0.631 | 16.58 | 511.8 [337.2, 686.5] | 0.070 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 4.0 | A2_Biomechanical_NoK | Random_Forest | 69 | 44 | 0.612 | 0.265 [0.124, 0.407] | 0.580 | 16.25 | 491.3 [283.9, 698.6] | 0.347 | `{'n_estimators': 200, 'max_depth': 4, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| strict | 4.0 | A2_Biomechanical_NoK | XGBoost | 69 | 44 | 0.219 | 0.089 [0.034, 0.145] | 0.442 | 20.44 | 547.0 [325.7, 768.2] | 0.130 | `{'learning_rate': 0.001, 'max_depth': 4, 'n_estimators': 200, 'reg_alpha': 2.0, 'reg_lambda': 1.0}` |
| strict | 4.0 | A2_Biomechanical_NoK | Neural_Network | 69 | 44 | 0.540 | 0.226 [-0.118, 0.571] | 0.506 | 18.49 | 563.7 [288.8, 838.7] | 0.314 | `{'hidden_layer_sizes': (100,), 'alpha': 0.3, 'learning_rate_init': 0.0005}` |
| strict | 4.0 | A2_Biomechanical_NoK | Lasso | 69 | 44 | 0.485 | 0.296 [0.036, 0.556] | 0.671 | 16.32 | 511.9 [365.3, 658.6] | 0.189 | `{'alpha': 1.0}` |
| strict | 4.0 | A2_Biomechanical_NoK | ElasticNet | 69 | 44 | 0.441 | 0.275 [0.095, 0.455] | 0.670 | 18.36 | 510.5 [321.7, 699.2] | 0.166 | `{'alpha': 1.0, 'l1_ratio': 0.1}` |
| strict | 4.0 | A2_Biomechanical_NoK | Ridge | 69 | 44 | 0.475 | 0.316 [0.129, 0.504] | 0.660 | 16.58 | 509.8 [374.1, 645.5] | 0.159 | `{'alpha': 10.0}` |
| strict | 4.0 | B_Clinical | SVM | 69 | 44 | 0.232 | 0.026 [-0.119, 0.170] | 0.302 | 18.50 | 603.6 [442.6, 764.7] | 0.206 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.03}` |
| strict | 4.0 | B_Clinical | Random_Forest | 69 | 44 | 0.625 | 0.292 [-0.160, 0.744] | 0.626 | 19.27 | 508.0 [219.9, 796.2] | 0.333 | `{'n_estimators': 100, 'max_depth': 2, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| strict | 4.0 | B_Clinical | XGBoost | 69 | 44 | 0.180 | 0.025 [-0.120, 0.169] | 0.173 | 20.56 | 564.7 [343.7, 785.7] | 0.156 | `{'learning_rate': 0.001, 'max_depth': 4, 'n_estimators': 200, 'reg_alpha': 2.0, 'reg_lambda': 1.0}` |
| strict | 4.0 | B_Clinical | Neural_Network | 69 | 44 | 0.156 | 0.045 [-0.061, 0.151] | 0.319 | 21.19 | 592.4 [479.9, 704.9] | 0.111 | `{'hidden_layer_sizes': (80,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| strict | 4.0 | B_Clinical | Lasso | 69 | 44 | 0.326 | -0.001 [-0.390, 0.389] | 0.474 | 21.51 | 607.5 [340.0, 875.1] | 0.327 | `{'alpha': 0.01}` |
| strict | 4.0 | B_Clinical | ElasticNet | 69 | 44 | 0.326 | 0.000 [-0.389, 0.389] | 0.474 | 21.50 | 607.4 [339.7, 875.0] | 0.326 | `{'alpha': 0.01, 'l1_ratio': 0.9}` |
| strict | 4.0 | B_Clinical | Ridge | 69 | 44 | 0.326 | 0.001 [-0.388, 0.389] | 0.474 | 21.50 | 607.2 [339.5, 875.0] | 0.325 | `{'alpha': 0.1}` |
| strict | 4.0 | C1_Combined | SVM | 69 | 44 | 0.412 | 0.334 [0.092, 0.575] | 0.700 | 16.33 | 507.8 [338.0, 677.6] | 0.078 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 4.0 | C1_Combined | Random_Forest | 69 | 44 | 0.593 | 0.273 [0.089, 0.456] | 0.537 | 16.94 | 494.6 [269.1, 720.0] | 0.320 | `{'n_estimators': 200, 'max_depth': 4, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| strict | 4.0 | C1_Combined | XGBoost | 69 | 44 | 0.214 | 0.100 [-0.001, 0.200] | 0.461 | 20.28 | 546.7 [316.9, 776.4] | 0.114 | `{'learning_rate': 0.001, 'max_depth': 4, 'n_estimators': 200, 'reg_alpha': 2.0, 'reg_lambda': 1.0}` |
| strict | 4.0 | C1_Combined | Neural_Network | 69 | 44 | 0.481 | 0.279 [0.080, 0.478] | 0.620 | 16.76 | 515.3 [420.4, 610.2] | 0.202 | `{'hidden_layer_sizes': (80,), 'alpha': 0.1, 'learning_rate_init': 0.001}` |
| strict | 4.0 | C1_Combined | Lasso | 69 | 44 | 0.516 | 0.321 [0.053, 0.590] | 0.689 | 17.27 | 494.9 [361.9, 627.8] | 0.194 | `{'alpha': 1.0}` |
| strict | 4.0 | C1_Combined | ElasticNet | 69 | 44 | 0.416 | 0.329 [0.187, 0.471] | 0.693 | 17.66 | 508.4 [372.4, 644.4] | 0.087 | `{'alpha': 1.0, 'l1_ratio': 0.1}` |
| strict | 4.0 | C1_Combined | Ridge | 69 | 44 | 0.504 | 0.399 [0.191, 0.607] | 0.697 | 15.92 | 470.3 [361.0, 579.6] | 0.105 | `{'alpha': 10.0}` |
| strict | 4.5 | A1_Biomechanical_Core | SVM | 69 | 44 | 0.419 | 0.341 [0.111, 0.571] | 0.655 | 17.63 | 503.5 [390.0, 616.9] | 0.078 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 4.5 | A1_Biomechanical_Core | Random_Forest | 69 | 44 | 0.762 | 0.320 [-0.073, 0.713] | 0.582 | 19.51 | 552.4 [352.7, 752.0] | 0.442 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| strict | 4.5 | A1_Biomechanical_Core | XGBoost | 69 | 44 | 0.569 | 0.234 [0.054, 0.414] | 0.523 | 19.99 | 530.5 [438.7, 622.2] | 0.335 | `{'learning_rate': 0.05, 'max_depth': 2, 'n_estimators': 50, 'reg_alpha': 0.5, 'reg_lambda': 2.0}` |
| strict | 4.5 | A1_Biomechanical_Core | Neural_Network | 69 | 44 | 0.641 | 0.239 [-0.057, 0.536] | 0.639 | 18.91 | 505.8 [387.2, 624.3] | 0.402 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.5, 'learning_rate_init': 0.0005}` |
| strict | 4.5 | A1_Biomechanical_Core | Lasso | 69 | 44 | 0.488 | 0.363 [0.095, 0.632] | 0.670 | 16.19 | 489.7 [354.6, 624.8] | 0.125 | `{'alpha': 1.0}` |
| strict | 4.5 | A1_Biomechanical_Core | ElasticNet | 69 | 44 | 0.385 | 0.290 [0.108, 0.472] | 0.645 | 19.11 | 525.0 [423.9, 626.0] | 0.095 | `{'alpha': 1.0, 'l1_ratio': 0.1}` |
| strict | 4.5 | A1_Biomechanical_Core | Ridge | 69 | 44 | 0.477 | 0.365 [0.121, 0.609] | 0.663 | 16.81 | 491.3 [374.5, 608.0] | 0.111 | `{'alpha': 10.0}` |
| strict | 4.5 | A2_Biomechanical_NoK | SVM | 69 | 44 | 0.421 | 0.305 [0.112, 0.499] | 0.620 | 17.74 | 521.5 [402.0, 641.1] | 0.116 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 4.5 | A2_Biomechanical_NoK | Random_Forest | 69 | 44 | 0.801 | 0.308 [-0.053, 0.669] | 0.605 | 20.43 | 560.4 [378.7, 742.0] | 0.493 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| strict | 4.5 | A2_Biomechanical_NoK | XGBoost | 69 | 44 | 0.998 | 0.178 [-0.252, 0.608] | 0.656 | 21.55 | 556.3 [404.0, 708.5] | 0.819 | `{'learning_rate': 0.1, 'max_depth': 4, 'n_estimators': 100, 'reg_alpha': 1.0, 'reg_lambda': 0.5}` |
| strict | 4.5 | A2_Biomechanical_NoK | Neural_Network | 69 | 44 | 0.499 | 0.274 [-0.066, 0.613] | 0.543 | 18.37 | 523.1 [296.3, 749.9] | 0.225 | `{'hidden_layer_sizes': (100,), 'alpha': 0.3, 'learning_rate_init': 0.0005}` |
| strict | 4.5 | A2_Biomechanical_NoK | Lasso | 69 | 44 | 0.491 | 0.335 [0.105, 0.565] | 0.652 | 16.53 | 506.3 [377.4, 635.2] | 0.156 | `{'alpha': 1.0}` |
| strict | 4.5 | A2_Biomechanical_NoK | ElasticNet | 69 | 44 | 0.412 | 0.292 [-0.002, 0.586] | 0.605 | 20.85 | 575.6 [464.4, 686.8] | 0.120 | `{'alpha': 0.001, 'l1_ratio': 0.3}` |
| strict | 4.5 | A2_Biomechanical_NoK | Ridge | 69 | 44 | 0.480 | 0.337 [0.133, 0.540] | 0.640 | 17.12 | 507.4 [393.2, 621.6] | 0.144 | `{'alpha': 10.0}` |
| strict | 4.5 | B_Clinical | SVM | 69 | 44 | 0.307 | 0.107 [-0.109, 0.323] | 0.435 | 19.94 | 569.7 [497.3, 642.2] | 0.200 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.03}` |
| strict | 4.5 | B_Clinical | Random_Forest | 69 | 44 | 0.640 | 0.209 [-0.426, 0.845] | 0.560 | 20.10 | 511.6 [268.2, 755.0] | 0.431 | `{'n_estimators': 100, 'max_depth': 2, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| strict | 4.5 | B_Clinical | XGBoost | 69 | 44 | 0.195 | 0.080 [-0.040, 0.200] | 0.383 | 26.22 | 665.3 [601.1, 729.6] | 0.115 | `{'learning_rate': 0.01, 'max_depth': 2, 'n_estimators': 30, 'reg_alpha': 0.5, 'reg_lambda': 2.0}` |
| strict | 4.5 | B_Clinical | Neural_Network | 69 | 44 | 0.172 | 0.052 [-0.265, 0.370] | 0.336 | 22.02 | 582.0 [516.4, 647.5] | 0.119 | `{'hidden_layer_sizes': (80,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| strict | 4.5 | B_Clinical | Lasso | 69 | 44 | 0.353 | 0.068 [-0.363, 0.500] | 0.559 | 22.65 | 639.5 [438.7, 840.3] | 0.284 | `{'alpha': 1.0}` |
| strict | 4.5 | B_Clinical | ElasticNet | 69 | 44 | 0.351 | 0.077 [-0.310, 0.464] | 0.560 | 23.05 | 639.6 [451.7, 827.4] | 0.274 | `{'alpha': 0.1, 'l1_ratio': 0.3}` |
| strict | 4.5 | B_Clinical | Ridge | 69 | 44 | 0.342 | 0.079 [-0.239, 0.397] | 0.559 | 23.70 | 642.4 [472.3, 812.5] | 0.263 | `{'alpha': 10.0}` |
| strict | 4.5 | C1_Combined | SVM | 69 | 44 | 0.455 | 0.351 [0.136, 0.565] | 0.693 | 18.01 | 502.2 [368.4, 636.1] | 0.105 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 4.5 | C1_Combined | Random_Forest | 69 | 44 | 0.758 | 0.250 [-0.113, 0.614] | 0.546 | 20.68 | 587.2 [419.6, 754.7] | 0.507 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| strict | 4.5 | C1_Combined | XGBoost | 69 | 44 | 0.570 | 0.200 [0.013, 0.388] | 0.485 | 20.31 | 542.3 [445.6, 639.1] | 0.370 | `{'learning_rate': 0.05, 'max_depth': 2, 'n_estimators': 50, 'reg_alpha': 0.5, 'reg_lambda': 2.0}` |
| strict | 4.5 | C1_Combined | Neural_Network | 69 | 44 | 0.444 | 0.269 [0.063, 0.476] | 0.572 | 18.26 | 527.5 [443.8, 611.2] | 0.175 | `{'hidden_layer_sizes': (80,), 'alpha': 0.1, 'learning_rate_init': 0.001}` |
| strict | 4.5 | C1_Combined | Lasso | 69 | 44 | 0.525 | 0.396 [0.133, 0.660] | 0.686 | 16.90 | 471.7 [361.9, 581.5] | 0.129 | `{'alpha': 1.0}` |
| strict | 4.5 | C1_Combined | ElasticNet | 69 | 44 | 0.416 | 0.314 [0.139, 0.490] | 0.691 | 18.90 | 516.9 [405.7, 628.1] | 0.102 | `{'alpha': 1.0, 'l1_ratio': 0.1}` |
| strict | 4.5 | C1_Combined | Ridge | 69 | 44 | 0.512 | 0.414 [0.164, 0.663] | 0.697 | 17.05 | 467.5 [359.0, 576.0] | 0.099 | `{'alpha': 10.0}` |
| strict | 5.0 | A1_Biomechanical_Core | SVM | 69 | 44 | 0.340 | 0.223 [0.090, 0.356] | 0.694 | 20.02 | 620.6 [433.7, 807.5] | 0.117 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 5.0 | A1_Biomechanical_Core | Random_Forest | 69 | 44 | 0.881 | 0.309 [0.119, 0.500] | 0.626 | 19.28 | 563.8 [392.0, 735.5] | 0.572 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| strict | 5.0 | A1_Biomechanical_Core | XGBoost | 69 | 44 | 0.902 | 0.157 [-0.053, 0.367] | 0.567 | 21.03 | 615.4 [458.2, 772.5] | 0.745 | `{'learning_rate': 0.1, 'max_depth': 2, 'n_estimators': 100, 'reg_alpha': 0.1, 'reg_lambda': 2.0}` |
| strict | 5.0 | A1_Biomechanical_Core | Neural_Network | 69 | 44 | 0.504 | 0.279 [0.035, 0.524] | 0.705 | 24.95 | 646.3 [486.1, 806.4] | 0.224 | `{'hidden_layer_sizes': (60,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| strict | 5.0 | A1_Biomechanical_Core | Lasso | 69 | 44 | 0.499 | 0.317 [0.073, 0.561] | 0.695 | 22.38 | 617.1 [487.2, 747.1] | 0.182 | `{'alpha': 1.0}` |
| strict | 5.0 | A1_Biomechanical_Core | ElasticNet | 69 | 44 | 0.497 | 0.337 [0.127, 0.547] | 0.691 | 22.38 | 613.2 [477.4, 749.1] | 0.160 | `{'alpha': 0.1, 'l1_ratio': 0.3}` |
| strict | 5.0 | A1_Biomechanical_Core | Ridge | 69 | 44 | 0.486 | 0.347 [0.164, 0.531] | 0.683 | 22.74 | 614.2 [467.3, 761.0] | 0.138 | `{'alpha': 10.0}` |
| strict | 5.0 | A2_Biomechanical_NoK | SVM | 69 | 44 | 0.310 | 0.220 [-0.077, 0.517] | 0.620 | 28.20 | 658.6 [491.1, 826.1] | 0.090 | `{'C': 5000, 'epsilon': 800, 'gamma': 0.01}` |
| strict | 5.0 | A2_Biomechanical_NoK | Random_Forest | 69 | 44 | 0.701 | 0.227 [-0.075, 0.530] | 0.635 | 23.75 | 674.8 [458.1, 891.4] | 0.473 | `{'n_estimators': 100, 'max_depth': 2, 'min_samples_split': 5, 'min_samples_leaf': 2}` |
| strict | 5.0 | A2_Biomechanical_NoK | XGBoost | 69 | 44 | 0.517 | 0.109 [-0.098, 0.315] | 0.662 | 22.61 | 628.1 [344.8, 911.4] | 0.409 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 30, 'reg_alpha': 2.0, 'reg_lambda': 0.5}` |
| strict | 5.0 | A2_Biomechanical_NoK | Neural_Network | 69 | 44 | 0.397 | 0.148 [-0.212, 0.509] | 0.549 | 22.43 | 562.5 [494.5, 630.5] | 0.249 | `{'hidden_layer_sizes': (40,), 'alpha': 1.0, 'learning_rate_init': 0.0005}` |
| strict | 5.0 | A2_Biomechanical_NoK | Lasso | 69 | 44 | 0.546 | 0.340 [0.158, 0.522] | 0.693 | 22.06 | 610.3 [527.1, 693.5] | 0.206 | `{'alpha': 1.0}` |
| strict | 5.0 | A2_Biomechanical_NoK | ElasticNet | 69 | 44 | 0.543 | 0.343 [0.207, 0.479] | 0.692 | 22.21 | 616.4 [498.6, 734.1] | 0.201 | `{'alpha': 0.1, 'l1_ratio': 0.3}` |
| strict | 5.0 | A2_Biomechanical_NoK | Ridge | 69 | 44 | 0.531 | 0.329 [0.207, 0.450] | 0.677 | 22.69 | 630.4 [467.2, 793.6] | 0.202 | `{'alpha': 10.0}` |
| strict | 5.0 | B_Clinical | SVM | 69 | 44 | 0.415 | 0.121 [-0.196, 0.438] | 0.469 | 21.73 | 599.5 [427.1, 772.0] | 0.294 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.03}` |
| strict | 5.0 | B_Clinical | Random_Forest | 69 | 44 | 0.682 | 0.200 [-0.172, 0.571] | 0.637 | 24.05 | 678.4 [481.9, 874.9] | 0.482 | `{'n_estimators': 100, 'max_depth': 2, 'min_samples_split': 5, 'min_samples_leaf': 2}` |
| strict | 5.0 | B_Clinical | XGBoost | 69 | 44 | 0.596 | 0.145 [-0.457, 0.746] | 0.482 | 20.38 | 552.9 [359.7, 746.0] | 0.452 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 1.0}` |
| strict | 5.0 | B_Clinical | Neural_Network | 69 | 44 | 0.484 | 0.132 [-0.068, 0.332] | 0.686 | 27.33 | 703.9 [600.0, 807.7] | 0.352 | `{'hidden_layer_sizes': (60,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| strict | 5.0 | B_Clinical | Lasso | 69 | 44 | 0.449 | 0.199 [-0.074, 0.472] | 0.648 | 23.05 | 668.8 [541.6, 796.1] | 0.250 | `{'alpha': 1.0}` |
| strict | 5.0 | B_Clinical | ElasticNet | 69 | 44 | 0.447 | 0.212 [-0.010, 0.434] | 0.647 | 23.26 | 668.6 [545.4, 791.9] | 0.235 | `{'alpha': 0.1, 'l1_ratio': 0.3}` |
| strict | 5.0 | B_Clinical | Ridge | 69 | 44 | 0.437 | 0.222 [0.059, 0.384] | 0.644 | 24.09 | 670.7 [542.6, 798.8] | 0.216 | `{'alpha': 10.0}` |
| strict | 5.0 | C1_Combined | SVM | 69 | 44 | 0.399 | 0.292 [0.177, 0.407] | 0.732 | 18.95 | 588.4 [426.7, 750.1] | 0.107 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 5.0 | C1_Combined | Random_Forest | 69 | 44 | 0.902 | 0.299 [0.067, 0.531] | 0.594 | 21.61 | 579.6 [311.9, 847.3] | 0.603 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| strict | 5.0 | C1_Combined | XGBoost | 69 | 44 | 0.659 | 0.159 [-0.395, 0.712] | 0.602 | 19.44 | 549.1 [362.4, 735.8] | 0.501 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 1.0}` |
| strict | 5.0 | C1_Combined | Neural_Network | 69 | 44 | 0.690 | 0.331 [-0.056, 0.718] | 0.728 | 19.70 | 513.4 [401.8, 624.9] | 0.359 | `{'hidden_layer_sizes': (100,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| strict | 5.0 | C1_Combined | Lasso | 69 | 44 | 0.504 | 0.307 [0.053, 0.562] | 0.702 | 21.87 | 620.7 [488.6, 752.8] | 0.196 | `{'alpha': 1.0}` |
| strict | 5.0 | C1_Combined | ElasticNet | 69 | 44 | 0.501 | 0.315 [0.075, 0.554] | 0.696 | 21.79 | 619.1 [484.2, 754.0] | 0.187 | `{'alpha': 0.1, 'l1_ratio': 0.3}` |
| strict | 5.0 | C1_Combined | Ridge | 69 | 44 | 0.496 | 0.322 [0.111, 0.533] | 0.692 | 22.16 | 619.6 [483.6, 755.5] | 0.174 | `{'alpha': 10.0}` |
| strict | 5.5 | A1_Biomechanical_Core | SVM | 69 | 44 | 0.339 | 0.252 [0.084, 0.420] | 0.614 | 22.32 | 685.3 [498.2, 872.5] | 0.087 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 5.5 | A1_Biomechanical_Core | Random_Forest | 69 | 44 | 0.911 | 0.267 [0.013, 0.520] | 0.718 | 22.25 | 642.8 [485.8, 799.7] | 0.644 | `{'n_estimators': 100, 'max_depth': 5, 'min_samples_split': 2, 'min_samples_leaf': 1}` |
| strict | 5.5 | A1_Biomechanical_Core | XGBoost | 69 | 44 | 0.507 | 0.275 [0.237, 0.314] | 0.689 | 26.21 | 659.1 [464.8, 853.4] | 0.231 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 30, 'reg_alpha': 2.0, 'reg_lambda': 0.5}` |
| strict | 5.5 | A1_Biomechanical_Core | Neural_Network | 69 | 44 | 0.498 | 0.269 [-0.040, 0.578] | 0.701 | 26.25 | 677.0 [475.6, 878.3] | 0.229 | `{'hidden_layer_sizes': (60,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| strict | 5.5 | A1_Biomechanical_Core | Lasso | 69 | 44 | 0.490 | 0.313 [0.122, 0.504] | 0.709 | 23.76 | 653.4 [535.9, 770.8] | 0.177 | `{'alpha': 1.0}` |
| strict | 5.5 | A1_Biomechanical_Core | ElasticNet | 69 | 44 | 0.488 | 0.331 [0.140, 0.523] | 0.705 | 23.76 | 647.6 [511.0, 784.2] | 0.156 | `{'alpha': 0.1, 'l1_ratio': 0.3}` |
| strict | 5.5 | A1_Biomechanical_Core | Ridge | 69 | 44 | 0.477 | 0.339 [0.135, 0.544] | 0.694 | 24.23 | 646.7 [484.8, 808.6] | 0.137 | `{'alpha': 10.0}` |
| strict | 5.5 | A2_Biomechanical_NoK | SVM | 69 | 44 | 0.368 | 0.250 [0.077, 0.423] | 0.616 | 22.22 | 683.6 [503.1, 864.1] | 0.118 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 5.5 | A2_Biomechanical_NoK | Random_Forest | 69 | 44 | 0.921 | 0.324 [0.181, 0.467] | 0.723 | 22.36 | 629.4 [457.7, 801.0] | 0.597 | `{'n_estimators': 100, 'max_depth': 5, 'min_samples_split': 2, 'min_samples_leaf': 1}` |
| strict | 5.5 | A2_Biomechanical_NoK | XGBoost | 69 | 44 | 0.509 | 0.273 [0.238, 0.309] | 0.687 | 26.20 | 659.9 [466.1, 853.7] | 0.236 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 30, 'reg_alpha': 2.0, 'reg_lambda': 0.5}` |
| strict | 5.5 | A2_Biomechanical_NoK | Neural_Network | 69 | 44 | 0.510 | 0.182 [-0.193, 0.558] | 0.507 | 25.69 | 647.5 [510.1, 784.8] | 0.328 | `{'hidden_layer_sizes': (100,), 'alpha': 0.3, 'learning_rate_init': 0.0005}` |
| strict | 5.5 | A2_Biomechanical_NoK | Lasso | 69 | 44 | 0.516 | 0.342 [0.162, 0.523] | 0.710 | 23.31 | 640.1 [516.6, 763.6] | 0.173 | `{'alpha': 1.0}` |
| strict | 5.5 | A2_Biomechanical_NoK | ElasticNet | 69 | 44 | 0.513 | 0.355 [0.179, 0.532] | 0.711 | 23.41 | 637.2 [493.7, 780.7] | 0.158 | `{'alpha': 0.1, 'l1_ratio': 0.3}` |
| strict | 5.5 | A2_Biomechanical_NoK | Ridge | 69 | 44 | 0.501 | 0.345 [0.168, 0.522] | 0.702 | 24.07 | 647.6 [474.5, 820.7] | 0.156 | `{'alpha': 10.0}` |
| strict | 5.5 | B_Clinical | SVM | 69 | 44 | 0.446 | 0.117 [-0.112, 0.347] | 0.554 | 24.34 | 659.3 [459.7, 858.9] | 0.328 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.03}` |
| strict | 5.5 | B_Clinical | Random_Forest | 69 | 44 | 0.614 | 0.140 [-0.244, 0.524] | 0.488 | 25.94 | 669.8 [400.8, 938.8] | 0.474 | `{'n_estimators': 50, 'max_depth': 2, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| strict | 5.5 | B_Clinical | XGBoost | 69 | 44 | 0.600 | 0.151 [-0.359, 0.660] | 0.458 | 23.56 | 612.0 [521.2, 702.8] | 0.450 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 1.0}` |
| strict | 5.5 | B_Clinical | Neural_Network | 69 | 44 | 0.462 | 0.096 [-0.178, 0.370] | 0.686 | 29.34 | 746.5 [619.7, 873.2] | 0.366 | `{'hidden_layer_sizes': (60,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| strict | 5.5 | B_Clinical | Lasso | 69 | 44 | 0.458 | 0.197 [-0.090, 0.485] | 0.642 | 25.49 | 699.1 [590.6, 807.6] | 0.261 | `{'alpha': 1.0}` |
| strict | 5.5 | B_Clinical | ElasticNet | 69 | 44 | 0.456 | 0.212 [-0.068, 0.491] | 0.643 | 25.20 | 696.7 [569.9, 823.4] | 0.244 | `{'alpha': 0.1, 'l1_ratio': 0.3}` |
| strict | 5.5 | B_Clinical | Ridge | 69 | 44 | 0.445 | 0.221 [-0.053, 0.495] | 0.643 | 25.42 | 697.3 [540.4, 854.3] | 0.224 | `{'alpha': 10.0}` |
| strict | 5.5 | C1_Combined | SVM | 69 | 44 | 0.402 | 0.289 [0.057, 0.520] | 0.623 | 28.22 | 656.9 [487.9, 825.9] | 0.113 | `{'C': 5000, 'epsilon': 800, 'gamma': 0.01}` |
| strict | 5.5 | C1_Combined | Random_Forest | 69 | 44 | 0.915 | 0.259 [0.029, 0.489] | 0.628 | 23.22 | 649.4 [500.1, 798.8] | 0.656 | `{'n_estimators': 100, 'max_depth': 5, 'min_samples_split': 2, 'min_samples_leaf': 1}` |
| strict | 5.5 | C1_Combined | XGBoost | 69 | 44 | 0.656 | 0.237 [-0.062, 0.536] | 0.596 | 22.36 | 570.9 [420.7, 721.2] | 0.419 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 30, 'reg_alpha': 1.0, 'reg_lambda': 0.1}` |
| strict | 5.5 | C1_Combined | Neural_Network | 69 | 44 | 0.545 | 0.283 [0.080, 0.486] | 0.547 | 24.90 | 673.6 [446.2, 901.1] | 0.262 | `{'hidden_layer_sizes': (80,), 'alpha': 0.5, 'learning_rate_init': 0.001}` |
| strict | 5.5 | C1_Combined | Lasso | 69 | 44 | 0.525 | 0.308 [0.051, 0.564] | 0.678 | 23.59 | 621.8 [489.0, 754.5] | 0.217 | `{'alpha': 0.01}` |
| strict | 5.5 | C1_Combined | ElasticNet | 69 | 44 | 0.525 | 0.310 [0.056, 0.564] | 0.670 | 23.51 | 621.3 [488.2, 754.4] | 0.215 | `{'alpha': 0.1, 'l1_ratio': 0.9}` |
| strict | 5.5 | C1_Combined | Ridge | 69 | 44 | 0.495 | 0.315 [0.116, 0.515] | 0.690 | 23.91 | 653.5 [525.3, 781.8] | 0.180 | `{'alpha': 10.0}` |
| strict | 6.0 | A1_Biomechanical_Core | SVM | 69 | 44 | 0.360 | 0.287 [0.062, 0.511] | 0.614 | 29.67 | 723.7 [615.0, 832.4] | 0.073 | `{'C': 5000, 'epsilon': 800, 'gamma': 0.01}` |
| strict | 6.0 | A1_Biomechanical_Core | Random_Forest | 69 | 44 | 0.915 | 0.294 [-0.069, 0.657] | 0.683 | 23.32 | 600.6 [343.7, 857.5] | 0.620 | `{'n_estimators': 100, 'max_depth': 5, 'min_samples_split': 2, 'min_samples_leaf': 1}` |
| strict | 6.0 | A1_Biomechanical_Core | XGBoost | 69 | 44 | 0.997 | 0.229 [-0.280, 0.738] | 0.603 | 25.68 | 652.5 [467.1, 838.0] | 0.768 | `{'learning_rate': 0.1, 'max_depth': 4, 'n_estimators': 100, 'reg_alpha': 1.0, 'reg_lambda': 0.5}` |
| strict | 6.0 | A1_Biomechanical_Core | Neural_Network | 69 | 44 | 0.674 | 0.351 [0.113, 0.589] | 0.675 | 21.89 | 563.5 [337.8, 789.1] | 0.323 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.5, 'learning_rate_init': 0.0005}` |
| strict | 6.0 | A1_Biomechanical_Core | Lasso | 69 | 44 | 0.408 | 0.296 [0.115, 0.478] | 0.629 | 26.16 | 685.5 [591.0, 780.1] | 0.112 | `{'alpha': 1.0}` |
| strict | 6.0 | A1_Biomechanical_Core | ElasticNet | 69 | 44 | 0.407 | 0.304 [0.130, 0.477] | 0.622 | 26.05 | 683.3 [579.6, 787.0] | 0.103 | `{'alpha': 0.1, 'l1_ratio': 0.3}` |
| strict | 6.0 | A1_Biomechanical_Core | Ridge | 69 | 44 | 0.399 | 0.306 [0.140, 0.471] | 0.613 | 26.23 | 684.4 [567.6, 801.2] | 0.093 | `{'alpha': 10.0}` |
| strict | 6.0 | A2_Biomechanical_NoK | SVM | 69 | 44 | 0.389 | 0.312 [0.062, 0.562] | 0.628 | 28.86 | 708.6 [587.9, 829.4] | 0.077 | `{'C': 5000, 'epsilon': 800, 'gamma': 0.01}` |
| strict | 6.0 | A2_Biomechanical_NoK | Random_Forest | 69 | 44 | 0.921 | 0.379 [0.111, 0.646] | 0.758 | 21.89 | 568.7 [345.2, 792.1] | 0.542 | `{'n_estimators': 100, 'max_depth': 5, 'min_samples_split': 2, 'min_samples_leaf': 1}` |
| strict | 6.0 | A2_Biomechanical_NoK | XGBoost | 69 | 44 | 0.999 | 0.142 [-0.664, 0.947] | 0.634 | 25.34 | 655.3 [445.8, 864.8] | 0.857 | `{'learning_rate': 0.1, 'max_depth': 4, 'n_estimators': 100, 'reg_alpha': 1.0, 'reg_lambda': 0.5}` |
| strict | 6.0 | A2_Biomechanical_NoK | Neural_Network | 69 | 44 | 0.443 | 0.262 [0.048, 0.475] | 0.557 | 29.52 | 746.4 [562.0, 930.8] | 0.181 | `{'hidden_layer_sizes': (80,), 'alpha': 0.5, 'learning_rate_init': 0.001}` |
| strict | 6.0 | A2_Biomechanical_NoK | Lasso | 69 | 44 | 0.414 | 0.300 [-0.094, 0.693] | 0.639 | 27.12 | 705.6 [531.9, 879.3] | 0.115 | `{'alpha': 10.0}` |
| strict | 6.0 | A2_Biomechanical_NoK | ElasticNet | 69 | 44 | 0.415 | 0.293 [-0.116, 0.702] | 0.637 | 27.32 | 708.1 [529.7, 886.5] | 0.122 | `{'alpha': 0.001, 'l1_ratio': 0.3}` |
| strict | 6.0 | A2_Biomechanical_NoK | Ridge | 69 | 44 | 0.454 | 0.341 [0.207, 0.475] | 0.634 | 25.41 | 666.9 [569.3, 764.5] | 0.113 | `{'alpha': 10.0}` |
| strict | 6.0 | B_Clinical | SVM | 69 | 44 | 0.239 | 0.161 [-0.029, 0.351] | 0.610 | 32.01 | 754.6 [616.5, 892.8] | 0.078 | `{'C': 500, 'epsilon': 800, 'gamma': 0.03}` |
| strict | 6.0 | B_Clinical | Random_Forest | 69 | 44 | 0.632 | 0.216 [-0.133, 0.565] | 0.555 | 27.04 | 733.4 [459.9, 1006.9] | 0.416 | `{'n_estimators': 100, 'max_depth': 2, 'min_samples_split': 5, 'min_samples_leaf': 2}` |
| strict | 6.0 | B_Clinical | XGBoost | 69 | 44 | 0.206 | 0.033 [-0.139, 0.205] | 0.237 | 34.25 | 857.6 [672.7, 1042.5] | 0.174 | `{'learning_rate': 0.01, 'max_depth': 2, 'n_estimators': 30, 'reg_alpha': 0.5, 'reg_lambda': 2.0}` |
| strict | 6.0 | B_Clinical | Neural_Network | 69 | 44 | 0.426 | 0.185 [-0.044, 0.415] | 0.622 | 28.90 | 740.2 [611.1, 869.3] | 0.241 | `{'hidden_layer_sizes': (60,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| strict | 6.0 | B_Clinical | Lasso | 69 | 44 | 0.355 | 0.199 [-0.035, 0.432] | 0.556 | 26.80 | 730.0 [619.6, 840.3] | 0.156 | `{'alpha': 1.0}` |
| strict | 6.0 | B_Clinical | ElasticNet | 69 | 44 | 0.353 | 0.206 [-0.011, 0.423] | 0.555 | 26.98 | 728.6 [614.3, 842.9] | 0.147 | `{'alpha': 0.1, 'l1_ratio': 0.3}` |
| strict | 6.0 | B_Clinical | Ridge | 69 | 44 | 0.344 | 0.210 [0.020, 0.399] | 0.552 | 27.59 | 730.4 [607.3, 853.4] | 0.135 | `{'alpha': 10.0}` |
| strict | 6.0 | C1_Combined | SVM | 69 | 44 | 0.393 | 0.301 [0.145, 0.456] | 0.604 | 29.47 | 722.3 [608.0, 836.6] | 0.093 | `{'C': 5000, 'epsilon': 800, 'gamma': 0.01}` |
| strict | 6.0 | C1_Combined | Random_Forest | 69 | 44 | 0.711 | 0.260 [-0.366, 0.885] | 0.691 | 24.62 | 632.3 [473.6, 791.1] | 0.452 | `{'n_estimators': 300, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 4}` |
| strict | 6.0 | C1_Combined | XGBoost | 69 | 44 | 0.999 | 0.153 [-0.482, 0.788] | 0.556 | 26.22 | 678.5 [474.3, 882.7] | 0.845 | `{'learning_rate': 0.1, 'max_depth': 4, 'n_estimators': 100, 'reg_alpha': 1.0, 'reg_lambda': 0.5}` |
| strict | 6.0 | C1_Combined | Neural_Network | 69 | 44 | 0.675 | 0.371 [0.162, 0.579] | 0.664 | 21.62 | 553.9 [348.8, 759.0] | 0.304 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.5, 'learning_rate_init': 0.0005}` |
| strict | 6.0 | C1_Combined | Lasso | 69 | 44 | 0.409 | 0.292 [0.111, 0.473] | 0.621 | 25.98 | 687.7 [593.2, 782.2] | 0.118 | `{'alpha': 1.0}` |
| strict | 6.0 | C1_Combined | ElasticNet | 69 | 44 | 0.407 | 0.292 [0.114, 0.470] | 0.613 | 25.85 | 688.4 [587.9, 788.9] | 0.115 | `{'alpha': 0.1, 'l1_ratio': 0.3}` |
| strict | 6.0 | C1_Combined | Ridge | 69 | 44 | 0.401 | 0.293 [0.124, 0.462] | 0.609 | 25.97 | 689.1 [581.3, 796.9] | 0.108 | `{'alpha': 10.0}` |
| lenient | 1.0 | A1_Biomechanical_Core | SVM | 71 | 46 | 0.640 | 0.458 [0.305, 0.610] | 0.742 | 10.83 | 564.8 [351.1, 778.6] | 0.183 | `{'C': 5000, 'epsilon': 100, 'gamma': 0.05}` |
| lenient | 1.0 | A1_Biomechanical_Core | Random_Forest | 71 | 46 | 0.715 | 0.401 [0.090, 0.713] | 0.732 | 12.01 | 540.4 [374.6, 706.2] | 0.314 | `{'n_estimators': 100, 'max_depth': 2, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| lenient | 1.0 | A1_Biomechanical_Core | XGBoost | 71 | 46 | 0.705 | 0.451 [0.303, 0.599] | 0.708 | 10.87 | 503.1 [360.5, 645.7] | 0.255 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 2.0}` |
| lenient | 1.0 | A1_Biomechanical_Core | Neural_Network | 71 | 46 | 0.434 | 0.286 [0.118, 0.453] | 0.648 | 11.92 | 602.8 [346.3, 859.3] | 0.149 | `{'hidden_layer_sizes': (80,), 'alpha': 0.3, 'learning_rate_init': 0.0001}` |
| lenient | 1.0 | A1_Biomechanical_Core | Lasso | 71 | 46 | 0.437 | 0.380 [0.170, 0.590] | 0.638 | 11.15 | 541.8 [330.2, 753.4] | 0.057 | `{'alpha': 1.0}` |
| lenient | 1.0 | A1_Biomechanical_Core | ElasticNet | 71 | 46 | 0.409 | 0.334 [0.010, 0.658] | 0.658 | 11.65 | 568.5 [255.1, 881.9] | 0.075 | `{'alpha': 0.1, 'l1_ratio': 0.3}` |
| lenient | 1.0 | A1_Biomechanical_Core | Ridge | 71 | 46 | 0.425 | 0.348 [0.119, 0.578] | 0.631 | 11.27 | 550.8 [347.1, 754.6] | 0.077 | `{'alpha': 10.0}` |
| lenient | 1.0 | A2_Biomechanical_NoK | SVM | 71 | 46 | 0.677 | 0.385 [0.162, 0.609] | 0.734 | 11.57 | 596.8 [365.2, 828.4] | 0.292 | `{'C': 5000, 'epsilon': 100, 'gamma': 0.05}` |
| lenient | 1.0 | A2_Biomechanical_NoK | Random_Forest | 71 | 46 | 0.723 | 0.410 [0.299, 0.520] | 0.684 | 11.61 | 564.5 [390.2, 738.9] | 0.313 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| lenient | 1.0 | A2_Biomechanical_NoK | XGBoost | 71 | 46 | 0.714 | 0.374 [0.175, 0.573] | 0.651 | 11.39 | 536.3 [375.2, 697.3] | 0.341 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 2.0}` |
| lenient | 1.0 | A2_Biomechanical_NoK | Neural_Network | 71 | 46 | 0.616 | 0.372 [0.190, 0.554] | 0.752 | 11.01 | 528.4 [390.3, 666.5] | 0.244 | `{'hidden_layer_sizes': (80, 40), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| lenient | 1.0 | A2_Biomechanical_NoK | Lasso | 71 | 46 | 0.442 | 0.312 [0.041, 0.583] | 0.598 | 11.38 | 571.5 [333.2, 809.8] | 0.130 | `{'alpha': 1.0}` |
| lenient | 1.0 | A2_Biomechanical_NoK | ElasticNet | 71 | 46 | 0.480 | 0.281 [0.018, 0.544] | 0.585 | 11.18 | 510.3 [327.0, 693.7] | 0.199 | `{'alpha': 0.001, 'l1_ratio': 0.3}` |
| lenient | 1.0 | A2_Biomechanical_NoK | Ridge | 71 | 46 | 0.480 | 0.281 [0.018, 0.544] | 0.585 | 11.18 | 510.3 [326.9, 693.7] | 0.199 | `{'alpha': 0.01}` |
| lenient | 1.0 | B_Clinical | SVM | 71 | 46 | 0.670 | 0.232 [-0.155, 0.618] | 0.659 | 12.21 | 624.7 [534.4, 715.0] | 0.438 | `{'C': 5000, 'epsilon': 100, 'gamma': 0.05}` |
| lenient | 1.0 | B_Clinical | Random_Forest | 71 | 46 | 0.585 | 0.312 [0.178, 0.447] | 0.623 | 11.94 | 566.1 [411.7, 720.5] | 0.273 | `{'n_estimators': 50, 'max_depth': 2, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 1.0 | B_Clinical | XGBoost | 71 | 46 | 0.630 | 0.305 [0.039, 0.571] | 0.591 | 12.31 | 567.3 [370.4, 764.3] | 0.325 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 2.0}` |
| lenient | 1.0 | B_Clinical | Neural_Network | 71 | 46 | 0.586 | 0.264 [-0.085, 0.614] | 0.680 | 11.51 | 559.1 [437.3, 681.0] | 0.322 | `{'hidden_layer_sizes': (100,), 'alpha': 0.1, 'learning_rate_init': 0.001}` |
| lenient | 1.0 | B_Clinical | Lasso | 71 | 46 | 0.412 | 0.169 [-0.293, 0.632] | 0.654 | 13.55 | 631.4 [337.6, 925.1] | 0.242 | `{'alpha': 0.001}` |
| lenient | 1.0 | B_Clinical | ElasticNet | 71 | 46 | 0.359 | 0.157 [-0.259, 0.573] | 0.656 | 13.41 | 635.4 [370.6, 900.2] | 0.203 | `{'alpha': 1.0, 'l1_ratio': 0.5}` |
| lenient | 1.0 | B_Clinical | Ridge | 71 | 46 | 0.412 | 0.169 [-0.293, 0.632] | 0.654 | 13.55 | 631.4 [337.6, 925.1] | 0.242 | `{'alpha': 0.01}` |
| lenient | 1.0 | C1_Combined | SVM | 71 | 46 | 0.502 | 0.388 [0.187, 0.590] | 0.643 | 11.48 | 557.5 [313.6, 801.4] | 0.114 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 1.0 | C1_Combined | Random_Forest | 71 | 46 | 0.733 | 0.422 [0.266, 0.577] | 0.700 | 11.21 | 552.7 [391.9, 713.4] | 0.311 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| lenient | 1.0 | C1_Combined | XGBoost | 71 | 46 | 0.728 | 0.433 [0.341, 0.525] | 0.712 | 11.00 | 513.2 [381.6, 644.9] | 0.295 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 2.0}` |
| lenient | 1.0 | C1_Combined | Neural_Network | 71 | 46 | 0.665 | 0.399 [0.255, 0.542] | 0.737 | 9.85 | 521.9 [379.8, 664.1] | 0.267 | `{'hidden_layer_sizes': (100,), 'alpha': 0.1, 'learning_rate_init': 0.001}` |
| lenient | 1.0 | C1_Combined | Lasso | 71 | 46 | 0.550 | 0.364 [-0.026, 0.753] | 0.699 | 10.86 | 523.7 [288.0, 759.4] | 0.187 | `{'alpha': 1.0}` |
| lenient | 1.0 | C1_Combined | ElasticNet | 71 | 46 | 0.548 | 0.397 [0.051, 0.742] | 0.708 | 10.70 | 514.9 [277.9, 751.8] | 0.151 | `{'alpha': 0.1, 'l1_ratio': 0.3}` |
| lenient | 1.0 | C1_Combined | Ridge | 71 | 46 | 0.537 | 0.424 [0.134, 0.715] | 0.716 | 10.62 | 510.1 [266.2, 754.0] | 0.113 | `{'alpha': 10.0}` |
| lenient | 1.5 | A1_Biomechanical_Core | SVM | 71 | 46 | 0.440 | 0.336 [0.194, 0.478] | 0.688 | 10.96 | 561.3 [336.5, 786.0] | 0.103 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 1.5 | A1_Biomechanical_Core | Random_Forest | 71 | 46 | 0.709 | 0.443 [0.167, 0.719] | 0.738 | 9.57 | 524.5 [319.2, 729.9] | 0.266 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| lenient | 1.5 | A1_Biomechanical_Core | XGBoost | 71 | 46 | 0.736 | 0.434 [0.182, 0.687] | 0.697 | 10.30 | 541.2 [320.4, 762.1] | 0.301 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 1.0}` |
| lenient | 1.5 | A1_Biomechanical_Core | Neural_Network | 71 | 46 | 0.596 | 0.376 [0.211, 0.541] | 0.738 | 9.45 | 517.8 [274.4, 761.2] | 0.219 | `{'hidden_layer_sizes': (80,), 'alpha': 0.5, 'learning_rate_init': 0.001}` |
| lenient | 1.5 | A1_Biomechanical_Core | Lasso | 71 | 46 | 0.508 | 0.403 [0.170, 0.636] | 0.695 | 10.42 | 561.7 [337.0, 786.4] | 0.105 | `{'alpha': 10.0}` |
| lenient | 1.5 | A1_Biomechanical_Core | ElasticNet | 71 | 46 | 0.509 | 0.388 [0.155, 0.620] | 0.688 | 10.52 | 568.9 [348.4, 789.4] | 0.121 | `{'alpha': 0.001, 'l1_ratio': 0.5}` |
| lenient | 1.5 | A1_Biomechanical_Core | Ridge | 71 | 46 | 0.578 | 0.372 [0.218, 0.526] | 0.688 | 10.82 | 469.8 [312.4, 627.2] | 0.206 | `{'alpha': 0.1}` |
| lenient | 1.5 | A2_Biomechanical_NoK | SVM | 71 | 46 | 0.360 | 0.324 [0.127, 0.522] | 0.707 | 9.27 | 527.4 [213.3, 841.4] | 0.036 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 1.5 | A2_Biomechanical_NoK | Random_Forest | 71 | 46 | 0.782 | 0.506 [0.301, 0.711] | 0.786 | 9.63 | 422.2 [240.0, 604.4] | 0.276 | `{'n_estimators': 100, 'max_depth': 2, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| lenient | 1.5 | A2_Biomechanical_NoK | XGBoost | 71 | 46 | 0.675 | 0.425 [0.277, 0.573] | 0.743 | 9.72 | 451.4 [291.5, 611.3] | 0.250 | `{'learning_rate': 0.01, 'max_depth': 4, 'n_estimators': 100, 'reg_alpha': 2.0, 'reg_lambda': 2.0}` |
| lenient | 1.5 | A2_Biomechanical_NoK | Neural_Network | 71 | 46 | 0.600 | 0.298 [0.036, 0.560] | 0.702 | 9.67 | 500.0 [309.0, 691.1] | 0.302 | `{'hidden_layer_sizes': (100,), 'alpha': 0.3, 'learning_rate_init': 0.0005}` |
| lenient | 1.5 | A2_Biomechanical_NoK | Lasso | 71 | 46 | 0.457 | 0.229 [-0.176, 0.633] | 0.572 | 10.22 | 561.0 [285.4, 836.5] | 0.228 | `{'alpha': 10.0}` |
| lenient | 1.5 | A2_Biomechanical_NoK | ElasticNet | 71 | 46 | 0.480 | 0.186 [-0.309, 0.681] | 0.720 | 9.89 | 532.7 [298.9, 766.4] | 0.294 | `{'alpha': 0.1, 'l1_ratio': 0.9}` |
| lenient | 1.5 | A2_Biomechanical_NoK | Ridge | 71 | 46 | 0.468 | 0.275 [-0.008, 0.559] | 0.715 | 9.59 | 521.5 [263.9, 779.2] | 0.192 | `{'alpha': 10.0}` |
| lenient | 1.5 | B_Clinical | SVM | 71 | 46 | 0.322 | 0.234 [0.065, 0.403] | 0.719 | 10.44 | 553.6 [260.5, 846.6] | 0.088 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 1.5 | B_Clinical | Random_Forest | 71 | 46 | 0.657 | 0.319 [0.228, 0.409] | 0.622 | 10.45 | 546.6 [294.8, 798.3] | 0.339 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 1.5 | B_Clinical | XGBoost | 71 | 46 | 0.639 | 0.219 [-0.141, 0.578] | 0.671 | 11.87 | 604.5 [333.4, 875.7] | 0.420 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 50, 'reg_alpha': 2.0, 'reg_lambda': 0.1}` |
| lenient | 1.5 | B_Clinical | Neural_Network | 71 | 46 | 0.731 | 0.320 [0.085, 0.555] | 0.684 | 12.20 | 540.0 [336.7, 743.3] | 0.410 | `{'hidden_layer_sizes': (60,), 'alpha': 0.3, 'learning_rate_init': 0.0005}` |
| lenient | 1.5 | B_Clinical | Lasso | 71 | 46 | 0.460 | 0.219 [-0.066, 0.504] | 0.734 | 11.48 | 538.3 [289.7, 787.0] | 0.241 | `{'alpha': 1.0}` |
| lenient | 1.5 | B_Clinical | ElasticNet | 71 | 46 | 0.460 | 0.221 [-0.057, 0.500] | 0.734 | 11.46 | 537.7 [289.3, 786.1] | 0.238 | `{'alpha': 0.1, 'l1_ratio': 0.9}` |
| lenient | 1.5 | B_Clinical | Ridge | 71 | 46 | 0.446 | 0.253 [0.061, 0.445] | 0.733 | 11.08 | 532.4 [280.2, 784.7] | 0.193 | `{'alpha': 10.0}` |
| lenient | 1.5 | C1_Combined | SVM | 71 | 46 | 0.507 | 0.411 [0.272, 0.550] | 0.721 | 10.16 | 525.4 [331.2, 719.7] | 0.097 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 1.5 | C1_Combined | Random_Forest | 71 | 46 | 0.724 | 0.473 [0.228, 0.718] | 0.729 | 9.39 | 515.2 [322.6, 707.9] | 0.251 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| lenient | 1.5 | C1_Combined | XGBoost | 71 | 46 | 0.708 | 0.388 [0.132, 0.644] | 0.774 | 10.27 | 504.4 [218.0, 790.9] | 0.320 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 30, 'reg_alpha': 1.0, 'reg_lambda': 0.1}` |
| lenient | 1.5 | C1_Combined | Neural_Network | 71 | 46 | 0.575 | 0.310 [0.061, 0.558] | 0.649 | 9.82 | 446.2 [327.3, 565.0] | 0.265 | `{'hidden_layer_sizes': (100,), 'alpha': 0.5, 'learning_rate_init': 0.0001}` |
| lenient | 1.5 | C1_Combined | Lasso | 71 | 46 | 0.578 | 0.538 [0.312, 0.764] | 0.744 | 9.27 | 491.4 [259.9, 722.9] | 0.040 | `{'alpha': 10.0}` |
| lenient | 1.5 | C1_Combined | ElasticNet | 71 | 46 | 0.578 | 0.529 [0.314, 0.745] | 0.740 | 9.40 | 496.8 [272.3, 721.3] | 0.049 | `{'alpha': 0.001, 'l1_ratio': 0.5}` |
| lenient | 1.5 | C1_Combined | Ridge | 71 | 46 | 0.635 | 0.398 [0.234, 0.563] | 0.732 | 11.03 | 467.6 [285.7, 649.5] | 0.236 | `{'alpha': 0.1}` |
| lenient | 2.0 | A1_Biomechanical_Core | SVM | 71 | 46 | 0.394 | 0.301 [0.158, 0.444] | 0.592 | 10.64 | 520.9 [323.7, 718.1] | 0.094 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 2.0 | A1_Biomechanical_Core | Random_Forest | 71 | 46 | 0.654 | 0.394 [0.157, 0.630] | 0.699 | 10.52 | 475.9 [273.7, 678.2] | 0.261 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| lenient | 2.0 | A1_Biomechanical_Core | XGBoost | 71 | 46 | 0.684 | 0.421 [0.151, 0.691] | 0.683 | 10.22 | 464.1 [258.1, 670.1] | 0.263 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 1.0}` |
| lenient | 2.0 | A1_Biomechanical_Core | Neural_Network | 71 | 46 | 0.518 | 0.372 [0.231, 0.512] | 0.662 | 10.03 | 460.9 [246.1, 675.7] | 0.146 | `{'hidden_layer_sizes': (80,), 'alpha': 0.5, 'learning_rate_init': 0.001}` |
| lenient | 2.0 | A1_Biomechanical_Core | Lasso | 71 | 46 | 0.449 | 0.349 [0.151, 0.548] | 0.669 | 10.16 | 496.0 [290.8, 701.2] | 0.100 | `{'alpha': 10.0}` |
| lenient | 2.0 | A1_Biomechanical_Core | ElasticNet | 71 | 46 | 0.450 | 0.329 [0.147, 0.511] | 0.663 | 10.34 | 502.5 [306.8, 698.1] | 0.121 | `{'alpha': 0.001, 'l1_ratio': 0.5}` |
| lenient | 2.0 | A1_Biomechanical_Core | Ridge | 71 | 46 | 0.415 | 0.290 [0.178, 0.402] | 0.622 | 10.86 | 486.6 [343.4, 629.8] | 0.125 | `{'alpha': 10.0}` |
| lenient | 2.0 | A2_Biomechanical_NoK | SVM | 71 | 46 | 0.451 | 0.197 [-0.053, 0.448] | 0.497 | 11.08 | 556.7 [341.7, 771.7] | 0.254 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 2.0 | A2_Biomechanical_NoK | Random_Forest | 71 | 46 | 0.698 | 0.398 [0.077, 0.718] | 0.686 | 10.37 | 472.4 [225.9, 719.0] | 0.300 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| lenient | 2.0 | A2_Biomechanical_NoK | XGBoost | 71 | 46 | 0.707 | 0.349 [0.007, 0.691] | 0.635 | 11.54 | 490.1 [265.1, 715.1] | 0.357 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 1.0}` |
| lenient | 2.0 | A2_Biomechanical_NoK | Neural_Network | 71 | 46 | 0.433 | 0.248 [0.058, 0.438] | 0.717 | 11.55 | 431.1 [269.8, 592.5] | 0.185 | `{'hidden_layer_sizes': (80, 40), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| lenient | 2.0 | A2_Biomechanical_NoK | Lasso | 71 | 46 | 0.483 | 0.292 [0.085, 0.499] | 0.572 | 11.02 | 525.0 [315.9, 734.0] | 0.191 | `{'alpha': 10.0}` |
| lenient | 2.0 | A2_Biomechanical_NoK | ElasticNet | 71 | 46 | 0.485 | 0.258 [-0.002, 0.518] | 0.554 | 11.17 | 536.9 [316.7, 757.0] | 0.227 | `{'alpha': 0.1, 'l1_ratio': 0.9}` |
| lenient | 2.0 | A2_Biomechanical_NoK | Ridge | 71 | 46 | 0.460 | 0.246 [0.148, 0.345] | 0.555 | 12.04 | 476.3 [364.6, 588.0] | 0.213 | `{'alpha': 1.0}` |
| lenient | 2.0 | B_Clinical | SVM | 71 | 46 | 0.311 | 0.234 [0.055, 0.414] | 0.672 | 10.29 | 475.6 [235.2, 716.1] | 0.077 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 2.0 | B_Clinical | Random_Forest | 71 | 46 | 0.604 | 0.230 [0.163, 0.298] | 0.552 | 11.92 | 508.0 [298.0, 718.0] | 0.374 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 2.0 | B_Clinical | XGBoost | 71 | 46 | 0.575 | 0.232 [0.044, 0.421] | 0.622 | 12.77 | 541.5 [345.4, 737.6] | 0.343 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 50, 'reg_alpha': 2.0, 'reg_lambda': 0.1}` |
| lenient | 2.0 | B_Clinical | Neural_Network | 71 | 46 | 0.391 | 0.182 [-0.036, 0.400] | 0.486 | 12.60 | 530.0 [302.5, 757.6] | 0.209 | `{'hidden_layer_sizes': (60,), 'alpha': 1.0, 'learning_rate_init': 0.0005}` |
| lenient | 2.0 | B_Clinical | Lasso | 71 | 46 | 0.429 | 0.165 [-0.102, 0.433] | 0.679 | 11.72 | 475.7 [290.0, 661.4] | 0.264 | `{'alpha': 1.0}` |
| lenient | 2.0 | B_Clinical | ElasticNet | 71 | 46 | 0.429 | 0.168 [-0.093, 0.429] | 0.678 | 11.68 | 475.2 [289.2, 661.3] | 0.261 | `{'alpha': 0.1, 'l1_ratio': 0.9}` |
| lenient | 2.0 | B_Clinical | Ridge | 71 | 46 | 0.416 | 0.203 [0.028, 0.378] | 0.678 | 11.19 | 471.3 [272.7, 669.9] | 0.213 | `{'alpha': 10.0}` |
| lenient | 2.0 | C1_Combined | SVM | 71 | 46 | 0.480 | 0.393 [0.300, 0.486] | 0.678 | 9.86 | 482.9 [320.7, 645.2] | 0.087 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 2.0 | C1_Combined | Random_Forest | 71 | 46 | 0.668 | 0.396 [0.152, 0.639] | 0.672 | 10.20 | 475.1 [272.8, 677.4] | 0.272 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| lenient | 2.0 | C1_Combined | XGBoost | 71 | 46 | 0.614 | 0.344 [0.080, 0.609] | 0.628 | 10.82 | 445.4 [278.3, 612.6] | 0.269 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 2.0}` |
| lenient | 2.0 | C1_Combined | Neural_Network | 71 | 46 | 0.553 | 0.324 [0.241, 0.407] | 0.657 | 10.80 | 507.2 [349.0, 665.5] | 0.229 | `{'hidden_layer_sizes': (80,), 'alpha': 0.3, 'learning_rate_init': 0.0001}` |
| lenient | 2.0 | C1_Combined | Lasso | 71 | 46 | 0.513 | 0.474 [0.295, 0.653] | 0.702 | 9.71 | 447.6 [247.8, 647.4] | 0.039 | `{'alpha': 10.0}` |
| lenient | 2.0 | C1_Combined | ElasticNet | 71 | 46 | 0.514 | 0.467 [0.304, 0.629] | 0.701 | 9.82 | 449.8 [258.4, 641.2] | 0.047 | `{'alpha': 0.001, 'l1_ratio': 0.5}` |
| lenient | 2.0 | C1_Combined | Ridge | 71 | 46 | 0.448 | 0.369 [0.180, 0.558] | 0.684 | 11.42 | 438.0 [293.7, 582.2] | 0.079 | `{'alpha': 1.0}` |
| lenient | 2.5 | A1_Biomechanical_Core | SVM | 71 | 46 | 0.446 | 0.312 [0.186, 0.437] | 0.620 | 13.15 | 489.9 [339.9, 639.9] | 0.134 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 2.5 | A1_Biomechanical_Core | Random_Forest | 71 | 46 | 0.557 | 0.262 [-0.018, 0.542] | 0.558 | 13.40 | 448.4 [314.4, 582.5] | 0.295 | `{'n_estimators': 50, 'max_depth': 2, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 2.5 | A1_Biomechanical_Core | XGBoost | 71 | 46 | 0.573 | 0.235 [0.018, 0.451] | 0.600 | 13.53 | 504.8 [390.2, 619.5] | 0.338 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 50, 'reg_alpha': 2.0, 'reg_lambda': 0.1}` |
| lenient | 2.5 | A1_Biomechanical_Core | Neural_Network | 71 | 46 | 0.447 | 0.296 [0.169, 0.423] | 0.608 | 13.35 | 495.5 [346.4, 644.6] | 0.151 | `{'hidden_layer_sizes': (80,), 'alpha': 0.3, 'learning_rate_init': 0.0001}` |
| lenient | 2.5 | A1_Biomechanical_Core | Lasso | 71 | 46 | 0.472 | 0.376 [0.262, 0.491] | 0.652 | 12.71 | 466.9 [324.7, 609.2] | 0.096 | `{'alpha': 10.0}` |
| lenient | 2.5 | A1_Biomechanical_Core | ElasticNet | 71 | 46 | 0.473 | 0.362 [0.242, 0.482] | 0.640 | 12.80 | 472.9 [325.4, 620.4] | 0.111 | `{'alpha': 0.1, 'l1_ratio': 0.9}` |
| lenient | 2.5 | A1_Biomechanical_Core | Ridge | 71 | 46 | 0.411 | 0.288 [0.100, 0.476] | 0.620 | 14.78 | 481.2 [189.8, 772.5] | 0.123 | `{'alpha': 10.0}` |
| lenient | 2.5 | A2_Biomechanical_NoK | SVM | 71 | 46 | 0.502 | 0.205 [-0.037, 0.447] | 0.519 | 13.45 | 530.0 [337.7, 722.4] | 0.297 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 2.5 | A2_Biomechanical_NoK | Random_Forest | 71 | 46 | 0.598 | 0.227 [-0.003, 0.457] | 0.533 | 13.46 | 457.6 [346.4, 568.8] | 0.371 | `{'n_estimators': 50, 'max_depth': 2, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 2.5 | A2_Biomechanical_NoK | XGBoost | 71 | 46 | 0.640 | 0.269 [0.179, 0.359] | 0.668 | 12.14 | 423.7 [280.7, 566.6] | 0.371 | `{'learning_rate': 0.01, 'max_depth': 4, 'n_estimators': 100, 'reg_alpha': 2.0, 'reg_lambda': 2.0}` |
| lenient | 2.5 | A2_Biomechanical_NoK | Neural_Network | 71 | 46 | 0.454 | 0.204 [0.011, 0.397] | 0.634 | 13.79 | 442.3 [278.4, 606.1] | 0.250 | `{'hidden_layer_sizes': (80, 40), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| lenient | 2.5 | A2_Biomechanical_NoK | Lasso | 71 | 46 | 0.521 | 0.300 [0.188, 0.411] | 0.603 | 13.40 | 496.8 [342.8, 650.8] | 0.221 | `{'alpha': 10.0}` |
| lenient | 2.5 | A2_Biomechanical_NoK | ElasticNet | 71 | 46 | 0.522 | 0.267 [0.107, 0.427] | 0.586 | 13.69 | 509.6 [339.1, 680.0] | 0.255 | `{'alpha': 0.1, 'l1_ratio': 0.9}` |
| lenient | 2.5 | A2_Biomechanical_NoK | Ridge | 71 | 46 | 0.470 | 0.239 [0.076, 0.402] | 0.586 | 14.73 | 499.9 [186.9, 813.0] | 0.231 | `{'alpha': 10.0}` |
| lenient | 2.5 | B_Clinical | SVM | 71 | 46 | 0.243 | 0.142 [-0.032, 0.317] | 0.477 | 15.32 | 547.8 [369.4, 726.1] | 0.100 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 2.5 | B_Clinical | Random_Forest | 71 | 46 | 0.464 | 0.054 [-0.291, 0.400] | 0.388 | 15.81 | 500.8 [408.8, 592.7] | 0.410 | `{'n_estimators': 50, 'max_depth': 2, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 2.5 | B_Clinical | XGBoost | 71 | 46 | 0.538 | 0.246 [0.111, 0.381] | 0.647 | 14.74 | 513.1 [355.3, 670.8] | 0.292 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 50, 'reg_alpha': 2.0, 'reg_lambda': 0.1}` |
| lenient | 2.5 | B_Clinical | Neural_Network | 71 | 46 | 0.460 | 0.135 [-0.142, 0.412] | 0.534 | 14.64 | 493.2 [390.5, 595.8] | 0.325 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.3, 'learning_rate_init': 0.001}` |
| lenient | 2.5 | B_Clinical | Lasso | 71 | 46 | 0.348 | 0.160 [0.038, 0.283] | 0.564 | 14.65 | 483.9 [351.0, 616.8] | 0.187 | `{'alpha': 1.0}` |
| lenient | 2.5 | B_Clinical | ElasticNet | 71 | 46 | 0.348 | 0.161 [0.037, 0.285] | 0.564 | 14.62 | 483.7 [351.0, 616.4] | 0.187 | `{'alpha': 0.1, 'l1_ratio': 0.9}` |
| lenient | 2.5 | B_Clinical | Ridge | 71 | 46 | 0.338 | 0.165 [0.020, 0.309] | 0.562 | 14.08 | 481.9 [349.8, 614.0] | 0.173 | `{'alpha': 10.0}` |
| lenient | 2.5 | C1_Combined | SVM | 71 | 46 | 0.503 | 0.376 [0.285, 0.467] | 0.682 | 12.91 | 466.7 [331.0, 602.4] | 0.127 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 2.5 | C1_Combined | Random_Forest | 71 | 46 | 0.559 | 0.235 [-0.050, 0.521] | 0.535 | 13.59 | 456.0 [324.4, 587.5] | 0.324 | `{'n_estimators': 50, 'max_depth': 2, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 2.5 | C1_Combined | XGBoost | 71 | 46 | 0.630 | 0.246 [0.068, 0.425] | 0.646 | 13.73 | 501.5 [399.5, 603.5] | 0.383 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 50, 'reg_alpha': 2.0, 'reg_lambda': 0.1}` |
| lenient | 2.5 | C1_Combined | Neural_Network | 71 | 46 | 0.561 | 0.324 [0.197, 0.451] | 0.669 | 12.98 | 482.7 [349.3, 616.2] | 0.237 | `{'hidden_layer_sizes': (80,), 'alpha': 0.3, 'learning_rate_init': 0.0001}` |
| lenient | 2.5 | C1_Combined | Lasso | 71 | 46 | 0.513 | 0.374 [0.299, 0.448] | 0.672 | 13.21 | 465.2 [344.3, 586.1] | 0.140 | `{'alpha': 10.0}` |
| lenient | 2.5 | C1_Combined | ElasticNet | 71 | 46 | 0.515 | 0.364 [0.281, 0.448] | 0.672 | 13.32 | 469.2 [343.9, 594.6] | 0.150 | `{'alpha': 0.1, 'l1_ratio': 0.9}` |
| lenient | 2.5 | C1_Combined | Ridge | 71 | 46 | 0.346 | 0.249 [0.172, 0.326] | 0.670 | 14.73 | 510.1 [373.4, 646.7] | 0.097 | `{'alpha': 100.0}` |
| lenient | 3.0 | A1_Biomechanical_Core | SVM | 71 | 46 | 0.343 | 0.266 [0.103, 0.429] | 0.576 | 13.89 | 551.5 [320.2, 782.9] | 0.077 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 3.0 | A1_Biomechanical_Core | Random_Forest | 71 | 46 | 0.554 | 0.334 [0.047, 0.622] | 0.616 | 14.13 | 508.3 [295.4, 721.1] | 0.220 | `{'n_estimators': 50, 'max_depth': 2, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 3.0 | A1_Biomechanical_Core | XGBoost | 71 | 46 | 0.579 | 0.292 [0.015, 0.568] | 0.578 | 14.69 | 524.1 [315.3, 732.8] | 0.287 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 2.0}` |
| lenient | 3.0 | A1_Biomechanical_Core | Neural_Network | 71 | 46 | 0.490 | 0.315 [0.027, 0.603] | 0.627 | 13.64 | 511.7 [290.4, 733.0] | 0.175 | `{'hidden_layer_sizes': (80,), 'alpha': 0.5, 'learning_rate_init': 0.001}` |
| lenient | 3.0 | A1_Biomechanical_Core | Lasso | 71 | 46 | 0.400 | 0.334 [0.193, 0.476] | 0.638 | 12.92 | 516.5 [281.0, 752.1] | 0.066 | `{'alpha': 10.0}` |
| lenient | 3.0 | A1_Biomechanical_Core | ElasticNet | 71 | 46 | 0.401 | 0.324 [0.202, 0.446] | 0.635 | 13.07 | 520.9 [286.9, 755.0] | 0.077 | `{'alpha': 0.001, 'l1_ratio': 0.3}` |
| lenient | 3.0 | A1_Biomechanical_Core | Ridge | 71 | 46 | 0.398 | 0.318 [0.058, 0.577] | 0.575 | 13.99 | 476.5 [258.5, 694.4] | 0.081 | `{'alpha': 0.1}` |
| lenient | 3.0 | A2_Biomechanical_NoK | SVM | 71 | 46 | 0.481 | 0.210 [-0.008, 0.429] | 0.511 | 14.33 | 576.3 [311.3, 841.4] | 0.271 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 3.0 | A2_Biomechanical_NoK | Random_Forest | 71 | 46 | 0.593 | 0.324 [0.023, 0.624] | 0.611 | 14.40 | 508.6 [301.3, 715.9] | 0.269 | `{'n_estimators': 50, 'max_depth': 2, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 3.0 | A2_Biomechanical_NoK | XGBoost | 71 | 46 | 0.677 | 0.309 [0.037, 0.582] | 0.623 | 15.82 | 516.4 [317.6, 715.3] | 0.368 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 2.0}` |
| lenient | 3.0 | A2_Biomechanical_NoK | Neural_Network | 71 | 46 | 0.572 | 0.271 [-0.096, 0.637] | 0.597 | 14.79 | 552.8 [316.6, 789.0] | 0.301 | `{'hidden_layer_sizes': (100,), 'alpha': 0.3, 'learning_rate_init': 0.0005}` |
| lenient | 3.0 | A2_Biomechanical_NoK | Lasso | 71 | 46 | 0.542 | 0.325 [0.062, 0.588] | 0.602 | 13.04 | 524.1 [240.4, 807.8] | 0.217 | `{'alpha': 10.0}` |
| lenient | 3.0 | A2_Biomechanical_NoK | ElasticNet | 71 | 46 | 0.751 | 0.313 [-0.099, 0.724] | 0.674 | 13.88 | 435.6 [307.1, 564.1] | 0.438 | `{'alpha': 0.01, 'l1_ratio': 0.9}` |
| lenient | 3.0 | A2_Biomechanical_NoK | Ridge | 71 | 46 | 0.751 | 0.312 [-0.099, 0.724] | 0.674 | 13.88 | 435.8 [306.9, 564.7] | 0.438 | `{'alpha': 0.1}` |
| lenient | 3.0 | B_Clinical | SVM | 71 | 46 | 0.286 | 0.212 [0.039, 0.385] | 0.621 | 15.41 | 510.6 [310.7, 710.5] | 0.074 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 3.0 | B_Clinical | Random_Forest | 71 | 46 | 0.651 | 0.203 [-0.238, 0.644] | 0.565 | 14.64 | 557.8 [379.4, 736.3] | 0.447 | `{'n_estimators': 300, 'max_depth': 3, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| lenient | 3.0 | B_Clinical | XGBoost | 71 | 46 | 0.503 | 0.138 [-0.170, 0.446] | 0.605 | 17.09 | 598.2 [335.4, 861.0] | 0.365 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 50, 'reg_alpha': 2.0, 'reg_lambda': 0.1}` |
| lenient | 3.0 | B_Clinical | Neural_Network | 71 | 46 | 0.523 | 0.107 [-0.270, 0.483] | 0.501 | 18.29 | 535.2 [311.4, 759.0] | 0.416 | `{'hidden_layer_sizes': (100,), 'alpha': 0.3, 'learning_rate_init': 0.0005}` |
| lenient | 3.0 | B_Clinical | Lasso | 71 | 46 | 0.365 | 0.235 [0.110, 0.360] | 0.645 | 16.14 | 503.2 [318.1, 688.3] | 0.131 | `{'alpha': 1.0}` |
| lenient | 3.0 | B_Clinical | ElasticNet | 71 | 46 | 0.365 | 0.235 [0.112, 0.358] | 0.644 | 16.12 | 503.0 [318.2, 687.8] | 0.130 | `{'alpha': 0.1, 'l1_ratio': 0.9}` |
| lenient | 3.0 | B_Clinical | Ridge | 71 | 46 | 0.355 | 0.240 [0.138, 0.343] | 0.645 | 15.96 | 501.0 [318.5, 683.4] | 0.115 | `{'alpha': 10.0}` |
| lenient | 3.0 | C1_Combined | SVM | 71 | 46 | 0.401 | 0.295 [0.120, 0.469] | 0.652 | 13.89 | 543.3 [307.3, 779.3] | 0.106 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 3.0 | C1_Combined | Random_Forest | 71 | 46 | 0.553 | 0.282 [-0.029, 0.593] | 0.568 | 14.72 | 524.2 [318.9, 729.5] | 0.271 | `{'n_estimators': 50, 'max_depth': 2, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 3.0 | C1_Combined | XGBoost | 71 | 46 | 0.584 | 0.246 [-0.071, 0.562] | 0.530 | 15.26 | 537.2 [331.0, 743.3] | 0.339 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 2.0}` |
| lenient | 3.0 | C1_Combined | Neural_Network | 71 | 46 | 0.495 | 0.263 [0.182, 0.345] | 0.598 | 14.30 | 545.7 [352.8, 738.7] | 0.232 | `{'hidden_layer_sizes': (80,), 'alpha': 0.3, 'learning_rate_init': 0.0001}` |
| lenient | 3.0 | C1_Combined | Lasso | 71 | 46 | 0.438 | 0.376 [0.011, 0.740] | 0.645 | 13.42 | 505.4 [275.5, 735.3] | 0.062 | `{'alpha': 10.0}` |
| lenient | 3.0 | C1_Combined | ElasticNet | 71 | 46 | 0.439 | 0.368 [-0.007, 0.744] | 0.642 | 13.61 | 506.8 [279.0, 734.7] | 0.070 | `{'alpha': 0.001, 'l1_ratio': 0.5}` |
| lenient | 3.0 | C1_Combined | Ridge | 71 | 46 | 0.388 | 0.319 [0.113, 0.525] | 0.661 | 15.15 | 516.5 [327.1, 705.9] | 0.069 | `{'alpha': 1.0}` |
| lenient | 3.5 | A1_Biomechanical_Core | SVM | 71 | 46 | 0.328 | 0.189 [0.060, 0.319] | 0.510 | 15.06 | 550.6 [400.1, 701.0] | 0.138 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 3.5 | A1_Biomechanical_Core | Random_Forest | 71 | 46 | 0.602 | 0.255 [0.072, 0.439] | 0.625 | 13.41 | 492.9 [302.6, 683.1] | 0.346 | `{'n_estimators': 100, 'max_depth': 5, 'min_samples_split': 5, 'min_samples_leaf': 4}` |
| lenient | 3.5 | A1_Biomechanical_Core | XGBoost | 71 | 46 | 0.365 | 0.184 [-0.175, 0.544] | 0.558 | 16.51 | 529.5 [261.9, 797.0] | 0.181 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 30, 'reg_alpha': 2.0, 'reg_lambda': 0.5}` |
| lenient | 3.5 | A1_Biomechanical_Core | Neural_Network | 71 | 46 | 0.373 | 0.226 [0.023, 0.430] | 0.538 | 16.29 | 506.8 [288.6, 724.9] | 0.147 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.3, 'learning_rate_init': 0.001}` |
| lenient | 3.5 | A1_Biomechanical_Core | Lasso | 71 | 46 | 0.423 | 0.312 [0.047, 0.576] | 0.623 | 13.49 | 479.9 [262.9, 697.0] | 0.112 | `{'alpha': 1.0}` |
| lenient | 3.5 | A1_Biomechanical_Core | ElasticNet | 71 | 46 | 0.405 | 0.297 [0.052, 0.542] | 0.615 | 13.69 | 485.6 [265.5, 705.6] | 0.108 | `{'alpha': 1.0, 'l1_ratio': 0.7}` |
| lenient | 3.5 | A1_Biomechanical_Core | Ridge | 71 | 46 | 0.416 | 0.308 [0.058, 0.559] | 0.617 | 13.39 | 481.6 [263.2, 700.0] | 0.108 | `{'alpha': 10.0}` |
| lenient | 3.5 | A2_Biomechanical_NoK | SVM | 71 | 46 | 0.229 | 0.170 [-0.010, 0.349] | 0.498 | 15.98 | 538.7 [357.7, 719.7] | 0.059 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 3.5 | A2_Biomechanical_NoK | Random_Forest | 71 | 46 | 0.724 | 0.287 [0.011, 0.563] | 0.626 | 15.08 | 527.6 [332.3, 722.9] | 0.436 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 3.5 | A2_Biomechanical_NoK | XGBoost | 71 | 46 | 0.869 | 0.372 [0.223, 0.521] | 0.639 | 14.44 | 442.1 [232.9, 651.3] | 0.497 | `{'learning_rate': 0.05, 'max_depth': 2, 'n_estimators': 100, 'reg_alpha': 2.0, 'reg_lambda': 1.0}` |
| lenient | 3.5 | A2_Biomechanical_NoK | Neural_Network | 71 | 46 | 0.230 | 0.255 [0.029, 0.481] | 0.525 | 15.68 | 476.7 [255.2, 698.2] | -0.025 | `{'hidden_layer_sizes': (100,), 'alpha': 0.5, 'learning_rate_init': 0.0001}` |
| lenient | 3.5 | A2_Biomechanical_NoK | Lasso | 71 | 46 | 0.446 | 0.240 [0.081, 0.399] | 0.517 | 15.88 | 554.0 [373.8, 734.2] | 0.206 | `{'alpha': 10.0}` |
| lenient | 3.5 | A2_Biomechanical_NoK | ElasticNet | 71 | 46 | 0.494 | 0.255 [0.032, 0.478] | 0.559 | 15.10 | 488.8 [279.8, 697.8] | 0.239 | `{'alpha': 1.0, 'l1_ratio': 0.7}` |
| lenient | 3.5 | A2_Biomechanical_NoK | Ridge | 71 | 46 | 0.512 | 0.239 [0.027, 0.450] | 0.559 | 15.25 | 490.3 [293.3, 687.4] | 0.274 | `{'alpha': 10.0}` |
| lenient | 3.5 | B_Clinical | SVM | 71 | 46 | 0.234 | 0.187 [0.015, 0.360] | 0.550 | 16.45 | 530.3 [365.6, 695.0] | 0.046 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 3.5 | B_Clinical | Random_Forest | 71 | 46 | 0.553 | 0.081 [-0.123, 0.285] | 0.427 | 18.51 | 609.5 [404.6, 814.4] | 0.472 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 3.5 | B_Clinical | XGBoost | 71 | 46 | 0.495 | 0.097 [-0.201, 0.395] | 0.515 | 18.71 | 582.2 [392.2, 772.2] | 0.398 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 50, 'reg_alpha': 2.0, 'reg_lambda': 0.1}` |
| lenient | 3.5 | B_Clinical | Neural_Network | 71 | 46 | 0.368 | 0.181 [0.069, 0.293] | 0.599 | 16.75 | 517.0 [322.8, 711.2] | 0.187 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.3, 'learning_rate_init': 0.001}` |
| lenient | 3.5 | B_Clinical | Lasso | 71 | 46 | 0.295 | 0.227 [0.047, 0.408] | 0.557 | 16.61 | 517.9 [350.4, 685.5] | 0.068 | `{'alpha': 1.0}` |
| lenient | 3.5 | B_Clinical | ElasticNet | 71 | 46 | 0.295 | 0.227 [0.047, 0.407] | 0.557 | 16.59 | 517.9 [350.8, 685.1] | 0.068 | `{'alpha': 0.1, 'l1_ratio': 0.9}` |
| lenient | 3.5 | B_Clinical | Ridge | 71 | 46 | 0.287 | 0.221 [0.062, 0.381] | 0.555 | 16.59 | 518.9 [359.2, 678.7] | 0.065 | `{'alpha': 10.0}` |
| lenient | 3.5 | C1_Combined | SVM | 71 | 46 | 0.392 | 0.239 [0.078, 0.399] | 0.597 | 14.64 | 532.0 [388.0, 676.1] | 0.154 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 3.5 | C1_Combined | Random_Forest | 71 | 46 | 0.672 | 0.193 [-0.162, 0.548] | 0.545 | 15.99 | 557.5 [342.6, 772.5] | 0.479 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 3.5 | C1_Combined | XGBoost | 71 | 46 | 0.372 | 0.165 [-0.200, 0.530] | 0.542 | 16.76 | 534.5 [268.5, 800.5] | 0.207 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 30, 'reg_alpha': 2.0, 'reg_lambda': 0.5}` |
| lenient | 3.5 | C1_Combined | Neural_Network | 71 | 46 | 0.419 | 0.217 [0.055, 0.379] | 0.519 | 15.49 | 535.9 [416.2, 655.5] | 0.202 | `{'hidden_layer_sizes': (80,), 'alpha': 0.3, 'learning_rate_init': 0.0001}` |
| lenient | 3.5 | C1_Combined | Lasso | 71 | 46 | 0.395 | 0.319 [0.056, 0.582] | 0.570 | 14.46 | 456.2 [230.1, 682.3] | 0.076 | `{'alpha': 0.01}` |
| lenient | 3.5 | C1_Combined | ElasticNet | 71 | 46 | 0.426 | 0.270 [0.082, 0.457] | 0.656 | 13.81 | 490.5 [292.5, 688.6] | 0.157 | `{'alpha': 1.0, 'l1_ratio': 0.7}` |
| lenient | 3.5 | C1_Combined | Ridge | 71 | 46 | 0.395 | 0.321 [0.055, 0.588] | 0.571 | 14.44 | 455.4 [228.6, 682.3] | 0.073 | `{'alpha': 0.1}` |
| lenient | 4.0 | A1_Biomechanical_Core | SVM | 71 | 46 | 0.327 | 0.223 [0.140, 0.305] | 0.548 | 17.87 | 617.1 [422.9, 811.3] | 0.104 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 4.0 | A1_Biomechanical_Core | Random_Forest | 71 | 46 | 0.702 | 0.153 [-0.182, 0.487] | 0.481 | 17.48 | 515.4 [323.4, 707.3] | 0.550 | `{'n_estimators': 100, 'max_depth': 4, 'min_samples_split': 10, 'min_samples_leaf': 1}` |
| lenient | 4.0 | A1_Biomechanical_Core | XGBoost | 71 | 46 | 0.598 | 0.238 [-0.055, 0.530] | 0.514 | 17.04 | 490.3 [298.4, 682.1] | 0.360 | `{'learning_rate': 0.01, 'max_depth': 4, 'n_estimators': 100, 'reg_alpha': 2.0, 'reg_lambda': 2.0}` |
| lenient | 4.0 | A1_Biomechanical_Core | Neural_Network | 71 | 46 | 0.400 | 0.202 [0.078, 0.326] | 0.504 | 19.47 | 619.0 [460.8, 777.3] | 0.198 | `{'hidden_layer_sizes': (80,), 'alpha': 0.3, 'learning_rate_init': 0.0001}` |
| lenient | 4.0 | A1_Biomechanical_Core | Lasso | 71 | 46 | 0.399 | 0.245 [0.123, 0.367] | 0.564 | 18.67 | 602.4 [443.6, 761.3] | 0.154 | `{'alpha': 10.0}` |
| lenient | 4.0 | A1_Biomechanical_Core | ElasticNet | 71 | 46 | 0.400 | 0.228 [0.093, 0.363] | 0.551 | 18.83 | 609.2 [447.0, 771.4] | 0.172 | `{'alpha': 0.1, 'l1_ratio': 0.9}` |
| lenient | 4.0 | A1_Biomechanical_Core | Ridge | 71 | 46 | 0.393 | 0.226 [-0.066, 0.518] | 0.541 | 17.39 | 523.2 [312.3, 734.1] | 0.167 | `{'alpha': 0.1}` |
| lenient | 4.0 | A2_Biomechanical_NoK | SVM | 71 | 46 | 0.427 | 0.167 [0.006, 0.327] | 0.476 | 18.16 | 643.7 [402.8, 884.6] | 0.261 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 4.0 | A2_Biomechanical_NoK | Random_Forest | 71 | 46 | 0.701 | 0.220 [-0.147, 0.588] | 0.627 | 19.05 | 600.7 [469.1, 732.4] | 0.481 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 4.0 | A2_Biomechanical_NoK | XGBoost | 71 | 46 | 0.427 | 0.139 [-0.192, 0.470] | 0.483 | 18.98 | 588.3 [386.6, 789.9] | 0.288 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 30, 'reg_alpha': 2.0, 'reg_lambda': 0.5}` |
| lenient | 4.0 | A2_Biomechanical_NoK | Neural_Network | 71 | 46 | 0.302 | 0.251 [0.054, 0.449] | 0.568 | 17.24 | 527.9 [282.8, 772.9] | 0.050 | `{'hidden_layer_sizes': (100,), 'alpha': 0.5, 'learning_rate_init': 0.0001}` |
| lenient | 4.0 | A2_Biomechanical_NoK | Lasso | 71 | 46 | 0.590 | 0.259 [-0.161, 0.678] | 0.630 | 18.00 | 486.5 [444.3, 528.8] | 0.332 | `{'alpha': 0.01}` |
| lenient | 4.0 | A2_Biomechanical_NoK | ElasticNet | 71 | 46 | 0.590 | 0.258 [-0.162, 0.678] | 0.630 | 18.01 | 486.5 [444.4, 528.7] | 0.332 | `{'alpha': 0.01, 'l1_ratio': 0.9}` |
| lenient | 4.0 | A2_Biomechanical_NoK | Ridge | 71 | 46 | 0.590 | 0.258 [-0.162, 0.679] | 0.630 | 18.01 | 486.5 [444.4, 528.6] | 0.332 | `{'alpha': 0.1}` |
| lenient | 4.0 | B_Clinical | SVM | 71 | 46 | 0.182 | 0.159 [0.026, 0.292] | 0.559 | 18.45 | 623.5 [420.4, 826.5] | 0.023 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 4.0 | B_Clinical | Random_Forest | 71 | 46 | 0.737 | 0.046 [-0.468, 0.560] | 0.508 | 20.42 | 655.3 [485.6, 825.0] | 0.691 | `{'n_estimators': 300, 'max_depth': None, 'min_samples_split': 2, 'min_samples_leaf': 2}` |
| lenient | 4.0 | B_Clinical | XGBoost | 71 | 46 | 0.535 | 0.067 [-0.446, 0.579] | 0.574 | 22.24 | 654.8 [450.4, 859.1] | 0.469 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 50, 'reg_alpha': 2.0, 'reg_lambda': 0.1}` |
| lenient | 4.0 | B_Clinical | Neural_Network | 71 | 46 | 0.339 | 0.160 [0.075, 0.245] | 0.635 | 18.85 | 563.8 [294.3, 833.3] | 0.179 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.3, 'learning_rate_init': 0.001}` |
| lenient | 4.0 | B_Clinical | Lasso | 71 | 46 | 0.298 | 0.244 [0.127, 0.360] | 0.579 | 20.59 | 594.4 [390.6, 798.3] | 0.055 | `{'alpha': 1.0}` |
| lenient | 4.0 | B_Clinical | ElasticNet | 71 | 46 | 0.298 | 0.244 [0.128, 0.360] | 0.578 | 20.58 | 594.2 [390.9, 797.6] | 0.054 | `{'alpha': 0.1, 'l1_ratio': 0.9}` |
| lenient | 4.0 | B_Clinical | Ridge | 71 | 46 | 0.290 | 0.239 [0.137, 0.341] | 0.576 | 20.48 | 594.7 [398.9, 790.5] | 0.051 | `{'alpha': 10.0}` |
| lenient | 4.0 | C1_Combined | SVM | 71 | 46 | 0.400 | 0.288 [0.163, 0.413] | 0.637 | 17.19 | 585.6 [419.3, 751.8] | 0.112 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 4.0 | C1_Combined | Random_Forest | 71 | 46 | 0.716 | 0.102 [-0.107, 0.310] | 0.429 | 16.92 | 528.1 [370.0, 686.1] | 0.614 | `{'n_estimators': 100, 'max_depth': 4, 'min_samples_split': 10, 'min_samples_leaf': 1}` |
| lenient | 4.0 | C1_Combined | XGBoost | 71 | 46 | 0.402 | 0.131 [-0.251, 0.514] | 0.503 | 19.13 | 594.2 [368.4, 820.1] | 0.271 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 30, 'reg_alpha': 2.0, 'reg_lambda': 0.5}` |
| lenient | 4.0 | C1_Combined | Neural_Network | 71 | 46 | 0.469 | 0.260 [0.081, 0.439] | 0.539 | 18.43 | 585.4 [487.6, 683.2] | 0.209 | `{'hidden_layer_sizes': (80,), 'alpha': 0.3, 'learning_rate_init': 0.0001}` |
| lenient | 4.0 | C1_Combined | Lasso | 71 | 46 | 0.418 | 0.311 [0.089, 0.533] | 0.596 | 17.47 | 502.1 [274.1, 730.0] | 0.107 | `{'alpha': 0.01}` |
| lenient | 4.0 | C1_Combined | ElasticNet | 71 | 46 | 0.460 | 0.240 [0.049, 0.431] | 0.607 | 19.69 | 596.5 [471.2, 721.8] | 0.220 | `{'alpha': 0.1, 'l1_ratio': 0.9}` |
| lenient | 4.0 | C1_Combined | Ridge | 71 | 46 | 0.418 | 0.311 [0.089, 0.533] | 0.595 | 17.48 | 502.1 [274.4, 729.9] | 0.107 | `{'alpha': 0.1}` |
| lenient | 4.5 | A1_Biomechanical_Core | SVM | 71 | 46 | 0.351 | 0.209 [0.076, 0.341] | 0.510 | 19.63 | 633.9 [498.9, 768.9] | 0.143 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 4.5 | A1_Biomechanical_Core | Random_Forest | 71 | 46 | 0.838 | 0.224 [-0.301, 0.749] | 0.585 | 18.68 | 521.2 [336.4, 705.9] | 0.614 | `{'n_estimators': 300, 'max_depth': 5, 'min_samples_split': 2, 'min_samples_leaf': 2}` |
| lenient | 4.5 | A1_Biomechanical_Core | XGBoost | 71 | 46 | 0.442 | 0.216 [0.057, 0.375] | 0.533 | 20.89 | 596.8 [376.8, 816.8] | 0.226 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 30, 'reg_alpha': 1.0, 'reg_lambda': 0.1}` |
| lenient | 4.5 | A1_Biomechanical_Core | Neural_Network | 71 | 46 | 0.315 | 0.237 [0.102, 0.372] | 0.582 | 20.57 | 558.7 [331.6, 785.8] | 0.078 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.3, 'learning_rate_init': 0.001}` |
| lenient | 4.5 | A1_Biomechanical_Core | Lasso | 71 | 46 | 0.404 | 0.276 [0.136, 0.416] | 0.581 | 19.57 | 525.1 [374.4, 675.8] | 0.128 | `{'alpha': 0.01}` |
| lenient | 4.5 | A1_Biomechanical_Core | ElasticNet | 71 | 46 | 0.410 | 0.259 [-0.006, 0.523] | 0.573 | 18.95 | 549.9 [300.1, 799.7] | 0.151 | `{'alpha': 1.0, 'l1_ratio': 0.7}` |
| lenient | 4.5 | A1_Biomechanical_Core | Ridge | 71 | 46 | 0.404 | 0.276 [0.136, 0.416] | 0.581 | 19.57 | 525.1 [374.4, 675.7] | 0.128 | `{'alpha': 0.1}` |
| lenient | 4.5 | A2_Biomechanical_NoK | SVM | 71 | 46 | 0.403 | 0.125 [-0.017, 0.268] | 0.431 | 20.28 | 673.7 [485.7, 861.7] | 0.278 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 4.5 | A2_Biomechanical_NoK | Random_Forest | 71 | 46 | 0.854 | 0.231 [-0.056, 0.518] | 0.548 | 20.14 | 531.9 [371.0, 692.8] | 0.623 | `{'n_estimators': 300, 'max_depth': 5, 'min_samples_split': 2, 'min_samples_leaf': 2}` |
| lenient | 4.5 | A2_Biomechanical_NoK | XGBoost | 71 | 46 | 0.461 | 0.181 [-0.024, 0.385] | 0.489 | 20.96 | 607.5 [389.7, 825.3] | 0.281 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 30, 'reg_alpha': 1.0, 'reg_lambda': 0.1}` |
| lenient | 4.5 | A2_Biomechanical_NoK | Neural_Network | 71 | 46 | 0.338 | 0.301 [0.194, 0.409] | 0.620 | 18.65 | 511.3 [396.7, 625.9] | 0.036 | `{'hidden_layer_sizes': (100,), 'alpha': 0.5, 'learning_rate_init': 0.0001}` |
| lenient | 4.5 | A2_Biomechanical_NoK | Lasso | 71 | 46 | 0.459 | 0.218 [0.063, 0.374] | 0.525 | 20.40 | 546.5 [382.7, 710.3] | 0.240 | `{'alpha': 0.01}` |
| lenient | 4.5 | A2_Biomechanical_NoK | ElasticNet | 71 | 46 | 0.432 | 0.168 [-0.037, 0.374] | 0.532 | 20.94 | 646.4 [510.6, 782.2] | 0.264 | `{'alpha': 0.1, 'l1_ratio': 0.9}` |
| lenient | 4.5 | A2_Biomechanical_NoK | Ridge | 71 | 46 | 0.459 | 0.218 [0.063, 0.373] | 0.525 | 20.40 | 546.6 [382.8, 710.3] | 0.241 | `{'alpha': 0.1}` |
| lenient | 4.5 | B_Clinical | SVM | 71 | 46 | 0.196 | 0.159 [0.064, 0.253] | 0.541 | 21.02 | 665.5 [468.8, 862.3] | 0.038 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 4.5 | B_Clinical | Random_Forest | 71 | 46 | 0.740 | 0.053 [-0.298, 0.404] | 0.475 | 23.66 | 674.8 [568.2, 781.3] | 0.687 | `{'n_estimators': 300, 'max_depth': None, 'min_samples_split': 2, 'min_samples_leaf': 2}` |
| lenient | 4.5 | B_Clinical | XGBoost | 71 | 46 | 0.552 | 0.154 [-0.156, 0.463] | 0.588 | 22.76 | 650.5 [491.7, 809.2] | 0.398 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 50, 'reg_alpha': 2.0, 'reg_lambda': 0.1}` |
| lenient | 4.5 | B_Clinical | Neural_Network | 71 | 46 | 0.358 | 0.274 [0.110, 0.439] | 0.675 | 20.32 | 547.3 [310.0, 784.6] | 0.083 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.3, 'learning_rate_init': 0.001}` |
| lenient | 4.5 | B_Clinical | Lasso | 71 | 46 | 0.317 | 0.234 [0.129, 0.340] | 0.562 | 23.27 | 635.7 [438.7, 832.6] | 0.083 | `{'alpha': 1.0}` |
| lenient | 4.5 | B_Clinical | ElasticNet | 71 | 46 | 0.317 | 0.234 [0.130, 0.339] | 0.562 | 23.27 | 635.7 [439.3, 832.0] | 0.083 | `{'alpha': 0.1, 'l1_ratio': 0.9}` |
| lenient | 4.5 | B_Clinical | Ridge | 71 | 46 | 0.309 | 0.231 [0.152, 0.311] | 0.560 | 23.24 | 636.1 [448.3, 823.9] | 0.077 | `{'alpha': 10.0}` |
| lenient | 4.5 | C1_Combined | SVM | 71 | 46 | 0.419 | 0.290 [0.102, 0.479] | 0.649 | 20.23 | 594.1 [483.3, 705.0] | 0.129 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 4.5 | C1_Combined | Random_Forest | 71 | 46 | 0.828 | 0.180 [-0.357, 0.717] | 0.558 | 19.40 | 535.7 [366.8, 704.6] | 0.648 | `{'n_estimators': 300, 'max_depth': 5, 'min_samples_split': 2, 'min_samples_leaf': 2}` |
| lenient | 4.5 | C1_Combined | XGBoost | 71 | 46 | 0.457 | 0.197 [0.002, 0.392] | 0.519 | 21.09 | 600.7 [385.0, 816.3] | 0.259 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 30, 'reg_alpha': 1.0, 'reg_lambda': 0.1}` |
| lenient | 4.5 | C1_Combined | Neural_Network | 71 | 46 | 0.445 | 0.269 [0.061, 0.476] | 0.545 | 20.07 | 605.1 [468.9, 741.3] | 0.176 | `{'hidden_layer_sizes': (80,), 'alpha': 0.3, 'learning_rate_init': 0.0001}` |
| lenient | 4.5 | C1_Combined | Lasso | 71 | 46 | 0.449 | 0.223 [-0.197, 0.643] | 0.616 | 21.32 | 601.2 [503.3, 699.2] | 0.225 | `{'alpha': 10.0}` |
| lenient | 4.5 | C1_Combined | ElasticNet | 71 | 46 | 0.448 | 0.238 [-0.045, 0.521] | 0.637 | 19.51 | 554.5 [323.9, 785.2] | 0.210 | `{'alpha': 1.0, 'l1_ratio': 0.7}` |
| lenient | 4.5 | C1_Combined | Ridge | 71 | 46 | 0.301 | 0.234 [0.150, 0.317] | 0.615 | 22.40 | 632.0 [461.7, 802.3] | 0.067 | `{'alpha': 100.0}` |
| lenient | 5.0 | A1_Biomechanical_Core | SVM | 71 | 46 | 0.339 | 0.170 [0.068, 0.272] | 0.590 | 22.40 | 699.4 [500.0, 898.7] | 0.169 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 5.0 | A1_Biomechanical_Core | Random_Forest | 71 | 46 | 0.702 | 0.286 [0.082, 0.489] | 0.630 | 20.64 | 630.9 [462.7, 799.1] | 0.416 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 5.0 | A1_Biomechanical_Core | XGBoost | 71 | 46 | 0.536 | 0.255 [0.047, 0.464] | 0.660 | 18.53 | 539.5 [317.5, 761.6] | 0.281 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 30, 'reg_alpha': 1.0, 'reg_lambda': 0.1}` |
| lenient | 5.0 | A1_Biomechanical_Core | Neural_Network | 71 | 46 | 0.388 | 0.261 [0.079, 0.443] | 0.608 | 20.51 | 582.0 [351.5, 812.6] | 0.127 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.3, 'learning_rate_init': 0.001}` |
| lenient | 5.0 | A1_Biomechanical_Core | Lasso | 71 | 46 | 0.487 | 0.329 [-0.055, 0.713] | 0.623 | 19.23 | 551.8 [293.3, 810.4] | 0.158 | `{'alpha': 1.0}` |
| lenient | 5.0 | A1_Biomechanical_Core | ElasticNet | 71 | 46 | 0.463 | 0.298 [-0.017, 0.613] | 0.610 | 19.14 | 562.8 [308.5, 817.2] | 0.165 | `{'alpha': 1.0, 'l1_ratio': 0.7}` |
| lenient | 5.0 | A1_Biomechanical_Core | Ridge | 71 | 46 | 0.477 | 0.318 [-0.017, 0.653] | 0.615 | 19.16 | 555.9 [300.7, 811.2] | 0.159 | `{'alpha': 10.0}` |
| lenient | 5.0 | A2_Biomechanical_NoK | SVM | 71 | 46 | 0.259 | 0.175 [0.102, 0.249] | 0.562 | 21.80 | 669.9 [586.4, 753.3] | 0.084 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 5.0 | A2_Biomechanical_NoK | Random_Forest | 71 | 46 | 0.741 | 0.410 [0.310, 0.511] | 0.716 | 18.30 | 578.4 [431.0, 725.9] | 0.331 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 5.0 | A2_Biomechanical_NoK | XGBoost | 71 | 46 | 0.715 | 0.324 [0.044, 0.604] | 0.621 | 20.99 | 620.1 [383.9, 856.3] | 0.391 | `{'learning_rate': 0.05, 'max_depth': 2, 'n_estimators': 50, 'reg_alpha': 0.5, 'reg_lambda': 2.0}` |
| lenient | 5.0 | A2_Biomechanical_NoK | Neural_Network | 71 | 46 | 0.352 | 0.278 [0.162, 0.394] | 0.574 | 19.14 | 563.1 [370.3, 756.0] | 0.074 | `{'hidden_layer_sizes': (100,), 'alpha': 0.5, 'learning_rate_init': 0.0001}` |
| lenient | 5.0 | A2_Biomechanical_NoK | Lasso | 71 | 46 | 0.514 | 0.176 [-0.360, 0.712] | 0.541 | 20.45 | 611.4 [282.1, 940.8] | 0.338 | `{'alpha': 1.0}` |
| lenient | 5.0 | A2_Biomechanical_NoK | ElasticNet | 71 | 46 | 0.490 | 0.184 [-0.214, 0.581] | 0.532 | 19.77 | 607.5 [312.6, 902.5] | 0.306 | `{'alpha': 1.0, 'l1_ratio': 0.7}` |
| lenient | 5.0 | A2_Biomechanical_NoK | Ridge | 71 | 46 | 0.361 | 0.214 [-0.008, 0.436] | 0.547 | 24.06 | 651.9 [523.2, 780.5] | 0.147 | `{'alpha': 10.0}` |
| lenient | 5.0 | B_Clinical | SVM | 71 | 46 | 0.521 | 0.272 [0.087, 0.457] | 0.628 | 21.64 | 640.9 [450.3, 831.6] | 0.248 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.03}` |
| lenient | 5.0 | B_Clinical | Random_Forest | 71 | 46 | 0.719 | 0.305 [0.118, 0.491] | 0.603 | 20.31 | 627.4 [440.7, 814.0] | 0.414 | `{'n_estimators': 50, 'max_depth': 3, 'min_samples_split': 5, 'min_samples_leaf': 2}` |
| lenient | 5.0 | B_Clinical | XGBoost | 71 | 46 | 0.604 | 0.347 [0.126, 0.568] | 0.648 | 21.88 | 608.1 [435.2, 781.0] | 0.258 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 50, 'reg_alpha': 2.0, 'reg_lambda': 0.1}` |
| lenient | 5.0 | B_Clinical | Neural_Network | 71 | 46 | 0.539 | 0.279 [-0.008, 0.565] | 0.652 | 22.09 | 626.7 [447.7, 805.8] | 0.260 | `{'hidden_layer_sizes': (80,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| lenient | 5.0 | B_Clinical | Lasso | 71 | 46 | 0.377 | 0.299 [0.079, 0.520] | 0.641 | 23.92 | 617.1 [461.3, 772.9] | 0.077 | `{'alpha': 1.0}` |
| lenient | 5.0 | B_Clinical | ElasticNet | 71 | 46 | 0.377 | 0.300 [0.084, 0.517] | 0.641 | 23.91 | 616.8 [463.0, 770.6] | 0.076 | `{'alpha': 0.1, 'l1_ratio': 0.9}` |
| lenient | 5.0 | B_Clinical | Ridge | 71 | 46 | 0.368 | 0.303 [0.150, 0.455] | 0.636 | 23.92 | 616.2 [493.6, 738.7] | 0.065 | `{'alpha': 10.0}` |
| lenient | 5.0 | C1_Combined | SVM | 71 | 46 | 0.465 | 0.310 [0.137, 0.483] | 0.673 | 21.69 | 622.1 [495.5, 748.6] | 0.156 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 5.0 | C1_Combined | Random_Forest | 71 | 46 | 0.849 | 0.278 [-0.045, 0.602] | 0.604 | 20.51 | 630.1 [432.6, 827.7] | 0.571 | `{'n_estimators': 300, 'max_depth': None, 'min_samples_split': 2, 'min_samples_leaf': 2}` |
| lenient | 5.0 | C1_Combined | XGBoost | 71 | 46 | 0.624 | 0.339 [0.076, 0.602] | 0.655 | 21.29 | 606.0 [429.1, 782.9] | 0.285 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 50, 'reg_alpha': 2.0, 'reg_lambda': 0.1}` |
| lenient | 5.0 | C1_Combined | Neural_Network | 71 | 46 | 0.547 | 0.381 [0.298, 0.464] | 0.638 | 19.94 | 597.6 [454.0, 741.2] | 0.166 | `{'hidden_layer_sizes': (80,), 'alpha': 0.3, 'learning_rate_init': 0.0001}` |
| lenient | 5.0 | C1_Combined | Lasso | 71 | 46 | 0.482 | 0.303 [-0.076, 0.682] | 0.627 | 20.98 | 596.2 [467.7, 724.7] | 0.178 | `{'alpha': 10.0}` |
| lenient | 5.0 | C1_Combined | ElasticNet | 71 | 46 | 0.500 | 0.302 [-0.013, 0.617] | 0.665 | 19.55 | 562.8 [323.0, 802.6] | 0.198 | `{'alpha': 1.0, 'l1_ratio': 0.7}` |
| lenient | 5.0 | C1_Combined | Ridge | 71 | 46 | 0.392 | 0.308 [0.105, 0.511] | 0.617 | 23.24 | 612.2 [479.2, 745.2] | 0.084 | `{'alpha': 10.0}` |
| lenient | 5.5 | A1_Biomechanical_Core | SVM | 71 | 46 | 0.354 | 0.237 [0.111, 0.363] | 0.646 | 23.59 | 739.4 [526.1, 952.6] | 0.117 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 5.5 | A1_Biomechanical_Core | Random_Forest | 71 | 46 | 0.731 | 0.270 [-0.019, 0.560] | 0.648 | 21.75 | 632.9 [489.0, 776.7] | 0.461 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 5.5 | A1_Biomechanical_Core | XGBoost | 71 | 46 | 0.824 | 0.234 [-0.044, 0.513] | 0.506 | 22.66 | 648.3 [429.1, 867.5] | 0.590 | `{'learning_rate': 0.05, 'max_depth': 2, 'n_estimators': 100, 'reg_alpha': 2.0, 'reg_lambda': 1.0}` |
| lenient | 5.5 | A1_Biomechanical_Core | Neural_Network | 71 | 46 | 0.460 | 0.212 [-0.022, 0.445] | 0.557 | 22.79 | 588.8 [389.3, 788.4] | 0.249 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.5, 'learning_rate_init': 0.0005}` |
| lenient | 5.5 | A1_Biomechanical_Core | Lasso | 71 | 46 | 0.494 | 0.283 [-0.224, 0.791] | 0.623 | 22.28 | 614.9 [393.6, 836.1] | 0.211 | `{'alpha': 1.0}` |
| lenient | 5.5 | A1_Biomechanical_Core | ElasticNet | 71 | 46 | 0.469 | 0.278 [-0.125, 0.681] | 0.612 | 22.81 | 627.3 [401.7, 852.9] | 0.191 | `{'alpha': 1.0, 'l1_ratio': 0.7}` |
| lenient | 5.5 | A1_Biomechanical_Core | Ridge | 71 | 46 | 0.484 | 0.288 [-0.150, 0.726] | 0.617 | 22.62 | 619.3 [395.5, 843.2] | 0.196 | `{'alpha': 10.0}` |
| lenient | 5.5 | A2_Biomechanical_NoK | SVM | 71 | 46 | 0.222 | 0.171 [0.082, 0.259] | 0.577 | 22.08 | 696.9 [589.8, 804.0] | 0.051 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 5.5 | A2_Biomechanical_NoK | Random_Forest | 71 | 46 | 0.764 | 0.368 [0.168, 0.567] | 0.724 | 19.68 | 593.5 [483.7, 703.3] | 0.397 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 5.5 | A2_Biomechanical_NoK | XGBoost | 71 | 46 | 0.743 | 0.272 [0.038, 0.505] | 0.582 | 24.85 | 723.9 [431.4, 1016.3] | 0.471 | `{'learning_rate': 0.05, 'max_depth': 2, 'n_estimators': 50, 'reg_alpha': 0.5, 'reg_lambda': 2.0}` |
| lenient | 5.5 | A2_Biomechanical_NoK | Neural_Network | 71 | 46 | 0.397 | 0.257 [0.108, 0.406] | 0.576 | 22.14 | 641.8 [495.3, 788.2] | 0.141 | `{'hidden_layer_sizes': (100,), 'alpha': 0.5, 'learning_rate_init': 0.0001}` |
| lenient | 5.5 | A2_Biomechanical_NoK | Lasso | 71 | 46 | 0.374 | 0.186 [-0.023, 0.396] | 0.537 | 26.68 | 688.6 [544.0, 833.1] | 0.188 | `{'alpha': 1.0}` |
| lenient | 5.5 | A2_Biomechanical_NoK | ElasticNet | 71 | 46 | 0.482 | 0.205 [-0.273, 0.683] | 0.569 | 23.30 | 657.9 [393.0, 922.7] | 0.277 | `{'alpha': 1.0, 'l1_ratio': 0.7}` |
| lenient | 5.5 | A2_Biomechanical_NoK | Ridge | 71 | 46 | 0.365 | 0.217 [0.053, 0.381] | 0.536 | 26.26 | 676.7 [545.4, 808.0] | 0.148 | `{'alpha': 10.0}` |
| lenient | 5.5 | B_Clinical | SVM | 71 | 46 | 0.518 | 0.326 [0.129, 0.523] | 0.653 | 23.32 | 691.4 [453.1, 929.7] | 0.193 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.03}` |
| lenient | 5.5 | B_Clinical | Random_Forest | 71 | 46 | 0.845 | 0.282 [0.046, 0.518] | 0.568 | 26.22 | 698.1 [540.4, 855.8] | 0.562 | `{'n_estimators': 300, 'max_depth': None, 'min_samples_split': 2, 'min_samples_leaf': 2}` |
| lenient | 5.5 | B_Clinical | XGBoost | 71 | 46 | 0.640 | 0.369 [0.165, 0.572] | 0.632 | 25.84 | 655.5 [478.3, 832.7] | 0.272 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 50, 'reg_alpha': 2.0, 'reg_lambda': 0.1}` |
| lenient | 5.5 | B_Clinical | Neural_Network | 71 | 46 | 0.553 | 0.316 [0.069, 0.564] | 0.658 | 25.35 | 693.5 [450.0, 937.0] | 0.237 | `{'hidden_layer_sizes': (80,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| lenient | 5.5 | B_Clinical | Lasso | 71 | 46 | 0.384 | 0.248 [-0.098, 0.594] | 0.644 | 26.04 | 660.0 [460.7, 859.3] | 0.136 | `{'alpha': 1.0}` |
| lenient | 5.5 | B_Clinical | ElasticNet | 71 | 46 | 0.384 | 0.249 [-0.089, 0.588] | 0.643 | 26.04 | 659.6 [462.7, 856.6] | 0.134 | `{'alpha': 0.1, 'l1_ratio': 0.9}` |
| lenient | 5.5 | B_Clinical | Ridge | 71 | 46 | 0.374 | 0.269 [0.031, 0.507] | 0.636 | 25.90 | 654.6 [488.7, 820.5] | 0.106 | `{'alpha': 10.0}` |
| lenient | 5.5 | C1_Combined | SVM | 71 | 46 | 0.475 | 0.300 [-0.037, 0.637] | 0.687 | 22.93 | 674.7 [545.3, 804.2] | 0.175 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 5.5 | C1_Combined | Random_Forest | 71 | 46 | 0.886 | 0.311 [0.011, 0.611] | 0.591 | 26.20 | 680.6 [489.6, 871.6] | 0.575 | `{'n_estimators': 300, 'max_depth': None, 'min_samples_split': 2, 'min_samples_leaf': 2}` |
| lenient | 5.5 | C1_Combined | XGBoost | 71 | 46 | 0.669 | 0.384 [0.146, 0.621] | 0.655 | 25.10 | 646.1 [450.3, 842.0] | 0.285 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 50, 'reg_alpha': 2.0, 'reg_lambda': 0.1}` |
| lenient | 5.5 | C1_Combined | Neural_Network | 71 | 46 | 0.578 | 0.358 [0.179, 0.537] | 0.633 | 23.87 | 662.5 [521.1, 803.9] | 0.220 | `{'hidden_layer_sizes': (80,), 'alpha': 0.3, 'learning_rate_init': 0.0001}` |
| lenient | 5.5 | C1_Combined | Lasso | 71 | 46 | 0.488 | 0.303 [0.095, 0.511] | 0.670 | 25.23 | 696.5 [468.1, 925.0] | 0.185 | `{'alpha': 10.0}` |
| lenient | 5.5 | C1_Combined | ElasticNet | 71 | 46 | 0.488 | 0.300 [0.100, 0.501] | 0.665 | 25.36 | 697.9 [470.4, 925.5] | 0.187 | `{'alpha': 0.1, 'l1_ratio': 0.5}` |
| lenient | 5.5 | C1_Combined | Ridge | 71 | 46 | 0.401 | 0.286 [0.075, 0.497] | 0.611 | 25.52 | 647.2 [486.5, 807.9] | 0.115 | `{'alpha': 10.0}` |
| lenient | 6.0 | A1_Biomechanical_Core | SVM | 71 | 46 | 0.424 | 0.269 [-0.092, 0.630] | 0.612 | 28.24 | 684.6 [534.0, 835.2] | 0.155 | `{'C': 5000, 'epsilon': 800, 'gamma': 0.01}` |
| lenient | 6.0 | A1_Biomechanical_Core | Random_Forest | 71 | 46 | 0.721 | 0.335 [0.146, 0.524] | 0.640 | 24.67 | 676.9 [467.3, 886.6] | 0.386 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 6.0 | A1_Biomechanical_Core | XGBoost | 71 | 46 | 0.559 | 0.345 [0.096, 0.594] | 0.660 | 21.69 | 560.8 [312.2, 809.4] | 0.214 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 30, 'reg_alpha': 1.0, 'reg_lambda': 0.1}` |
| lenient | 6.0 | A1_Biomechanical_Core | Neural_Network | 71 | 46 | 0.438 | 0.256 [0.052, 0.460] | 0.563 | 24.49 | 691.7 [551.1, 832.3] | 0.182 | `{'hidden_layer_sizes': (80,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| lenient | 6.0 | A1_Biomechanical_Core | Lasso | 71 | 46 | 0.462 | 0.284 [0.069, 0.499] | 0.603 | 26.45 | 693.4 [512.2, 874.7] | 0.178 | `{'alpha': 10.0}` |
| lenient | 6.0 | A1_Biomechanical_Core | ElasticNet | 71 | 46 | 0.462 | 0.271 [0.050, 0.492] | 0.594 | 26.73 | 699.4 [516.5, 882.3] | 0.191 | `{'alpha': 0.001, 'l1_ratio': 0.3}` |
| lenient | 6.0 | A1_Biomechanical_Core | Ridge | 71 | 46 | 0.453 | 0.228 [-0.186, 0.642] | 0.560 | 23.69 | 652.3 [437.2, 867.4] | 0.226 | `{'alpha': 10.0}` |
| lenient | 6.0 | A2_Biomechanical_NoK | SVM | 71 | 46 | 0.434 | 0.261 [-0.097, 0.619] | 0.601 | 27.90 | 688.2 [534.2, 842.2] | 0.172 | `{'C': 5000, 'epsilon': 800, 'gamma': 0.01}` |
| lenient | 6.0 | A2_Biomechanical_NoK | Random_Forest | 71 | 46 | 0.760 | 0.377 [0.194, 0.560] | 0.682 | 22.43 | 646.0 [478.6, 813.4] | 0.383 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 6.0 | A2_Biomechanical_NoK | XGBoost | 71 | 46 | 0.569 | 0.332 [0.078, 0.586] | 0.654 | 21.83 | 565.5 [317.0, 814.0] | 0.237 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 30, 'reg_alpha': 1.0, 'reg_lambda': 0.1}` |
| lenient | 6.0 | A2_Biomechanical_NoK | Neural_Network | 71 | 46 | 0.368 | 0.221 [0.019, 0.423] | 0.605 | 25.07 | 636.0 [444.0, 828.0] | 0.148 | `{'hidden_layer_sizes': (100,), 'alpha': 0.5, 'learning_rate_init': 0.0001}` |
| lenient | 6.0 | A2_Biomechanical_NoK | Lasso | 71 | 46 | 0.489 | 0.263 [0.055, 0.471] | 0.582 | 26.30 | 707.0 [499.6, 914.4] | 0.226 | `{'alpha': 10.0}` |
| lenient | 6.0 | A2_Biomechanical_NoK | ElasticNet | 71 | 46 | 0.490 | 0.233 [0.010, 0.456] | 0.557 | 26.68 | 722.3 [499.4, 945.3] | 0.257 | `{'alpha': 0.001, 'l1_ratio': 0.3}` |
| lenient | 6.0 | A2_Biomechanical_NoK | Ridge | 71 | 46 | 0.259 | 0.149 [-0.021, 0.318] | 0.528 | 27.55 | 737.5 [625.6, 849.5] | 0.110 | `{'alpha': 100.0}` |
| lenient | 6.0 | B_Clinical | SVM | 71 | 46 | 0.476 | 0.312 [0.128, 0.496] | 0.586 | 23.83 | 667.4 [519.2, 815.6] | 0.164 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.03}` |
| lenient | 6.0 | B_Clinical | Random_Forest | 71 | 46 | 0.645 | 0.226 [-0.026, 0.479] | 0.498 | 25.02 | 708.9 [519.7, 898.1] | 0.418 | `{'n_estimators': 50, 'max_depth': 3, 'min_samples_split': 5, 'min_samples_leaf': 2}` |
| lenient | 6.0 | B_Clinical | XGBoost | 71 | 46 | 0.624 | 0.196 [-0.042, 0.433] | 0.464 | 24.80 | 722.3 [549.8, 894.7] | 0.428 | `{'learning_rate': 0.05, 'max_depth': 2, 'n_estimators': 50, 'reg_alpha': 0.5, 'reg_lambda': 2.0}` |
| lenient | 6.0 | B_Clinical | Neural_Network | 71 | 46 | 0.502 | 0.281 [-0.002, 0.564] | 0.585 | 25.06 | 678.5 [497.4, 859.6] | 0.221 | `{'hidden_layer_sizes': (80,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| lenient | 6.0 | B_Clinical | Lasso | 71 | 46 | 0.331 | 0.197 [-0.046, 0.440] | 0.584 | 28.76 | 713.8 [550.1, 877.5] | 0.135 | `{'alpha': 1.0}` |
| lenient | 6.0 | B_Clinical | ElasticNet | 71 | 46 | 0.331 | 0.198 [-0.040, 0.437] | 0.584 | 28.74 | 713.3 [551.6, 875.1] | 0.133 | `{'alpha': 0.1, 'l1_ratio': 0.9}` |
| lenient | 6.0 | B_Clinical | Ridge | 71 | 46 | 0.324 | 0.208 [0.039, 0.377] | 0.580 | 28.64 | 710.4 [578.9, 841.9] | 0.115 | `{'alpha': 10.0}` |
| lenient | 6.0 | C1_Combined | SVM | 71 | 46 | 0.539 | 0.318 [0.088, 0.547] | 0.608 | 23.18 | 662.7 [502.8, 822.6] | 0.221 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.03}` |
| lenient | 6.0 | C1_Combined | Random_Forest | 71 | 46 | 0.738 | 0.258 [0.013, 0.503] | 0.606 | 25.82 | 704.1 [511.9, 896.4] | 0.481 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 6.0 | C1_Combined | XGBoost | 71 | 46 | 0.568 | 0.244 [0.044, 0.444] | 0.586 | 22.56 | 597.1 [387.4, 806.7] | 0.324 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 30, 'reg_alpha': 1.0, 'reg_lambda': 0.1}` |
| lenient | 6.0 | C1_Combined | Neural_Network | 71 | 46 | 0.502 | 0.352 [0.111, 0.592] | 0.638 | 24.31 | 642.2 [493.0, 791.5] | 0.150 | `{'hidden_layer_sizes': (80,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| lenient | 6.0 | C1_Combined | Lasso | 71 | 46 | 0.499 | 0.327 [0.081, 0.572] | 0.637 | 25.60 | 662.5 [523.5, 801.5] | 0.172 | `{'alpha': 10.0}` |
| lenient | 6.0 | C1_Combined | ElasticNet | 71 | 46 | 0.500 | 0.314 [0.058, 0.570] | 0.630 | 25.92 | 667.8 [529.7, 806.0] | 0.185 | `{'alpha': 0.001, 'l1_ratio': 0.3}` |
| lenient | 6.0 | C1_Combined | Ridge | 71 | 46 | 0.305 | 0.242 [0.133, 0.351] | 0.614 | 26.24 | 698.1 [599.3, 796.9] | 0.063 | `{'alpha': 100.0}` |
| strict | 1.0 | A1_Biomechanical_Core_K | SVM | 69 | 44 | 0.470 | 0.319 [0.011, 0.627] | 0.645 | 11.31 | 505.1 [339.9, 670.3] | 0.151 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 1.0 | A1_Biomechanical_Core_K | Random_Forest | 69 | 44 | 0.842 | 0.400 [0.126, 0.673] | 0.666 | 9.34 | 420.4 [315.4, 525.4] | 0.443 | `{'n_estimators': 300, 'max_depth': 5, 'min_samples_split': 2, 'min_samples_leaf': 2}` |
| strict | 1.0 | A1_Biomechanical_Core_K | XGBoost | 69 | 44 | 0.604 | 0.416 [0.279, 0.553] | 0.688 | 10.67 | 469.8 [370.8, 568.7] | 0.188 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 50, 'reg_alpha': 2.0, 'reg_lambda': 0.1}` |
| strict | 1.0 | A1_Biomechanical_Core_K | Neural_Network | 69 | 44 | 0.589 | 0.365 [0.295, 0.436] | 0.664 | 11.56 | 540.6 [331.1, 750.2] | 0.224 | `{'hidden_layer_sizes': (60,), 'alpha': 1.0, 'learning_rate_init': 0.0005}` |
| strict | 1.0 | A1_Biomechanical_Core_K | Lasso | 69 | 44 | 0.568 | 0.502 [0.222, 0.783] | 0.716 | 8.32 | 386.4 [252.8, 520.1] | 0.066 | `{'alpha': 0.01}` |
| strict | 1.0 | A1_Biomechanical_Core_K | ElasticNet | 69 | 44 | 0.579 | 0.432 [0.205, 0.659] | 0.686 | 10.52 | 491.9 [331.2, 652.5] | 0.147 | `{'alpha': 0.001, 'l1_ratio': 0.3}` |
| strict | 1.0 | A1_Biomechanical_Core_K | Ridge | 69 | 44 | 0.568 | 0.502 [0.221, 0.783] | 0.716 | 8.32 | 386.4 [252.6, 520.2] | 0.066 | `{'alpha': 0.1}` |
| strict | 1.0 | A2_Biomechanical_WithK | SVM | 69 | 44 | 0.391 | 0.301 [0.089, 0.514] | 0.659 | 10.13 | 467.5 [316.5, 618.6] | 0.090 | `{'C': 500, 'epsilon': 800, 'gamma': 0.1}` |
| strict | 1.0 | A2_Biomechanical_WithK | Random_Forest | 69 | 44 | 0.825 | 0.390 [0.195, 0.585] | 0.659 | 9.81 | 442.3 [317.3, 567.3] | 0.434 | `{'n_estimators': 100, 'max_depth': 3, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| strict | 1.0 | A2_Biomechanical_WithK | XGBoost | 69 | 44 | 0.832 | 0.389 [0.051, 0.727] | 0.646 | 9.77 | 425.6 [283.7, 567.6] | 0.442 | `{'learning_rate': 0.05, 'max_depth': 2, 'n_estimators': 100, 'reg_alpha': 2.0, 'reg_lambda': 1.0}` |
| strict | 1.0 | A2_Biomechanical_WithK | Neural_Network | 69 | 44 | 0.615 | 0.402 [0.162, 0.641] | 0.649 | 9.45 | 431.3 [279.0, 583.6] | 0.214 | `{'hidden_layer_sizes': (100,), 'alpha': 0.5, 'learning_rate_init': 0.0001}` |
| strict | 1.0 | A2_Biomechanical_WithK | Lasso | 69 | 44 | 0.571 | 0.485 [0.199, 0.772] | 0.712 | 8.56 | 392.4 [263.5, 521.2] | 0.086 | `{'alpha': 0.01}` |
| strict | 1.0 | A2_Biomechanical_WithK | ElasticNet | 69 | 44 | 0.590 | 0.426 [0.159, 0.692] | 0.678 | 10.35 | 490.6 [327.7, 653.6] | 0.164 | `{'alpha': 0.001, 'l1_ratio': 0.3}` |
| strict | 1.0 | A2_Biomechanical_WithK | Ridge | 69 | 44 | 0.571 | 0.486 [0.199, 0.773] | 0.712 | 8.56 | 392.3 [263.2, 521.4] | 0.085 | `{'alpha': 0.1}` |
| strict | 1.0 | B_Clinical_K | SVM | 69 | 44 | 0.389 | 0.299 [0.111, 0.487] | 0.671 | 10.01 | 466.5 [337.0, 595.9] | 0.091 | `{'C': 500, 'epsilon': 800, 'gamma': 0.1}` |
| strict | 1.0 | B_Clinical_K | Random_Forest | 69 | 44 | 0.842 | 0.287 [0.131, 0.442] | 0.610 | 11.57 | 519.8 [409.1, 630.4] | 0.555 | `{'n_estimators': 300, 'max_depth': None, 'min_samples_split': 2, 'min_samples_leaf': 2}` |
| strict | 1.0 | B_Clinical_K | XGBoost | 69 | 44 | 0.539 | 0.306 [0.155, 0.458] | 0.625 | 11.51 | 511.7 [412.4, 611.0] | 0.232 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 50, 'reg_alpha': 2.0, 'reg_lambda': 0.1}` |
| strict | 1.0 | B_Clinical_K | Neural_Network | 69 | 44 | 0.398 | 0.206 [0.072, 0.340] | 0.502 | 12.00 | 547.6 [449.4, 645.7] | 0.192 | `{'hidden_layer_sizes': (80,), 'alpha': 0.3, 'learning_rate_init': 0.0001}` |
| strict | 1.0 | B_Clinical_K | Lasso | 69 | 44 | 0.598 | 0.308 [-0.218, 0.834] | 0.697 | 10.00 | 440.6 [290.3, 590.9] | 0.290 | `{'alpha': 1.0}` |
| strict | 1.0 | B_Clinical_K | ElasticNet | 69 | 44 | 0.521 | 0.270 [-0.206, 0.747] | 0.647 | 10.78 | 462.3 [308.6, 616.1] | 0.250 | `{'alpha': 1.0, 'l1_ratio': 0.7}` |
| strict | 1.0 | B_Clinical_K | Ridge | 69 | 44 | 0.552 | 0.293 [-0.208, 0.794] | 0.663 | 10.52 | 451.8 [300.3, 603.3] | 0.259 | `{'alpha': 10.0}` |
| strict | 1.0 | C1_Combined_K | SVM | 69 | 44 | 0.528 | 0.387 [0.122, 0.652] | 0.687 | 10.86 | 479.7 [326.3, 633.2] | 0.141 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 1.0 | C1_Combined_K | Random_Forest | 69 | 44 | 0.858 | 0.364 [0.086, 0.642] | 0.656 | 9.71 | 432.7 [331.0, 534.3] | 0.495 | `{'n_estimators': 300, 'max_depth': 5, 'min_samples_split': 2, 'min_samples_leaf': 2}` |
| strict | 1.0 | C1_Combined_K | XGBoost | 69 | 44 | 0.631 | 0.388 [0.301, 0.475] | 0.678 | 10.79 | 479.4 [411.4, 547.4] | 0.243 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 50, 'reg_alpha': 2.0, 'reg_lambda': 0.1}` |
| strict | 1.0 | C1_Combined_K | Neural_Network | 69 | 44 | 0.633 | 0.346 [0.014, 0.679] | 0.651 | 9.64 | 468.8 [395.4, 542.3] | 0.287 | `{'hidden_layer_sizes': (80, 40), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| strict | 1.0 | C1_Combined_K | Lasso | 69 | 44 | 0.571 | 0.444 [0.124, 0.765] | 0.697 | 8.93 | 407.1 [264.8, 549.5] | 0.127 | `{'alpha': 0.01}` |
| strict | 1.0 | C1_Combined_K | ElasticNet | 69 | 44 | 0.585 | 0.433 [0.196, 0.671] | 0.686 | 10.46 | 490.7 [326.4, 655.0] | 0.151 | `{'alpha': 0.001, 'l1_ratio': 0.3}` |
| strict | 1.0 | C1_Combined_K | Ridge | 69 | 44 | 0.571 | 0.444 [0.122, 0.765] | 0.697 | 8.94 | 407.2 [264.6, 549.8] | 0.128 | `{'alpha': 0.1}` |
| strict | 1.5 | A1_Biomechanical_Core_K | SVM | 69 | 44 | 0.426 | 0.407 [0.106, 0.708] | 0.687 | 9.39 | 434.3 [215.7, 652.8] | 0.019 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 1.5 | A1_Biomechanical_Core_K | Random_Forest | 69 | 44 | 0.741 | 0.459 [0.046, 0.872] | 0.731 | 8.44 | 414.2 [235.1, 593.3] | 0.281 | `{'n_estimators': 200, 'max_depth': 4, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| strict | 1.5 | A1_Biomechanical_Core_K | XGBoost | 69 | 44 | 0.623 | 0.439 [0.107, 0.771] | 0.690 | 9.47 | 407.7 [229.9, 585.4] | 0.184 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 50, 'reg_alpha': 2.0, 'reg_lambda': 0.1}` |
| strict | 1.5 | A1_Biomechanical_Core_K | Neural_Network | 69 | 44 | 0.705 | 0.388 [-0.028, 0.804] | 0.680 | 8.66 | 357.7 [303.2, 412.1] | 0.317 | `{'hidden_layer_sizes': (60,), 'alpha': 1.0, 'learning_rate_init': 0.001}` |
| strict | 1.5 | A1_Biomechanical_Core_K | Lasso | 69 | 44 | 0.651 | 0.505 [0.392, 0.618] | 0.742 | 8.14 | 340.7 [264.7, 416.6] | 0.146 | `{'alpha': 0.1}` |
| strict | 1.5 | A1_Biomechanical_Core_K | ElasticNet | 69 | 44 | 0.651 | 0.505 [0.391, 0.618] | 0.742 | 8.14 | 340.7 [264.7, 416.6] | 0.146 | `{'alpha': 0.001, 'l1_ratio': 0.1}` |
| strict | 1.5 | A1_Biomechanical_Core_K | Ridge | 69 | 44 | 0.651 | 0.508 [0.392, 0.623] | 0.741 | 8.12 | 339.8 [263.1, 416.4] | 0.143 | `{'alpha': 1.0}` |
| strict | 1.5 | A2_Biomechanical_WithK | SVM | 69 | 44 | 0.470 | 0.398 [0.056, 0.740] | 0.676 | 9.32 | 437.2 [207.0, 667.3] | 0.072 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 1.5 | A2_Biomechanical_WithK | Random_Forest | 69 | 44 | 0.755 | 0.445 [0.246, 0.645] | 0.763 | 8.43 | 419.3 [274.1, 564.4] | 0.310 | `{'n_estimators': 100, 'max_depth': 5, 'min_samples_split': 10, 'min_samples_leaf': 4}` |
| strict | 1.5 | A2_Biomechanical_WithK | XGBoost | 69 | 44 | 0.843 | 0.426 [0.220, 0.632] | 0.748 | 8.36 | 359.3 [295.4, 423.2] | 0.417 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 2.0}` |
| strict | 1.5 | A2_Biomechanical_WithK | Neural_Network | 69 | 44 | 0.647 | 0.407 [0.205, 0.610] | 0.677 | 9.82 | 445.1 [307.1, 583.2] | 0.240 | `{'hidden_layer_sizes': (60,), 'alpha': 0.3, 'learning_rate_init': 0.0005}` |
| strict | 1.5 | A2_Biomechanical_WithK | Lasso | 69 | 44 | 0.568 | 0.491 [0.209, 0.772] | 0.727 | 8.47 | 398.2 [196.3, 600.1] | 0.077 | `{'alpha': 1.0}` |
| strict | 1.5 | A2_Biomechanical_WithK | ElasticNet | 69 | 44 | 0.568 | 0.492 [0.209, 0.774] | 0.727 | 8.47 | 397.8 [195.0, 600.5] | 0.076 | `{'alpha': 0.1, 'l1_ratio': 0.9}` |
| strict | 1.5 | A2_Biomechanical_WithK | Ridge | 69 | 44 | 0.554 | 0.469 [0.137, 0.801] | 0.697 | 8.72 | 405.2 [180.6, 629.8] | 0.085 | `{'alpha': 10.0}` |
| strict | 1.5 | B_Clinical_K | SVM | 69 | 44 | 0.320 | 0.186 [-0.198, 0.570] | 0.492 | 12.16 | 500.4 [273.2, 727.7] | 0.134 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 1.5 | B_Clinical_K | Random_Forest | 69 | 44 | 0.838 | 0.307 [0.004, 0.610] | 0.679 | 8.41 | 369.0 [243.6, 494.4] | 0.531 | `{'n_estimators': 300, 'max_depth': 5, 'min_samples_split': 2, 'min_samples_leaf': 2}` |
| strict | 1.5 | B_Clinical_K | XGBoost | 69 | 44 | 0.510 | 0.284 [-0.016, 0.584] | 0.564 | 11.35 | 466.2 [285.4, 647.1] | 0.226 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 50, 'reg_alpha': 2.0, 'reg_lambda': 0.1}` |
| strict | 1.5 | B_Clinical_K | Neural_Network | 69 | 44 | 0.526 | 0.238 [-0.054, 0.529] | 0.542 | 9.45 | 400.5 [309.8, 491.2] | 0.289 | `{'hidden_layer_sizes': (60,), 'alpha': 0.5, 'learning_rate_init': 0.0001}` |
| strict | 1.5 | B_Clinical_K | Lasso | 69 | 44 | 0.473 | 0.273 [-0.112, 0.658] | 0.538 | 9.27 | 385.9 [273.4, 498.3] | 0.200 | `{'alpha': 1.0}` |
| strict | 1.5 | B_Clinical_K | ElasticNet | 69 | 44 | 0.430 | 0.240 [-0.093, 0.573] | 0.520 | 9.53 | 398.4 [295.8, 501.0] | 0.190 | `{'alpha': 1.0, 'l1_ratio': 0.7}` |
| strict | 1.5 | B_Clinical_K | Ridge | 69 | 44 | 0.450 | 0.259 [-0.088, 0.607] | 0.526 | 9.39 | 392.0 [287.5, 496.6] | 0.191 | `{'alpha': 10.0}` |
| strict | 1.5 | C1_Combined_K | SVM | 69 | 44 | 0.440 | 0.414 [0.081, 0.747] | 0.695 | 9.33 | 430.9 [201.9, 660.0] | 0.026 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 1.5 | C1_Combined_K | Random_Forest | 69 | 44 | 0.753 | 0.447 [0.155, 0.738] | 0.746 | 8.20 | 348.8 [271.0, 426.6] | 0.306 | `{'n_estimators': 50, 'max_depth': 2, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| strict | 1.5 | C1_Combined_K | XGBoost | 69 | 44 | 0.624 | 0.427 [0.094, 0.759] | 0.684 | 9.68 | 412.9 [235.2, 590.7] | 0.197 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 50, 'reg_alpha': 2.0, 'reg_lambda': 0.1}` |
| strict | 1.5 | C1_Combined_K | Neural_Network | 69 | 44 | 0.652 | 0.443 [0.033, 0.852] | 0.696 | 9.11 | 412.9 [172.9, 652.9] | 0.210 | `{'hidden_layer_sizes': (100,), 'alpha': 0.3, 'learning_rate_init': 0.0005}` |
| strict | 1.5 | C1_Combined_K | Lasso | 69 | 44 | 0.660 | 0.504 [0.401, 0.607] | 0.747 | 7.94 | 340.8 [270.5, 411.0] | 0.156 | `{'alpha': 0.1}` |
| strict | 1.5 | C1_Combined_K | ElasticNet | 69 | 44 | 0.660 | 0.504 [0.400, 0.608] | 0.747 | 7.94 | 340.6 [270.6, 410.6] | 0.156 | `{'alpha': 0.001, 'l1_ratio': 0.1}` |
| strict | 1.5 | C1_Combined_K | Ridge | 69 | 44 | 0.660 | 0.510 [0.403, 0.617] | 0.750 | 7.87 | 338.0 [270.4, 405.7] | 0.150 | `{'alpha': 1.0}` |
| strict | 2.0 | A1_Biomechanical_Core_K | SVM | 69 | 44 | 0.413 | 0.357 [0.075, 0.638] | 0.623 | 10.25 | 409.2 [216.2, 602.2] | 0.056 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 2.0 | A1_Biomechanical_Core_K | Random_Forest | 69 | 44 | 0.716 | 0.438 [0.159, 0.717] | 0.703 | 9.91 | 375.8 [205.1, 546.5] | 0.279 | `{'n_estimators': 200, 'max_depth': 4, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| strict | 2.0 | A1_Biomechanical_Core_K | XGBoost | 69 | 44 | 0.749 | 0.355 [0.190, 0.521] | 0.689 | 9.69 | 370.5 [240.2, 500.9] | 0.393 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 2.0}` |
| strict | 2.0 | A1_Biomechanical_Core_K | Neural_Network | 69 | 44 | 0.486 | 0.355 [0.153, 0.556] | 0.639 | 10.99 | 408.5 [233.1, 583.9] | 0.131 | `{'hidden_layer_sizes': (80,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| strict | 2.0 | A1_Biomechanical_Core_K | Lasso | 69 | 44 | 0.523 | 0.358 [0.129, 0.587] | 0.640 | 9.58 | 364.0 [234.1, 493.8] | 0.165 | `{'alpha': 0.1}` |
| strict | 2.0 | A1_Biomechanical_Core_K | ElasticNet | 69 | 44 | 0.523 | 0.358 [0.129, 0.587] | 0.640 | 9.58 | 363.9 [234.2, 493.7] | 0.165 | `{'alpha': 0.001, 'l1_ratio': 0.1}` |
| strict | 2.0 | A1_Biomechanical_Core_K | Ridge | 69 | 44 | 0.520 | 0.383 [0.202, 0.563] | 0.739 | 10.62 | 415.3 [305.0, 525.6] | 0.137 | `{'alpha': 10.0}` |
| strict | 2.0 | A2_Biomechanical_WithK | SVM | 69 | 44 | 0.464 | 0.351 [0.205, 0.497] | 0.741 | 10.32 | 423.8 [334.2, 513.4] | 0.112 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 2.0 | A2_Biomechanical_WithK | Random_Forest | 69 | 44 | 0.806 | 0.421 [0.218, 0.624] | 0.683 | 10.47 | 401.0 [205.2, 596.7] | 0.385 | `{'n_estimators': 100, 'max_depth': 3, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| strict | 2.0 | A2_Biomechanical_WithK | XGBoost | 69 | 44 | 0.801 | 0.391 [0.165, 0.618] | 0.723 | 8.83 | 352.4 [237.2, 467.5] | 0.409 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 2.0}` |
| strict | 2.0 | A2_Biomechanical_WithK | Neural_Network | 69 | 44 | 0.748 | 0.347 [0.051, 0.642] | 0.689 | 8.83 | 360.4 [241.1, 479.7] | 0.401 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.5, 'learning_rate_init': 0.0005}` |
| strict | 2.0 | A2_Biomechanical_WithK | Lasso | 69 | 44 | 0.545 | 0.490 [0.315, 0.666] | 0.746 | 9.31 | 374.1 [209.7, 538.5] | 0.055 | `{'alpha': 1.0}` |
| strict | 2.0 | A2_Biomechanical_WithK | ElasticNet | 69 | 44 | 0.545 | 0.492 [0.317, 0.666] | 0.745 | 9.29 | 373.5 [209.9, 537.0] | 0.054 | `{'alpha': 0.1, 'l1_ratio': 0.9}` |
| strict | 2.0 | A2_Biomechanical_WithK | Ridge | 69 | 44 | 0.530 | 0.497 [0.301, 0.694] | 0.729 | 9.12 | 369.1 [205.4, 532.7] | 0.033 | `{'alpha': 10.0}` |
| strict | 2.0 | B_Clinical_K | SVM | 69 | 44 | 0.303 | 0.169 [-0.245, 0.583] | 0.480 | 12.41 | 467.0 [224.9, 709.2] | 0.134 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 2.0 | B_Clinical_K | Random_Forest | 69 | 44 | 0.797 | 0.083 [-0.167, 0.333] | 0.405 | 13.49 | 489.8 [291.7, 687.9] | 0.714 | `{'n_estimators': 300, 'max_depth': None, 'min_samples_split': 2, 'min_samples_leaf': 2}` |
| strict | 2.0 | B_Clinical_K | XGBoost | 69 | 44 | 0.330 | 0.161 [0.013, 0.310] | 0.456 | 12.03 | 431.1 [290.5, 571.7] | 0.168 | `{'learning_rate': 0.005, 'max_depth': 1, 'n_estimators': 200, 'reg_alpha': 1.0, 'reg_lambda': 0.1}` |
| strict | 2.0 | B_Clinical_K | Neural_Network | 69 | 44 | 0.389 | 0.182 [0.021, 0.343] | 0.480 | 11.33 | 417.8 [309.3, 526.3] | 0.207 | `{'hidden_layer_sizes': (60,), 'alpha': 0.5, 'learning_rate_init': 0.0001}` |
| strict | 2.0 | B_Clinical_K | Lasso | 69 | 44 | 0.397 | 0.231 [0.031, 0.430] | 0.544 | 11.08 | 403.1 [293.6, 512.5] | 0.166 | `{'alpha': 1.0}` |
| strict | 2.0 | B_Clinical_K | ElasticNet | 69 | 44 | 0.354 | 0.254 [0.097, 0.411] | 0.530 | 10.97 | 403.5 [278.0, 529.0] | 0.100 | `{'alpha': 1.0, 'l1_ratio': 0.7}` |
| strict | 2.0 | B_Clinical_K | Ridge | 69 | 44 | 0.374 | 0.264 [0.102, 0.425] | 0.539 | 10.96 | 399.8 [277.7, 521.9] | 0.110 | `{'alpha': 10.0}` |
| strict | 2.0 | C1_Combined_K | SVM | 69 | 44 | 0.431 | 0.355 [0.085, 0.624] | 0.671 | 10.20 | 409.3 [222.4, 596.2] | 0.077 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 2.0 | C1_Combined_K | Random_Forest | 69 | 44 | 0.720 | 0.410 [0.137, 0.682] | 0.676 | 10.14 | 384.9 [215.2, 554.5] | 0.311 | `{'n_estimators': 200, 'max_depth': 4, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| strict | 2.0 | C1_Combined_K | XGBoost | 69 | 44 | 0.758 | 0.310 [0.186, 0.434] | 0.684 | 9.89 | 384.2 [255.4, 513.0] | 0.448 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 2.0}` |
| strict | 2.0 | C1_Combined_K | Neural_Network | 69 | 44 | 0.645 | 0.307 [-0.009, 0.623] | 0.678 | 9.58 | 362.5 [277.0, 448.1] | 0.338 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.5, 'learning_rate_init': 0.0005}` |
| strict | 2.0 | C1_Combined_K | Lasso | 69 | 44 | 0.546 | 0.386 [0.174, 0.599] | 0.670 | 9.10 | 355.1 [228.6, 481.5] | 0.159 | `{'alpha': 0.1}` |
| strict | 2.0 | C1_Combined_K | ElasticNet | 69 | 44 | 0.546 | 0.386 [0.174, 0.599] | 0.670 | 9.10 | 355.0 [228.7, 481.4] | 0.159 | `{'alpha': 0.001, 'l1_ratio': 0.1}` |
| strict | 2.0 | C1_Combined_K | Ridge | 69 | 44 | 0.437 | 0.396 [0.109, 0.684] | 0.640 | 10.35 | 409.2 [197.5, 620.9] | 0.041 | `{'alpha': 10.0}` |
| strict | 2.5 | A1_Biomechanical_Core_K | SVM | 69 | 44 | 0.523 | 0.449 [0.284, 0.615] | 0.763 | 11.85 | 405.8 [361.1, 450.6] | 0.073 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 2.5 | A1_Biomechanical_Core_K | Random_Forest | 69 | 44 | 0.730 | 0.384 [0.109, 0.659] | 0.644 | 11.86 | 398.8 [275.9, 521.8] | 0.347 | `{'n_estimators': 200, 'max_depth': 4, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| strict | 2.5 | A1_Biomechanical_Core_K | XGBoost | 69 | 44 | 0.688 | 0.371 [0.116, 0.626] | 0.680 | 11.21 | 376.1 [261.9, 490.3] | 0.318 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 1.0}` |
| strict | 2.5 | A1_Biomechanical_Core_K | Neural_Network | 69 | 44 | 0.519 | 0.379 [0.268, 0.490] | 0.652 | 12.00 | 409.8 [306.8, 512.7] | 0.140 | `{'hidden_layer_sizes': (80,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| strict | 2.5 | A1_Biomechanical_Core_K | Lasso | 69 | 44 | 0.592 | 0.471 [0.293, 0.649] | 0.757 | 11.56 | 396.6 [331.8, 461.4] | 0.121 | `{'alpha': 1.0}` |
| strict | 2.5 | A1_Biomechanical_Core_K | ElasticNet | 69 | 44 | 0.484 | 0.422 [0.297, 0.548] | 0.757 | 12.82 | 418.8 [369.9, 467.8] | 0.062 | `{'alpha': 1.0, 'l1_ratio': 0.1}` |
| strict | 2.5 | A1_Biomechanical_Core_K | Ridge | 69 | 44 | 0.581 | 0.486 [0.333, 0.639] | 0.759 | 11.51 | 392.0 [346.8, 437.2] | 0.095 | `{'alpha': 10.0}` |
| strict | 2.5 | A2_Biomechanical_WithK | SVM | 69 | 44 | 0.523 | 0.439 [0.273, 0.605] | 0.767 | 11.91 | 410.1 [357.0, 463.2] | 0.084 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 2.5 | A2_Biomechanical_WithK | Random_Forest | 69 | 44 | 0.885 | 0.393 [0.132, 0.654] | 0.695 | 12.69 | 415.2 [228.1, 602.2] | 0.492 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| strict | 2.5 | A2_Biomechanical_WithK | XGBoost | 69 | 44 | 0.931 | 0.390 [0.097, 0.682] | 0.633 | 11.35 | 407.0 [239.7, 574.4] | 0.541 | `{'learning_rate': 0.1, 'max_depth': 2, 'n_estimators': 100, 'reg_alpha': 0.1, 'reg_lambda': 2.0}` |
| strict | 2.5 | A2_Biomechanical_WithK | Neural_Network | 69 | 44 | 0.815 | 0.551 [0.297, 0.806] | 0.779 | 10.18 | 319.9 [222.9, 417.0] | 0.264 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.5, 'learning_rate_init': 0.0005}` |
| strict | 2.5 | A2_Biomechanical_WithK | Lasso | 69 | 44 | 0.668 | 0.512 [0.221, 0.803] | 0.761 | 10.74 | 329.7 [201.9, 457.6] | 0.156 | `{'alpha': 0.001}` |
| strict | 2.5 | A2_Biomechanical_WithK | ElasticNet | 69 | 44 | 0.597 | 0.432 [0.188, 0.676] | 0.737 | 11.18 | 394.5 [229.4, 559.6] | 0.165 | `{'alpha': 0.1, 'l1_ratio': 0.9}` |
| strict | 2.5 | A2_Biomechanical_WithK | Ridge | 69 | 44 | 0.668 | 0.512 [0.221, 0.803] | 0.761 | 10.74 | 329.7 [201.8, 457.6] | 0.156 | `{'alpha': 0.01}` |
| strict | 2.5 | B_Clinical_K | SVM | 69 | 44 | 0.101 | 0.049 [-0.066, 0.164] | 0.526 | 12.49 | 474.3 [264.5, 684.1] | 0.052 | `{'C': 100, 'epsilon': 100, 'gamma': 0.03}` |
| strict | 2.5 | B_Clinical_K | Random_Forest | 69 | 44 | 0.682 | 0.070 [-0.376, 0.517] | 0.397 | 15.16 | 480.2 [369.0, 591.3] | 0.612 | `{'n_estimators': 200, 'max_depth': 4, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| strict | 2.5 | B_Clinical_K | XGBoost | 69 | 44 | 0.240 | 0.079 [-0.027, 0.186] | 0.452 | 15.76 | 487.3 [430.5, 544.2] | 0.161 | `{'learning_rate': 0.001, 'max_depth': 4, 'n_estimators': 200, 'reg_alpha': 2.0, 'reg_lambda': 1.0}` |
| strict | 2.5 | B_Clinical_K | Neural_Network | 69 | 44 | 0.238 | 0.216 [0.103, 0.329] | 0.578 | 13.57 | 469.3 [329.8, 608.8] | 0.022 | `{'hidden_layer_sizes': (100,), 'alpha': 0.3, 'learning_rate_init': 0.0005}` |
| strict | 2.5 | B_Clinical_K | Lasso | 69 | 44 | 0.368 | 0.028 [-0.686, 0.742] | 0.498 | 12.96 | 433.4 [287.8, 579.0] | 0.340 | `{'alpha': 1.0}` |
| strict | 2.5 | B_Clinical_K | ElasticNet | 69 | 44 | 0.329 | 0.106 [-0.307, 0.519] | 0.482 | 12.78 | 437.2 [271.8, 602.7] | 0.223 | `{'alpha': 1.0, 'l1_ratio': 0.7}` |
| strict | 2.5 | B_Clinical_K | Ridge | 69 | 44 | 0.347 | 0.098 [-0.390, 0.585] | 0.489 | 12.79 | 433.6 [274.1, 593.2] | 0.249 | `{'alpha': 10.0}` |
| strict | 2.5 | C1_Combined_K | SVM | 69 | 44 | 0.527 | 0.397 [0.214, 0.581] | 0.747 | 12.65 | 426.0 [351.6, 500.4] | 0.130 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 2.5 | C1_Combined_K | Random_Forest | 69 | 44 | 0.734 | 0.340 [0.073, 0.607] | 0.605 | 12.45 | 413.7 [290.8, 536.6] | 0.394 | `{'n_estimators': 200, 'max_depth': 4, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| strict | 2.5 | C1_Combined_K | XGBoost | 69 | 44 | 0.690 | 0.364 [0.107, 0.622] | 0.676 | 11.30 | 378.1 [262.7, 493.5] | 0.326 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 1.0}` |
| strict | 2.5 | C1_Combined_K | Neural_Network | 69 | 44 | 0.643 | 0.364 [0.155, 0.572] | 0.678 | 12.05 | 389.3 [298.4, 480.1] | 0.279 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.5, 'learning_rate_init': 0.0005}` |
| strict | 2.5 | C1_Combined_K | Lasso | 69 | 44 | 0.596 | 0.448 [0.271, 0.625] | 0.742 | 11.69 | 405.3 [342.8, 467.7] | 0.147 | `{'alpha': 1.0}` |
| strict | 2.5 | C1_Combined_K | ElasticNet | 69 | 44 | 0.524 | 0.387 [0.158, 0.617] | 0.668 | 11.47 | 392.8 [304.9, 480.6] | 0.136 | `{'alpha': 0.01, 'l1_ratio': 0.1}` |
| strict | 2.5 | C1_Combined_K | Ridge | 69 | 44 | 0.584 | 0.463 [0.301, 0.626] | 0.749 | 11.85 | 400.9 [344.4, 457.4] | 0.120 | `{'alpha': 10.0}` |
| strict | 3.0 | A1_Biomechanical_Core_K | SVM | 69 | 44 | 0.471 | 0.423 [0.275, 0.572] | 0.746 | 13.35 | 426.6 [307.5, 545.8] | 0.048 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 3.0 | A1_Biomechanical_Core_K | Random_Forest | 69 | 44 | 0.710 | 0.332 [-0.123, 0.787] | 0.552 | 12.85 | 436.1 [265.7, 606.4] | 0.378 | `{'n_estimators': 100, 'max_depth': 5, 'min_samples_split': 10, 'min_samples_leaf': 4}` |
| strict | 3.0 | A1_Biomechanical_Core_K | XGBoost | 69 | 44 | 0.618 | 0.323 [0.055, 0.590] | 0.611 | 13.54 | 445.1 [194.8, 695.5] | 0.295 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 1.0}` |
| strict | 3.0 | A1_Biomechanical_Core_K | Neural_Network | 69 | 44 | 0.558 | 0.362 [0.074, 0.650] | 0.710 | 13.94 | 480.8 [129.6, 832.0] | 0.196 | `{'hidden_layer_sizes': (100,), 'alpha': 0.3, 'learning_rate_init': 0.0005}` |
| strict | 3.0 | A1_Biomechanical_Core_K | Lasso | 69 | 44 | 0.574 | 0.481 [0.215, 0.747] | 0.736 | 11.43 | 396.5 [239.0, 553.9] | 0.093 | `{'alpha': 1.0}` |
| strict | 3.0 | A1_Biomechanical_Core_K | ElasticNet | 69 | 44 | 0.470 | 0.417 [0.267, 0.567] | 0.740 | 13.78 | 428.5 [311.7, 545.3] | 0.053 | `{'alpha': 1.0, 'l1_ratio': 0.1}` |
| strict | 3.0 | A1_Biomechanical_Core_K | Ridge | 69 | 44 | 0.564 | 0.488 [0.261, 0.715] | 0.738 | 11.29 | 396.1 [257.2, 535.1] | 0.076 | `{'alpha': 10.0}` |
| strict | 3.0 | A2_Biomechanical_WithK | SVM | 69 | 44 | 0.478 | 0.418 [0.268, 0.567] | 0.741 | 13.09 | 429.2 [306.2, 552.1] | 0.060 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 3.0 | A2_Biomechanical_WithK | Random_Forest | 69 | 44 | 0.887 | 0.430 [0.231, 0.629] | 0.695 | 13.16 | 459.8 [144.1, 775.4] | 0.458 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| strict | 3.0 | A2_Biomechanical_WithK | XGBoost | 69 | 44 | 0.936 | 0.360 [0.026, 0.693] | 0.604 | 13.96 | 470.9 [168.9, 772.9] | 0.577 | `{'learning_rate': 0.1, 'max_depth': 2, 'n_estimators': 100, 'reg_alpha': 0.1, 'reg_lambda': 2.0}` |
| strict | 3.0 | A2_Biomechanical_WithK | Neural_Network | 69 | 44 | 0.866 | 0.565 [0.321, 0.809] | 0.790 | 9.84 | 352.1 [185.8, 518.5] | 0.301 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.5, 'learning_rate_init': 0.0005}` |
| strict | 3.0 | A2_Biomechanical_WithK | Lasso | 69 | 44 | 0.635 | 0.501 [0.239, 0.763] | 0.751 | 11.99 | 404.5 [164.8, 644.1] | 0.134 | `{'alpha': 1.0}` |
| strict | 3.0 | A2_Biomechanical_WithK | ElasticNet | 69 | 44 | 0.635 | 0.501 [0.237, 0.765] | 0.750 | 11.95 | 404.0 [165.6, 642.5] | 0.134 | `{'alpha': 0.1, 'l1_ratio': 0.9}` |
| strict | 3.0 | A2_Biomechanical_WithK | Ridge | 69 | 44 | 0.742 | 0.488 [0.176, 0.799] | 0.771 | 12.04 | 349.6 [262.9, 436.4] | 0.254 | `{'alpha': 0.01}` |
| strict | 3.0 | B_Clinical_K | SVM | 69 | 44 | 0.275 | 0.104 [-0.302, 0.510] | 0.457 | 17.65 | 541.0 [297.6, 784.5] | 0.171 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 3.0 | B_Clinical_K | Random_Forest | 69 | 44 | 0.691 | 0.182 [-0.201, 0.566] | 0.498 | 16.39 | 507.6 [299.9, 715.3] | 0.509 | `{'n_estimators': 100, 'max_depth': 5, 'min_samples_split': 10, 'min_samples_leaf': 4}` |
| strict | 3.0 | B_Clinical_K | XGBoost | 69 | 44 | 0.230 | 0.084 [-0.050, 0.217] | 0.433 | 17.79 | 505.5 [418.0, 593.0] | 0.147 | `{'learning_rate': 0.001, 'max_depth': 4, 'n_estimators': 200, 'reg_alpha': 2.0, 'reg_lambda': 1.0}` |
| strict | 3.0 | B_Clinical_K | Neural_Network | 69 | 44 | 0.437 | 0.124 [-0.081, 0.330] | 0.455 | 15.16 | 524.8 [372.6, 677.1] | 0.312 | `{'hidden_layer_sizes': (80,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| strict | 3.0 | B_Clinical_K | Lasso | 69 | 44 | 0.380 | -0.136 [-0.781, 0.509] | 0.454 | 17.88 | 565.7 [228.3, 903.2] | 0.516 | `{'alpha': 0.01}` |
| strict | 3.0 | B_Clinical_K | ElasticNet | 69 | 44 | 0.248 | 0.055 [-0.298, 0.408] | 0.427 | 19.27 | 558.2 [324.1, 792.3] | 0.194 | `{'alpha': 1.0, 'l1_ratio': 0.1}` |
| strict | 3.0 | B_Clinical_K | Ridge | 69 | 44 | 0.109 | 0.009 [-0.197, 0.214] | 0.327 | 16.74 | 559.0 [405.0, 713.0] | 0.100 | `{'alpha': 100.0}` |
| strict | 3.0 | C1_Combined_K | SVM | 69 | 44 | 0.487 | 0.398 [0.169, 0.627] | 0.725 | 13.60 | 435.2 [277.7, 592.7] | 0.089 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 3.0 | C1_Combined_K | Random_Forest | 69 | 44 | 0.713 | 0.333 [-0.113, 0.779] | 0.550 | 12.86 | 436.1 [270.4, 601.7] | 0.380 | `{'n_estimators': 100, 'max_depth': 5, 'min_samples_split': 10, 'min_samples_leaf': 4}` |
| strict | 3.0 | C1_Combined_K | XGBoost | 69 | 44 | 0.938 | 0.319 [0.059, 0.578] | 0.601 | 14.63 | 497.8 [174.8, 820.8] | 0.619 | `{'learning_rate': 0.1, 'max_depth': 2, 'n_estimators': 100, 'reg_alpha': 0.1, 'reg_lambda': 2.0}` |
| strict | 3.0 | C1_Combined_K | Neural_Network | 69 | 44 | 0.545 | 0.389 [0.146, 0.633] | 0.693 | 11.99 | 423.4 [257.6, 589.2] | 0.155 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.5, 'learning_rate_init': 0.0005}` |
| strict | 3.0 | C1_Combined_K | Lasso | 69 | 44 | 0.578 | 0.468 [0.225, 0.711] | 0.729 | 11.36 | 402.8 [258.7, 546.9] | 0.110 | `{'alpha': 1.0}` |
| strict | 3.0 | C1_Combined_K | ElasticNet | 69 | 44 | 0.478 | 0.396 [0.194, 0.597] | 0.737 | 14.24 | 437.3 [288.3, 586.3] | 0.082 | `{'alpha': 1.0, 'l1_ratio': 0.1}` |
| strict | 3.0 | C1_Combined_K | Ridge | 69 | 44 | 0.567 | 0.473 [0.228, 0.718] | 0.737 | 11.84 | 401.8 [251.0, 552.6] | 0.094 | `{'alpha': 10.0}` |
| strict | 3.5 | A1_Biomechanical_Core_K | SVM | 69 | 44 | 0.439 | 0.370 [0.155, 0.585] | 0.667 | 13.51 | 428.0 [304.1, 552.0] | 0.069 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 3.5 | A1_Biomechanical_Core_K | Random_Forest | 69 | 44 | 0.664 | 0.199 [-0.206, 0.604] | 0.460 | 15.02 | 475.6 [327.2, 623.9] | 0.465 | `{'n_estimators': 100, 'max_depth': 5, 'min_samples_split': 10, 'min_samples_leaf': 4}` |
| strict | 3.5 | A1_Biomechanical_Core_K | XGBoost | 69 | 44 | 0.225 | 0.095 [0.024, 0.165] | 0.519 | 18.71 | 514.0 [362.0, 666.0] | 0.130 | `{'learning_rate': 0.001, 'max_depth': 4, 'n_estimators': 200, 'reg_alpha': 2.0, 'reg_lambda': 1.0}` |
| strict | 3.5 | A1_Biomechanical_Core_K | Neural_Network | 69 | 44 | 0.680 | 0.279 [-0.195, 0.754] | 0.619 | 14.14 | 410.1 [179.9, 640.2] | 0.401 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.5, 'learning_rate_init': 0.0005}` |
| strict | 3.5 | A1_Biomechanical_Core_K | Lasso | 69 | 44 | 0.512 | 0.365 [0.042, 0.688] | 0.665 | 12.67 | 419.1 [259.6, 578.7] | 0.146 | `{'alpha': 1.0}` |
| strict | 3.5 | A1_Biomechanical_Core_K | ElasticNet | 69 | 44 | 0.419 | 0.348 [0.182, 0.514] | 0.666 | 14.35 | 438.0 [324.7, 551.4] | 0.071 | `{'alpha': 1.0, 'l1_ratio': 0.1}` |
| strict | 3.5 | A1_Biomechanical_Core_K | Ridge | 69 | 44 | 0.503 | 0.389 [0.121, 0.657] | 0.667 | 12.35 | 415.7 [280.2, 551.1] | 0.114 | `{'alpha': 10.0}` |
| strict | 3.5 | A2_Biomechanical_WithK | SVM | 69 | 44 | 0.441 | 0.347 [0.142, 0.552] | 0.639 | 13.42 | 437.3 [315.7, 558.9] | 0.094 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 3.5 | A2_Biomechanical_WithK | Random_Forest | 69 | 44 | 0.780 | 0.259 [0.037, 0.482] | 0.526 | 16.26 | 532.3 [294.6, 770.0] | 0.520 | `{'n_estimators': 100, 'max_depth': 3, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| strict | 3.5 | A2_Biomechanical_WithK | XGBoost | 69 | 44 | 0.233 | 0.076 [-0.001, 0.153] | 0.513 | 18.67 | 521.9 [356.0, 687.8] | 0.156 | `{'learning_rate': 0.001, 'max_depth': 4, 'n_estimators': 200, 'reg_alpha': 2.0, 'reg_lambda': 1.0}` |
| strict | 3.5 | A2_Biomechanical_WithK | Neural_Network | 69 | 44 | 0.791 | 0.429 [0.115, 0.744] | 0.709 | 12.61 | 370.3 [198.2, 542.5] | 0.361 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.5, 'learning_rate_init': 0.0005}` |
| strict | 3.5 | A2_Biomechanical_WithK | Lasso | 69 | 44 | 0.668 | 0.487 [0.185, 0.789] | 0.731 | 12.87 | 332.3 [187.1, 477.4] | 0.181 | `{'alpha': 0.001}` |
| strict | 3.5 | A2_Biomechanical_WithK | ElasticNet | 69 | 44 | 0.525 | 0.395 [0.169, 0.622] | 0.730 | 14.42 | 392.0 [235.9, 548.1] | 0.130 | `{'alpha': 1.0, 'l1_ratio': 0.1}` |
| strict | 3.5 | A2_Biomechanical_WithK | Ridge | 69 | 44 | 0.668 | 0.487 [0.185, 0.789] | 0.731 | 12.87 | 332.3 [187.1, 477.4] | 0.181 | `{'alpha': 0.01}` |
| strict | 3.5 | B_Clinical_K | SVM | 69 | 44 | 0.247 | 0.068 [-0.246, 0.382] | 0.383 | 18.36 | 536.0 [318.2, 753.9] | 0.179 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 3.5 | B_Clinical_K | Random_Forest | 69 | 44 | 0.715 | 0.114 [-0.472, 0.699] | 0.447 | 18.20 | 487.5 [206.0, 768.9] | 0.601 | `{'n_estimators': 100, 'max_depth': 2, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| strict | 3.5 | B_Clinical_K | XGBoost | 69 | 44 | 0.214 | 0.006 [-0.106, 0.119] | 0.120 | 19.24 | 536.5 [385.0, 688.1] | 0.208 | `{'learning_rate': 0.001, 'max_depth': 4, 'n_estimators': 200, 'reg_alpha': 2.0, 'reg_lambda': 1.0}` |
| strict | 3.5 | B_Clinical_K | Neural_Network | 69 | 44 | 0.417 | 0.055 [-0.118, 0.227] | 0.418 | 16.33 | 513.1 [393.2, 633.0] | 0.363 | `{'hidden_layer_sizes': (80,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| strict | 3.5 | B_Clinical_K | Lasso | 69 | 44 | 0.320 | -0.081 [-0.544, 0.383] | 0.405 | 16.38 | 508.5 [176.1, 840.9] | 0.400 | `{'alpha': 0.01}` |
| strict | 3.5 | B_Clinical_K | ElasticNet | 69 | 44 | 0.229 | 0.047 [-0.223, 0.316] | 0.377 | 19.34 | 541.6 [335.9, 747.4] | 0.182 | `{'alpha': 1.0, 'l1_ratio': 0.1}` |
| strict | 3.5 | B_Clinical_K | Ridge | 69 | 44 | 0.096 | -0.018 [-0.123, 0.088] | 0.270 | 17.54 | 536.6 [399.5, 673.8] | 0.114 | `{'alpha': 100.0}` |
| strict | 3.5 | C1_Combined_K | SVM | 69 | 44 | 0.445 | 0.344 [0.123, 0.564] | 0.658 | 13.83 | 439.0 [301.5, 576.5] | 0.101 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 3.5 | C1_Combined_K | Random_Forest | 69 | 44 | 0.670 | 0.177 [-0.281, 0.635] | 0.438 | 15.21 | 479.1 [326.1, 632.1] | 0.493 | `{'n_estimators': 100, 'max_depth': 5, 'min_samples_split': 10, 'min_samples_leaf': 4}` |
| strict | 3.5 | C1_Combined_K | XGBoost | 69 | 44 | 0.226 | 0.083 [0.011, 0.156] | 0.502 | 18.73 | 516.1 [367.9, 664.3] | 0.142 | `{'learning_rate': 0.001, 'max_depth': 4, 'n_estimators': 200, 'reg_alpha': 2.0, 'reg_lambda': 1.0}` |
| strict | 3.5 | C1_Combined_K | Neural_Network | 69 | 44 | 0.557 | 0.349 [0.116, 0.582] | 0.639 | 13.42 | 403.3 [246.4, 560.3] | 0.208 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.5, 'learning_rate_init': 0.0005}` |
| strict | 3.5 | C1_Combined_K | Lasso | 69 | 44 | 0.514 | 0.376 [0.048, 0.704] | 0.663 | 12.42 | 413.5 [254.4, 572.7] | 0.138 | `{'alpha': 1.0}` |
| strict | 3.5 | C1_Combined_K | ElasticNet | 69 | 44 | 0.426 | 0.336 [0.144, 0.529] | 0.668 | 14.57 | 443.1 [310.3, 575.9] | 0.090 | `{'alpha': 1.0, 'l1_ratio': 0.1}` |
| strict | 3.5 | C1_Combined_K | Ridge | 69 | 44 | 0.505 | 0.395 [0.116, 0.674] | 0.670 | 12.30 | 412.0 [273.3, 550.8] | 0.110 | `{'alpha': 10.0}` |
| strict | 4.0 | A1_Biomechanical_Core_K | SVM | 69 | 44 | 0.422 | 0.348 [0.112, 0.583] | 0.679 | 16.81 | 499.1 [348.6, 649.6] | 0.074 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 4.0 | A1_Biomechanical_Core_K | Random_Forest | 69 | 44 | 0.593 | 0.227 [0.011, 0.442] | 0.529 | 16.81 | 509.4 [278.9, 739.9] | 0.366 | `{'n_estimators': 200, 'max_depth': 4, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| strict | 4.0 | A1_Biomechanical_Core_K | XGBoost | 69 | 44 | 0.894 | 0.152 [0.018, 0.286] | 0.481 | 20.61 | 588.8 [370.9, 806.7] | 0.742 | `{'learning_rate': 0.1, 'max_depth': 2, 'n_estimators': 100, 'reg_alpha': 0.1, 'reg_lambda': 2.0}` |
| strict | 4.0 | A1_Biomechanical_Core_K | Neural_Network | 69 | 44 | 0.452 | 0.267 [0.228, 0.307] | 0.611 | 18.58 | 522.7 [402.0, 643.5] | 0.185 | `{'hidden_layer_sizes': (80,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| strict | 4.0 | A1_Biomechanical_Core_K | Lasso | 69 | 44 | 0.421 | 0.211 [-0.237, 0.658] | 0.616 | 16.56 | 499.1 [327.5, 670.6] | 0.210 | `{'alpha': 1.0}` |
| strict | 4.0 | A1_Biomechanical_Core_K | ElasticNet | 69 | 44 | 0.416 | 0.302 [0.137, 0.466] | 0.670 | 18.36 | 516.0 [387.8, 644.3] | 0.114 | `{'alpha': 1.0, 'l1_ratio': 0.1}` |
| strict | 4.0 | A1_Biomechanical_Core_K | Ridge | 69 | 44 | 0.499 | 0.286 [0.021, 0.551] | 0.669 | 17.16 | 508.9 [411.4, 606.4] | 0.213 | `{'alpha': 10.0}` |
| strict | 4.0 | A2_Biomechanical_WithK | SVM | 69 | 44 | 0.425 | 0.331 [0.107, 0.555] | 0.663 | 16.92 | 508.2 [347.6, 668.8] | 0.094 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 4.0 | A2_Biomechanical_WithK | Random_Forest | 69 | 44 | 0.637 | 0.222 [0.098, 0.345] | 0.557 | 16.64 | 501.9 [305.9, 697.9] | 0.415 | `{'n_estimators': 200, 'max_depth': 4, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| strict | 4.0 | A2_Biomechanical_WithK | XGBoost | 69 | 44 | 0.224 | 0.088 [-0.017, 0.193] | 0.390 | 20.71 | 548.9 [323.0, 774.7] | 0.136 | `{'learning_rate': 0.001, 'max_depth': 4, 'n_estimators': 200, 'reg_alpha': 2.0, 'reg_lambda': 1.0}` |
| strict | 4.0 | A2_Biomechanical_WithK | Neural_Network | 69 | 44 | 0.777 | 0.398 [-0.029, 0.825] | 0.735 | 15.79 | 411.7 [249.7, 573.7] | 0.379 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.5, 'learning_rate_init': 0.0005}` |
| strict | 4.0 | A2_Biomechanical_WithK | Lasso | 69 | 44 | 0.619 | 0.347 [0.117, 0.576] | 0.699 | 16.15 | 464.8 [346.9, 582.7] | 0.273 | `{'alpha': 0.001}` |
| strict | 4.0 | A2_Biomechanical_WithK | ElasticNet | 69 | 44 | 0.490 | 0.349 [0.144, 0.554] | 0.693 | 17.59 | 476.8 [299.7, 654.0] | 0.141 | `{'alpha': 1.0, 'l1_ratio': 0.1}` |
| strict | 4.0 | A2_Biomechanical_WithK | Ridge | 69 | 44 | 0.619 | 0.347 [0.117, 0.577] | 0.699 | 16.15 | 464.7 [346.8, 582.7] | 0.272 | `{'alpha': 0.01}` |
| strict | 4.0 | B_Clinical_K | SVM | 69 | 44 | 0.341 | 0.072 [-0.114, 0.258] | 0.358 | 19.57 | 585.3 [437.6, 733.0] | 0.270 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.03}` |
| strict | 4.0 | B_Clinical_K | Random_Forest | 69 | 44 | 0.671 | 0.209 [-0.302, 0.720] | 0.563 | 19.96 | 540.5 [226.6, 854.5] | 0.462 | `{'n_estimators': 100, 'max_depth': 2, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| strict | 4.0 | B_Clinical_K | XGBoost | 69 | 44 | 0.208 | 0.015 [-0.133, 0.164] | 0.120 | 20.81 | 567.7 [344.3, 791.1] | 0.192 | `{'learning_rate': 0.001, 'max_depth': 4, 'n_estimators': 200, 'reg_alpha': 2.0, 'reg_lambda': 1.0}` |
| strict | 4.0 | B_Clinical_K | Neural_Network | 69 | 44 | 0.475 | 0.166 [-0.075, 0.408] | 0.460 | 19.68 | 551.2 [407.7, 694.7] | 0.309 | `{'hidden_layer_sizes': (80,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| strict | 4.0 | B_Clinical_K | Lasso | 69 | 44 | 0.338 | -0.027 [-0.499, 0.446] | 0.544 | 21.96 | 670.9 [453.7, 888.1] | 0.364 | `{'alpha': 1.0}` |
| strict | 4.0 | B_Clinical_K | ElasticNet | 69 | 44 | 0.211 | 0.002 [-0.135, 0.139] | 0.411 | 20.57 | 617.0 [392.8, 841.2] | 0.209 | `{'alpha': 1.0, 'l1_ratio': 0.5}` |
| strict | 4.0 | B_Clinical_K | Ridge | 69 | 44 | 0.100 | 0.026 [-0.082, 0.134] | 0.301 | 21.05 | 599.7 [472.4, 727.0] | 0.074 | `{'alpha': 100.0}` |
| strict | 4.0 | C1_Combined_K | SVM | 69 | 44 | 0.422 | 0.321 [0.089, 0.552] | 0.676 | 16.88 | 511.0 [353.5, 668.6] | 0.101 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 4.0 | C1_Combined_K | Random_Forest | 69 | 44 | 0.612 | 0.241 [0.015, 0.466] | 0.511 | 16.96 | 505.2 [272.3, 738.1] | 0.371 | `{'n_estimators': 200, 'max_depth': 4, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| strict | 4.0 | C1_Combined_K | XGBoost | 69 | 44 | 0.916 | 0.178 [0.036, 0.320] | 0.492 | 19.91 | 591.3 [320.7, 861.9] | 0.738 | `{'learning_rate': 0.1, 'max_depth': 2, 'n_estimators': 100, 'reg_alpha': 0.1, 'reg_lambda': 2.0}` |
| strict | 4.0 | C1_Combined_K | Neural_Network | 69 | 44 | 0.594 | 0.222 [-0.052, 0.497] | 0.637 | 17.02 | 507.0 [382.6, 631.4] | 0.372 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.5, 'learning_rate_init': 0.0005}` |
| strict | 4.0 | C1_Combined_K | Lasso | 69 | 44 | 0.524 | 0.232 [-0.104, 0.568] | 0.660 | 18.26 | 519.0 [396.7, 641.3] | 0.293 | `{'alpha': 1.0}` |
| strict | 4.0 | C1_Combined_K | ElasticNet | 69 | 44 | 0.431 | 0.310 [0.150, 0.469] | 0.682 | 18.06 | 513.0 [387.2, 638.9] | 0.121 | `{'alpha': 1.0, 'l1_ratio': 0.1}` |
| strict | 4.0 | C1_Combined_K | Ridge | 69 | 44 | 0.513 | 0.336 [0.058, 0.614] | 0.678 | 16.42 | 486.7 [394.1, 579.3] | 0.177 | `{'alpha': 10.0}` |
| strict | 4.5 | A1_Biomechanical_Core_K | SVM | 69 | 44 | 0.470 | 0.355 [0.176, 0.533] | 0.698 | 18.47 | 497.0 [417.7, 576.3] | 0.116 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 4.5 | A1_Biomechanical_Core_K | Random_Forest | 69 | 44 | 0.708 | 0.263 [-0.198, 0.723] | 0.687 | 20.01 | 531.0 [366.1, 695.9] | 0.445 | `{'n_estimators': 300, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 4}` |
| strict | 4.5 | A1_Biomechanical_Core_K | XGBoost | 69 | 44 | 0.596 | 0.184 [0.087, 0.280] | 0.479 | 20.69 | 547.5 [494.4, 600.5] | 0.412 | `{'learning_rate': 0.05, 'max_depth': 2, 'n_estimators': 50, 'reg_alpha': 0.5, 'reg_lambda': 2.0}` |
| strict | 4.5 | A1_Biomechanical_Core_K | Neural_Network | 69 | 44 | 0.442 | 0.305 [0.220, 0.389] | 0.618 | 19.70 | 504.3 [469.4, 539.2] | 0.137 | `{'hidden_layer_sizes': (80,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| strict | 4.5 | A1_Biomechanical_Core_K | Lasso | 69 | 44 | 0.531 | 0.303 [-0.025, 0.632] | 0.677 | 17.33 | 499.1 [403.4, 594.9] | 0.228 | `{'alpha': 1.0}` |
| strict | 4.5 | A1_Biomechanical_Core_K | ElasticNet | 69 | 44 | 0.433 | 0.320 [0.154, 0.485] | 0.681 | 19.13 | 511.1 [435.9, 586.3] | 0.113 | `{'alpha': 1.0, 'l1_ratio': 0.1}` |
| strict | 4.5 | A1_Biomechanical_Core_K | Ridge | 69 | 44 | 0.521 | 0.345 [0.071, 0.618] | 0.681 | 17.54 | 489.3 [416.2, 562.4] | 0.176 | `{'alpha': 10.0}` |
| strict | 4.5 | A2_Biomechanical_WithK | SVM | 69 | 44 | 0.473 | 0.333 [0.183, 0.483] | 0.689 | 18.58 | 507.7 [426.6, 588.8] | 0.140 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 4.5 | A2_Biomechanical_WithK | Random_Forest | 69 | 44 | 0.889 | 0.250 [-0.073, 0.574] | 0.632 | 20.06 | 533.0 [446.3, 619.7] | 0.639 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| strict | 4.5 | A2_Biomechanical_WithK | XGBoost | 69 | 44 | 0.514 | 0.108 [-0.032, 0.249] | 0.662 | 22.86 | 579.0 [429.8, 728.3] | 0.406 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 30, 'reg_alpha': 2.0, 'reg_lambda': 0.5}` |
| strict | 4.5 | A2_Biomechanical_WithK | Neural_Network | 69 | 44 | 0.596 | 0.389 [0.045, 0.734] | 0.645 | 16.40 | 439.0 [328.0, 549.9] | 0.207 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.5, 'learning_rate_init': 0.0005}` |
| strict | 4.5 | A2_Biomechanical_WithK | Lasso | 69 | 44 | 0.613 | 0.345 [-0.113, 0.804] | 0.690 | 18.76 | 467.9 [399.8, 536.0] | 0.268 | `{'alpha': 0.01}` |
| strict | 4.5 | A2_Biomechanical_WithK | ElasticNet | 69 | 44 | 0.613 | 0.345 [-0.113, 0.804] | 0.690 | 18.76 | 467.9 [399.8, 536.0] | 0.268 | `{'alpha': 0.001, 'l1_ratio': 0.5}` |
| strict | 4.5 | A2_Biomechanical_WithK | Ridge | 69 | 44 | 0.613 | 0.346 [-0.112, 0.803] | 0.690 | 18.75 | 467.8 [399.8, 535.8] | 0.267 | `{'alpha': 0.1}` |
| strict | 4.5 | B_Clinical_K | SVM | 69 | 44 | 0.382 | 0.192 [-0.075, 0.460] | 0.513 | 19.09 | 539.4 [451.0, 627.8] | 0.190 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.03}` |
| strict | 4.5 | B_Clinical_K | Random_Forest | 69 | 44 | 0.661 | 0.089 [-0.764, 0.941] | 0.494 | 21.04 | 539.5 [277.0, 802.0] | 0.573 | `{'n_estimators': 100, 'max_depth': 2, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| strict | 4.5 | B_Clinical_K | XGBoost | 69 | 44 | 0.223 | 0.032 [0.003, 0.061] | 0.232 | 27.12 | 683.5 [628.8, 738.2] | 0.191 | `{'learning_rate': 0.01, 'max_depth': 2, 'n_estimators': 30, 'reg_alpha': 0.5, 'reg_lambda': 2.0}` |
| strict | 4.5 | B_Clinical_K | Neural_Network | 69 | 44 | 0.447 | 0.158 [-0.040, 0.355] | 0.481 | 21.38 | 552.1 [518.3, 586.0] | 0.290 | `{'hidden_layer_sizes': (80,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| strict | 4.5 | B_Clinical_K | Lasso | 69 | 44 | 0.379 | 0.101 [-0.284, 0.487] | 0.580 | 22.41 | 632.9 [443.9, 822.0] | 0.278 | `{'alpha': 1.0}` |
| strict | 4.5 | B_Clinical_K | ElasticNet | 69 | 44 | 0.377 | 0.119 [-0.251, 0.490] | 0.590 | 22.51 | 627.2 [441.9, 812.6] | 0.258 | `{'alpha': 0.1, 'l1_ratio': 0.3}` |
| strict | 4.5 | B_Clinical_K | Ridge | 69 | 44 | 0.370 | 0.127 [-0.203, 0.456] | 0.596 | 22.93 | 626.0 [453.0, 799.0] | 0.243 | `{'alpha': 10.0}` |
| strict | 4.5 | C1_Combined_K | SVM | 69 | 44 | 0.477 | 0.307 [0.141, 0.473] | 0.692 | 18.43 | 519.8 [406.8, 632.7] | 0.170 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 4.5 | C1_Combined_K | Random_Forest | 69 | 44 | 0.706 | 0.246 [-0.183, 0.675] | 0.651 | 20.19 | 538.5 [381.1, 695.9] | 0.460 | `{'n_estimators': 300, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 4}` |
| strict | 4.5 | C1_Combined_K | XGBoost | 69 | 44 | 0.918 | 0.148 [-0.239, 0.534] | 0.561 | 21.18 | 572.0 [448.4, 695.7] | 0.770 | `{'learning_rate': 0.1, 'max_depth': 2, 'n_estimators': 100, 'reg_alpha': 0.1, 'reg_lambda': 2.0}` |
| strict | 4.5 | C1_Combined_K | Neural_Network | 69 | 44 | 0.588 | 0.259 [-0.012, 0.529] | 0.610 | 18.76 | 503.7 [372.2, 635.2] | 0.329 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.5, 'learning_rate_init': 0.0005}` |
| strict | 4.5 | C1_Combined_K | Lasso | 69 | 44 | 0.541 | 0.336 [-0.008, 0.681] | 0.677 | 17.26 | 482.5 [384.8, 580.2] | 0.205 | `{'alpha': 1.0}` |
| strict | 4.5 | C1_Combined_K | ElasticNet | 69 | 44 | 0.446 | 0.311 [0.161, 0.461] | 0.699 | 19.18 | 516.7 [424.5, 608.9] | 0.135 | `{'alpha': 1.0, 'l1_ratio': 0.1}` |
| strict | 4.5 | C1_Combined_K | Ridge | 69 | 44 | 0.530 | 0.359 [0.077, 0.641] | 0.695 | 17.12 | 482.1 [396.5, 567.7] | 0.171 | `{'alpha': 10.0}` |
| strict | 5.0 | A1_Biomechanical_Core_K | SVM | 69 | 44 | 0.384 | 0.248 [-0.005, 0.501] | 0.623 | 27.11 | 647.6 [499.3, 795.9] | 0.136 | `{'C': 5000, 'epsilon': 800, 'gamma': 0.01}` |
| strict | 5.0 | A1_Biomechanical_Core_K | Random_Forest | 69 | 44 | 0.901 | 0.384 [0.188, 0.579] | 0.682 | 18.40 | 524.7 [385.4, 663.9] | 0.517 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| strict | 5.0 | A1_Biomechanical_Core_K | XGBoost | 69 | 44 | 0.933 | 0.347 [0.108, 0.586] | 0.660 | 18.68 | 536.9 [400.8, 672.9] | 0.585 | `{'learning_rate': 0.1, 'max_depth': 2, 'n_estimators': 100, 'reg_alpha': 0.1, 'reg_lambda': 2.0}` |
| strict | 5.0 | A1_Biomechanical_Core_K | Neural_Network | 69 | 44 | 0.687 | 0.314 [0.021, 0.608] | 0.700 | 20.49 | 536.7 [401.2, 672.2] | 0.373 | `{'hidden_layer_sizes': (100,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| strict | 5.0 | A1_Biomechanical_Core_K | Lasso | 69 | 44 | 0.517 | 0.343 [0.137, 0.549] | 0.717 | 21.93 | 609.7 [480.7, 738.8] | 0.174 | `{'alpha': 1.0}` |
| strict | 5.0 | A1_Biomechanical_Core_K | ElasticNet | 69 | 44 | 0.515 | 0.367 [0.188, 0.545] | 0.721 | 21.88 | 602.4 [466.8, 738.0] | 0.148 | `{'alpha': 0.1, 'l1_ratio': 0.3}` |
| strict | 5.0 | A1_Biomechanical_Core_K | Ridge | 69 | 44 | 0.508 | 0.379 [0.232, 0.527] | 0.722 | 22.11 | 600.6 [458.3, 742.9] | 0.129 | `{'alpha': 10.0}` |
| strict | 5.0 | A2_Biomechanical_WithK | SVM | 69 | 44 | 0.662 | 0.243 [-0.284, 0.769] | 0.682 | 17.88 | 553.2 [131.3, 975.1] | 0.419 | `{'C': 5000, 'epsilon': 100, 'gamma': 0.05}` |
| strict | 5.0 | A2_Biomechanical_WithK | Random_Forest | 69 | 44 | 0.899 | 0.327 [0.081, 0.574] | 0.672 | 19.21 | 544.7 [401.2, 688.1] | 0.571 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| strict | 5.0 | A2_Biomechanical_WithK | XGBoost | 69 | 44 | 0.950 | 0.335 [0.107, 0.563] | 0.670 | 19.18 | 535.5 [434.0, 637.0] | 0.615 | `{'learning_rate': 0.1, 'max_depth': 2, 'n_estimators': 100, 'reg_alpha': 0.1, 'reg_lambda': 2.0}` |
| strict | 5.0 | A2_Biomechanical_WithK | Neural_Network | 69 | 44 | 0.653 | 0.368 [0.128, 0.608] | 0.736 | 20.83 | 595.0 [464.8, 725.1] | 0.285 | `{'hidden_layer_sizes': (60,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| strict | 5.0 | A2_Biomechanical_WithK | Lasso | 69 | 44 | 0.581 | 0.416 [0.252, 0.579] | 0.723 | 20.95 | 573.3 [504.5, 642.0] | 0.166 | `{'alpha': 1.0}` |
| strict | 5.0 | A2_Biomechanical_WithK | ElasticNet | 69 | 44 | 0.579 | 0.428 [0.284, 0.572] | 0.728 | 20.95 | 569.8 [491.5, 648.0] | 0.152 | `{'alpha': 0.1, 'l1_ratio': 0.3}` |
| strict | 5.0 | A2_Biomechanical_WithK | Ridge | 69 | 44 | 0.571 | 0.426 [0.316, 0.536] | 0.731 | 21.34 | 575.6 [477.0, 674.2] | 0.145 | `{'alpha': 10.0}` |
| strict | 5.0 | B_Clinical_K | SVM | 69 | 44 | 0.501 | 0.236 [-0.106, 0.577] | 0.581 | 19.90 | 552.3 [396.9, 707.8] | 0.266 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.03}` |
| strict | 5.0 | B_Clinical_K | Random_Forest | 69 | 44 | 0.715 | 0.234 [-0.466, 0.933] | 0.639 | 21.96 | 589.1 [333.7, 844.5] | 0.481 | `{'n_estimators': 300, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 4}` |
| strict | 5.0 | B_Clinical_K | XGBoost | 69 | 44 | 0.917 | 0.072 [-0.341, 0.485] | 0.475 | 23.85 | 636.6 [461.2, 812.0] | 0.846 | `{'learning_rate': 0.1, 'max_depth': 2, 'n_estimators': 100, 'reg_alpha': 0.1, 'reg_lambda': 2.0}` |
| strict | 5.0 | B_Clinical_K | Neural_Network | 69 | 44 | 0.743 | 0.288 [-0.169, 0.745] | 0.720 | 19.77 | 533.1 [352.3, 713.9] | 0.455 | `{'hidden_layer_sizes': (100,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| strict | 5.0 | B_Clinical_K | Lasso | 69 | 44 | 0.466 | 0.225 [0.034, 0.416] | 0.654 | 23.34 | 665.8 [540.7, 790.8] | 0.241 | `{'alpha': 1.0}` |
| strict | 5.0 | B_Clinical_K | ElasticNet | 69 | 44 | 0.464 | 0.250 [0.089, 0.411] | 0.666 | 23.22 | 657.8 [526.9, 788.8] | 0.214 | `{'alpha': 0.1, 'l1_ratio': 0.3}` |
| strict | 5.0 | B_Clinical_K | Ridge | 69 | 44 | 0.456 | 0.265 [0.146, 0.385] | 0.674 | 23.65 | 655.1 [517.4, 792.8] | 0.191 | `{'alpha': 10.0}` |
| strict | 5.0 | C1_Combined_K | SVM | 69 | 44 | 0.403 | 0.244 [0.006, 0.482] | 0.604 | 26.92 | 650.4 [503.1, 797.7] | 0.159 | `{'C': 5000, 'epsilon': 800, 'gamma': 0.01}` |
| strict | 5.0 | C1_Combined_K | Random_Forest | 69 | 44 | 0.907 | 0.294 [0.080, 0.507] | 0.596 | 21.53 | 580.5 [324.6, 836.4] | 0.614 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| strict | 5.0 | C1_Combined_K | XGBoost | 69 | 44 | 0.944 | 0.282 [0.100, 0.463] | 0.576 | 21.56 | 584.2 [345.4, 822.9] | 0.663 | `{'learning_rate': 0.1, 'max_depth': 2, 'n_estimators': 100, 'reg_alpha': 0.1, 'reg_lambda': 2.0}` |
| strict | 5.0 | C1_Combined_K | Neural_Network | 69 | 44 | 0.663 | 0.346 [0.031, 0.662] | 0.686 | 18.58 | 491.2 [289.5, 692.9] | 0.317 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.5, 'learning_rate_init': 0.0005}` |
| strict | 5.0 | C1_Combined_K | Lasso | 69 | 44 | 0.637 | 0.367 [-0.068, 0.802] | 0.713 | 19.16 | 516.7 [378.8, 654.5] | 0.270 | `{'alpha': 0.01}` |
| strict | 5.0 | C1_Combined_K | ElasticNet | 69 | 44 | 0.637 | 0.367 [-0.067, 0.801] | 0.713 | 19.16 | 516.6 [378.7, 654.5] | 0.270 | `{'alpha': 0.001, 'l1_ratio': 0.5}` |
| strict | 5.0 | C1_Combined_K | Ridge | 69 | 44 | 0.637 | 0.368 [-0.065, 0.801] | 0.713 | 19.14 | 516.4 [378.5, 654.2] | 0.269 | `{'alpha': 0.1}` |
| strict | 5.5 | A1_Biomechanical_Core_K | SVM | 69 | 44 | 0.402 | 0.267 [0.098, 0.436] | 0.562 | 23.30 | 677.8 [484.4, 871.2] | 0.135 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 5.5 | A1_Biomechanical_Core_K | Random_Forest | 69 | 44 | 0.919 | 0.275 [-0.071, 0.622] | 0.676 | 22.15 | 649.5 [399.8, 899.1] | 0.643 | `{'n_estimators': 100, 'max_depth': 5, 'min_samples_split': 2, 'min_samples_leaf': 1}` |
| strict | 5.5 | A1_Biomechanical_Core_K | XGBoost | 69 | 44 | 0.511 | 0.280 [0.234, 0.325] | 0.692 | 26.54 | 658.7 [457.7, 859.8] | 0.231 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 30, 'reg_alpha': 2.0, 'reg_lambda': 0.5}` |
| strict | 5.5 | A1_Biomechanical_Core_K | Neural_Network | 69 | 44 | 0.648 | 0.330 [0.048, 0.611] | 0.615 | 23.44 | 642.2 [403.7, 880.7] | 0.318 | `{'hidden_layer_sizes': (80,), 'alpha': 0.5, 'learning_rate_init': 0.001}` |
| strict | 5.5 | A1_Biomechanical_Core_K | Lasso | 69 | 44 | 0.497 | 0.315 [0.143, 0.487] | 0.708 | 23.85 | 655.4 [527.1, 783.6] | 0.181 | `{'alpha': 1.0}` |
| strict | 5.5 | A1_Biomechanical_Core_K | ElasticNet | 69 | 44 | 0.494 | 0.343 [0.177, 0.508] | 0.712 | 23.64 | 645.2 [500.7, 789.7] | 0.151 | `{'alpha': 0.1, 'l1_ratio': 0.3}` |
| strict | 5.5 | A1_Biomechanical_Core_K | Ridge | 69 | 44 | 0.485 | 0.353 [0.177, 0.530] | 0.710 | 23.80 | 642.0 [479.5, 804.6] | 0.132 | `{'alpha': 10.0}` |
| strict | 5.5 | A2_Biomechanical_WithK | SVM | 69 | 44 | 0.428 | 0.275 [0.082, 0.468] | 0.566 | 23.07 | 673.8 [470.7, 877.0] | 0.153 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 5.5 | A2_Biomechanical_WithK | Random_Forest | 69 | 44 | 0.925 | 0.343 [0.107, 0.579] | 0.714 | 22.13 | 622.0 [411.9, 832.1] | 0.582 | `{'n_estimators': 100, 'max_depth': 5, 'min_samples_split': 2, 'min_samples_leaf': 1}` |
| strict | 5.5 | A2_Biomechanical_WithK | XGBoost | 69 | 44 | 0.513 | 0.275 [0.238, 0.312] | 0.690 | 26.58 | 660.5 [461.3, 859.8] | 0.238 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 30, 'reg_alpha': 2.0, 'reg_lambda': 0.5}` |
| strict | 5.5 | A2_Biomechanical_WithK | Neural_Network | 69 | 44 | 0.668 | 0.371 [0.115, 0.627] | 0.702 | 20.35 | 541.2 [292.4, 790.0] | 0.297 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.5, 'learning_rate_init': 0.0005}` |
| strict | 5.5 | A2_Biomechanical_WithK | Lasso | 69 | 44 | 0.531 | 0.357 [0.213, 0.502] | 0.709 | 23.25 | 638.2 [491.0, 785.5] | 0.173 | `{'alpha': 1.0}` |
| strict | 5.5 | A2_Biomechanical_WithK | ElasticNet | 69 | 44 | 0.528 | 0.385 [0.227, 0.543] | 0.713 | 22.89 | 624.6 [467.5, 781.8] | 0.143 | `{'alpha': 0.1, 'l1_ratio': 0.3}` |
| strict | 5.5 | A2_Biomechanical_WithK | Ridge | 69 | 44 | 0.519 | 0.393 [0.220, 0.566] | 0.714 | 23.16 | 621.8 [451.1, 792.5] | 0.126 | `{'alpha': 10.0}` |
| strict | 5.5 | B_Clinical_K | SVM | 69 | 44 | 0.307 | 0.119 [-0.203, 0.440] | 0.702 | 32.05 | 745.5 [543.8, 947.3] | 0.188 | `{'C': 500, 'epsilon': 800, 'gamma': 0.03}` |
| strict | 5.5 | B_Clinical_K | Random_Forest | 69 | 44 | 0.619 | 0.149 [-0.213, 0.511] | 0.492 | 25.86 | 669.0 [401.1, 937.0] | 0.469 | `{'n_estimators': 50, 'max_depth': 2, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| strict | 5.5 | B_Clinical_K | XGBoost | 69 | 44 | 0.510 | 0.132 [-0.262, 0.527] | 0.419 | 28.91 | 696.4 [507.6, 885.2] | 0.378 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 30, 'reg_alpha': 2.0, 'reg_lambda': 0.5}` |
| strict | 5.5 | B_Clinical_K | Neural_Network | 69 | 44 | 0.356 | 0.134 [-0.002, 0.269] | 0.489 | 25.20 | 728.9 [518.3, 939.6] | 0.223 | `{'hidden_layer_sizes': (100,), 'alpha': 0.1, 'learning_rate_init': 0.001}` |
| strict | 5.5 | B_Clinical_K | Lasso | 69 | 44 | 0.463 | 0.171 [-0.097, 0.438] | 0.616 | 26.19 | 714.3 [599.5, 829.1] | 0.293 | `{'alpha': 1.0}` |
| strict | 5.5 | B_Clinical_K | ElasticNet | 69 | 44 | 0.460 | 0.210 [-0.047, 0.468] | 0.636 | 25.51 | 700.9 [560.7, 841.2] | 0.250 | `{'alpha': 0.1, 'l1_ratio': 0.3}` |
| strict | 5.5 | B_Clinical_K | Ridge | 69 | 44 | 0.449 | 0.233 [-0.024, 0.491] | 0.650 | 25.34 | 694.7 [526.3, 863.1] | 0.215 | `{'alpha': 10.0}` |
| strict | 5.5 | C1_Combined_K | SVM | 69 | 44 | 0.449 | 0.299 [0.117, 0.480] | 0.657 | 23.50 | 658.8 [484.1, 833.6] | 0.150 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 5.5 | C1_Combined_K | Random_Forest | 69 | 44 | 0.920 | 0.223 [-0.029, 0.474] | 0.632 | 24.62 | 668.1 [494.2, 841.9] | 0.697 | `{'n_estimators': 100, 'max_depth': 5, 'min_samples_split': 2, 'min_samples_leaf': 1}` |
| strict | 5.5 | C1_Combined_K | XGBoost | 69 | 44 | 0.657 | 0.231 [-0.060, 0.522] | 0.593 | 22.62 | 574.2 [425.9, 722.4] | 0.426 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 30, 'reg_alpha': 1.0, 'reg_lambda': 0.1}` |
| strict | 5.5 | C1_Combined_K | Neural_Network | 69 | 44 | 0.657 | 0.347 [0.096, 0.599] | 0.665 | 22.34 | 587.1 [377.4, 796.8] | 0.309 | `{'hidden_layer_sizes': (60,), 'alpha': 1.0, 'learning_rate_init': 0.001}` |
| strict | 5.5 | C1_Combined_K | Lasso | 69 | 44 | 0.594 | 0.287 [-0.149, 0.724] | 0.674 | 24.24 | 624.1 [467.3, 780.8] | 0.307 | `{'alpha': 0.01}` |
| strict | 5.5 | C1_Combined_K | ElasticNet | 69 | 44 | 0.506 | 0.291 [0.117, 0.465] | 0.674 | 24.25 | 667.3 [537.1, 797.5] | 0.215 | `{'alpha': 0.1, 'l1_ratio': 0.3}` |
| strict | 5.5 | C1_Combined_K | Ridge | 69 | 44 | 0.499 | 0.313 [0.131, 0.495] | 0.687 | 24.04 | 657.6 [518.7, 796.5] | 0.185 | `{'alpha': 10.0}` |
| strict | 6.0 | A1_Biomechanical_Core_K | SVM | 69 | 44 | 0.487 | 0.279 [-0.237, 0.794] | 0.663 | 21.20 | 542.7 [363.6, 721.8] | 0.209 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.03}` |
| strict | 6.0 | A1_Biomechanical_Core_K | Random_Forest | 69 | 44 | 0.729 | 0.270 [-0.351, 0.890] | 0.737 | 24.57 | 627.5 [471.6, 783.4] | 0.459 | `{'n_estimators': 300, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 4}` |
| strict | 6.0 | A1_Biomechanical_Core_K | XGBoost | 69 | 44 | 0.917 | 0.229 [-0.035, 0.494] | 0.580 | 24.52 | 618.5 [428.4, 808.7] | 0.688 | `{'learning_rate': 0.1, 'max_depth': 2, 'n_estimators': 100, 'reg_alpha': 0.1, 'reg_lambda': 2.0}` |
| strict | 6.0 | A1_Biomechanical_Core_K | Neural_Network | 69 | 44 | 0.609 | 0.357 [0.051, 0.662] | 0.635 | 25.06 | 685.2 [459.5, 911.0] | 0.252 | `{'hidden_layer_sizes': (80,), 'alpha': 0.5, 'learning_rate_init': 0.001}` |
| strict | 6.0 | A1_Biomechanical_Core_K | Lasso | 69 | 44 | 0.414 | 0.288 [0.119, 0.457] | 0.628 | 26.24 | 691.2 [595.5, 786.9] | 0.127 | `{'alpha': 1.0}` |
| strict | 6.0 | A1_Biomechanical_Core_K | ElasticNet | 69 | 44 | 0.413 | 0.303 [0.139, 0.467] | 0.633 | 25.96 | 684.8 [580.9, 788.6] | 0.109 | `{'alpha': 0.1, 'l1_ratio': 0.3}` |
| strict | 6.0 | A1_Biomechanical_Core_K | Ridge | 69 | 44 | 0.406 | 0.311 [0.159, 0.464] | 0.634 | 25.93 | 682.4 [568.8, 795.9] | 0.095 | `{'alpha': 10.0}` |
| strict | 6.0 | A2_Biomechanical_WithK | SVM | 69 | 44 | 0.436 | 0.306 [0.138, 0.474] | 0.634 | 30.33 | 720.9 [587.5, 854.3] | 0.129 | `{'C': 5000, 'epsilon': 800, 'gamma': 0.01}` |
| strict | 6.0 | A2_Biomechanical_WithK | Random_Forest | 69 | 44 | 0.929 | 0.324 [-0.108, 0.756] | 0.748 | 21.73 | 574.5 [358.9, 790.0] | 0.604 | `{'n_estimators': 100, 'max_depth': 5, 'min_samples_split': 2, 'min_samples_leaf': 1}` |
| strict | 6.0 | A2_Biomechanical_WithK | XGBoost | 69 | 44 | 0.999 | 0.160 [-0.421, 0.741] | 0.651 | 26.18 | 672.2 [542.2, 802.3] | 0.839 | `{'learning_rate': 0.1, 'max_depth': 4, 'n_estimators': 100, 'reg_alpha': 1.0, 'reg_lambda': 0.5}` |
| strict | 6.0 | A2_Biomechanical_WithK | Neural_Network | 69 | 44 | 0.574 | 0.335 [0.028, 0.642] | 0.669 | 25.02 | 659.3 [517.1, 801.4] | 0.239 | `{'hidden_layer_sizes': (60,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| strict | 6.0 | A2_Biomechanical_WithK | Lasso | 69 | 44 | 0.539 | 0.249 [-0.001, 0.500] | 0.663 | 21.44 | 596.6 [437.4, 755.8] | 0.289 | `{'alpha': 0.001}` |
| strict | 6.0 | A2_Biomechanical_WithK | ElasticNet | 69 | 44 | 0.434 | 0.350 [0.153, 0.548] | 0.661 | 22.90 | 568.8 [340.8, 796.8] | 0.084 | `{'alpha': 1.0, 'l1_ratio': 0.1}` |
| strict | 6.0 | A2_Biomechanical_WithK | Ridge | 69 | 44 | 0.477 | 0.326 [0.216, 0.437] | 0.653 | 25.30 | 679.6 [540.6, 818.6] | 0.151 | `{'alpha': 10.0}` |
| strict | 6.0 | B_Clinical_K | SVM | 69 | 44 | 0.259 | 0.173 [-0.011, 0.357] | 0.653 | 31.60 | 749.4 [614.9, 883.8] | 0.086 | `{'C': 500, 'epsilon': 800, 'gamma': 0.03}` |
| strict | 6.0 | B_Clinical_K | Random_Forest | 69 | 44 | 0.663 | 0.186 [-0.161, 0.534] | 0.501 | 27.64 | 747.7 [474.6, 1020.7] | 0.477 | `{'n_estimators': 100, 'max_depth': 2, 'min_samples_split': 5, 'min_samples_leaf': 2}` |
| strict | 6.0 | B_Clinical_K | XGBoost | 69 | 44 | 0.227 | 0.020 [-0.006, 0.046] | 0.223 | 35.07 | 861.8 [730.8, 992.7] | 0.207 | `{'learning_rate': 0.01, 'max_depth': 2, 'n_estimators': 30, 'reg_alpha': 0.5, 'reg_lambda': 2.0}` |
| strict | 6.0 | B_Clinical_K | Neural_Network | 69 | 44 | 0.574 | 0.178 [-0.339, 0.695] | 0.525 | 23.08 | 583.0 [440.9, 725.1] | 0.396 | `{'hidden_layer_sizes': (80,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| strict | 6.0 | B_Clinical_K | Lasso | 69 | 44 | 0.361 | 0.190 [-0.039, 0.419] | 0.553 | 26.96 | 735.1 [623.0, 847.2] | 0.171 | `{'alpha': 1.0}` |
| strict | 6.0 | B_Clinical_K | ElasticNet | 69 | 44 | 0.359 | 0.209 [-0.001, 0.419] | 0.563 | 26.92 | 728.2 [612.3, 844.2] | 0.150 | `{'alpha': 0.1, 'l1_ratio': 0.3}` |
| strict | 6.0 | B_Clinical_K | Ridge | 69 | 44 | 0.352 | 0.221 [0.039, 0.403] | 0.569 | 27.34 | 725.7 [602.8, 848.6] | 0.131 | `{'alpha': 10.0}` |
| strict | 6.0 | C1_Combined_K | SVM | 69 | 44 | 0.501 | 0.304 [-0.077, 0.685] | 0.608 | 21.38 | 545.1 [372.9, 717.3] | 0.197 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.03}` |
| strict | 6.0 | C1_Combined_K | Random_Forest | 69 | 44 | 0.729 | 0.276 [-0.346, 0.898] | 0.696 | 24.11 | 625.0 [462.8, 787.2] | 0.453 | `{'n_estimators': 300, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 4}` |
| strict | 6.0 | C1_Combined_K | XGBoost | 69 | 44 | 0.999 | 0.195 [-0.377, 0.768] | 0.632 | 24.23 | 660.0 [476.0, 843.9] | 0.804 | `{'learning_rate': 0.1, 'max_depth': 4, 'n_estimators': 100, 'reg_alpha': 1.0, 'reg_lambda': 0.5}` |
| strict | 6.0 | C1_Combined_K | Neural_Network | 69 | 44 | 0.620 | 0.431 [0.195, 0.667] | 0.727 | 22.37 | 548.2 [342.1, 754.2] | 0.189 | `{'hidden_layer_sizes': (60,), 'alpha': 1.0, 'learning_rate_init': 0.001}` |
| strict | 6.0 | C1_Combined_K | Lasso | 69 | 44 | 0.417 | 0.267 [0.111, 0.423] | 0.603 | 26.40 | 702.6 [604.0, 801.2] | 0.150 | `{'alpha': 1.0}` |
| strict | 6.0 | C1_Combined_K | ElasticNet | 69 | 44 | 0.377 | 0.289 [0.149, 0.429] | 0.614 | 23.08 | 594.7 [384.4, 805.1] | 0.088 | `{'alpha': 1.0, 'l1_ratio': 0.1}` |
| strict | 6.0 | C1_Combined_K | Ridge | 69 | 44 | 0.406 | 0.291 [0.133, 0.450] | 0.614 | 25.95 | 691.3 [583.2, 799.3] | 0.115 | `{'alpha': 10.0}` |
| lenient | 1.0 | A1_Biomechanical_Core_K | SVM | 71 | 46 | 0.386 | 0.362 [0.083, 0.641] | 0.650 | 10.16 | 519.9 [255.9, 783.8] | 0.025 | `{'C': 5000, 'epsilon': 800, 'gamma': 0.01}` |
| lenient | 1.0 | A1_Biomechanical_Core_K | Random_Forest | 71 | 46 | 0.740 | 0.451 [0.338, 0.564] | 0.713 | 11.14 | 543.1 [380.2, 706.0] | 0.289 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| lenient | 1.0 | A1_Biomechanical_Core_K | XGBoost | 71 | 46 | 0.721 | 0.515 [0.395, 0.635] | 0.745 | 10.53 | 511.7 [348.7, 674.8] | 0.206 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 1.0}` |
| lenient | 1.0 | A1_Biomechanical_Core_K | Neural_Network | 71 | 46 | 0.650 | 0.397 [0.169, 0.626] | 0.694 | 10.61 | 550.5 [434.0, 667.0] | 0.253 | `{'hidden_layer_sizes': (60,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| lenient | 1.0 | A1_Biomechanical_Core_K | Lasso | 71 | 46 | 0.559 | 0.436 [0.214, 0.658] | 0.741 | 11.73 | 526.7 [367.1, 686.3] | 0.123 | `{'alpha': 0.01}` |
| lenient | 1.0 | A1_Biomechanical_Core_K | ElasticNet | 71 | 46 | 0.559 | 0.436 [0.214, 0.658] | 0.741 | 11.74 | 526.7 [367.3, 686.2] | 0.123 | `{'alpha': 0.01, 'l1_ratio': 0.9}` |
| lenient | 1.0 | A1_Biomechanical_Core_K | Ridge | 71 | 46 | 0.559 | 0.436 [0.215, 0.657] | 0.741 | 11.74 | 526.7 [367.4, 686.1] | 0.123 | `{'alpha': 0.1}` |
| lenient | 1.0 | A2_Biomechanical_WithK | SVM | 71 | 46 | 0.385 | 0.314 [-0.028, 0.656] | 0.608 | 10.19 | 533.6 [267.3, 799.9] | 0.072 | `{'C': 5000, 'epsilon': 800, 'gamma': 0.01}` |
| lenient | 1.0 | A2_Biomechanical_WithK | Random_Forest | 71 | 46 | 0.755 | 0.440 [0.289, 0.591] | 0.708 | 10.99 | 550.8 [361.1, 740.5] | 0.315 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| lenient | 1.0 | A2_Biomechanical_WithK | XGBoost | 71 | 46 | 0.733 | 0.455 [0.255, 0.654] | 0.729 | 11.03 | 536.7 [369.3, 704.1] | 0.278 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 1.0}` |
| lenient | 1.0 | A2_Biomechanical_WithK | Neural_Network | 71 | 46 | 0.733 | 0.342 [-0.075, 0.758] | 0.732 | 10.02 | 520.0 [401.0, 639.0] | 0.391 | `{'hidden_layer_sizes': (80, 40), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| lenient | 1.0 | A2_Biomechanical_WithK | Lasso | 71 | 46 | 0.592 | 0.452 [0.265, 0.640] | 0.749 | 11.59 | 520.9 [369.2, 672.6] | 0.140 | `{'alpha': 0.01}` |
| lenient | 1.0 | A2_Biomechanical_WithK | ElasticNet | 71 | 46 | 0.592 | 0.453 [0.266, 0.640] | 0.749 | 11.59 | 520.7 [369.1, 672.4] | 0.139 | `{'alpha': 0.01, 'l1_ratio': 0.9}` |
| lenient | 1.0 | A2_Biomechanical_WithK | Ridge | 71 | 46 | 0.592 | 0.453 [0.267, 0.639] | 0.749 | 11.58 | 520.6 [369.0, 672.1] | 0.139 | `{'alpha': 0.1}` |
| lenient | 1.0 | B_Clinical_K | SVM | 71 | 46 | 0.251 | 0.247 [0.050, 0.444] | 0.549 | 11.55 | 577.9 [287.8, 868.0] | 0.004 | `{'C': 5000, 'epsilon': 800, 'gamma': 0.01}` |
| lenient | 1.0 | B_Clinical_K | Random_Forest | 71 | 46 | 0.723 | 0.374 [0.086, 0.661] | 0.720 | 12.31 | 547.4 [392.0, 702.8] | 0.349 | `{'n_estimators': 100, 'max_depth': 2, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| lenient | 1.0 | B_Clinical_K | XGBoost | 71 | 46 | 0.653 | 0.279 [0.133, 0.425] | 0.650 | 11.58 | 572.4 [405.5, 739.3] | 0.374 | `{'learning_rate': 0.01, 'max_depth': 4, 'n_estimators': 100, 'reg_alpha': 2.0, 'reg_lambda': 2.0}` |
| lenient | 1.0 | B_Clinical_K | Neural_Network | 71 | 46 | 0.441 | 0.269 [0.005, 0.533] | 0.694 | 12.30 | 581.7 [393.7, 769.7] | 0.172 | `{'hidden_layer_sizes': (60,), 'alpha': 1.0, 'learning_rate_init': 0.001}` |
| lenient | 1.0 | B_Clinical_K | Lasso | 71 | 46 | 0.458 | 0.201 [-0.218, 0.620] | 0.630 | 13.37 | 618.0 [345.8, 890.1] | 0.257 | `{'alpha': 0.001}` |
| lenient | 1.0 | B_Clinical_K | ElasticNet | 71 | 46 | 0.415 | 0.240 [-0.154, 0.635] | 0.645 | 12.88 | 602.2 [345.5, 858.8] | 0.174 | `{'alpha': 1.0, 'l1_ratio': 0.5}` |
| lenient | 1.0 | B_Clinical_K | Ridge | 71 | 46 | 0.458 | 0.201 [-0.218, 0.621] | 0.630 | 13.36 | 617.9 [345.8, 890.0] | 0.257 | `{'alpha': 0.01}` |
| lenient | 1.0 | C1_Combined_K | SVM | 71 | 46 | 0.419 | 0.372 [0.136, 0.608] | 0.664 | 10.45 | 517.0 [265.2, 768.8] | 0.047 | `{'C': 5000, 'epsilon': 800, 'gamma': 0.01}` |
| lenient | 1.0 | C1_Combined_K | Random_Forest | 71 | 46 | 0.759 | 0.422 [0.109, 0.735] | 0.748 | 11.88 | 528.4 [369.9, 686.9] | 0.337 | `{'n_estimators': 100, 'max_depth': 2, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| lenient | 1.0 | C1_Combined_K | XGBoost | 71 | 46 | 0.659 | 0.413 [0.274, 0.551] | 0.770 | 11.37 | 544.8 [322.5, 767.0] | 0.246 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 50, 'reg_alpha': 2.0, 'reg_lambda': 0.1}` |
| lenient | 1.0 | C1_Combined_K | Neural_Network | 71 | 46 | 0.666 | 0.419 [0.317, 0.522] | 0.720 | 9.95 | 499.4 [286.0, 712.7] | 0.246 | `{'hidden_layer_sizes': (60,), 'alpha': 0.5, 'learning_rate_init': 0.0001}` |
| lenient | 1.0 | C1_Combined_K | Lasso | 71 | 46 | 0.617 | 0.390 [0.258, 0.522] | 0.753 | 9.59 | 496.6 [329.2, 664.1] | 0.227 | `{'alpha': 1.0}` |
| lenient | 1.0 | C1_Combined_K | ElasticNet | 71 | 46 | 0.593 | 0.435 [0.298, 0.573] | 0.761 | 9.76 | 498.1 [252.0, 744.2] | 0.157 | `{'alpha': 1.0, 'l1_ratio': 0.7}` |
| lenient | 1.0 | C1_Combined_K | Ridge | 71 | 46 | 0.608 | 0.444 [0.344, 0.545] | 0.761 | 9.52 | 489.6 [269.1, 710.0] | 0.163 | `{'alpha': 10.0}` |
| lenient | 1.5 | A1_Biomechanical_Core_K | SVM | 71 | 46 | 0.583 | 0.408 [0.143, 0.672] | 0.674 | 11.15 | 593.4 [207.2, 979.6] | 0.175 | `{'C': 5000, 'epsilon': 100, 'gamma': 0.05}` |
| lenient | 1.5 | A1_Biomechanical_Core_K | Random_Forest | 71 | 46 | 0.748 | 0.550 [0.295, 0.805] | 0.760 | 8.56 | 477.0 [236.5, 717.5] | 0.198 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| lenient | 1.5 | A1_Biomechanical_Core_K | XGBoost | 71 | 46 | 0.784 | 0.563 [0.310, 0.817] | 0.767 | 9.21 | 476.6 [226.5, 726.7] | 0.221 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 1.0}` |
| lenient | 1.5 | A1_Biomechanical_Core_K | Neural_Network | 71 | 46 | 0.633 | 0.485 [0.190, 0.779] | 0.701 | 9.06 | 509.8 [244.6, 774.9] | 0.148 | `{'hidden_layer_sizes': (80,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| lenient | 1.5 | A1_Biomechanical_Core_K | Lasso | 71 | 46 | 0.591 | 0.534 [0.293, 0.775] | 0.743 | 8.84 | 488.5 [247.8, 729.1] | 0.057 | `{'alpha': 10.0}` |
| lenient | 1.5 | A1_Biomechanical_Core_K | ElasticNet | 71 | 46 | 0.592 | 0.530 [0.291, 0.769] | 0.741 | 8.94 | 490.6 [254.3, 726.9] | 0.062 | `{'alpha': 0.001, 'l1_ratio': 0.5}` |
| lenient | 1.5 | A1_Biomechanical_Core_K | Ridge | 71 | 46 | 0.635 | 0.469 [0.375, 0.563] | 0.766 | 9.99 | 439.7 [271.5, 607.9] | 0.167 | `{'alpha': 0.1}` |
| lenient | 1.5 | A2_Biomechanical_WithK | SVM | 71 | 46 | 0.504 | 0.400 [0.211, 0.589] | 0.751 | 13.07 | 536.3 [209.8, 862.8] | 0.104 | `{'C': 2000, 'epsilon': 800, 'gamma': 0.03}` |
| lenient | 1.5 | A2_Biomechanical_WithK | Random_Forest | 71 | 46 | 0.763 | 0.537 [0.252, 0.823] | 0.742 | 9.05 | 482.9 [216.5, 749.3] | 0.225 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| lenient | 1.5 | A2_Biomechanical_WithK | XGBoost | 71 | 46 | 0.799 | 0.551 [0.310, 0.791] | 0.759 | 9.57 | 481.3 [252.8, 709.9] | 0.249 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 1.0}` |
| lenient | 1.5 | A2_Biomechanical_WithK | Neural_Network | 71 | 46 | 0.679 | 0.325 [-0.111, 0.760] | 0.614 | 11.00 | 567.1 [409.5, 724.6] | 0.355 | `{'hidden_layer_sizes': (80,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| lenient | 1.5 | A2_Biomechanical_WithK | Lasso | 71 | 46 | 0.728 | 0.574 [0.450, 0.697] | 0.819 | 9.03 | 380.4 [265.3, 495.5] | 0.154 | `{'alpha': 0.01}` |
| lenient | 1.5 | A2_Biomechanical_WithK | ElasticNet | 71 | 46 | 0.728 | 0.574 [0.452, 0.696] | 0.819 | 9.04 | 380.6 [265.2, 495.9] | 0.154 | `{'alpha': 0.01, 'l1_ratio': 0.9}` |
| lenient | 1.5 | A2_Biomechanical_WithK | Ridge | 71 | 46 | 0.728 | 0.574 [0.453, 0.695] | 0.819 | 9.04 | 380.7 [265.2, 496.3] | 0.154 | `{'alpha': 0.1}` |
| lenient | 1.5 | B_Clinical_K | SVM | 71 | 46 | 0.344 | 0.325 [0.117, 0.533] | 0.756 | 9.38 | 527.0 [217.2, 836.8] | 0.020 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 1.5 | B_Clinical_K | Random_Forest | 71 | 46 | 0.705 | 0.358 [0.191, 0.526] | 0.629 | 10.44 | 529.7 [265.0, 794.4] | 0.347 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 1.5 | B_Clinical_K | XGBoost | 71 | 46 | 0.791 | 0.188 [0.069, 0.307] | 0.578 | 13.88 | 655.0 [453.7, 856.3] | 0.602 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 1.0}` |
| lenient | 1.5 | B_Clinical_K | Neural_Network | 71 | 46 | 0.387 | 0.199 [0.016, 0.382] | 0.609 | 12.02 | 582.8 [345.5, 820.0] | 0.188 | `{'hidden_layer_sizes': (80,), 'alpha': 0.5, 'learning_rate_init': 0.001}` |
| lenient | 1.5 | B_Clinical_K | Lasso | 71 | 46 | 0.343 | 0.279 [0.117, 0.442] | 0.575 | 12.11 | 567.5 [262.8, 872.1] | 0.064 | `{'alpha': 10.0}` |
| lenient | 1.5 | B_Clinical_K | ElasticNet | 71 | 46 | 0.506 | 0.254 [-0.136, 0.644] | 0.655 | 11.06 | 562.9 [383.8, 741.9] | 0.252 | `{'alpha': 1.0, 'l1_ratio': 0.5}` |
| lenient | 1.5 | B_Clinical_K | Ridge | 71 | 46 | 0.506 | 0.298 [0.062, 0.533] | 0.777 | 9.70 | 512.8 [273.7, 751.9] | 0.208 | `{'alpha': 10.0}` |
| lenient | 1.5 | C1_Combined_K | SVM | 71 | 46 | 0.428 | 0.420 [0.204, 0.636] | 0.753 | 8.62 | 492.3 [180.6, 804.0] | 0.008 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 1.5 | C1_Combined_K | Random_Forest | 71 | 46 | 0.748 | 0.517 [0.275, 0.759] | 0.737 | 9.16 | 496.9 [271.5, 722.3] | 0.231 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| lenient | 1.5 | C1_Combined_K | XGBoost | 71 | 46 | 0.719 | 0.414 [0.201, 0.626] | 0.788 | 9.88 | 495.8 [220.2, 771.4] | 0.306 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 30, 'reg_alpha': 1.0, 'reg_lambda': 0.1}` |
| lenient | 1.5 | C1_Combined_K | Neural_Network | 71 | 46 | 0.760 | 0.394 [0.202, 0.586] | 0.791 | 9.73 | 478.4 [294.1, 662.8] | 0.366 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.5, 'learning_rate_init': 0.0005}` |
| lenient | 1.5 | C1_Combined_K | Lasso | 71 | 46 | 0.617 | 0.612 [0.359, 0.864] | 0.780 | 8.07 | 447.8 [183.5, 712.0] | 0.005 | `{'alpha': 10.0}` |
| lenient | 1.5 | C1_Combined_K | ElasticNet | 71 | 46 | 0.618 | 0.606 [0.358, 0.854] | 0.779 | 8.23 | 451.9 [192.2, 711.7] | 0.012 | `{'alpha': 0.001, 'l1_ratio': 0.5}` |
| lenient | 1.5 | C1_Combined_K | Ridge | 71 | 46 | 0.657 | 0.470 [0.387, 0.554] | 0.783 | 10.00 | 438.7 [274.9, 602.5] | 0.186 | `{'alpha': 0.1}` |
| lenient | 2.0 | A1_Biomechanical_Core_K | SVM | 71 | 46 | 0.372 | 0.288 [0.158, 0.419] | 0.692 | 9.96 | 465.3 [207.6, 723.0] | 0.084 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 2.0 | A1_Biomechanical_Core_K | Random_Forest | 71 | 46 | 0.697 | 0.455 [0.209, 0.700] | 0.700 | 9.59 | 455.1 [230.5, 679.7] | 0.242 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| lenient | 2.0 | A1_Biomechanical_Core_K | XGBoost | 71 | 46 | 0.725 | 0.426 [0.165, 0.686] | 0.692 | 9.79 | 462.6 [256.1, 669.0] | 0.299 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 1.0}` |
| lenient | 2.0 | A1_Biomechanical_Core_K | Neural_Network | 71 | 46 | 0.525 | 0.402 [0.103, 0.700] | 0.657 | 10.37 | 474.7 [224.8, 724.6] | 0.123 | `{'hidden_layer_sizes': (80,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| lenient | 2.0 | A1_Biomechanical_Core_K | Lasso | 71 | 46 | 0.518 | 0.462 [0.213, 0.710] | 0.691 | 9.76 | 449.2 [228.5, 670.0] | 0.056 | `{'alpha': 10.0}` |
| lenient | 2.0 | A1_Biomechanical_Core_K | ElasticNet | 71 | 46 | 0.519 | 0.457 [0.205, 0.708] | 0.687 | 9.94 | 450.5 [232.7, 668.3] | 0.062 | `{'alpha': 0.001, 'l1_ratio': 0.5}` |
| lenient | 2.0 | A1_Biomechanical_Core_K | Ridge | 71 | 46 | 0.449 | 0.349 [0.170, 0.528] | 0.672 | 11.53 | 444.2 [305.6, 582.7] | 0.100 | `{'alpha': 1.0}` |
| lenient | 2.0 | A2_Biomechanical_WithK | SVM | 71 | 46 | 0.384 | 0.283 [0.126, 0.440] | 0.685 | 10.11 | 465.0 [209.8, 720.2] | 0.101 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 2.0 | A2_Biomechanical_WithK | Random_Forest | 71 | 46 | 0.723 | 0.458 [0.160, 0.756] | 0.697 | 9.55 | 452.3 [207.2, 697.5] | 0.265 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| lenient | 2.0 | A2_Biomechanical_WithK | XGBoost | 71 | 46 | 0.762 | 0.441 [0.158, 0.725] | 0.724 | 9.77 | 450.8 [252.4, 649.2] | 0.320 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 1.0}` |
| lenient | 2.0 | A2_Biomechanical_WithK | Neural_Network | 71 | 46 | 0.632 | 0.326 [0.099, 0.553] | 0.620 | 11.25 | 493.2 [336.9, 649.6] | 0.306 | `{'hidden_layer_sizes': (80,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| lenient | 2.0 | A2_Biomechanical_WithK | Lasso | 71 | 46 | 0.583 | 0.497 [0.278, 0.716] | 0.711 | 9.49 | 436.8 [225.9, 647.8] | 0.086 | `{'alpha': 10.0}` |
| lenient | 2.0 | A2_Biomechanical_WithK | ElasticNet | 71 | 46 | 0.584 | 0.520 [0.314, 0.726] | 0.730 | 9.46 | 427.8 [219.5, 636.0] | 0.064 | `{'alpha': 0.001, 'l1_ratio': 0.5}` |
| lenient | 2.0 | A2_Biomechanical_WithK | Ridge | 71 | 46 | 0.533 | 0.462 [0.206, 0.718] | 0.703 | 10.57 | 398.2 [244.4, 551.9] | 0.071 | `{'alpha': 1.0}` |
| lenient | 2.0 | B_Clinical_K | SVM | 71 | 46 | 0.217 | 0.237 [0.111, 0.362] | 0.616 | 14.34 | 513.5 [266.6, 760.3] | -0.020 | `{'C': 5000, 'epsilon': 800, 'gamma': 0.01}` |
| lenient | 2.0 | B_Clinical_K | Random_Forest | 71 | 46 | 0.661 | 0.262 [0.074, 0.451] | 0.564 | 12.52 | 499.5 [263.3, 735.7] | 0.399 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 2.0 | B_Clinical_K | XGBoost | 71 | 46 | 0.581 | 0.165 [-0.069, 0.398] | 0.574 | 13.53 | 561.3 [371.0, 751.6] | 0.416 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 50, 'reg_alpha': 2.0, 'reg_lambda': 0.1}` |
| lenient | 2.0 | B_Clinical_K | Neural_Network | 71 | 46 | 0.348 | 0.302 [0.215, 0.389] | 0.613 | 12.77 | 489.0 [270.4, 707.6] | 0.046 | `{'hidden_layer_sizes': (80,), 'alpha': 0.5, 'learning_rate_init': 0.001}` |
| lenient | 2.0 | B_Clinical_K | Lasso | 71 | 46 | 0.312 | 0.281 [0.144, 0.418] | 0.551 | 12.95 | 503.4 [241.7, 765.1] | 0.031 | `{'alpha': 10.0}` |
| lenient | 2.0 | B_Clinical_K | ElasticNet | 71 | 46 | 0.445 | 0.302 [0.022, 0.581] | 0.635 | 11.19 | 504.6 [354.1, 655.2] | 0.143 | `{'alpha': 1.0, 'l1_ratio': 0.5}` |
| lenient | 2.0 | B_Clinical_K | Ridge | 71 | 46 | 0.496 | 0.240 [-0.187, 0.666] | 0.632 | 12.12 | 511.1 [365.3, 656.8] | 0.257 | `{'alpha': 1.0}` |
| lenient | 2.0 | C1_Combined_K | SVM | 71 | 46 | 0.510 | 0.370 [0.316, 0.424] | 0.685 | 10.89 | 488.7 [342.0, 635.4] | 0.140 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 2.0 | C1_Combined_K | Random_Forest | 71 | 46 | 0.698 | 0.421 [0.175, 0.667] | 0.677 | 9.76 | 467.9 [248.4, 687.4] | 0.277 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| lenient | 2.0 | C1_Combined_K | XGBoost | 71 | 46 | 0.641 | 0.369 [0.085, 0.652] | 0.645 | 10.88 | 437.2 [259.3, 615.0] | 0.272 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 2.0}` |
| lenient | 2.0 | C1_Combined_K | Neural_Network | 71 | 46 | 0.660 | 0.293 [0.082, 0.504] | 0.691 | 10.52 | 428.2 [263.5, 593.0] | 0.367 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.5, 'learning_rate_init': 0.0005}` |
| lenient | 2.0 | C1_Combined_K | Lasso | 71 | 46 | 0.544 | 0.505 [0.309, 0.702] | 0.718 | 9.64 | 433.8 [230.2, 637.4] | 0.039 | `{'alpha': 10.0}` |
| lenient | 2.0 | C1_Combined_K | ElasticNet | 71 | 46 | 0.545 | 0.493 [0.304, 0.683] | 0.712 | 9.91 | 438.4 [241.0, 635.7] | 0.052 | `{'alpha': 0.001, 'l1_ratio': 0.5}` |
| lenient | 2.0 | C1_Combined_K | Ridge | 71 | 46 | 0.471 | 0.368 [0.173, 0.563] | 0.680 | 11.34 | 438.2 [292.9, 583.5] | 0.103 | `{'alpha': 1.0}` |
| lenient | 2.5 | A1_Biomechanical_Core_K | SVM | 71 | 46 | 0.492 | 0.302 [0.122, 0.483] | 0.624 | 13.88 | 492.2 [340.3, 644.1] | 0.190 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 2.5 | A1_Biomechanical_Core_K | Random_Forest | 71 | 46 | 0.571 | 0.235 [-0.030, 0.501] | 0.535 | 13.68 | 457.0 [329.6, 584.4] | 0.336 | `{'n_estimators': 50, 'max_depth': 2, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 2.5 | A1_Biomechanical_Core_K | XGBoost | 71 | 46 | 0.601 | 0.176 [-0.147, 0.499] | 0.588 | 14.30 | 521.6 [398.3, 644.8] | 0.425 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 50, 'reg_alpha': 2.0, 'reg_lambda': 0.1}` |
| lenient | 2.5 | A1_Biomechanical_Core_K | Neural_Network | 71 | 46 | 0.562 | 0.329 [0.184, 0.474] | 0.639 | 12.99 | 481.5 [338.9, 624.1] | 0.232 | `{'hidden_layer_sizes': (80,), 'alpha': 0.3, 'learning_rate_init': 0.0001}` |
| lenient | 2.5 | A1_Biomechanical_Core_K | Lasso | 71 | 46 | 0.510 | 0.376 [0.169, 0.583] | 0.654 | 13.05 | 465.1 [314.9, 615.3] | 0.135 | `{'alpha': 10.0}` |
| lenient | 2.5 | A1_Biomechanical_Core_K | ElasticNet | 71 | 46 | 0.511 | 0.357 [0.140, 0.573] | 0.643 | 13.34 | 472.4 [317.9, 626.9] | 0.155 | `{'alpha': 0.1, 'l1_ratio': 0.9}` |
| lenient | 2.5 | A1_Biomechanical_Core_K | Ridge | 71 | 46 | 0.447 | 0.294 [0.224, 0.365] | 0.605 | 12.46 | 457.8 [285.8, 629.9] | 0.153 | `{'alpha': 1.0}` |
| lenient | 2.5 | A2_Biomechanical_WithK | SVM | 71 | 46 | 0.561 | 0.270 [0.128, 0.412] | 0.592 | 13.94 | 507.7 [344.1, 671.2] | 0.290 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 2.5 | A2_Biomechanical_WithK | Random_Forest | 71 | 46 | 0.604 | 0.217 [-0.008, 0.441] | 0.521 | 13.63 | 460.8 [352.0, 569.7] | 0.387 | `{'n_estimators': 50, 'max_depth': 2, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 2.5 | A2_Biomechanical_WithK | XGBoost | 71 | 46 | 0.675 | 0.298 [0.038, 0.558] | 0.676 | 11.74 | 403.8 [287.4, 520.2] | 0.377 | `{'learning_rate': 0.01, 'max_depth': 4, 'n_estimators': 100, 'reg_alpha': 2.0, 'reg_lambda': 2.0}` |
| lenient | 2.5 | A2_Biomechanical_WithK | Neural_Network | 71 | 46 | 0.522 | 0.215 [-0.137, 0.568] | 0.659 | 13.22 | 430.0 [270.6, 589.5] | 0.307 | `{'hidden_layer_sizes': (80, 40), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| lenient | 2.5 | A2_Biomechanical_WithK | Lasso | 71 | 46 | 0.591 | 0.476 [0.144, 0.808] | 0.723 | 11.98 | 411.2 [232.5, 589.9] | 0.115 | `{'alpha': 10.0}` |
| lenient | 2.5 | A2_Biomechanical_WithK | ElasticNet | 71 | 46 | 0.593 | 0.473 [0.114, 0.832] | 0.726 | 11.97 | 410.2 [218.5, 601.9] | 0.120 | `{'alpha': 0.1, 'l1_ratio': 0.9}` |
| lenient | 2.5 | A2_Biomechanical_WithK | Ridge | 71 | 46 | 0.516 | 0.316 [-0.065, 0.697] | 0.637 | 12.22 | 415.7 [289.7, 541.7] | 0.200 | `{'alpha': 1.0}` |
| lenient | 2.5 | B_Clinical_K | SVM | 71 | 46 | 0.301 | 0.044 [-0.317, 0.405] | 0.463 | 14.20 | 505.8 [380.4, 631.1] | 0.257 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 2.5 | B_Clinical_K | Random_Forest | 71 | 46 | 0.578 | 0.101 [-0.034, 0.235] | 0.422 | 13.87 | 479.0 [272.9, 685.1] | 0.477 | `{'n_estimators': 200, 'max_depth': 5, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| lenient | 2.5 | B_Clinical_K | XGBoost | 71 | 46 | 0.549 | 0.173 [-0.035, 0.380] | 0.602 | 15.44 | 533.1 [383.2, 682.9] | 0.376 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 50, 'reg_alpha': 2.0, 'reg_lambda': 0.1}` |
| lenient | 2.5 | B_Clinical_K | Neural_Network | 71 | 46 | 0.357 | 0.153 [-0.204, 0.509] | 0.603 | 13.46 | 468.6 [346.6, 590.6] | 0.205 | `{'hidden_layer_sizes': (100,), 'alpha': 0.3, 'learning_rate_init': 0.0005}` |
| lenient | 2.5 | B_Clinical_K | Lasso | 71 | 46 | 0.436 | 0.156 [-0.420, 0.733] | 0.579 | 13.93 | 500.2 [386.8, 613.6] | 0.280 | `{'alpha': 0.1}` |
| lenient | 2.5 | B_Clinical_K | ElasticNet | 71 | 46 | 0.392 | 0.237 [-0.013, 0.488] | 0.571 | 13.59 | 493.9 [414.2, 573.5] | 0.154 | `{'alpha': 1.0, 'l1_ratio': 0.5}` |
| lenient | 2.5 | B_Clinical_K | Ridge | 71 | 46 | 0.407 | 0.190 [-0.023, 0.402] | 0.648 | 13.05 | 472.3 [346.3, 598.2] | 0.217 | `{'alpha': 10.0}` |
| lenient | 2.5 | C1_Combined_K | SVM | 71 | 46 | 0.527 | 0.385 [0.232, 0.537] | 0.695 | 12.75 | 464.8 [312.7, 617.0] | 0.142 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 2.5 | C1_Combined_K | Random_Forest | 71 | 46 | 0.571 | 0.217 [-0.071, 0.504] | 0.516 | 13.70 | 461.5 [331.7, 591.3] | 0.355 | `{'n_estimators': 50, 'max_depth': 2, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 2.5 | C1_Combined_K | XGBoost | 71 | 46 | 0.640 | 0.201 [-0.054, 0.457] | 0.631 | 14.44 | 513.0 [410.6, 615.5] | 0.438 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 50, 'reg_alpha': 2.0, 'reg_lambda': 0.1}` |
| lenient | 2.5 | C1_Combined_K | Neural_Network | 71 | 46 | 0.573 | 0.272 [0.048, 0.497] | 0.660 | 14.93 | 496.4 [369.8, 623.0] | 0.300 | `{'hidden_layer_sizes': (80,), 'alpha': 0.3, 'learning_rate_init': 0.0001}` |
| lenient | 2.5 | C1_Combined_K | Lasso | 71 | 46 | 0.532 | 0.418 [0.303, 0.533] | 0.695 | 12.23 | 450.8 [317.7, 583.8] | 0.114 | `{'alpha': 10.0}` |
| lenient | 2.5 | C1_Combined_K | ElasticNet | 71 | 46 | 0.533 | 0.410 [0.281, 0.539] | 0.691 | 12.32 | 454.4 [315.0, 593.8] | 0.123 | `{'alpha': 0.1, 'l1_ratio': 0.9}` |
| lenient | 2.5 | C1_Combined_K | Ridge | 71 | 46 | 0.385 | 0.281 [0.152, 0.410] | 0.694 | 14.42 | 500.6 [354.7, 646.6] | 0.104 | `{'alpha': 100.0}` |
| lenient | 3.0 | A1_Biomechanical_Core_K | SVM | 71 | 46 | 0.389 | 0.253 [0.002, 0.504] | 0.600 | 14.27 | 549.6 [325.9, 773.3] | 0.136 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 3.0 | A1_Biomechanical_Core_K | Random_Forest | 71 | 46 | 0.636 | 0.309 [-0.064, 0.682] | 0.604 | 14.04 | 534.0 [295.7, 772.3] | 0.327 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| lenient | 3.0 | A1_Biomechanical_Core_K | XGBoost | 71 | 46 | 0.611 | 0.321 [0.022, 0.620] | 0.607 | 13.79 | 515.2 [286.6, 743.7] | 0.290 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 2.0}` |
| lenient | 3.0 | A1_Biomechanical_Core_K | Neural_Network | 71 | 46 | 0.532 | 0.313 [-0.167, 0.792] | 0.617 | 14.97 | 515.8 [227.5, 804.1] | 0.220 | `{'hidden_layer_sizes': (60,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| lenient | 3.0 | A1_Biomechanical_Core_K | Lasso | 71 | 46 | 0.479 | 0.423 [0.021, 0.825] | 0.640 | 11.76 | 472.9 [204.5, 741.2] | 0.056 | `{'alpha': 0.1}` |
| lenient | 3.0 | A1_Biomechanical_Core_K | ElasticNet | 71 | 46 | 0.479 | 0.423 [0.021, 0.824] | 0.640 | 11.77 | 472.9 [204.6, 741.1] | 0.056 | `{'alpha': 0.01, 'l1_ratio': 0.9}` |
| lenient | 3.0 | A1_Biomechanical_Core_K | Ridge | 71 | 46 | 0.479 | 0.422 [0.026, 0.818] | 0.640 | 11.83 | 473.7 [207.9, 739.5] | 0.057 | `{'alpha': 1.0}` |
| lenient | 3.0 | A2_Biomechanical_WithK | SVM | 71 | 46 | 0.567 | 0.325 [0.044, 0.606] | 0.640 | 13.59 | 531.0 [271.6, 790.5] | 0.242 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 3.0 | A2_Biomechanical_WithK | Random_Forest | 71 | 46 | 0.597 | 0.312 [0.007, 0.616] | 0.592 | 14.64 | 513.2 [301.9, 724.5] | 0.285 | `{'n_estimators': 50, 'max_depth': 2, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 3.0 | A2_Biomechanical_WithK | XGBoost | 71 | 46 | 0.707 | 0.344 [0.052, 0.636] | 0.625 | 14.35 | 506.7 [283.9, 729.5] | 0.363 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 2.0}` |
| lenient | 3.0 | A2_Biomechanical_WithK | Neural_Network | 71 | 46 | 0.628 | 0.310 [0.044, 0.575] | 0.637 | 15.81 | 525.4 [356.4, 694.4] | 0.318 | `{'hidden_layer_sizes': (80,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| lenient | 3.0 | A2_Biomechanical_WithK | Lasso | 71 | 46 | 0.808 | 0.495 [0.029, 0.961] | 0.781 | 10.92 | 322.3 [225.6, 418.9] | 0.313 | `{'alpha': 0.01}` |
| lenient | 3.0 | A2_Biomechanical_WithK | ElasticNet | 71 | 46 | 0.808 | 0.495 [0.029, 0.961] | 0.781 | 10.93 | 322.3 [225.7, 418.8] | 0.313 | `{'alpha': 0.01, 'l1_ratio': 0.9}` |
| lenient | 3.0 | A2_Biomechanical_WithK | Ridge | 71 | 46 | 0.808 | 0.495 [0.029, 0.961] | 0.781 | 10.93 | 322.2 [225.9, 418.6] | 0.313 | `{'alpha': 0.1}` |
| lenient | 3.0 | B_Clinical_K | SVM | 71 | 46 | 0.324 | 0.207 [0.077, 0.336] | 0.644 | 15.27 | 510.0 [325.4, 694.7] | 0.118 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 3.0 | B_Clinical_K | Random_Forest | 71 | 46 | 0.729 | 0.238 [-0.160, 0.637] | 0.521 | 13.49 | 551.0 [358.9, 743.0] | 0.491 | `{'n_estimators': 300, 'max_depth': 3, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| lenient | 3.0 | B_Clinical_K | XGBoost | 71 | 46 | 0.895 | 0.106 [0.029, 0.183] | 0.535 | 14.93 | 540.7 [354.4, 727.1] | 0.789 | `{'learning_rate': 0.1, 'max_depth': 2, 'n_estimators': 100, 'reg_alpha': 0.1, 'reg_lambda': 2.0}` |
| lenient | 3.0 | B_Clinical_K | Neural_Network | 71 | 46 | 0.502 | 0.115 [-0.329, 0.558] | 0.507 | 18.77 | 602.3 [267.5, 937.0] | 0.387 | `{'hidden_layer_sizes': (60,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| lenient | 3.0 | B_Clinical_K | Lasso | 71 | 46 | 0.417 | 0.237 [-0.326, 0.800] | 0.615 | 14.51 | 536.4 [328.1, 744.7] | 0.180 | `{'alpha': 0.1}` |
| lenient | 3.0 | B_Clinical_K | ElasticNet | 71 | 46 | 0.375 | 0.297 [0.015, 0.580] | 0.608 | 14.53 | 531.1 [376.3, 685.9] | 0.078 | `{'alpha': 1.0, 'l1_ratio': 0.5}` |
| lenient | 3.0 | B_Clinical_K | Ridge | 71 | 46 | 0.402 | 0.256 [0.021, 0.491] | 0.688 | 14.00 | 491.2 [315.5, 666.9] | 0.147 | `{'alpha': 10.0}` |
| lenient | 3.0 | C1_Combined_K | SVM | 71 | 46 | 0.414 | 0.341 [0.111, 0.570] | 0.685 | 14.07 | 526.9 [277.9, 775.9] | 0.074 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 3.0 | C1_Combined_K | Random_Forest | 71 | 46 | 0.563 | 0.257 [-0.050, 0.564] | 0.538 | 15.18 | 532.8 [331.1, 734.5] | 0.306 | `{'n_estimators': 50, 'max_depth': 2, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 3.0 | C1_Combined_K | XGBoost | 71 | 46 | 0.614 | 0.281 [-0.037, 0.599] | 0.568 | 14.37 | 526.9 [302.2, 751.5] | 0.333 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 2.0}` |
| lenient | 3.0 | C1_Combined_K | Neural_Network | 71 | 46 | 0.528 | 0.281 [-0.231, 0.794] | 0.594 | 15.60 | 532.3 [226.8, 837.8] | 0.246 | `{'hidden_layer_sizes': (60,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| lenient | 3.0 | C1_Combined_K | Lasso | 71 | 46 | 0.461 | 0.402 [0.017, 0.786] | 0.655 | 12.39 | 492.7 [257.4, 728.0] | 0.059 | `{'alpha': 10.0}` |
| lenient | 3.0 | C1_Combined_K | ElasticNet | 71 | 46 | 0.462 | 0.395 [-0.009, 0.799] | 0.651 | 12.61 | 493.7 [257.8, 729.7] | 0.067 | `{'alpha': 0.001, 'l1_ratio': 0.5}` |
| lenient | 3.0 | C1_Combined_K | Ridge | 71 | 46 | 0.403 | 0.337 [0.094, 0.580] | 0.671 | 13.99 | 509.3 [306.9, 711.6] | 0.065 | `{'alpha': 1.0}` |
| lenient | 3.5 | A1_Biomechanical_Core_K | SVM | 71 | 46 | 0.318 | 0.257 [-0.211, 0.725] | 0.602 | 14.18 | 575.1 [166.2, 983.9] | 0.061 | `{'C': 5000, 'epsilon': 100, 'gamma': 0.05}` |
| lenient | 3.5 | A1_Biomechanical_Core_K | Random_Forest | 71 | 46 | 0.541 | 0.173 [-0.193, 0.540] | 0.548 | 15.68 | 502.4 [312.9, 691.9] | 0.368 | `{'n_estimators': 50, 'max_depth': 2, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 3.5 | A1_Biomechanical_Core_K | XGBoost | 71 | 46 | 0.367 | 0.188 [-0.153, 0.529] | 0.558 | 16.64 | 529.4 [260.8, 798.0] | 0.179 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 30, 'reg_alpha': 2.0, 'reg_lambda': 0.5}` |
| lenient | 3.5 | A1_Biomechanical_Core_K | Neural_Network | 71 | 46 | 0.371 | 0.316 [0.165, 0.466] | 0.588 | 12.98 | 455.8 [262.2, 649.4] | 0.056 | `{'hidden_layer_sizes': (100,), 'alpha': 0.5, 'learning_rate_init': 0.0001}` |
| lenient | 3.5 | A1_Biomechanical_Core_K | Lasso | 71 | 46 | 0.399 | 0.301 [0.071, 0.531] | 0.567 | 14.07 | 461.8 [246.0, 677.6] | 0.098 | `{'alpha': 0.01}` |
| lenient | 3.5 | A1_Biomechanical_Core_K | ElasticNet | 71 | 46 | 0.441 | 0.264 [-0.054, 0.582] | 0.605 | 13.33 | 484.9 [261.4, 708.4] | 0.177 | `{'alpha': 0.01, 'l1_ratio': 0.9}` |
| lenient | 3.5 | A1_Biomechanical_Core_K | Ridge | 71 | 46 | 0.399 | 0.301 [0.071, 0.530] | 0.567 | 14.07 | 461.7 [246.1, 677.4] | 0.098 | `{'alpha': 0.1}` |
| lenient | 3.5 | A2_Biomechanical_WithK | SVM | 71 | 46 | 0.520 | 0.263 [-0.010, 0.536] | 0.583 | 14.26 | 518.3 [360.1, 676.6] | 0.258 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 3.5 | A2_Biomechanical_WithK | Random_Forest | 71 | 46 | 0.728 | 0.245 [-0.043, 0.534] | 0.618 | 15.45 | 539.5 [362.0, 717.0] | 0.483 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 3.5 | A2_Biomechanical_WithK | XGBoost | 71 | 46 | 0.874 | 0.317 [0.057, 0.577] | 0.617 | 14.52 | 454.8 [249.8, 659.8] | 0.556 | `{'learning_rate': 0.05, 'max_depth': 2, 'n_estimators': 100, 'reg_alpha': 2.0, 'reg_lambda': 1.0}` |
| lenient | 3.5 | A2_Biomechanical_WithK | Neural_Network | 71 | 46 | 0.495 | 0.225 [-0.030, 0.480] | 0.519 | 17.69 | 549.6 [399.3, 699.9] | 0.270 | `{'hidden_layer_sizes': (80,), 'alpha': 0.5, 'learning_rate_init': 0.001}` |
| lenient | 3.5 | A2_Biomechanical_WithK | Lasso | 71 | 46 | 0.526 | 0.412 [0.187, 0.637] | 0.677 | 14.24 | 482.5 [297.4, 667.6] | 0.114 | `{'alpha': 10.0}` |
| lenient | 3.5 | A2_Biomechanical_WithK | ElasticNet | 71 | 46 | 0.527 | 0.402 [0.165, 0.639] | 0.680 | 14.53 | 485.5 [299.0, 671.9] | 0.126 | `{'alpha': 0.001, 'l1_ratio': 0.3}` |
| lenient | 3.5 | A2_Biomechanical_WithK | Ridge | 71 | 46 | 0.527 | 0.328 [0.091, 0.564] | 0.612 | 13.58 | 445.1 [251.7, 638.5] | 0.199 | `{'alpha': 0.1}` |
| lenient | 3.5 | B_Clinical_K | SVM | 71 | 46 | 0.253 | 0.186 [0.039, 0.332] | 0.563 | 15.77 | 532.1 [367.1, 697.1] | 0.068 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 3.5 | B_Clinical_K | Random_Forest | 71 | 46 | 0.840 | 0.049 [-0.524, 0.622] | 0.504 | 17.56 | 563.7 [262.5, 864.9] | 0.791 | `{'n_estimators': 100, 'max_depth': 5, 'min_samples_split': 2, 'min_samples_leaf': 1}` |
| lenient | 3.5 | B_Clinical_K | XGBoost | 71 | 46 | 0.310 | 0.078 [-0.273, 0.429] | 0.539 | 19.10 | 563.1 [290.0, 836.1] | 0.232 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 30, 'reg_alpha': 2.0, 'reg_lambda': 0.5}` |
| lenient | 3.5 | B_Clinical_K | Neural_Network | 71 | 46 | 0.368 | 0.079 [-0.208, 0.367] | 0.412 | 15.38 | 514.4 [344.8, 684.0] | 0.289 | `{'hidden_layer_sizes': (100,), 'alpha': 0.5, 'learning_rate_init': 0.0001}` |
| lenient | 3.5 | B_Clinical_K | Lasso | 71 | 46 | 0.329 | 0.213 [-0.010, 0.436] | 0.585 | 15.05 | 518.9 [360.1, 677.6] | 0.117 | `{'alpha': 1.0}` |
| lenient | 3.5 | B_Clinical_K | ElasticNet | 71 | 46 | 0.361 | 0.219 [-0.092, 0.530] | 0.565 | 15.98 | 527.2 [428.8, 625.7] | 0.142 | `{'alpha': 1.0, 'l1_ratio': 0.5}` |
| lenient | 3.5 | B_Clinical_K | Ridge | 71 | 46 | 0.323 | 0.232 [0.054, 0.409] | 0.587 | 14.75 | 515.1 [355.5, 674.8] | 0.091 | `{'alpha': 10.0}` |
| lenient | 3.5 | C1_Combined_K | SVM | 71 | 46 | 0.412 | 0.263 [0.024, 0.503] | 0.597 | 14.49 | 520.0 [367.0, 673.0] | 0.148 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 3.5 | C1_Combined_K | Random_Forest | 71 | 46 | 0.827 | 0.142 [-0.194, 0.477] | 0.586 | 15.77 | 496.3 [314.4, 678.2] | 0.685 | `{'n_estimators': 300, 'max_depth': 5, 'min_samples_split': 2, 'min_samples_leaf': 2}` |
| lenient | 3.5 | C1_Combined_K | XGBoost | 71 | 46 | 0.372 | 0.160 [-0.197, 0.517] | 0.534 | 16.92 | 537.0 [268.8, 805.2] | 0.212 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 30, 'reg_alpha': 2.0, 'reg_lambda': 0.5}` |
| lenient | 3.5 | C1_Combined_K | Neural_Network | 71 | 46 | 0.482 | 0.219 [-0.038, 0.475] | 0.492 | 15.73 | 480.8 [282.9, 678.7] | 0.263 | `{'hidden_layer_sizes': (100,), 'alpha': 0.5, 'learning_rate_init': 0.0001}` |
| lenient | 3.5 | C1_Combined_K | Lasso | 71 | 46 | 0.457 | 0.295 [-0.048, 0.639] | 0.632 | 14.94 | 501.1 [276.4, 725.8] | 0.162 | `{'alpha': 10.0}` |
| lenient | 3.5 | C1_Combined_K | ElasticNet | 71 | 46 | 0.458 | 0.284 [-0.087, 0.656] | 0.625 | 14.96 | 502.6 [279.0, 726.3] | 0.174 | `{'alpha': 0.001, 'l1_ratio': 0.5}` |
| lenient | 3.5 | C1_Combined_K | Ridge | 71 | 46 | 0.338 | 0.242 [0.065, 0.420] | 0.583 | 14.89 | 513.6 [346.1, 681.0] | 0.096 | `{'alpha': 10.0}` |
| lenient | 4.0 | A1_Biomechanical_Core_K | SVM | 71 | 46 | 0.372 | 0.225 [0.006, 0.445] | 0.550 | 18.01 | 609.2 [423.3, 795.1] | 0.147 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 4.0 | A1_Biomechanical_Core_K | Random_Forest | 71 | 46 | 0.728 | 0.177 [-0.128, 0.482] | 0.470 | 16.80 | 500.9 [349.1, 652.8] | 0.552 | `{'n_estimators': 100, 'max_depth': 4, 'min_samples_split': 10, 'min_samples_leaf': 1}` |
| lenient | 4.0 | A1_Biomechanical_Core_K | XGBoost | 71 | 46 | 0.400 | 0.158 [-0.157, 0.474] | 0.533 | 18.77 | 587.5 [367.8, 807.2] | 0.242 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 30, 'reg_alpha': 2.0, 'reg_lambda': 0.5}` |
| lenient | 4.0 | A1_Biomechanical_Core_K | Neural_Network | 71 | 46 | 0.395 | 0.242 [0.026, 0.458] | 0.584 | 17.13 | 520.2 [319.0, 721.3] | 0.152 | `{'hidden_layer_sizes': (100,), 'alpha': 0.5, 'learning_rate_init': 0.0001}` |
| lenient | 4.0 | A1_Biomechanical_Core_K | Lasso | 71 | 46 | 0.415 | 0.239 [0.048, 0.429] | 0.568 | 17.75 | 522.6 [319.7, 725.5] | 0.176 | `{'alpha': 0.01}` |
| lenient | 4.0 | A1_Biomechanical_Core_K | ElasticNet | 71 | 46 | 0.354 | 0.188 [-0.057, 0.434] | 0.504 | 20.78 | 674.8 [522.0, 827.7] | 0.166 | `{'alpha': 1.0, 'l1_ratio': 0.7}` |
| lenient | 4.0 | A1_Biomechanical_Core_K | Ridge | 71 | 46 | 0.415 | 0.239 [0.048, 0.429] | 0.568 | 17.76 | 522.6 [319.7, 725.4] | 0.176 | `{'alpha': 0.1}` |
| lenient | 4.0 | A2_Biomechanical_WithK | SVM | 71 | 46 | 0.526 | 0.215 [0.016, 0.414] | 0.540 | 18.54 | 618.2 [407.5, 828.9] | 0.311 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 4.0 | A2_Biomechanical_WithK | Random_Forest | 71 | 46 | 0.716 | 0.199 [-0.178, 0.577] | 0.635 | 19.25 | 608.9 [488.8, 729.1] | 0.516 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 4.0 | A2_Biomechanical_WithK | XGBoost | 71 | 46 | 0.427 | 0.141 [-0.185, 0.467] | 0.485 | 18.96 | 587.7 [386.5, 789.0] | 0.286 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 30, 'reg_alpha': 2.0, 'reg_lambda': 0.5}` |
| lenient | 4.0 | A2_Biomechanical_WithK | Neural_Network | 71 | 46 | 0.521 | 0.199 [-0.139, 0.538] | 0.538 | 20.42 | 611.5 [498.4, 724.5] | 0.322 | `{'hidden_layer_sizes': (80,), 'alpha': 0.5, 'learning_rate_init': 0.001}` |
| lenient | 4.0 | A2_Biomechanical_WithK | Lasso | 71 | 46 | 0.494 | 0.384 [0.070, 0.698] | 0.648 | 18.77 | 569.5 [411.5, 727.5] | 0.110 | `{'alpha': 10.0}` |
| lenient | 4.0 | A2_Biomechanical_WithK | ElasticNet | 71 | 46 | 0.570 | 0.368 [-0.056, 0.793] | 0.630 | 17.93 | 503.4 [335.6, 671.1] | 0.202 | `{'alpha': 0.1, 'l1_ratio': 0.9}` |
| lenient | 4.0 | A2_Biomechanical_WithK | Ridge | 71 | 46 | 0.548 | 0.303 [0.058, 0.548] | 0.636 | 17.30 | 488.8 [312.9, 664.7] | 0.245 | `{'alpha': 0.1}` |
| lenient | 4.0 | B_Clinical_K | SVM | 71 | 46 | 0.223 | 0.188 [0.079, 0.298] | 0.600 | 17.70 | 613.4 [413.8, 812.9] | 0.034 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 4.0 | B_Clinical_K | Random_Forest | 71 | 46 | 0.516 | 0.017 [-0.092, 0.127] | 0.306 | 18.74 | 552.3 [365.1, 739.6] | 0.499 | `{'n_estimators': 200, 'max_depth': 5, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| lenient | 4.0 | B_Clinical_K | XGBoost | 71 | 46 | 0.180 | 0.038 [-0.072, 0.148] | 0.341 | 24.61 | 702.3 [504.2, 900.4] | 0.142 | `{'learning_rate': 0.01, 'max_depth': 2, 'n_estimators': 30, 'reg_alpha': 0.5, 'reg_lambda': 2.0}` |
| lenient | 4.0 | B_Clinical_K | Neural_Network | 71 | 46 | 0.349 | 0.126 [-0.055, 0.307] | 0.518 | 20.68 | 621.0 [495.3, 746.6] | 0.223 | `{'hidden_layer_sizes': (100,), 'alpha': 0.3, 'learning_rate_init': 0.0005}` |
| lenient | 4.0 | B_Clinical_K | Lasso | 71 | 46 | 0.336 | 0.219 [-0.065, 0.504] | 0.594 | 19.12 | 595.8 [394.8, 796.7] | 0.117 | `{'alpha': 1.0}` |
| lenient | 4.0 | B_Clinical_K | ElasticNet | 71 | 46 | 0.336 | 0.222 [-0.059, 0.502] | 0.595 | 19.08 | 595.1 [394.5, 795.6] | 0.114 | `{'alpha': 0.1, 'l1_ratio': 0.9}` |
| lenient | 4.0 | B_Clinical_K | Ridge | 71 | 46 | 0.329 | 0.248 [0.052, 0.444] | 0.598 | 18.78 | 588.4 [393.4, 783.4] | 0.081 | `{'alpha': 10.0}` |
| lenient | 4.0 | C1_Combined_K | SVM | 71 | 46 | 0.421 | 0.254 [0.066, 0.442] | 0.591 | 17.92 | 595.3 [437.7, 752.8] | 0.167 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 4.0 | C1_Combined_K | Random_Forest | 71 | 46 | 0.734 | 0.120 [-0.132, 0.371] | 0.415 | 16.93 | 516.9 [380.2, 653.6] | 0.615 | `{'n_estimators': 100, 'max_depth': 4, 'min_samples_split': 10, 'min_samples_leaf': 1}` |
| lenient | 4.0 | C1_Combined_K | XGBoost | 71 | 46 | 0.402 | 0.131 [-0.251, 0.514] | 0.503 | 19.13 | 594.2 [368.4, 820.1] | 0.271 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 30, 'reg_alpha': 2.0, 'reg_lambda': 0.5}` |
| lenient | 4.0 | C1_Combined_K | Neural_Network | 71 | 46 | 0.582 | 0.177 [-0.148, 0.501] | 0.497 | 19.61 | 584.3 [492.8, 675.7] | 0.405 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.3, 'learning_rate_init': 0.0005}` |
| lenient | 4.0 | C1_Combined_K | Lasso | 71 | 46 | 0.478 | 0.275 [0.068, 0.482] | 0.619 | 18.66 | 582.5 [452.2, 712.8] | 0.203 | `{'alpha': 10.0}` |
| lenient | 4.0 | C1_Combined_K | ElasticNet | 71 | 46 | 0.479 | 0.261 [0.029, 0.492] | 0.612 | 18.71 | 587.3 [453.9, 720.7] | 0.218 | `{'alpha': 0.1, 'l1_ratio': 0.9}` |
| lenient | 4.0 | C1_Combined_K | Ridge | 71 | 46 | 0.350 | 0.245 [0.163, 0.327] | 0.626 | 20.31 | 607.0 [424.4, 789.5] | 0.105 | `{'alpha': 100.0}` |
| lenient | 4.5 | A1_Biomechanical_Core_K | SVM | 71 | 46 | 0.415 | 0.249 [-0.015, 0.513] | 0.560 | 18.96 | 606.0 [500.5, 711.6] | 0.166 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 4.5 | A1_Biomechanical_Core_K | Random_Forest | 71 | 46 | 0.592 | 0.133 [-0.334, 0.600] | 0.555 | 19.23 | 591.8 [295.6, 887.9] | 0.459 | `{'n_estimators': 200, 'max_depth': 4, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| lenient | 4.5 | A1_Biomechanical_Core_K | XGBoost | 71 | 46 | 0.466 | 0.133 [-0.019, 0.286] | 0.472 | 22.30 | 623.2 [421.4, 825.1] | 0.332 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 30, 'reg_alpha': 1.0, 'reg_lambda': 0.1}` |
| lenient | 4.5 | A1_Biomechanical_Core_K | Neural_Network | 71 | 46 | 0.459 | 0.259 [0.168, 0.350] | 0.579 | 19.40 | 524.0 [432.7, 615.2] | 0.200 | `{'hidden_layer_sizes': (100,), 'alpha': 0.5, 'learning_rate_init': 0.0001}` |
| lenient | 4.5 | A1_Biomechanical_Core_K | Lasso | 71 | 46 | 0.438 | 0.266 [0.169, 0.363] | 0.622 | 19.63 | 528.1 [386.2, 670.0] | 0.172 | `{'alpha': 0.01}` |
| lenient | 4.5 | A1_Biomechanical_Core_K | ElasticNet | 71 | 46 | 0.458 | 0.236 [-0.123, 0.595] | 0.570 | 19.85 | 601.2 [498.0, 704.5] | 0.221 | `{'alpha': 0.1, 'l1_ratio': 0.9}` |
| lenient | 4.5 | A1_Biomechanical_Core_K | Ridge | 71 | 46 | 0.438 | 0.266 [0.170, 0.363] | 0.622 | 19.63 | 528.1 [386.4, 669.7] | 0.172 | `{'alpha': 0.1}` |
| lenient | 4.5 | A2_Biomechanical_WithK | SVM | 71 | 46 | 0.486 | 0.281 [0.086, 0.477] | 0.594 | 19.11 | 599.9 [469.9, 729.9] | 0.204 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 4.5 | A2_Biomechanical_WithK | Random_Forest | 71 | 46 | 0.863 | 0.182 [-0.195, 0.559] | 0.528 | 20.82 | 541.3 [378.2, 704.5] | 0.680 | `{'n_estimators': 300, 'max_depth': 5, 'min_samples_split': 2, 'min_samples_leaf': 2}` |
| lenient | 4.5 | A2_Biomechanical_WithK | XGBoost | 71 | 46 | 0.481 | 0.117 [-0.026, 0.259] | 0.466 | 22.46 | 629.0 [431.3, 826.7] | 0.365 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 30, 'reg_alpha': 1.0, 'reg_lambda': 0.1}` |
| lenient | 4.5 | A2_Biomechanical_WithK | Neural_Network | 71 | 46 | 0.433 | 0.124 [-0.040, 0.288] | 0.544 | 18.03 | 529.3 [416.4, 642.2] | 0.309 | `{'hidden_layer_sizes': (80, 40), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| lenient | 4.5 | A2_Biomechanical_WithK | Lasso | 71 | 46 | 0.529 | 0.337 [-0.061, 0.735] | 0.631 | 19.11 | 543.8 [405.8, 681.9] | 0.192 | `{'alpha': 10.0}` |
| lenient | 4.5 | A2_Biomechanical_WithK | ElasticNet | 71 | 46 | 0.530 | 0.315 [-0.084, 0.713] | 0.625 | 19.43 | 557.0 [427.7, 686.4] | 0.215 | `{'alpha': 0.1, 'l1_ratio': 0.9}` |
| lenient | 4.5 | A2_Biomechanical_WithK | Ridge | 71 | 46 | 0.514 | 0.297 [0.139, 0.456] | 0.675 | 19.55 | 514.1 [377.3, 650.8] | 0.217 | `{'alpha': 0.1}` |
| lenient | 4.5 | B_Clinical_K | SVM | 71 | 46 | 0.260 | 0.202 [0.142, 0.261] | 0.581 | 19.94 | 645.9 [471.9, 819.8] | 0.058 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 4.5 | B_Clinical_K | Random_Forest | 71 | 46 | 0.627 | -0.021 [-0.345, 0.303] | 0.509 | 22.98 | 643.6 [370.4, 916.8] | 0.648 | `{'n_estimators': 100, 'max_depth': 5, 'min_samples_split': 5, 'min_samples_leaf': 4}` |
| lenient | 4.5 | B_Clinical_K | XGBoost | 71 | 46 | 0.565 | 0.051 [-0.270, 0.372] | 0.519 | 24.25 | 678.2 [576.4, 780.1] | 0.513 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 50, 'reg_alpha': 2.0, 'reg_lambda': 0.1}` |
| lenient | 4.5 | B_Clinical_K | Neural_Network | 71 | 46 | 0.461 | 0.159 [0.061, 0.257] | 0.509 | 22.26 | 661.6 [485.2, 838.0] | 0.302 | `{'hidden_layer_sizes': (100,), 'alpha': 0.3, 'learning_rate_init': 0.0005}` |
| lenient | 4.5 | B_Clinical_K | Lasso | 71 | 46 | 0.382 | 0.225 [-0.049, 0.500] | 0.613 | 20.90 | 625.3 [464.3, 786.4] | 0.157 | `{'alpha': 1.0}` |
| lenient | 4.5 | B_Clinical_K | ElasticNet | 71 | 46 | 0.382 | 0.228 [-0.041, 0.497] | 0.613 | 20.87 | 624.6 [463.3, 785.8] | 0.154 | `{'alpha': 0.1, 'l1_ratio': 0.9}` |
| lenient | 4.5 | B_Clinical_K | Ridge | 71 | 46 | 0.375 | 0.266 [0.103, 0.429] | 0.614 | 20.67 | 615.7 [449.8, 781.5] | 0.109 | `{'alpha': 10.0}` |
| lenient | 4.5 | C1_Combined_K | SVM | 71 | 46 | 0.437 | 0.293 [0.111, 0.476] | 0.624 | 19.00 | 593.2 [484.4, 701.9] | 0.143 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 4.5 | C1_Combined_K | Random_Forest | 71 | 46 | 0.836 | 0.117 [-0.400, 0.633] | 0.510 | 20.55 | 556.0 [400.9, 711.1] | 0.719 | `{'n_estimators': 300, 'max_depth': 5, 'min_samples_split': 2, 'min_samples_leaf': 2}` |
| lenient | 4.5 | C1_Combined_K | XGBoost | 71 | 46 | 0.470 | 0.116 [-0.034, 0.266] | 0.471 | 22.54 | 628.7 [432.1, 825.2] | 0.354 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 30, 'reg_alpha': 1.0, 'reg_lambda': 0.1}` |
| lenient | 4.5 | C1_Combined_K | Neural_Network | 71 | 46 | 0.610 | 0.166 [-0.177, 0.509] | 0.643 | 19.76 | 567.9 [306.4, 829.4] | 0.444 | `{'hidden_layer_sizes': (60,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| lenient | 4.5 | C1_Combined_K | Lasso | 71 | 46 | 0.483 | 0.308 [0.056, 0.561] | 0.636 | 19.52 | 577.3 [489.2, 665.5] | 0.175 | `{'alpha': 10.0}` |
| lenient | 4.5 | C1_Combined_K | ElasticNet | 71 | 46 | 0.484 | 0.298 [0.032, 0.564] | 0.633 | 19.67 | 581.0 [491.0, 671.1] | 0.186 | `{'alpha': 0.1, 'l1_ratio': 0.9}` |
| lenient | 4.5 | C1_Combined_K | Ridge | 71 | 46 | 0.352 | 0.270 [0.209, 0.331] | 0.634 | 21.52 | 615.5 [454.5, 776.5] | 0.082 | `{'alpha': 100.0}` |
| lenient | 5.0 | A1_Biomechanical_Core_K | SVM | 71 | 46 | 0.318 | 0.267 [0.179, 0.355] | 0.631 | 19.81 | 631.8 [539.8, 723.8] | 0.051 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 5.0 | A1_Biomechanical_Core_K | Random_Forest | 71 | 46 | 0.737 | 0.292 [0.029, 0.555] | 0.648 | 19.43 | 620.7 [465.2, 776.2] | 0.446 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 5.0 | A1_Biomechanical_Core_K | XGBoost | 71 | 46 | 0.704 | 0.226 [-0.018, 0.470] | 0.523 | 21.48 | 666.2 [433.8, 898.7] | 0.478 | `{'learning_rate': 0.05, 'max_depth': 2, 'n_estimators': 50, 'reg_alpha': 0.5, 'reg_lambda': 2.0}` |
| lenient | 5.0 | A1_Biomechanical_Core_K | Neural_Network | 71 | 46 | 0.558 | 0.343 [0.194, 0.492] | 0.669 | 18.27 | 528.1 [366.4, 689.8] | 0.215 | `{'hidden_layer_sizes': (100,), 'alpha': 0.5, 'learning_rate_init': 0.0001}` |
| lenient | 5.0 | A1_Biomechanical_Core_K | Lasso | 71 | 46 | 0.503 | 0.294 [0.102, 0.485] | 0.622 | 22.91 | 626.2 [471.7, 780.8] | 0.210 | `{'alpha': 10.0}` |
| lenient | 5.0 | A1_Biomechanical_Core_K | ElasticNet | 71 | 46 | 0.464 | 0.283 [0.023, 0.543] | 0.619 | 21.89 | 616.8 [425.2, 808.4] | 0.181 | `{'alpha': 1.0, 'l1_ratio': 0.7}` |
| lenient | 5.0 | A1_Biomechanical_Core_K | Ridge | 71 | 46 | 0.411 | 0.295 [0.109, 0.480] | 0.614 | 22.44 | 617.7 [494.4, 741.0] | 0.117 | `{'alpha': 10.0}` |
| lenient | 5.0 | A2_Biomechanical_WithK | SVM | 71 | 46 | 0.331 | 0.254 [0.152, 0.356] | 0.613 | 20.36 | 637.1 [545.0, 729.2] | 0.077 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 5.0 | A2_Biomechanical_WithK | Random_Forest | 71 | 46 | 0.763 | 0.407 [0.283, 0.530] | 0.726 | 18.30 | 576.7 [441.2, 712.2] | 0.356 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 5.0 | A2_Biomechanical_WithK | XGBoost | 71 | 46 | 0.760 | 0.311 [0.037, 0.585] | 0.608 | 20.68 | 625.4 [385.9, 865.0] | 0.449 | `{'learning_rate': 0.05, 'max_depth': 2, 'n_estimators': 50, 'reg_alpha': 0.5, 'reg_lambda': 2.0}` |
| lenient | 5.0 | A2_Biomechanical_WithK | Neural_Network | 71 | 46 | 0.636 | 0.290 [0.116, 0.464] | 0.622 | 21.43 | 634.7 [453.6, 815.8] | 0.345 | `{'hidden_layer_sizes': (80,), 'alpha': 0.5, 'learning_rate_init': 0.001}` |
| lenient | 5.0 | A2_Biomechanical_WithK | Lasso | 71 | 46 | 0.569 | 0.404 [0.238, 0.570] | 0.699 | 21.57 | 576.1 [425.0, 727.3] | 0.165 | `{'alpha': 10.0}` |
| lenient | 5.0 | A2_Biomechanical_WithK | ElasticNet | 71 | 46 | 0.570 | 0.392 [0.234, 0.549] | 0.702 | 21.91 | 582.5 [436.5, 728.4] | 0.178 | `{'alpha': 0.001, 'l1_ratio': 0.3}` |
| lenient | 5.0 | A2_Biomechanical_WithK | Ridge | 71 | 46 | 0.516 | 0.313 [0.050, 0.577] | 0.634 | 21.58 | 596.6 [428.7, 764.5] | 0.203 | `{'alpha': 10.0}` |
| lenient | 5.0 | B_Clinical_K | SVM | 71 | 46 | 0.582 | 0.282 [-0.016, 0.579] | 0.623 | 22.30 | 633.9 [425.3, 842.6] | 0.301 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.03}` |
| lenient | 5.0 | B_Clinical_K | Random_Forest | 71 | 46 | 0.746 | 0.295 [0.055, 0.536] | 0.589 | 20.57 | 633.9 [420.8, 847.0] | 0.451 | `{'n_estimators': 50, 'max_depth': 3, 'min_samples_split': 5, 'min_samples_leaf': 2}` |
| lenient | 5.0 | B_Clinical_K | XGBoost | 71 | 46 | 0.711 | 0.299 [0.093, 0.504] | 0.565 | 21.18 | 637.5 [408.5, 866.5] | 0.412 | `{'learning_rate': 0.05, 'max_depth': 2, 'n_estimators': 50, 'reg_alpha': 0.5, 'reg_lambda': 2.0}` |
| lenient | 5.0 | B_Clinical_K | Neural_Network | 71 | 46 | 0.361 | 0.264 [0.053, 0.475] | 0.603 | 17.22 | 524.7 [265.3, 784.0] | 0.098 | `{'hidden_layer_sizes': (100,), 'alpha': 0.1, 'learning_rate_init': 0.001}` |
| lenient | 5.0 | B_Clinical_K | Lasso | 71 | 46 | 0.430 | 0.328 [0.101, 0.555] | 0.647 | 22.12 | 597.7 [485.8, 709.7] | 0.102 | `{'alpha': 1.0}` |
| lenient | 5.0 | B_Clinical_K | ElasticNet | 71 | 46 | 0.430 | 0.331 [0.107, 0.555] | 0.647 | 22.04 | 596.8 [486.3, 707.3] | 0.099 | `{'alpha': 0.1, 'l1_ratio': 0.9}` |
| lenient | 5.0 | B_Clinical_K | Ridge | 71 | 46 | 0.423 | 0.354 [0.177, 0.530] | 0.651 | 21.25 | 588.6 [490.5, 686.7] | 0.070 | `{'alpha': 10.0}` |
| lenient | 5.0 | C1_Combined_K | SVM | 71 | 46 | 0.519 | 0.376 [0.273, 0.478] | 0.692 | 19.18 | 601.0 [438.8, 763.2] | 0.143 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 5.0 | C1_Combined_K | Random_Forest | 71 | 46 | 0.748 | 0.240 [-0.035, 0.515] | 0.598 | 21.09 | 642.2 [473.2, 811.2] | 0.508 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 5.0 | C1_Combined_K | XGBoost | 71 | 46 | 0.925 | 0.219 [-0.265, 0.704] | 0.596 | 22.19 | 635.1 [392.9, 877.2] | 0.706 | `{'learning_rate': 0.1, 'max_depth': 2, 'n_estimators': 100, 'reg_alpha': 0.1, 'reg_lambda': 2.0}` |
| lenient | 5.0 | C1_Combined_K | Neural_Network | 71 | 46 | 0.641 | 0.284 [0.098, 0.469] | 0.594 | 21.92 | 629.7 [459.4, 800.1] | 0.358 | `{'hidden_layer_sizes': (80,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| lenient | 5.0 | C1_Combined_K | Lasso | 71 | 46 | 0.548 | 0.360 [0.130, 0.591] | 0.674 | 20.44 | 592.0 [462.2, 721.9] | 0.188 | `{'alpha': 10.0}` |
| lenient | 5.0 | C1_Combined_K | ElasticNet | 71 | 46 | 0.549 | 0.356 [0.115, 0.596] | 0.670 | 20.56 | 593.2 [461.9, 724.4] | 0.193 | `{'alpha': 0.1, 'l1_ratio': 0.9}` |
| lenient | 5.0 | C1_Combined_K | Ridge | 71 | 46 | 0.439 | 0.331 [0.136, 0.526] | 0.627 | 21.24 | 598.8 [490.5, 707.2] | 0.108 | `{'alpha': 10.0}` |
| lenient | 5.5 | A1_Biomechanical_Core_K | SVM | 71 | 46 | 0.531 | 0.335 [0.236, 0.434] | 0.637 | 23.67 | 688.9 [451.1, 926.8] | 0.196 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.03}` |
| lenient | 5.5 | A1_Biomechanical_Core_K | Random_Forest | 71 | 46 | 0.754 | 0.228 [-0.136, 0.591] | 0.649 | 21.34 | 643.2 [516.9, 769.5] | 0.527 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 5.5 | A1_Biomechanical_Core_K | XGBoost | 71 | 46 | 0.717 | 0.198 [-0.007, 0.404] | 0.553 | 26.57 | 752.6 [496.9, 1008.3] | 0.519 | `{'learning_rate': 0.05, 'max_depth': 2, 'n_estimators': 50, 'reg_alpha': 0.5, 'reg_lambda': 2.0}` |
| lenient | 5.5 | A1_Biomechanical_Core_K | Neural_Network | 71 | 46 | 0.534 | 0.274 [0.057, 0.491] | 0.606 | 23.38 | 632.3 [468.4, 796.1] | 0.260 | `{'hidden_layer_sizes': (100,), 'alpha': 0.5, 'learning_rate_init': 0.0001}` |
| lenient | 5.5 | A1_Biomechanical_Core_K | Lasso | 71 | 46 | 0.484 | 0.289 [0.039, 0.538] | 0.656 | 23.85 | 615.8 [508.7, 723.0] | 0.195 | `{'alpha': 0.01}` |
| lenient | 5.5 | A1_Biomechanical_Core_K | ElasticNet | 71 | 46 | 0.438 | 0.295 [0.111, 0.478] | 0.590 | 24.71 | 685.2 [478.3, 892.0] | 0.143 | `{'alpha': 1.0, 'l1_ratio': 0.7}` |
| lenient | 5.5 | A1_Biomechanical_Core_K | Ridge | 71 | 46 | 0.449 | 0.296 [0.095, 0.498] | 0.586 | 24.68 | 683.8 [470.0, 897.5] | 0.152 | `{'alpha': 10.0}` |
| lenient | 5.5 | A2_Biomechanical_WithK | SVM | 71 | 46 | 0.544 | 0.219 [0.040, 0.398] | 0.554 | 23.73 | 746.7 [483.6, 1009.7] | 0.325 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.03}` |
| lenient | 5.5 | A2_Biomechanical_WithK | Random_Forest | 71 | 46 | 0.777 | 0.350 [0.113, 0.587] | 0.729 | 19.90 | 597.7 [502.5, 692.9] | 0.427 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 5.5 | A2_Biomechanical_WithK | XGBoost | 71 | 46 | 0.765 | 0.251 [0.012, 0.491] | 0.548 | 24.68 | 735.6 [424.2, 1047.1] | 0.514 | `{'learning_rate': 0.05, 'max_depth': 2, 'n_estimators': 50, 'reg_alpha': 0.5, 'reg_lambda': 2.0}` |
| lenient | 5.5 | A2_Biomechanical_WithK | Neural_Network | 71 | 46 | 0.663 | 0.269 [0.058, 0.479] | 0.677 | 22.12 | 640.5 [516.4, 764.6] | 0.394 | `{'hidden_layer_sizes': (80,), 'alpha': 0.5, 'learning_rate_init': 0.001}` |
| lenient | 5.5 | A2_Biomechanical_WithK | Lasso | 71 | 46 | 0.585 | 0.377 [0.141, 0.612] | 0.721 | 22.53 | 586.0 [467.9, 704.0] | 0.209 | `{'alpha': 10.0}` |
| lenient | 5.5 | A2_Biomechanical_WithK | ElasticNet | 71 | 46 | 0.586 | 0.356 [0.113, 0.599] | 0.720 | 22.98 | 595.1 [483.0, 707.1] | 0.230 | `{'alpha': 0.001, 'l1_ratio': 0.3}` |
| lenient | 5.5 | A2_Biomechanical_WithK | Ridge | 71 | 46 | 0.468 | 0.307 [0.118, 0.496] | 0.598 | 24.32 | 677.1 [472.9, 881.3] | 0.161 | `{'alpha': 10.0}` |
| lenient | 5.5 | B_Clinical_K | SVM | 71 | 46 | 0.557 | 0.325 [0.126, 0.523] | 0.635 | 23.88 | 694.5 [448.1, 941.0] | 0.233 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.03}` |
| lenient | 5.5 | B_Clinical_K | Random_Forest | 71 | 46 | 0.760 | 0.252 [-0.044, 0.548] | 0.576 | 25.06 | 728.1 [455.4, 1000.9] | 0.508 | `{'n_estimators': 50, 'max_depth': 3, 'min_samples_split': 5, 'min_samples_leaf': 2}` |
| lenient | 5.5 | B_Clinical_K | XGBoost | 71 | 46 | 0.651 | 0.291 [-0.070, 0.651] | 0.602 | 26.58 | 674.2 [521.3, 827.1] | 0.360 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 50, 'reg_alpha': 2.0, 'reg_lambda': 0.1}` |
| lenient | 5.5 | B_Clinical_K | Neural_Network | 71 | 46 | 0.571 | 0.192 [-0.027, 0.412] | 0.567 | 28.73 | 742.5 [530.4, 954.6] | 0.379 | `{'hidden_layer_sizes': (80,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| lenient | 5.5 | B_Clinical_K | Lasso | 71 | 46 | 0.419 | 0.232 [-0.106, 0.571] | 0.625 | 26.07 | 664.3 [474.8, 853.9] | 0.187 | `{'alpha': 1.0}` |
| lenient | 5.5 | B_Clinical_K | ElasticNet | 71 | 46 | 0.419 | 0.242 [-0.079, 0.562] | 0.626 | 25.92 | 660.9 [477.4, 844.4] | 0.177 | `{'alpha': 0.1, 'l1_ratio': 0.9}` |
| lenient | 5.5 | B_Clinical_K | Ridge | 71 | 46 | 0.411 | 0.311 [0.103, 0.519] | 0.629 | 24.61 | 634.0 [487.6, 780.3] | 0.100 | `{'alpha': 10.0}` |
| lenient | 5.5 | C1_Combined_K | SVM | 71 | 46 | 0.504 | 0.345 [0.074, 0.616] | 0.670 | 21.90 | 661.1 [515.6, 806.6] | 0.159 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 5.5 | C1_Combined_K | Random_Forest | 71 | 46 | 0.860 | 0.255 [-0.022, 0.532] | 0.576 | 25.39 | 631.3 [488.3, 774.4] | 0.605 | `{'n_estimators': 300, 'max_depth': 5, 'min_samples_split': 2, 'min_samples_leaf': 2}` |
| lenient | 5.5 | C1_Combined_K | XGBoost | 71 | 46 | 0.677 | 0.298 [-0.078, 0.673] | 0.618 | 25.84 | 668.2 [497.7, 838.7] | 0.379 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 50, 'reg_alpha': 2.0, 'reg_lambda': 0.1}` |
| lenient | 5.5 | C1_Combined_K | Neural_Network | 71 | 46 | 0.642 | 0.316 [0.010, 0.622] | 0.652 | 25.08 | 675.2 [517.1, 833.3] | 0.326 | `{'hidden_layer_sizes': (80,), 'alpha': 0.3, 'learning_rate_init': 0.0001}` |
| lenient | 5.5 | C1_Combined_K | Lasso | 71 | 46 | 0.466 | 0.326 [0.121, 0.530] | 0.660 | 23.20 | 628.4 [497.1, 759.8] | 0.140 | `{'alpha': 10.0}` |
| lenient | 5.5 | C1_Combined_K | ElasticNet | 71 | 46 | 0.452 | 0.334 [0.147, 0.522] | 0.648 | 23.63 | 629.6 [484.9, 774.2] | 0.117 | `{'alpha': 1.0, 'l1_ratio': 0.7}` |
| lenient | 5.5 | C1_Combined_K | Ridge | 71 | 46 | 0.428 | 0.316 [0.115, 0.516] | 0.613 | 24.17 | 632.5 [481.4, 783.6] | 0.112 | `{'alpha': 10.0}` |
| lenient | 6.0 | A1_Biomechanical_Core_K | SVM | 71 | 46 | 0.548 | 0.360 [0.185, 0.536] | 0.621 | 21.19 | 643.2 [494.6, 791.8] | 0.188 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.03}` |
| lenient | 6.0 | A1_Biomechanical_Core_K | Random_Forest | 71 | 46 | 0.741 | 0.335 [0.098, 0.573] | 0.645 | 23.44 | 673.5 [460.3, 886.7] | 0.405 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 6.0 | A1_Biomechanical_Core_K | XGBoost | 71 | 46 | 0.579 | 0.293 [0.022, 0.563] | 0.634 | 22.51 | 580.1 [330.7, 829.4] | 0.286 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 30, 'reg_alpha': 1.0, 'reg_lambda': 0.1}` |
| lenient | 6.0 | A1_Biomechanical_Core_K | Neural_Network | 71 | 46 | 0.533 | 0.353 [0.206, 0.499] | 0.636 | 23.36 | 643.5 [534.9, 752.2] | 0.181 | `{'hidden_layer_sizes': (80,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| lenient | 6.0 | A1_Biomechanical_Core_K | Lasso | 71 | 46 | 0.515 | 0.323 [0.168, 0.477] | 0.624 | 26.36 | 684.8 [484.9, 884.7] | 0.192 | `{'alpha': 10.0}` |
| lenient | 6.0 | A1_Biomechanical_Core_K | ElasticNet | 71 | 46 | 0.515 | 0.313 [0.159, 0.467] | 0.623 | 26.69 | 690.3 [487.3, 893.4] | 0.202 | `{'alpha': 0.001, 'l1_ratio': 0.3}` |
| lenient | 6.0 | A1_Biomechanical_Core_K | Ridge | 71 | 46 | 0.305 | 0.252 [0.121, 0.383] | 0.630 | 25.59 | 692.8 [586.9, 798.8] | 0.053 | `{'alpha': 100.0}` |
| lenient | 6.0 | A2_Biomechanical_WithK | SVM | 71 | 46 | 0.463 | 0.297 [0.043, 0.551] | 0.635 | 29.62 | 685.6 [515.6, 855.5] | 0.166 | `{'C': 5000, 'epsilon': 800, 'gamma': 0.01}` |
| lenient | 6.0 | A2_Biomechanical_WithK | Random_Forest | 71 | 46 | 0.774 | 0.376 [0.195, 0.556] | 0.685 | 22.70 | 647.1 [481.0, 813.2] | 0.398 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 6.0 | A2_Biomechanical_WithK | XGBoost | 71 | 46 | 0.586 | 0.294 [0.030, 0.559] | 0.641 | 22.74 | 581.9 [328.0, 835.9] | 0.292 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 30, 'reg_alpha': 1.0, 'reg_lambda': 0.1}` |
| lenient | 6.0 | A2_Biomechanical_WithK | Neural_Network | 71 | 46 | 0.644 | 0.420 [0.344, 0.496] | 0.705 | 21.71 | 637.4 [449.5, 825.2] | 0.224 | `{'hidden_layer_sizes': (80,), 'alpha': 0.5, 'learning_rate_init': 0.001}` |
| lenient | 6.0 | A2_Biomechanical_WithK | Lasso | 71 | 46 | 0.566 | 0.414 [0.296, 0.531] | 0.695 | 24.58 | 635.4 [459.5, 811.3] | 0.152 | `{'alpha': 10.0}` |
| lenient | 6.0 | A2_Biomechanical_WithK | ElasticNet | 71 | 46 | 0.566 | 0.402 [0.297, 0.508] | 0.697 | 25.02 | 643.2 [462.3, 824.1] | 0.164 | `{'alpha': 0.001, 'l1_ratio': 0.3}` |
| lenient | 6.0 | A2_Biomechanical_WithK | Ridge | 71 | 46 | 0.441 | 0.275 [-0.072, 0.621] | 0.546 | 22.92 | 583.6 [324.2, 842.9] | 0.167 | `{'alpha': 0.01}` |
| lenient | 6.0 | B_Clinical_K | SVM | 71 | 46 | 0.536 | 0.291 [0.071, 0.512] | 0.593 | 23.25 | 677.8 [507.1, 848.6] | 0.245 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.03}` |
| lenient | 6.0 | B_Clinical_K | Random_Forest | 71 | 46 | 0.675 | 0.170 [-0.152, 0.491] | 0.458 | 25.11 | 732.7 [516.9, 948.5] | 0.505 | `{'n_estimators': 50, 'max_depth': 3, 'min_samples_split': 5, 'min_samples_leaf': 2}` |
| lenient | 6.0 | B_Clinical_K | XGBoost | 71 | 46 | 0.664 | 0.145 [-0.098, 0.388] | 0.433 | 25.01 | 745.1 [568.3, 921.9] | 0.519 | `{'learning_rate': 0.05, 'max_depth': 2, 'n_estimators': 50, 'reg_alpha': 0.5, 'reg_lambda': 2.0}` |
| lenient | 6.0 | B_Clinical_K | Neural_Network | 71 | 46 | 0.555 | 0.281 [0.143, 0.419] | 0.558 | 24.61 | 682.7 [552.4, 813.0] | 0.274 | `{'hidden_layer_sizes': (80,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| lenient | 6.0 | B_Clinical_K | Lasso | 71 | 46 | 0.377 | 0.250 [0.068, 0.433] | 0.590 | 25.80 | 688.4 [568.2, 808.6] | 0.127 | `{'alpha': 1.0}` |
| lenient | 6.0 | B_Clinical_K | ElasticNet | 71 | 46 | 0.377 | 0.253 [0.074, 0.432] | 0.591 | 25.73 | 687.1 [569.0, 805.3] | 0.124 | `{'alpha': 0.1, 'l1_ratio': 0.9}` |
| lenient | 6.0 | B_Clinical_K | Ridge | 71 | 46 | 0.371 | 0.276 [0.137, 0.416] | 0.594 | 25.16 | 677.8 [572.7, 782.9] | 0.095 | `{'alpha': 10.0}` |
| lenient | 6.0 | C1_Combined_K | SVM | 71 | 46 | 0.586 | 0.364 [0.202, 0.526] | 0.627 | 21.47 | 643.0 [494.9, 791.0] | 0.222 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.03}` |
| lenient | 6.0 | C1_Combined_K | Random_Forest | 71 | 46 | 0.751 | 0.241 [-0.010, 0.492] | 0.595 | 25.38 | 710.0 [522.6, 897.5] | 0.510 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 6.0 | C1_Combined_K | XGBoost | 71 | 46 | 0.584 | 0.219 [-0.013, 0.450] | 0.589 | 23.06 | 606.6 [388.0, 825.1] | 0.365 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 30, 'reg_alpha': 1.0, 'reg_lambda': 0.1}` |
| lenient | 6.0 | C1_Combined_K | Neural_Network | 71 | 46 | 0.541 | 0.305 [0.099, 0.511] | 0.659 | 28.60 | 696.4 [462.4, 930.4] | 0.236 | `{'hidden_layer_sizes': (80,), 'alpha': 0.5, 'learning_rate_init': 0.001}` |
| lenient | 6.0 | C1_Combined_K | Lasso | 71 | 46 | 0.457 | 0.327 [0.155, 0.500] | 0.633 | 23.20 | 671.4 [543.0, 799.9] | 0.129 | `{'alpha': 10.0}` |
| lenient | 6.0 | C1_Combined_K | ElasticNet | 71 | 46 | 0.442 | 0.319 [0.172, 0.466] | 0.626 | 24.03 | 678.3 [547.5, 809.1] | 0.123 | `{'alpha': 1.0, 'l1_ratio': 0.7}` |
| lenient | 6.0 | C1_Combined_K | Ridge | 71 | 46 | 0.349 | 0.290 [0.203, 0.378] | 0.636 | 25.04 | 676.3 [580.5, 772.1] | 0.059 | `{'alpha': 100.0}` |

## 八、可视化

### Strict 数据组：Distance × Model 热图 (q1plus_K)

![Strict Heatmap](FIG/SR0530_HP_Tuning_Heatmap_strict_q1plus_K.png)

### Lenient 数据组：Distance × Model 热图 (q1plus_K)

![Lenient Heatmap](FIG/SR0530_HP_Tuning_Heatmap_lenient_q1plus_K.png)

### Strict vs Lenient 各模型对比 (q1plus_K)

![Strict vs Lenient](FIG/SR0530_HP_Tuning_Strict_vs_Lenient_q1plus_K.png)

### 方案对比 (q1plus_K)

![Schema Comparison](FIG/SR0530_HP_Tuning_SchemaComparison_q1plus_K.png)

### 基线 vs +K 对比 (q1plus_K)

![Baseline vs K](FIG/SR0530_HP_Tuning_Baseline_vs_K_q1plus_K.png)

## 九、讨论

1. **K 的加入效应**：本报告核心是对比加入角膜曲率（K）后各基线方案 Test R² 的变化。若 ΔR² 普遍接近 0 或为负，说明 K 对预测局部密度没有独立贡献；若 ΔR² 稳定为正，说明 K 携带了 AL/SE/ACD 未捕获的变异。
2. **数据组差异**：strict 模式移除了局部 ROI 异常值，数据更干净；lenient 模式保留了更多样本但可能混入异常。
3. **最佳参数稳定性**：如果某模型在 strict 和 lenient 下的最佳参数差异很大，提示该模型对异常值敏感。
4. **方案选择**：各方案表现因距离和数据组而异，最佳方案需结合 Test R²、Gap 和参数稳定性综合判断，具体见上述结果表。
5. **置信区间解释**：R² 与 RMSE 的 95% CI 反映 5-fold CV fold 间变异；R² CI 跨越 0 或 RMSE CI 范围过大，均提示该配置泛化能力不稳定。
6. **参数寻优局限**：Random Search 的 n_iter 是计算与精度的折中，关键模型可进一步增加迭代次数。

---

*Report generated automatically by SR_ML_hyperparameter_tuning.py*
