# SR0530 项目移植与复现指南

> 本文档用于把整个工程移植到另一台电脑并重新运行。记录：项目目标、目录结构、依赖、数据流、执行顺序、关键脚本、当前结论与注意事项。

---

## 1. 项目目标

利用 69–71 眼（约 44–46 名受试者）的 AOSLO 视锥细胞密度数据，结合眼球形态参数（AL、ACD、SE、K、AL/K 等），通过**线性混合模型（LMM）**与**机器学习回归模型**，研究局部视锥细胞密度在不同偏心距（1.0–6.0 mm）下的统计关联与可预测性。

---

## 2. 推荐运行环境

| 项目 | 版本/说明 |
|------|----------|
| OS | Windows 10/11（当前在 Git Bash 下开发）或 Linux/macOS（路径需调整） |
| Python | **3.13.5**（已在 Anaconda 环境 `D:\conda\python` 验证） |
| 包管理 | `pip` 或 `conda` |

### 2.1 创建环境（conda 示例）

```bash
# 建议先安装 Anaconda/Miniconda
conda create -n sr0530 python=3.13.5 -y
conda activate sr0530
pip install -r requirements.txt
```

### 2.2 核心依赖

见 `requirements.txt`，主要包括：

- `numpy`, `pandas`, `scipy`
- `matplotlib`, `seaborn`
- `scikit-learn`
- `xgboost`
- `shap`
- `statsmodels`（含 `patsy`）

---

## 3. 目录结构

```
SR0530/
├── orgData/                        # 原始数据（需保留或重新生成）
│   ├── Normal/                     # 正常眼 CSV（单患者 44 ROI 表）
│   ├── srx-ao-slo/                 # 患者 CSV（单患者 44 ROI 表）
│   ├── AxialLength/                # 眼轴长度等临床参数 CSV
│   ├── orgData.csv                 # 由 DataRead.py 生成的原始宽表
│   └── orgDataWithAng.csv          # 由 DataCheck.py 加入角密度后的宽表
├── genData/                        # 生成数据
│   ├── CleanData/                  # 早期中间数据
│   ├── CleanDataRoi/               # 早期 44 ROI 数据
│   ├── CleanDataRoi_strict/        # 严格模式 44 ROI（69 眼）
│   ├── CleanDataRoi_lenient/       # 宽松模式 44 ROI（71 眼）★ 当前主流程
│   ├── sum/                        # 汇总 CSV、映射表、图像
│   └── FIGA / FIGB / distance_datasets / sum / ...
├── src/                            # 全部 Python 脚本
│   ├── DataRead.py                 # 原始数据读取 → orgData.csv
│   ├── DataCheck.py                # 计算角密度 → orgDataWithAng.csv + 11距离数据
│   ├── cal_ACD.py                  # RMF / 角密度光学计算函数
│   ├── gen_44ROIData.py            # 从 orgDataWithAng.csv 生成 strict/lenient 44 ROI
│   ├── SR_LMM_revised.py           # LMM 分析
│   ├── SR_ML_hyperparameter_tuning.py           # 基线 ML 调优
│   ├── SR_ML_hyperparameter_tuning_with_K.py    # 加入 K
│   ├── SR_ML_hyperparameter_tuning_with_ALK.py  # 加入 AL/K
│   ├── SR_ML_hyperparameter_tuning_with_local_features.py  # 加入局部结构特征
│   ├── SR_ML_hyperparameter_tuning_robust.py    # 重复 CV 稳健调优 ★ 当前推荐
│   ├── SR_ML_repeated_cv.py        # 重复 CV 诊断
│   ├── SR_ML_learning_curves_and_shap.py        # 学习曲线 + SHAP
│   ├── SR_ML_cv_shap.py            # Cross-validated SHAP (Method B)
│   ├── SR_ML_best_model_diagnostics.py          # 最佳模型诊断
│   ├── gen_lenient_K_summary_report.py          # 生成 +K 总结报告
│   ├── gen_lenient_ALK_summary_report.py        # 生成 AL/K 总结报告
│   └── ...（探索/备用脚本）
├── report/                         # Markdown 报告 + FIG/ 图片
├── requirements.txt                # Python 依赖（本文件生成）
└── PORTING_GUIDE.md                # 本文件
```

### 3.1 哪些目录必须带走？

- **必须**：`src/`, `orgData/`, `requirements.txt`
- **建议一起带走**：`genData/CleanDataRoi_strict/`, `genData/CleanDataRoi_lenient/`, `genData/sum/` 中的映射表（`Eye_to_Subject_Mapping*.csv`），因为这些是主分析脚本的直接输入。
- **可重新生成**：`genData/sum/` 中的结果 CSV、PNG、`report/` 中的报告与 FIG/。
- **大文件**：`genData/CleanData.zip` 等压缩包可酌情取舍。

---

## 4. 标准执行流程（从头复现）

以下顺序假设原始 CSV 已放在 `orgData/` 下。

### Step 0：准备环境

```bash
conda activate sr0530
cd /path/to/SR0530
```

### Step 1：读取原始病历 → `orgData/orgData.csv`

```bash
python src/DataRead.py
```

- **输入**：`orgData/Normal/*.csv`, `orgData/srx-ao-slo/*.csv`, `orgData/AxialLength/*.csv`
- **输出**：`orgData/orgData.csv`, `genData/sum/merge_exclusion_log.csv`

### Step 2：计算角密度 → `orgData/orgDataWithAng.csv`

```bash
python src/DataCheck.py
```

- **输入**：`orgData/orgData.csv`
- **输出**：`orgData/orgDataWithAng.csv`，以及 `genData/CleanData/` 下的 11 距离 data0.csv–data10.csv（当前未被主分析直接读取，仅作备用）
- **核心函数**：`cal_ACD.py::add_angular_density()`，基于 RMF 光学追迹。

### Step 3：生成 44 ROI 数据集（strict / lenient）

```bash
python src/gen_44ROIData.py
```

- **输入**：`orgData/orgDataWithAng.csv`
- **输出**：
  - `genData/CleanDataRoi_strict/data1.csv` … `data44.csv`（69 眼）
  - `genData/CleanDataRoi_lenient/data1.csv` … `data44.csv`（71 眼）
  - `genData/sum/Eye_to_Subject_Mapping_strict.csv`
  - `genData/sum/Eye_to_Subject_Mapping_lenient.csv`

### Step 4：LMM 分析

```bash
python src/SR_LMM_revised.py
```

- **输入**：`genData/CleanDataRoi_*`
- **输出**：`report/SR0530_LMM_Revised_*_q1plus_Report.md` 及对应图片

### Step 5：ML 超参数寻优

**基线（可选，历史）**：

```bash
python src/SR_ML_hyperparameter_tuning.py
```

**加入 K（可选，历史）**：

```bash
python src/SR_ML_hyperparameter_tuning_with_K.py
```

**加入 AL/K（可选，历史）**：

```bash
python src/SR_ML_hyperparameter_tuning_with_ALK.py
```

**当前推荐：重复 CV 稳健寻优（覆盖 1.0–6.0 mm）**：

```bash
python src/SR_ML_hyperparameter_tuning_robust.py
```

- **输入**：`genData/CleanDataRoi_lenient/`
- **输出**：
  - `genData/sum/SR0530_HP_Tuning_Results_robust_repeatedCV_all_distances.csv`
  - `report/SR0530_ML_Hyperparameter_Tuning_robust_repeatedCV_all_distances_Report.md`

### Step 6：诊断与解释（可选）

```bash
python src/SR_ML_repeated_cv.py          # 重复 CV 稳定性诊断
python src/SR_ML_learning_curves_and_shap.py   # 学习曲线 + SHAP
python src/SR_ML_cv_shap.py              # Cross-validated SHAP (Method B)
```

### Step 7：生成总结报告

```bash
python src/gen_lenient_K_summary_report.py
python src/gen_lenient_ALK_summary_report.py
python src/SR_generate_summary_report.py
python src/SR_combined_LMM_ML_report.py
```

- **注意**：部分总结报告脚本读取 `genData/sum/` 下历史 CSV（如 `SR0530_HP_Tuning_Results_q1plus.csv`），若删除了中间 CSV 可能报错。

---

## 5. 关键脚本速查表

| 脚本 | 作用 | 主要输入 | 主要输出 |
|------|------|---------|---------|
| `DataRead.py` | 合并临床 CSV 与 AOSLO 44 ROI 原始表 | `orgData/Normal/`, `srx-ao-slo/`, `AxialLength/` | `orgData/orgData.csv` |
| `cal_ACD.py` | RMF 光学追迹、角密度计算 | AL, K, ACD | 被 `DataCheck.py` 调用 |
| `DataCheck.py` | 清洗、计算角密度、生成 11 距离数据 | `orgData/orgData.csv` | `orgData/orgDataWithAng.csv`, `genData/CleanData/data*.csv` |
| `gen_44ROIData.py` | 生成 strict/lenient 44 ROI 数据集 | `orgData/orgDataWithAng.csv` | `genData/CleanDataRoi_*`, `Eye_to_Subject_Mapping*.csv` |
| `SR_LMM_revised.py` | 线性混合模型（LMM）统计关联分析 | `genData/CleanDataRoi_*` | `report/SR0530_LMM_Revised_*_Report.md` |
| `SR_ML_hyperparameter_tuning.py` | 基线 ML 调优 | `genData/CleanDataRoi_*` | `genData/sum/SR0530_HP_Tuning_Results_q1plus.csv`, 报告 |
| `SR_ML_hyperparameter_tuning_with_K.py` | 加入角膜曲率 K | `genData/CleanDataRoi_*` | `SR0530_HP_Tuning_Results_q1plus_K.csv` |
| `SR_ML_hyperparameter_tuning_with_ALK.py` | 加入 AL/K | `genData/CleanDataRoi_lenient` | `SR0530_HP_Tuning_Results_lenient_ALK.csv` |
| `SR_ML_hyperparameter_tuning_with_local_features.py` | 加入局部结构特征 | `genData/CleanDataRoi_*` | 对应报告与 CSV |
| `SR_ML_hyperparameter_tuning_robust.py` | ★ 重复 CV 稳健调优 | `genData/CleanDataRoi_lenient` | `SR0530_ML_Hyperparameter_Tuning_robust_repeatedCV_all_distances_Report.md` |
| `SR_ML_repeated_cv.py` | 重复 CV 稳定性诊断 | `genData/CleanDataRoi_lenient` | `report/SR0530_Repeated_CV_Report.md` |
| `SR_ML_learning_curves_and_shap.py` | 学习曲线 + SHAP 过拟合评估 | `genData/sum/` 中已有结果 | `report/SR0530_Learning_Curves_SHAP_Report.md` |
| `SR_ML_cv_shap.py` | Cross-validated SHAP (Method B) | `genData/sum/` 中已有结果 | `report/SR0530_CV_SHAP_Report.md` |
| `gen_lenient_K_summary_report.py` | +K 总结报告 | `genData/sum/SR0530_HP_Tuning_Results_q1plus_K.csv` | `report/SR0530_ML_Summary_Lenient_with_K_Report.md` |
| `gen_lenient_ALK_summary_report.py` | AL/K 总结报告 | 多个历史 CSV | `report/SR0530_ML_Summary_Lenient_with_ALK_Report.md` |
| `SR_generate_summary_report.py` | 综合总结 | LMM、ML、诊断结果 | `report/SR0530_Final_Summary_Report.md` |
| `SR_combined_LMM_ML_report.py` | LMM + ML 联合筛查图 | LMM 与 ML 结果 | `report/SR0530_Combined_LMM_ML_q1plus_Report.md` |

---

## 6. 当前最可靠的结论（截至 2026-06-11）

> 基于 **5 repeats × 5-fold GroupKFold** 重复交叉验证，结果显著比单次 5-fold CV 保守。

- **最佳稳健模型**：
  - **方案**：`C1_Combined_ALK`（SE + AL + Age + Gender + AL/K）
  - **模型**：`ElasticNet`
  - **最佳距离**：**1.5 mm**
  - **Mean Test R²**：**0.395** [95% CI: 0.274, 0.515]
  - **参数**：`alpha=1.0`, `l1_ratio=0.7`

- **替代稳健模型**：
  - `A2_Biomechanical_K_ALK + ElasticNet` @ 1.5 mm，R² = 0.393 [0.279, 0.508]
  - `C1_Combined_K + ElasticNet` @ 1.5 mm，R² = 0.368 [0.237, 0.498]

- **历史单次 CV 的 0.612 已被修正为高估**，相关总结报告已添加 `⚠️ 重要稳健性修正说明`。

完整结果见：

```
report/SR0530_ML_Hyperparameter_Tuning_robust_repeatedCV_all_distances_Report.md
```

---

## 7. 注意事项与常见问题

1. **路径**：脚本使用 `BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))` 自动定位项目根目录，因此必须从项目根目录运行，或保持 `src/` 与 `orgData/`、`genData/` 的相对位置不变。

2. **编码**：输出 CSV 多为 `utf-8-sig`（带 BOM），方便 Excel 打开；读取时 `pd.read_csv()` 一般能自动处理。

3. **运行时间**：
   - `SR_ML_hyperparameter_tuning_robust.py` 运行最久（约数小时，取决于 CPU），因为它对 11 个距离 × 16 个方案 × 6 个模型 × 15 组参数 × 5 repeats × 5-fold 进行训练。
   - 可通过修改脚本内 `N_ITER`、`N_REPEATS`、`N_SPLITS`、`DISTANCES` 来加速测试。

4. **随机性**：所有脚本固定 `RANDOM_STATE = 42`，结果可复现。但 `n_jobs=1` 的 RF/XGB 在跨平台时仍可能有微小差异。

5. **SHAP 警告**：`shap` 在部分 sklearn/NumPy 版本组合下会发出弃用警告，不影响结果。

6. **`Strict` vs `Lenient`**：
   - `strict`：某眼任意 ROI 角密度 > 7000 或血管占比 > 0.25 则剔除该眼（69 眼）。
   - `lenient`：放宽到 ≥1 象限可用（71 眼）。当前主分析使用 **lenient**。

7. **数据隐私**：`orgData/` 包含患者信息，移植时请确保符合数据合规要求，不要上传到公开仓库。

---

## 8. 移植检查清单

- [ ] 安装 Python 3.13（或兼容版本）与 conda/pip
- [ ] `pip install -r requirements.txt`
- [ ] 复制 `src/`、`orgData/`、`genData/CleanDataRoi_*` 到新电脑
- [ ] 复制 `genData/sum/Eye_to_Subject_Mapping*.csv`（若不想重新生成 44 ROI 数据）
- [ ] 在项目根目录运行 `python src/SR_ML_hyperparameter_tuning_robust.py`
- [ ] 检查输出 `report/SR0530_ML_Hyperparameter_Tuning_robust_repeatedCV_all_distances_Report.md`

---

## 9. 联系人 / 维护

- 本指南由 Kimi Code CLI 根据当前代码与数据状态自动生成。
- 若后续新增脚本或修改数据流，请同步更新 `PORTING_GUIDE.md` 与 `requirements.txt`。
