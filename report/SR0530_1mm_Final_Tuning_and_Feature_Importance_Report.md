# SR0530 1.0 mm 最终精细调优与特征重要性报告

> **目标**：在 ≥1 象限平均策略下，对 1.0 mm 偏心率的全部模型/方案组合进行精细参数寻优、稳定性评估与特征重要性分析。

> **方法**：GroupKFold by Subject（5 折），精细搜索 50 组参数，Bootstrap 重复 50 次评估稳定性。

---

## 一、总体最佳配置

- **数据组**：lenient
- **方案**：C1_Combined
- **模型**：Ridge
- **Fine Test R^2**：0.365
- **Bootstrap R^2**：0.175 ± 0.161 [95% CI: -0.271, 0.387]
- **Train R^2 / Gap**：0.415 / 0.049
- **MAPE / RMSE**：11.22% / 555.6
- **样本量**：71 眼 / 46 subjects
- **最佳参数**：`{'alpha': 30.0}`

## 二、全部配置精细调优结果

| 数据组 | 方案 | 模型 | Coarse R^2 | Fine R^2 | Train R^2 | Gap | MAPE | RMSE | Bootstrap Mean±Std | 95% CI |
|--------|------|------|-----------|---------|----------|-----|------|------|--------------------|--------|
| lenient | A2_Biomechanical_NoK | Random_Forest | 0.452 | 0.445 | 0.757 | 0.312 | 9.49 | 474.4 | 0.043 ± 0.258 | [-0.572, 0.375] |
| lenient | A1_Biomechanical_Core | Random_Forest | 0.438 | 0.424 | 0.721 | 0.297 | 9.57 | 492.9 | 0.076 ± 0.228 | [-0.454, 0.397] |
| lenient | C1_Combined | Random_Forest | 0.417 | 0.526 | 0.782 | 0.255 | 10.46 | 494.7 | 0.068 ± 0.230 | [-0.413, 0.379] |
| strict | B_Clinical | Neural_Network | 0.360 | 0.300 | 0.610 | 0.310 | 9.29 | 447.0 | -0.231 ± 0.369 | [-1.149, 0.261] |
| lenient | C1_Combined | Neural_Network | 0.342 | 0.507 | 0.666 | 0.159 | 10.94 | 530.3 | 0.107 ± 0.173 | [-0.366, 0.365] |
| lenient | C1_Combined | XGBoost | 0.341 | 0.386 | 0.804 | 0.418 | 11.62 | 583.2 | 0.097 ± 0.212 | [-0.463, 0.442] |
| lenient | C1_Combined | Ridge | 0.330 | 0.365 | 0.415 | 0.049 | 11.22 | 555.6 | 0.175 ± 0.161 | [-0.271, 0.387] |
| strict | A1_Biomechanical_Core | XGBoost | 0.322 | 0.350 | 0.715 | 0.365 | 12.42 | 538.4 | 0.065 ± 0.244 | [-0.569, 0.351] |
| lenient | C1_Combined | SVM | 0.319 | 0.396 | 0.755 | 0.359 | 11.45 | 553.7 | -0.096 ± 0.310 | [-0.787, 0.292] |
| lenient | C1_Combined | Lasso | 0.313 | 0.423 | 0.561 | 0.138 | 9.88 | 516.3 | -0.130 ± 0.484 | [-1.531, 0.362] |
| lenient | C1_Combined | ElasticNet | 0.306 | 0.519 | 0.565 | 0.046 | 10.74 | 531.6 | 0.160 ± 0.182 | [-0.321, 0.391] |
| lenient | A1_Biomechanical_Core | XGBoost | 0.302 | 0.367 | 0.719 | 0.352 | 12.23 | 556.6 | 0.137 ± 0.189 | [-0.245, 0.445] |

## 三、特征重要性汇总

| 数据组 | 方案 | 模型 | 方法 | 排名 | 特征 | 重要性 |
|--------|------|------|------|------|------|--------|
| lenient | A1_Biomechanical_Core | Random_Forest | Builtin | 1 | Axial length (mm) | 0.8537 |
| lenient | A1_Biomechanical_Core | Random_Forest | Builtin | 2 | Age | 0.1055 |
| lenient | A1_Biomechanical_Core | Random_Forest | Builtin | 3 | Gender | 0.0408 |
| lenient | A1_Biomechanical_Core | Random_Forest | Permutation | 1 | Axial length (mm) | 1.2035 |
| lenient | A1_Biomechanical_Core | Random_Forest | Permutation | 2 | Age | 0.1065 |
| lenient | A1_Biomechanical_Core | Random_Forest | Permutation | 3 | Gender | 0.0394 |
| lenient | A1_Biomechanical_Core | Random_Forest | SHAP | 1 | Axial length (mm) | 438.8618 |
| lenient | A1_Biomechanical_Core | Random_Forest | SHAP | 2 | Age | 99.4949 |
| lenient | A1_Biomechanical_Core | Random_Forest | SHAP | 3 | Gender | 21.3018 |
| lenient | A1_Biomechanical_Core | XGBoost | Builtin | 1 | Axial length (mm) | 0.7697 |
| lenient | A1_Biomechanical_Core | XGBoost | Builtin | 2 | Age | 0.2303 |
| lenient | A1_Biomechanical_Core | XGBoost | Builtin | 3 | Gender | 0.0000 |
| lenient | A1_Biomechanical_Core | XGBoost | Permutation | 1 | Axial length (mm) | 1.0498 |
| lenient | A1_Biomechanical_Core | XGBoost | Permutation | 2 | Age | 0.1075 |
| lenient | A1_Biomechanical_Core | XGBoost | Permutation | 3 | Gender | 0.0000 |
| lenient | A1_Biomechanical_Core | XGBoost | SHAP | 1 | Axial length (mm) | 390.2881 |
| lenient | A1_Biomechanical_Core | XGBoost | SHAP | 2 | Age | 118.9194 |
| lenient | A1_Biomechanical_Core | XGBoost | SHAP | 3 | Gender | 0.0000 |
| lenient | A2_Biomechanical_NoK | Random_Forest | Builtin | 1 | Axial length (mm) | 0.7413 |
| lenient | A2_Biomechanical_NoK | Random_Forest | Builtin | 2 | Anterior chamber depth (mm) | 0.1457 |
| lenient | A2_Biomechanical_NoK | Random_Forest | Builtin | 3 | Age | 0.0823 |
| lenient | A2_Biomechanical_NoK | Random_Forest | Builtin | 4 | Gender | 0.0308 |
| lenient | A2_Biomechanical_NoK | Random_Forest | Permutation | 1 | Axial length (mm) | 1.2357 |
| lenient | A2_Biomechanical_NoK | Random_Forest | Permutation | 2 | Anterior chamber depth (mm) | 0.1426 |
| lenient | A2_Biomechanical_NoK | Random_Forest | Permutation | 3 | Age | 0.0893 |
| lenient | A2_Biomechanical_NoK | Random_Forest | Permutation | 4 | Gender | 0.0266 |
| lenient | A2_Biomechanical_NoK | Random_Forest | SHAP | 1 | Axial length (mm) | 427.6566 |
| lenient | A2_Biomechanical_NoK | Random_Forest | SHAP | 2 | Anterior chamber depth (mm) | 76.8904 |
| lenient | A2_Biomechanical_NoK | Random_Forest | SHAP | 3 | Age | 74.8085 |
| lenient | A2_Biomechanical_NoK | Random_Forest | SHAP | 4 | Gender | 15.3284 |
| lenient | C1_Combined | ElasticNet | Builtin | 1 | Axial length (mm) | 294.8990 |
| lenient | C1_Combined | ElasticNet | Builtin | 2 | Spherical equivalent refraction (D) | 198.4297 |
| lenient | C1_Combined | ElasticNet | Builtin | 3 | Age | 34.5648 |
| lenient | C1_Combined | ElasticNet | Builtin | 4 | Gender | 33.9315 |
| lenient | C1_Combined | ElasticNet | Permutation | 1 | Axial length (mm) | 0.4266 |
| lenient | C1_Combined | ElasticNet | Permutation | 2 | Spherical equivalent refraction (D) | 0.1790 |
| lenient | C1_Combined | ElasticNet | Permutation | 3 | Gender | 0.0073 |
| lenient | C1_Combined | ElasticNet | Permutation | 4 | Age | 0.0046 |
| lenient | C1_Combined | ElasticNet | SHAP | 1 | Axial length (mm) | 235.6117 |
| lenient | C1_Combined | ElasticNet | SHAP | 2 | Spherical equivalent refraction (D) | 151.3958 |
| lenient | C1_Combined | ElasticNet | SHAP | 3 | Gender | 33.3578 |
| lenient | C1_Combined | ElasticNet | SHAP | 4 | Age | 27.1719 |
| lenient | C1_Combined | Lasso | Builtin | 1 | Axial length (mm) | 397.5133 |
| lenient | C1_Combined | Lasso | Builtin | 2 | Spherical equivalent refraction (D) | 240.2616 |
| lenient | C1_Combined | Lasso | Builtin | 3 | Age | 70.6862 |
| lenient | C1_Combined | Lasso | Builtin | 4 | Gender | 50.1447 |
| lenient | C1_Combined | Lasso | Permutation | 1 | Axial length (mm) | 0.5604 |
| lenient | C1_Combined | Lasso | Permutation | 2 | Spherical equivalent refraction (D) | 0.1903 |
| lenient | C1_Combined | Lasso | Permutation | 3 | Age | 0.0149 |
| lenient | C1_Combined | Lasso | Permutation | 4 | Gender | 0.0118 |
| lenient | C1_Combined | Lasso | SHAP | 1 | Axial length (mm) | 317.5961 |
| lenient | C1_Combined | Lasso | SHAP | 2 | Spherical equivalent refraction (D) | 183.3122 |
| lenient | C1_Combined | Lasso | SHAP | 3 | Age | 55.5674 |
| lenient | C1_Combined | Lasso | SHAP | 4 | Gender | 49.2970 |
| lenient | C1_Combined | Neural_Network | Permutation | 1 | Axial length (mm) | 0.0011 |
| lenient | C1_Combined | Neural_Network | Permutation | 2 | Spherical equivalent refraction (D) | 0.0003 |
| lenient | C1_Combined | Neural_Network | Permutation | 3 | Age | 0.0002 |
| lenient | C1_Combined | Neural_Network | Permutation | 4 | Gender | -0.0002 |
| lenient | C1_Combined | Neural_Network | SHAP | 1 | Axial length (mm) | 0.3354 |
| lenient | C1_Combined | Neural_Network | SHAP | 2 | Spherical equivalent refraction (D) | 0.1359 |
| lenient | C1_Combined | Neural_Network | SHAP | 3 | Gender | 0.0637 |
| lenient | C1_Combined | Neural_Network | SHAP | 4 | Age | 0.0438 |
| lenient | C1_Combined | Random_Forest | Builtin | 1 | Axial length (mm) | 0.5960 |
| lenient | C1_Combined | Random_Forest | Builtin | 2 | Spherical equivalent refraction (D) | 0.3229 |
| lenient | C1_Combined | Random_Forest | Builtin | 3 | Age | 0.0622 |
| lenient | C1_Combined | Random_Forest | Builtin | 4 | Gender | 0.0189 |
| lenient | C1_Combined | Random_Forest | Permutation | 1 | Axial length (mm) | 0.6345 |
| lenient | C1_Combined | Random_Forest | Permutation | 2 | Spherical equivalent refraction (D) | 0.2299 |
| lenient | C1_Combined | Random_Forest | Permutation | 3 | Age | 0.0505 |
| lenient | C1_Combined | Random_Forest | Permutation | 4 | Gender | 0.0169 |
| lenient | C1_Combined | Random_Forest | SHAP | 1 | Axial length (mm) | 303.3712 |
| lenient | C1_Combined | Random_Forest | SHAP | 2 | Spherical equivalent refraction (D) | 190.8733 |
| lenient | C1_Combined | Random_Forest | SHAP | 3 | Age | 52.3134 |
| lenient | C1_Combined | Random_Forest | SHAP | 4 | Gender | 13.3671 |
| lenient | C1_Combined | Ridge | Builtin | 1 | Axial length (mm) | 286.0447 |
| lenient | C1_Combined | Ridge | Builtin | 2 | Spherical equivalent refraction (D) | 194.0466 |
| lenient | C1_Combined | Ridge | Builtin | 3 | Gender | 32.8093 |
| lenient | C1_Combined | Ridge | Builtin | 4 | Age | 32.2058 |
| lenient | C1_Combined | Ridge | Permutation | 1 | Axial length (mm) | 0.4152 |
| lenient | C1_Combined | Ridge | Permutation | 2 | Spherical equivalent refraction (D) | 0.1770 |
| lenient | C1_Combined | Ridge | Permutation | 3 | Gender | 0.0070 |
| lenient | C1_Combined | Ridge | Permutation | 4 | Age | 0.0040 |
| lenient | C1_Combined | Ridge | SHAP | 1 | Axial length (mm) | 228.5375 |
| lenient | C1_Combined | Ridge | SHAP | 2 | Spherical equivalent refraction (D) | 148.0516 |
| lenient | C1_Combined | Ridge | SHAP | 3 | Gender | 32.2546 |
| lenient | C1_Combined | Ridge | SHAP | 4 | Age | 25.3174 |
| lenient | C1_Combined | SVM | Permutation | 1 | Axial length (mm) | 0.4091 |
| lenient | C1_Combined | SVM | Permutation | 2 | Spherical equivalent refraction (D) | 0.3714 |
| lenient | C1_Combined | SVM | Permutation | 3 | Gender | 0.1766 |
| lenient | C1_Combined | SVM | Permutation | 4 | Age | 0.1612 |
| lenient | C1_Combined | SVM | SHAP | 1 | Axial length (mm) | 238.0877 |
| lenient | C1_Combined | SVM | SHAP | 2 | Spherical equivalent refraction (D) | 196.0273 |
| lenient | C1_Combined | SVM | SHAP | 3 | Age | 102.0926 |
| lenient | C1_Combined | SVM | SHAP | 4 | Gender | 85.6232 |
| lenient | C1_Combined | XGBoost | Builtin | 1 | Axial length (mm) | 0.4717 |
| lenient | C1_Combined | XGBoost | Builtin | 2 | Spherical equivalent refraction (D) | 0.2343 |
| lenient | C1_Combined | XGBoost | Builtin | 3 | Age | 0.1812 |
| lenient | C1_Combined | XGBoost | Builtin | 4 | Gender | 0.1128 |
| lenient | C1_Combined | XGBoost | Permutation | 1 | Axial length (mm) | 0.5513 |
| lenient | C1_Combined | XGBoost | Permutation | 2 | Spherical equivalent refraction (D) | 0.2601 |
| lenient | C1_Combined | XGBoost | Permutation | 3 | Gender | 0.0578 |
| lenient | C1_Combined | XGBoost | Permutation | 4 | Age | 0.0518 |
| lenient | C1_Combined | XGBoost | SHAP | 1 | Axial length (mm) | 263.4713 |
| lenient | C1_Combined | XGBoost | SHAP | 2 | Spherical equivalent refraction (D) | 189.6319 |
| lenient | C1_Combined | XGBoost | SHAP | 3 | Age | 47.2026 |
| lenient | C1_Combined | XGBoost | SHAP | 4 | Gender | 34.1285 |
| strict | A1_Biomechanical_Core | XGBoost | Builtin | 1 | Axial length (mm) | 0.8305 |
| strict | A1_Biomechanical_Core | XGBoost | Builtin | 2 | Age | 0.1695 |
| strict | A1_Biomechanical_Core | XGBoost | Builtin | 3 | Gender | 0.0000 |
| strict | A1_Biomechanical_Core | XGBoost | Permutation | 1 | Axial length (mm) | 1.1260 |
| strict | A1_Biomechanical_Core | XGBoost | Permutation | 2 | Age | 0.1299 |
| strict | A1_Biomechanical_Core | XGBoost | Permutation | 3 | Gender | 0.0000 |
| strict | A1_Biomechanical_Core | XGBoost | SHAP | 1 | Axial length (mm) | 384.3961 |
| strict | A1_Biomechanical_Core | XGBoost | SHAP | 2 | Age | 123.9354 |
| strict | A1_Biomechanical_Core | XGBoost | SHAP | 3 | Gender | 0.0000 |
| strict | B_Clinical | Neural_Network | Permutation | 1 | Spherical equivalent refraction (D) | 0.0009 |
| strict | B_Clinical | Neural_Network | Permutation | 2 | Age | -0.0002 |
| strict | B_Clinical | Neural_Network | Permutation | 3 | Gender | -0.0002 |
| strict | B_Clinical | Neural_Network | SHAP | 1 | Spherical equivalent refraction (D) | 0.4116 |
| strict | B_Clinical | Neural_Network | SHAP | 2 | Gender | 0.0827 |
| strict | B_Clinical | Neural_Network | SHAP | 3 | Age | 0.0336 |

## 四、主要发现

1. **最稳定配置**：lenient + C1_Combined + Ridge (Bootstrap R^2 = 0.175)
2. **Fine 最高配置**：lenient + C1_Combined + Random_Forest (Fine R^2 = 0.526)
3. **平均特征重要性排序（已归一化）**：Axial length (mm) (1.000, rank 1), Spherical equivalent refraction (D) (0.565, rank 2), Anterior chamber depth (mm) (0.136, rank 3), Age (0.091, rank 4), Gender (0.011, rank 5)
    - 三种方法（Builtin / Permutation / SHAP）在各自模型内归一化后取平均。
    - 第一名 `Axial length (mm)` 的归一化重要性（1.000）显著高于第二名 `Spherical equivalent refraction (D)`（0.565）。

## 五、可视化

### Fine R^2 汇总

![Fine R2 Summary](FIG/SR0530_1mm_Fine_R2_Summary.png)

### Bootstrap 稳定性

![Bootstrap Stability](FIG/SR0530_1mm_Bootstrap_Stability_Summary.png)

### 特征重要性热图

![Importance Heatmap](FIG/SR0530_1mm_Importance_Heatmap.png)

## 六、讨论

1. **精细寻优效果**：对比 Coarse 与 Fine R^2，可判断原搜索空间是否充分。
2. **稳定性优先**：Bootstrap 95% CI 下限更高的配置比单纯 Fine R^2 最高的配置更值得信赖。
3. **特征重要性一致性**：若 Permutation、Builtin、SHAP 三种方法均将某特征排在前列，则该特征对 1.0 mm 密度预测最为关键。
4. **最终模型选择**：建议采用 Bootstrap Mean 最高且 Gap 最小的配置作为最终报告用模型。

---

*Report generated by SR_ML_1mm_final_tuning.py*
