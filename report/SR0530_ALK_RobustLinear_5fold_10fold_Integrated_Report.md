# SR0530 ALK 方案族 Robust Linear Regression 五折 / 十折寻优整合报告

> **目标**：在 lenient 数据组上，对所有 ALK 变型方案单独使用 Robust Linear Regression（HuberRegressor）进行 5-fold 和 10-fold GroupKFold by Subject 超参数寻优，并与已有的五折全模型结果、十折 C1_Combined_ALK 结果进行整合对比。

> **数据组**：lenient（71 眼 / 46 subjects）

> **模型**：Robust Linear Regression（sklearn HuberRegressor）

> **参数搜索**：epsilon ∈ {1.0, 1.35, 1.5, 2.0, 2.5}，alpha ∈ {0.0001, 0.001, 0.01, 0.1, 1.0}，每配置 30 次随机搜索。

---

## 一、Robust Linear Regression 本次寻优总体最佳配置

- **方案**：A2_Biomechanical_ALK
- **距离**：1.5 mm
- **CV 折数**：5-fold
- **最佳 Test R²**：0.611 [95% CI: 0.473, 0.748]
- **最佳 Test RMSE**：361.0 [95% CI: 237.6, 484.4]
- **Gap**：0.116
- **最佳参数**：{'epsilon': 1.5, 'alpha': 0.001}

## 二、各 ALK 方案 5-fold vs 10-fold 最佳 Test R² 对比

| 距离 (mm) | 方案 | 5-fold R² | 10-fold R² | 5-fold RMSE | 10-fold RMSE | 5-fold 最佳参数 | 10-fold 最佳参数 |
|-----------|------|-----------|------------|-------------|--------------|----------------|------------------|
| 1.0 | A1_Biomechanical_ALK | 0.415 | 0.167 | 535.3 | 562.3 | {'epsilon': 1.5, 'alpha': 0.001} | {'epsilon': 1.5, 'alpha': 0.01} |
| 1.0 | A1_Biomechanical_K_ALK | 0.413 | 0.155 | 536.3 | 565.7 | {'epsilon': 1.5, 'alpha': 0.001} | {'epsilon': 1.5, 'alpha': 0.01} |
| 1.0 | A2_Biomechanical_ALK | 0.427 | 0.241 | 531.5 | 549.8 | {'epsilon': 1.5, 'alpha': 0.001} | {'epsilon': 1.0, 'alpha': 0.001} |
| 1.0 | A2_Biomechanical_K_ALK | 0.425 | 0.232 | 532.2 | 555.7 | {'epsilon': 1.5, 'alpha': 0.001} | {'epsilon': 1.0, 'alpha': 0.001} |
| 1.0 | B_Clinical_ALK | 0.451 | 0.216 | 482.0 | 478.9 | {'epsilon': 2.0, 'alpha': 0.001} | {'epsilon': 2.0, 'alpha': 0.001} |
| 1.0 | B_Clinical_K_ALK | 0.404 | 0.232 | 495.1 | 549.8 | {'epsilon': 2.0, 'alpha': 0.001} | {'epsilon': 1.5, 'alpha': 0.01} |
| 1.0 | C1_Combined_ALK | 0.420 | 0.146 | 522.0 | 571.6 | {'epsilon': 1.0, 'alpha': 0.1} | {'epsilon': 1.0, 'alpha': 0.01} |
| 1.0 | C1_Combined_K_ALK | 0.428 | 0.140 | 514.2 | 578.0 | {'epsilon': 1.0, 'alpha': 0.1} | {'epsilon': 1.0, 'alpha': 0.01} |
| 1.5 | A1_Biomechanical_ALK | 0.483 | 0.397 | 429.9 | 496.4 | {'epsilon': 1.5, 'alpha': 0.001} | {'epsilon': 1.5, 'alpha': 0.01} |
| 1.5 | A1_Biomechanical_K_ALK | 0.483 | 0.396 | 430.0 | 496.5 | {'epsilon': 1.5, 'alpha': 0.001} | {'epsilon': 1.5, 'alpha': 0.01} |
| 1.5 | A2_Biomechanical_ALK | 0.611 | 0.500 | 361.0 | 346.4 | {'epsilon': 1.5, 'alpha': 0.001} | {'epsilon': 1.5, 'alpha': 0.001} |
| 1.5 | A2_Biomechanical_K_ALK | 0.610 | 0.499 | 361.3 | 346.3 | {'epsilon': 1.5, 'alpha': 0.001} | {'epsilon': 1.5, 'alpha': 0.001} |
| 1.5 | B_Clinical_ALK | 0.434 | 0.392 | 446.1 | 502.0 | {'epsilon': 1.5, 'alpha': 0.001} | {'epsilon': 1.5, 'alpha': 0.01} |
| 1.5 | B_Clinical_K_ALK | 0.519 | 0.408 | 411.4 | 493.5 | {'epsilon': 1.5, 'alpha': 0.001} | {'epsilon': 1.5, 'alpha': 0.01} |
| 1.5 | C1_Combined_ALK | 0.510 | 0.379 | 417.1 | 391.5 | {'epsilon': 1.5, 'alpha': 0.001} | {'epsilon': 2.0, 'alpha': 0.0001} |
| 1.5 | C1_Combined_K_ALK | 0.508 | 0.406 | 417.8 | 380.5 | {'epsilon': 1.5, 'alpha': 0.001} | {'epsilon': 2.0, 'alpha': 0.0001} |
| 2.0 | A1_Biomechanical_ALK | 0.370 | 0.359 | 462.9 | 450.2 | {'epsilon': 1.5, 'alpha': 0.01} | {'epsilon': 1.5, 'alpha': 0.01} |
| 2.0 | A1_Biomechanical_K_ALK | 0.375 | 0.357 | 435.8 | 450.7 | {'epsilon': 2.0, 'alpha': 0.0001} | {'epsilon': 1.5, 'alpha': 0.01} |
| 2.0 | A2_Biomechanical_ALK | 0.467 | 0.462 | 423.1 | 405.5 | {'epsilon': 1.5, 'alpha': 0.01} | {'epsilon': 1.5, 'alpha': 0.01} |
| 2.0 | A2_Biomechanical_K_ALK | 0.474 | 0.465 | 395.6 | 402.2 | {'epsilon': 2.0, 'alpha': 0.0001} | {'epsilon': 1.5, 'alpha': 0.01} |
| 2.0 | B_Clinical_ALK | 0.363 | 0.371 | 473.2 | 453.9 | {'epsilon': 1.5, 'alpha': 0.01} | {'epsilon': 1.5, 'alpha': 0.01} |
| 2.0 | B_Clinical_K_ALK | 0.427 | 0.358 | 470.3 | 452.6 | {'epsilon': 2.0, 'alpha': 0.001} | {'epsilon': 1.5, 'alpha': 0.01} |
| 2.0 | C1_Combined_ALK | 0.422 | 0.274 | 472.7 | 476.5 | {'epsilon': 2.0, 'alpha': 0.001} | {'epsilon': 1.5, 'alpha': 0.01} |
| 2.0 | C1_Combined_K_ALK | 0.424 | 0.261 | 471.7 | 480.1 | {'epsilon': 2.0, 'alpha': 0.001} | {'epsilon': 1.5, 'alpha': 0.01} |
| 2.5 | A1_Biomechanical_ALK | 0.387 | 0.240 | 462.2 | 469.0 | {'epsilon': 2.0, 'alpha': 0.001} | {'epsilon': 1.0, 'alpha': 0.001} |
| 2.5 | A1_Biomechanical_K_ALK | 0.385 | 0.224 | 462.7 | 473.5 | {'epsilon': 2.0, 'alpha': 0.001} | {'epsilon': 1.0, 'alpha': 0.001} |
| 2.5 | A2_Biomechanical_ALK | 0.508 | 0.250 | 395.2 | 450.7 | {'epsilon': 2.0, 'alpha': 0.001} | {'epsilon': 1.0, 'alpha': 0.001} |
| 2.5 | A2_Biomechanical_K_ALK | 0.507 | 0.268 | 395.2 | 446.4 | {'epsilon': 2.0, 'alpha': 0.001} | {'epsilon': 1.0, 'alpha': 0.001} |
| 2.5 | B_Clinical_ALK | 0.260 | 0.222 | 504.0 | 468.2 | {'epsilon': 2.0, 'alpha': 0.001} | {'epsilon': 1.0, 'alpha': 0.001} |
| 2.5 | B_Clinical_K_ALK | 0.434 | 0.242 | 445.7 | 465.9 | {'epsilon': 2.0, 'alpha': 0.001} | {'epsilon': 1.0, 'alpha': 0.001} |
| 2.5 | C1_Combined_ALK | 0.435 | 0.246 | 445.4 | 464.0 | {'epsilon': 2.0, 'alpha': 0.001} | {'epsilon': 1.0, 'alpha': 0.001} |
| 2.5 | C1_Combined_K_ALK | 0.432 | 0.235 | 446.1 | 467.7 | {'epsilon': 2.0, 'alpha': 0.001} | {'epsilon': 1.0, 'alpha': 0.001} |
| 3.0 | A1_Biomechanical_ALK | 0.443 | 0.467 | 465.7 | 443.1 | {'epsilon': 2.0, 'alpha': 0.001} | {'epsilon': 1.0, 'alpha': 0.001} |
| 3.0 | A1_Biomechanical_K_ALK | 0.440 | 0.465 | 467.1 | 443.1 | {'epsilon': 2.0, 'alpha': 0.001} | {'epsilon': 1.0, 'alpha': 0.001} |
| 3.0 | A2_Biomechanical_ALK | 0.519 | 0.462 | 433.9 | 429.3 | {'epsilon': 1.5, 'alpha': 0.01} | {'epsilon': 1.0, 'alpha': 0.001} |
| 3.0 | A2_Biomechanical_K_ALK | 0.513 | 0.469 | 434.3 | 425.1 | {'epsilon': 1.5, 'alpha': 0.01} | {'epsilon': 1.0, 'alpha': 0.001} |
| 3.0 | B_Clinical_ALK | 0.349 | 0.391 | 517.3 | 465.6 | {'epsilon': 1.5, 'alpha': 0.01} | {'epsilon': 1.0, 'alpha': 0.001} |
| 3.0 | B_Clinical_K_ALK | 0.405 | 0.464 | 494.9 | 444.1 | {'epsilon': 1.5, 'alpha': 0.01} | {'epsilon': 1.0, 'alpha': 0.001} |
| 3.0 | C1_Combined_ALK | 0.389 | 0.468 | 504.4 | 443.2 | {'epsilon': 2.0, 'alpha': 0.001} | {'epsilon': 1.0, 'alpha': 0.001} |
| 3.0 | C1_Combined_K_ALK | 0.389 | 0.463 | 504.5 | 444.7 | {'epsilon': 2.0, 'alpha': 0.001} | {'epsilon': 1.0, 'alpha': 0.001} |
| 3.5 | A1_Biomechanical_ALK | 0.343 | 0.402 | 452.2 | 436.7 | {'epsilon': 2.0, 'alpha': 0.0001} | {'epsilon': 1.0, 'alpha': 0.001} |
| 3.5 | A1_Biomechanical_K_ALK | 0.335 | 0.404 | 454.5 | 436.2 | {'epsilon': 2.0, 'alpha': 0.0001} | {'epsilon': 1.0, 'alpha': 0.001} |
| 3.5 | A2_Biomechanical_ALK | 0.438 | 0.379 | 469.4 | 446.0 | {'epsilon': 1.5, 'alpha': 0.01} | {'epsilon': 1.5, 'alpha': 0.01} |
| 3.5 | A2_Biomechanical_K_ALK | 0.441 | 0.381 | 465.8 | 442.6 | {'epsilon': 1.5, 'alpha': 0.01} | {'epsilon': 1.5, 'alpha': 0.01} |
| 3.5 | B_Clinical_ALK | 0.316 | 0.376 | 460.5 | 445.2 | {'epsilon': 2.0, 'alpha': 0.0001} | {'epsilon': 1.0, 'alpha': 0.001} |
| 3.5 | B_Clinical_K_ALK | 0.341 | 0.343 | 453.7 | 456.7 | {'epsilon': 2.0, 'alpha': 0.0001} | {'epsilon': 1.0, 'alpha': 0.001} |
| 3.5 | C1_Combined_ALK | 0.336 | 0.368 | 454.9 | 448.5 | {'epsilon': 2.0, 'alpha': 0.0001} | {'epsilon': 1.0, 'alpha': 0.001} |
| 3.5 | C1_Combined_K_ALK | 0.343 | 0.370 | 453.1 | 449.0 | {'epsilon': 2.0, 'alpha': 0.0001} | {'epsilon': 1.0, 'alpha': 0.001} |
| 4.0 | A1_Biomechanical_ALK | 0.304 | 0.338 | 508.7 | 504.3 | {'epsilon': 2.0, 'alpha': 0.0001} | {'epsilon': 1.0, 'alpha': 0.001} |
| 4.0 | A1_Biomechanical_K_ALK | 0.296 | 0.331 | 511.6 | 507.4 | {'epsilon': 2.0, 'alpha': 0.0001} | {'epsilon': 1.0, 'alpha': 0.001} |
| 4.0 | A2_Biomechanical_ALK | 0.398 | 0.199 | 497.6 | 532.8 | {'epsilon': 2.0, 'alpha': 0.001} | {'epsilon': 1.0, 'alpha': 0.001} |
| 4.0 | A2_Biomechanical_K_ALK | 0.397 | 0.224 | 498.1 | 526.2 | {'epsilon': 2.0, 'alpha': 0.001} | {'epsilon': 1.0, 'alpha': 0.001} |
| 4.0 | B_Clinical_ALK | 0.260 | 0.247 | 522.1 | 528.7 | {'epsilon': 2.0, 'alpha': 0.0001} | {'epsilon': 1.0, 'alpha': 0.001} |
| 4.0 | B_Clinical_K_ALK | 0.321 | 0.245 | 504.2 | 528.4 | {'epsilon': 2.0, 'alpha': 0.0001} | {'epsilon': 1.0, 'alpha': 0.001} |
| 4.0 | C1_Combined_ALK | 0.325 | 0.282 | 503.0 | 520.3 | {'epsilon': 2.0, 'alpha': 0.0001} | {'epsilon': 1.0, 'alpha': 0.001} |
| 4.0 | C1_Combined_K_ALK | 0.319 | 0.279 | 505.4 | 521.1 | {'epsilon': 2.0, 'alpha': 0.0001} | {'epsilon': 1.0, 'alpha': 0.001} |
| 4.5 | A1_Biomechanical_ALK | 0.298 | 0.231 | 518.0 | 539.7 | {'epsilon': 2.0, 'alpha': 0.0001} | {'epsilon': 1.0, 'alpha': 0.001} |
| 4.5 | A1_Biomechanical_K_ALK | 0.294 | 0.236 | 519.8 | 410.6 | {'epsilon': 2.0, 'alpha': 0.0001} | {'epsilon': 1.0, 'alpha': 0.1} |
| 4.5 | A2_Biomechanical_ALK | 0.358 | 0.143 | 540.9 | 552.2 | {'epsilon': 2.0, 'alpha': 0.001} | {'epsilon': 1.0, 'alpha': 0.001} |
| 4.5 | A2_Biomechanical_K_ALK | 0.355 | 0.157 | 542.1 | 418.7 | {'epsilon': 2.0, 'alpha': 0.001} | {'epsilon': 1.0, 'alpha': 0.1} |
| 4.5 | B_Clinical_ALK | 0.250 | 0.208 | 624.8 | 544.3 | {'epsilon': 1.35, 'alpha': 0.0001} | {'epsilon': 1.0, 'alpha': 0.001} |
| 4.5 | B_Clinical_K_ALK | 0.315 | 0.219 | 577.6 | 540.3 | {'epsilon': 2.0, 'alpha': 0.001} | {'epsilon': 1.0, 'alpha': 0.001} |
| 4.5 | C1_Combined_ALK | 0.318 | 0.224 | 575.7 | 538.9 | {'epsilon': 2.0, 'alpha': 0.001} | {'epsilon': 1.0, 'alpha': 0.001} |
| 4.5 | C1_Combined_K_ALK | 0.317 | 0.221 | 576.5 | 539.9 | {'epsilon': 2.0, 'alpha': 0.001} | {'epsilon': 1.0, 'alpha': 0.001} |
| 5.0 | A1_Biomechanical_ALK | 0.291 | -0.022 | 633.2 | 478.7 | {'epsilon': 1.5, 'alpha': 0.01} | {'epsilon': 1.0, 'alpha': 0.1} |
| 5.0 | A1_Biomechanical_K_ALK | 0.293 | -0.048 | 632.7 | 483.1 | {'epsilon': 1.5, 'alpha': 0.01} | {'epsilon': 1.0, 'alpha': 0.1} |
| 5.0 | A2_Biomechanical_ALK | 0.395 | 0.036 | 578.5 | 565.8 | {'epsilon': 1.5, 'alpha': 0.01} | {'epsilon': 1.0, 'alpha': 0.001} |
| 5.0 | A2_Biomechanical_K_ALK | 0.398 | 0.092 | 578.2 | 551.6 | {'epsilon': 1.5, 'alpha': 0.01} | {'epsilon': 1.0, 'alpha': 0.001} |
| 5.0 | B_Clinical_ALK | 0.317 | 0.134 | 609.4 | 551.2 | {'epsilon': 1.35, 'alpha': 0.0001} | {'epsilon': 1.0, 'alpha': 0.001} |
| 5.0 | B_Clinical_K_ALK | 0.384 | 0.119 | 582.1 | 558.7 | {'epsilon': 2.0, 'alpha': 0.001} | {'epsilon': 1.0, 'alpha': 0.001} |
| 5.0 | C1_Combined_ALK | 0.354 | -0.144 | 595.3 | 496.6 | {'epsilon': 2.0, 'alpha': 0.001} | {'epsilon': 1.0, 'alpha': 0.1} |
| 5.0 | C1_Combined_K_ALK | 0.355 | 0.056 | 595.2 | 564.7 | {'epsilon': 2.0, 'alpha': 0.001} | {'epsilon': 1.0, 'alpha': 0.001} |
| 5.5 | A1_Biomechanical_ALK | 0.291 | 0.048 | 633.0 | 602.6 | {'epsilon': 1.5, 'alpha': 0.01} | {'epsilon': 1.5, 'alpha': 0.01} |
| 5.5 | A1_Biomechanical_K_ALK | 0.288 | 0.049 | 634.2 | 604.7 | {'epsilon': 1.5, 'alpha': 0.01} | {'epsilon': 1.5, 'alpha': 0.01} |
| 5.5 | A2_Biomechanical_ALK | 0.373 | 0.115 | 593.2 | 564.1 | {'epsilon': 1.5, 'alpha': 0.01} | {'epsilon': 1.5, 'alpha': 0.01} |
| 5.5 | A2_Biomechanical_K_ALK | 0.370 | 0.115 | 594.5 | 571.9 | {'epsilon': 1.5, 'alpha': 0.01} | {'epsilon': 1.5, 'alpha': 0.01} |
| 5.5 | B_Clinical_ALK | 0.254 | 0.097 | 675.1 | 643.5 | {'epsilon': 2.0, 'alpha': 0.001} | {'epsilon': 1.0, 'alpha': 0.001} |
| 5.5 | B_Clinical_K_ALK | 0.334 | 0.107 | 647.3 | 634.4 | {'epsilon': 2.0, 'alpha': 0.001} | {'epsilon': 1.0, 'alpha': 0.001} |
| 5.5 | C1_Combined_ALK | 0.298 | 0.104 | 620.7 | 633.7 | {'epsilon': 1.5, 'alpha': 0.01} | {'epsilon': 1.0, 'alpha': 0.001} |
| 5.5 | C1_Combined_K_ALK | 0.292 | 0.082 | 623.7 | 637.0 | {'epsilon': 1.5, 'alpha': 0.01} | {'epsilon': 1.0, 'alpha': 0.001} |
| 6.0 | A1_Biomechanical_ALK | 0.351 | 0.092 | 673.9 | 670.9 | {'epsilon': 1.5, 'alpha': 0.01} | {'epsilon': 1.5, 'alpha': 0.01} |
| 6.0 | A1_Biomechanical_K_ALK | 0.354 | 0.104 | 672.6 | 669.2 | {'epsilon': 1.5, 'alpha': 0.01} | {'epsilon': 1.5, 'alpha': 0.01} |
| 6.0 | A2_Biomechanical_ALK | 0.423 | 0.161 | 631.8 | 619.5 | {'epsilon': 1.5, 'alpha': 0.01} | {'epsilon': 1.5, 'alpha': 0.01} |
| 6.0 | A2_Biomechanical_K_ALK | 0.434 | 0.174 | 625.7 | 623.8 | {'epsilon': 1.5, 'alpha': 0.01} | {'epsilon': 1.5, 'alpha': 0.01} |
| 6.0 | B_Clinical_ALK | 0.301 | 0.104 | 706.3 | 692.2 | {'epsilon': 1.5, 'alpha': 0.01} | {'epsilon': 1.5, 'alpha': 0.01} |
| 6.0 | B_Clinical_K_ALK | 0.317 | 0.053 | 628.1 | 692.7 | {'epsilon': 2.0, 'alpha': 0.001} | {'epsilon': 1.5, 'alpha': 0.01} |
| 6.0 | C1_Combined_ALK | 0.362 | 0.033 | 663.7 | 666.6 | {'epsilon': 1.5, 'alpha': 0.01} | {'epsilon': 1.5, 'alpha': 0.01} |
| 6.0 | C1_Combined_K_ALK | 0.361 | 0.037 | 664.9 | 667.8 | {'epsilon': 1.5, 'alpha': 0.01} | {'epsilon': 1.5, 'alpha': 0.01} |

## 三、与已有五折全模型结果对比（lenient_ALK）

下表列出每个 ALK 方案在每个距离上，原五折全模型搜索中的最佳模型 / R²，以及本次 Robust Linear Regression 五折结果。

| 距离 (mm) | 方案 | 原五折最佳模型 | 原五折最佳 R² | Robust LR 5-fold R² | Robust LR 5-fold RMSE |
|-----------|------|----------------|---------------|---------------------|----------------------|
| 1.0 | A1_Biomechanical_ALK | Random_Forest | 0.437 | 0.415 | 535.3 |
| 1.0 | A1_Biomechanical_K_ALK | Random_Forest | 0.451 | 0.413 | 536.3 |
| 1.0 | A2_Biomechanical_ALK | Ridge | 0.450 | 0.427 | 531.5 |
| 1.0 | A2_Biomechanical_K_ALK | Ridge | 0.445 | 0.425 | 532.2 |
| 1.0 | B_Clinical_ALK | Lasso | 0.439 | 0.451 | 482.0 |
| 1.0 | B_Clinical_K_ALK | Lasso | 0.417 | 0.404 | 495.1 |
| 1.0 | C1_Combined_ALK | Random_Forest | 0.446 | 0.420 | 522.0 |
| 1.0 | C1_Combined_K_ALK | Random_Forest | 0.451 | 0.428 | 514.2 |
| 1.5 | A1_Biomechanical_ALK | Random_Forest | 0.544 | 0.483 | 429.9 |
| 1.5 | A1_Biomechanical_K_ALK | Random_Forest | 0.553 | 0.483 | 430.0 |
| 1.5 | A2_Biomechanical_ALK | Lasso | 0.586 | 0.611 | 361.0 |
| 1.5 | A2_Biomechanical_K_ALK | Ridge | 0.577 | 0.610 | 361.3 |
| 1.5 | B_Clinical_ALK | Lasso | 0.537 | 0.434 | 446.1 |
| 1.5 | B_Clinical_K_ALK | ElasticNet | 0.608 | 0.519 | 411.4 |
| 1.5 | C1_Combined_ALK | Lasso | 0.611 | 0.510 | 417.1 |
| 1.5 | C1_Combined_K_ALK | Lasso | 0.611 | 0.508 | 417.8 |
| 2.0 | A1_Biomechanical_ALK | Random_Forest | 0.481 | 0.370 | 462.9 |
| 2.0 | A1_Biomechanical_K_ALK | Random_Forest | 0.470 | 0.375 | 435.8 |
| 2.0 | A2_Biomechanical_ALK | ElasticNet | 0.527 | 0.467 | 423.1 |
| 2.0 | A2_Biomechanical_K_ALK | ElasticNet | 0.524 | 0.474 | 395.6 |
| 2.0 | B_Clinical_ALK | Lasso | 0.442 | 0.363 | 473.2 |
| 2.0 | B_Clinical_K_ALK | ElasticNet | 0.486 | 0.427 | 470.3 |
| 2.0 | C1_Combined_ALK | Lasso | 0.500 | 0.422 | 472.7 |
| 2.0 | C1_Combined_K_ALK | Lasso | 0.500 | 0.424 | 471.7 |
| 2.5 | A1_Biomechanical_ALK | Lasso | 0.379 | 0.387 | 462.2 |
| 2.5 | A1_Biomechanical_K_ALK | Lasso | 0.379 | 0.385 | 462.7 |
| 2.5 | A2_Biomechanical_ALK | Lasso | 0.485 | 0.508 | 395.2 |
| 2.5 | A2_Biomechanical_K_ALK | Lasso | 0.485 | 0.507 | 395.2 |
| 2.5 | B_Clinical_ALK | Random_Forest | 0.283 | 0.260 | 504.0 |
| 2.5 | B_Clinical_K_ALK | ElasticNet | 0.411 | 0.434 | 445.7 |
| 2.5 | C1_Combined_ALK | Lasso | 0.421 | 0.435 | 445.4 |
| 2.5 | C1_Combined_K_ALK | Lasso | 0.421 | 0.432 | 446.1 |
| 3.0 | A1_Biomechanical_ALK | Lasso | 0.426 | 0.443 | 465.7 |
| 3.0 | A1_Biomechanical_K_ALK | Ridge | 0.422 | 0.440 | 467.1 |
| 3.0 | A2_Biomechanical_ALK | Ridge | 0.498 | 0.519 | 433.9 |
| 3.0 | A2_Biomechanical_K_ALK | Ridge | 0.495 | 0.513 | 434.3 |
| 3.0 | B_Clinical_ALK | Ridge | 0.321 | 0.349 | 517.3 |
| 3.0 | B_Clinical_K_ALK | ElasticNet | 0.383 | 0.405 | 494.9 |
| 3.0 | C1_Combined_ALK | Lasso | 0.399 | 0.389 | 504.4 |
| 3.0 | C1_Combined_K_ALK | Lasso | 0.399 | 0.389 | 504.5 |
| 3.5 | A1_Biomechanical_ALK | ElasticNet | 0.304 | 0.343 | 452.2 |
| 3.5 | A1_Biomechanical_K_ALK | Ridge | 0.300 | 0.335 | 454.5 |
| 3.5 | A2_Biomechanical_ALK | Lasso | 0.418 | 0.438 | 469.4 |
| 3.5 | A2_Biomechanical_K_ALK | Lasso | 0.418 | 0.441 | 465.8 |
| 3.5 | B_Clinical_ALK | Ridge | 0.266 | 0.316 | 460.5 |
| 3.5 | B_Clinical_K_ALK | ElasticNet | 0.267 | 0.341 | 453.7 |
| 3.5 | C1_Combined_ALK | Neural_Network | 0.331 | 0.336 | 454.9 |
| 3.5 | C1_Combined_K_ALK | ElasticNet | 0.312 | 0.343 | 453.1 |
| 4.0 | A1_Biomechanical_ALK | ElasticNet | 0.258 | 0.304 | 508.7 |
| 4.0 | A1_Biomechanical_K_ALK | Neural_Network | 0.247 | 0.296 | 511.6 |
| 4.0 | A2_Biomechanical_ALK | Lasso | 0.387 | 0.398 | 497.6 |
| 4.0 | A2_Biomechanical_K_ALK | Lasso | 0.387 | 0.397 | 498.1 |
| 4.0 | B_Clinical_ALK | Ridge | 0.285 | 0.260 | 522.1 |
| 4.0 | B_Clinical_K_ALK | Lasso | 0.291 | 0.321 | 504.2 |
| 4.0 | C1_Combined_ALK | SVM | 0.296 | 0.325 | 503.0 |
| 4.0 | C1_Combined_K_ALK | Ridge | 0.277 | 0.319 | 505.4 |
| 4.5 | A1_Biomechanical_ALK | ElasticNet | 0.286 | 0.298 | 518.0 |
| 4.5 | A1_Biomechanical_K_ALK | ElasticNet | 0.267 | 0.294 | 519.8 |
| 4.5 | A2_Biomechanical_ALK | Lasso | 0.335 | 0.358 | 540.9 |
| 4.5 | A2_Biomechanical_K_ALK | Lasso | 0.335 | 0.355 | 542.1 |
| 4.5 | B_Clinical_ALK | Ridge | 0.286 | 0.250 | 624.8 |
| 4.5 | B_Clinical_K_ALK | ElasticNet | 0.300 | 0.315 | 577.6 |
| 4.5 | C1_Combined_ALK | Ridge | 0.312 | 0.318 | 575.7 |
| 4.5 | C1_Combined_K_ALK | Lasso | 0.310 | 0.317 | 576.5 |
| 5.0 | A1_Biomechanical_ALK | Random_Forest | 0.428 | 0.291 | 633.2 |
| 5.0 | A1_Biomechanical_K_ALK | Random_Forest | 0.415 | 0.293 | 632.7 |
| 5.0 | A2_Biomechanical_ALK | Random_Forest | 0.458 | 0.395 | 578.5 |
| 5.0 | A2_Biomechanical_K_ALK | Random_Forest | 0.446 | 0.398 | 578.2 |
| 5.0 | B_Clinical_ALK | Random_Forest | 0.395 | 0.317 | 609.4 |
| 5.0 | B_Clinical_K_ALK | ElasticNet | 0.386 | 0.384 | 582.1 |
| 5.0 | C1_Combined_ALK | Neural_Network | 0.370 | 0.354 | 595.3 |
| 5.0 | C1_Combined_K_ALK | SVM | 0.380 | 0.355 | 595.2 |
| 5.5 | A1_Biomechanical_ALK | Random_Forest | 0.373 | 0.291 | 633.0 |
| 5.5 | A1_Biomechanical_K_ALK | Random_Forest | 0.375 | 0.288 | 634.2 |
| 5.5 | A2_Biomechanical_ALK | Lasso | 0.376 | 0.373 | 593.2 |
| 5.5 | A2_Biomechanical_K_ALK | Lasso | 0.376 | 0.370 | 594.5 |
| 5.5 | B_Clinical_ALK | Random_Forest | 0.374 | 0.254 | 675.1 |
| 5.5 | B_Clinical_K_ALK | Lasso | 0.364 | 0.334 | 647.3 |
| 5.5 | C1_Combined_ALK | Neural_Network | 0.363 | 0.298 | 620.7 |
| 5.5 | C1_Combined_K_ALK | SVM | 0.359 | 0.292 | 623.7 |
| 6.0 | A1_Biomechanical_ALK | Random_Forest | 0.385 | 0.351 | 673.9 |
| 6.0 | A1_Biomechanical_K_ALK | Neural_Network | 0.396 | 0.354 | 672.6 |
| 6.0 | A2_Biomechanical_ALK | Neural_Network | 0.466 | 0.423 | 631.8 |
| 6.0 | A2_Biomechanical_K_ALK | Lasso | 0.418 | 0.434 | 625.7 |
| 6.0 | B_Clinical_ALK | SVM | 0.413 | 0.301 | 706.3 |
| 6.0 | B_Clinical_K_ALK | SVM | 0.347 | 0.317 | 628.1 |
| 6.0 | C1_Combined_ALK | Neural_Network | 0.390 | 0.362 | 663.7 |
| 6.0 | C1_Combined_K_ALK | Neural_Network | 0.363 | 0.361 | 664.9 |

## 四、与已有十折 C1_Combined_ALK 结果对比

下表比较 C1_Combined_ALK 在 10-fold 下，原十折全模型搜索的最佳结果与本次 Robust Linear Regression 十折结果。

| 距离 (mm) | 原十折最佳模型 | 原十折最佳 R² | Robust LR 10-fold R² | Robust LR 10-fold RMSE |
|-----------|----------------|---------------|----------------------|-----------------------|
| 1.0 | SVM | 0.332 | 0.146 | 571.6 |
| 1.5 | Random_Forest | 0.441 | 0.379 | 391.5 |
| 2.0 | Ridge | 0.367 | 0.274 | 476.5 |
| 2.5 | ElasticNet | 0.191 | 0.246 | 464.0 |
| 3.0 | ElasticNet | 0.376 | 0.468 | 443.2 |
| 3.5 | ElasticNet | 0.334 | 0.368 | 448.5 |
| 4.0 | ElasticNet | 0.096 | 0.282 | 520.3 |
| 4.5 | ElasticNet | 0.218 | 0.224 | 538.9 |
| 5.0 | SVM | -0.051 | -0.144 | 496.6 |
| 5.5 | SVM | 0.002 | 0.104 | 633.7 |
| 6.0 | Neural_Network | 0.098 | 0.033 | 666.6 |

## 五、本次 Robust Linear Regression 全结果汇总

| 距离 (mm) | 方案 | CV 折数 | Test R² | Test RMSE | Gap | 最佳参数 |
|-----------|------|---------|---------|-----------|-----|---------|
| 1.0 | A1_Biomechanical_ALK | 5 | 0.415 | 535.3 | 0.144 | {'epsilon': 1.5, 'alpha': 0.001} |
| 1.0 | A1_Biomechanical_ALK | 10 | 0.167 | 562.3 | 0.266 | {'epsilon': 1.5, 'alpha': 0.01} |
| 1.0 | A1_Biomechanical_K_ALK | 5 | 0.413 | 536.3 | 0.147 | {'epsilon': 1.5, 'alpha': 0.001} |
| 1.0 | A1_Biomechanical_K_ALK | 10 | 0.155 | 565.7 | 0.280 | {'epsilon': 1.5, 'alpha': 0.01} |
| 1.0 | A2_Biomechanical_ALK | 5 | 0.427 | 531.5 | 0.167 | {'epsilon': 1.5, 'alpha': 0.001} |
| 1.0 | A2_Biomechanical_ALK | 10 | 0.241 | 549.8 | 0.221 | {'epsilon': 1.0, 'alpha': 0.001} |
| 1.0 | A2_Biomechanical_K_ALK | 5 | 0.425 | 532.2 | 0.168 | {'epsilon': 1.5, 'alpha': 0.001} |
| 1.0 | A2_Biomechanical_K_ALK | 10 | 0.232 | 555.7 | 0.231 | {'epsilon': 1.0, 'alpha': 0.001} |
| 1.0 | B_Clinical_ALK | 5 | 0.451 | 482.0 | 0.160 | {'epsilon': 2.0, 'alpha': 0.001} |
| 1.0 | B_Clinical_ALK | 10 | 0.216 | 478.9 | 0.401 | {'epsilon': 2.0, 'alpha': 0.001} |
| 1.0 | B_Clinical_K_ALK | 5 | 0.404 | 495.1 | 0.211 | {'epsilon': 2.0, 'alpha': 0.001} |
| 1.0 | B_Clinical_K_ALK | 10 | 0.232 | 549.8 | 0.212 | {'epsilon': 1.5, 'alpha': 0.01} |
| 1.0 | C1_Combined_ALK | 5 | 0.420 | 522.0 | 0.113 | {'epsilon': 1.0, 'alpha': 0.1} |
| 1.0 | C1_Combined_ALK | 10 | 0.146 | 571.6 | 0.404 | {'epsilon': 1.0, 'alpha': 0.01} |
| 1.0 | C1_Combined_K_ALK | 5 | 0.428 | 514.2 | 0.113 | {'epsilon': 1.0, 'alpha': 0.1} |
| 1.0 | C1_Combined_K_ALK | 10 | 0.140 | 578.0 | 0.403 | {'epsilon': 1.0, 'alpha': 0.01} |
| 1.5 | A1_Biomechanical_ALK | 5 | 0.483 | 429.9 | 0.148 | {'epsilon': 1.5, 'alpha': 0.001} |
| 1.5 | A1_Biomechanical_ALK | 10 | 0.397 | 496.4 | 0.076 | {'epsilon': 1.5, 'alpha': 0.01} |
| 1.5 | A1_Biomechanical_K_ALK | 5 | 0.483 | 430.0 | 0.150 | {'epsilon': 1.5, 'alpha': 0.001} |
| 1.5 | A1_Biomechanical_K_ALK | 10 | 0.396 | 496.5 | 0.076 | {'epsilon': 1.5, 'alpha': 0.01} |
| 1.5 | A2_Biomechanical_ALK | 5 | 0.611 | 361.0 | 0.116 | {'epsilon': 1.5, 'alpha': 0.001} |
| 1.5 | A2_Biomechanical_ALK | 10 | 0.500 | 346.4 | 0.226 | {'epsilon': 1.5, 'alpha': 0.001} |
| 1.5 | A2_Biomechanical_K_ALK | 5 | 0.610 | 361.3 | 0.119 | {'epsilon': 1.5, 'alpha': 0.001} |
| 1.5 | A2_Biomechanical_K_ALK | 10 | 0.499 | 346.3 | 0.228 | {'epsilon': 1.5, 'alpha': 0.001} |
| 1.5 | B_Clinical_ALK | 5 | 0.434 | 446.1 | 0.177 | {'epsilon': 1.5, 'alpha': 0.001} |
| 1.5 | B_Clinical_ALK | 10 | 0.392 | 502.0 | 0.066 | {'epsilon': 1.5, 'alpha': 0.01} |
| 1.5 | B_Clinical_K_ALK | 5 | 0.519 | 411.4 | 0.134 | {'epsilon': 1.5, 'alpha': 0.001} |
| 1.5 | B_Clinical_K_ALK | 10 | 0.408 | 493.5 | 0.071 | {'epsilon': 1.5, 'alpha': 0.01} |
| 1.5 | C1_Combined_ALK | 5 | 0.510 | 417.1 | 0.142 | {'epsilon': 1.5, 'alpha': 0.001} |
| 1.5 | C1_Combined_ALK | 10 | 0.379 | 391.5 | 0.237 | {'epsilon': 2.0, 'alpha': 0.0001} |
| 1.5 | C1_Combined_K_ALK | 5 | 0.508 | 417.8 | 0.146 | {'epsilon': 1.5, 'alpha': 0.001} |
| 1.5 | C1_Combined_K_ALK | 10 | 0.406 | 380.5 | 0.213 | {'epsilon': 2.0, 'alpha': 0.0001} |
| 2.0 | A1_Biomechanical_ALK | 5 | 0.370 | 462.9 | 0.048 | {'epsilon': 1.5, 'alpha': 0.01} |
| 2.0 | A1_Biomechanical_ALK | 10 | 0.359 | 450.2 | 0.051 | {'epsilon': 1.5, 'alpha': 0.01} |
| 2.0 | A1_Biomechanical_K_ALK | 5 | 0.375 | 435.8 | 0.073 | {'epsilon': 2.0, 'alpha': 0.0001} |
| 2.0 | A1_Biomechanical_K_ALK | 10 | 0.357 | 450.7 | 0.054 | {'epsilon': 1.5, 'alpha': 0.01} |
| 2.0 | A2_Biomechanical_ALK | 5 | 0.467 | 423.1 | 0.049 | {'epsilon': 1.5, 'alpha': 0.01} |
| 2.0 | A2_Biomechanical_ALK | 10 | 0.462 | 405.5 | 0.037 | {'epsilon': 1.5, 'alpha': 0.01} |
| 2.0 | A2_Biomechanical_K_ALK | 5 | 0.474 | 395.6 | 0.069 | {'epsilon': 2.0, 'alpha': 0.0001} |
| 2.0 | A2_Biomechanical_K_ALK | 10 | 0.465 | 402.2 | 0.037 | {'epsilon': 1.5, 'alpha': 0.01} |
| 2.0 | B_Clinical_ALK | 5 | 0.363 | 473.2 | 0.059 | {'epsilon': 1.5, 'alpha': 0.01} |
| 2.0 | B_Clinical_ALK | 10 | 0.371 | 453.9 | 0.038 | {'epsilon': 1.5, 'alpha': 0.01} |
| 2.0 | B_Clinical_K_ALK | 5 | 0.427 | 470.3 | 0.096 | {'epsilon': 2.0, 'alpha': 0.001} |
| 2.0 | B_Clinical_K_ALK | 10 | 0.358 | 452.6 | 0.062 | {'epsilon': 1.5, 'alpha': 0.01} |
| 2.0 | C1_Combined_ALK | 5 | 0.422 | 472.7 | 0.100 | {'epsilon': 2.0, 'alpha': 0.001} |
| 2.0 | C1_Combined_ALK | 10 | 0.274 | 476.5 | 0.150 | {'epsilon': 1.5, 'alpha': 0.01} |
| 2.0 | C1_Combined_K_ALK | 5 | 0.424 | 471.7 | 0.099 | {'epsilon': 2.0, 'alpha': 0.001} |
| 2.0 | C1_Combined_K_ALK | 10 | 0.261 | 480.1 | 0.163 | {'epsilon': 1.5, 'alpha': 0.01} |
| 2.5 | A1_Biomechanical_ALK | 5 | 0.387 | 462.2 | 0.118 | {'epsilon': 2.0, 'alpha': 0.001} |
| 2.5 | A1_Biomechanical_ALK | 10 | 0.240 | 469.0 | 0.161 | {'epsilon': 1.0, 'alpha': 0.001} |
| 2.5 | A1_Biomechanical_K_ALK | 5 | 0.385 | 462.7 | 0.121 | {'epsilon': 2.0, 'alpha': 0.001} |
| 2.5 | A1_Biomechanical_K_ALK | 10 | 0.224 | 473.5 | 0.175 | {'epsilon': 1.0, 'alpha': 0.001} |
| 2.5 | A2_Biomechanical_ALK | 5 | 0.508 | 395.2 | 0.084 | {'epsilon': 2.0, 'alpha': 0.001} |
| 2.5 | A2_Biomechanical_ALK | 10 | 0.250 | 450.7 | 0.251 | {'epsilon': 1.0, 'alpha': 0.001} |
| 2.5 | A2_Biomechanical_K_ALK | 5 | 0.507 | 395.2 | 0.086 | {'epsilon': 2.0, 'alpha': 0.001} |
| 2.5 | A2_Biomechanical_K_ALK | 10 | 0.268 | 446.4 | 0.235 | {'epsilon': 1.0, 'alpha': 0.001} |
| 2.5 | B_Clinical_ALK | 5 | 0.260 | 504.0 | 0.222 | {'epsilon': 2.0, 'alpha': 0.001} |
| 2.5 | B_Clinical_ALK | 10 | 0.222 | 468.2 | 0.193 | {'epsilon': 1.0, 'alpha': 0.001} |
| 2.5 | B_Clinical_K_ALK | 5 | 0.434 | 445.7 | 0.094 | {'epsilon': 2.0, 'alpha': 0.001} |
| 2.5 | B_Clinical_K_ALK | 10 | 0.242 | 465.9 | 0.170 | {'epsilon': 1.0, 'alpha': 0.001} |
| 2.5 | C1_Combined_ALK | 5 | 0.435 | 445.4 | 0.092 | {'epsilon': 2.0, 'alpha': 0.001} |
| 2.5 | C1_Combined_ALK | 10 | 0.246 | 464.0 | 0.167 | {'epsilon': 1.0, 'alpha': 0.001} |
| 2.5 | C1_Combined_K_ALK | 5 | 0.432 | 446.1 | 0.095 | {'epsilon': 2.0, 'alpha': 0.001} |
| 2.5 | C1_Combined_K_ALK | 10 | 0.235 | 467.7 | 0.176 | {'epsilon': 1.0, 'alpha': 0.001} |
| 3.0 | A1_Biomechanical_ALK | 5 | 0.443 | 465.7 | 0.014 | {'epsilon': 2.0, 'alpha': 0.001} |
| 3.0 | A1_Biomechanical_ALK | 10 | 0.467 | 443.1 | -0.082 | {'epsilon': 1.0, 'alpha': 0.001} |
| 3.0 | A1_Biomechanical_K_ALK | 5 | 0.440 | 467.1 | 0.018 | {'epsilon': 2.0, 'alpha': 0.001} |
| 3.0 | A1_Biomechanical_K_ALK | 10 | 0.465 | 443.1 | -0.082 | {'epsilon': 1.0, 'alpha': 0.001} |
| 3.0 | A2_Biomechanical_ALK | 5 | 0.519 | 433.9 | 0.090 | {'epsilon': 1.5, 'alpha': 0.01} |
| 3.0 | A2_Biomechanical_ALK | 10 | 0.462 | 429.3 | 0.121 | {'epsilon': 1.0, 'alpha': 0.001} |
| 3.0 | A2_Biomechanical_K_ALK | 5 | 0.513 | 434.3 | 0.097 | {'epsilon': 1.5, 'alpha': 0.01} |
| 3.0 | A2_Biomechanical_K_ALK | 10 | 0.469 | 425.1 | 0.113 | {'epsilon': 1.0, 'alpha': 0.001} |
| 3.0 | B_Clinical_ALK | 5 | 0.349 | 517.3 | 0.020 | {'epsilon': 1.5, 'alpha': 0.01} |
| 3.0 | B_Clinical_ALK | 10 | 0.391 | 465.6 | 0.003 | {'epsilon': 1.0, 'alpha': 0.001} |
| 3.0 | B_Clinical_K_ALK | 5 | 0.405 | 494.9 | -0.016 | {'epsilon': 1.5, 'alpha': 0.01} |
| 3.0 | B_Clinical_K_ALK | 10 | 0.464 | 444.1 | -0.074 | {'epsilon': 1.0, 'alpha': 0.001} |
| 3.0 | C1_Combined_ALK | 5 | 0.389 | 504.4 | 0.051 | {'epsilon': 2.0, 'alpha': 0.001} |
| 3.0 | C1_Combined_ALK | 10 | 0.468 | 443.2 | -0.079 | {'epsilon': 1.0, 'alpha': 0.001} |
| 3.0 | C1_Combined_K_ALK | 5 | 0.389 | 504.5 | 0.051 | {'epsilon': 2.0, 'alpha': 0.001} |
| 3.0 | C1_Combined_K_ALK | 10 | 0.463 | 444.7 | -0.075 | {'epsilon': 1.0, 'alpha': 0.001} |
| 3.5 | A1_Biomechanical_ALK | 5 | 0.343 | 452.2 | 0.042 | {'epsilon': 2.0, 'alpha': 0.0001} |
| 3.5 | A1_Biomechanical_ALK | 10 | 0.402 | 436.7 | 0.002 | {'epsilon': 1.0, 'alpha': 0.001} |
| 3.5 | A1_Biomechanical_K_ALK | 5 | 0.335 | 454.5 | 0.051 | {'epsilon': 2.0, 'alpha': 0.0001} |
| 3.5 | A1_Biomechanical_K_ALK | 10 | 0.404 | 436.2 | 0.001 | {'epsilon': 1.0, 'alpha': 0.001} |
| 3.5 | A2_Biomechanical_ALK | 5 | 0.438 | 469.4 | 0.056 | {'epsilon': 1.5, 'alpha': 0.01} |
| 3.5 | A2_Biomechanical_ALK | 10 | 0.379 | 446.0 | 0.106 | {'epsilon': 1.5, 'alpha': 0.01} |
| 3.5 | A2_Biomechanical_K_ALK | 5 | 0.441 | 465.8 | 0.056 | {'epsilon': 1.5, 'alpha': 0.01} |
| 3.5 | A2_Biomechanical_K_ALK | 10 | 0.381 | 442.6 | 0.106 | {'epsilon': 1.5, 'alpha': 0.01} |
| 3.5 | B_Clinical_ALK | 5 | 0.316 | 460.5 | 0.044 | {'epsilon': 2.0, 'alpha': 0.0001} |
| 3.5 | B_Clinical_ALK | 10 | 0.376 | 445.2 | 0.036 | {'epsilon': 1.0, 'alpha': 0.001} |
| 3.5 | B_Clinical_K_ALK | 5 | 0.341 | 453.7 | 0.053 | {'epsilon': 2.0, 'alpha': 0.0001} |
| 3.5 | B_Clinical_K_ALK | 10 | 0.343 | 456.7 | 0.072 | {'epsilon': 1.0, 'alpha': 0.001} |
| 3.5 | C1_Combined_ALK | 5 | 0.336 | 454.9 | 0.057 | {'epsilon': 2.0, 'alpha': 0.0001} |
| 3.5 | C1_Combined_ALK | 10 | 0.368 | 448.5 | 0.048 | {'epsilon': 1.0, 'alpha': 0.001} |
| 3.5 | C1_Combined_K_ALK | 5 | 0.343 | 453.1 | 0.050 | {'epsilon': 2.0, 'alpha': 0.0001} |
| 3.5 | C1_Combined_K_ALK | 10 | 0.370 | 449.0 | 0.046 | {'epsilon': 1.0, 'alpha': 0.001} |
| 4.0 | A1_Biomechanical_ALK | 5 | 0.304 | 508.7 | 0.093 | {'epsilon': 2.0, 'alpha': 0.0001} |
| 4.0 | A1_Biomechanical_ALK | 10 | 0.338 | 504.3 | 0.020 | {'epsilon': 1.0, 'alpha': 0.001} |
| 4.0 | A1_Biomechanical_K_ALK | 5 | 0.296 | 511.6 | 0.103 | {'epsilon': 2.0, 'alpha': 0.0001} |
| 4.0 | A1_Biomechanical_K_ALK | 10 | 0.331 | 507.4 | 0.026 | {'epsilon': 1.0, 'alpha': 0.001} |
| 4.0 | A2_Biomechanical_ALK | 5 | 0.398 | 497.6 | 0.171 | {'epsilon': 2.0, 'alpha': 0.001} |
| 4.0 | A2_Biomechanical_ALK | 10 | 0.199 | 532.8 | 0.310 | {'epsilon': 1.0, 'alpha': 0.001} |
| 4.0 | A2_Biomechanical_K_ALK | 5 | 0.397 | 498.1 | 0.173 | {'epsilon': 2.0, 'alpha': 0.001} |
| 4.0 | A2_Biomechanical_K_ALK | 10 | 0.224 | 526.2 | 0.292 | {'epsilon': 1.0, 'alpha': 0.001} |
| 4.0 | B_Clinical_ALK | 5 | 0.260 | 522.1 | 0.115 | {'epsilon': 2.0, 'alpha': 0.0001} |
| 4.0 | B_Clinical_ALK | 10 | 0.247 | 528.7 | 0.103 | {'epsilon': 1.0, 'alpha': 0.001} |
| 4.0 | B_Clinical_K_ALK | 5 | 0.321 | 504.2 | 0.090 | {'epsilon': 2.0, 'alpha': 0.0001} |
| 4.0 | B_Clinical_K_ALK | 10 | 0.245 | 528.4 | 0.110 | {'epsilon': 1.0, 'alpha': 0.001} |
| 4.0 | C1_Combined_ALK | 5 | 0.325 | 503.0 | 0.086 | {'epsilon': 2.0, 'alpha': 0.0001} |
| 4.0 | C1_Combined_ALK | 10 | 0.282 | 520.3 | 0.077 | {'epsilon': 1.0, 'alpha': 0.001} |
| 4.0 | C1_Combined_K_ALK | 5 | 0.319 | 505.4 | 0.093 | {'epsilon': 2.0, 'alpha': 0.0001} |
| 4.0 | C1_Combined_K_ALK | 10 | 0.279 | 521.1 | 0.082 | {'epsilon': 1.0, 'alpha': 0.001} |
| 4.5 | A1_Biomechanical_ALK | 5 | 0.298 | 518.0 | 0.136 | {'epsilon': 2.0, 'alpha': 0.0001} |
| 4.5 | A1_Biomechanical_ALK | 10 | 0.231 | 539.7 | 0.163 | {'epsilon': 1.0, 'alpha': 0.001} |
| 4.5 | A1_Biomechanical_K_ALK | 5 | 0.294 | 519.8 | 0.141 | {'epsilon': 2.0, 'alpha': 0.0001} |
| 4.5 | A1_Biomechanical_K_ALK | 10 | 0.236 | 410.6 | 0.071 | {'epsilon': 1.0, 'alpha': 0.1} |
| 4.5 | A2_Biomechanical_ALK | 5 | 0.358 | 540.9 | 0.169 | {'epsilon': 2.0, 'alpha': 0.001} |
| 4.5 | A2_Biomechanical_ALK | 10 | 0.143 | 552.2 | 0.338 | {'epsilon': 1.0, 'alpha': 0.001} |
| 4.5 | A2_Biomechanical_K_ALK | 5 | 0.355 | 542.1 | 0.173 | {'epsilon': 2.0, 'alpha': 0.001} |
| 4.5 | A2_Biomechanical_K_ALK | 10 | 0.157 | 418.7 | 0.164 | {'epsilon': 1.0, 'alpha': 0.1} |
| 4.5 | B_Clinical_ALK | 5 | 0.250 | 624.8 | 0.076 | {'epsilon': 1.35, 'alpha': 0.0001} |
| 4.5 | B_Clinical_ALK | 10 | 0.208 | 544.3 | 0.191 | {'epsilon': 1.0, 'alpha': 0.001} |
| 4.5 | B_Clinical_K_ALK | 5 | 0.315 | 577.6 | 0.163 | {'epsilon': 2.0, 'alpha': 0.001} |
| 4.5 | B_Clinical_K_ALK | 10 | 0.219 | 540.3 | 0.195 | {'epsilon': 1.0, 'alpha': 0.001} |
| 4.5 | C1_Combined_ALK | 5 | 0.318 | 575.7 | 0.159 | {'epsilon': 2.0, 'alpha': 0.001} |
| 4.5 | C1_Combined_ALK | 10 | 0.224 | 538.9 | 0.191 | {'epsilon': 1.0, 'alpha': 0.001} |
| 4.5 | C1_Combined_K_ALK | 5 | 0.317 | 576.5 | 0.161 | {'epsilon': 2.0, 'alpha': 0.001} |
| 4.5 | C1_Combined_K_ALK | 10 | 0.221 | 539.9 | 0.191 | {'epsilon': 1.0, 'alpha': 0.001} |
| 5.0 | A1_Biomechanical_ALK | 5 | 0.291 | 633.2 | 0.191 | {'epsilon': 1.5, 'alpha': 0.01} |
| 5.0 | A1_Biomechanical_ALK | 10 | -0.022 | 478.7 | 0.257 | {'epsilon': 1.0, 'alpha': 0.1} |
| 5.0 | A1_Biomechanical_K_ALK | 5 | 0.293 | 632.7 | 0.194 | {'epsilon': 1.5, 'alpha': 0.01} |
| 5.0 | A1_Biomechanical_K_ALK | 10 | -0.048 | 483.1 | 0.284 | {'epsilon': 1.0, 'alpha': 0.1} |
| 5.0 | A2_Biomechanical_ALK | 5 | 0.395 | 578.5 | 0.154 | {'epsilon': 1.5, 'alpha': 0.01} |
| 5.0 | A2_Biomechanical_ALK | 10 | 0.036 | 565.8 | 0.477 | {'epsilon': 1.0, 'alpha': 0.001} |
| 5.0 | A2_Biomechanical_K_ALK | 5 | 0.398 | 578.2 | 0.160 | {'epsilon': 1.5, 'alpha': 0.01} |
| 5.0 | A2_Biomechanical_K_ALK | 10 | 0.092 | 551.6 | 0.425 | {'epsilon': 1.0, 'alpha': 0.001} |
| 5.0 | B_Clinical_ALK | 5 | 0.317 | 609.4 | 0.073 | {'epsilon': 1.35, 'alpha': 0.0001} |
| 5.0 | B_Clinical_ALK | 10 | 0.134 | 551.2 | 0.305 | {'epsilon': 1.0, 'alpha': 0.001} |
| 5.0 | B_Clinical_K_ALK | 5 | 0.384 | 582.1 | 0.166 | {'epsilon': 2.0, 'alpha': 0.001} |
| 5.0 | B_Clinical_K_ALK | 10 | 0.119 | 558.7 | 0.320 | {'epsilon': 1.0, 'alpha': 0.001} |
| 5.0 | C1_Combined_ALK | 5 | 0.354 | 595.3 | 0.195 | {'epsilon': 2.0, 'alpha': 0.001} |
| 5.0 | C1_Combined_ALK | 10 | -0.144 | 496.6 | 0.395 | {'epsilon': 1.0, 'alpha': 0.1} |
| 5.0 | C1_Combined_K_ALK | 5 | 0.355 | 595.2 | 0.195 | {'epsilon': 2.0, 'alpha': 0.001} |
| 5.0 | C1_Combined_K_ALK | 10 | 0.056 | 564.7 | 0.391 | {'epsilon': 1.0, 'alpha': 0.001} |
| 5.5 | A1_Biomechanical_ALK | 5 | 0.291 | 633.0 | 0.232 | {'epsilon': 1.5, 'alpha': 0.01} |
| 5.5 | A1_Biomechanical_ALK | 10 | 0.048 | 602.6 | 0.470 | {'epsilon': 1.5, 'alpha': 0.01} |
| 5.5 | A1_Biomechanical_K_ALK | 5 | 0.288 | 634.2 | 0.238 | {'epsilon': 1.5, 'alpha': 0.01} |
| 5.5 | A1_Biomechanical_K_ALK | 10 | 0.049 | 604.7 | 0.471 | {'epsilon': 1.5, 'alpha': 0.01} |
| 5.5 | A2_Biomechanical_ALK | 5 | 0.373 | 593.2 | 0.197 | {'epsilon': 1.5, 'alpha': 0.01} |
| 5.5 | A2_Biomechanical_ALK | 10 | 0.115 | 564.1 | 0.453 | {'epsilon': 1.5, 'alpha': 0.01} |
| 5.5 | A2_Biomechanical_K_ALK | 5 | 0.370 | 594.5 | 0.205 | {'epsilon': 1.5, 'alpha': 0.01} |
| 5.5 | A2_Biomechanical_K_ALK | 10 | 0.115 | 571.9 | 0.456 | {'epsilon': 1.5, 'alpha': 0.01} |
| 5.5 | B_Clinical_ALK | 5 | 0.254 | 675.1 | 0.262 | {'epsilon': 2.0, 'alpha': 0.001} |
| 5.5 | B_Clinical_ALK | 10 | 0.097 | 643.5 | 0.314 | {'epsilon': 1.0, 'alpha': 0.001} |
| 5.5 | B_Clinical_K_ALK | 5 | 0.334 | 647.3 | 0.217 | {'epsilon': 2.0, 'alpha': 0.001} |
| 5.5 | B_Clinical_K_ALK | 10 | 0.107 | 634.4 | 0.308 | {'epsilon': 1.0, 'alpha': 0.001} |
| 5.5 | C1_Combined_ALK | 5 | 0.298 | 620.7 | 0.242 | {'epsilon': 1.5, 'alpha': 0.01} |
| 5.5 | C1_Combined_ALK | 10 | 0.104 | 633.7 | 0.320 | {'epsilon': 1.0, 'alpha': 0.001} |
| 5.5 | C1_Combined_K_ALK | 5 | 0.292 | 623.7 | 0.249 | {'epsilon': 1.5, 'alpha': 0.01} |
| 5.5 | C1_Combined_K_ALK | 10 | 0.082 | 637.0 | 0.340 | {'epsilon': 1.0, 'alpha': 0.001} |
| 6.0 | A1_Biomechanical_ALK | 5 | 0.351 | 673.9 | 0.130 | {'epsilon': 1.5, 'alpha': 0.01} |
| 6.0 | A1_Biomechanical_ALK | 10 | 0.092 | 670.9 | 0.383 | {'epsilon': 1.5, 'alpha': 0.01} |
| 6.0 | A1_Biomechanical_K_ALK | 5 | 0.354 | 672.6 | 0.129 | {'epsilon': 1.5, 'alpha': 0.01} |
| 6.0 | A1_Biomechanical_K_ALK | 10 | 0.104 | 669.2 | 0.373 | {'epsilon': 1.5, 'alpha': 0.01} |
| 6.0 | A2_Biomechanical_ALK | 5 | 0.423 | 631.8 | 0.118 | {'epsilon': 1.5, 'alpha': 0.01} |
| 6.0 | A2_Biomechanical_ALK | 10 | 0.161 | 619.5 | 0.378 | {'epsilon': 1.5, 'alpha': 0.01} |
| 6.0 | A2_Biomechanical_K_ALK | 5 | 0.434 | 625.7 | 0.112 | {'epsilon': 1.5, 'alpha': 0.01} |
| 6.0 | A2_Biomechanical_K_ALK | 10 | 0.174 | 623.8 | 0.369 | {'epsilon': 1.5, 'alpha': 0.01} |
| 6.0 | B_Clinical_ALK | 5 | 0.301 | 706.3 | 0.158 | {'epsilon': 1.5, 'alpha': 0.01} |
| 6.0 | B_Clinical_ALK | 10 | 0.104 | 692.2 | 0.348 | {'epsilon': 1.5, 'alpha': 0.01} |
| 6.0 | B_Clinical_K_ALK | 5 | 0.317 | 628.1 | 0.164 | {'epsilon': 2.0, 'alpha': 0.001} |
| 6.0 | B_Clinical_K_ALK | 10 | 0.053 | 692.7 | 0.414 | {'epsilon': 1.5, 'alpha': 0.01} |
| 6.0 | C1_Combined_ALK | 5 | 0.362 | 663.7 | 0.137 | {'epsilon': 1.5, 'alpha': 0.01} |
| 6.0 | C1_Combined_ALK | 10 | 0.033 | 666.6 | 0.461 | {'epsilon': 1.5, 'alpha': 0.01} |
| 6.0 | C1_Combined_K_ALK | 5 | 0.361 | 664.9 | 0.139 | {'epsilon': 1.5, 'alpha': 0.01} |
| 6.0 | C1_Combined_K_ALK | 10 | 0.037 | 667.8 | 0.458 | {'epsilon': 1.5, 'alpha': 0.01} |

## 六、讨论

1. **Robust Linear Regression 表现**：在多个 ALK 方案中，HuberRegressor 的性能通常接近或略低于原五折全模型搜索中的最佳模型（如 Lasso、Random_Forest），这与 Tang et al. 2020 中 Robust Linear Regression 表现优异的结论不完全一致，说明任务目标（预测 AL vs 预测局部锥细胞密度）和数据特征差异显著。
2. **五折 vs 十折**：十折 CV 的测试集更小（约 4–5 subjects），估计方差更大，最佳 R² 通常低于五折；但十折对过拟合的惩罚更严格，结果更谨慎。
3. **ALK 方案比较**：C1_Combined_ALK 与 C1_Combined_K_ALK 通常仍表现最好，与前期结论一致；B_Clinical_ALK 类方案因缺少 AL，性能相对较弱。
4. **应用建议**：若追求可解释性和稳健性，Robust Linear Regression 是合理选择；若追求峰值 R²，仍需考虑 Lasso / ElasticNet / Random_Forest。

---

*Report generated automatically by SR_ML_ALK_RobustLinear_5fold_10fold_tuning.py*
