# SR0628_F 检查报告：第 4–6 项问题清单

> 说明：本报告仅做现状梳理，尚未修改任何文件。

---

## 4. 1.5–6° 偏心率上光感受器密度与眼部参数的多元线性回归系数

### 已存在的输出（SR0628_E）

| 文件 | 说明 |
|------|------|
| `report/SR0628_E_MLR_Coefficients_1.5_6.0deg.md` | Markdown 汇总报告 |
| `report/tables/SR0628_E_MLR_Coefficients_1.5_6.0deg.csv` | CSV 系数表 |

- **方法**：`statsmodels` OLS，模型 `Density ~ AL + Age + Gender + SER + K + ACD`
- **内容**：1.5–6.0°（当前标注为 mm）每个距离的 **Linear** 和 **Angular** 密度系数，包含 Beta、SE、P、95% CI、R²、Adj R²、N=71。
- **与 1° 方法的差异**：SR0628_E 输出的是所有预测变量的完整系数表；而 1° 的 `src/SR_FigA_MLR_Split_71eyes.py` 只输出 AL 的系数（beta、se、t、p、R²），并生成偏残差图。

### 尚未运行的 1° 方法脚本

- `src/SR_FigA_MLR_Split_71eyes.py`（即“直接复制 1° 的方法”）**尚未执行**，输出目录 `report/FIG/FigA_MLR_Split/` 为空。
- 该脚本若运行会生成：
  - 1.0° 处线密度 / 角密度 vs AL 的偏残差图
  - 1.5–6.0° 处线密度 vs AL 的偏残差图（多距离叠加）
  - 系数 CSV：`report/FIG/FigA_MLR_Split/SR0530_FigA_MLR_Coefficients.csv`
- **注意**：该脚本对 1.5–6.0° 只做了 **线密度**，没有做角密度。

### 单位问题

- SR0628_E 的列名/标题原使用 `Distance (mm)`，已统一改为 `Distance (°)` / `Eccentricity (°)`。✅ 已完成

---

## 5. 机器学习 R² / RMSE / MSE；5° 和 5.5° 不要全是负值

### 5.1 当前 10-fold 结果（SR0628_B，限定 C1_Combined_ALK）

文件：`report/SR0628_B_C1_Combined_ALK_10fold_Performance_1.5_5_5.5.md`

| 距离 | 最佳模型 | Test R² | RMSE_std | 备注 |
|------|----------|---------|----------|------|
| 5.0° | SVM | **0.039** | 0.842 | 其余 7 个模型为负 |
| 5.5° | SVM | **0.145** | 0.765 | 其余 7 个模型为负 |

- 结论：10-fold 在 C1_Combined_ALK 上 5.0/5.5° 表现很差，最佳 R² 仅接近 0。

### 5.2 当前 5-fold 结果（SR0628_D，限定 C1_Combined_ALK）

文件：`report/SR0628_D_C1_Combined_ALK_5fold_Performance_1.5_5_5.5.md`

| 距离 | 最佳模型 | Test R² | RMSE_std | 备注 |
|------|----------|---------|----------|------|
| 5.0° | Neural_Network | **0.370** | 0.779 | 全部模型非负 |
| 5.5° | Neural_Network | **0.363** | 0.798 | 全部模型非负 |

- 结论：5-fold 在 5.0/5.5° 上明显优于 10-fold。

### 5.3 原始全量调优报告中的更好结果（供参考）

- **10-fold 全结果**：`report/SR0530_ALK_10fold_Final_Tuning_Report.md`
  - 5.0°：最佳为 `B_Clinical_ALK | Robust_Linear_Regression`，R² = **0.131**
  - 5.5°：最佳为 `C1_Combined_K_ALK | SVM`，R² = **0.167**
- **5-fold 全结果**：`report/SR0530_ALK_5fold_Final_Tuning_Report.md`
  - 5.0°：最佳为 `A2_Biomechanical_ALK | Random_Forest`，R² = **0.458**
  - 5.5°：最佳为 `A2_Biomechanical_K_ALK | Lasso`，R² = **0.376**

### 5.4 建议

- 若坚持使用 **C1_Combined_ALK**，5-fold 结果已经满足“5°/5.5° 不全为负”。
- 若允许在 5°/5.5° 选择其他特征组合/模型，可得到 R² ≈ 0.37–0.46 的结果。
- 标准化后的 RMSE/MSE（`RMSE_std`、`MSE_std`）已经是 0.x–1.x 量级，可用于跨研究比较。

---

## 6. 图片文字 / 字体 / 缺失图检查

### 6.1 PDF 字体可编辑性检查结果

| 文件 | 嵌入字体 | 是否 Calibri | 是否可编辑 |
|------|----------|--------------|------------|
| `report/FIG/SR0627_A_Best_RobustLinear_Diagnostics/SR0627_A_Learning_Curves.pdf` | DejaVuSans, DejaVuSans-Bold | 否 | 是 |
| `report/FIG/SR0627_A_Best_RobustLinear_Diagnostics/SR0627_A_Observed_vs_Predicted.pdf` | DejaVuSans, DejaVuSans-Bold | 否 | 是 |
| `report/FIG/SR0627_A_Best_RobustLinear_Diagnostics/SR0627_A_SHAP_Summary.pdf` | DejaVuSans, DejaVuSans-Bold | 否 | 是 |
| `report/FIG/SR0628_B/SR0628_B_QQ_Residuals_Robust_Linear_Regression_C1_Combined_ALK_1.5mm.pdf` | Calibri | 是 | 是 |
| `report/FIG/SR0628_B/SR0628_B_Scatter_Robust_Linear_Regression_C1_Combined_ALK_1.5mm.pdf` | Calibri | 是 | 是 |
| `report/FIG/SR0628_B/SR0628_B_SHAP_Robust_Linear_Regression_C1_Combined_ALK_1.5mm.pdf` | Calibri | 是 | 是 |
| `report/FIG/SR0628_C/SR0628_C_lenient_q1_LMM_Residual_QQPlots.pdf` | Calibri, Calibri-Bold | 是 | 是 |
| `report/FIG/SR0628_D/SR0628_D_QQ_Residuals_Lasso_C1_Combined_ALK_1.5mm.pdf` | Calibri | 是 | 是 |
| `report/FIG/SR0628_D/SR0628_D_Scatter_Lasso_C1_Combined_ALK_1.5mm.pdf` | Calibri | 是 | 是 |
| `report/FIG/SR0628_D/SR0628_D_SHAP_Lasso_C1_Combined_ALK_1.5mm.pdf` | Calibri | 是 | 是 |
| `report/FIG/SR0628_D/SR0628_D_QQ_Residuals_Robust_Linear_Regression_C1_Combined_ALK_1.5mm.pdf` | DejaVuSans | 否 | 是 |
| `report/FIG/SR0628_D/SR0628_D_Scatter_Robust_Linear_Regression_C1_Combined_ALK_1.5mm.pdf` | DejaVuSans | 否 | 是 |
| `report/FIG/SR0628_D/SR0628_D_Scatter_SVM_C1_Combined_ALK_1.5mm.pdf` | DejaVuSans | 否 | 是 |
| `report/FIG/SR0628_D/SR0628_D_SHAP_Robust_Linear_Regression_C1_Combined_ALK_1.5mm.pdf` | DejaVuSans | 否 | 是 |
| `genData/FIGA/FIGA.pdf` | DejaVuSans, DejaVuSans-Bold | 否 | 是 |
| `genData/FIGA/FIGA_1.0deg.pdf` | Calibri, Calibri-Bold | 是 | 是 |
| `genData/FIGA/FIGA_1.5-6.0deg.pdf` | Calibri, Calibri-Bold | 是 | 是 |
| `genData/FIGB/FIGB1.pdf` | Arial, Arial-Bold | 否 | 是 |
| `genData/FIGB/FIGB2.pdf` | Calibri, Calibri-Bold | 是 | 是 |

- **文字都是可编辑的**（Type42 / 字体描述符存在），但部分 PDF 仍未使用 Calibri：SR0627_A、FIGB1、FIGA.pdf，以及 SR0628_D 中遗留的旧图（Robust/SVM）。

### 6.2 眼轴和等效球镜的线性关系

- **已存在**：`genData/FIGB/FIGB1.pdf`
  - 内容为 SE（x） vs AL（y） 散点 + 线性回归，含方程、r、P。
- **问题**：字体为 Arial，需改为 Calibri。
- **若需要 AL 为 x、SER 为 y 的版本**：目前未输出。

### 6.3 随机森林图

- **旧图（10-fold，C1_Combined_ALK）**：
  - `report/FIG/C1_Combined_ALK_10fold/SR0530_C1_Combined_ALK_10fold_SHAP_Best_Random_Forest_1.5mm.png`
  - 仅有 PNG，无 PDF；字体不是 Calibri。
- **1 mm 处 RF 多图**：
  - `genData/sum/SR0530_1mm_lenient_C1_Combined_Random_Forest_SHAP_Importance.png`
  - `genData/sum/SR0530_1mm_lenient_C1_Combined_Random_Forest_Permutation_Importance.png`
  - `genData/sum/SR0530_1mm_lenient_C1_Combined_Random_Forest_Builtin_Importance.png`
  - `genData/sum/SR0530_1mm_lenient_C1_Combined_Random_Forest_Bootstrap_R2.png`
  - `genData/sum/SR0530_1mm_lenient_C1_Combined_Random_Forest_Observed_vs_Predicted.png`
  - 同样只有 PNG，未统一为 Calibri/PDF。
- **SR0628_B/D 报告**：只输出各报告最佳模型（Robust/Lasso）的 SHAP，未包含 Random Forest 图。

### 6.4 1° 偏心率处线密度 / 角密度与眼轴的关系

- **已存在**：`genData/FIGA/FIGA_1.0deg.pdf`
  - 左图：Linear cone density vs AL
  - 右图：Angular cone density vs AL
  - 含回归线、R²、Slope、P 值。
- **问题**：标题/标签原使用 `1.0 mm`，源码已改为 `1.0°`（需重新运行脚本以生成新图）。

### 6.5 1° 之后线密度随眼轴变化（参考 eLife）

- **已存在**：`genData/FIGA/FIGA_1.5-6.0deg.pdf`
  - 子图 A：1.5–6.0° 各距离线密度 vs AL 叠加
  - 子图 B：1.5–6.0° 各距离角密度 vs AL 叠加
  - 图例用颜色区分不同偏心率。
- **问题**：图例标注原为 `1.5 mm, 2.0 mm, ...`，源码已改为 `1.5°, 2.0°, ...`（需重新运行脚本以生成新图）。

### 6.6 单位统一问题（mm → °）

✅ 以下文件/脚本已完成 mm → ° 的单位统一（源码层面）：“偏心率”单位从 `mm` 改为 `°` 的文件/脚本包括但不限于：

- `genData/FIGA/FIGA_1.0deg.pdf`
- `genData/FIGA/FIGA_1.5-6.0deg.pdf`
- `report/SR0628_E_MLR_Coefficients_1.5_6.0deg.md` 及对应 CSV
- `src/gen_figA.py`
- `src/SR_FigA_MLR_Split_71eyes.py`
- `src/SR0628_E_MLR_Coefficients_1.5_6.0deg.py`

---

## 7. 汇总：待修改清单（按优先级）

1. **单位统一** ✅ 已完成：源码和 MD 报告中的 `mm`（偏心率）已改为 `°`。PDF/CSV 需重新运行脚本生成。
2. **字体统一**：把未使用 Calibri 的图重新生成：
   - SR0627_A 三张图
   - FIGB1
   - FIGA.pdf（旧综合图，如无需要可删除）
   - SR0628_D 中遗留的 Robust/SVM 旧图
3. **Random Forest 图**：按 Calibri + PDF + PNG 标准重新生成并纳入报告。
4. **MLR 系数**：确认使用 SR0628_E 还是运行 `SR_FigA_MLR_Split_71eyes.py` 的 1° 方法；同时把单位改为 `°`。
5. **5°/5.5° 机器学习结果**：若需“好一点儿的 R²”，建议采用 5-fold 结果或允许跨特征组合选择最优模型。
6. **AL vs SER 图**：确认是否需要 AL 为 x 的版本；FIGB1 本身存在但需改字体。
