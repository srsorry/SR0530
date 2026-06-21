# SR0530 局部形状模型消融实验报告

> **目标**：按偏心率独立评估眼球形状特征（ACR、PSR_approx）对视锥细胞线性密度的预测增益。

> **方法**：互斥特征设计 + GroupKFold by Subject；ΔR² 基于 CV Test R²。

> **Primary Target**：Linear cone density (cones/mm²)。

---

## 一、ACR 与 PSR_approx 相关性检查

```
Data group: strict
Spearman rho(ACR, PSR_approx) = 0.6855, p = 1.9677e-106
Decision: Extended scheme kept as primary analysis (rho <= 0.75).
```

```
Data group: lenient
Spearman rho(ACR, PSR_approx) = 0.6846, p = 4.5541e-109
Decision: Extended scheme kept as primary analysis (rho <= 0.75).
```

## 二、ΔR² 曲线

![Delta R2](FIG/SR0530_DeltaR2_by_Eccentricity.png)

**解读**：
- ΔR² = CV_Test_R²(Shape) − CV_Test_R²(Baseline)。
- ΔR² > 0 表示 ACR 比例特征优于绝对眼轴长度。
- 阴影带使用配对差异的标准差（同一 CV 折内 Shape 与 Baseline R² 之差），而非简单叠加独立标准差。

## 三、每个偏心率消融结果

| 数据组 | 距离 | 模型 | Baseline R² | Shape R² | ΔR² | Extended R² |
|--------|------|------|------------|---------|-----|------------|
| lenient | 1.0 | ElasticNet | - | - | - | -0.234 |
| lenient | 1.0 | LMM | -0.372 | -0.658 | -0.287 | -0.526 |
| lenient | 1.0 | RF | -0.267 | -0.188 | 0.079 | -0.238 |
| lenient | 1.5 | ElasticNet | - | - | - | -0.280 |
| lenient | 1.5 | LMM | -0.343 | -0.916 | -0.573 | -0.298 |
| lenient | 1.5 | RF | -0.181 | -0.169 | 0.012 | -0.165 |
| lenient | 2.0 | ElasticNet | - | - | - | -0.053 |
| lenient | 2.0 | LMM | -0.038 | -0.485 | -0.447 | -0.027 |
| lenient | 2.0 | RF | -0.194 | 0.095 | 0.289 | -0.212 |
| lenient | 2.5 | ElasticNet | - | - | - | -0.116 |
| lenient | 2.5 | LMM | -0.095 | -0.127 | -0.032 | -0.027 |
| lenient | 2.5 | RF | -0.174 | -0.043 | 0.131 | -0.207 |
| lenient | 3.0 | ElasticNet | - | - | - | -0.113 |
| lenient | 3.0 | LMM | -0.097 | -0.227 | -0.129 | 0.034 |
| lenient | 3.0 | RF | -0.213 | -0.008 | 0.205 | -0.100 |
| lenient | 3.5 | ElasticNet | - | - | - | -0.106 |
| lenient | 3.5 | LMM | -0.111 | -0.232 | -0.121 | -0.045 |
| lenient | 3.5 | RF | -0.144 | -0.154 | -0.010 | -0.223 |
| lenient | 4.0 | ElasticNet | - | - | - | -0.133 |
| lenient | 4.0 | LMM | -0.151 | -0.223 | -0.073 | -0.057 |
| lenient | 4.0 | RF | -0.136 | -0.225 | -0.088 | -0.221 |
| lenient | 4.5 | ElasticNet | - | - | - | -0.209 |
| lenient | 4.5 | LMM | -0.325 | -0.169 | 0.156 | -0.195 |
| lenient | 4.5 | RF | -0.213 | -0.110 | 0.103 | -0.253 |
| lenient | 5.0 | ElasticNet | - | - | - | -0.086 |
| lenient | 5.0 | LMM | -0.143 | -0.222 | -0.079 | -0.035 |
| lenient | 5.0 | RF | -0.031 | -0.062 | -0.031 | -0.056 |
| lenient | 5.5 | ElasticNet | - | - | - | -0.139 |
| lenient | 5.5 | LMM | -0.182 | -0.217 | -0.035 | -0.141 |
| lenient | 5.5 | RF | 0.030 | -0.070 | -0.100 | -0.028 |
| lenient | 6.0 | ElasticNet | - | - | - | -0.142 |
| lenient | 6.0 | LMM | -0.123 | -0.263 | -0.140 | -0.037 |
| lenient | 6.0 | RF | -0.054 | -0.089 | -0.035 | -0.014 |
| strict | 1.0 | ElasticNet | - | - | - | -0.343 |
| strict | 1.0 | LMM | -0.319 | -0.558 | -0.239 | -0.492 |
| strict | 1.0 | RF | -0.396 | -0.098 | 0.298 | -0.388 |
| strict | 1.5 | ElasticNet | - | - | - | -0.212 |
| strict | 1.5 | LMM | -0.167 | -0.602 | -0.435 | -0.176 |
| strict | 1.5 | RF | -0.068 | 0.083 | 0.151 | -0.042 |
| strict | 2.0 | ElasticNet | - | - | - | -0.017 |
| strict | 2.0 | LMM | 0.071 | -0.090 | -0.161 | 0.079 |
| strict | 2.0 | RF | -0.083 | 0.054 | 0.137 | -0.070 |
| strict | 2.5 | ElasticNet | - | - | - | -0.128 |
| strict | 2.5 | LMM | -0.063 | -0.106 | -0.044 | -0.032 |
| strict | 2.5 | RF | -0.166 | -0.064 | 0.102 | -0.067 |
| strict | 3.0 | ElasticNet | - | - | - | -0.112 |
| strict | 3.0 | LMM | -0.070 | -0.158 | -0.088 | 0.070 |
| strict | 3.0 | RF | -0.210 | 0.072 | 0.283 | -0.045 |
| strict | 3.5 | ElasticNet | - | - | - | -0.064 |
| strict | 3.5 | LMM | -0.059 | -0.245 | -0.185 | 0.010 |
| strict | 3.5 | RF | -0.270 | 0.079 | 0.350 | -0.300 |
| strict | 4.0 | ElasticNet | - | - | - | -0.041 |
| strict | 4.0 | LMM | -0.105 | -0.423 | -0.318 | -0.034 |
| strict | 4.0 | RF | -0.306 | -0.179 | 0.127 | -0.188 |
| strict | 4.5 | ElasticNet | - | - | - | -0.024 |
| strict | 4.5 | LMM | -0.061 | -0.023 | 0.038 | 0.006 |
| strict | 4.5 | RF | -0.081 | 0.029 | 0.110 | -0.044 |
| strict | 5.0 | ElasticNet | - | - | - | -0.064 |
| strict | 5.0 | LMM | -0.145 | -0.104 | 0.041 | -0.038 |
| strict | 5.0 | RF | -0.115 | -0.113 | 0.002 | -0.085 |
| strict | 5.5 | ElasticNet | - | - | - | -0.071 |
| strict | 5.5 | LMM | -0.090 | -0.357 | -0.267 | -0.034 |
| strict | 5.5 | RF | -0.010 | -0.114 | -0.104 | 0.022 |
| strict | 6.0 | ElasticNet | - | - | - | -0.085 |
| strict | 6.0 | LMM | -0.146 | -0.145 | 0.001 | -0.092 |
| strict | 6.0 | RF | -0.002 | 0.073 | 0.075 | 0.024 |

## 四、论文写作素材

### Methods

> To isolate the effect of globe shape from absolute axial elongation, we adopted a mutual exclusion design: the baseline model included absolute axial length (AL), whereas the shape model replaced AL with the axial-to-corneal ratio (ACR = AL / R). The primary outcome was linear cone density (cones/mm²) to prevent circular reasoning. Due to the absence of lens thickness measurements, a simplified posterior segment proxy (PSR_approx = (AL − ACD) / AL) was used; age was included as a covariate. Separate models were trained for each eccentricity to respect the heteroscedastic variance structure. The incremental explanatory power of shape was quantified as ΔR² = CV_Test_R²(Shape) − CV_Test_R²(Baseline) using GroupKFold cross-validation by subject. For the extended model containing both AL and ACR, feature importance was assessed exclusively via ElasticNet standardized coefficients. The regularization parameter α was selected via cross-validation on the full dataset; only the cross-validated test performance of the final model is reported. Corneal curvature was converted to radius using K(mm) = 337.5 / K(D) when the input exceeded 10 D; otherwise it was treated as already in millimeters. Gender was encoded as binary before modeling.

### Discussion 模板

> **STRICT**: ACR 与 PSR_approx 相对独立（ρ ≤ 0.75），Extended 方案可纳入主分析，ElasticNet 系数支持多维度眼球形状表征。

> **LENIENT**: ACR 与 PSR_approx 相对独立（ρ ≤ 0.75），Extended 方案可纳入主分析，ElasticNet 系数支持多维度眼球形状表征。

---

*Report generated by SR_local_shape_model.py*
