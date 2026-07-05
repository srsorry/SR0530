# SR0705_A_FIG_Report 组合图表报告

> **数据**：lenient 数据集（71 eyes / 46 subjects）
> **生成日期**：2026-07-05

---

## 一、眼轴长度与角密度/线密度关系

### 1.1 偏心率 1.0°

![1.0°](FIG/FIGA/FIGA_1.0deg.png)

左图：Linear cone density (cones/mm²) vs Axial Length (mm)
右图：Angular cone density (cones/deg²) vs Axial Length (mm)
含回归线、R²、Slope、P 值。

[下载 PDF](FIG/FIGA/FIGA_1.0deg.pdf)

### 1.2 偏心率 1.5°–6.0°

![1.5-6.0°](FIG/FIGA/FIGA_1.5-6.0deg.png)

子图 A：Linear cone density vs Axial Length — 各偏心率叠加
子图 B：Angular cone density vs Axial Length — 各偏心率叠加
图例以颜色区分偏心率，标注回归方程。

[下载 PDF](FIG/FIGA/FIGA_1.5-6.0deg.pdf)

---

## 二、等效球镜与眼轴长度关系 + GEE 多因素回归

### 2.1 SER vs AL 散点图

![FIGB1](FIG/FIGB/FIGB1.png)

Spherical Equivalent Refraction (D) vs Axial Length (mm)，含线性回归方程、Pearson r、P 值。

[下载 PDF](FIG/FIGB/FIGB1.pdf)

### 2.2 GEE 多因素回归森林图（1.0°）

![FIGB2](FIG/FIGB/FIGB2.png)

标准化 β 系数 ± 95% CI，基于 GEE（Exchangeable 相关结构，Subject 聚类）。各预测变量对 1.0° 角密度的独立贡献。

[下载 PDF](FIG/FIGB/FIGB2.pdf)

---

## 三、LMM 残差诊断

### 3.1 各偏心率 LMM 残差 Q-Q 图

![LMM QQ](FIG/SR0628_C/SR0628_C_lenient_q1_LMM_Residual_QQPlots.png)

每个偏心率独立拟合 LMM（Subject 随机截距 + Eye 固定效应），标准化残差的 Q-Q 图。n=71 eyes / 46 subjects，lenient q1plus。

[下载 PDF](FIG/SR0628_C/SR0628_C_lenient_q1_LMM_Residual_QQPlots.pdf)

---

## 四、机器学习预测性能

### 4.1 5-fold CV 性能汇总（C1_Combined_ALK）

| 偏心率 | 最佳模型 | R^2 | RMSE | MSE |
|--------|----------|-----|------|-----|
| 1.5 deg | Lasso | 0.611 | 446.6 | 199,452 |
| 5.0 deg | Neural Network | 0.370 | 587.5 | 345,156 |
| 5.5 deg | Neural Network | 0.363 | 651.2 | 424,061 |

> 5-fold GroupKFold by Subject，Myopia 分层。1.5 deg 处预测性能最优，Lasso 线性模型简洁可解释。全模型非负。

### 4.2 最佳模型 @ 1.5 deg：Lasso 诊断图

**Observed vs Predicted 散点图**

![Lasso Scatter](FIG/SR0628_D/SR0628_D_Scatter_Lasso_C1_Combined_ALK_1.5mm.png)

n=71 eyes，含 5-fold CV 均值 R^2/RMSE/MAPE，全样本 Pearson r。

[下载 PDF](FIG/SR0628_D/SR0628_D_Scatter_Lasso_C1_Combined_ALK_1.5mm.pdf)

**SHAP 特征重要性**

![Lasso SHAP](FIG/SR0628_D/SR0628_D_SHAP_Lasso_C1_Combined_ALK_1.5mm.png)

SHAP summary plot，展示各特征对预测密度值的边际贡献方向与大小。

[下载 PDF](FIG/SR0628_D/SR0628_D_SHAP_Lasso_C1_Combined_ALK_1.5mm.pdf)

**残差 Q-Q 图**

![Lasso QQ](FIG/SR0628_D/SR0628_D_QQ_Residuals_Lasso_C1_Combined_ALK_1.5mm.png)

Lasso 回归标准化残差的 Q-Q 图，n=71 eyes。

[下载 PDF](FIG/SR0628_D/SR0628_D_QQ_Residuals_Lasso_C1_Combined_ALK_1.5mm.pdf)

---

*Generated: 2026-07-05 | SR0705_A*
