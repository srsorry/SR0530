# SR0627_A_Best_RobustLinear_Diagnostics 报告

> **来源配置**：`report/SR0530_ALK_10fold_Final_Tuning_Report.md` 中的总体最佳配置

---

## 一、最佳配置

| 项目 | 内容 |
|------|------|
| data_group | lenient |
| distance_mm | 1.5 |
| schema | C1_Combined_ALK |
| model_name | Robust_Linear_Regression |
| params | `{'epsilon': 1.8, 'alpha': 0.05}` |
| n_splits | 10 |
| random_state | 42 |
| cv_seed | 43 |

## 二、10-fold 交叉验证性能（含 95% CI）

### 与 tuning 报告一致的最佳 CV 结果

- **Mean Test R²**：0.504 [95% CI: 0.326, 0.682]
- **Mean Test RMSE**：458.0 [95% CI: 200.2, 715.8]
- **Mean Gap**：0.081
- **CV 种子**：43

### 本次 fold-level 汇总

- **Mean Test R²**：0.504 [95% CI: 0.326, 0.682]
- **Mean Test RMSE**：458.0 [95% CI: 200.2, 715.8]
- **Mean Gap (Train - Test R²)**：0.081
- **Overall CV R²**：0.546
- **Overall CV RMSE**：510.1

### 每折详细结果

|   Fold |   Train_R2 |   Test_R2 |    Gap |   Test_RMSE |   N_Train |   N_Test |
|-------:|-----------:|----------:|-------:|------------:|----------:|---------:|
|  1.000 |      0.614 |     0.316 |  0.298 |     691.645 |    62.000 |   10.000 |
|  2.000 |      0.575 |     0.627 | -0.052 |     112.418 |    65.000 |    7.000 |
|  3.000 |      0.621 |     0.220 |  0.401 |     416.625 |    64.000 |    8.000 |
|  4.000 |      0.582 |     0.641 | -0.060 |     169.340 |    62.000 |   10.000 |
|  5.000 |      0.562 |     0.647 | -0.084 |     486.531 |    65.000 |    7.000 |
|  6.000 |      0.555 |     0.779 | -0.223 |     226.685 |    64.000 |    8.000 |
|  7.000 |      0.517 |     0.790 | -0.274 |     368.243 |    65.000 |    7.000 |
|  8.000 |      0.661 |     0.047 |  0.614 |    1353.646 |    68.000 |    4.000 |
|  9.000 |      0.571 |     0.589 | -0.018 |     503.880 |    66.000 |    6.000 |
| 10.000 |      0.592 |     0.381 |  0.211 |     250.775 |    67.000 |    5.000 |

## 三、学习曲线

> 学习曲线基于与最佳 CV 相同的 10-fold GroupKFold by Subject 拆分（seed = 43)，对每个训练集大小计算训练/验证 R² 和 RMSE 的均值 ± 标准差。

![Learning Curves](FIG/SR0627_A_Best_RobustLinear_Diagnostics/SR0627_A_Learning_Curves.pdf)

## 四、Observed vs Predicted

![Observed vs Predicted](FIG/SR0627_A_Best_RobustLinear_Diagnostics/SR0627_A_Observed_vs_Predicted.pdf)

## 五、SHAP 特征重要性（Cross-validated，Method B）

| Feature                             |   MeanAbsSHAP |
|:------------------------------------|--------------:|
| AL/K ratio                          |      209.8485 |
| Axial length (mm)                   |      125.2503 |
| Gender                              |       93.6994 |
| Spherical equivalent refraction (D) |       58.3231 |
| Age                                 |       28.1329 |

![SHAP Summary](FIG/SR0627_A_Best_RobustLinear_Diagnostics/SR0627_A_SHAP_Summary.pdf)

---

*Report generated automatically by SR0627_A_Best_RobustLinear_Diagnostics.py*
