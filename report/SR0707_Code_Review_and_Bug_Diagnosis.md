# SR0707 代码审查与 group_stratified_kfold Bug 诊断报告

> **日期**：2026-07-07  
> **审查范围**：SR0530 全工程 `src/` 目录（约 45 个脚本）  
> **触发问题**：SR0705_A_FIG_Report 中 10-fold Robust Linear Regression @ 1.5° 的 Observed vs Predicted 散点图出现 (0,0) 数据点  

---

## 一、Bug 诊断：group_stratified_kfold 索引映射错误

### 1.1 现象

在 `report/FIG/SR0628_B/SR0628_B_Scatter_Robust_Linear_Regression_C1_Combined_ALK_1.5mm.png` 中，Observed vs Predicted 散点图出现一个 **(0, 0)** 的数据点——即某个样本的观测值和预测值均为 0。但实际数据中视锥细胞密度不可能为 0，说明该点并非真实预测结果。

### 1.2 根因

问题出在 `src/SR_ML_ALK_10fold_Final_Tuning_Report.py`（及所有复制了同样实现的脚本）中的 `group_stratified_kfold` 函数。

**错误代码**（L230–266，简化）：

```python
def group_stratified_kfold(groups, y_stratify, n_splits=10, random_state=42):
    ...
    group_info = group_info.sample(frac=1, random_state=random_state).reset_index(drop=True)
    # ⇒ group_info 的 Index 变为 [0, 1, 2, ..., 45]
    
    pos_groups = group_info[group_info['y'] == 1].copy().reset_index(drop=True)
    # ⇒ pos_groups 的 Index 变为 [0, 1, 2, ...]（重新编号！）
    neg_groups = group_info[group_info['y'] == 0].copy().reset_index(drop=True)
    # ⇒ neg_groups 的 Index 变为 [0, 1, 2, ...]（重新编号！）
    
    for label_df in [pos_groups, neg_groups]:
        for i, row in label_df.iterrows():
            folds[i % n_splits].append(row.name)   
            # ↑ BUG: row.name 是子集重编号后的索引（0, 1, 2...）
            #   而非原始 group_info 的行号！
    
    for i in range(n_splits):
        test_groups = folds[i]
        test_idx = np.array([idx for g in test_groups 
                             for idx in group_info.loc[g, 'idx']])
        # ↑ 用错误的行号 g 在 group_info 中查找，可能取到错误组的样本
```

**具体错误示例**（46 subjects 的 group_info）：

| group_info 原始行号 | y (myopia) | pos_groups 行号 | neg_groups 行号 |
|:---------------------|:-----------|:----------------|:----------------|
| 0 | 1 (myopia) | 0 | — |
| 1 | 0 (non)    | — | 0 |
| 2 | 1 (myopia) | 1 | — |
| 3 | 0 (non)    | — | 1 |

`neg_groups` 行 0 的 `row.name = 0`。用 `group_info.loc[0]` 取到的是 myopia 组的 subject（原始第 0 行），而非 non-myopia 的第 1 行。**分组被打乱**。

### 1.3 (0,0) 数据的直接成因

在 `SR0628_B_C1_Combined_ALK_Diagnostics.py` 的 `collect_out_of_fold_predictions` 函数（L185–186）：

```python
all_pred = np.empty(len(y))   # ← 未初始化内存
all_true = np.empty(len(y))   # ← 未初始化内存
```

由于索引映射错误，某些样本**永远不会出现在任何一个 test fold** 中，其 `all_pred[vi]` 和 `all_true[vi]` 从未被赋值。在 Windows 上，操作系统将新分配的内存页置零，因此这些位置保持 **(0, 0)**。散点图中的 (0,0) 点即为此类未被覆盖的样本。

### 1.4 影响范围

此 `group_stratified_kfold` 实现（含相同 Bug）存在于 **至少 4 个文件** 中：

| 文件 | 影响 |
|:-----|:-----|
| `src/SR_ML_ALK_10fold_Final_Tuning_Report.py` | 10-fold ALK 最终调优报告（所有模型） |
| `src/SR_ML_hyperparameter_tuning_robust.py` | **★ 当前推荐的重复 CV 稳健调优主脚本** |
| `src/SR_ML_best_model_diagnostics.py` | 最佳模型诊断 |
| `src/SR_ML_C1_Combined_ALK_10fold_tuning_shap.py` | C1 10-fold SHAP 分析 |

以及通过 `sys.path.insert` / `importlib` 间接引用该实现的所有下游脚本（如 `SR0628_B_C1_Combined_ALK_Diagnostics.py`）。

**后果**：所有 GroupKFold 的分层拆分均存在索引偏差，所有 R² / RMSE / MAPE 指标均受影响，历史最佳结论（"C1_Combined_ALK + ElasticNet @ 1.5 mm, R²=0.395"）也需要重新验证。

### 1.5 修复方案

**修复前（错误）**：

```python
pos_groups = group_info[group_info['y'] == 1].copy().reset_index(drop=True)
neg_groups = group_info[group_info['y'] == 0].copy().reset_index(drop=True)

folds = [[] for _ in range(n_splits)]
for label_df in [pos_groups, neg_groups]:
    for i, row in label_df.iterrows():
        folds[i % n_splits].append(row.name)
```

**修复后（正确）**：

```python
pos_groups = group_info[group_info['y'] == 1]  # 保留原始索引
neg_groups = group_info[group_info['y'] == 0]  # 保留原始索引

folds = [[] for _ in range(n_splits)]
for label_df in [pos_groups, neg_groups]:
    for i, (orig_idx, row) in enumerate(label_df.iterrows()):
        folds[i % n_splits].append(orig_idx)    # 使用原始 group_info 的行号
```

---

## 二、代码审查：工程级问题

### 2.1 严重问题：大规模代码重复（DRY 原则违反）

| 函数 | 在 `src/` 中的重复次数 |
|:-----|:-----------------------|
| `load_subject_mapping` | **20 次** |
| `aggregate_distance` | 10+ 次 |
| `fill_na` | 10+ 次 |
| `load_distance_data` | 10+ 次 |
| `group_stratified_kfold` | 4+ 次 |
| `calc_r2_marginal_conditional` | 3 次 |

**所有副本实现完全相同或近乎相同**。这意味着：
- 修一个 Bug（如 `group_stratified_kfold`）需要改 N 个文件
- 极易出现不同步（如 `aggregate_distance` 的 `min_quadrants` 参数仅在部分文件中存在）

**建议**：将共享功能抽取到 `src/common.py`，所有脚本从此导入。

### 2.2 数据预处理不一致

`SR_LMM_revised.py::aggregate_distance` 有 `min_quadrants` 参数（支持 ≥1 / ≥4），但 `SR_ML_hyperparameter_tuning_robust.py::aggregate_distance` 硬编码为 `>= 1`。LMM 和 ML 在 strict 模式下的数据筛选逻辑可能不一致。

### 2.3 历史脚本未清理

以下脚本在 `PORTING_GUIDE.md` 中被标记为"可选，历史"但仍保留在 `src/` 中：

- `SR_ML_hyperparameter_tuning.py`（基线）
- `SR_ML_hyperparameter_tuning_with_K.py`
- `SR_ML_hyperparameter_tuning_with_ALK.py`
- `SR_ML_hyperparameter_tuning_with_local_features.py`

这些文件与当前推荐的主脚本功能重叠，增加混淆和维护负担。建议移至 `src/archive/` 或加 `_DEPRECATED` 前缀。

### 2.4 常量散落

以下常量在多个文件中独立定义：

| 常量 | 独立定义次数 |
|:-----|:------------|
| `RANDOM_STATE = 42` | 15+ |
| `MYOPIA_THRESHOLD = -0.5` | 4+ |
| 参数搜索网格值（SVM C / gamma 等） | 4+ |

**建议**：统一到 `src/config.py`，所有脚本从此导入。

### 2.5 文件命名不一致

- 文件名：`SR_E_LMM_ICC_All_Types.py`
- 内容 docstring / 前缀：`SR0702_A`
- 自动日期前缀：`SR{MMDD}_`

文件名中的 `E` 无法从内容或路径推断含义，建议统一为日期前缀格式。

---

## 三、项目优点

尽管存在上述技术债务，以下方面值得肯定：

1. **统计方法严谨**：使用 GroupKFold（by Subject）防止数据泄漏，重复 CV 降低随机性，t 分布 CI 估计
2. **FDR 校正**：使用 Benjamini-Hochberg 多重比较校正
3. **固定随机种子**：`RANDOM_STATE=42` 保证可复现
4. **CKPT 断点续跑**：长运行任务的中断恢复机制降低了风险
5. **双格式输出**：所有脚本同时输出 CSV（utf-8-sig）和 Markdown 报告
6. **移植文档**：`PORTING_GUIDE.md` 非常详尽，包含完整执行流程和检查清单
7. **matplotlibrc**：统一了全局字体（Calibri）和 PDF 字体类型（Type 42）
8. **数据隐私**：`orgData/` 和 `genData/` 均被 `.gitignore` 排除

---

## 四、改进建议（按优先级）

| 优先级 | 建议 | 预估工作量 | 说明 |
|:-------|:-----|:----------|:-----|
| **P0** | 修复所有 `group_stratified_kfold` 的索引映射 Bug | 30 min | 见 §1.5 修复方案；修复后需完整重跑所有 ML 分析 |
| **P0** | 抽取 `src/common.py`（数据加载、聚合、分层 CV） | 2–3 h | 消除 20+ 处重复，降低未来不一致风险 |
| **P1** | 统一 `aggregate_distance`（加入 `min_quadrants` 参数） | 30 min | 确保 LMM 和 ML 使用一致的数据筛选逻辑 |
| **P1** | 创建 `src/config.py` 集中管理常量和参数网格 | 30 min | 单一真实来源（Single Source of Truth） |
| **P2** | 清理/归档历史脚本到 `src/archive/` | 15 min | 减少混淆 |
| **P2** | 修复命名不一致（如 `SR_E_LMM_ICC_All_Types.py`） | 5 min | 统一为日期前缀格式 |
| **P3** | 添加单元测试（pytest） | 1–2 d | 覆盖数据加载、聚合、分层 CV 拆分等核心函数 |

---

*Generated: 2026-07-07 | 人工 Review + 自动搜索辅助*