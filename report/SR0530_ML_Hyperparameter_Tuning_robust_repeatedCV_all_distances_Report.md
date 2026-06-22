# SR0530 稳健性超参数寻优报告（robust_repeatedCV_all_distances）

> **目标**：使用重复交叉验证（Repeated GroupKFold）重新评估各方案，降低 fold split 随机性带来的选择偏倚。

> **方法**：Random Search + 5-fold GroupKFold × 5 repeats，每模型 15 组参数

> **数据**：lenient（71 眼 / 46 subjects），Distance = 1.0–6.0 mm

> **置信区间**：基于 25 个 fold-level R²（5 seeds × 5 folds）估算 95% CI。

---

## 一、总体最佳配置（稳健性评估，所有距离）

- **距离**：1.5 mm
- **方案**：C1_Combined_ALK
- **模型**：ElasticNet
- **Mean Test R²**：0.395 [95% CI: 0.274, 0.515]
- **Std Test R²**：0.292
- **Mean Gap**：0.196
- **最佳参数**：{'alpha': 1.0, 'l1_ratio': 0.7}
- **样本量**：71 眼 / 46 subjects

## 二、各距离最佳配置

| 距离 (mm) | 最佳方案 | 最佳模型 | Mean Test R² (95% CI) | Std | Gap | 最佳参数 |
|-----------|---------|---------|----------------------|-----|-----|---------|
| 1.0 | C1_Combined_ALK | ElasticNet | 0.362 [0.235, 0.488] | 0.307 | 0.146 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 1.5 | C1_Combined_ALK | ElasticNet | 0.395 [0.274, 0.515] | 0.292 | 0.196 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| 2.0 | A2_Biomechanical_K_ALK | ElasticNet | 0.364 [0.281, 0.447] | 0.201 | 0.185 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| 2.5 | A2_Biomechanical_K_ALK | ElasticNet | 0.206 [0.078, 0.333] | 0.309 | 0.241 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 3.0 | A2_Biomechanical_ALK | Lasso | 0.315 [0.179, 0.450] | 0.328 | 0.272 | {'alpha': 10.0} |
| 3.5 | A2_Biomechanical_K_ALK | ElasticNet | 0.219 [0.047, 0.391] | 0.417 | 0.253 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| 4.0 | A2_Biomechanical_ALK | ElasticNet | 0.158 [0.063, 0.252] | 0.229 | 0.247 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 4.5 | A2_Biomechanical_K_ALK | ElasticNet | 0.124 [-0.007, 0.254] | 0.316 | 0.282 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 5.0 | C1_Combined_ALK | ElasticNet | 0.195 [0.073, 0.317] | 0.295 | 0.233 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 5.5 | C1_Combined_ALK | ElasticNet | 0.216 [0.110, 0.322] | 0.256 | 0.215 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 6.0 | A1_Biomechanical_Core_K | Neural_Network | 0.194 [0.110, 0.278] | 0.204 | 0.313 | {'hidden_layer_sizes': (100,), 'alpha': 0.1, 'learning_rate_init': 0.001} |

## 三、每个方案在每个距离的最佳模型

| 距离 (mm) | 方案 | 最佳模型 | Mean Test R² (95% CI) | Std | Gap | 最佳参数 |
|-----------|------|---------|----------------------|-----|-----|---------|
| 1.0 | A1_Biomechanical_Core | XGBoost | 0.264 [0.141, 0.388] | 0.299 | 0.334 | {'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 1.0, 'reg_lambda': 2.0} |
| 1.5 | A1_Biomechanical_Core | ElasticNet | 0.269 [0.132, 0.406] | 0.331 | 0.216 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| 2.0 | A1_Biomechanical_Core | ElasticNet | 0.261 [0.161, 0.362] | 0.244 | 0.164 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| 2.5 | A1_Biomechanical_Core | ElasticNet | 0.147 [0.041, 0.254] | 0.258 | 0.183 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 3.0 | A1_Biomechanical_Core | Ridge | 0.228 [0.101, 0.356] | 0.308 | 0.167 | {'alpha': 0.1} |
| 3.5 | A1_Biomechanical_Core | Ridge | 0.169 [0.026, 0.312] | 0.346 | 0.166 | {'alpha': 0.1} |
| 4.0 | A1_Biomechanical_Core | ElasticNet | 0.095 [0.014, 0.176] | 0.197 | 0.184 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 4.5 | A1_Biomechanical_Core | ElasticNet | 0.076 [-0.036, 0.188] | 0.271 | 0.204 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 5.0 | A1_Biomechanical_Core | Ridge | 0.087 [-0.084, 0.257] | 0.413 | 0.283 | {'alpha': 0.1} |
| 5.5 | A1_Biomechanical_Core | ElasticNet | 0.138 [0.056, 0.221] | 0.200 | 0.201 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 6.0 | A1_Biomechanical_Core | Ridge | 0.081 [-0.057, 0.220] | 0.335 | 0.267 | {'alpha': 0.1} |
| 1.0 | A1_Biomechanical_Core_K | XGBoost | 0.350 [0.260, 0.441] | 0.220 | 0.291 | {'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 1.0, 'reg_lambda': 2.0} |
| 1.5 | A1_Biomechanical_Core_K | Neural_Network | 0.384 [0.279, 0.490] | 0.256 | 0.180 | {'hidden_layer_sizes': (100,), 'alpha': 1.0, 'learning_rate_init': 0.001} |
| 2.0 | A1_Biomechanical_Core_K | Neural_Network | 0.310 [0.199, 0.421] | 0.270 | 0.250 | {'hidden_layer_sizes': (40,), 'alpha': 0.5, 'learning_rate_init': 0.001} |
| 2.5 | A1_Biomechanical_Core_K | ElasticNet | 0.185 [0.076, 0.294] | 0.264 | 0.191 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 3.0 | A1_Biomechanical_Core_K | Ridge | 0.240 [0.095, 0.384] | 0.350 | 0.178 | {'alpha': 0.1} |
| 3.5 | A1_Biomechanical_Core_K | Ridge | 0.155 [-0.009, 0.318] | 0.395 | 0.197 | {'alpha': 0.1} |
| 4.0 | A1_Biomechanical_Core_K | SVM | 0.105 [0.040, 0.169] | 0.156 | 0.130 | {'C': 2000, 'epsilon': 300, 'gamma': 0.005} |
| 4.5 | A1_Biomechanical_Core_K | Neural_Network | 0.107 [-0.050, 0.263] | 0.379 | 0.434 | {'hidden_layer_sizes': (80, 40), 'alpha': 1.0, 'learning_rate_init': 0.0001} |
| 5.0 | A1_Biomechanical_Core_K | ElasticNet | 0.133 [0.005, 0.260] | 0.308 | 0.256 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 5.5 | A1_Biomechanical_Core_K | ElasticNet | 0.175 [0.079, 0.270] | 0.231 | 0.219 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 6.0 | A1_Biomechanical_Core_K | Neural_Network | 0.194 [0.110, 0.278] | 0.204 | 0.313 | {'hidden_layer_sizes': (100,), 'alpha': 0.1, 'learning_rate_init': 0.001} |
| 1.0 | A1_Biomechanical_ALK | ElasticNet | 0.298 [0.136, 0.459] | 0.390 | 0.168 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 1.5 | A1_Biomechanical_ALK | ElasticNet | 0.387 [0.271, 0.503] | 0.281 | 0.182 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| 2.0 | A1_Biomechanical_ALK | ElasticNet | 0.318 [0.223, 0.413] | 0.231 | 0.172 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| 2.5 | A1_Biomechanical_ALK | Neural_Network | 0.199 [0.105, 0.293] | 0.228 | 0.286 | {'hidden_layer_sizes': (80, 40), 'alpha': 1.0, 'learning_rate_init': 0.0001} |
| 3.0 | A1_Biomechanical_ALK | ElasticNet | 0.261 [0.152, 0.370] | 0.265 | 0.078 | {'alpha': 1.0, 'l1_ratio': 0.1} |
| 3.5 | A1_Biomechanical_ALK | SVM | 0.165 [0.068, 0.262] | 0.235 | 0.101 | {'C': 2000, 'epsilon': 300, 'gamma': 0.005} |
| 4.0 | A1_Biomechanical_ALK | SVM | 0.132 [0.064, 0.201] | 0.165 | 0.119 | {'C': 2000, 'epsilon': 300, 'gamma': 0.005} |
| 4.5 | A1_Biomechanical_ALK | ElasticNet | 0.116 [0.012, 0.219] | 0.251 | 0.233 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 5.0 | A1_Biomechanical_ALK | ElasticNet | 0.137 [-0.005, 0.280] | 0.345 | 0.255 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 5.5 | A1_Biomechanical_ALK | ElasticNet | 0.186 [0.087, 0.286] | 0.241 | 0.218 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 6.0 | A1_Biomechanical_ALK | SVM | 0.132 [-0.049, 0.312] | 0.437 | 0.356 | {'C': 5000, 'epsilon': 300, 'gamma': 0.03} |
| 1.0 | A1_Biomechanical_K_ALK | Random_Forest | 0.304 [0.217, 0.391] | 0.211 | 0.405 | {'n_estimators': 200, 'max_depth': 5, 'min_samples_split': 2, 'min_samples_leaf': 4} |
| 1.5 | A1_Biomechanical_K_ALK | ElasticNet | 0.382 [0.269, 0.496] | 0.275 | 0.190 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| 2.0 | A1_Biomechanical_K_ALK | ElasticNet | 0.304 [0.205, 0.402] | 0.238 | 0.190 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| 2.5 | A1_Biomechanical_K_ALK | ElasticNet | 0.182 [0.060, 0.304] | 0.296 | 0.208 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 3.0 | A1_Biomechanical_K_ALK | Neural_Network | 0.285 [0.162, 0.407] | 0.296 | 0.208 | {'hidden_layer_sizes': (80, 40), 'alpha': 1.0, 'learning_rate_init': 0.0001} |
| 3.5 | A1_Biomechanical_K_ALK | SVM | 0.157 [0.050, 0.263] | 0.258 | 0.113 | {'C': 2000, 'epsilon': 300, 'gamma': 0.005} |
| 4.0 | A1_Biomechanical_K_ALK | SVM | 0.119 [0.055, 0.184] | 0.157 | 0.136 | {'C': 2000, 'epsilon': 300, 'gamma': 0.005} |
| 4.5 | A1_Biomechanical_K_ALK | ElasticNet | 0.098 [-0.014, 0.209] | 0.270 | 0.260 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 5.0 | A1_Biomechanical_K_ALK | ElasticNet | 0.130 [-0.017, 0.278] | 0.358 | 0.274 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 5.5 | A1_Biomechanical_K_ALK | ElasticNet | 0.176 [0.064, 0.287] | 0.269 | 0.234 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 6.0 | A1_Biomechanical_K_ALK | SVM | 0.148 [-0.030, 0.326] | 0.432 | 0.359 | {'C': 5000, 'epsilon': 300, 'gamma': 0.03} |
| 1.0 | A2_Biomechanical_NoK | Random_Forest | 0.242 [0.117, 0.367] | 0.304 | 0.449 | {'n_estimators': 200, 'max_depth': 5, 'min_samples_split': 2, 'min_samples_leaf': 4} |
| 1.5 | A2_Biomechanical_NoK | Random_Forest | 0.283 [0.144, 0.422] | 0.336 | 0.417 | {'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 4} |
| 2.0 | A2_Biomechanical_NoK | ElasticNet | 0.198 [0.055, 0.341] | 0.347 | 0.265 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| 2.5 | A2_Biomechanical_NoK | ElasticNet | 0.084 [-0.058, 0.225] | 0.343 | 0.387 | {'alpha': 0.1, 'l1_ratio': 0.9} |
| 3.0 | A2_Biomechanical_NoK | SVM | 0.195 [0.105, 0.284] | 0.217 | 0.139 | {'C': 2000, 'epsilon': 300, 'gamma': 0.005} |
| 3.5 | A2_Biomechanical_NoK | ElasticNet | 0.120 [-0.027, 0.267] | 0.357 | 0.292 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| 4.0 | A2_Biomechanical_NoK | ElasticNet | 0.071 [-0.028, 0.170] | 0.240 | 0.271 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 4.5 | A2_Biomechanical_NoK | SVM | 0.041 [-0.069, 0.151] | 0.267 | 0.279 | {'C': 1000, 'epsilon': 500, 'gamma': 0.01} |
| 5.0 | A2_Biomechanical_NoK | XGBoost | 0.043 [-0.102, 0.189] | 0.352 | 0.524 | {'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 1.0, 'reg_lambda': 2.0} |
| 5.5 | A2_Biomechanical_NoK | XGBoost | 0.062 [-0.100, 0.223] | 0.392 | 0.527 | {'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 1.0, 'reg_lambda': 2.0} |
| 6.0 | A2_Biomechanical_NoK | XGBoost | 0.062 [-0.094, 0.217] | 0.378 | 0.518 | {'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 1.0, 'reg_lambda': 2.0} |
| 1.0 | A2_Biomechanical_WithK | XGBoost | 0.339 [0.245, 0.432] | 0.226 | 0.307 | {'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 1.0, 'reg_lambda': 2.0} |
| 1.5 | A2_Biomechanical_WithK | ElasticNet | 0.374 [0.258, 0.489] | 0.279 | 0.210 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| 2.0 | A2_Biomechanical_WithK | ElasticNet | 0.352 [0.275, 0.429] | 0.187 | 0.183 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| 2.5 | A2_Biomechanical_WithK | ElasticNet | 0.190 [0.075, 0.304] | 0.277 | 0.239 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 3.0 | A2_Biomechanical_WithK | Lasso | 0.298 [0.158, 0.437] | 0.338 | 0.289 | {'alpha': 10.0} |
| 3.5 | A2_Biomechanical_WithK | ElasticNet | 0.209 [0.048, 0.369] | 0.388 | 0.254 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| 4.0 | A2_Biomechanical_WithK | ElasticNet | 0.135 [0.032, 0.238] | 0.250 | 0.266 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 4.5 | A2_Biomechanical_WithK | ElasticNet | 0.105 [-0.019, 0.230] | 0.302 | 0.283 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 5.0 | A2_Biomechanical_WithK | Ridge | 0.131 [-0.004, 0.265] | 0.327 | 0.336 | {'alpha': 10.0} |
| 5.5 | A2_Biomechanical_WithK | ElasticNet | 0.153 [0.041, 0.266] | 0.272 | 0.265 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 6.0 | A2_Biomechanical_WithK | Ridge | 0.131 [-0.051, 0.312] | 0.440 | 0.320 | {'alpha': 10.0} |
| 1.0 | A2_Biomechanical_ALK | ElasticNet | 0.296 [0.144, 0.448] | 0.369 | 0.180 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 1.5 | A2_Biomechanical_ALK | ElasticNet | 0.368 [0.233, 0.503] | 0.328 | 0.225 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| 2.0 | A2_Biomechanical_ALK | ElasticNet | 0.354 [0.266, 0.441] | 0.212 | 0.188 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| 2.5 | A2_Biomechanical_ALK | ElasticNet | 0.193 [0.065, 0.321] | 0.310 | 0.244 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 3.0 | A2_Biomechanical_ALK | Lasso | 0.315 [0.179, 0.450] | 0.328 | 0.272 | {'alpha': 10.0} |
| 3.5 | A2_Biomechanical_ALK | ElasticNet | 0.219 [0.056, 0.382] | 0.394 | 0.248 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| 4.0 | A2_Biomechanical_ALK | ElasticNet | 0.158 [0.063, 0.252] | 0.229 | 0.247 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 4.5 | A2_Biomechanical_ALK | ElasticNet | 0.115 [-0.010, 0.240] | 0.303 | 0.275 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 5.0 | A2_Biomechanical_ALK | ElasticNet | 0.125 [-0.003, 0.252] | 0.308 | 0.305 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 5.5 | A2_Biomechanical_ALK | ElasticNet | 0.166 [0.052, 0.280] | 0.276 | 0.261 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 6.0 | A2_Biomechanical_ALK | Ridge | 0.111 [-0.076, 0.298] | 0.453 | 0.334 | {'alpha': 10.0} |
| 1.0 | A2_Biomechanical_K_ALK | Random_Forest | 0.306 [0.215, 0.397] | 0.220 | 0.418 | {'n_estimators': 200, 'max_depth': 5, 'min_samples_split': 2, 'min_samples_leaf': 4} |
| 1.5 | A2_Biomechanical_K_ALK | ElasticNet | 0.393 [0.279, 0.508] | 0.278 | 0.206 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| 2.0 | A2_Biomechanical_K_ALK | ElasticNet | 0.364 [0.281, 0.447] | 0.201 | 0.185 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| 2.5 | A2_Biomechanical_K_ALK | ElasticNet | 0.206 [0.078, 0.333] | 0.309 | 0.241 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 3.0 | A2_Biomechanical_K_ALK | Lasso | 0.304 [0.166, 0.442] | 0.335 | 0.284 | {'alpha': 10.0} |
| 3.5 | A2_Biomechanical_K_ALK | ElasticNet | 0.219 [0.047, 0.391] | 0.417 | 0.253 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| 4.0 | A2_Biomechanical_K_ALK | ElasticNet | 0.151 [0.037, 0.266] | 0.277 | 0.265 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 4.5 | A2_Biomechanical_K_ALK | ElasticNet | 0.124 [-0.007, 0.254] | 0.316 | 0.282 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 5.0 | A2_Biomechanical_K_ALK | ElasticNet | 0.151 [0.026, 0.276] | 0.304 | 0.297 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 5.5 | A2_Biomechanical_K_ALK | ElasticNet | 0.177 [0.061, 0.294] | 0.282 | 0.259 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 6.0 | A2_Biomechanical_K_ALK | Ridge | 0.123 [-0.074, 0.320] | 0.478 | 0.332 | {'alpha': 10.0} |
| 1.0 | B_Clinical | XGBoost | 0.126 [-0.010, 0.261] | 0.328 | 0.332 | {'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 30, 'reg_alpha': 2.0, 'reg_lambda': 0.5} |
| 1.5 | B_Clinical | Random_Forest | 0.191 [0.076, 0.306] | 0.278 | 0.423 | {'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 4} |
| 2.0 | B_Clinical | Random_Forest | 0.073 [-0.078, 0.224] | 0.365 | 0.478 | {'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 4} |
| 2.5 | B_Clinical | Neural_Network | -0.101 [-0.274, 0.072] | 0.419 | 0.391 | {'hidden_layer_sizes': (80,), 'alpha': 1.0, 'learning_rate_init': 0.0001} |
| 3.0 | B_Clinical | SVM | 0.032 [-0.142, 0.206] | 0.422 | 0.384 | {'C': 5000, 'epsilon': 300, 'gamma': 0.03} |
| 3.5 | B_Clinical | SVM | -0.014 [-0.168, 0.140] | 0.373 | 0.364 | {'C': 5000, 'epsilon': 300, 'gamma': 0.03} |
| 4.0 | B_Clinical | Neural_Network | -0.067 [-0.217, 0.083] | 0.364 | 0.343 | {'hidden_layer_sizes': (80,), 'alpha': 1.0, 'learning_rate_init': 0.0001} |
| 4.5 | B_Clinical | XGBoost | -0.047 [-0.158, 0.064] | 0.269 | 0.356 | {'learning_rate': 0.01, 'max_depth': 3, 'n_estimators': 50, 'reg_alpha': 2.0, 'reg_lambda': 2.0} |
| 5.0 | B_Clinical | XGBoost | 0.027 [-0.141, 0.194] | 0.406 | 0.633 | {'learning_rate': 0.05, 'max_depth': 2, 'n_estimators': 50, 'reg_alpha': 0.5, 'reg_lambda': 2.0} |
| 5.5 | B_Clinical | SVM | 0.112 [-0.045, 0.269] | 0.381 | 0.372 | {'C': 5000, 'epsilon': 300, 'gamma': 0.03} |
| 6.0 | B_Clinical | SVM | 0.006 [-0.159, 0.171] | 0.400 | 0.428 | {'C': 5000, 'epsilon': 300, 'gamma': 0.03} |
| 1.0 | B_Clinical_K | Random_Forest | 0.174 [-0.053, 0.402] | 0.552 | 0.491 | {'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 4} |
| 1.5 | B_Clinical_K | Random_Forest | 0.181 [0.037, 0.324] | 0.348 | 0.494 | {'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 4} |
| 2.0 | B_Clinical_K | Random_Forest | 0.051 [-0.107, 0.209] | 0.384 | 0.554 | {'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 4} |
| 2.5 | B_Clinical_K | ElasticNet | -0.040 [-0.203, 0.123] | 0.395 | 0.289 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 3.0 | B_Clinical_K | SVM | -0.056 [-0.289, 0.177] | 0.564 | 0.518 | {'C': 5000, 'epsilon': 300, 'gamma': 0.03} |
| 3.5 | B_Clinical_K | SVM | -0.033 [-0.176, 0.111] | 0.348 | 0.421 | {'C': 5000, 'epsilon': 300, 'gamma': 0.03} |
| 4.0 | B_Clinical_K | SVM | -0.080 [-0.125, -0.035] | 0.109 | 0.105 | {'C': 100, 'epsilon': 500, 'gamma': 0.01} |
| 4.5 | B_Clinical_K | Neural_Network | -0.044 [-0.231, 0.143] | 0.453 | 0.398 | {'hidden_layer_sizes': (100,), 'alpha': 1.0, 'learning_rate_init': 0.0001} |
| 5.0 | B_Clinical_K | SVM | 0.026 [-0.190, 0.241] | 0.523 | 0.517 | {'C': 5000, 'epsilon': 300, 'gamma': 0.03} |
| 5.5 | B_Clinical_K | SVM | 0.114 [-0.041, 0.269] | 0.376 | 0.413 | {'C': 5000, 'epsilon': 300, 'gamma': 0.03} |
| 6.0 | B_Clinical_K | SVM | 0.050 [-0.131, 0.230] | 0.438 | 0.446 | {'C': 5000, 'epsilon': 300, 'gamma': 0.03} |
| 1.0 | B_Clinical_ALK | ElasticNet | 0.285 [0.121, 0.448] | 0.395 | 0.175 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 1.5 | B_Clinical_ALK | Ridge | 0.298 [0.163, 0.434] | 0.328 | 0.220 | {'alpha': 10.0} |
| 2.0 | B_Clinical_ALK | ElasticNet | 0.258 [0.152, 0.364] | 0.257 | 0.223 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| 2.5 | B_Clinical_ALK | ElasticNet | 0.104 [-0.014, 0.222] | 0.285 | 0.248 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 3.0 | B_Clinical_ALK | Lasso | 0.124 [-0.026, 0.273] | 0.363 | 0.278 | {'alpha': 10.0} |
| 3.5 | B_Clinical_ALK | ElasticNet | 0.094 [-0.160, 0.348] | 0.615 | 0.267 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| 4.0 | B_Clinical_ALK | ElasticNet | 0.012 [-0.149, 0.173] | 0.390 | 0.288 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 4.5 | B_Clinical_ALK | ElasticNet | 0.031 [-0.109, 0.171] | 0.340 | 0.307 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 5.0 | B_Clinical_ALK | ElasticNet | 0.120 [-0.057, 0.296] | 0.427 | 0.280 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 5.5 | B_Clinical_ALK | SVM | 0.137 [-0.013, 0.286] | 0.361 | 0.387 | {'C': 5000, 'epsilon': 300, 'gamma': 0.03} |
| 6.0 | B_Clinical_ALK | Random_Forest | 0.112 [-0.019, 0.243] | 0.317 | 0.540 | {'n_estimators': 200, 'max_depth': 5, 'min_samples_split': 2, 'min_samples_leaf': 4} |
| 1.0 | B_Clinical_K_ALK | Random_Forest | 0.265 [0.178, 0.353] | 0.213 | 0.426 | {'n_estimators': 200, 'max_depth': 5, 'min_samples_split': 2, 'min_samples_leaf': 4} |
| 1.5 | B_Clinical_K_ALK | Lasso | 0.335 [0.212, 0.457] | 0.297 | 0.234 | {'alpha': 0.01} |
| 2.0 | B_Clinical_K_ALK | ElasticNet | 0.239 [0.130, 0.349] | 0.265 | 0.242 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| 2.5 | B_Clinical_K_ALK | ElasticNet | 0.089 [-0.032, 0.210] | 0.294 | 0.263 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 3.0 | B_Clinical_K_ALK | Lasso | 0.219 [0.081, 0.358] | 0.336 | 0.207 | {'alpha': 0.01} |
| 3.5 | B_Clinical_K_ALK | Ridge | 0.113 [-0.044, 0.270] | 0.380 | 0.250 | {'alpha': 0.1} |
| 4.0 | B_Clinical_K_ALK | SVM | 0.000 [-0.089, 0.089] | 0.216 | 0.221 | {'C': 2000, 'epsilon': 300, 'gamma': 0.005} |
| 4.5 | B_Clinical_K_ALK | Neural_Network | 0.012 [-0.137, 0.162] | 0.363 | 0.484 | {'hidden_layer_sizes': (80, 40), 'alpha': 0.3, 'learning_rate_init': 0.0005} |
| 5.0 | B_Clinical_K_ALK | Neural_Network | 0.095 [-0.056, 0.247] | 0.368 | 0.515 | {'hidden_layer_sizes': (80, 40), 'alpha': 0.3, 'learning_rate_init': 0.0005} |
| 5.5 | B_Clinical_K_ALK | SVM | 0.146 [0.013, 0.280] | 0.324 | 0.403 | {'C': 5000, 'epsilon': 300, 'gamma': 0.03} |
| 6.0 | B_Clinical_K_ALK | SVM | 0.115 [-0.070, 0.299] | 0.446 | 0.414 | {'C': 5000, 'epsilon': 300, 'gamma': 0.03} |
| 1.0 | C1_Combined | ElasticNet | 0.347 [0.259, 0.436] | 0.215 | 0.121 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 1.5 | C1_Combined | ElasticNet | 0.292 [0.101, 0.482] | 0.462 | 0.253 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| 2.0 | C1_Combined | ElasticNet | 0.315 [0.221, 0.408] | 0.226 | 0.171 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| 2.5 | C1_Combined | ElasticNet | 0.115 [-0.014, 0.243] | 0.311 | 0.244 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 3.0 | C1_Combined | SVM | 0.175 [0.062, 0.288] | 0.274 | 0.113 | {'C': 2000, 'epsilon': 300, 'gamma': 0.005} |
| 3.5 | C1_Combined | ElasticNet | 0.133 [-0.079, 0.346] | 0.514 | 0.238 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| 4.0 | C1_Combined | ElasticNet | 0.091 [-0.004, 0.187] | 0.230 | 0.217 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 4.5 | C1_Combined | ElasticNet | 0.068 [-0.050, 0.185] | 0.285 | 0.255 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 5.0 | C1_Combined | ElasticNet | 0.173 [0.067, 0.278] | 0.256 | 0.213 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 5.5 | C1_Combined | ElasticNet | 0.199 [0.116, 0.283] | 0.201 | 0.199 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 6.0 | C1_Combined | ElasticNet | 0.065 [-0.058, 0.188] | 0.297 | 0.253 | {'alpha': 1.0, 'l1_ratio': 0.1} |
| 1.0 | C1_Combined_K | ElasticNet | 0.349 [0.225, 0.472] | 0.299 | 0.150 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 1.5 | C1_Combined_K | ElasticNet | 0.368 [0.237, 0.498] | 0.316 | 0.215 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| 2.0 | C1_Combined_K | ElasticNet | 0.331 [0.230, 0.432] | 0.244 | 0.180 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| 2.5 | C1_Combined_K | ElasticNet | 0.133 [0.004, 0.262] | 0.313 | 0.253 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 3.0 | C1_Combined_K | Ridge | 0.216 [0.076, 0.355] | 0.337 | 0.211 | {'alpha': 0.1} |
| 3.5 | C1_Combined_K | ElasticNet | 0.135 [-0.117, 0.387] | 0.611 | 0.256 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| 4.0 | C1_Combined_K | SVM | 0.071 [0.003, 0.138] | 0.163 | 0.179 | {'C': 2000, 'epsilon': 300, 'gamma': 0.005} |
| 4.5 | C1_Combined_K | ElasticNet | 0.063 [-0.063, 0.189] | 0.305 | 0.297 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 5.0 | C1_Combined_K | ElasticNet | 0.175 [0.046, 0.303] | 0.312 | 0.249 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 5.5 | C1_Combined_K | ElasticNet | 0.192 [0.082, 0.303] | 0.267 | 0.232 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 6.0 | C1_Combined_K | SVM | 0.131 [-0.038, 0.300] | 0.409 | 0.395 | {'C': 5000, 'epsilon': 300, 'gamma': 0.03} |
| 1.0 | C1_Combined_ALK | ElasticNet | 0.362 [0.235, 0.488] | 0.307 | 0.146 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 1.5 | C1_Combined_ALK | ElasticNet | 0.395 [0.274, 0.515] | 0.292 | 0.196 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| 2.0 | C1_Combined_ALK | ElasticNet | 0.348 [0.242, 0.454] | 0.258 | 0.169 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| 2.5 | C1_Combined_ALK | Neural_Network | 0.146 [0.078, 0.213] | 0.163 | 0.352 | {'hidden_layer_sizes': (80, 40), 'alpha': 1.0, 'learning_rate_init': 0.0001} |
| 3.0 | C1_Combined_ALK | Neural_Network | 0.235 [0.109, 0.361] | 0.305 | 0.252 | {'hidden_layer_sizes': (80, 40), 'alpha': 1.0, 'learning_rate_init': 0.0001} |
| 3.5 | C1_Combined_ALK | ElasticNet | 0.156 [-0.101, 0.413] | 0.622 | 0.239 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| 4.0 | C1_Combined_ALK | SVM | 0.105 [0.034, 0.175] | 0.170 | 0.154 | {'C': 2000, 'epsilon': 300, 'gamma': 0.005} |
| 4.5 | C1_Combined_ALK | ElasticNet | 0.088 [-0.033, 0.209] | 0.293 | 0.275 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 5.0 | C1_Combined_ALK | ElasticNet | 0.195 [0.073, 0.317] | 0.295 | 0.233 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 5.5 | C1_Combined_ALK | ElasticNet | 0.216 [0.110, 0.322] | 0.256 | 0.215 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 6.0 | C1_Combined_ALK | SVM | 0.129 [-0.055, 0.313] | 0.446 | 0.387 | {'C': 5000, 'epsilon': 300, 'gamma': 0.03} |
| 1.0 | C1_Combined_K_ALK | ElasticNet | 0.347 [0.204, 0.489] | 0.346 | 0.164 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 1.5 | C1_Combined_K_ALK | ElasticNet | 0.390 [0.268, 0.512] | 0.296 | 0.203 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| 2.0 | C1_Combined_K_ALK | ElasticNet | 0.335 [0.222, 0.448] | 0.274 | 0.183 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| 2.5 | C1_Combined_K_ALK | ElasticNet | 0.138 [-0.002, 0.278] | 0.340 | 0.259 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 3.0 | C1_Combined_K_ALK | SVM | 0.207 [0.082, 0.332] | 0.303 | 0.115 | {'C': 2000, 'epsilon': 300, 'gamma': 0.005} |
| 3.5 | C1_Combined_K_ALK | ElasticNet | 0.139 [-0.127, 0.406] | 0.645 | 0.258 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| 4.0 | C1_Combined_K_ALK | SVM | 0.091 [0.023, 0.160] | 0.167 | 0.172 | {'C': 2000, 'epsilon': 300, 'gamma': 0.005} |
| 4.5 | C1_Combined_K_ALK | ElasticNet | 0.066 [-0.065, 0.197] | 0.317 | 0.304 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 5.0 | C1_Combined_K_ALK | ElasticNet | 0.175 [0.039, 0.311] | 0.330 | 0.259 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 5.5 | C1_Combined_K_ALK | ElasticNet | 0.198 [0.079, 0.317] | 0.289 | 0.236 | {'alpha': 1.0, 'l1_ratio': 0.5} |
| 6.0 | C1_Combined_K_ALK | SVM | 0.135 [-0.037, 0.307] | 0.416 | 0.402 | {'C': 5000, 'epsilon': 300, 'gamma': 0.03} |

## 四、每个模型在所有方案/距离中的最佳表现

| 模型 | 最佳距离 | 最佳方案 | Mean Test R² (95% CI) | Gap | 最佳参数 |
|------|---------|---------|----------------------|-----|---------|
| ElasticNet | 1.5 mm | C1_Combined_ALK | 0.395 [0.274, 0.515] | 0.196 | {'alpha': 1.0, 'l1_ratio': 0.7} |
| Lasso | 1.5 mm | A2_Biomechanical_K_ALK | 0.339 [0.173, 0.505] | 0.301 | {'alpha': 1.0} |
| Neural_Network | 1.5 mm | A1_Biomechanical_Core_K | 0.384 [0.279, 0.490] | 0.180 | {'hidden_layer_sizes': (100,), 'alpha': 1.0, 'learning_rate_init': 0.001} |
| Random_Forest | 1.5 mm | A2_Biomechanical_ALK | 0.326 [0.189, 0.462] | 0.402 | {'n_estimators': 200, 'max_depth': None, 'min_samples_split': 10, 'min_samples_leaf': 4} |
| Ridge | 1.5 mm | A2_Biomechanical_K_ALK | 0.370 [0.236, 0.504] | 0.239 | {'alpha': 10.0} |
| SVM | 1.0 mm | C1_Combined_ALK | 0.291 [0.219, 0.363] | 0.165 | {'C': 1000, 'epsilon': 500, 'gamma': 0.01} |
| XGBoost | 1.0 mm | A1_Biomechanical_Core_K | 0.350 [0.260, 0.441] | 0.291 | {'learning_rate': 0.05, 'max_depth': 1, 'n_estimators': 100, 'reg_alpha': 1.0, 'reg_lambda': 2.0} |

## 五、基线 vs K vs AL/K vs K+ALK 对比（按方案族取最佳距离）

### A1 方案族

| 方案 | 最佳距离 | 最佳模型 | Mean Test R² | Std | Gap |
|------|---------|---------|-------------|-----|-----|
| A1_Biomechanical_Core | 1.5 mm | ElasticNet | 0.269 | 0.331 | 0.216 |
| A1_Biomechanical_Core_K | 1.5 mm | Neural_Network | 0.384 | 0.256 | 0.180 |
| A1_Biomechanical_ALK | 1.5 mm | ElasticNet | 0.387 | 0.281 | 0.182 |
| A1_Biomechanical_K_ALK | 1.5 mm | ElasticNet | 0.382 | 0.275 | 0.190 |

### A2 方案族

| 方案 | 最佳距离 | 最佳模型 | Mean Test R² | Std | Gap |
|------|---------|---------|-------------|-----|-----|
| A2_Biomechanical_NoK | 1.5 mm | Random_Forest | 0.283 | 0.336 | 0.417 |
| A2_Biomechanical_WithK | 1.5 mm | ElasticNet | 0.374 | 0.279 | 0.210 |
| A2_Biomechanical_ALK | 1.5 mm | ElasticNet | 0.368 | 0.328 | 0.225 |
| A2_Biomechanical_K_ALK | 1.5 mm | ElasticNet | 0.393 | 0.278 | 0.206 |

### B 方案族

| 方案 | 最佳距离 | 最佳模型 | Mean Test R² | Std | Gap |
|------|---------|---------|-------------|-----|-----|
| B_Clinical | 1.5 mm | Random_Forest | 0.191 | 0.278 | 0.423 |
| B_Clinical_K | 1.5 mm | Random_Forest | 0.181 | 0.348 | 0.494 |
| B_Clinical_ALK | 1.5 mm | Ridge | 0.298 | 0.328 | 0.220 |
| B_Clinical_K_ALK | 1.5 mm | Lasso | 0.335 | 0.297 | 0.234 |

### C1 方案族

| 方案 | 最佳距离 | 最佳模型 | Mean Test R² | Std | Gap |
|------|---------|---------|-------------|-----|-----|
| C1_Combined | 1.0 mm | ElasticNet | 0.347 | 0.215 | 0.121 |
| C1_Combined_K | 1.5 mm | ElasticNet | 0.368 | 0.316 | 0.215 |
| C1_Combined_ALK | 1.5 mm | ElasticNet | 0.395 | 0.292 | 0.196 |
| C1_Combined_K_ALK | 1.5 mm | ElasticNet | 0.390 | 0.296 | 0.203 |

## 六、按距离汇总的平均 R²（跨方案/模型）

| 距离 (mm) | 平均 Mean Test R² | 中位数 | 最佳方案 | 最佳模型 | 最佳 R² |
|-----------|------------------|--------|---------|---------|--------|
| 1.0 | 0.207 | 0.225 | C1_Combined_ALK | ElasticNet | 0.362 |
| 1.5 | 0.241 | 0.254 | C1_Combined_ALK | ElasticNet | 0.395 |
| 2.0 | 0.174 | 0.181 | A2_Biomechanical_K_ALK | ElasticNet | 0.364 |
| 2.5 | 0.039 | 0.044 | A2_Biomechanical_K_ALK | ElasticNet | 0.206 |
| 3.0 | 0.129 | 0.147 | A2_Biomechanical_ALK | Lasso | 0.315 |
| 3.5 | 0.059 | 0.084 | A2_Biomechanical_K_ALK | ElasticNet | 0.219 |
| 4.0 | -0.013 | -0.023 | A2_Biomechanical_ALK | ElasticNet | 0.158 |
| 4.5 | -0.020 | -0.020 | A2_Biomechanical_K_ALK | ElasticNet | 0.124 |
| 5.0 | 0.046 | 0.055 | C1_Combined_ALK | ElasticNet | 0.195 |
| 5.5 | 0.068 | 0.084 | C1_Combined_ALK | ElasticNet | 0.216 |
| 6.0 | 0.038 | 0.048 | A1_Biomechanical_Core_K | Neural_Network | 0.194 |

## 七、讨论

1. **重复 CV 显著降低了选择偏倚**：此前单 CV 的 0.6+ R² 在重复 CV 下降至更保守的水平。
2. **最佳距离和方案可能随距离变化**：不同偏心距下最优方案可能不同，需结合生理意义选择。
3. **最佳模型仍以线性模型为主**：ElasticNet / Lasso / Ridge 在多数距离表现稳健。
4. **K 与 AL/K 的优劣因距离而异**：需结合具体距离判断，不能一概而论。
5. **样本量仍是根本限制**：46 subjects 导致 95% CI 较宽，结论仍属探索性。

---

*Report generated automatically by SR_ML_hyperparameter_tuning_robust.py*
