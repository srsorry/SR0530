# SR0702_H 字体统一报告：全部图表 PDF 字体改为 Calibri

> **日期**：2026-07-02
> **摘要**：修复 3 个字体 bug，重新运行 6 个图表生成脚本，确保所有 PDF 使用 Calibri + Type 42 TrueType（AI 可编辑）。

---

## 一、发现的字体 Bug

| # | 文件 | Bug | 影响 |
|---|------|-----|------|
| 1 | `src/SR_FigA_MLR_Split_71eyes.py:62` | `font.sans-serif` 覆盖掉了 Calibri（只留 SimHei/DejaVu Sans） | 该脚本生成的 PDF 会使用 DejaVu Sans 而非 Calibri |
| 2 | `src/gen_figB.py:104` | `sns.set_theme()` 在 `plt.rcParams` 之后调用，将字体重置为 seaborn 默认（Arial） | FIGB1.pdf 使用了 Arial 字体 |
| 3 | `src/analyze_cleaned_data.py:22` | 额外用 `matplotlib.rcParams` 覆盖字体为 `['SimHei', 'DejaVu Sans']` | 该旧脚本输出非 Calibri |

### 修复方案

| Bug | 修复 |
|-----|------|
| 1 | 将 `['SimHei', ...]` 改回 `['Calibri', 'SimHei', ...]` |
| 2 | 在 `sns.set_theme()` 之后重新设置 `plt.rcParams['font.sans-serif']` 为 Calibri 系列 |
| 3 | 注释掉覆盖语句 |

---

## 二、重新运行的脚本

| 脚本 | 生成内容 | 输出文件 |
|------|----------|----------|
| `src/gen_figA.py` | FIGA 图（1° 单独 + 1.5–6° 合并） | `genData/FIGA/FIGA_1.0deg.pdf`、`FIGA_1.5-6.0deg.pdf` |
| `src/gen_figB.py` | SE vs AL 散点 + GEE 森林图 | `genData/FIGB/FIGB1.pdf`、`FIGB2.pdf` |
| `src/SR0628_C_LMM_Residual_QQ_Combined.py` | LMM 残差 Q-Q 合并图 | `report/FIG/SR0628_C/*.pdf` |
| `src/SR0628_B_C1_Combined_ALK_Diagnostics.py` | 10-fold 诊断图（散点/SHAP/QQ）+ MD 报告 + CSV | `report/FIG/SR0628_B/*.pdf` |
| `src/SR0628_D_C1_Combined_ALK_5fold_Performance.py` | 5-fold 诊断图（散点/SHAP/QQ）+ MD 报告 + CSV | `report/FIG/SR0628_D/*.pdf` |
| `src/SR0628_E_MLR_Coefficients_1.5_6.0mm.py` | MLR 系数表 CSV + MD 报告 | `report/tables/SR0628_E_*.csv`、MD 报告 |

---

## 三、字体对比（修改前 vs 修改后）

| 文件 | 修改前字体 | 修改后字体 | 修改方式 |
|------|-----------|-----------|----------|
| `FIGA_1.0deg.pdf` | Calibri | **Calibri** ✅ | 重跑（原已正确） |
| `FIGA_1.5-6.0deg.pdf` | Calibri | **Calibri** ✅ | 重跑（原已正确） |
| `FIGB1.pdf` | **Arial** ❌ | **Calibri** ✅ | Bug 修复 + 重跑 |
| `FIGB2.pdf` | Calibri | **Calibri** ✅ | 重跑（原已正确） |
| `SR0628_B/*.pdf` (3 张) | Calibri | **Calibri** ✅ | 重跑 + mm→° 标签更新 |
| `SR0628_C/*.pdf` | Calibri | **Calibri** ✅ | 重跑 + mm→° 标签更新 |
| `SR0628_D/*.pdf` (3 张 Lasso) | Calibri | **Calibri** ✅ | 重跑 + mm→° 标签更新 |

---

## 四、未重新生成的图表

| 文件 | 原因 | 当前字体 | 建议 |
|------|------|----------|------|
| `SR0627_A_*.pdf` (3 张) | DejaVuSans | 旧图，需修改 `SR0627_A_*.py` 后重跑 | 下次单独处理 |
| `SR0628_D` 中 Robust/SVM 旧图 | DejaVuSans | 遗留文件，应清理 | 删除或重跑 |
| `FIGA.pdf`（旧综合图） | DejaVuSans | 已被 split 版本替代 | 可删除 |

---

## 五、PDF 可编辑性确认

所有重新生成的 PDF 均设置了：
```python
plt.rcParams['pdf.fonttype'] = 42  # Type 42 TrueType，AI 可编辑
```
这些 PDF 在 Adobe Illustrator 等工具中可以直接选择/编辑文字。

---

## 六、SR0628_F 对应状态更新

| SR0628_F Item | 状态 |
|---------------|------|
| Item 1 (单位统一 mm→°) | ✅ 已完成 |
| **Item 2 (字体统一 Calibri)** | ✅ **大部分已完成**（FIGA/B/C 系列 + SR0628_B/D 诊断图） |
| Item 3 (Random Forest 图) | ⬜ 未处理 |
| Item 4 (MLR 方法确认) | ⬜ 未处理 |
| Item 5 (5°/5.5° ML) | ⬜ 未处理 |
| Item 6 (AL vs SER 图) | ⬜ FIGB1 已修复字体 ✅ |

---

*Generated: 2026-07-02 | SR0702_H*
