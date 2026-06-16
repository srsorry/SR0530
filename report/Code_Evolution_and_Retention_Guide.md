# SR0530 代码脉络与保留建议

> 本文档梳理当前 `src/` 下所有脚本的功能、数据流向、以及本轮修改新增的内容，供决策保留/清理/合并。

---

## 一、整体数据流

```
原始数据 (orgData/)
    ├── cal_ACD.py              → 计算前房深度
    ├── DataRead.py             → 读取宽表
    ├── DataCheck.py            → 质量检查、异常值标记
    └── gen_44ROIData.py        → 生成 44 个 ROI 文件 (strict/lenient)
                                      ↓
                              genData/CleanDataRoi_*/
                                      ↓
    ┌─────────────────────────┬─────────────────────────┐
    │      LMM 分析流          │       ML 分析流          │
    │                         │                         │
    │  SR_LMM_revised.py      │  SR_ML_hyperparameter_  │
    │  (修复版，支持 q4/q1plus)│   tuning.py             │
    │                         │  (粗粒度参数寻优)        │
    │                         │        ↓                │
    │                         │  SR_ML_1mm_final_       │
    │                         │   tuning.py             │
    │                         │  (1.0 mm 细调+特征重要)  │
    └──────────┬──────────────┴──────────┬──────────────┘
               │                         │
               └──────────┬──────────────┘
                          ↓
              SR_combined_LMM_ML_report.py
              (LMM + ML 合成报告)
```

---

## 二、脚本分类与功能

### 1. 数据预处理层

| 脚本 | 功能 | 本轮是否修改 | 备注 |
|------|------|------------|------|
| `cal_ACD.py` | 计算前房深度 | 否 | 早期工具脚本 |
| `DataRead.py` | 读取原始宽表数据 | 否 | 预处理 |
| `DataCheck.py` | 数据质量检查、异常值标记 | 否 | 预处理 |
| `gen_44ROIData.py` | 生成 44 个 ROI 独立 CSV，含 strict/lenient 两套黑名单 | 否（但结果驱动了后续分析） | **核心预处理脚本**，必须保留 |
| `compare_roi_datasets.py` | 比较不同 ROI 数据集差异 | 否 | 辅助检查 |
| `analyze_cleaned_data.py` | 清洗后数据描述统计 | 否 | 早期探索 |
| `analyze_roi_effects.py` | ROI 效应分析 | 否 | 早期探索 |
| `gen_figA.py` | 生成图 A | 否 | 作图 |
| `gen_figB.py` | 生成图 B | 否 | 作图 |

### 2. LMM 分析层

| 脚本 | 功能 | 本轮是否修改 | 备注 |
|------|------|------------|------|
| `SR_LMM_analysis.py` | 基于 `orgData.csv` 的 LMM | 否 | **旧版**，从原始宽表构建长数据 |
| `SR_LMM_kimi_v2.py` | 另一版 LMM | 否 | 旧版变体 |
| `SR_LMM_V3.0.py` | V3.0 LMM | 否 | 旧版变体 |
| `SR_LMM_revised.py` | **修复版 LMM**，使用 `CleanDataRoi`，与 ML 数据一致，支持 q4/q1plus | **是（本轮修改）** | **建议保留为主力 LMM 脚本** |

### 3. ML 分析层

| 脚本 | 功能 | 本轮是否修改 | 备注 |
|------|------|------------|------|
| `SR_ML_hyperparameter_tuning.py` | 7 模型 × 4 方案 × 11 距离的粗粒度随机寻优 | **是（本轮修改）** | 新增 `min_quadrants` 支持，当前默认 q1plus。建议保留并参数化 |
| `SR_ML_fine_tuning.py` | 对 top 12 配置做精细寻优 + 稳定性评估 | 否 | 基于 q4 coarse 结果，与本轮 1.0 mm 分析口径不完全一致 |
| `SR_ML_1mm_final_tuning.py` | **1.0 mm q1plus 精细寻优 + 特征重要性 + Bootstrap 稳定性** | **是（本轮新增）** | **建议保留**，是最终模型依据 |
| `SR_ML_V3.0.py` | V3.0 ML 分析 | 否 | 旧版 |
| `SR_ML_kimi_v2.py` | 另一版 ML | 否 | 旧版 |
| `SR_ML_subject_aware.py` | subject-aware ML | 否 | 旧版 |
| `SR_ML_stratified_analysis.py` | 分层分析 | 否 | 旧版 |
| `SR_ML_task2.py` | task2 ML | 否 | 旧版 |
| `SR_integrated_analysis.py` | 整合 V6.0 ML 方法（含 SHAP） | 否 | 旧版，依赖 shap |
| `SR_ML_final_report.py` | 基于 3.0 mm 的最终推荐报告 | 否 | **结果已过时**（推荐 3.0 mm，而最新结果支持 1.0 mm） |
| `SR_generate_comprehensive_report.py` | 综合报告生成 | 否 | 结果口径需核对 |

### 4. 报告层

| 脚本 | 功能 | 本轮是否修改 | 备注 |
|------|------|------------|------|
| `SR_combined_LMM_ML_report.py` | 合成 LMM q1plus + ML q1plus 报告 | **是（本轮新增）** | **建议保留** |

### 5. 测试/工具

| 脚本 | 功能 | 备注 |
|------|------|------|
| `test.py` | z-score 标准化测试 | 早期工具 |

---

## 三、本轮修改/新增脉络

### 1. 发现的问题

- 原始 LMM 脚本使用 `orgData.csv` 或旧数据路径，与 ML 层使用的 `CleanDataRoi` 数据不一致。
- 原始 ML 参数寻优使用 **inner merge（≥4 象限）**，导致远周边样本量骤降（6.0 mm 仅 39 眼）。
- LMM 和 ML 结果分散在不同报告中，没有统一口径的合成报告。
- 旧版 `SR_ML_final_report.py` 推荐 3.0 mm，与最新 LMM/ML 共同支持的 1.0 mm 不一致。

### 2. 修改内容

#### (1) `SR_LMM_revised.py`
- 新增 `min_quadrants` 参数到 `aggregate_distance()`：
  - `min_quadrants=4`：传统 inner merge（不放宽）
  - `min_quadrants=1`：outer merge，≥1 象限可用即纳入
- `main()` 中自动跑 q4 和 q1plus 两套模式
- 输出文件带 `_q4` / `_q1plus` 后缀

#### (2) `SR_ML_hyperparameter_tuning.py`
- 同样新增 `min_quadrants` 参数
- 当前 `MIN_QUADRANTS = 1`，输出 `_q1plus` 结果
- 保存文件带 `_q1plus` 后缀，避免覆盖原 q4 结果

#### (3) `SR_combined_LMM_ML_report.py`（新增）
- 读取 LMM q1plus + ML q1plus 结果
- 生成合成 Figure 1 和 Overlay 图
- 输出统一 Markdown 报告

#### (4) `SR_ML_1mm_final_tuning.py`（新增）
- 读取 q1plus coarse 结果中 1.0 mm 的 top 12 配置
- 对每个配置做 50 次精细随机寻优
- 50 次 Bootstrap 稳定性评估
- Permutation + Builtin 特征重要性
- 生成观测-预测图、Bootstrap 分布图、特征重要性图

### 3. 当前已生成的关键结果文件

```
genData/sum/
├── SR0530_LMM_Revised_*_q4_Results.csv
├── SR0530_LMM_Revised_*_q1plus_Results.csv
├── SR0530_HP_Tuning_Results_q1plus.csv
├── SR0530_1mm_Fine_Tuning_Results.csv
├── SR0530_1mm_Feature_Importance.csv
└── ...（大量图表）

report/
├── SR0530_LMM_Revised_*_q4_Report.md
├── SR0530_LMM_Revised_*_q1plus_Report.md
├── SR0530_ML_Hyperparameter_Tuning_q1plus_Report.md
├── SR0530_Combined_LMM_ML_q1plus_Report.md
└── SR0530_1mm_Final_Tuning_and_Feature_Importance_Report.md
```

---

## 四、存在的问题与冗余

### 1. 多版本重复

- **LMM 有 4 个版本**：`SR_LMM_analysis.py`、`SR_LMM_kimi_v2.py`、`SR_LMM_V3.0.py`、`SR_LMM_revised.py`
  - 建议：保留 `SR_LMM_revised.py`，其余归档或删除。
- **ML 有 7+ 个版本**：V3.0、kimi_v2、subject_aware、stratified、task2、integrated、hyperparameter_tuning、fine_tuning、1mm_final_tuning
  - 建议：保留 `SR_ML_hyperparameter_tuning.py` 和 `SR_ML_1mm_final_tuning.py`，其余归档或删除。

### 2. 模式切换不灵活

- `SR_ML_hyperparameter_tuning.py` 中 `MIN_QUADRANTS = 1` 是硬编码常量。若需要同时生成 q4 和 q1plus，需改代码再跑。
- 建议：改为命令行参数或 `if __name__ == '__main__'` 中循环两种模式。

### 3. 特征重要性尺度问题（已修正）

- 原始 `SR_ML_1mm_final_tuning.py` 生成的报告中，直接对不同方法的重要性原始值做平均，导致 ElasticNet/Ridge 系数（数百）dominate Random Forest 重要性（0-1）。
- 已修正：对每个 (模型, 方法) 组内做 [0,1] 归一化后再平均，并生成归一化热图。

### 4. 报告结果不一致

- `SR_ML_final_report.py` 推荐 3.0 mm，本轮最新结果推荐 1.0 mm。
- 建议：若保留 1.0 mm 结论，需更新或弃用旧报告脚本。

### 5. 编码问题

- 部分脚本含 `²` 等 Unicode 字符，在 Windows Git Bash 控制台打印时会报 `'gbk' codec can't encode character`。
- 已在本轮新增脚本中替换为 `^2`。旧脚本若运行时遇到类似问题，需同样处理。

### 6. 依赖问题

- `SR_integrated_analysis.py` 依赖 `shap`，当前环境未安装。
- `SR_ML_1mm_final_tuning.py` 尝试导入 shap，失败则回退到 permutation importance。

---

## 五、保留/清理建议

### 建议保留（形成最终工作流）

| 保留脚本 | 理由 |
|---------|------|
| `gen_44ROIData.py` | 核心预处理 |
| `SR_LMM_revised.py` | 主力 LMM，支持 q4/q1plus，与 ML 数据一致 |
| `SR_ML_hyperparameter_tuning.py` | 主力粗粒度寻优（建议改为参数化模式） |
| `SR_ML_1mm_final_tuning.py` | 1.0 mm 最终模型与特征重要性 |
| `SR_combined_LMM_ML_report.py` | LMM + ML 合成报告 |

### 建议归档/删除

| 脚本 | 理由 |
|------|------|
| `SR_LMM_analysis.py` | 旧版，数据口径不一致 |
| `SR_LMM_kimi_v2.py` | 旧版变体 |
| `SR_LMM_V3.0.py` | 旧版变体 |
| `SR_ML_V3.0.py` | 旧版 |
| `SR_ML_kimi_v2.py` | 旧版 |
| `SR_ML_subject_aware.py` | 旧版 |
| `SR_ML_stratified_analysis.py` | 旧版 |
| `SR_ML_task2.py` | 旧版 |
| `SR_integrated_analysis.py` | 旧版，依赖 shap |
| `SR_ML_final_report.py` | 推荐 3.0 mm，与最新结论冲突 |
| `SR_generate_comprehensive_report.py` | 口径需核对，功能可被合成报告替代 |
| `SR_ML_fine_tuning.py` | 可被 `SR_ML_1mm_final_tuning.py` 替代或合并 |

### 建议合并/重构

1. **统一 `SR_ML_hyperparameter_tuning.py` 的模式切换**
   - 将 `MIN_QUADRANTS` 和 `MODE_LABEL` 改为可通过命令行参数传入
   - 或让 `main()` 同时跑 q4 和 q1plus，保存两套文件

2. **合并 `SR_ML_fine_tuning.py` 与 `SR_ML_1mm_final_tuning.py`**
   - `SR_ML_fine_tuning.py` 针对所有距离的 top 配置
   - `SR_ML_1mm_final_tuning.py` 只针对 1.0 mm，但多了特征重要性
   - 可合并为通用脚本，支持指定距离和是否计算特征重要性

3. **统一报告层**
   - 保留 `SR_combined_LMM_ML_report.py`
   - 删除 `SR_generate_comprehensive_report.py` 和 `SR_ML_final_report.py`

---

## 六、最终推荐的最小可用工作流

如果目标是发表 1.0 mm 靶点论文，最小脚本集合为：

```
gen_44ROIData.py
    ↓
SR_LMM_revised.py              → LMM 结果（q4 作为敏感性分析，q1plus 作为主分析）
SR_ML_hyperparameter_tuning.py → 粗粒度寻优（q1plus）
    ↓
SR_ML_1mm_final_tuning.py      → 1.0 mm 最终模型 + 特征重要性
    ↓
SR_combined_LMM_ML_report.py   → 合成报告
```

---

## 七、待用户决策事项

1. **是否保留 q4（≥4 象限）结果作为敏感性分析？**
   - 是：保留 `SR_LMM_revised.py` 的 q4 输出，但需将 `SR_ML_hyperparameter_tuning.py` 也改为支持 q4
   - 否：仅保留 q1plus，简化结果

2. **最终靶点是 1.0 mm 还是 3.0 mm？**
   - 1.0 mm：保留 `SR_ML_1mm_final_tuning.py`，删除/归档 `SR_ML_final_report.py`
   - 3.0 mm：需要重新跑 3.0 mm 的细调和特征重要性

3. **是否删除旧版 LMM/ML 脚本？**
   - 删除：减少混乱
   - 保留但移入 `src/archive/`：安全但占用空间

4. **是否安装 shap 并启用 SHAP 解释？**
   - 是：可增强特征解释
   - 否：permutation importance 已足够
