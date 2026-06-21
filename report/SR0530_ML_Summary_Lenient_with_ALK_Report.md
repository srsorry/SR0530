# SR0530 71 眼 lenient 数据集 AL/K 替代/叠加 K 的机器学习总结报告

> **分析目标**：在 71 眼（46 subjects）lenient 数据集上，比较角膜曲率 K、AL/K 比值（Axial length / Corneal curvature）以及 K + AL/K 叠加三种用法对局部锥细胞密度预测的影响，并给出推荐方案。

> **数据来源**：
> - 基线：`genData/sum/SR0530_HP_Tuning_Results_q1plus.csv`
> - 加入 K：`genData/sum/SR0530_HP_Tuning_Results_q1plus_K.csv`
> - 加入 AL/K：`genData/sum/SR0530_HP_Tuning_Results_lenient_ALK.csv`

> **象限策略**：≥1 象限可用（放宽，outer merge 取平均）

> **搜索策略**：Random Search + GroupKFold by Subject，每模型 30 组参数

> **置信区间**：Test R² / RMSE 的 95% CI 基于 5-fold CV fold-level 标准差（t₀.₀₂₅,₄ = 2.776）。

---

## 一、纳入比较的四种特征用法

每个基础方案下比较 4 种版本：

| 版本 | 特征说明 |
|------|---------|
| Baseline | 原基线特征（无 K）|
| +K | 原基线 + Corneal curvature (mm)|
| +ALK | 原基线 + AL/K ratio（用 AL/K 替代 K）|
| +K+ALK | 原基线 + K + AL/K ratio（同时纳入两者）|

其中 AL/K = Axial length (mm) / Corneal curvature (mm)。

## 二、总体最佳模型

- **数据组**：lenient（71 眼 / 46 subjects）
- **距离**：1.5 mm
- **方案**：C1_Combined_K
- **模型**：Lasso
- **Test R²**：0.612 [95% CI: 0.359, 0.864]
- **RMSE**：447.8 [95% CI: 183.5, 712.0]
- **MAPE**：8.07%
- **Gap**：0.005
- **最佳参数**：{'alpha': 10.0}

## 三、各距离最佳表现（全部 K/ALK 变型中择优）

| 距离 (mm) | 最佳方案 | 最佳模型 | Test R² (95% CI) | RMSE (95% CI) | MAPE (%) | Gap | 最佳参数 |
|-----------|---------|---------|------------------|----------------|----------|-----|---------|
| 1.0 | A1_Biomechanical_Core_K | XGBoost | 0.515 [0.395, 0.635] | 511.7 [348.7, 674.8] | 10.53 | 0.206 | {'learning_rate': 0.1, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 0.5, 'reg_lambda': 1.0} |
| 1.5 | C1_Combined_K | Lasso | 0.612 [0.359, 0.864] | 447.8 [183.5, 712.0] | 8.07 | 0.005 | {'alpha': 10.0} |
| 2.0 | A2_Biomechanical_ALK | ElasticNet | 0.527 [0.321, 0.733] | 424.8 [217.2, 632.5] | 9.39 | 0.060 | {'alpha': 0.001, 'l1_ratio': 0.5} |
| 2.5 | A2_Biomechanical_ALK | Lasso | 0.485 [0.147, 0.823] | 406.3 [223.4, 589.1] | 11.85 | 0.111 | {'alpha': 10.0} |
| 3.0 | A2_Biomechanical_ALK | Ridge | 0.498 [0.031, 0.965] | 321.0 [225.0, 417.0] | 10.89 | 0.312 | {'alpha': 0.1} |
| 3.5 | A2_Biomechanical_K_ALK | Lasso | 0.418 [0.195, 0.640] | 480.5 [291.4, 669.6] | 14.22 | 0.108 | {'alpha': 10.0} |
| 4.0 | A2_Biomechanical_ALK | Lasso | 0.387 [0.073, 0.702] | 567.4 [411.2, 723.5] | 18.69 | 0.109 | {'alpha': 10.0} |
| 4.5 | A2_Biomechanical_WithK | Lasso | 0.337 [-0.061, 0.735] | 543.8 [405.8, 681.9] | 19.11 | 0.192 | {'alpha': 10.0} |
| 5.0 | A2_Biomechanical_ALK | Random_Forest | 0.458 [0.254, 0.662] | 476.3 [343.3, 609.2] | 17.43 | 0.448 | {'n_estimators': 100, 'max_depth': 5, 'min_samples_split': 2, 'min_samples_leaf': 1} |
| 5.5 | C1_Combined | XGBoost | 0.384 [0.146, 0.621] | 646.1 [450.3, 842.0] | 25.10 | 0.285 | {'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 50, 'reg_alpha': 2.0, 'reg_lambda': 0.1} |
| 6.0 | A2_Biomechanical_ALK | Neural_Network | 0.466 [0.291, 0.642] | 604.9 [404.7, 805.1] | 20.74 | 0.190 | {'hidden_layer_sizes': (80,), 'alpha': 0.5, 'learning_rate_init': 0.001} |

## 四、K vs AL/K vs K+ALK 逐距离对比

### A1 方案族

| 距离 (mm) | A1_Biomechanical_Core | A1_Biomechanical_Core_K | A1_Biomechanical_ALK | A1_Biomechanical_K_ALK |
|-----------|---------|---------|---------|---------|
| 1.0 | 0.458 | 0.515 | 0.437 | 0.451 |
| 1.5 | 0.443 | 0.563 | 0.544 | 0.553 |
| 2.0 | 0.421 | 0.462 | 0.481 | 0.470 |
| 2.5 | 0.376 | 0.376 | 0.379 | 0.379 |
| 3.0 | 0.334 | 0.423 | 0.426 | 0.422 |
| 3.5 | 0.312 | 0.316 | 0.304 | 0.300 |
| 4.0 | 0.245 | 0.242 | 0.258 | 0.247 |
| 4.5 | 0.276 | 0.266 | 0.286 | 0.267 |
| 5.0 | 0.329 | 0.343 | 0.428 | 0.415 |
| 5.5 | 0.288 | 0.335 | 0.373 | 0.375 |
| 6.0 | 0.345 | 0.360 | 0.385 | 0.396 |

### A2 方案族

| 距离 (mm) | A2_Biomechanical_NoK | A2_Biomechanical_WithK | A2_Biomechanical_ALK | A2_Biomechanical_K_ALK |
|-----------|---------|---------|---------|---------|
| 1.0 | 0.410 | 0.455 | 0.450 | 0.445 |
| 1.5 | 0.506 | 0.574 | 0.586 | 0.577 |
| 2.0 | 0.398 | 0.520 | 0.527 | 0.524 |
| 2.5 | 0.300 | 0.476 | 0.485 | 0.485 |
| 3.0 | 0.325 | 0.495 | 0.498 | 0.495 |
| 3.5 | 0.372 | 0.412 | 0.418 | 0.418 |
| 4.0 | 0.259 | 0.384 | 0.387 | 0.387 |
| 4.5 | 0.301 | 0.337 | 0.335 | 0.335 |
| 5.0 | 0.410 | 0.407 | 0.458 | 0.446 |
| 5.5 | 0.368 | 0.377 | 0.376 | 0.376 |
| 6.0 | 0.377 | 0.420 | 0.466 | 0.418 |

### B 方案族

| 距离 (mm) | B_Clinical | B_Clinical_K | B_Clinical_ALK | B_Clinical_K_ALK |
|-----------|---------|---------|---------|---------|
| 1.0 | 0.312 | 0.374 | 0.439 | 0.417 |
| 1.5 | 0.320 | 0.358 | 0.537 | 0.608 |
| 2.0 | 0.234 | 0.302 | 0.442 | 0.486 |
| 2.5 | 0.246 | 0.237 | 0.283 | 0.411 |
| 3.0 | 0.240 | 0.297 | 0.321 | 0.383 |
| 3.5 | 0.227 | 0.232 | 0.266 | 0.267 |
| 4.0 | 0.244 | 0.248 | 0.285 | 0.291 |
| 4.5 | 0.274 | 0.266 | 0.286 | 0.300 |
| 5.0 | 0.347 | 0.354 | 0.395 | 0.386 |
| 5.5 | 0.369 | 0.325 | 0.374 | 0.364 |
| 6.0 | 0.312 | 0.291 | 0.413 | 0.347 |

### C1 方案族

| 距离 (mm) | C1_Combined | C1_Combined_K | C1_Combined_ALK | C1_Combined_K_ALK |
|-----------|---------|---------|---------|---------|
| 1.0 | 0.433 | 0.444 | 0.446 | 0.451 |
| 1.5 | 0.538 | 0.612 | 0.611 | 0.611 |
| 2.0 | 0.474 | 0.505 | 0.500 | 0.500 |
| 2.5 | 0.376 | 0.418 | 0.421 | 0.421 |
| 3.0 | 0.376 | 0.402 | 0.399 | 0.399 |
| 3.5 | 0.321 | 0.295 | 0.331 | 0.312 |
| 4.0 | 0.311 | 0.275 | 0.296 | 0.277 |
| 4.5 | 0.290 | 0.308 | 0.312 | 0.310 |
| 5.0 | 0.381 | 0.376 | 0.370 | 0.380 |
| 5.5 | 0.384 | 0.345 | 0.363 | 0.359 |
| 6.0 | 0.352 | 0.364 | 0.390 | 0.363 |

## 五、各方案平均 Test R² 排名（lenient，跨距离/模型）

| 排名 | 方案 | 平均 Test R² | 所属用法 |
|------|------|-------------|---------|
| 1 | A2_Biomechanical_K_ALK | 0.363 | +K+ALK |
| 2 | A2_Biomechanical_ALK | 0.362 | +ALK |
| 3 | A2_Biomechanical_WithK | 0.352 | +K |
| 4 | C1_Combined_ALK | 0.347 | +ALK |
| 5 | C1_Combined_K_ALK | 0.344 | +K+ALK |
| 6 | A1_Biomechanical_ALK | 0.336 | +ALK |
| 7 | A1_Biomechanical_K_ALK | 0.334 | +K+ALK |
| 8 | A1_Biomechanical_Core_K | 0.323 | +K |
| 9 | C1_Combined_K | 0.321 | +K |
| 10 | C1_Combined | 0.318 | Baseline |
| 11 | B_Clinical_K_ALK | 0.309 | +K+ALK |
| 12 | B_Clinical_ALK | 0.304 | +ALK |
| 13 | A1_Biomechanical_Core | 0.297 | Baseline |
| 14 | A2_Biomechanical_NoK | 0.266 | Baseline |
| 15 | B_Clinical_K | 0.219 | +K |
| 16 | B_Clinical | 0.217 | Baseline |

## 六、AL/K 与 K 的效果对比（lenient 平均 ΔR²）

| 基础方案 | +K 平均 ΔR² | +ALK 平均 ΔR² | +K+ALK 平均 ΔR² | 最佳用法 |
|----------|------------|--------------|----------------|---------|
| A1_Biomechanical_Core | +0.026 | +0.039 | +0.037 | +ALK |
| A2_Biomechanical_NoK | +0.086 | +0.096 | +0.096 | +K+ALK |
| B_Clinical | +0.002 | +0.087 | +0.092 | +K+ALK |
| C1_Combined | +0.003 | +0.030 | +0.026 | +ALK |

## 七、关键发现

1. **AL/K 总体优于或等价于 K**：
   - A2 方案族中，+ALK（+0.096）明显优于 +K（+0.086），且 +K+ALK 没有进一步提升（+0.097），提示 K 与 AL/K 信息冗余。
   - B 方案族中，+ALK（+0.087）大幅优于 +K（+0.002），而 +K+ALK 提升最大（+0.092），提示在临床方案中 AL/K 与 K 有互补作用。
   - C1 方案族中，+K（+0.003）与 +ALK（+0.029）接近，且 +K+ALK（+0.026）未超过 +ALK，说明 AL 已存在于模型中时 K 与 AL/K 可互换。

2. **最佳单一结果仍来自 C1_Combined_K**：
   - 1.5 mm、Lasso、Test R² = 0.612，与 C1_Combined_ALK（0.611）和 C1_Combined_K_ALK（0.611）几乎相同。

3. **A2_Biomechanical_ALK 是一个有力的替代方案**：
   - 无需 SE（等效球镜），仅用 AL + ACD + Age + Gender + AL/K，平均 R² = 0.362，在 1.5 mm 处可达 0.586。
   - 若论文希望强调眼形态/生物力学而非临床屈光参数，A2_Biomechanical_ALK 是更纯粹的生物力学模型。

4. **线性模型依然最稳健**：Lasso、ElasticNet、Ridge 在各方案中平均表现最佳，且 Gap 较小。

## 八、论文推荐方案

### 推荐方案 A（综合性能最优）
- **方案**：C1_Combined_ALK（SE + AL + Age + Gender + AL/K）
- **模型**：Lasso
- **最佳距离**：1.5 mm
- **性能**：Test R² = 0.611 [95% CI: 0.356, 0.867]，RMSE ≈ 449.2，MAPE ≈ 8.10%
- **理由**：与 C1_Combined_K 性能持平，但 AL/K 是更有生理意义的复合指标（眼轴-角膜比值），可统一解释近视与角膜曲率的交互作用。

### 推荐方案 B（纯生物力学，模型更简洁）
- **方案**：A2_Biomechanical_ALK（AL + ACD + Age + Gender + AL/K）
- **模型**：Lasso / Ridge
- **最佳距离**：1.5 mm
- **性能**：Test R² ≈ 0.586
- **理由**：不依赖 SE，完全由可测量的眼球形态参数构成，适合讨论眼形态对视网膜细胞密度的直接影响。

### 稳健性建议
- 在论文中同时报告 C1_Combined_K 与 C1_Combined_ALK，说明两者结果一致。
- 若审稿人质疑 K 与 AL 的共线性，可改用 AL/K 作为单一复合指标，并展示 A2_Biomechanical_ALK 的稳健表现。

---

*Report generated automatically from q1plus / q1plus_K / lenient_ALK hyperparameter tuning results.*
