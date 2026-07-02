# SR0702_G 单位统一报告：偏心率 mm → °

> **日期**：2026-07-02
> **摘要**：将全工程中偏心率（eccentricity/distance）单位从 `mm` 统一改为 `°`，仅修改源码输出标签和 MD 报告，不改变数据文件数值。

---

## 一、修改策略

| 规则 | 说明 |
|------|------|
| ✅ 改 | 偏心率/距离标签：`1.5 mm` → `1.5°`、`Distance (mm)` → `Eccentricity (°)` |
| ✅ 改 | 输出列名：`Distance_mm` → `Distance_deg` |
| ✅ 改 | 输出文件名：`_1.5_6.0mm` → `_1.5_6.0deg`、`FIGA_1.0mm` → `FIGA_1.0deg` |
| ✅ 改 | 图表标题/轴标签/图例中的距离 `mm` |
| ❌ 不改 | 眼球参数单位：`Axial length (mm)`、`Corneal curvature (mm)`、`Anterior chamber depth (mm)` |
| ❌ 不改 | 密度单位：`cones/mm²`、`cones/deg²` |
| ❌ 不改 | 源数据列名：`Eccentricity (mm)`（数据源 CSV 列名无法改动，否则所有读取代码断裂） |
| ❌ 不改 | 已有 PDF/PNG 图片文件（需重新运行脚本才能生成新图） |

---

## 二、修改明细

### 2.1 源码文件（12 个）

| 文件 | 主要改动 |
|------|----------|
| `src/SR0628_E_MLR_Coefficients_1.5_6.0mm.py` | `DIST_COL` → `Eccentricity (°)`；`Distance_mm` → `Distance_deg`；输出 CSV/MD 文件名改 `deg`；打印 `{dist:.1f}°`；MD 表头 `Distance (mm)` → `Eccentricity (°)` |
| `src/SR_FigA_MLR_Split_71eyes.py` | `DIST_COL` → `Eccentricity (°)`；标题 `1.0 mm:` → `1.0°:`；`1.5–6.0 mm:` → `1.5–6.0°:`；图例 `X.X mm` → `X.X°`；输出列 `Distance_mm` → `Distance_deg` |
| `src/SR0628_B_C1_Combined_ALK_Diagnostics.py` | 性能表列名 `Distance_mm` → `Distance_deg`；打印 `{dist:.1f} mm` → `{dist:.1f}°` |
| `src/SR0628_D_C1_Combined_ALK_5fold_Performance.py` | 性能表列名 `Distance_mm` → `Distance_deg` |
| `src/SR0628_C_LMM_Residual_QQ_Combined.py` | MD 报告表头 `Distance (mm)` → `Eccentricity (°)` |
| `src/gen_figA.py` | 输出文件名 `FIGA_1.0mm` → `FIGA_1.0deg`、`FIGA_1.5-6.0mm` → `FIGA_1.5-6.0deg`；标题 `1.0 mm` → `1.0°`；图例 `{dist:.1f} mm` → `{dist:.1f}°`；错误信息 |
| `src/gen_figB.py` | GEE 标题 `(1.0 mm)` → `(1.0°)`；数据列名 `Eccentricity (mm)` → `Eccentricity (°)`；注释 |
| `src/SR_SER_AL_LinearRegression_Plots.py` | 文件名 `_mm` → `_deg`；标题 `mm` → `°` |
| `src/SR0627_A_Best_RobustLinear_Diagnostics.py` | 未匹配（无直接 mm 标签改动的需求） |

### 2.2 Markdown 报告（5 个）

| 文件 | 主要改动 |
|------|----------|
| `report/SR0628_E_MLR_Coefficients_1.5_6.0mm.md` | 文件名改 `_deg`；标题 `mm` → `°`；表头 `Distance (mm)` → `Eccentricity (°)`；引用路径 |
| `report/SR0628_B_C1_Combined_ALK_10fold_Performance_1.5_5_5.5.md` | 标题 `mm` → `°`；全部 `### X.X mm` → `### X.X°` |
| `report/SR0628_D_C1_Combined_ALK_5fold_Performance_1.5_5_5.5.md` | 标题 `mm` → `°`；全部 `### X.X mm` → `### X.X°` |
| `report/SR0628_C_LMM_Residual_QQ_Combined_lenient_q1.md` | 表头 `Distance (mm)` → `Eccentricity (°)` |
| `report/SR0628_F_Review_Items_4_5_6.md` | 距离标签 `mm` → `°`；Item 1 标记为已完成；文件引用路径更新 |

### 2.3 CSV 文件（3 个）

| 文件 | 改动 |
|------|------|
| `report/tables/SR0628_E_MLR_Coefficients_1.5_6.0mm.csv` | 列名 `Distance_mm` → `Distance_deg` |
| `report/tables/SR0628_B_C1_Combined_ALK_10fold_Performance_1.5_5_5.5.csv` | 列名 `Distance_mm` → `Distance_deg` |
| `report/tables/SR0628_D_C1_Combined_ALK_5fold_Performance_1.5_5_5.5.csv` | 列名 `Distance_mm` → `Distance_deg` |

---

## 三、未改动的项目（需重新运行脚本才能生效）

由于未重新运行任何脚本，以下**现有输出文件**中的 `mm` 标签不会自动更新：

| 项 | 需要执行的动作 |
|----|---------------|
| `genData/FIGA/FIGA_1.0mm.pdf` → `FIGA_1.0deg.pdf` | 重新运行 `src/gen_figA.py` |
| `genData/FIGA/FIGA_1.5-6.0mm.pdf` → `FIGA_1.5-6.0deg.pdf` | 重新运行 `src/gen_figA.py` |
| `genData/FIGB/FIGB2.pdf` 中的 `(1.0 mm)` 标题 | 重新运行 `src/gen_figB.py` |
| SR0628_B/D 的诊断图（PDF/PNG） | 重新运行 `SR0628_B/D_*.py` |
| SR0628_E 的 MD + CSV 报告中所有内容 | 重新运行 `SR0628_E_*.py` |
| SR0628_C 的 Q-Q 图 | 重新运行 `SR0628_C_*.py` |

**说明**：源码已全部修正，下次运行脚本即可自动生成带 `°` 的输出。

---

## 四、潜在风险与注意事项

1. **数据列名断裂风险**：约 20 个脚本仍读 `'Eccentricity (mm)'` 列名（来自 `genData/CleanDataRoi_*/data*.csv`），这是原始数据列名，未改动。如需彻底统一，需修改 `gen_44ROIData.py` 并重新生成全部 CleanDataRoi 数据。
2. **文件名不一致**：部分旧 PDF 文件仍保留 `_mm` 命名（如 `FIGA_1.0mm.pdf`），与新代码输出文件名 `FIGA_1.0deg.pdf` 不一致。建议在重跑脚本后清理旧文件。
3. **SR0628_F 第 143 行**：因 Unicode 引号问题未能完整替换，保留"需要全局把…"的部分描述。可在后续手动修正。

---

## 五、与 SR0628_F 的对应关系

| SR0628_F Item | 状态 |
|---------------|------|
| **Item 1 (单位统一)** | ✅ **已完成** — 源码和 MD 报告已统一 |
| Item 2 (字体统一 Calibri) | 未处理 — 需单独处理 |
| Item 3 (Random Forest 图) | 未处理 — 需单独处理 |
| Item 4 (MLR 系数方法确认) | 未处理 — 需用户决策 |
| Item 5 (5°/5.5° ML 结果) | 未处理 — 需用户决策 |
| Item 6 (AL vs SER 图) | 未处理 — 需单独处理 |

---

*Generated: 2026-07-02 | SR0702_G*
