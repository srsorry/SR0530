# SR0628_B C1_Combined_ALK 在 1.5 / 5.0 / 5.5 mm 的性能汇总与最佳模型诊断

- **数据组**：lenient（71 eyes / 46 subjects）
- **方案**：C1_Combined_ALK
- **CV**：10-fold GroupKFold by Subject，按 Myopia 分层
- **性能来源**：`report/SR0530_ALK_10fold_Final_Tuning_Report.md` 表 VII（单次 10-fold 各模型最佳参数下的结果），并额外计算 Multiple Linear Regression；MSE = RMSE²
- **诊断图说明**：散点图与 SHAP 图使用与报告最佳 R²=0.504 相匹配的 CV 拆分种子（seed=43）生成

## 一、各距离模型性能

> `RMSE_std` = RMSE / SD(y)，`MSE_std` = RMSE_std²；即目标变量标准化后的误差，便于跨研究比较。

### 1.5 mm

| Model | Test R² | RMSE | MSE | RMSE_std | MSE_std | Gap | Best Params |
|-------|---------|------|-----|----------|---------|-----|-------------|
| Robust_Linear_Regression | 0.504 | 458.0 | 209764.0 | 0.629 | 0.396 | 0.081 | `{'epsilon': 1.8, 'alpha': 0.05}` |
| Neural_Network | 0.423 | 382.4 | 146229.8 | 0.525 | 0.276 | 0.219 | `{'hidden_layer_sizes': (100, 50), 'alpha': 0.1, 'learning_rate_init': 0.001}` |
| SVM | 0.417 | 403.9 | 163135.2 | 0.555 | 0.308 | 0.223 | `{'C': 5000, 'epsilon': 200, 'gamma': 0.005}` |
| Ridge | 0.399 | 389.2 | 151476.6 | 0.534 | 0.286 | 0.222 | `{'alpha': 0.5}` |
| ElasticNet | 0.394 | 391.2 | 153037.4 | 0.537 | 0.289 | 0.227 | `{'alpha': 0.005, 'l1_ratio': 0.8}` |
| Lasso | 0.393 | 391.5 | 153272.2 | 0.538 | 0.289 | 0.228 | `{'alpha': 0.1}` |
| Random_Forest | 0.371 | 410.6 | 168592.4 | 0.564 | 0.318 | 0.491 | `{'n_estimators': 100, 'max_depth': 3, 'min_samples_split': 2, 'min_samples_leaf': 2}` |
| XGBoost | 0.359 | 428.3 | 183440.9 | 0.588 | 0.346 | 0.410 | `{'learning_rate': 0.03, 'max_depth': 2, 'n_estimators': 50, 'reg_alpha': 0.5, 'reg_lambda': 0.1}` |
| Multiple_Linear_Regression | -0.436 | 469.4 | 220299.1 | 0.645 | 0.415 | 0.935 | `{}` |

### 5.0 mm

| Model | Test R² | RMSE | MSE | RMSE_std | MSE_std | Gap | Best Params |
|-------|---------|------|-----|----------|---------|-----|-------------|
| SVM | 0.039 | 635.1 | 403352.0 | 0.842 | 0.709 | 0.316 | `{'C': 500, 'epsilon': 200, 'gamma': 0.01}` |
| Robust_Linear_Regression | -0.078 | 605.5 | 366630.2 | 0.803 | 0.645 | 0.275 | `{'epsilon': 1.2, 'alpha': 0.1}` |
| Ridge | -0.095 | 595.1 | 354144.0 | 0.789 | 0.623 | 0.453 | `{'alpha': 100.0}` |
| Neural_Network | -0.170 | 614.5 | 377610.2 | 0.815 | 0.664 | 0.744 | `{'hidden_layer_sizes': (40,), 'alpha': 0.3, 'learning_rate_init': 0.0005}` |
| ElasticNet | -0.277 | 558.4 | 311810.6 | 0.741 | 0.548 | 0.626 | `{'alpha': 1.0, 'l1_ratio': 0.05}` |
| XGBoost | -0.287 | 569.5 | 324330.2 | 0.755 | 0.570 | 0.895 | `{'learning_rate': 0.03, 'max_depth': 3, 'n_estimators': 30, 'reg_alpha': 0.5, 'reg_lambda': 1.0}` |
| Random_Forest | -0.293 | 522.6 | 273110.8 | 0.693 | 0.480 | 0.973 | `{'n_estimators': 300, 'max_depth': 2, 'min_samples_split': 2, 'min_samples_leaf': 4}` |
| Lasso | -0.420 | 606.2 | 367478.4 | 0.804 | 0.646 | 0.922 | `{'alpha': 0.003}` |
| Multiple_Linear_Regression | -3.538 | 681.9 | 464937.2 | 0.904 | 0.818 | 3.893 | `{}` |

### 5.5 mm

| Model | Test R² | RMSE | MSE | RMSE_std | MSE_std | Gap | Best Params |
|-------|---------|------|-----|----------|---------|-----|-------------|
| SVM | 0.145 | 624.5 | 390000.2 | 0.765 | 0.585 | 0.235 | `{'C': 500, 'epsilon': 200, 'gamma': 0.01}` |
| Robust_Linear_Regression | 0.078 | 635.6 | 403987.4 | 0.779 | 0.606 | 0.347 | `{'epsilon': 1.0, 'alpha': 0.0005}` |
| Neural_Network | -0.032 | 605.7 | 366872.5 | 0.742 | 0.550 | 0.640 | `{'hidden_layer_sizes': (40,), 'alpha': 0.3, 'learning_rate_init': 0.0005}` |
| Ridge | -0.114 | 617.6 | 381429.8 | 0.757 | 0.572 | 0.468 | `{'alpha': 100.0}` |
| ElasticNet | -0.132 | 601.7 | 362042.9 | 0.737 | 0.543 | 0.678 | `{'alpha': 0.05, 'l1_ratio': 0.5}` |
| Lasso | -0.176 | 615.9 | 379332.8 | 0.754 | 0.569 | 0.722 | `{'alpha': 0.1}` |
| Random_Forest | -0.231 | 635.4 | 403733.2 | 0.778 | 0.606 | 0.948 | `{'n_estimators': 200, 'max_depth': 3, 'min_samples_split': 10, 'min_samples_leaf': 4}` |
| XGBoost | -0.313 | 608.5 | 370272.2 | 0.745 | 0.556 | 0.776 | `{'learning_rate': 0.005, 'max_depth': 1, 'n_estimators': 300, 'reg_alpha': 0.1, 'reg_lambda': 2.0}` |
| Multiple_Linear_Regression | -3.068 | 801.5 | 642368.8 | 0.982 | 0.964 | 3.412 | `{}` |

## 二、最佳 Robust Linear Regression @ 1.5 mm 诊断图

- **最佳参数**：{'epsilon': 1.8, 'alpha': 0.05}
- **10-fold mean R² ± SD**：0.504 ± 0.249
- **10-fold mean RMSE ± SD**：458.0 ± 360.3
- **10-fold mean MAPE ± SD**：8.5 ± 4.3%
- **全样本 Pearson r**：0.950

### Observed vs Predicted 散点图（n=71 eyes）

![Observed vs Predicted](FIG/SR0628_B/SR0628_B_Scatter_Robust_Linear_Regression_C1_Combined_ALK_1.5mm.png)

[Download PDF version](FIG/SR0628_B/SR0628_B_Scatter_Robust_Linear_Regression_C1_Combined_ALK_1.5mm.pdf)

### SHAP Summary

![SHAP Summary](FIG/SR0628_B/SR0628_B_SHAP_Robust_Linear_Regression_C1_Combined_ALK_1.5mm.png)

[Download PDF version](FIG/SR0628_B/SR0628_B_SHAP_Robust_Linear_Regression_C1_Combined_ALK_1.5mm.pdf)

### Residual Q-Q plot（n=71 eyes）

![Residual Q-Q](FIG/SR0628_B/SR0628_B_QQ_Residuals_Robust_Linear_Regression_C1_Combined_ALK_1.5mm.png)

[Download PDF version](FIG/SR0628_B/SR0628_B_QQ_Residuals_Robust_Linear_Regression_C1_Combined_ALK_1.5mm.pdf)

---

*Generated by src/SR0628_B_C1_Combined_ALK_Diagnostics.py*
