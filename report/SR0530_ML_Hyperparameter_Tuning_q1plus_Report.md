# SR0530 ML 超参数寻优报告（≥1 象限可用（放宽，outer merge 取平均））

> **目标**：针对每种 ML 方法，在 strict（69 眼）和 lenient（71 眼）两套数据上做超参数寻优，比较最佳参数与结果。

> **搜索策略**：Random Search + GroupKFold by Subject，每模型 10 组参数

> **象限策略**：≥1 象限可用（放宽，outer merge 取平均）

> **数据组**：`CleanDataRoi_strict/`（任意 ROI >7000 剔除）和 `CleanDataRoi_lenient/`（距离平均 >7000 剔除）

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
- **方案**：C1_Combined
- **模型**：Lasso
- **最佳 Test R²**：0.538
- **最佳参数**：{'alpha': 10.0}
- **样本量**：71 眼 / 46 subjects

## 三、每个数据组的最佳结果（按距离）

### STRICT 数据组

| 距离 (mm) | 最佳方案 | 最佳模型 | Test R² | MAPE (%) | RMSE | Gap | 最佳参数 |
|-----------|---------|---------|---------|----------|------|-----|---------|
| 1.0 | B_Clinical | Neural_Network | 0.360 | 10.30 | 472.0 | 0.236 | `{'hidden_layer_sizes': (40,), 'alpha': 0.3, 'learning_rate_init': 0.001}` |
| 1.5 | C1_Combined | ElasticNet | 0.387 | 9.40 | 399.2 | 0.098 | `{'alpha': 1.0, 'l1_ratio': 0.7}` |
| 2.0 | C1_Combined | Lasso | 0.288 | 10.36 | 383.4 | 0.102 | `{'alpha': 10.0}` |
| 2.5 | C1_Combined | ElasticNet | 0.322 | 11.62 | 425.5 | 0.086 | `{'alpha': 0.01, 'l1_ratio': 0.5}` |
| 3.0 | A1_Biomechanical_Core | XGBoost | 0.376 | 12.63 | 426.9 | 0.516 | `{'learning_rate': 0.05, 'max_depth': 3, 'n_estimators': 100, 'reg_alpha': 0.1, 'reg_lambda': 2.0}` |
| 3.5 | A1_Biomechanical_Core | Random_Forest | 0.215 | 17.36 | 565.0 | 0.436 | `{'n_estimators': 300, 'max_depth': 5, 'min_samples_split': 5, 'min_samples_leaf': 4}` |
| 4.0 | A2_Biomechanical_NoK | Neural_Network | 0.195 | 19.72 | 548.9 | 0.044 | `{'hidden_layer_sizes': (100,), 'alpha': 0.5, 'learning_rate_init': 0.001}` |
| 4.5 | A1_Biomechanical_Core | Random_Forest | 0.330 | 18.96 | 553.0 | 0.508 | `{'n_estimators': 300, 'max_depth': 4, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| 5.0 | C1_Combined | ElasticNet | 0.268 | 20.66 | 555.3 | 0.059 | `{'alpha': 1.0, 'l1_ratio': 0.1}` |
| 5.5 | C1_Combined | Ridge | 0.308 | 23.57 | 621.6 | 0.216 | `{'alpha': 0.1}` |
| 6.0 | C1_Combined | SVM | 0.321 | 25.45 | 704.6 | 0.180 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.03}` |

### LENIENT 数据组

| 距离 (mm) | 最佳方案 | 最佳模型 | Test R² | MAPE (%) | RMSE | Gap | 最佳参数 |
|-----------|---------|---------|---------|----------|------|-----|---------|
| 1.0 | A2_Biomechanical_NoK | Random_Forest | 0.452 | 9.39 | 472.8 | 0.238 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| 1.5 | C1_Combined | Lasso | 0.538 | 9.27 | 491.4 | 0.040 | `{'alpha': 10.0}` |
| 2.0 | C1_Combined | Lasso | 0.474 | 9.71 | 447.6 | 0.039 | `{'alpha': 10.0}` |
| 2.5 | A1_Biomechanical_Core | ElasticNet | 0.258 | 13.40 | 421.0 | 0.130 | `{'alpha': 1.0, 'l1_ratio': 0.5}` |
| 3.0 | C1_Combined | ElasticNet | 0.369 | 13.60 | 506.8 | 0.070 | `{'alpha': 0.01, 'l1_ratio': 0.7}` |
| 3.5 | A2_Biomechanical_NoK | Random_Forest | 0.275 | 15.52 | 535.0 | 0.342 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 5, 'min_samples_leaf': 4}` |
| 4.0 | C1_Combined | Neural_Network | 0.232 | 19.48 | 611.7 | 0.146 | `{'hidden_layer_sizes': (40,), 'alpha': 0.5, 'learning_rate_init': 0.0005}` |
| 4.5 | A2_Biomechanical_NoK | Random_Forest | 0.233 | 19.46 | 607.3 | 0.378 | `{'n_estimators': 300, 'max_depth': 2, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| 5.0 | A2_Biomechanical_NoK | Random_Forest | 0.410 | 18.30 | 578.4 | 0.331 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| 5.5 | C1_Combined | Neural_Network | 0.348 | 24.96 | 681.7 | 0.203 | `{'hidden_layer_sizes': (80,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| 6.0 | C1_Combined | Neural_Network | 0.344 | 24.71 | 646.2 | 0.151 | `{'hidden_layer_sizes': (80,), 'alpha': 0.3, 'learning_rate_init': 0.001}` |

## 四、每个模型在每个数据组的最佳结果

| 数据组 | 模型 | 最佳距离 | 最佳方案 | Test R² | MAPE (%) | 最佳参数 |
|--------|------|---------|---------|---------|----------|---------|
| strict | ElasticNet | 1.5 mm | C1_Combined | 0.387 | 9.40 | `{'alpha': 1.0, 'l1_ratio': 0.7}` |
| strict | Lasso | 1.5 mm | C1_Combined | 0.360 | 9.07 | `{'alpha': 0.01}` |
| strict | Neural_Network | 1.0 mm | B_Clinical | 0.360 | 10.30 | `{'hidden_layer_sizes': (40,), 'alpha': 0.3, 'learning_rate_init': 0.001}` |
| strict | Random_Forest | 1.5 mm | A2_Biomechanical_NoK | 0.357 | 9.66 | `{'n_estimators': 200, 'max_depth': 2, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| strict | Ridge | 2.5 mm | C1_Combined | 0.317 | 11.66 | `{'alpha': 0.01}` |
| strict | SVM | 6.0 mm | C1_Combined | 0.321 | 25.45 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.03}` |
| strict | XGBoost | 3.0 mm | A1_Biomechanical_Core | 0.376 | 12.63 | `{'learning_rate': 0.05, 'max_depth': 3, 'n_estimators': 100, 'reg_alpha': 0.1, 'reg_lambda': 2.0}` |
| lenient | ElasticNet | 1.5 mm | C1_Combined | 0.530 | 9.40 | `{'alpha': 0.01, 'l1_ratio': 0.7}` |
| lenient | Lasso | 1.5 mm | C1_Combined | 0.538 | 9.27 | `{'alpha': 10.0}` |
| lenient | Neural_Network | 2.0 mm | C1_Combined | 0.408 | 11.67 | `{'hidden_layer_sizes': (60,), 'alpha': 1.0, 'learning_rate_init': 0.001}` |
| lenient | Random_Forest | 1.5 mm | C1_Combined | 0.472 | 9.38 | `{'n_estimators': 300, 'max_depth': 5, 'min_samples_split': 5, 'min_samples_leaf': 4}` |
| lenient | Ridge | 1.5 mm | C1_Combined | 0.529 | 9.40 | `{'alpha': 0.01}` |
| lenient | SVM | 2.0 mm | C1_Combined | 0.351 | 10.40 | `{'C': 1000, 'epsilon': 100, 'gamma': 0.01}` |
| lenient | XGBoost | 1.5 mm | A2_Biomechanical_NoK | 0.420 | 10.39 | `{'learning_rate': 0.05, 'max_depth': 3, 'n_estimators': 30, 'reg_alpha': 0.5, 'reg_lambda': 2.0}` |

## 五、每个特征方案的最佳结果

| 方案 | 数据组 | 最佳距离 | 最佳模型 | Test R² |
|------|--------|---------|---------|----------|
| A1_Biomechanical_Core | lenient | 1.5 mm | Random_Forest | 0.453 |
| A2_Biomechanical_NoK | lenient | 1.5 mm | Random_Forest | 0.470 |
| B_Clinical | strict | 1.0 mm | Neural_Network | 0.360 |
| C1_Combined | lenient | 1.5 mm | Lasso | 0.538 |

## 六、全部详细结果

| 数据组 | 距离 | 方案 | 模型 | N_Eyes | N_Subj | Train R² | Test R² | Corr | MAPE | RMSE | Gap | 最佳参数 |
|--------|------|------|------|--------|--------|----------|---------|------|------|------|-----|---------|
| strict | 1.0 | A1_Biomechanical_Core | SVM | 69 | 44 | 0.234 | 0.222 | 0.669 | 11.98 | 522.4 | 0.012 | `{'C': 500, 'epsilon': 800, 'gamma': 0.03}` |
| strict | 1.0 | A1_Biomechanical_Core | Random_Forest | 69 | 44 | 0.642 | 0.289 | 0.700 | 10.44 | 500.1 | 0.352 | `{'n_estimators': 100, 'max_depth': 2, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| strict | 1.0 | A1_Biomechanical_Core | XGBoost | 69 | 44 | 0.721 | 0.322 | 0.694 | 10.51 | 484.5 | 0.399 | `{'learning_rate': 0.1, 'max_depth': 2, 'n_estimators': 30, 'reg_alpha': 2.0, 'reg_lambda': 2.0}` |
| strict | 1.0 | A1_Biomechanical_Core | Neural_Network | 69 | 44 | 0.491 | 0.259 | 0.588 | 11.37 | 501.4 | 0.233 | `{'hidden_layer_sizes': (40,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| strict | 1.0 | A1_Biomechanical_Core | Lasso | 69 | 44 | 0.356 | 0.075 | 0.539 | 11.19 | 529.5 | 0.281 | `{'alpha': 0.001}` |
| strict | 1.0 | A1_Biomechanical_Core | ElasticNet | 69 | 44 | 0.349 | 0.079 | 0.452 | 12.78 | 545.1 | 0.270 | `{'alpha': 1.0, 'l1_ratio': 0.5}` |
| strict | 1.0 | A1_Biomechanical_Core | Ridge | 69 | 44 | 0.396 | 0.055 | 0.499 | 12.79 | 546.3 | 0.341 | `{'alpha': 0.1}` |
| strict | 1.0 | A2_Biomechanical_NoK | SVM | 69 | 44 | 0.468 | 0.034 | 0.506 | 10.41 | 516.5 | 0.434 | `{'C': 2000, 'epsilon': 500, 'gamma': 0.05}` |
| strict | 1.0 | A2_Biomechanical_NoK | Random_Forest | 69 | 44 | 0.748 | 0.264 | 0.680 | 10.76 | 513.6 | 0.484 | `{'n_estimators': 300, 'max_depth': 4, 'min_samples_split': 10, 'min_samples_leaf': 1}` |
| strict | 1.0 | A2_Biomechanical_NoK | XGBoost | 69 | 44 | 0.867 | 0.207 | 0.660 | 11.45 | 525.2 | 0.660 | `{'learning_rate': 0.05, 'max_depth': 2, 'n_estimators': 100, 'reg_alpha': 2.0, 'reg_lambda': 0.5}` |
| strict | 1.0 | A2_Biomechanical_NoK | Neural_Network | 69 | 44 | 0.504 | -0.023 | 0.513 | 11.09 | 533.2 | 0.527 | `{'hidden_layer_sizes': (100,), 'alpha': 0.5, 'learning_rate_init': 0.0001}` |
| strict | 1.0 | A2_Biomechanical_NoK | Lasso | 69 | 44 | 0.417 | -0.037 | 0.492 | 11.99 | 575.3 | 0.454 | `{'alpha': 1.0}` |
| strict | 1.0 | A2_Biomechanical_NoK | ElasticNet | 69 | 44 | 0.416 | -0.009 | 0.488 | 11.99 | 572.0 | 0.424 | `{'alpha': 0.1, 'l1_ratio': 0.5}` |
| strict | 1.0 | A2_Biomechanical_NoK | Ridge | 69 | 44 | 0.405 | 0.041 | 0.483 | 12.01 | 565.4 | 0.365 | `{'alpha': 10.0}` |
| strict | 1.0 | B_Clinical | SVM | 69 | 44 | 0.514 | 0.221 | 0.559 | 10.95 | 515.6 | 0.293 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.03}` |
| strict | 1.0 | B_Clinical | Random_Forest | 69 | 44 | 0.597 | 0.157 | 0.622 | 11.14 | 518.2 | 0.440 | `{'n_estimators': 50, 'max_depth': 2, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| strict | 1.0 | B_Clinical | XGBoost | 69 | 44 | 0.609 | 0.271 | 0.614 | 10.28 | 504.6 | 0.338 | `{'learning_rate': 0.01, 'max_depth': 3, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 0.5}` |
| strict | 1.0 | B_Clinical | Neural_Network | 69 | 44 | 0.596 | 0.360 | 0.670 | 10.30 | 472.0 | 0.236 | `{'hidden_layer_sizes': (40,), 'alpha': 0.3, 'learning_rate_init': 0.001}` |
| strict | 1.0 | B_Clinical | Lasso | 69 | 44 | 0.184 | -0.216 | 0.312 | 14.02 | 617.0 | 0.400 | `{'alpha': 1.0}` |
| strict | 1.0 | B_Clinical | ElasticNet | 69 | 44 | 0.183 | -0.193 | 0.314 | 13.96 | 613.6 | 0.376 | `{'alpha': 0.1, 'l1_ratio': 0.1}` |
| strict | 1.0 | B_Clinical | Ridge | 69 | 44 | 0.181 | -0.178 | 0.406 | 12.96 | 607.2 | 0.359 | `{'alpha': 10.0}` |
| strict | 1.0 | C1_Combined | SVM | 69 | 44 | 0.222 | 0.141 | 0.630 | 12.45 | 547.8 | 0.081 | `{'C': 500, 'epsilon': 1000, 'gamma': 0.1}` |
| strict | 1.0 | C1_Combined | Random_Forest | 69 | 44 | 0.690 | 0.208 | 0.566 | 11.52 | 503.5 | 0.482 | `{'n_estimators': 300, 'max_depth': None, 'min_samples_split': 5, 'min_samples_leaf': 4}` |
| strict | 1.0 | C1_Combined | XGBoost | 69 | 44 | 0.999 | 0.043 | 0.650 | 12.36 | 565.0 | 0.956 | `{'learning_rate': 0.1, 'max_depth': 3, 'n_estimators': 200, 'reg_alpha': 0.1, 'reg_lambda': 0.5}` |
| strict | 1.0 | C1_Combined | Neural_Network | 69 | 44 | 0.527 | 0.295 | 0.602 | 10.62 | 480.8 | 0.232 | `{'hidden_layer_sizes': (80,), 'alpha': 0.5, 'learning_rate_init': 0.0005}` |
| strict | 1.0 | C1_Combined | Lasso | 69 | 44 | 0.503 | 0.234 | 0.637 | 10.97 | 519.6 | 0.269 | `{'alpha': 0.01}` |
| strict | 1.0 | C1_Combined | ElasticNet | 69 | 44 | 0.503 | 0.235 | 0.637 | 10.97 | 519.4 | 0.268 | `{'alpha': 0.001, 'l1_ratio': 0.1}` |
| strict | 1.0 | C1_Combined | Ridge | 69 | 44 | 0.493 | 0.294 | 0.651 | 10.82 | 504.8 | 0.199 | `{'alpha': 10.0}` |
| strict | 1.5 | A1_Biomechanical_Core | SVM | 69 | 44 | 0.228 | 0.087 | 0.524 | 10.54 | 454.0 | 0.141 | `{'C': 500, 'epsilon': 100, 'gamma': 0.005}` |
| strict | 1.5 | A1_Biomechanical_Core | Random_Forest | 69 | 44 | 0.662 | 0.307 | 0.644 | 9.96 | 424.2 | 0.355 | `{'n_estimators': 50, 'max_depth': 5, 'min_samples_split': 10, 'min_samples_leaf': 4}` |
| strict | 1.5 | A1_Biomechanical_Core | XGBoost | 69 | 44 | 0.180 | 0.111 | 0.567 | 11.89 | 487.6 | 0.069 | `{'learning_rate': 0.005, 'max_depth': 1, 'n_estimators': 50, 'reg_alpha': 0.5, 'reg_lambda': 0.5}` |
| strict | 1.5 | A1_Biomechanical_Core | Neural_Network | 69 | 44 | 0.509 | 0.203 | 0.579 | 11.05 | 457.8 | 0.305 | `{'hidden_layer_sizes': (80,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| strict | 1.5 | A1_Biomechanical_Core | Lasso | 69 | 44 | 0.424 | 0.247 | 0.548 | 9.37 | 384.7 | 0.177 | `{'alpha': 10.0}` |
| strict | 1.5 | A1_Biomechanical_Core | ElasticNet | 69 | 44 | 0.349 | 0.257 | 0.662 | 10.96 | 443.0 | 0.092 | `{'alpha': 1.0, 'l1_ratio': 0.1}` |
| strict | 1.5 | A1_Biomechanical_Core | Ridge | 69 | 44 | 0.432 | 0.212 | 0.685 | 10.48 | 457.0 | 0.220 | `{'alpha': 10.0}` |
| strict | 1.5 | A2_Biomechanical_NoK | SVM | 69 | 44 | 0.282 | 0.194 | 0.624 | 11.46 | 462.4 | 0.088 | `{'C': 100, 'epsilon': 300, 'gamma': 0.05}` |
| strict | 1.5 | A2_Biomechanical_NoK | Random_Forest | 69 | 44 | 0.701 | 0.357 | 0.649 | 9.66 | 410.0 | 0.344 | `{'n_estimators': 200, 'max_depth': 2, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| strict | 1.5 | A2_Biomechanical_NoK | XGBoost | 69 | 44 | 0.646 | 0.239 | 0.555 | 8.83 | 420.7 | 0.407 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 2.0}` |
| strict | 1.5 | A2_Biomechanical_NoK | Neural_Network | 69 | 44 | 0.483 | -0.034 | 0.367 | 11.23 | 505.9 | 0.516 | `{'hidden_layer_sizes': (40,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| strict | 1.5 | A2_Biomechanical_NoK | Lasso | 69 | 44 | 0.475 | 0.184 | 0.508 | 9.56 | 398.2 | 0.290 | `{'alpha': 10.0}` |
| strict | 1.5 | A2_Biomechanical_NoK | ElasticNet | 69 | 44 | 0.474 | 0.168 | 0.496 | 9.62 | 401.7 | 0.306 | `{'alpha': 0.1, 'l1_ratio': 0.3}` |
| strict | 1.5 | A2_Biomechanical_NoK | Ridge | 69 | 44 | 0.478 | 0.120 | 0.483 | 9.94 | 412.2 | 0.357 | `{'alpha': 0.01}` |
| strict | 1.5 | B_Clinical | SVM | 69 | 44 | 0.024 | -0.055 | 0.233 | 13.12 | 526.7 | 0.079 | `{'C': 100, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 1.5 | B_Clinical | Random_Forest | 69 | 44 | 0.576 | 0.067 | 0.497 | 11.04 | 479.1 | 0.509 | `{'n_estimators': 50, 'max_depth': 4, 'min_samples_split': 10, 'min_samples_leaf': 4}` |
| strict | 1.5 | B_Clinical | XGBoost | 69 | 44 | 0.332 | 0.120 | 0.487 | 11.30 | 478.4 | 0.212 | `{'learning_rate': 0.005, 'max_depth': 2, 'n_estimators': 100, 'reg_alpha': 2.0, 'reg_lambda': 0.1}` |
| strict | 1.5 | B_Clinical | Neural_Network | 69 | 44 | 0.182 | -0.109 | 0.430 | 12.97 | 528.3 | 0.291 | `{'hidden_layer_sizes': (40,), 'alpha': 0.1, 'learning_rate_init': 0.0001}` |
| strict | 1.5 | B_Clinical | Lasso | 69 | 44 | 0.146 | -0.378 | 0.145 | 13.71 | 590.9 | 0.524 | `{'alpha': 1.0}` |
| strict | 1.5 | B_Clinical | ElasticNet | 69 | 44 | 0.097 | -0.355 | -0.451 | 13.70 | 537.3 | 0.452 | `{'alpha': 1.0, 'l1_ratio': 0.5}` |
| strict | 1.5 | B_Clinical | Ridge | 69 | 44 | 0.146 | -0.380 | 0.144 | 13.71 | 591.3 | 0.526 | `{'alpha': 0.01}` |
| strict | 1.5 | C1_Combined | SVM | 69 | 44 | 0.065 | 0.037 | 0.607 | 13.34 | 504.8 | 0.028 | `{'C': 100, 'epsilon': 800, 'gamma': 0.05}` |
| strict | 1.5 | C1_Combined | Random_Forest | 69 | 44 | 0.676 | 0.266 | 0.617 | 10.41 | 438.9 | 0.410 | `{'n_estimators': 300, 'max_depth': 5, 'min_samples_split': 10, 'min_samples_leaf': 4}` |
| strict | 1.5 | C1_Combined | XGBoost | 69 | 44 | 0.234 | 0.095 | 0.514 | 10.90 | 433.4 | 0.139 | `{'learning_rate': 0.005, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 2.0, 'reg_lambda': 1.0}` |
| strict | 1.5 | C1_Combined | Neural_Network | 69 | 44 | 0.398 | 0.234 | 0.631 | 10.90 | 441.4 | 0.164 | `{'hidden_layer_sizes': (40,), 'alpha': 0.3, 'learning_rate_init': 0.0005}` |
| strict | 1.5 | C1_Combined | Lasso | 69 | 44 | 0.514 | 0.360 | 0.730 | 9.07 | 404.4 | 0.154 | `{'alpha': 0.01}` |
| strict | 1.5 | C1_Combined | ElasticNet | 69 | 44 | 0.485 | 0.387 | 0.730 | 9.40 | 399.2 | 0.098 | `{'alpha': 1.0, 'l1_ratio': 0.7}` |
| strict | 1.5 | C1_Combined | Ridge | 69 | 44 | 0.314 | 0.245 | 0.698 | 11.15 | 449.1 | 0.069 | `{'alpha': 100.0}` |
| strict | 2.0 | A1_Biomechanical_Core | SVM | 69 | 44 | 0.323 | 0.190 | 0.571 | 10.75 | 423.2 | 0.133 | `{'C': 100, 'epsilon': 100, 'gamma': 0.1}` |
| strict | 2.0 | A1_Biomechanical_Core | Random_Forest | 69 | 44 | 0.574 | 0.205 | 0.530 | 11.58 | 435.6 | 0.369 | `{'n_estimators': 200, 'max_depth': 3, 'min_samples_split': 5, 'min_samples_leaf': 4}` |
| strict | 2.0 | A1_Biomechanical_Core | XGBoost | 69 | 44 | 0.620 | 0.283 | 0.579 | 9.26 | 391.7 | 0.337 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 2.0, 'reg_lambda': 2.0}` |
| strict | 2.0 | A1_Biomechanical_Core | Neural_Network | 69 | 44 | 0.371 | 0.158 | 0.557 | 10.86 | 413.3 | 0.213 | `{'hidden_layer_sizes': (100,), 'alpha': 1.0, 'learning_rate_init': 0.001}` |
| strict | 2.0 | A1_Biomechanical_Core | Lasso | 69 | 44 | 0.507 | 0.236 | 0.706 | 10.50 | 410.6 | 0.271 | `{'alpha': 0.01}` |
| strict | 2.0 | A1_Biomechanical_Core | ElasticNet | 69 | 44 | 0.507 | 0.239 | 0.706 | 10.48 | 410.2 | 0.268 | `{'alpha': 0.1, 'l1_ratio': 0.9}` |
| strict | 2.0 | A1_Biomechanical_Core | Ridge | 69 | 44 | 0.507 | 0.241 | 0.706 | 10.46 | 409.9 | 0.266 | `{'alpha': 1.0}` |
| strict | 2.0 | A2_Biomechanical_NoK | SVM | 69 | 44 | 0.277 | 0.119 | 0.484 | 12.94 | 474.1 | 0.158 | `{'C': 2000, 'epsilon': 500, 'gamma': 0.005}` |
| strict | 2.0 | A2_Biomechanical_NoK | Random_Forest | 69 | 44 | 0.750 | 0.261 | 0.611 | 9.56 | 395.7 | 0.489 | `{'n_estimators': 100, 'max_depth': 3, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| strict | 2.0 | A2_Biomechanical_NoK | XGBoost | 69 | 44 | 0.493 | 0.282 | 0.554 | 11.12 | 425.0 | 0.211 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 50, 'reg_alpha': 1.0, 'reg_lambda': 0.5}` |
| strict | 2.0 | A2_Biomechanical_NoK | Neural_Network | 69 | 44 | 0.586 | -0.040 | 0.340 | 11.07 | 477.4 | 0.627 | `{'hidden_layer_sizes': (80,), 'alpha': 0.5, 'learning_rate_init': 0.0001}` |
| strict | 2.0 | A2_Biomechanical_NoK | Lasso | 69 | 44 | 0.580 | 0.210 | 0.678 | 11.03 | 418.6 | 0.370 | `{'alpha': 0.01}` |
| strict | 2.0 | A2_Biomechanical_NoK | ElasticNet | 69 | 44 | 0.580 | 0.211 | 0.678 | 11.03 | 418.6 | 0.369 | `{'alpha': 0.01, 'l1_ratio': 0.7}` |
| strict | 2.0 | A2_Biomechanical_NoK | Ridge | 69 | 44 | 0.567 | 0.228 | 0.667 | 10.85 | 418.0 | 0.338 | `{'alpha': 10.0}` |
| strict | 2.0 | B_Clinical | SVM | 69 | 44 | 0.192 | -0.012 | 0.445 | 12.43 | 476.8 | 0.204 | `{'C': 500, 'epsilon': 300, 'gamma': 0.03}` |
| strict | 2.0 | B_Clinical | Random_Forest | 69 | 44 | 0.456 | -0.108 | 0.200 | 13.82 | 519.3 | 0.564 | `{'n_estimators': 50, 'max_depth': None, 'min_samples_split': 5, 'min_samples_leaf': 4}` |
| strict | 2.0 | B_Clinical | XGBoost | 69 | 44 | 0.195 | -0.020 | 0.419 | 12.98 | 476.9 | 0.215 | `{'learning_rate': 0.005, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 1.0}` |
| strict | 2.0 | B_Clinical | Neural_Network | 69 | 44 | 0.168 | 0.088 | 0.432 | 11.85 | 438.5 | 0.081 | `{'hidden_layer_sizes': (80,), 'alpha': 0.5, 'learning_rate_init': 0.0005}` |
| strict | 2.0 | B_Clinical | Lasso | 69 | 44 | 0.156 | -0.306 | 0.201 | 13.61 | 534.0 | 0.462 | `{'alpha': 0.01}` |
| strict | 2.0 | B_Clinical | ElasticNet | 69 | 44 | 0.156 | -0.306 | 0.201 | 13.61 | 534.0 | 0.462 | `{'alpha': 0.001, 'l1_ratio': 0.9}` |
| strict | 2.0 | B_Clinical | Ridge | 69 | 44 | 0.052 | -0.182 | 0.014 | 13.69 | 475.0 | 0.234 | `{'alpha': 100.0}` |
| strict | 2.0 | C1_Combined | SVM | 69 | 44 | 0.275 | 0.023 | 0.396 | 12.56 | 490.2 | 0.252 | `{'C': 500, 'epsilon': 300, 'gamma': 0.01}` |
| strict | 2.0 | C1_Combined | Random_Forest | 69 | 44 | 0.562 | 0.239 | 0.565 | 11.27 | 428.2 | 0.323 | `{'n_estimators': 50, 'max_depth': 2, 'min_samples_split': 2, 'min_samples_leaf': 2}` |
| strict | 2.0 | C1_Combined | XGBoost | 69 | 44 | 0.465 | 0.236 | 0.599 | 10.39 | 409.8 | 0.229 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 30, 'reg_alpha': 0.5, 'reg_lambda': 0.1}` |
| strict | 2.0 | C1_Combined | Neural_Network | 69 | 44 | 0.356 | 0.046 | 0.405 | 12.16 | 461.2 | 0.310 | `{'hidden_layer_sizes': (60,), 'alpha': 0.3, 'learning_rate_init': 0.001}` |
| strict | 2.0 | C1_Combined | Lasso | 69 | 44 | 0.390 | 0.288 | 0.610 | 10.36 | 383.4 | 0.102 | `{'alpha': 10.0}` |
| strict | 2.0 | C1_Combined | ElasticNet | 69 | 44 | 0.392 | 0.286 | 0.600 | 10.28 | 382.9 | 0.106 | `{'alpha': 0.001, 'l1_ratio': 0.5}` |
| strict | 2.0 | C1_Combined | Ridge | 69 | 44 | 0.392 | 0.285 | 0.596 | 10.29 | 383.0 | 0.106 | `{'alpha': 1.0}` |
| strict | 2.5 | A1_Biomechanical_Core | SVM | 69 | 44 | 0.452 | 0.181 | 0.459 | 12.10 | 467.5 | 0.271 | `{'C': 5000, 'epsilon': 100, 'gamma': 0.1}` |
| strict | 2.5 | A1_Biomechanical_Core | Random_Forest | 69 | 44 | 0.691 | 0.305 | 0.667 | 11.87 | 396.1 | 0.385 | `{'n_estimators': 300, 'max_depth': 3, 'min_samples_split': 2, 'min_samples_leaf': 2}` |
| strict | 2.5 | A1_Biomechanical_Core | XGBoost | 69 | 44 | 0.709 | 0.307 | 0.615 | 11.80 | 403.3 | 0.402 | `{'learning_rate': 0.01, 'max_depth': 3, 'n_estimators': 200, 'reg_alpha': 0.1, 'reg_lambda': 2.0}` |
| strict | 2.5 | A1_Biomechanical_Core | Neural_Network | 69 | 44 | 0.438 | 0.301 | 0.610 | 12.19 | 433.3 | 0.137 | `{'hidden_layer_sizes': (80,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| strict | 2.5 | A1_Biomechanical_Core | Lasso | 69 | 44 | 0.418 | 0.280 | 0.525 | 11.04 | 365.1 | 0.138 | `{'alpha': 10.0}` |
| strict | 2.5 | A1_Biomechanical_Core | ElasticNet | 69 | 44 | 0.390 | 0.237 | 0.646 | 12.03 | 447.2 | 0.153 | `{'alpha': 0.001, 'l1_ratio': 0.9}` |
| strict | 2.5 | A1_Biomechanical_Core | Ridge | 69 | 44 | 0.419 | 0.281 | 0.532 | 10.99 | 364.6 | 0.139 | `{'alpha': 0.01}` |
| strict | 2.5 | A2_Biomechanical_NoK | SVM | 69 | 44 | 0.462 | 0.144 | 0.455 | 13.25 | 487.0 | 0.318 | `{'C': 1000, 'epsilon': 300, 'gamma': 0.03}` |
| strict | 2.5 | A2_Biomechanical_NoK | Random_Forest | 69 | 44 | 0.575 | 0.249 | 0.525 | 12.91 | 443.3 | 0.326 | `{'n_estimators': 100, 'max_depth': 2, 'min_samples_split': 10, 'min_samples_leaf': 1}` |
| strict | 2.5 | A2_Biomechanical_NoK | XGBoost | 69 | 44 | 0.894 | 0.091 | 0.459 | 14.25 | 488.7 | 0.803 | `{'learning_rate': 0.05, 'max_depth': 3, 'n_estimators': 50, 'reg_alpha': 0.5, 'reg_lambda': 0.1}` |
| strict | 2.5 | A2_Biomechanical_NoK | Neural_Network | 69 | 44 | 0.529 | 0.160 | 0.582 | 13.72 | 443.7 | 0.368 | `{'hidden_layer_sizes': (100,), 'alpha': 0.3, 'learning_rate_init': 0.0001}` |
| strict | 2.5 | A2_Biomechanical_NoK | Lasso | 69 | 44 | 0.542 | 0.243 | 0.639 | 12.92 | 392.5 | 0.298 | `{'alpha': 1.0}` |
| strict | 2.5 | A2_Biomechanical_NoK | ElasticNet | 69 | 44 | 0.542 | 0.243 | 0.637 | 12.92 | 392.8 | 0.299 | `{'alpha': 0.01, 'l1_ratio': 0.5}` |
| strict | 2.5 | A2_Biomechanical_NoK | Ridge | 69 | 44 | 0.528 | 0.301 | 0.644 | 12.67 | 387.9 | 0.227 | `{'alpha': 10.0}` |
| strict | 2.5 | B_Clinical | SVM | 69 | 44 | 0.204 | -0.094 | 0.278 | 14.44 | 548.8 | 0.298 | `{'C': 5000, 'epsilon': 100, 'gamma': 0.03}` |
| strict | 2.5 | B_Clinical | Random_Forest | 69 | 44 | 0.593 | -0.074 | 0.369 | 14.90 | 498.9 | 0.668 | `{'n_estimators': 100, 'max_depth': 3, 'min_samples_split': 2, 'min_samples_leaf': 2}` |
| strict | 2.5 | B_Clinical | XGBoost | 69 | 44 | 0.143 | 0.019 | 0.124 | 15.56 | 512.2 | 0.124 | `{'learning_rate': 0.01, 'max_depth': 1, 'n_estimators': 50, 'reg_alpha': 2.0, 'reg_lambda': 0.1}` |
| strict | 2.5 | B_Clinical | Neural_Network | 69 | 44 | 0.141 | 0.071 | 0.389 | 15.20 | 489.9 | 0.069 | `{'hidden_layer_sizes': (40,), 'alpha': 0.5, 'learning_rate_init': 0.001}` |
| strict | 2.5 | B_Clinical | Lasso | 69 | 44 | 0.114 | -0.355 | 0.159 | 17.65 | 578.2 | 0.469 | `{'alpha': 10.0}` |
| strict | 2.5 | B_Clinical | ElasticNet | 69 | 44 | 0.101 | -0.311 | 0.006 | 16.85 | 575.7 | 0.412 | `{'alpha': 1.0, 'l1_ratio': 0.5}` |
| strict | 2.5 | B_Clinical | Ridge | 69 | 44 | 0.289 | -0.353 | 0.355 | 17.17 | 539.5 | 0.643 | `{'alpha': 10.0}` |
| strict | 2.5 | C1_Combined | SVM | 69 | 44 | 0.440 | -0.069 | 0.402 | 13.54 | 475.0 | 0.509 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.03}` |
| strict | 2.5 | C1_Combined | Random_Forest | 69 | 44 | 0.711 | 0.308 | 0.644 | 11.86 | 396.1 | 0.403 | `{'n_estimators': 200, 'max_depth': 3, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| strict | 2.5 | C1_Combined | XGBoost | 69 | 44 | 0.534 | 0.211 | 0.584 | 12.81 | 431.5 | 0.323 | `{'learning_rate': 0.01, 'max_depth': 3, 'n_estimators': 100, 'reg_alpha': 0.1, 'reg_lambda': 2.0}` |
| strict | 2.5 | C1_Combined | Neural_Network | 69 | 44 | 0.562 | 0.144 | 0.482 | 14.20 | 473.0 | 0.418 | `{'hidden_layer_sizes': (80,), 'alpha': 0.5, 'learning_rate_init': 0.0005}` |
| strict | 2.5 | C1_Combined | Lasso | 69 | 44 | 0.408 | 0.317 | 0.640 | 11.67 | 426.8 | 0.091 | `{'alpha': 0.001}` |
| strict | 2.5 | C1_Combined | ElasticNet | 69 | 44 | 0.408 | 0.322 | 0.640 | 11.62 | 425.5 | 0.086 | `{'alpha': 0.01, 'l1_ratio': 0.5}` |
| strict | 2.5 | C1_Combined | Ridge | 69 | 44 | 0.408 | 0.317 | 0.640 | 11.66 | 426.7 | 0.091 | `{'alpha': 0.01}` |
| strict | 3.0 | A1_Biomechanical_Core | SVM | 69 | 44 | 0.315 | 0.131 | 0.471 | 14.66 | 527.6 | 0.184 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.05}` |
| strict | 3.0 | A1_Biomechanical_Core | Random_Forest | 69 | 44 | 0.584 | 0.307 | 0.614 | 13.99 | 454.0 | 0.277 | `{'n_estimators': 300, 'max_depth': 2, 'min_samples_split': 2, 'min_samples_leaf': 1}` |
| strict | 3.0 | A1_Biomechanical_Core | XGBoost | 69 | 44 | 0.892 | 0.376 | 0.687 | 12.63 | 426.9 | 0.516 | `{'learning_rate': 0.05, 'max_depth': 3, 'n_estimators': 100, 'reg_alpha': 0.1, 'reg_lambda': 2.0}` |
| strict | 3.0 | A1_Biomechanical_Core | Neural_Network | 69 | 44 | 0.320 | 0.132 | 0.522 | 16.45 | 524.5 | 0.189 | `{'hidden_layer_sizes': (60,), 'alpha': 0.3, 'learning_rate_init': 0.001}` |
| strict | 3.0 | A1_Biomechanical_Core | Lasso | 69 | 44 | 0.377 | 0.244 | 0.580 | 12.68 | 406.3 | 0.133 | `{'alpha': 0.1}` |
| strict | 3.0 | A1_Biomechanical_Core | ElasticNet | 69 | 44 | 0.377 | 0.243 | 0.580 | 12.69 | 406.5 | 0.133 | `{'alpha': 0.01, 'l1_ratio': 0.5}` |
| strict | 3.0 | A1_Biomechanical_Core | Ridge | 69 | 44 | 0.376 | 0.241 | 0.578 | 12.71 | 407.2 | 0.135 | `{'alpha': 1.0}` |
| strict | 3.0 | A2_Biomechanical_NoK | SVM | 69 | 44 | 0.189 | 0.143 | 0.501 | 14.80 | 529.0 | 0.046 | `{'C': 100, 'epsilon': 300, 'gamma': 0.1}` |
| strict | 3.0 | A2_Biomechanical_NoK | Random_Forest | 69 | 44 | 0.599 | 0.240 | 0.587 | 14.61 | 473.4 | 0.359 | `{'n_estimators': 200, 'max_depth': 2, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| strict | 3.0 | A2_Biomechanical_NoK | XGBoost | 69 | 44 | 0.696 | 0.188 | 0.526 | 14.85 | 476.9 | 0.509 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 200, 'reg_alpha': 0.5, 'reg_lambda': 1.0}` |
| strict | 3.0 | A2_Biomechanical_NoK | Neural_Network | 69 | 44 | 0.262 | 0.209 | 0.483 | 15.50 | 502.2 | 0.053 | `{'hidden_layer_sizes': (100,), 'alpha': 0.3, 'learning_rate_init': 0.0005}` |
| strict | 3.0 | A2_Biomechanical_NoK | Lasso | 69 | 44 | 0.383 | 0.199 | 0.522 | 13.05 | 416.5 | 0.183 | `{'alpha': 10.0}` |
| strict | 3.0 | A2_Biomechanical_NoK | ElasticNet | 69 | 44 | 0.386 | 0.176 | 0.499 | 13.14 | 420.4 | 0.210 | `{'alpha': 0.001, 'l1_ratio': 0.5}` |
| strict | 3.0 | A2_Biomechanical_NoK | Ridge | 69 | 44 | 0.386 | 0.176 | 0.499 | 13.14 | 420.4 | 0.210 | `{'alpha': 0.01}` |
| strict | 3.0 | B_Clinical | SVM | 69 | 44 | 0.181 | 0.144 | 0.518 | 13.74 | 511.8 | 0.037 | `{'C': 2000, 'epsilon': 100, 'gamma': 0.03}` |
| strict | 3.0 | B_Clinical | Random_Forest | 69 | 44 | 0.456 | -0.009 | 0.358 | 17.27 | 538.7 | 0.465 | `{'n_estimators': 200, 'max_depth': 2, 'min_samples_split': 2, 'min_samples_leaf': 1}` |
| strict | 3.0 | B_Clinical | XGBoost | 69 | 44 | 0.627 | -0.103 | 0.358 | 16.93 | 559.8 | 0.729 | `{'learning_rate': 0.01, 'max_depth': 4, 'n_estimators': 100, 'reg_alpha': 2.0, 'reg_lambda': 0.5}` |
| strict | 3.0 | B_Clinical | Neural_Network | 69 | 44 | 0.201 | -0.223 | 0.409 | 20.55 | 648.0 | 0.423 | `{'hidden_layer_sizes': (80,), 'alpha': 0.1, 'learning_rate_init': 0.001}` |
| strict | 3.0 | B_Clinical | Lasso | 69 | 44 | 0.113 | -0.224 | 0.288 | 20.77 | 657.2 | 0.337 | `{'alpha': 0.01}` |
| strict | 3.0 | B_Clinical | ElasticNet | 69 | 44 | 0.112 | -0.195 | 0.290 | 20.75 | 651.1 | 0.307 | `{'alpha': 0.1, 'l1_ratio': 0.1}` |
| strict | 3.0 | B_Clinical | Ridge | 69 | 44 | 0.113 | -0.223 | 0.288 | 20.77 | 657.0 | 0.336 | `{'alpha': 0.1}` |
| strict | 3.0 | C1_Combined | SVM | 69 | 44 | 0.267 | 0.077 | 0.453 | 16.36 | 587.6 | 0.189 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.03}` |
| strict | 3.0 | C1_Combined | Random_Forest | 69 | 44 | 0.574 | 0.261 | 0.575 | 14.48 | 470.4 | 0.313 | `{'n_estimators': 200, 'max_depth': 4, 'min_samples_split': 10, 'min_samples_leaf': 4}` |
| strict | 3.0 | C1_Combined | XGBoost | 69 | 44 | 0.551 | 0.220 | 0.572 | 15.14 | 485.9 | 0.330 | `{'learning_rate': 0.05, 'max_depth': 2, 'n_estimators': 30, 'reg_alpha': 0.1, 'reg_lambda': 1.0}` |
| strict | 3.0 | C1_Combined | Neural_Network | 69 | 44 | 0.284 | 0.168 | 0.464 | 15.68 | 516.9 | 0.116 | `{'hidden_layer_sizes': (100,), 'alpha': 0.5, 'learning_rate_init': 0.0001}` |
| strict | 3.0 | C1_Combined | Lasso | 69 | 44 | 0.382 | 0.238 | 0.540 | 12.71 | 404.9 | 0.144 | `{'alpha': 0.001}` |
| strict | 3.0 | C1_Combined | ElasticNet | 69 | 44 | 0.382 | 0.238 | 0.540 | 12.71 | 404.9 | 0.144 | `{'alpha': 0.001, 'l1_ratio': 0.7}` |
| strict | 3.0 | C1_Combined | Ridge | 69 | 44 | 0.308 | 0.141 | 0.585 | 14.43 | 517.7 | 0.167 | `{'alpha': 0.01}` |
| strict | 3.5 | A1_Biomechanical_Core | SVM | 69 | 44 | 0.220 | 0.053 | 0.539 | 17.58 | 544.0 | 0.167 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.001}` |
| strict | 3.5 | A1_Biomechanical_Core | Random_Forest | 69 | 44 | 0.651 | 0.215 | 0.475 | 17.36 | 565.0 | 0.436 | `{'n_estimators': 300, 'max_depth': 5, 'min_samples_split': 5, 'min_samples_leaf': 4}` |
| strict | 3.5 | A1_Biomechanical_Core | XGBoost | 69 | 44 | 0.109 | 0.019 | 0.470 | 19.75 | 561.6 | 0.090 | `{'learning_rate': 0.005, 'max_depth': 1, 'n_estimators': 50, 'reg_alpha': 2.0, 'reg_lambda': 0.5}` |
| strict | 3.5 | A1_Biomechanical_Core | Neural_Network | 69 | 44 | 0.106 | 0.092 | 0.323 | 20.83 | 614.2 | 0.013 | `{'hidden_layer_sizes': (60,), 'alpha': 0.5, 'learning_rate_init': 0.0005}` |
| strict | 3.5 | A1_Biomechanical_Core | Lasso | 69 | 44 | 0.326 | 0.198 | 0.568 | 15.08 | 442.6 | 0.128 | `{'alpha': 0.001}` |
| strict | 3.5 | A1_Biomechanical_Core | ElasticNet | 69 | 44 | 0.308 | 0.177 | 0.551 | 15.53 | 451.4 | 0.130 | `{'alpha': 1.0, 'l1_ratio': 0.7}` |
| strict | 3.5 | A1_Biomechanical_Core | Ridge | 69 | 44 | 0.326 | 0.198 | 0.567 | 15.09 | 443.0 | 0.128 | `{'alpha': 1.0}` |
| strict | 3.5 | A2_Biomechanical_NoK | SVM | 69 | 44 | 0.305 | 0.206 | 0.529 | 14.55 | 440.3 | 0.099 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 3.5 | A2_Biomechanical_NoK | Random_Forest | 69 | 44 | 0.921 | 0.058 | 0.466 | 17.95 | 617.9 | 0.864 | `{'n_estimators': 300, 'max_depth': 5, 'min_samples_split': 2, 'min_samples_leaf': 1}` |
| strict | 3.5 | A2_Biomechanical_NoK | XGBoost | 69 | 44 | 0.942 | 0.074 | 0.428 | 15.56 | 514.7 | 0.868 | `{'learning_rate': 0.05, 'max_depth': 3, 'n_estimators': 100, 'reg_alpha': 1.0, 'reg_lambda': 0.5}` |
| strict | 3.5 | A2_Biomechanical_NoK | Neural_Network | 69 | 44 | 0.565 | 0.131 | 0.400 | 16.76 | 447.5 | 0.434 | `{'hidden_layer_sizes': (100,), 'alpha': 0.3, 'learning_rate_init': 0.0005}` |
| strict | 3.5 | A2_Biomechanical_NoK | Lasso | 69 | 44 | 0.339 | 0.158 | 0.492 | 15.63 | 450.4 | 0.181 | `{'alpha': 0.01}` |
| strict | 3.5 | A2_Biomechanical_NoK | ElasticNet | 69 | 44 | 0.338 | 0.162 | 0.493 | 15.63 | 450.7 | 0.176 | `{'alpha': 0.1, 'l1_ratio': 0.5}` |
| strict | 3.5 | A2_Biomechanical_NoK | Ridge | 69 | 44 | 0.339 | 0.158 | 0.493 | 15.63 | 450.4 | 0.181 | `{'alpha': 0.01}` |
| strict | 3.5 | B_Clinical | SVM | 69 | 44 | 0.192 | 0.047 | 0.331 | 15.48 | 521.0 | 0.145 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.03}` |
| strict | 3.5 | B_Clinical | Random_Forest | 69 | 44 | 0.385 | -0.004 | 0.302 | 18.53 | 568.2 | 0.388 | `{'n_estimators': 50, 'max_depth': 2, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| strict | 3.5 | B_Clinical | XGBoost | 69 | 44 | 0.205 | -0.014 | 0.338 | 19.46 | 571.3 | 0.219 | `{'learning_rate': 0.01, 'max_depth': 2, 'n_estimators': 50, 'reg_alpha': 0.5, 'reg_lambda': 2.0}` |
| strict | 3.5 | B_Clinical | Neural_Network | 69 | 44 | 0.133 | -0.076 | 0.349 | 22.50 | 641.9 | 0.209 | `{'hidden_layer_sizes': (40,), 'alpha': 0.3, 'learning_rate_init': 0.0001}` |
| strict | 3.5 | B_Clinical | Lasso | 69 | 44 | 0.111 | -0.228 | 0.221 | 22.30 | 682.9 | 0.339 | `{'alpha': 0.01}` |
| strict | 3.5 | B_Clinical | ElasticNet | 69 | 44 | 0.105 | -0.151 | 0.224 | 22.29 | 667.4 | 0.256 | `{'alpha': 1.0, 'l1_ratio': 0.7}` |
| strict | 3.5 | B_Clinical | Ridge | 69 | 44 | 0.065 | -0.078 | 0.231 | 22.57 | 654.5 | 0.144 | `{'alpha': 100.0}` |
| strict | 3.5 | C1_Combined | SVM | 69 | 44 | 0.188 | 0.159 | 0.472 | 16.97 | 589.7 | 0.029 | `{'C': 1000, 'epsilon': 300, 'gamma': 0.01}` |
| strict | 3.5 | C1_Combined | Random_Forest | 69 | 44 | 0.787 | 0.158 | 0.450 | 15.40 | 515.9 | 0.629 | `{'n_estimators': 100, 'max_depth': 4, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| strict | 3.5 | C1_Combined | XGBoost | 69 | 44 | 0.935 | -0.036 | 0.457 | 17.63 | 638.3 | 0.971 | `{'learning_rate': 0.05, 'max_depth': 4, 'n_estimators': 50, 'reg_alpha': 1.0, 'reg_lambda': 0.5}` |
| strict | 3.5 | C1_Combined | Neural_Network | 69 | 44 | 0.255 | -0.042 | 0.301 | 17.51 | 506.0 | 0.297 | `{'hidden_layer_sizes': (60,), 'alpha': 0.5, 'learning_rate_init': 0.0001}` |
| strict | 3.5 | C1_Combined | Lasso | 69 | 44 | 0.334 | 0.197 | 0.513 | 15.18 | 441.6 | 0.137 | `{'alpha': 0.1}` |
| strict | 3.5 | C1_Combined | ElasticNet | 69 | 44 | 0.276 | 0.112 | 0.484 | 16.57 | 470.4 | 0.164 | `{'alpha': 1.0, 'l1_ratio': 0.3}` |
| strict | 3.5 | C1_Combined | Ridge | 69 | 44 | 0.334 | 0.196 | 0.513 | 15.19 | 441.7 | 0.138 | `{'alpha': 0.1}` |
| strict | 4.0 | A1_Biomechanical_Core | SVM | 69 | 44 | 0.180 | 0.142 | 0.515 | 15.71 | 566.7 | 0.039 | `{'C': 1000, 'epsilon': 100, 'gamma': 0.03}` |
| strict | 4.0 | A1_Biomechanical_Core | Random_Forest | 69 | 44 | 0.726 | 0.167 | 0.540 | 20.08 | 633.5 | 0.560 | `{'n_estimators': 100, 'max_depth': 4, 'min_samples_split': 10, 'min_samples_leaf': 1}` |
| strict | 4.0 | A1_Biomechanical_Core | XGBoost | 69 | 44 | 0.178 | 0.050 | 0.427 | 22.18 | 605.3 | 0.128 | `{'learning_rate': 0.005, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.1, 'reg_lambda': 1.0}` |
| strict | 4.0 | A1_Biomechanical_Core | Neural_Network | 69 | 44 | 0.211 | 0.157 | 0.322 | 22.78 | 639.0 | 0.054 | `{'hidden_layer_sizes': (60,), 'alpha': 0.5, 'learning_rate_init': 0.001}` |
| strict | 4.0 | A1_Biomechanical_Core | Lasso | 69 | 44 | 0.316 | 0.108 | 0.486 | 20.04 | 635.1 | 0.208 | `{'alpha': 0.001}` |
| strict | 4.0 | A1_Biomechanical_Core | ElasticNet | 69 | 44 | 0.301 | 0.139 | 0.481 | 20.74 | 630.9 | 0.162 | `{'alpha': 1.0, 'l1_ratio': 0.7}` |
| strict | 4.0 | A1_Biomechanical_Core | Ridge | 69 | 44 | 0.163 | 0.167 | 0.513 | 19.99 | 560.5 | -0.004 | `{'alpha': 100.0}` |
| strict | 4.0 | A2_Biomechanical_NoK | SVM | 69 | 44 | 0.207 | 0.081 | 0.434 | 15.82 | 590.0 | 0.125 | `{'C': 2000, 'epsilon': 100, 'gamma': 0.005}` |
| strict | 4.0 | A2_Biomechanical_NoK | Random_Forest | 69 | 44 | 0.846 | -0.064 | 0.376 | 22.61 | 620.6 | 0.910 | `{'n_estimators': 50, 'max_depth': 5, 'min_samples_split': 2, 'min_samples_leaf': 1}` |
| strict | 4.0 | A2_Biomechanical_NoK | XGBoost | 69 | 44 | 0.180 | 0.020 | 0.519 | 24.97 | 682.6 | 0.159 | `{'learning_rate': 0.005, 'max_depth': 3, 'n_estimators': 30, 'reg_alpha': 0.5, 'reg_lambda': 0.1}` |
| strict | 4.0 | A2_Biomechanical_NoK | Neural_Network | 69 | 44 | 0.239 | 0.195 | 0.456 | 19.72 | 548.9 | 0.044 | `{'hidden_layer_sizes': (100,), 'alpha': 0.5, 'learning_rate_init': 0.001}` |
| strict | 4.0 | A2_Biomechanical_NoK | Lasso | 69 | 44 | 0.428 | 0.192 | 0.541 | 20.01 | 582.5 | 0.236 | `{'alpha': 1.0}` |
| strict | 4.0 | A2_Biomechanical_NoK | ElasticNet | 69 | 44 | 0.428 | 0.190 | 0.541 | 20.02 | 582.7 | 0.238 | `{'alpha': 0.001, 'l1_ratio': 0.9}` |
| strict | 4.0 | A2_Biomechanical_NoK | Ridge | 69 | 44 | 0.269 | 0.113 | 0.507 | 22.93 | 640.9 | 0.156 | `{'alpha': 100.0}` |
| strict | 4.0 | B_Clinical | SVM | 69 | 44 | 0.008 | -0.019 | 0.163 | 20.96 | 615.7 | 0.027 | `{'C': 1000, 'epsilon': 500, 'gamma': 0.001}` |
| strict | 4.0 | B_Clinical | Random_Forest | 69 | 44 | 0.473 | 0.018 | 0.332 | 20.38 | 596.4 | 0.455 | `{'n_estimators': 200, 'max_depth': 5, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| strict | 4.0 | B_Clinical | XGBoost | 69 | 44 | 0.035 | -0.021 | 0.102 | 22.29 | 616.6 | 0.056 | `{'learning_rate': 0.001, 'max_depth': 4, 'n_estimators': 30, 'reg_alpha': 0.5, 'reg_lambda': 0.1}` |
| strict | 4.0 | B_Clinical | Neural_Network | 69 | 44 | 0.220 | 0.033 | 0.279 | 23.10 | 597.7 | 0.187 | `{'hidden_layer_sizes': (60,), 'alpha': 0.3, 'learning_rate_init': 0.0005}` |
| strict | 4.0 | B_Clinical | Lasso | 69 | 44 | 0.154 | -0.271 | 0.250 | 25.46 | 741.4 | 0.425 | `{'alpha': 10.0}` |
| strict | 4.0 | B_Clinical | ElasticNet | 69 | 44 | 0.112 | -0.160 | 0.222 | 23.58 | 659.1 | 0.272 | `{'alpha': 1.0, 'l1_ratio': 0.1}` |
| strict | 4.0 | B_Clinical | Ridge | 69 | 44 | 0.071 | -0.010 | 0.262 | 21.63 | 609.1 | 0.081 | `{'alpha': 100.0}` |
| strict | 4.0 | C1_Combined | SVM | 69 | 44 | 0.290 | 0.064 | 0.342 | 19.16 | 589.7 | 0.226 | `{'C': 500, 'epsilon': 300, 'gamma': 0.1}` |
| strict | 4.0 | C1_Combined | Random_Forest | 69 | 44 | 0.550 | 0.116 | 0.431 | 21.45 | 657.2 | 0.434 | `{'n_estimators': 200, 'max_depth': 2, 'min_samples_split': 10, 'min_samples_leaf': 1}` |
| strict | 4.0 | C1_Combined | XGBoost | 69 | 44 | 0.110 | 0.038 | 0.360 | 21.49 | 598.8 | 0.072 | `{'learning_rate': 0.01, 'max_depth': 1, 'n_estimators': 30, 'reg_alpha': 2.0, 'reg_lambda': 2.0}` |
| strict | 4.0 | C1_Combined | Neural_Network | 69 | 44 | 0.455 | -0.006 | 0.390 | 21.37 | 603.5 | 0.460 | `{'hidden_layer_sizes': (80,), 'alpha': 0.3, 'learning_rate_init': 0.0005}` |
| strict | 4.0 | C1_Combined | Lasso | 69 | 44 | 0.395 | 0.116 | 0.480 | 18.73 | 500.1 | 0.278 | `{'alpha': 0.1}` |
| strict | 4.0 | C1_Combined | ElasticNet | 69 | 44 | 0.290 | 0.164 | 0.494 | 21.07 | 627.3 | 0.126 | `{'alpha': 1.0, 'l1_ratio': 0.3}` |
| strict | 4.0 | C1_Combined | Ridge | 69 | 44 | 0.395 | 0.119 | 0.480 | 18.73 | 500.3 | 0.276 | `{'alpha': 1.0}` |
| strict | 4.5 | A1_Biomechanical_Core | SVM | 69 | 44 | 0.297 | 0.133 | 0.513 | 21.44 | 562.6 | 0.164 | `{'C': 2000, 'epsilon': 500, 'gamma': 0.05}` |
| strict | 4.5 | A1_Biomechanical_Core | Random_Forest | 69 | 44 | 0.838 | 0.330 | 0.602 | 18.96 | 553.0 | 0.508 | `{'n_estimators': 300, 'max_depth': 4, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| strict | 4.5 | A1_Biomechanical_Core | XGBoost | 69 | 44 | 0.686 | 0.113 | 0.527 | 20.74 | 564.3 | 0.573 | `{'learning_rate': 0.1, 'max_depth': 2, 'n_estimators': 30, 'reg_alpha': 1.0, 'reg_lambda': 0.1}` |
| strict | 4.5 | A1_Biomechanical_Core | Neural_Network | 69 | 44 | 0.354 | 0.256 | 0.555 | 21.41 | 592.5 | 0.099 | `{'hidden_layer_sizes': (60,), 'alpha': 0.5, 'learning_rate_init': 0.001}` |
| strict | 4.5 | A1_Biomechanical_Core | Lasso | 69 | 44 | 0.362 | 0.264 | 0.592 | 20.65 | 592.4 | 0.098 | `{'alpha': 0.001}` |
| strict | 4.5 | A1_Biomechanical_Core | ElasticNet | 69 | 44 | 0.322 | 0.252 | 0.573 | 22.55 | 599.5 | 0.070 | `{'alpha': 1.0, 'l1_ratio': 0.5}` |
| strict | 4.5 | A1_Biomechanical_Core | Ridge | 69 | 44 | 0.362 | 0.264 | 0.592 | 20.65 | 592.4 | 0.097 | `{'alpha': 0.01}` |
| strict | 4.5 | A2_Biomechanical_NoK | SVM | 69 | 44 | 0.397 | 0.305 | 0.602 | 21.07 | 572.6 | 0.092 | `{'C': 5000, 'epsilon': 500, 'gamma': 0.01}` |
| strict | 4.5 | A2_Biomechanical_NoK | Random_Forest | 69 | 44 | 0.801 | 0.308 | 0.605 | 20.43 | 560.4 | 0.493 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| strict | 4.5 | A2_Biomechanical_NoK | XGBoost | 69 | 44 | 0.770 | 0.219 | 0.561 | 21.24 | 601.5 | 0.551 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 200, 'reg_alpha': 1.0, 'reg_lambda': 2.0}` |
| strict | 4.5 | A2_Biomechanical_NoK | Neural_Network | 69 | 44 | 0.438 | 0.148 | 0.430 | 21.02 | 526.2 | 0.290 | `{'hidden_layer_sizes': (40,), 'alpha': 0.3, 'learning_rate_init': 0.0005}` |
| strict | 4.5 | A2_Biomechanical_NoK | Lasso | 69 | 44 | 0.411 | 0.298 | 0.607 | 20.92 | 574.1 | 0.112 | `{'alpha': 10.0}` |
| strict | 4.5 | A2_Biomechanical_NoK | ElasticNet | 69 | 44 | 0.412 | 0.292 | 0.605 | 20.85 | 575.6 | 0.120 | `{'alpha': 0.001, 'l1_ratio': 0.3}` |
| strict | 4.5 | A2_Biomechanical_NoK | Ridge | 69 | 44 | 0.412 | 0.292 | 0.605 | 20.85 | 575.6 | 0.120 | `{'alpha': 0.01}` |
| strict | 4.5 | B_Clinical | SVM | 69 | 44 | 0.479 | 0.116 | 0.639 | 22.12 | 562.6 | 0.363 | `{'C': 1000, 'epsilon': 500, 'gamma': 0.1}` |
| strict | 4.5 | B_Clinical | Random_Forest | 69 | 44 | 0.527 | 0.011 | 0.320 | 25.97 | 681.5 | 0.516 | `{'n_estimators': 300, 'max_depth': 3, 'min_samples_split': 10, 'min_samples_leaf': 4}` |
| strict | 4.5 | B_Clinical | XGBoost | 69 | 44 | 0.403 | 0.134 | 0.444 | 21.85 | 561.4 | 0.269 | `{'learning_rate': 0.005, 'max_depth': 2, 'n_estimators': 200, 'reg_alpha': 0.5, 'reg_lambda': 0.1}` |
| strict | 4.5 | B_Clinical | Neural_Network | 69 | 44 | 0.306 | 0.134 | 0.391 | 25.47 | 645.0 | 0.172 | `{'hidden_layer_sizes': (60,), 'alpha': 0.1, 'learning_rate_init': 0.0005}` |
| strict | 4.5 | B_Clinical | Lasso | 69 | 44 | 0.156 | -0.103 | 0.232 | 26.65 | 719.9 | 0.260 | `{'alpha': 0.01}` |
| strict | 4.5 | B_Clinical | ElasticNet | 69 | 44 | 0.107 | -0.065 | 0.283 | 23.45 | 616.8 | 0.172 | `{'alpha': 1.0, 'l1_ratio': 0.3}` |
| strict | 4.5 | B_Clinical | Ridge | 69 | 44 | 0.076 | -0.010 | 0.293 | 23.46 | 606.6 | 0.086 | `{'alpha': 100.0}` |
| strict | 4.5 | C1_Combined | SVM | 69 | 44 | 0.395 | 0.233 | 0.543 | 20.53 | 605.9 | 0.162 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.03}` |
| strict | 4.5 | C1_Combined | Random_Forest | 69 | 44 | 0.700 | 0.298 | 0.602 | 21.08 | 573.2 | 0.402 | `{'n_estimators': 100, 'max_depth': 4, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| strict | 4.5 | C1_Combined | XGBoost | 69 | 44 | 0.407 | 0.250 | 0.601 | 23.21 | 599.7 | 0.157 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 30, 'reg_alpha': 2.0, 'reg_lambda': 1.0}` |
| strict | 4.5 | C1_Combined | Neural_Network | 69 | 44 | 0.456 | 0.216 | 0.529 | 22.54 | 613.1 | 0.241 | `{'hidden_layer_sizes': (80,), 'alpha': 0.5, 'learning_rate_init': 0.0001}` |
| strict | 4.5 | C1_Combined | Lasso | 69 | 44 | 0.329 | 0.256 | 0.541 | 18.89 | 522.9 | 0.073 | `{'alpha': 0.01}` |
| strict | 4.5 | C1_Combined | ElasticNet | 69 | 44 | 0.388 | 0.260 | 0.591 | 21.58 | 595.9 | 0.129 | `{'alpha': 0.1, 'l1_ratio': 0.1}` |
| strict | 4.5 | C1_Combined | Ridge | 69 | 44 | 0.382 | 0.284 | 0.595 | 21.48 | 587.1 | 0.098 | `{'alpha': 10.0}` |
| strict | 5.0 | A1_Biomechanical_Core | SVM | 69 | 44 | 0.061 | -0.091 | 0.574 | 33.08 | 777.4 | 0.151 | `{'C': 2000, 'epsilon': 800, 'gamma': 0.001}` |
| strict | 5.0 | A1_Biomechanical_Core | Random_Forest | 69 | 44 | 0.674 | 0.215 | 0.529 | 21.97 | 643.9 | 0.460 | `{'n_estimators': 300, 'max_depth': 3, 'min_samples_split': 5, 'min_samples_leaf': 4}` |
| strict | 5.0 | A1_Biomechanical_Core | XGBoost | 69 | 44 | 0.305 | 0.103 | 0.438 | 23.57 | 615.0 | 0.202 | `{'learning_rate': 0.01, 'max_depth': 4, 'n_estimators': 30, 'reg_alpha': 0.5, 'reg_lambda': 1.0}` |
| strict | 5.0 | A1_Biomechanical_Core | Neural_Network | 69 | 44 | 0.489 | 0.179 | 0.588 | 21.69 | 546.1 | 0.310 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.5, 'learning_rate_init': 0.0001}` |
| strict | 5.0 | A1_Biomechanical_Core | Lasso | 69 | 44 | 0.385 | 0.236 | 0.625 | 23.51 | 648.1 | 0.149 | `{'alpha': 10.0}` |
| strict | 5.0 | A1_Biomechanical_Core | ElasticNet | 69 | 44 | 0.382 | 0.240 | 0.622 | 23.85 | 650.3 | 0.142 | `{'alpha': 1.0, 'l1_ratio': 0.9}` |
| strict | 5.0 | A1_Biomechanical_Core | Ridge | 69 | 44 | 0.385 | 0.231 | 0.626 | 23.63 | 649.2 | 0.155 | `{'alpha': 0.1}` |
| strict | 5.0 | A2_Biomechanical_NoK | SVM | 69 | 44 | 0.144 | -0.003 | 0.550 | 27.18 | 758.1 | 0.148 | `{'C': 500, 'epsilon': 500, 'gamma': 0.005}` |
| strict | 5.0 | A2_Biomechanical_NoK | Random_Forest | 69 | 44 | 0.801 | 0.150 | 0.502 | 23.22 | 669.1 | 0.651 | `{'n_estimators': 50, 'max_depth': 5, 'min_samples_split': 10, 'min_samples_leaf': 1}` |
| strict | 5.0 | A2_Biomechanical_NoK | XGBoost | 69 | 44 | 0.997 | 0.062 | 0.598 | 22.27 | 706.6 | 0.935 | `{'learning_rate': 0.05, 'max_depth': 4, 'n_estimators': 100, 'reg_alpha': 1.0, 'reg_lambda': 0.1}` |
| strict | 5.0 | A2_Biomechanical_NoK | Neural_Network | 69 | 44 | 0.631 | 0.140 | 0.476 | 22.43 | 705.0 | 0.491 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.5, 'learning_rate_init': 0.001}` |
| strict | 5.0 | A2_Biomechanical_NoK | Lasso | 69 | 44 | 0.417 | 0.214 | 0.590 | 23.34 | 658.2 | 0.202 | `{'alpha': 0.1}` |
| strict | 5.0 | A2_Biomechanical_NoK | ElasticNet | 69 | 44 | 0.395 | 0.213 | 0.579 | 24.28 | 668.2 | 0.182 | `{'alpha': 1.0, 'l1_ratio': 0.7}` |
| strict | 5.0 | A2_Biomechanical_NoK | Ridge | 69 | 44 | 0.417 | 0.214 | 0.590 | 23.35 | 658.3 | 0.202 | `{'alpha': 0.1}` |
| strict | 5.0 | B_Clinical | SVM | 69 | 44 | 0.525 | 0.134 | 0.480 | 22.07 | 582.4 | 0.391 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.05}` |
| strict | 5.0 | B_Clinical | Random_Forest | 69 | 44 | 0.727 | 0.075 | 0.506 | 21.14 | 575.2 | 0.652 | `{'n_estimators': 300, 'max_depth': 4, 'min_samples_split': 5, 'min_samples_leaf': 2}` |
| strict | 5.0 | B_Clinical | XGBoost | 69 | 44 | 0.463 | 0.088 | 0.368 | 25.89 | 720.4 | 0.375 | `{'learning_rate': 0.005, 'max_depth': 2, 'n_estimators': 200, 'reg_alpha': 0.5, 'reg_lambda': 2.0}` |
| strict | 5.0 | B_Clinical | Neural_Network | 69 | 44 | 0.521 | 0.078 | 0.525 | 23.45 | 576.0 | 0.443 | `{'hidden_layer_sizes': (80, 40), 'alpha': 1.0, 'learning_rate_init': 0.0005}` |
| strict | 5.0 | B_Clinical | Lasso | 69 | 44 | 0.261 | 0.016 | 0.406 | 28.90 | 747.9 | 0.245 | `{'alpha': 0.001}` |
| strict | 5.0 | B_Clinical | ElasticNet | 69 | 44 | 0.249 | 0.051 | 0.402 | 28.75 | 738.1 | 0.198 | `{'alpha': 1.0, 'l1_ratio': 0.7}` |
| strict | 5.0 | B_Clinical | Ridge | 69 | 44 | 0.256 | 0.045 | 0.403 | 28.75 | 739.6 | 0.211 | `{'alpha': 10.0}` |
| strict | 5.0 | C1_Combined | SVM | 69 | 44 | 0.497 | 0.206 | 0.505 | 23.23 | 673.9 | 0.291 | `{'C': 5000, 'epsilon': 100, 'gamma': 0.03}` |
| strict | 5.0 | C1_Combined | Random_Forest | 69 | 44 | 0.578 | 0.249 | 0.583 | 22.60 | 639.1 | 0.330 | `{'n_estimators': 100, 'max_depth': 2, 'min_samples_split': 10, 'min_samples_leaf': 4}` |
| strict | 5.0 | C1_Combined | XGBoost | 69 | 44 | 0.532 | 0.100 | 0.373 | 25.53 | 718.8 | 0.432 | `{'learning_rate': 0.01, 'max_depth': 2, 'n_estimators': 100, 'reg_alpha': 2.0, 'reg_lambda': 0.5}` |
| strict | 5.0 | C1_Combined | Neural_Network | 69 | 44 | 0.368 | 0.114 | 0.454 | 26.94 | 709.1 | 0.254 | `{'hidden_layer_sizes': (60,), 'alpha': 0.3, 'learning_rate_init': 0.0001}` |
| strict | 5.0 | C1_Combined | Lasso | 69 | 44 | 0.461 | 0.190 | 0.615 | 24.53 | 657.6 | 0.271 | `{'alpha': 1.0}` |
| strict | 5.0 | C1_Combined | ElasticNet | 69 | 44 | 0.328 | 0.268 | 0.591 | 20.66 | 555.3 | 0.059 | `{'alpha': 1.0, 'l1_ratio': 0.1}` |
| strict | 5.0 | C1_Combined | Ridge | 69 | 44 | 0.307 | 0.223 | 0.639 | 25.67 | 668.2 | 0.084 | `{'alpha': 100.0}` |
| strict | 5.5 | A1_Biomechanical_Core | SVM | 69 | 44 | 0.437 | 0.270 | 0.578 | 24.64 | 669.3 | 0.167 | `{'C': 1000, 'epsilon': 500, 'gamma': 0.05}` |
| strict | 5.5 | A1_Biomechanical_Core | Random_Forest | 69 | 44 | 0.828 | 0.267 | 0.701 | 22.72 | 651.0 | 0.561 | `{'n_estimators': 300, 'max_depth': 5, 'min_samples_split': 5, 'min_samples_leaf': 2}` |
| strict | 5.5 | A1_Biomechanical_Core | XGBoost | 69 | 44 | 0.461 | 0.209 | 0.560 | 26.90 | 704.7 | 0.252 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 30, 'reg_alpha': 1.0, 'reg_lambda': 0.1}` |
| strict | 5.5 | A1_Biomechanical_Core | Neural_Network | 69 | 44 | 0.655 | 0.138 | 0.482 | 25.83 | 623.8 | 0.517 | `{'hidden_layer_sizes': (100,), 'alpha': 0.3, 'learning_rate_init': 0.0005}` |
| strict | 5.5 | A1_Biomechanical_Core | Lasso | 69 | 44 | 0.430 | 0.284 | 0.649 | 24.33 | 649.6 | 0.146 | `{'alpha': 1.0}` |
| strict | 5.5 | A1_Biomechanical_Core | ElasticNet | 69 | 44 | 0.428 | 0.293 | 0.646 | 24.44 | 650.1 | 0.136 | `{'alpha': 0.1, 'l1_ratio': 0.3}` |
| strict | 5.5 | A1_Biomechanical_Core | Ridge | 69 | 44 | 0.430 | 0.284 | 0.649 | 24.35 | 649.8 | 0.146 | `{'alpha': 0.1}` |
| strict | 5.5 | A2_Biomechanical_NoK | SVM | 69 | 44 | 0.226 | 0.091 | 0.655 | 23.74 | 747.4 | 0.136 | `{'C': 1000, 'epsilon': 300, 'gamma': 0.005}` |
| strict | 5.5 | A2_Biomechanical_NoK | Random_Forest | 69 | 44 | 0.834 | 0.286 | 0.711 | 22.97 | 645.8 | 0.548 | `{'n_estimators': 300, 'max_depth': 4, 'min_samples_split': 2, 'min_samples_leaf': 2}` |
| strict | 5.5 | A2_Biomechanical_NoK | XGBoost | 69 | 44 | 0.969 | 0.297 | 0.674 | 21.93 | 626.4 | 0.671 | `{'learning_rate': 0.1, 'max_depth': 3, 'n_estimators': 50, 'reg_alpha': 0.5, 'reg_lambda': 0.5}` |
| strict | 5.5 | A2_Biomechanical_NoK | Neural_Network | 69 | 44 | 0.508 | 0.133 | 0.454 | 27.08 | 736.9 | 0.375 | `{'hidden_layer_sizes': (80,), 'alpha': 0.3, 'learning_rate_init': 0.0005}` |
| strict | 5.5 | A2_Biomechanical_NoK | Lasso | 69 | 44 | 0.448 | 0.286 | 0.642 | 23.97 | 647.2 | 0.162 | `{'alpha': 0.1}` |
| strict | 5.5 | A2_Biomechanical_NoK | ElasticNet | 69 | 44 | 0.448 | 0.287 | 0.641 | 23.99 | 647.5 | 0.161 | `{'alpha': 0.1, 'l1_ratio': 0.9}` |
| strict | 5.5 | A2_Biomechanical_NoK | Ridge | 69 | 44 | 0.273 | 0.139 | 0.602 | 29.07 | 731.7 | 0.134 | `{'alpha': 100.0}` |
| strict | 5.5 | B_Clinical | SVM | 69 | 44 | 0.452 | 0.234 | 0.573 | 25.07 | 690.5 | 0.217 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.05}` |
| strict | 5.5 | B_Clinical | Random_Forest | 69 | 44 | 0.693 | 0.050 | 0.466 | 25.06 | 662.9 | 0.643 | `{'n_estimators': 200, 'max_depth': 5, 'min_samples_split': 10, 'min_samples_leaf': 1}` |
| strict | 5.5 | B_Clinical | XGBoost | 69 | 44 | 0.470 | 0.220 | 0.497 | 23.56 | 596.0 | 0.249 | `{'learning_rate': 0.01, 'max_depth': 1, 'n_estimators': 200, 'reg_alpha': 1.0, 'reg_lambda': 0.1}` |
| strict | 5.5 | B_Clinical | Neural_Network | 69 | 44 | 0.536 | 0.114 | 0.572 | 28.93 | 730.0 | 0.422 | `{'hidden_layer_sizes': (100,), 'alpha': 0.3, 'learning_rate_init': 0.0001}` |
| strict | 5.5 | B_Clinical | Lasso | 69 | 44 | 0.243 | -0.044 | 0.378 | 31.59 | 798.1 | 0.286 | `{'alpha': 0.001}` |
| strict | 5.5 | B_Clinical | ElasticNet | 69 | 44 | 0.241 | -0.020 | 0.377 | 31.49 | 791.8 | 0.261 | `{'alpha': 0.1, 'l1_ratio': 0.1}` |
| strict | 5.5 | B_Clinical | Ridge | 69 | 44 | 0.129 | -0.023 | 0.334 | 30.93 | 788.1 | 0.151 | `{'alpha': 100.0}` |
| strict | 5.5 | C1_Combined | SVM | 69 | 44 | 0.274 | 0.218 | 0.677 | 23.02 | 701.0 | 0.056 | `{'C': 5000, 'epsilon': 100, 'gamma': 0.001}` |
| strict | 5.5 | C1_Combined | Random_Forest | 69 | 44 | 0.690 | 0.219 | 0.650 | 26.14 | 680.3 | 0.471 | `{'n_estimators': 50, 'max_depth': 2, 'min_samples_split': 2, 'min_samples_leaf': 1}` |
| strict | 5.5 | C1_Combined | XGBoost | 69 | 44 | 0.637 | 0.125 | 0.446 | 26.21 | 728.8 | 0.512 | `{'learning_rate': 0.01, 'max_depth': 3, 'n_estimators': 100, 'reg_alpha': 1.0, 'reg_lambda': 2.0}` |
| strict | 5.5 | C1_Combined | Neural_Network | 69 | 44 | 0.552 | 0.214 | 0.508 | 25.70 | 702.3 | 0.338 | `{'hidden_layer_sizes': (80, 40), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| strict | 5.5 | C1_Combined | Lasso | 69 | 44 | 0.525 | 0.308 | 0.678 | 23.59 | 621.8 | 0.217 | `{'alpha': 0.001}` |
| strict | 5.5 | C1_Combined | ElasticNet | 69 | 44 | 0.525 | 0.308 | 0.678 | 23.59 | 621.8 | 0.217 | `{'alpha': 0.001, 'l1_ratio': 0.7}` |
| strict | 5.5 | C1_Combined | Ridge | 69 | 44 | 0.525 | 0.308 | 0.676 | 23.57 | 621.6 | 0.216 | `{'alpha': 0.1}` |
| strict | 6.0 | A1_Biomechanical_Core | SVM | 69 | 44 | 0.154 | 0.112 | 0.609 | 30.82 | 632.2 | 0.042 | `{'C': 5000, 'epsilon': 1000, 'gamma': 0.05}` |
| strict | 6.0 | A1_Biomechanical_Core | Random_Forest | 69 | 44 | 0.594 | 0.273 | 0.568 | 27.43 | 721.0 | 0.321 | `{'n_estimators': 300, 'max_depth': 2, 'min_samples_split': 2, 'min_samples_leaf': 2}` |
| strict | 6.0 | A1_Biomechanical_Core | XGBoost | 69 | 44 | 0.629 | 0.296 | 0.727 | 22.94 | 609.0 | 0.333 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 30, 'reg_alpha': 0.5, 'reg_lambda': 0.1}` |
| strict | 6.0 | A1_Biomechanical_Core | Neural_Network | 69 | 44 | 0.492 | 0.236 | 0.507 | 27.44 | 755.4 | 0.256 | `{'hidden_layer_sizes': (80,), 'alpha': 0.1, 'learning_rate_init': 0.001}` |
| strict | 6.0 | A1_Biomechanical_Core | Lasso | 69 | 44 | 0.381 | 0.257 | 0.627 | 28.16 | 731.0 | 0.124 | `{'alpha': 1.0}` |
| strict | 6.0 | A1_Biomechanical_Core | ElasticNet | 69 | 44 | 0.381 | 0.258 | 0.626 | 28.15 | 731.0 | 0.123 | `{'alpha': 0.01, 'l1_ratio': 0.1}` |
| strict | 6.0 | A1_Biomechanical_Core | Ridge | 69 | 44 | 0.381 | 0.256 | 0.627 | 28.19 | 731.4 | 0.125 | `{'alpha': 0.01}` |
| strict | 6.0 | A2_Biomechanical_NoK | SVM | 69 | 44 | 0.477 | 0.207 | 0.455 | 31.08 | 763.1 | 0.270 | `{'C': 5000, 'epsilon': 800, 'gamma': 0.1}` |
| strict | 6.0 | A2_Biomechanical_NoK | Random_Forest | 69 | 44 | 0.786 | 0.315 | 0.732 | 22.50 | 592.7 | 0.471 | `{'n_estimators': 200, 'max_depth': 3, 'min_samples_split': 2, 'min_samples_leaf': 2}` |
| strict | 6.0 | A2_Biomechanical_NoK | XGBoost | 69 | 44 | 0.992 | 0.319 | 0.743 | 23.01 | 578.8 | 0.674 | `{'learning_rate': 0.05, 'max_depth': 3, 'n_estimators': 200, 'reg_alpha': 0.5, 'reg_lambda': 0.5}` |
| strict | 6.0 | A2_Biomechanical_NoK | Neural_Network | 69 | 44 | 0.391 | 0.163 | 0.446 | 31.42 | 788.5 | 0.228 | `{'hidden_layer_sizes': (40,), 'alpha': 0.3, 'learning_rate_init': 0.001}` |
| strict | 6.0 | A2_Biomechanical_NoK | Lasso | 69 | 44 | 0.415 | 0.293 | 0.637 | 27.32 | 708.1 | 0.122 | `{'alpha': 0.1}` |
| strict | 6.0 | A2_Biomechanical_NoK | ElasticNet | 69 | 44 | 0.351 | 0.271 | 0.609 | 29.65 | 736.9 | 0.080 | `{'alpha': 1.0, 'l1_ratio': 0.3}` |
| strict | 6.0 | A2_Biomechanical_NoK | Ridge | 69 | 44 | 0.415 | 0.296 | 0.636 | 27.29 | 707.6 | 0.119 | `{'alpha': 1.0}` |
| strict | 6.0 | B_Clinical | SVM | 69 | 44 | 0.443 | 0.189 | 0.492 | 28.46 | 779.6 | 0.255 | `{'C': 1000, 'epsilon': 300, 'gamma': 0.1}` |
| strict | 6.0 | B_Clinical | Random_Forest | 69 | 44 | 0.591 | 0.029 | 0.337 | 31.17 | 833.8 | 0.562 | `{'n_estimators': 300, 'max_depth': 3, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| strict | 6.0 | B_Clinical | XGBoost | 69 | 44 | 0.554 | 0.148 | 0.441 | 31.12 | 781.0 | 0.406 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 200, 'reg_alpha': 1.0, 'reg_lambda': 0.5}` |
| strict | 6.0 | B_Clinical | Neural_Network | 69 | 44 | 0.333 | 0.234 | 0.528 | 31.39 | 754.6 | 0.098 | `{'hidden_layer_sizes': (40,), 'alpha': 0.1, 'learning_rate_init': 0.001}` |
| strict | 6.0 | B_Clinical | Lasso | 69 | 44 | 0.200 | -0.000 | 0.374 | 34.86 | 861.6 | 0.201 | `{'alpha': 1.0}` |
| strict | 6.0 | B_Clinical | ElasticNet | 69 | 44 | 0.200 | -0.001 | 0.374 | 34.87 | 862.0 | 0.201 | `{'alpha': 0.001, 'l1_ratio': 0.7}` |
| strict | 6.0 | B_Clinical | Ridge | 69 | 44 | 0.200 | 0.003 | 0.374 | 34.84 | 860.5 | 0.197 | `{'alpha': 1.0}` |
| strict | 6.0 | C1_Combined | SVM | 69 | 44 | 0.502 | 0.321 | 0.611 | 25.45 | 704.6 | 0.180 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.03}` |
| strict | 6.0 | C1_Combined | Random_Forest | 69 | 44 | 0.742 | 0.202 | 0.514 | 28.30 | 760.8 | 0.540 | `{'n_estimators': 200, 'max_depth': 4, 'min_samples_split': 10, 'min_samples_leaf': 1}` |
| strict | 6.0 | C1_Combined | XGBoost | 69 | 44 | 0.531 | 0.245 | 0.578 | 22.46 | 587.0 | 0.286 | `{'learning_rate': 0.01, 'max_depth': 3, 'n_estimators': 100, 'reg_alpha': 2.0, 'reg_lambda': 2.0}` |
| strict | 6.0 | C1_Combined | Neural_Network | 69 | 44 | 0.547 | 0.215 | 0.533 | 28.09 | 767.8 | 0.332 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.3, 'learning_rate_init': 0.0005}` |
| strict | 6.0 | C1_Combined | Lasso | 69 | 44 | 0.424 | 0.098 | 0.614 | 30.86 | 786.5 | 0.326 | `{'alpha': 0.01}` |
| strict | 6.0 | C1_Combined | ElasticNet | 69 | 44 | 0.421 | 0.237 | 0.620 | 29.43 | 741.1 | 0.184 | `{'alpha': 0.1, 'l1_ratio': 0.3}` |
| strict | 6.0 | C1_Combined | Ridge | 69 | 44 | 0.215 | 0.170 | 0.543 | 24.71 | 614.4 | 0.046 | `{'alpha': 100.0}` |
| lenient | 1.0 | A1_Biomechanical_Core | SVM | 71 | 46 | 0.441 | 0.171 | 0.611 | 12.87 | 653.3 | 0.270 | `{'C': 2000, 'epsilon': 1000, 'gamma': 0.1}` |
| lenient | 1.0 | A1_Biomechanical_Core | Random_Forest | 71 | 46 | 0.661 | 0.438 | 0.699 | 9.49 | 472.9 | 0.223 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 5, 'min_samples_leaf': 4}` |
| lenient | 1.0 | A1_Biomechanical_Core | XGBoost | 71 | 46 | 0.905 | 0.302 | 0.701 | 11.07 | 524.5 | 0.602 | `{'learning_rate': 0.1, 'max_depth': 3, 'n_estimators': 30, 'reg_alpha': 2.0, 'reg_lambda': 0.1}` |
| lenient | 1.0 | A1_Biomechanical_Core | Neural_Network | 71 | 46 | 0.543 | 0.274 | 0.641 | 12.87 | 617.9 | 0.269 | `{'hidden_layer_sizes': (60,), 'alpha': 0.5, 'learning_rate_init': 0.0001}` |
| lenient | 1.0 | A1_Biomechanical_Core | Lasso | 71 | 46 | 0.422 | 0.242 | 0.578 | 12.30 | 638.4 | 0.180 | `{'alpha': 0.01}` |
| lenient | 1.0 | A1_Biomechanical_Core | ElasticNet | 71 | 46 | 0.422 | 0.243 | 0.577 | 12.30 | 638.3 | 0.179 | `{'alpha': 0.01, 'l1_ratio': 0.3}` |
| lenient | 1.0 | A1_Biomechanical_Core | Ridge | 71 | 46 | 0.422 | 0.243 | 0.578 | 12.30 | 638.4 | 0.180 | `{'alpha': 0.1}` |
| lenient | 1.0 | A2_Biomechanical_NoK | SVM | 71 | 46 | 0.255 | 0.090 | 0.549 | 14.59 | 723.3 | 0.165 | `{'C': 5000, 'epsilon': 100, 'gamma': 0.001}` |
| lenient | 1.0 | A2_Biomechanical_NoK | Random_Forest | 71 | 46 | 0.690 | 0.452 | 0.705 | 9.39 | 472.8 | 0.238 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| lenient | 1.0 | A2_Biomechanical_NoK | XGBoost | 71 | 46 | 0.497 | 0.225 | 0.685 | 12.66 | 603.9 | 0.273 | `{'learning_rate': 0.005, 'max_depth': 2, 'n_estimators': 200, 'reg_alpha': 2.0, 'reg_lambda': 2.0}` |
| lenient | 1.0 | A2_Biomechanical_NoK | Neural_Network | 71 | 46 | 0.480 | 0.168 | 0.540 | 12.72 | 602.4 | 0.312 | `{'hidden_layer_sizes': (60,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| lenient | 1.0 | A2_Biomechanical_NoK | Lasso | 71 | 46 | 0.427 | 0.205 | 0.554 | 12.37 | 651.0 | 0.223 | `{'alpha': 0.001}` |
| lenient | 1.0 | A2_Biomechanical_NoK | ElasticNet | 71 | 46 | 0.427 | 0.206 | 0.553 | 12.37 | 650.7 | 0.222 | `{'alpha': 0.01, 'l1_ratio': 0.3}` |
| lenient | 1.0 | A2_Biomechanical_NoK | Ridge | 71 | 46 | 0.417 | 0.215 | 0.548 | 12.39 | 649.4 | 0.202 | `{'alpha': 10.0}` |
| lenient | 1.0 | B_Clinical | SVM | 71 | 46 | 0.461 | 0.210 | 0.539 | 11.77 | 570.5 | 0.251 | `{'C': 1000, 'epsilon': 300, 'gamma': 0.1}` |
| lenient | 1.0 | B_Clinical | Random_Forest | 71 | 46 | 0.645 | 0.297 | 0.664 | 10.46 | 531.2 | 0.349 | `{'n_estimators': 300, 'max_depth': 2, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| lenient | 1.0 | B_Clinical | XGBoost | 71 | 46 | 0.446 | 0.189 | 0.603 | 12.84 | 615.3 | 0.256 | `{'learning_rate': 0.01, 'max_depth': 4, 'n_estimators': 50, 'reg_alpha': 0.1, 'reg_lambda': 1.0}` |
| lenient | 1.0 | B_Clinical | Neural_Network | 71 | 46 | 0.589 | 0.231 | 0.636 | 12.40 | 599.5 | 0.358 | `{'hidden_layer_sizes': (100,), 'alpha': 0.5, 'learning_rate_init': 0.001}` |
| lenient | 1.0 | B_Clinical | Lasso | 71 | 46 | 0.238 | -0.064 | 0.412 | 13.95 | 657.6 | 0.302 | `{'alpha': 10.0}` |
| lenient | 1.0 | B_Clinical | ElasticNet | 71 | 46 | 0.277 | -0.065 | 0.499 | 14.26 | 697.1 | 0.342 | `{'alpha': 0.001, 'l1_ratio': 0.3}` |
| lenient | 1.0 | B_Clinical | Ridge | 71 | 46 | 0.135 | -0.057 | 0.401 | 13.15 | 655.2 | 0.193 | `{'alpha': 100.0}` |
| lenient | 1.0 | C1_Combined | SVM | 71 | 46 | 0.483 | 0.319 | 0.730 | 11.15 | 565.8 | 0.164 | `{'C': 2000, 'epsilon': 800, 'gamma': 0.03}` |
| lenient | 1.0 | C1_Combined | Random_Forest | 71 | 46 | 0.694 | 0.417 | 0.709 | 11.19 | 556.6 | 0.277 | `{'n_estimators': 200, 'max_depth': 2, 'min_samples_split': 2, 'min_samples_leaf': 2}` |
| lenient | 1.0 | C1_Combined | XGBoost | 71 | 46 | 0.896 | 0.341 | 0.685 | 10.89 | 525.3 | 0.555 | `{'learning_rate': 0.05, 'max_depth': 3, 'n_estimators': 50, 'reg_alpha': 0.1, 'reg_lambda': 0.5}` |
| lenient | 1.0 | C1_Combined | Neural_Network | 71 | 46 | 0.629 | 0.342 | 0.688 | 10.49 | 567.3 | 0.286 | `{'hidden_layer_sizes': (40,), 'alpha': 0.1, 'learning_rate_init': 0.0001}` |
| lenient | 1.0 | C1_Combined | Lasso | 71 | 46 | 0.484 | 0.313 | 0.625 | 11.62 | 602.5 | 0.171 | `{'alpha': 1.0}` |
| lenient | 1.0 | C1_Combined | ElasticNet | 71 | 46 | 0.460 | 0.306 | 0.735 | 11.24 | 556.5 | 0.155 | `{'alpha': 1.0, 'l1_ratio': 0.1}` |
| lenient | 1.0 | C1_Combined | Ridge | 71 | 46 | 0.551 | 0.330 | 0.744 | 11.29 | 562.6 | 0.221 | `{'alpha': 10.0}` |
| lenient | 1.5 | A1_Biomechanical_Core | SVM | 71 | 46 | 0.444 | 0.252 | 0.658 | 11.66 | 587.3 | 0.192 | `{'C': 500, 'epsilon': 500, 'gamma': 0.1}` |
| lenient | 1.5 | A1_Biomechanical_Core | Random_Forest | 71 | 46 | 0.704 | 0.453 | 0.742 | 9.53 | 519.7 | 0.251 | `{'n_estimators': 300, 'max_depth': 3, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| lenient | 1.5 | A1_Biomechanical_Core | XGBoost | 71 | 46 | 0.992 | 0.156 | 0.653 | 12.24 | 594.2 | 0.837 | `{'learning_rate': 0.1, 'max_depth': 4, 'n_estimators': 50, 'reg_alpha': 1.0, 'reg_lambda': 0.1}` |
| lenient | 1.5 | A1_Biomechanical_Core | Neural_Network | 71 | 46 | 0.535 | 0.339 | 0.673 | 10.00 | 533.3 | 0.197 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.1, 'learning_rate_init': 0.0001}` |
| lenient | 1.5 | A1_Biomechanical_Core | Lasso | 71 | 46 | 0.508 | 0.403 | 0.695 | 10.42 | 561.7 | 0.105 | `{'alpha': 10.0}` |
| lenient | 1.5 | A1_Biomechanical_Core | ElasticNet | 71 | 46 | 0.509 | 0.388 | 0.688 | 10.52 | 568.9 | 0.121 | `{'alpha': 0.001, 'l1_ratio': 0.9}` |
| lenient | 1.5 | A1_Biomechanical_Core | Ridge | 71 | 46 | 0.509 | 0.388 | 0.688 | 10.53 | 568.8 | 0.121 | `{'alpha': 0.1}` |
| lenient | 1.5 | A2_Biomechanical_NoK | SVM | 71 | 46 | 0.376 | -0.004 | 0.543 | 14.00 | 636.3 | 0.380 | `{'C': 2000, 'epsilon': 800, 'gamma': 0.1}` |
| lenient | 1.5 | A2_Biomechanical_NoK | Random_Forest | 71 | 46 | 0.800 | 0.470 | 0.719 | 9.17 | 498.7 | 0.330 | `{'n_estimators': 200, 'max_depth': 3, 'min_samples_split': 2, 'min_samples_leaf': 2}` |
| lenient | 1.5 | A2_Biomechanical_NoK | XGBoost | 71 | 46 | 0.757 | 0.420 | 0.668 | 10.39 | 547.2 | 0.337 | `{'learning_rate': 0.05, 'max_depth': 3, 'n_estimators': 30, 'reg_alpha': 0.5, 'reg_lambda': 2.0}` |
| lenient | 1.5 | A2_Biomechanical_NoK | Neural_Network | 71 | 46 | 0.588 | 0.163 | 0.499 | 10.81 | 619.2 | 0.425 | `{'hidden_layer_sizes': (40,), 'alpha': 1.0, 'learning_rate_init': 0.001}` |
| lenient | 1.5 | A2_Biomechanical_NoK | Lasso | 71 | 46 | 0.457 | 0.177 | 0.553 | 10.26 | 575.3 | 0.280 | `{'alpha': 0.1}` |
| lenient | 1.5 | A2_Biomechanical_NoK | ElasticNet | 71 | 46 | 0.457 | 0.191 | 0.552 | 10.28 | 572.2 | 0.266 | `{'alpha': 0.1, 'l1_ratio': 0.7}` |
| lenient | 1.5 | A2_Biomechanical_NoK | Ridge | 71 | 46 | 0.511 | 0.178 | 0.503 | 11.38 | 631.1 | 0.333 | `{'alpha': 10.0}` |
| lenient | 1.5 | B_Clinical | SVM | 71 | 46 | 0.126 | -0.020 | 0.550 | 15.50 | 728.8 | 0.146 | `{'C': 100, 'epsilon': 800, 'gamma': 0.1}` |
| lenient | 1.5 | B_Clinical | Random_Forest | 71 | 46 | 0.526 | 0.232 | 0.577 | 11.24 | 579.7 | 0.294 | `{'n_estimators': 100, 'max_depth': 3, 'min_samples_split': 10, 'min_samples_leaf': 4}` |
| lenient | 1.5 | B_Clinical | XGBoost | 71 | 46 | 0.386 | 0.204 | 0.622 | 13.36 | 646.6 | 0.182 | `{'learning_rate': 0.01, 'max_depth': 3, 'n_estimators': 50, 'reg_alpha': 0.1, 'reg_lambda': 2.0}` |
| lenient | 1.5 | B_Clinical | Neural_Network | 71 | 46 | 0.719 | 0.234 | 0.614 | 13.83 | 627.0 | 0.485 | `{'hidden_layer_sizes': (40,), 'alpha': 1.0, 'learning_rate_init': 0.001}` |
| lenient | 1.5 | B_Clinical | Lasso | 71 | 46 | 0.247 | 0.094 | 0.505 | 14.01 | 628.9 | 0.153 | `{'alpha': 1.0}` |
| lenient | 1.5 | B_Clinical | ElasticNet | 71 | 46 | 0.247 | 0.094 | 0.505 | 14.01 | 629.1 | 0.154 | `{'alpha': 0.001, 'l1_ratio': 0.3}` |
| lenient | 1.5 | B_Clinical | Ridge | 71 | 46 | 0.247 | 0.094 | 0.505 | 14.01 | 629.0 | 0.153 | `{'alpha': 0.1}` |
| lenient | 1.5 | C1_Combined | SVM | 71 | 46 | 0.533 | 0.338 | 0.733 | 9.82 | 528.0 | 0.195 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.03}` |
| lenient | 1.5 | C1_Combined | Random_Forest | 71 | 46 | 0.723 | 0.472 | 0.730 | 9.38 | 512.8 | 0.251 | `{'n_estimators': 300, 'max_depth': 5, 'min_samples_split': 5, 'min_samples_leaf': 4}` |
| lenient | 1.5 | C1_Combined | XGBoost | 71 | 46 | 0.501 | 0.329 | 0.671 | 11.61 | 590.1 | 0.173 | `{'learning_rate': 0.01, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 2.0, 'reg_lambda': 0.5}` |
| lenient | 1.5 | C1_Combined | Neural_Network | 71 | 46 | 0.573 | 0.380 | 0.694 | 11.12 | 570.0 | 0.193 | `{'hidden_layer_sizes': (100,), 'alpha': 0.5, 'learning_rate_init': 0.0005}` |
| lenient | 1.5 | C1_Combined | Lasso | 71 | 46 | 0.578 | 0.538 | 0.744 | 9.27 | 491.4 | 0.040 | `{'alpha': 10.0}` |
| lenient | 1.5 | C1_Combined | ElasticNet | 71 | 46 | 0.578 | 0.530 | 0.740 | 9.40 | 496.7 | 0.049 | `{'alpha': 0.01, 'l1_ratio': 0.7}` |
| lenient | 1.5 | C1_Combined | Ridge | 71 | 46 | 0.578 | 0.529 | 0.740 | 9.40 | 496.9 | 0.049 | `{'alpha': 0.01}` |
| lenient | 2.0 | A1_Biomechanical_Core | SVM | 71 | 46 | 0.216 | 0.209 | 0.613 | 12.26 | 518.6 | 0.007 | `{'C': 2000, 'epsilon': 500, 'gamma': 0.005}` |
| lenient | 2.0 | A1_Biomechanical_Core | Random_Forest | 71 | 46 | 0.644 | 0.392 | 0.693 | 10.48 | 479.7 | 0.252 | `{'n_estimators': 50, 'max_depth': 2, 'min_samples_split': 10, 'min_samples_leaf': 1}` |
| lenient | 2.0 | A1_Biomechanical_Core | XGBoost | 71 | 46 | 0.706 | 0.168 | 0.544 | 13.15 | 556.4 | 0.538 | `{'learning_rate': 0.01, 'max_depth': 4, 'n_estimators': 100, 'reg_alpha': 0.1, 'reg_lambda': 0.5}` |
| lenient | 2.0 | A1_Biomechanical_Core | Neural_Network | 71 | 46 | 0.402 | 0.227 | 0.496 | 10.99 | 492.9 | 0.174 | `{'hidden_layer_sizes': (40,), 'alpha': 1.0, 'learning_rate_init': 0.001}` |
| lenient | 2.0 | A1_Biomechanical_Core | Lasso | 71 | 46 | 0.449 | 0.349 | 0.669 | 10.16 | 496.0 | 0.100 | `{'alpha': 10.0}` |
| lenient | 2.0 | A1_Biomechanical_Core | ElasticNet | 71 | 46 | 0.450 | 0.329 | 0.663 | 10.34 | 502.4 | 0.120 | `{'alpha': 0.01, 'l1_ratio': 0.9}` |
| lenient | 2.0 | A1_Biomechanical_Core | Ridge | 71 | 46 | 0.450 | 0.330 | 0.663 | 10.34 | 502.4 | 0.120 | `{'alpha': 0.1}` |
| lenient | 2.0 | A2_Biomechanical_NoK | SVM | 71 | 46 | 0.286 | 0.220 | 0.554 | 11.20 | 512.8 | 0.067 | `{'C': 500, 'epsilon': 100, 'gamma': 0.01}` |
| lenient | 2.0 | A2_Biomechanical_NoK | Random_Forest | 71 | 46 | 0.681 | 0.403 | 0.690 | 10.33 | 471.9 | 0.278 | `{'n_estimators': 200, 'max_depth': 3, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| lenient | 2.0 | A2_Biomechanical_NoK | XGBoost | 71 | 46 | 0.645 | 0.303 | 0.612 | 12.04 | 513.6 | 0.341 | `{'learning_rate': 0.005, 'max_depth': 3, 'n_estimators': 200, 'reg_alpha': 2.0, 'reg_lambda': 1.0}` |
| lenient | 2.0 | A2_Biomechanical_NoK | Neural_Network | 71 | 46 | 0.614 | 0.318 | 0.671 | 10.64 | 403.0 | 0.296 | `{'hidden_layer_sizes': (60,), 'alpha': 1.0, 'learning_rate_init': 0.0005}` |
| lenient | 2.0 | A2_Biomechanical_NoK | Lasso | 71 | 46 | 0.427 | 0.176 | 0.481 | 10.49 | 515.7 | 0.251 | `{'alpha': 1.0}` |
| lenient | 2.0 | A2_Biomechanical_NoK | ElasticNet | 71 | 46 | 0.427 | 0.171 | 0.479 | 10.50 | 517.0 | 0.256 | `{'alpha': 0.01, 'l1_ratio': 0.9}` |
| lenient | 2.0 | A2_Biomechanical_NoK | Ridge | 71 | 46 | 0.476 | 0.211 | 0.486 | 10.73 | 539.5 | 0.265 | `{'alpha': 10.0}` |
| lenient | 2.0 | B_Clinical | SVM | 71 | 46 | 0.490 | 0.142 | 0.506 | 12.26 | 546.2 | 0.348 | `{'C': 5000, 'epsilon': 100, 'gamma': 0.03}` |
| lenient | 2.0 | B_Clinical | Random_Forest | 71 | 46 | 0.512 | 0.234 | 0.547 | 12.03 | 511.7 | 0.278 | `{'n_estimators': 100, 'max_depth': 5, 'min_samples_split': 5, 'min_samples_leaf': 4}` |
| lenient | 2.0 | B_Clinical | XGBoost | 71 | 46 | 0.509 | 0.090 | 0.572 | 13.21 | 581.3 | 0.419 | `{'learning_rate': 0.01, 'max_depth': 2, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 0.1}` |
| lenient | 2.0 | B_Clinical | Neural_Network | 71 | 46 | 0.484 | 0.250 | 0.604 | 12.30 | 528.0 | 0.234 | `{'hidden_layer_sizes': (100,), 'alpha': 0.1, 'learning_rate_init': 0.0005}` |
| lenient | 2.0 | B_Clinical | Lasso | 71 | 46 | 0.220 | 0.111 | 0.436 | 14.41 | 552.7 | 0.109 | `{'alpha': 1.0}` |
| lenient | 2.0 | B_Clinical | ElasticNet | 71 | 46 | 0.220 | 0.110 | 0.435 | 14.41 | 553.2 | 0.111 | `{'alpha': 0.001, 'l1_ratio': 0.5}` |
| lenient | 2.0 | B_Clinical | Ridge | 71 | 46 | 0.248 | 0.089 | 0.613 | 13.81 | 580.7 | 0.160 | `{'alpha': 100.0}` |
| lenient | 2.0 | C1_Combined | SVM | 71 | 46 | 0.362 | 0.351 | 0.635 | 10.40 | 468.2 | 0.011 | `{'C': 1000, 'epsilon': 100, 'gamma': 0.01}` |
| lenient | 2.0 | C1_Combined | Random_Forest | 71 | 46 | 0.704 | 0.409 | 0.695 | 10.19 | 471.7 | 0.295 | `{'n_estimators': 100, 'max_depth': 3, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 2.0 | C1_Combined | XGBoost | 71 | 46 | 0.797 | 0.168 | 0.623 | 12.49 | 543.6 | 0.629 | `{'learning_rate': 0.01, 'max_depth': 4, 'n_estimators': 200, 'reg_alpha': 0.1, 'reg_lambda': 2.0}` |
| lenient | 2.0 | C1_Combined | Neural_Network | 71 | 46 | 0.563 | 0.408 | 0.652 | 11.67 | 468.1 | 0.155 | `{'hidden_layer_sizes': (60,), 'alpha': 1.0, 'learning_rate_init': 0.001}` |
| lenient | 2.0 | C1_Combined | Lasso | 71 | 46 | 0.513 | 0.474 | 0.702 | 9.71 | 447.6 | 0.039 | `{'alpha': 10.0}` |
| lenient | 2.0 | C1_Combined | ElasticNet | 71 | 46 | 0.514 | 0.467 | 0.701 | 9.82 | 449.8 | 0.047 | `{'alpha': 0.001, 'l1_ratio': 0.3}` |
| lenient | 2.0 | C1_Combined | Ridge | 71 | 46 | 0.514 | 0.467 | 0.700 | 9.83 | 450.0 | 0.047 | `{'alpha': 1.0}` |
| lenient | 2.5 | A1_Biomechanical_Core | SVM | 71 | 46 | 0.235 | 0.051 | 0.449 | 16.71 | 568.0 | 0.184 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.001}` |
| lenient | 2.5 | A1_Biomechanical_Core | Random_Forest | 71 | 46 | 0.656 | 0.091 | 0.593 | 13.57 | 441.8 | 0.565 | `{'n_estimators': 100, 'max_depth': None, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| lenient | 2.5 | A1_Biomechanical_Core | XGBoost | 71 | 46 | 0.637 | -0.008 | 0.473 | 13.79 | 516.7 | 0.645 | `{'learning_rate': 0.05, 'max_depth': 2, 'n_estimators': 50, 'reg_alpha': 1.0, 'reg_lambda': 1.0}` |
| lenient | 2.5 | A1_Biomechanical_Core | Neural_Network | 71 | 46 | 0.413 | 0.141 | 0.530 | 14.16 | 489.4 | 0.272 | `{'hidden_layer_sizes': (100,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| lenient | 2.5 | A1_Biomechanical_Core | Lasso | 71 | 46 | 0.430 | 0.192 | 0.669 | 13.02 | 436.2 | 0.238 | `{'alpha': 0.001}` |
| lenient | 2.5 | A1_Biomechanical_Core | ElasticNet | 71 | 46 | 0.387 | 0.258 | 0.669 | 13.40 | 421.0 | 0.130 | `{'alpha': 1.0, 'l1_ratio': 0.5}` |
| lenient | 2.5 | A1_Biomechanical_Core | Ridge | 71 | 46 | 0.270 | 0.194 | 0.667 | 14.60 | 443.7 | 0.076 | `{'alpha': 100.0}` |
| lenient | 2.5 | A2_Biomechanical_NoK | SVM | 71 | 46 | 0.216 | 0.111 | 0.574 | 15.42 | 466.2 | 0.105 | `{'C': 500, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 2.5 | A2_Biomechanical_NoK | Random_Forest | 71 | 46 | 0.638 | 0.213 | 0.649 | 11.90 | 462.3 | 0.425 | `{'n_estimators': 50, 'max_depth': None, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| lenient | 2.5 | A2_Biomechanical_NoK | XGBoost | 71 | 46 | 0.940 | 0.218 | 0.585 | 12.13 | 434.5 | 0.721 | `{'learning_rate': 0.05, 'max_depth': 4, 'n_estimators': 50, 'reg_alpha': 0.1, 'reg_lambda': 0.5}` |
| lenient | 2.5 | A2_Biomechanical_NoK | Neural_Network | 71 | 46 | 0.403 | 0.244 | 0.676 | 14.28 | 427.8 | 0.159 | `{'hidden_layer_sizes': (80,), 'alpha': 1.0, 'learning_rate_init': 0.0005}` |
| lenient | 2.5 | A2_Biomechanical_NoK | Lasso | 71 | 46 | 0.438 | 0.165 | 0.661 | 13.09 | 443.7 | 0.273 | `{'alpha': 0.001}` |
| lenient | 2.5 | A2_Biomechanical_NoK | ElasticNet | 71 | 46 | 0.438 | 0.165 | 0.661 | 13.09 | 443.7 | 0.273 | `{'alpha': 0.001, 'l1_ratio': 0.9}` |
| lenient | 2.5 | A2_Biomechanical_NoK | Ridge | 71 | 46 | 0.438 | 0.166 | 0.661 | 13.09 | 443.5 | 0.272 | `{'alpha': 0.1}` |
| lenient | 2.5 | B_Clinical | SVM | 71 | 46 | 0.134 | 0.004 | 0.287 | 16.35 | 564.5 | 0.130 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 2.5 | B_Clinical | Random_Forest | 71 | 46 | 0.510 | 0.140 | 0.489 | 14.69 | 511.6 | 0.371 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 5, 'min_samples_leaf': 4}` |
| lenient | 2.5 | B_Clinical | XGBoost | 71 | 46 | 0.337 | 0.066 | 0.448 | 15.85 | 557.1 | 0.271 | `{'learning_rate': 0.01, 'max_depth': 4, 'n_estimators': 30, 'reg_alpha': 0.1, 'reg_lambda': 0.1}` |
| lenient | 2.5 | B_Clinical | Neural_Network | 71 | 46 | 0.536 | 0.220 | 0.634 | 13.84 | 481.7 | 0.316 | `{'hidden_layer_sizes': (100,), 'alpha': 0.1, 'learning_rate_init': 0.0005}` |
| lenient | 2.5 | B_Clinical | Lasso | 71 | 46 | 0.371 | -0.063 | 0.562 | 16.84 | 551.9 | 0.433 | `{'alpha': 0.1}` |
| lenient | 2.5 | B_Clinical | ElasticNet | 71 | 46 | 0.347 | 0.069 | 0.562 | 16.28 | 537.4 | 0.278 | `{'alpha': 1.0, 'l1_ratio': 0.7}` |
| lenient | 2.5 | B_Clinical | Ridge | 71 | 46 | 0.361 | 0.037 | 0.562 | 16.40 | 540.1 | 0.323 | `{'alpha': 10.0}` |
| lenient | 2.5 | C1_Combined | SVM | 71 | 46 | 0.258 | 0.077 | 0.525 | 15.33 | 549.2 | 0.182 | `{'C': 100, 'epsilon': 300, 'gamma': 0.1}` |
| lenient | 2.5 | C1_Combined | Random_Forest | 71 | 46 | 0.667 | 0.088 | 0.560 | 13.25 | 450.9 | 0.580 | `{'n_estimators': 100, 'max_depth': 3, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 2.5 | C1_Combined | XGBoost | 71 | 46 | 0.166 | -0.052 | 0.452 | 17.96 | 599.1 | 0.218 | `{'learning_rate': 0.001, 'max_depth': 2, 'n_estimators': 200, 'reg_alpha': 0.5, 'reg_lambda': 0.5}` |
| lenient | 2.5 | C1_Combined | Neural_Network | 71 | 46 | 0.485 | 0.162 | 0.517 | 14.24 | 482.3 | 0.323 | `{'hidden_layer_sizes': (80,), 'alpha': 0.1, 'learning_rate_init': 0.001}` |
| lenient | 2.5 | C1_Combined | Lasso | 71 | 46 | 0.438 | 0.126 | 0.642 | 13.65 | 454.4 | 0.312 | `{'alpha': 1.0}` |
| lenient | 2.5 | C1_Combined | ElasticNet | 71 | 46 | 0.437 | 0.124 | 0.628 | 13.72 | 456.0 | 0.313 | `{'alpha': 0.1, 'l1_ratio': 0.5}` |
| lenient | 2.5 | C1_Combined | Ridge | 71 | 46 | 0.438 | 0.121 | 0.640 | 13.67 | 455.6 | 0.317 | `{'alpha': 0.01}` |
| lenient | 3.0 | A1_Biomechanical_Core | SVM | 71 | 46 | 0.212 | 0.149 | 0.683 | 13.61 | 462.9 | 0.063 | `{'C': 100, 'epsilon': 100, 'gamma': 0.03}` |
| lenient | 3.0 | A1_Biomechanical_Core | Random_Forest | 71 | 46 | 0.525 | 0.288 | 0.603 | 16.05 | 537.6 | 0.237 | `{'n_estimators': 50, 'max_depth': 2, 'min_samples_split': 10, 'min_samples_leaf': 4}` |
| lenient | 3.0 | A1_Biomechanical_Core | XGBoost | 71 | 46 | 0.094 | 0.029 | 0.635 | 18.92 | 629.2 | 0.065 | `{'learning_rate': 0.005, 'max_depth': 1, 'n_estimators': 30, 'reg_alpha': 0.1, 'reg_lambda': 1.0}` |
| lenient | 3.0 | A1_Biomechanical_Core | Neural_Network | 71 | 46 | 0.482 | 0.211 | 0.560 | 16.10 | 563.3 | 0.270 | `{'hidden_layer_sizes': (60,), 'alpha': 0.3, 'learning_rate_init': 0.001}` |
| lenient | 3.0 | A1_Biomechanical_Core | Lasso | 71 | 46 | 0.400 | 0.334 | 0.638 | 12.92 | 516.5 | 0.066 | `{'alpha': 10.0}` |
| lenient | 3.0 | A1_Biomechanical_Core | ElasticNet | 71 | 46 | 0.401 | 0.324 | 0.635 | 13.07 | 520.9 | 0.077 | `{'alpha': 0.001, 'l1_ratio': 0.3}` |
| lenient | 3.0 | A1_Biomechanical_Core | Ridge | 71 | 46 | 0.406 | 0.323 | 0.635 | 13.93 | 531.1 | 0.083 | `{'alpha': 10.0}` |
| lenient | 3.0 | A2_Biomechanical_NoK | SVM | 71 | 46 | 0.459 | 0.202 | 0.448 | 14.89 | 562.3 | 0.257 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.01}` |
| lenient | 3.0 | A2_Biomechanical_NoK | Random_Forest | 71 | 46 | 0.674 | 0.276 | 0.618 | 12.38 | 527.3 | 0.399 | `{'n_estimators': 300, 'max_depth': 4, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 3.0 | A2_Biomechanical_NoK | XGBoost | 71 | 46 | 0.696 | 0.165 | 0.532 | 17.38 | 586.9 | 0.531 | `{'learning_rate': 0.1, 'max_depth': 2, 'n_estimators': 30, 'reg_alpha': 0.1, 'reg_lambda': 2.0}` |
| lenient | 3.0 | A2_Biomechanical_NoK | Neural_Network | 71 | 46 | 0.492 | 0.098 | 0.425 | 16.09 | 557.8 | 0.395 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.3, 'learning_rate_init': 0.001}` |
| lenient | 3.0 | A2_Biomechanical_NoK | Lasso | 71 | 46 | 0.542 | 0.325 | 0.602 | 13.04 | 524.1 | 0.217 | `{'alpha': 10.0}` |
| lenient | 3.0 | A2_Biomechanical_NoK | ElasticNet | 71 | 46 | 0.543 | 0.277 | 0.562 | 13.31 | 543.2 | 0.266 | `{'alpha': 0.01, 'l1_ratio': 0.5}` |
| lenient | 3.0 | A2_Biomechanical_NoK | Ridge | 71 | 46 | 0.543 | 0.281 | 0.563 | 13.27 | 542.0 | 0.263 | `{'alpha': 1.0}` |
| lenient | 3.0 | B_Clinical | SVM | 71 | 46 | 0.308 | 0.179 | 0.554 | 16.26 | 571.2 | 0.130 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.01}` |
| lenient | 3.0 | B_Clinical | Random_Forest | 71 | 46 | 0.568 | 0.261 | 0.572 | 13.93 | 539.1 | 0.308 | `{'n_estimators': 300, 'max_depth': 2, 'min_samples_split': 10, 'min_samples_leaf': 1}` |
| lenient | 3.0 | B_Clinical | XGBoost | 71 | 46 | 0.245 | 0.085 | 0.412 | 18.68 | 608.8 | 0.160 | `{'learning_rate': 0.01, 'max_depth': 2, 'n_estimators': 50, 'reg_alpha': 2.0, 'reg_lambda': 1.0}` |
| lenient | 3.0 | B_Clinical | Neural_Network | 71 | 46 | 0.309 | 0.109 | 0.454 | 17.93 | 582.4 | 0.201 | `{'hidden_layer_sizes': (60,), 'alpha': 0.1, 'learning_rate_init': 0.0005}` |
| lenient | 3.0 | B_Clinical | Lasso | 71 | 46 | 0.366 | 0.119 | 0.597 | 17.37 | 576.1 | 0.247 | `{'alpha': 10.0}` |
| lenient | 3.0 | B_Clinical | ElasticNet | 71 | 46 | 0.365 | 0.135 | 0.592 | 17.45 | 573.6 | 0.230 | `{'alpha': 0.1, 'l1_ratio': 0.3}` |
| lenient | 3.0 | B_Clinical | Ridge | 71 | 46 | 0.367 | 0.109 | 0.593 | 17.58 | 577.8 | 0.258 | `{'alpha': 1.0}` |
| lenient | 3.0 | C1_Combined | SVM | 71 | 46 | 0.263 | 0.149 | 0.552 | 15.32 | 558.0 | 0.114 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 3.0 | C1_Combined | Random_Forest | 71 | 46 | 0.639 | 0.266 | 0.587 | 15.26 | 547.8 | 0.373 | `{'n_estimators': 200, 'max_depth': 3, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 3.0 | C1_Combined | XGBoost | 71 | 46 | 0.485 | 0.122 | 0.504 | 15.49 | 560.7 | 0.363 | `{'learning_rate': 0.01, 'max_depth': 1, 'n_estimators': 200, 'reg_alpha': 2.0, 'reg_lambda': 1.0}` |
| lenient | 3.0 | C1_Combined | Neural_Network | 71 | 46 | 0.445 | 0.215 | 0.537 | 15.94 | 557.9 | 0.230 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.3, 'learning_rate_init': 0.0001}` |
| lenient | 3.0 | C1_Combined | Lasso | 71 | 46 | 0.439 | 0.368 | 0.642 | 13.61 | 506.8 | 0.070 | `{'alpha': 0.01}` |
| lenient | 3.0 | C1_Combined | ElasticNet | 71 | 46 | 0.439 | 0.369 | 0.642 | 13.60 | 506.8 | 0.070 | `{'alpha': 0.01, 'l1_ratio': 0.7}` |
| lenient | 3.0 | C1_Combined | Ridge | 71 | 46 | 0.292 | 0.224 | 0.625 | 16.41 | 561.7 | 0.068 | `{'alpha': 100.0}` |
| lenient | 3.5 | A1_Biomechanical_Core | SVM | 71 | 46 | 0.452 | 0.140 | 0.568 | 16.79 | 554.6 | 0.312 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.05}` |
| lenient | 3.5 | A1_Biomechanical_Core | Random_Forest | 71 | 46 | 0.630 | 0.215 | 0.559 | 15.77 | 544.9 | 0.414 | `{'n_estimators': 50, 'max_depth': 4, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 3.5 | A1_Biomechanical_Core | XGBoost | 71 | 46 | 0.749 | 0.188 | 0.452 | 16.35 | 492.5 | 0.561 | `{'learning_rate': 0.01, 'max_depth': 4, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 0.1}` |
| lenient | 3.5 | A1_Biomechanical_Core | Neural_Network | 71 | 46 | 0.341 | 0.167 | 0.459 | 17.53 | 568.3 | 0.174 | `{'hidden_layer_sizes': (60,), 'alpha': 0.3, 'learning_rate_init': 0.0005}` |
| lenient | 3.5 | A1_Biomechanical_Core | Lasso | 71 | 46 | 0.359 | 0.258 | 0.539 | 15.83 | 545.1 | 0.101 | `{'alpha': 10.0}` |
| lenient | 3.5 | A1_Biomechanical_Core | ElasticNet | 71 | 46 | 0.360 | 0.252 | 0.535 | 15.83 | 547.8 | 0.108 | `{'alpha': 0.1, 'l1_ratio': 0.7}` |
| lenient | 3.5 | A1_Biomechanical_Core | Ridge | 71 | 46 | 0.360 | 0.250 | 0.535 | 15.82 | 548.5 | 0.110 | `{'alpha': 0.01}` |
| lenient | 3.5 | A2_Biomechanical_NoK | SVM | 71 | 46 | 0.410 | 0.214 | 0.555 | 15.21 | 513.7 | 0.196 | `{'C': 2000, 'epsilon': 300, 'gamma': 0.03}` |
| lenient | 3.5 | A2_Biomechanical_NoK | Random_Forest | 71 | 46 | 0.618 | 0.275 | 0.620 | 15.52 | 535.0 | 0.342 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 5, 'min_samples_leaf': 4}` |
| lenient | 3.5 | A2_Biomechanical_NoK | XGBoost | 71 | 46 | 0.690 | 0.142 | 0.544 | 17.84 | 586.0 | 0.548 | `{'learning_rate': 0.01, 'max_depth': 4, 'n_estimators': 100, 'reg_alpha': 1.0, 'reg_lambda': 1.0}` |
| lenient | 3.5 | A2_Biomechanical_NoK | Neural_Network | 71 | 46 | 0.333 | 0.179 | 0.573 | 14.46 | 456.4 | 0.153 | `{'hidden_layer_sizes': (40,), 'alpha': 0.1, 'learning_rate_init': 0.0001}` |
| lenient | 3.5 | A2_Biomechanical_NoK | Lasso | 71 | 46 | 0.447 | 0.190 | 0.477 | 16.06 | 571.2 | 0.257 | `{'alpha': 0.1}` |
| lenient | 3.5 | A2_Biomechanical_NoK | ElasticNet | 71 | 46 | 0.447 | 0.190 | 0.477 | 16.06 | 571.3 | 0.257 | `{'alpha': 0.01, 'l1_ratio': 0.9}` |
| lenient | 3.5 | A2_Biomechanical_NoK | Ridge | 71 | 46 | 0.447 | 0.190 | 0.477 | 16.06 | 571.2 | 0.257 | `{'alpha': 0.1}` |
| lenient | 3.5 | B_Clinical | SVM | 71 | 46 | 0.332 | 0.157 | 0.582 | 17.55 | 529.0 | 0.175 | `{'C': 2000, 'epsilon': 500, 'gamma': 0.05}` |
| lenient | 3.5 | B_Clinical | Random_Forest | 71 | 46 | 0.550 | 0.083 | 0.432 | 18.55 | 607.6 | 0.467 | `{'n_estimators': 300, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 3.5 | B_Clinical | XGBoost | 71 | 46 | 0.136 | -0.046 | 0.376 | 21.41 | 615.5 | 0.182 | `{'learning_rate': 0.005, 'max_depth': 1, 'n_estimators': 50, 'reg_alpha': 2.0, 'reg_lambda': 0.5}` |
| lenient | 3.5 | B_Clinical | Neural_Network | 71 | 46 | 0.367 | 0.005 | 0.460 | 20.75 | 591.3 | 0.362 | `{'hidden_layer_sizes': (40,), 'alpha': 0.3, 'learning_rate_init': 0.0001}` |
| lenient | 3.5 | B_Clinical | Lasso | 71 | 46 | 0.353 | -0.022 | 0.554 | 19.19 | 578.8 | 0.376 | `{'alpha': 0.01}` |
| lenient | 3.5 | B_Clinical | ElasticNet | 71 | 46 | 0.129 | 0.006 | 0.301 | 22.53 | 638.3 | 0.122 | `{'alpha': 1.0, 'l1_ratio': 0.1}` |
| lenient | 3.5 | B_Clinical | Ridge | 71 | 46 | 0.344 | 0.068 | 0.550 | 18.67 | 566.7 | 0.276 | `{'alpha': 10.0}` |
| lenient | 3.5 | C1_Combined | SVM | 71 | 46 | 0.359 | 0.229 | 0.533 | 15.95 | 556.3 | 0.130 | `{'C': 500, 'epsilon': 300, 'gamma': 0.1}` |
| lenient | 3.5 | C1_Combined | Random_Forest | 71 | 46 | 0.566 | 0.238 | 0.540 | 15.33 | 546.5 | 0.329 | `{'n_estimators': 50, 'max_depth': 4, 'min_samples_split': 5, 'min_samples_leaf': 4}` |
| lenient | 3.5 | C1_Combined | XGBoost | 71 | 46 | 0.211 | 0.102 | 0.457 | 20.18 | 604.3 | 0.109 | `{'learning_rate': 0.005, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 2.0, 'reg_lambda': 2.0}` |
| lenient | 3.5 | C1_Combined | Neural_Network | 71 | 46 | 0.427 | 0.223 | 0.517 | 16.02 | 558.9 | 0.204 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.1, 'learning_rate_init': 0.0005}` |
| lenient | 3.5 | C1_Combined | Lasso | 71 | 46 | 0.437 | 0.260 | 0.623 | 15.89 | 512.0 | 0.177 | `{'alpha': 0.1}` |
| lenient | 3.5 | C1_Combined | ElasticNet | 71 | 46 | 0.437 | 0.260 | 0.623 | 15.89 | 512.0 | 0.177 | `{'alpha': 0.001, 'l1_ratio': 0.5}` |
| lenient | 3.5 | C1_Combined | Ridge | 71 | 46 | 0.437 | 0.260 | 0.623 | 15.89 | 512.0 | 0.177 | `{'alpha': 0.01}` |
| lenient | 4.0 | A1_Biomechanical_Core | SVM | 71 | 46 | 0.318 | 0.139 | 0.555 | 18.54 | 621.6 | 0.179 | `{'C': 1000, 'epsilon': 300, 'gamma': 0.05}` |
| lenient | 4.0 | A1_Biomechanical_Core | Random_Forest | 71 | 46 | 0.552 | 0.172 | 0.535 | 18.59 | 621.0 | 0.380 | `{'n_estimators': 200, 'max_depth': 5, 'min_samples_split': 10, 'min_samples_leaf': 4}` |
| lenient | 4.0 | A1_Biomechanical_Core | XGBoost | 71 | 46 | 0.562 | 0.132 | 0.416 | 18.31 | 527.0 | 0.430 | `{'learning_rate': 0.005, 'max_depth': 4, 'n_estimators': 200, 'reg_alpha': 1.0, 'reg_lambda': 2.0}` |
| lenient | 4.0 | A1_Biomechanical_Core | Neural_Network | 71 | 46 | 0.328 | 0.181 | 0.523 | 18.75 | 626.4 | 0.147 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.1, 'learning_rate_init': 0.0005}` |
| lenient | 4.0 | A1_Biomechanical_Core | Lasso | 71 | 46 | 0.358 | 0.168 | 0.495 | 19.00 | 624.4 | 0.190 | `{'alpha': 0.01}` |
| lenient | 4.0 | A1_Biomechanical_Core | ElasticNet | 71 | 46 | 0.358 | 0.168 | 0.495 | 19.00 | 624.4 | 0.190 | `{'alpha': 0.001, 'l1_ratio': 0.1}` |
| lenient | 4.0 | A1_Biomechanical_Core | Ridge | 71 | 46 | 0.358 | 0.168 | 0.495 | 19.00 | 624.4 | 0.190 | `{'alpha': 0.1}` |
| lenient | 4.0 | A2_Biomechanical_NoK | SVM | 71 | 46 | 0.176 | 0.002 | 0.356 | 19.69 | 664.5 | 0.174 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.001}` |
| lenient | 4.0 | A2_Biomechanical_NoK | Random_Forest | 71 | 46 | 0.788 | 0.200 | 0.621 | 19.27 | 614.7 | 0.588 | `{'n_estimators': 200, 'max_depth': 5, 'min_samples_split': 5, 'min_samples_leaf': 2}` |
| lenient | 4.0 | A2_Biomechanical_NoK | XGBoost | 71 | 46 | 0.964 | 0.008 | 0.434 | 18.84 | 559.9 | 0.955 | `{'learning_rate': 0.05, 'max_depth': 3, 'n_estimators': 100, 'reg_alpha': 2.0, 'reg_lambda': 0.1}` |
| lenient | 4.0 | A2_Biomechanical_NoK | Neural_Network | 71 | 46 | 0.418 | 0.095 | 0.568 | 17.94 | 519.9 | 0.323 | `{'hidden_layer_sizes': (80,), 'alpha': 0.5, 'learning_rate_init': 0.0005}` |
| lenient | 4.0 | A2_Biomechanical_NoK | Lasso | 71 | 46 | 0.374 | 0.132 | 0.595 | 16.89 | 502.9 | 0.241 | `{'alpha': 1.0}` |
| lenient | 4.0 | A2_Biomechanical_NoK | ElasticNet | 71 | 46 | 0.357 | 0.195 | 0.588 | 17.16 | 495.2 | 0.162 | `{'alpha': 1.0, 'l1_ratio': 0.7}` |
| lenient | 4.0 | A2_Biomechanical_NoK | Ridge | 71 | 46 | 0.241 | 0.156 | 0.569 | 18.59 | 516.7 | 0.086 | `{'alpha': 100.0}` |
| lenient | 4.0 | B_Clinical | SVM | 71 | 46 | 0.390 | 0.071 | 0.396 | 22.04 | 670.5 | 0.319 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.05}` |
| lenient | 4.0 | B_Clinical | Random_Forest | 71 | 46 | 0.476 | 0.101 | 0.466 | 22.30 | 666.8 | 0.375 | `{'n_estimators': 300, 'max_depth': 4, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| lenient | 4.0 | B_Clinical | XGBoost | 71 | 46 | 0.285 | 0.089 | 0.449 | 21.47 | 631.3 | 0.195 | `{'learning_rate': 0.005, 'max_depth': 1, 'n_estimators': 200, 'reg_alpha': 0.1, 'reg_lambda': 2.0}` |
| lenient | 4.0 | B_Clinical | Neural_Network | 71 | 46 | 0.487 | -0.031 | 0.542 | 20.22 | 610.0 | 0.518 | `{'hidden_layer_sizes': (80,), 'alpha': 1.0, 'learning_rate_init': 0.0005}` |
| lenient | 4.0 | B_Clinical | Lasso | 71 | 46 | 0.182 | -0.054 | 0.301 | 27.15 | 737.2 | 0.235 | `{'alpha': 10.0}` |
| lenient | 4.0 | B_Clinical | ElasticNet | 71 | 46 | 0.149 | 0.008 | 0.293 | 26.17 | 712.1 | 0.141 | `{'alpha': 1.0, 'l1_ratio': 0.3}` |
| lenient | 4.0 | B_Clinical | Ridge | 71 | 46 | 0.104 | 0.001 | 0.287 | 25.93 | 713.4 | 0.103 | `{'alpha': 100.0}` |
| lenient | 4.0 | C1_Combined | SVM | 71 | 46 | 0.034 | -0.122 | 0.483 | 23.25 | 689.9 | 0.156 | `{'C': 100, 'epsilon': 500, 'gamma': 0.005}` |
| lenient | 4.0 | C1_Combined | Random_Forest | 71 | 46 | 0.889 | 0.099 | 0.543 | 19.98 | 592.6 | 0.789 | `{'n_estimators': 300, 'max_depth': None, 'min_samples_split': 2, 'min_samples_leaf': 1}` |
| lenient | 4.0 | C1_Combined | XGBoost | 71 | 46 | 0.358 | 0.066 | 0.342 | 18.50 | 537.1 | 0.292 | `{'learning_rate': 0.005, 'max_depth': 3, 'n_estimators': 100, 'reg_alpha': 1.0, 'reg_lambda': 2.0}` |
| lenient | 4.0 | C1_Combined | Neural_Network | 71 | 46 | 0.378 | 0.232 | 0.525 | 19.48 | 611.7 | 0.146 | `{'hidden_layer_sizes': (40,), 'alpha': 0.5, 'learning_rate_init': 0.0005}` |
| lenient | 4.0 | C1_Combined | Lasso | 71 | 46 | 0.384 | 0.182 | 0.587 | 16.71 | 491.4 | 0.201 | `{'alpha': 0.1}` |
| lenient | 4.0 | C1_Combined | ElasticNet | 71 | 46 | 0.314 | 0.188 | 0.526 | 20.74 | 629.0 | 0.126 | `{'alpha': 1.0, 'l1_ratio': 0.1}` |
| lenient | 4.0 | C1_Combined | Ridge | 71 | 46 | 0.260 | 0.144 | 0.538 | 18.06 | 512.9 | 0.116 | `{'alpha': 100.0}` |
| lenient | 4.5 | A1_Biomechanical_Core | SVM | 71 | 46 | 0.466 | 0.158 | 0.527 | 18.42 | 646.5 | 0.307 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.1}` |
| lenient | 4.5 | A1_Biomechanical_Core | Random_Forest | 71 | 46 | 0.603 | 0.202 | 0.599 | 19.45 | 620.8 | 0.401 | `{'n_estimators': 50, 'max_depth': 3, 'min_samples_split': 5, 'min_samples_leaf': 4}` |
| lenient | 4.5 | A1_Biomechanical_Core | XGBoost | 71 | 46 | 0.515 | 0.053 | 0.420 | 21.20 | 588.2 | 0.462 | `{'learning_rate': 0.01, 'max_depth': 4, 'n_estimators': 50, 'reg_alpha': 2.0, 'reg_lambda': 0.1}` |
| lenient | 4.5 | A1_Biomechanical_Core | Neural_Network | 71 | 46 | 0.405 | 0.179 | 0.493 | 20.50 | 577.6 | 0.226 | `{'hidden_layer_sizes': (80,), 'alpha': 0.5, 'learning_rate_init': 0.0001}` |
| lenient | 4.5 | A1_Biomechanical_Core | Lasso | 71 | 46 | 0.358 | 0.095 | 0.477 | 20.60 | 657.4 | 0.263 | `{'alpha': 0.001}` |
| lenient | 4.5 | A1_Biomechanical_Core | ElasticNet | 71 | 46 | 0.341 | 0.128 | 0.586 | 19.55 | 524.6 | 0.214 | `{'alpha': 1.0, 'l1_ratio': 0.7}` |
| lenient | 4.5 | A1_Biomechanical_Core | Ridge | 71 | 46 | 0.226 | 0.096 | 0.584 | 20.31 | 541.5 | 0.130 | `{'alpha': 100.0}` |
| lenient | 4.5 | A2_Biomechanical_NoK | SVM | 71 | 46 | 0.276 | 0.097 | 0.538 | 22.84 | 678.8 | 0.179 | `{'C': 500, 'epsilon': 300, 'gamma': 0.03}` |
| lenient | 4.5 | A2_Biomechanical_NoK | Random_Forest | 71 | 46 | 0.611 | 0.233 | 0.665 | 19.46 | 607.3 | 0.378 | `{'n_estimators': 300, 'max_depth': 2, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 4.5 | A2_Biomechanical_NoK | XGBoost | 71 | 46 | 0.540 | 0.092 | 0.535 | 22.33 | 665.9 | 0.448 | `{'learning_rate': 0.005, 'max_depth': 2, 'n_estimators': 200, 'reg_alpha': 2.0, 'reg_lambda': 0.1}` |
| lenient | 4.5 | A2_Biomechanical_NoK | Neural_Network | 71 | 46 | 0.105 | -0.070 | 0.308 | 24.81 | 605.9 | 0.175 | `{'hidden_layer_sizes': (80,), 'alpha': 0.5, 'learning_rate_init': 0.0001}` |
| lenient | 4.5 | A2_Biomechanical_NoK | Lasso | 71 | 46 | 0.332 | 0.067 | 0.437 | 21.54 | 609.3 | 0.264 | `{'alpha': 10.0}` |
| lenient | 4.5 | A2_Biomechanical_NoK | ElasticNet | 71 | 46 | 0.331 | 0.056 | 0.424 | 21.78 | 613.0 | 0.275 | `{'alpha': 0.1, 'l1_ratio': 0.3}` |
| lenient | 4.5 | A2_Biomechanical_NoK | Ridge | 71 | 46 | 0.228 | 0.080 | 0.561 | 20.59 | 546.7 | 0.148 | `{'alpha': 100.0}` |
| lenient | 4.5 | B_Clinical | SVM | 71 | 46 | 0.419 | 0.094 | 0.559 | 23.36 | 666.0 | 0.325 | `{'C': 5000, 'epsilon': 100, 'gamma': 0.03}` |
| lenient | 4.5 | B_Clinical | Random_Forest | 71 | 46 | 0.454 | 0.090 | 0.500 | 24.16 | 670.4 | 0.364 | `{'n_estimators': 100, 'max_depth': 2, 'min_samples_split': 5, 'min_samples_leaf': 4}` |
| lenient | 4.5 | B_Clinical | XGBoost | 71 | 46 | 0.508 | 0.119 | 0.589 | 21.23 | 600.3 | 0.389 | `{'learning_rate': 0.01, 'max_depth': 3, 'n_estimators': 100, 'reg_alpha': 1.0, 'reg_lambda': 1.0}` |
| lenient | 4.5 | B_Clinical | Neural_Network | 71 | 46 | 0.469 | -0.038 | 0.594 | 23.37 | 645.7 | 0.507 | `{'hidden_layer_sizes': (60,), 'alpha': 0.5, 'learning_rate_init': 0.001}` |
| lenient | 4.5 | B_Clinical | Lasso | 71 | 46 | 0.181 | -0.113 | 0.302 | 29.87 | 774.2 | 0.293 | `{'alpha': 0.01}` |
| lenient | 4.5 | B_Clinical | ElasticNet | 71 | 46 | 0.179 | -0.088 | 0.300 | 29.61 | 763.9 | 0.267 | `{'alpha': 1.0, 'l1_ratio': 0.9}` |
| lenient | 4.5 | B_Clinical | Ridge | 71 | 46 | 0.181 | -0.107 | 0.302 | 29.81 | 772.0 | 0.288 | `{'alpha': 1.0}` |
| lenient | 4.5 | C1_Combined | SVM | 71 | 46 | 0.451 | 0.082 | 0.596 | 20.25 | 614.1 | 0.369 | `{'C': 500, 'epsilon': 100, 'gamma': 0.1}` |
| lenient | 4.5 | C1_Combined | Random_Forest | 71 | 46 | 0.620 | 0.168 | 0.582 | 20.08 | 625.0 | 0.451 | `{'n_estimators': 200, 'max_depth': 3, 'min_samples_split': 5, 'min_samples_leaf': 4}` |
| lenient | 4.5 | C1_Combined | XGBoost | 71 | 46 | 0.609 | -0.075 | 0.328 | 21.82 | 621.4 | 0.685 | `{'learning_rate': 0.01, 'max_depth': 2, 'n_estimators': 200, 'reg_alpha': 0.1, 'reg_lambda': 0.1}` |
| lenient | 4.5 | C1_Combined | Neural_Network | 71 | 46 | 0.400 | 0.192 | 0.505 | 22.17 | 640.8 | 0.207 | `{'hidden_layer_sizes': (40,), 'alpha': 0.5, 'learning_rate_init': 0.0005}` |
| lenient | 4.5 | C1_Combined | Lasso | 71 | 46 | 0.392 | 0.073 | 0.527 | 20.99 | 647.9 | 0.319 | `{'alpha': 0.01}` |
| lenient | 4.5 | C1_Combined | ElasticNet | 71 | 46 | 0.338 | 0.100 | 0.518 | 19.85 | 530.0 | 0.237 | `{'alpha': 1.0, 'l1_ratio': 0.5}` |
| lenient | 4.5 | C1_Combined | Ridge | 71 | 46 | 0.256 | 0.090 | 0.520 | 25.09 | 681.8 | 0.166 | `{'alpha': 100.0}` |
| lenient | 5.0 | A1_Biomechanical_Core | SVM | 71 | 46 | 0.477 | 0.261 | 0.617 | 20.90 | 623.3 | 0.216 | `{'C': 2000, 'epsilon': 500, 'gamma': 0.05}` |
| lenient | 5.0 | A1_Biomechanical_Core | Random_Forest | 71 | 46 | 0.681 | 0.280 | 0.627 | 20.75 | 633.2 | 0.401 | `{'n_estimators': 200, 'max_depth': 3, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 5.0 | A1_Biomechanical_Core | XGBoost | 71 | 46 | 0.660 | 0.267 | 0.592 | 19.44 | 609.8 | 0.393 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 1.0, 'reg_lambda': 1.0}` |
| lenient | 5.0 | A1_Biomechanical_Core | Neural_Network | 71 | 46 | 0.438 | 0.212 | 0.533 | 19.19 | 587.0 | 0.227 | `{'hidden_layer_sizes': (40,), 'alpha': 0.3, 'learning_rate_init': 0.0005}` |
| lenient | 5.0 | A1_Biomechanical_Core | Lasso | 71 | 46 | 0.415 | 0.206 | 0.563 | 22.44 | 649.7 | 0.209 | `{'alpha': 1.0}` |
| lenient | 5.0 | A1_Biomechanical_Core | ElasticNet | 71 | 46 | 0.415 | 0.205 | 0.563 | 22.46 | 650.1 | 0.210 | `{'alpha': 0.001, 'l1_ratio': 0.3}` |
| lenient | 5.0 | A1_Biomechanical_Core | Ridge | 71 | 46 | 0.406 | 0.203 | 0.559 | 22.56 | 653.9 | 0.203 | `{'alpha': 10.0}` |
| lenient | 5.0 | A2_Biomechanical_NoK | SVM | 71 | 46 | 0.148 | 0.071 | 0.410 | 18.16 | 583.5 | 0.078 | `{'C': 100, 'epsilon': 300, 'gamma': 0.1}` |
| lenient | 5.0 | A2_Biomechanical_NoK | Random_Forest | 71 | 46 | 0.741 | 0.410 | 0.716 | 18.30 | 578.4 | 0.331 | `{'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 5.0 | A2_Biomechanical_NoK | XGBoost | 71 | 46 | 0.411 | 0.243 | 0.571 | 23.89 | 654.7 | 0.169 | `{'learning_rate': 0.01, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 2.0, 'reg_lambda': 0.5}` |
| lenient | 5.0 | A2_Biomechanical_NoK | Neural_Network | 71 | 46 | 0.133 | 0.021 | 0.474 | 24.07 | 582.8 | 0.112 | `{'hidden_layer_sizes': (80,), 'alpha': 0.1, 'learning_rate_init': 0.001}` |
| lenient | 5.0 | A2_Biomechanical_NoK | Lasso | 71 | 46 | 0.356 | 0.083 | 0.434 | 20.59 | 619.3 | 0.273 | `{'alpha': 10.0}` |
| lenient | 5.0 | A2_Biomechanical_NoK | ElasticNet | 71 | 46 | 0.357 | 0.062 | 0.416 | 20.55 | 626.9 | 0.295 | `{'alpha': 0.001, 'l1_ratio': 0.1}` |
| lenient | 5.0 | A2_Biomechanical_NoK | Ridge | 71 | 46 | 0.350 | 0.081 | 0.405 | 20.88 | 627.1 | 0.268 | `{'alpha': 10.0}` |
| lenient | 5.0 | B_Clinical | SVM | 71 | 46 | 0.257 | 0.083 | 0.565 | 20.85 | 700.6 | 0.174 | `{'C': 500, 'epsilon': 100, 'gamma': 0.03}` |
| lenient | 5.0 | B_Clinical | Random_Forest | 71 | 46 | 0.613 | 0.330 | 0.619 | 20.11 | 615.6 | 0.284 | `{'n_estimators': 200, 'max_depth': 4, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| lenient | 5.0 | B_Clinical | XGBoost | 71 | 46 | 0.698 | 0.295 | 0.573 | 20.60 | 637.5 | 0.403 | `{'learning_rate': 0.05, 'max_depth': 2, 'n_estimators': 50, 'reg_alpha': 0.1, 'reg_lambda': 1.0}` |
| lenient | 5.0 | B_Clinical | Neural_Network | 71 | 46 | 0.525 | 0.259 | 0.672 | 19.04 | 559.5 | 0.266 | `{'hidden_layer_sizes': (40,), 'alpha': 0.5, 'learning_rate_init': 0.0005}` |
| lenient | 5.0 | B_Clinical | Lasso | 71 | 46 | 0.338 | -0.050 | 0.530 | 27.59 | 736.1 | 0.388 | `{'alpha': 0.01}` |
| lenient | 5.0 | B_Clinical | ElasticNet | 71 | 46 | 0.390 | 0.072 | 0.570 | 26.23 | 680.1 | 0.318 | `{'alpha': 1.0, 'l1_ratio': 0.7}` |
| lenient | 5.0 | B_Clinical | Ridge | 71 | 46 | 0.338 | -0.050 | 0.530 | 27.59 | 736.1 | 0.388 | `{'alpha': 0.01}` |
| lenient | 5.0 | C1_Combined | SVM | 71 | 46 | 0.534 | 0.320 | 0.623 | 19.95 | 622.1 | 0.214 | `{'C': 500, 'epsilon': 300, 'gamma': 0.1}` |
| lenient | 5.0 | C1_Combined | Random_Forest | 71 | 46 | 0.642 | 0.283 | 0.591 | 21.04 | 626.8 | 0.359 | `{'n_estimators': 50, 'max_depth': 4, 'min_samples_split': 10, 'min_samples_leaf': 4}` |
| lenient | 5.0 | C1_Combined | XGBoost | 71 | 46 | 0.592 | 0.249 | 0.537 | 22.89 | 650.8 | 0.344 | `{'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 50, 'reg_alpha': 1.0, 'reg_lambda': 0.5}` |
| lenient | 5.0 | C1_Combined | Neural_Network | 71 | 46 | 0.647 | 0.285 | 0.653 | 19.67 | 624.8 | 0.363 | `{'hidden_layer_sizes': (80,), 'alpha': 0.3, 'learning_rate_init': 0.0005}` |
| lenient | 5.0 | C1_Combined | Lasso | 71 | 46 | 0.482 | 0.289 | 0.621 | 21.29 | 600.0 | 0.194 | `{'alpha': 0.1}` |
| lenient | 5.0 | C1_Combined | ElasticNet | 71 | 46 | 0.482 | 0.289 | 0.621 | 21.29 | 600.0 | 0.194 | `{'alpha': 0.001, 'l1_ratio': 0.5}` |
| lenient | 5.0 | C1_Combined | Ridge | 71 | 46 | 0.482 | 0.289 | 0.621 | 21.28 | 599.9 | 0.193 | `{'alpha': 0.1}` |
| lenient | 5.5 | A1_Biomechanical_Core | SVM | 71 | 46 | 0.373 | 0.145 | 0.640 | 22.67 | 701.1 | 0.228 | `{'C': 500, 'epsilon': 300, 'gamma': 0.03}` |
| lenient | 5.5 | A1_Biomechanical_Core | Random_Forest | 71 | 46 | 0.689 | 0.167 | 0.561 | 27.30 | 745.8 | 0.522 | `{'n_estimators': 300, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 2}` |
| lenient | 5.5 | A1_Biomechanical_Core | XGBoost | 71 | 46 | 0.652 | 0.278 | 0.630 | 20.02 | 609.1 | 0.374 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 50, 'reg_alpha': 2.0, 'reg_lambda': 0.1}` |
| lenient | 5.5 | A1_Biomechanical_Core | Neural_Network | 71 | 46 | 0.683 | 0.086 | 0.557 | 28.26 | 782.0 | 0.597 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.3, 'learning_rate_init': 0.0005}` |
| lenient | 5.5 | A1_Biomechanical_Core | Lasso | 71 | 46 | 0.474 | 0.214 | 0.627 | 24.20 | 645.5 | 0.260 | `{'alpha': 0.1}` |
| lenient | 5.5 | A1_Biomechanical_Core | ElasticNet | 71 | 46 | 0.474 | 0.214 | 0.627 | 24.20 | 645.5 | 0.260 | `{'alpha': 0.001, 'l1_ratio': 0.1}` |
| lenient | 5.5 | A1_Biomechanical_Core | Ridge | 71 | 46 | 0.464 | 0.203 | 0.623 | 24.40 | 651.9 | 0.260 | `{'alpha': 10.0}` |
| lenient | 5.5 | A2_Biomechanical_NoK | SVM | 71 | 46 | 0.243 | 0.168 | 0.614 | 19.51 | 663.6 | 0.075 | `{'C': 1000, 'epsilon': 100, 'gamma': 0.01}` |
| lenient | 5.5 | A2_Biomechanical_NoK | Random_Forest | 71 | 46 | 0.807 | 0.282 | 0.712 | 21.06 | 639.2 | 0.524 | `{'n_estimators': 50, 'max_depth': 3, 'min_samples_split': 2, 'min_samples_leaf': 2}` |
| lenient | 5.5 | A2_Biomechanical_NoK | XGBoost | 71 | 46 | 0.496 | 0.058 | 0.393 | 29.00 | 809.0 | 0.438 | `{'learning_rate': 0.005, 'max_depth': 4, 'n_estimators': 100, 'reg_alpha': 2.0, 'reg_lambda': 1.0}` |
| lenient | 5.5 | A2_Biomechanical_NoK | Neural_Network | 71 | 46 | 0.264 | 0.060 | 0.428 | 28.71 | 708.4 | 0.204 | `{'hidden_layer_sizes': (80,), 'alpha': 0.3, 'learning_rate_init': 0.0005}` |
| lenient | 5.5 | A2_Biomechanical_NoK | Lasso | 71 | 46 | 0.270 | 0.117 | 0.402 | 23.63 | 642.8 | 0.153 | `{'alpha': 0.001}` |
| lenient | 5.5 | A2_Biomechanical_NoK | ElasticNet | 71 | 46 | 0.269 | 0.128 | 0.407 | 23.58 | 639.1 | 0.141 | `{'alpha': 0.1, 'l1_ratio': 0.5}` |
| lenient | 5.5 | A2_Biomechanical_NoK | Ridge | 71 | 46 | 0.265 | 0.142 | 0.412 | 23.54 | 634.0 | 0.122 | `{'alpha': 10.0}` |
| lenient | 5.5 | B_Clinical | SVM | 71 | 46 | 0.499 | 0.217 | 0.747 | 25.03 | 633.7 | 0.283 | `{'C': 1000, 'epsilon': 500, 'gamma': 0.1}` |
| lenient | 5.5 | B_Clinical | Random_Forest | 71 | 46 | 0.792 | 0.280 | 0.612 | 24.55 | 709.0 | 0.512 | `{'n_estimators': 100, 'max_depth': 4, 'min_samples_split': 5, 'min_samples_leaf': 2}` |
| lenient | 5.5 | B_Clinical | XGBoost | 71 | 46 | 0.411 | 0.230 | 0.631 | 27.77 | 701.2 | 0.180 | `{'learning_rate': 0.01, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 2.0, 'reg_lambda': 1.0}` |
| lenient | 5.5 | B_Clinical | Neural_Network | 71 | 46 | 0.581 | 0.314 | 0.657 | 25.52 | 694.7 | 0.268 | `{'hidden_layer_sizes': (80,), 'alpha': 0.1, 'learning_rate_init': 0.0001}` |
| lenient | 5.5 | B_Clinical | Lasso | 71 | 46 | 0.319 | -0.036 | 0.516 | 32.18 | 825.4 | 0.355 | `{'alpha': 0.1}` |
| lenient | 5.5 | B_Clinical | ElasticNet | 71 | 46 | 0.332 | 0.117 | 0.571 | 30.27 | 751.0 | 0.215 | `{'alpha': 1.0, 'l1_ratio': 0.1}` |
| lenient | 5.5 | B_Clinical | Ridge | 71 | 46 | 0.256 | 0.098 | 0.569 | 30.93 | 772.4 | 0.158 | `{'alpha': 100.0}` |
| lenient | 5.5 | C1_Combined | SVM | 71 | 46 | 0.478 | 0.225 | 0.655 | 23.77 | 659.1 | 0.254 | `{'C': 5000, 'epsilon': 300, 'gamma': 0.005}` |
| lenient | 5.5 | C1_Combined | Random_Forest | 71 | 46 | 0.844 | 0.159 | 0.562 | 25.47 | 682.7 | 0.684 | `{'n_estimators': 300, 'max_depth': 4, 'min_samples_split': 2, 'min_samples_leaf': 2}` |
| lenient | 5.5 | C1_Combined | XGBoost | 71 | 46 | 0.575 | 0.204 | 0.505 | 22.55 | 604.4 | 0.371 | `{'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 50, 'reg_alpha': 1.0, 'reg_lambda': 0.1}` |
| lenient | 5.5 | C1_Combined | Neural_Network | 71 | 46 | 0.551 | 0.348 | 0.677 | 24.96 | 681.7 | 0.203 | `{'hidden_layer_sizes': (80,), 'alpha': 1.0, 'learning_rate_init': 0.0001}` |
| lenient | 5.5 | C1_Combined | Lasso | 71 | 46 | 0.518 | 0.295 | 0.665 | 22.94 | 600.2 | 0.223 | `{'alpha': 10.0}` |
| lenient | 5.5 | C1_Combined | ElasticNet | 71 | 46 | 0.488 | 0.296 | 0.665 | 25.38 | 699.4 | 0.192 | `{'alpha': 0.1, 'l1_ratio': 0.7}` |
| lenient | 5.5 | C1_Combined | Ridge | 71 | 46 | 0.519 | 0.283 | 0.662 | 23.07 | 602.7 | 0.236 | `{'alpha': 0.1}` |
| lenient | 6.0 | A1_Biomechanical_Core | SVM | 71 | 46 | 0.467 | 0.209 | 0.648 | 24.42 | 737.2 | 0.258 | `{'C': 500, 'epsilon': 300, 'gamma': 0.1}` |
| lenient | 6.0 | A1_Biomechanical_Core | Random_Forest | 71 | 46 | 0.667 | 0.324 | 0.644 | 23.49 | 683.0 | 0.343 | `{'n_estimators': 50, 'max_depth': 2, 'min_samples_split': 5, 'min_samples_leaf': 1}` |
| lenient | 6.0 | A1_Biomechanical_Core | XGBoost | 71 | 46 | 0.890 | 0.214 | 0.592 | 23.92 | 698.9 | 0.676 | `{'learning_rate': 0.1, 'max_depth': 2, 'n_estimators': 100, 'reg_alpha': 1.0, 'reg_lambda': 2.0}` |
| lenient | 6.0 | A1_Biomechanical_Core | Neural_Network | 71 | 46 | 0.495 | 0.247 | 0.642 | 26.71 | 711.9 | 0.248 | `{'hidden_layer_sizes': (80, 40), 'alpha': 0.5, 'learning_rate_init': 0.0001}` |
| lenient | 6.0 | A1_Biomechanical_Core | Lasso | 71 | 46 | 0.462 | 0.271 | 0.594 | 26.73 | 699.4 | 0.191 | `{'alpha': 0.001}` |
| lenient | 6.0 | A1_Biomechanical_Core | ElasticNet | 71 | 46 | 0.462 | 0.273 | 0.594 | 26.69 | 698.8 | 0.188 | `{'alpha': 0.1, 'l1_ratio': 0.7}` |
| lenient | 6.0 | A1_Biomechanical_Core | Ridge | 71 | 46 | 0.452 | 0.273 | 0.590 | 26.63 | 700.4 | 0.179 | `{'alpha': 10.0}` |
| lenient | 6.0 | A2_Biomechanical_NoK | SVM | 71 | 46 | 0.212 | 0.119 | 0.534 | 30.87 | 748.9 | 0.093 | `{'C': 1000, 'epsilon': 800, 'gamma': 0.01}` |
| lenient | 6.0 | A2_Biomechanical_NoK | Random_Forest | 71 | 46 | 0.918 | 0.244 | 0.632 | 23.50 | 702.0 | 0.674 | `{'n_estimators': 300, 'max_depth': 5, 'min_samples_split': 2, 'min_samples_leaf': 1}` |
| lenient | 6.0 | A2_Biomechanical_NoK | XGBoost | 71 | 46 | 0.619 | 0.188 | 0.602 | 23.95 | 638.4 | 0.432 | `{'learning_rate': 0.05, 'max_depth': 2, 'n_estimators': 30, 'reg_alpha': 1.0, 'reg_lambda': 0.5}` |
| lenient | 6.0 | A2_Biomechanical_NoK | Neural_Network | 71 | 46 | 0.550 | 0.280 | 0.599 | 26.03 | 701.6 | 0.270 | `{'hidden_layer_sizes': (40,), 'alpha': 0.1, 'learning_rate_init': 0.0005}` |
| lenient | 6.0 | A2_Biomechanical_NoK | Lasso | 71 | 46 | 0.489 | 0.263 | 0.582 | 26.30 | 707.0 | 0.226 | `{'alpha': 10.0}` |
| lenient | 6.0 | A2_Biomechanical_NoK | ElasticNet | 71 | 46 | 0.490 | 0.233 | 0.557 | 26.68 | 722.3 | 0.257 | `{'alpha': 0.001, 'l1_ratio': 0.3}` |
| lenient | 6.0 | A2_Biomechanical_NoK | Ridge | 71 | 46 | 0.490 | 0.233 | 0.557 | 26.68 | 722.3 | 0.256 | `{'alpha': 0.1}` |
| lenient | 6.0 | B_Clinical | SVM | 71 | 46 | 0.303 | 0.098 | 0.611 | 29.29 | 697.5 | 0.205 | `{'C': 500, 'epsilon': 800, 'gamma': 0.1}` |
| lenient | 6.0 | B_Clinical | Random_Forest | 71 | 46 | 0.530 | 0.240 | 0.509 | 25.12 | 702.1 | 0.290 | `{'n_estimators': 50, 'max_depth': 2, 'min_samples_split': 10, 'min_samples_leaf': 1}` |
| lenient | 6.0 | B_Clinical | XGBoost | 71 | 46 | 0.093 | 0.031 | 0.536 | 30.34 | 790.2 | 0.062 | `{'learning_rate': 0.005, 'max_depth': 1, 'n_estimators': 30, 'reg_alpha': 0.1, 'reg_lambda': 2.0}` |
| lenient | 6.0 | B_Clinical | Neural_Network | 71 | 46 | 0.529 | 0.274 | 0.574 | 24.93 | 681.3 | 0.254 | `{'hidden_layer_sizes': (80,), 'alpha': 0.1, 'learning_rate_init': 0.0001}` |
| lenient | 6.0 | B_Clinical | Lasso | 71 | 46 | 0.264 | 0.018 | 0.450 | 29.84 | 787.8 | 0.246 | `{'alpha': 0.01}` |
| lenient | 6.0 | B_Clinical | ElasticNet | 71 | 46 | 0.250 | 0.082 | 0.447 | 29.40 | 768.0 | 0.169 | `{'alpha': 1.0, 'l1_ratio': 0.7}` |
| lenient | 6.0 | B_Clinical | Ridge | 71 | 46 | 0.258 | 0.068 | 0.448 | 29.48 | 772.3 | 0.190 | `{'alpha': 10.0}` |
| lenient | 6.0 | C1_Combined | SVM | 71 | 46 | 0.390 | 0.286 | 0.590 | 25.53 | 678.5 | 0.103 | `{'C': 2000, 'epsilon': 500, 'gamma': 0.01}` |
| lenient | 6.0 | C1_Combined | Random_Forest | 71 | 46 | 0.665 | 0.268 | 0.613 | 25.08 | 693.6 | 0.397 | `{'n_estimators': 200, 'max_depth': 2, 'min_samples_split': 10, 'min_samples_leaf': 1}` |
| lenient | 6.0 | C1_Combined | XGBoost | 71 | 46 | 0.439 | 0.045 | 0.422 | 28.75 | 749.5 | 0.394 | `{'learning_rate': 0.005, 'max_depth': 4, 'n_estimators': 100, 'reg_alpha': 2.0, 'reg_lambda': 2.0}` |
| lenient | 6.0 | C1_Combined | Neural_Network | 71 | 46 | 0.495 | 0.344 | 0.626 | 24.71 | 646.2 | 0.151 | `{'hidden_layer_sizes': (80,), 'alpha': 0.3, 'learning_rate_init': 0.001}` |
| lenient | 6.0 | C1_Combined | Lasso | 71 | 46 | 0.500 | 0.314 | 0.630 | 25.93 | 668.0 | 0.186 | `{'alpha': 0.001}` |
| lenient | 6.0 | C1_Combined | ElasticNet | 71 | 46 | 0.500 | 0.314 | 0.630 | 25.92 | 667.9 | 0.185 | `{'alpha': 0.001, 'l1_ratio': 0.7}` |
| lenient | 6.0 | C1_Combined | Ridge | 71 | 46 | 0.500 | 0.319 | 0.632 | 25.83 | 665.9 | 0.180 | `{'alpha': 1.0}` |

## 七、可视化

### Strict 数据组：Distance × Model 热图 (q1plus)

![Strict Heatmap](FIG/SR0530_HP_Tuning_Heatmap_strict_q1plus.png)

### Lenient 数据组：Distance × Model 热图 (q1plus)

![Lenient Heatmap](FIG/SR0530_HP_Tuning_Heatmap_lenient_q1plus.png)

### Strict vs Lenient 各模型对比 (q1plus)

![Strict vs Lenient](FIG/SR0530_HP_Tuning_Strict_vs_Lenient_q1plus.png)

### 方案对比 (q1plus)

![Schema Comparison](FIG/SR0530_HP_Tuning_SchemaComparison_q1plus.png)

## 八、讨论

1. **数据组差异**：strict 模式移除了局部 ROI 异常值，数据更干净；lenient 模式保留了更多样本但可能混入异常。
2. **最佳参数稳定性**：如果某模型在 strict 和 lenient 下的最佳参数差异很大，提示该模型对异常值敏感。
3. **方案选择**：各方案表现因距离和数据组而异，最佳方案需结合 Test R²、Gap 和参数稳定性综合判断，具体见上述结果表。
4. **参数寻优局限**：Random Search 的 n_iter=10 是计算与精度的折中，关键模型可进一步增加迭代次数。

---

*Report generated automatically by SR_ML_hyperparameter_tuning.py*
