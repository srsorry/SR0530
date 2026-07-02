"""
SR0530: 视锥细胞密度受眼部参数影响的空间异质性分析
基于 Gemini 方法论：OLS统计筛选 + XGBoost机器学习预测 + SHAP解释
"""

import pandas as pd
import numpy as np
import os
import warnings
warnings.filterwarnings('ignore')

import matplotlib.pyplot as plt

# 全局字体设置：Calibri 为首选，中文回退
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['font.sans-serif'] = ['Calibri', 'SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score, mean_squared_error
import xgboost as xgb
import statsmodels.api as sm
import shap

# ==========================================
# 0. 路径配置
# ==========================================
DATA_PATH = "orgData/orgData.csv"
OUT_DIR = "genData/sum"
os.makedirs(OUT_DIR, exist_ok=True)

# ==========================================
# 1. 数据加载与预处理
# ==========================================
print("=" * 70)
print("Step 1: 数据加载与预处理")
print("=" * 70)

df = pd.read_csv(DATA_PATH)
print(f"原始数据: {df.shape[0]} 只眼 × {df.shape[1]} 列")

# 眼部参数定义
oc_params = {
    'AL': 'Axial length (mm)',
    'ACD': 'Anterior chamber depth (mm)',
    'CC': 'Cornea curvature (mm)',
    'Age': 'Age',
    'SE': 'Spherical equivalent refraction (D)',
}
covariates = ['Gender', 'Source_Class']

# 处理缺失值：中位数填充
for col in oc_params.values():
    if df[col].isna().sum() > 0:
        med = df[col].median()
        df[col].fillna(med, inplace=True)
        print(f"  --> {col}: 缺失 {df[col].isna().sum()} 个，已用中位数 {med:.2f} 填充")

# 构建 11 个距离组（1.0 ~ 6.0 mm，步长 0.5）
# 每个距离组 = 4个象限在该距离上的平均密度（排除BVR>0.25）
distance_map = {}
for roi in range(1, 45):
    k = (roi - 1) % 11
    dist = 1.0 + k * 0.5
    if dist not in distance_map:
        distance_map[dist] = []
    distance_map[dist].append(roi)

distances = sorted(distance_map.keys())  # [1.0, 1.5, ..., 6.0]
print(f"距离组: {distances} mm (共 {len(distances)} 组)")

# 为每个距离组计算平均Cone Density（仅使用BVR<=0.25的数据）
density_cols = {}
for dist in distances:
    rois = distance_map[dist]
    col_name = f'Density_Dist_{dist:.1f}'
    density_vals = []
    for _, row in df.iterrows():
        valid_densities = []
        for roi in rois:
            bvr = row.get(f'Blood_Vessel_Ratio_ROI_{roi}', np.nan)
            den = row.get(f'Cone_Density_ROI_{roi}', np.nan)
            if pd.notna(bvr) and pd.notna(den) and bvr <= 0.25:
                valid_densities.append(den)
        density_vals.append(np.mean(valid_densities) if valid_densities else np.nan)
    df[col_name] = density_vals
    density_cols[dist] = col_name

# 统计各距离组有效样本
print("\n各距离组有效样本数:")
for dist in distances:
    valid_n = df[density_cols[dist]].notna().sum()
    print(f"  {dist:.1f}mm: {valid_n} 只眼")

# 仅保留所有距离组密度均有效的样本（用于公平比较）
valid_mask = df[list(density_cols.values())].notna().all(axis=1)
df_valid = df[valid_mask].copy()
print(f"\n全距离组均有效的样本: {len(df_valid)} 只眼")

# ==========================================
# 2. 数据标准化
# ==========================================
print("\n" + "=" * 70)
print("Step 2: 数据标准化 (Z-score)")
print("=" * 70)

feature_cols = list(oc_params.values()) + covariates
scaler_X = StandardScaler()
scaler_Y = StandardScaler()

X_raw = df_valid[feature_cols].values
Y_raw = df_valid[list(density_cols.values())].values

X_std = scaler_X.fit_transform(X_raw)
Y_std = scaler_Y.fit_transform(Y_raw)

feature_names_short = ['AL', 'ACD', 'CC', 'Age', 'SE', 'Gender', 'Source_Class']
df_X = pd.DataFrame(X_std, columns=feature_names_short)
df_X['Patient_ID'] = df_valid['Patient ID'].values

# ==========================================
# 3. 传统统计：11个OLS模型
# ==========================================
print("\n" + "=" * 70)
print("Step 3: 传统统计 - OLS多元线性回归")
print("=" * 70)

ols_results = []
for idx, dist in enumerate(distances):
    y = Y_std[:, idx]
    X = sm.add_constant(X_std, has_constant='add')
    
    model = sm.OLS(y, X).fit()
    
    # 提取AL的系数（AL是第1列，加上const后是第2列）
    al_beta = model.params[1]
    al_p = model.pvalues[1]
    al_t = model.tvalues[1]
    r2 = model.rsquared
    adj_r2 = model.rsquared_adj
    
    ols_results.append({
        'Distance': dist,
        'Beta_AL': al_beta,
        'P_AL': al_p,
        'T_AL': al_t,
        'R2': r2,
        'Adj_R2': adj_r2,
    })
    
    sig = "***" if al_p < 0.001 else "**" if al_p < 0.01 else "*" if al_p < 0.05 else ""
    print(f"  {dist:.1f}mm | beta_AL={al_beta:+.3f} | p={al_p:.4f} {sig:3s} | t={al_t:+.2f} | R2={r2:.3f}")

df_ols = pd.DataFrame(ols_results)

# 找出标准化beta绝对值最大的距离
best_dist_ols = df_ols.loc[df_ols['Beta_AL'].abs().idxmax(), 'Distance']
print(f"\n[OLS] AL效应最显著距离: {best_dist_ols} mm (|beta|最大)")

# ==========================================
# 4. 机器学习：11个XGBoost模型 (5折交叉验证)
# ==========================================
print("\n" + "=" * 70)
print("Step 4: 机器学习 - XGBoost回归 (5-Fold CV)")
print("=" * 70)

xgb_results = []
models = {}
shap_data = {}

kf = KFold(n_splits=5, shuffle=True, random_state=42)

for idx, dist in enumerate(distances):
    y = Y_raw[:, idx]  # 使用原始密度值
    
    fold_r2 = []
    fold_rmse = []
    best_r2 = -np.inf
    best_model = None
    best_X_test = None
    
    for train_idx, test_idx in kf.split(X_raw):
        X_train, X_test = X_raw[train_idx], X_raw[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        model = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=3,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            objective='reg:squarederror',
            n_jobs=4,
        )
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        r2 = r2_score(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        fold_r2.append(r2)
        fold_rmse.append(rmse)
        
        if r2 > best_r2:
            best_r2 = r2
            best_model = model
            best_X_test = X_test
    
    mean_r2 = np.mean(fold_r2)
    std_r2 = np.std(fold_r2)
    mean_rmse = np.mean(fold_rmse)
    
    xgb_results.append({
        'Distance': dist,
        'Mean_R2': mean_r2,
        'Std_R2': std_r2,
        'Mean_RMSE': mean_rmse,
    })
    
    models[dist] = best_model
    shap_data[dist] = best_X_test
    
    print(f"  {dist:.1f}mm | CV R2={mean_r2:.3f}+-{std_r2:.3f} | RMSE={mean_rmse:.1f}")

df_xgb = pd.DataFrame(xgb_results)

best_dist_xgb = df_xgb.loc[df_xgb['Mean_R2'].idxmax(), 'Distance']
print(f"\n[XGBoost] 预测力最强距离: {best_dist_xgb} mm (CV R2最高)")

# ==========================================
# 5. SHAP 分析 (针对最佳距离组)
# ==========================================
print("\n" + "=" * 70)
print("Step 5: SHAP 可解释性分析")
print("=" * 70)

best_model = models[best_dist_xgb]
best_X = shap_data[best_dist_xgb]

explainer = shap.TreeExplainer(best_model)
shap_values = explainer.shap_values(best_X)

# 计算平均绝对SHAP值（特征重要性）
mean_shap = np.abs(shap_values).mean(axis=0)
shap_importance = pd.DataFrame({
    'Feature': feature_names_short,
    'Mean_SHAP': mean_shap
}).sort_values('Mean_SHAP', ascending=False)

print(f"\n距离 {best_dist_xgb}mm 的 SHAP 特征重要性:")
for _, row in shap_importance.iterrows():
    print(f"  {row['Feature']:<15s} | {row['Mean_SHAP']:.3f}")

# ==========================================
# 6. 可视化
# ==========================================
print("\n" + "=" * 70)
print("Step 6: 生成可视化图表")
print("=" * 70)

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('SR0530: Spatial Heterogeneity of Cone Density Response to Ocular Parameters', 
             fontsize=13, fontweight='bold')

# ---- Plot 1: 标准化beta_AL 随距离变化 ----
ax1 = axes[0, 0]
colors = ['#e74c3c' if p < 0.05 else '#95a5a6' for p in df_ols['P_AL']]
bars = ax1.bar(df_ols['Distance'].astype(str), df_ols['Beta_AL'], color=colors, edgecolor='black', linewidth=0.5)
ax1.axhline(0, color='black', linewidth=0.8)
ax1.set_xlabel('Distance from Fovea (mm)', fontsize=10)
ax1.set_ylabel('Standardized beta (Axial Length)', fontsize=10)
ax1.set_title('A. OLS: Standardized beta of AL across Distances', fontsize=11, fontweight='bold')
ax1.tick_params(axis='x', rotation=45)
# 标注最显著的点
max_idx = df_ols['Beta_AL'].abs().idxmax()
ax1.annotate(f"Peak: {df_ols.loc[max_idx, 'Distance']}mm\nbeta={df_ols.loc[max_idx, 'Beta_AL']:.3f}",
             xy=(max_idx, df_ols.loc[max_idx, 'Beta_AL']),
             xytext=(max_idx, df_ols.loc[max_idx, 'Beta_AL'] + 0.15),
             arrowprops=dict(arrowstyle='->', color='red'),
             fontsize=9, color='red', ha='center')

# ---- Plot 2: OLS R2 vs XGBoost R2 对比 ----
ax2 = axes[0, 1]
ax2.plot(df_ols['Distance'], df_ols['R2'], 'o-', color='#3498db', label='OLS R2', linewidth=2, markersize=6)
ax2.plot(df_xgb['Distance'], df_xgb['Mean_R2'], 's--', color='#e74c3c', label='XGBoost CV R2', linewidth=2, markersize=6)
ax2.fill_between(df_xgb['Distance'], 
                 df_xgb['Mean_R2'] - df_xgb['Std_R2'], 
                 df_xgb['Mean_R2'] + df_xgb['Std_R2'], 
                 color='#e74c3c', alpha=0.15)
ax2.set_xlabel('Distance from Fovea (mm)', fontsize=10)
ax2.set_ylabel('R2 (Coefficient of Determination)', fontsize=10)
ax2.set_title('B. Predictive Power: OLS vs XGBoost', fontsize=11, fontweight='bold')
ax2.legend(loc='best')
ax2.set_ylim(0, max(df_ols['R2'].max(), df_xgb['Mean_R2'].max()) * 1.2)
# 标注峰值
peak_xgb_idx = df_xgb['Mean_R2'].idxmax()
ax2.annotate(f"Peak: {df_xgb.loc[peak_xgb_idx, 'Distance']}mm\nR2={df_xgb.loc[peak_xgb_idx, 'Mean_R2']:.3f}",
             xy=(df_xgb.loc[peak_xgb_idx, 'Distance'], df_xgb.loc[peak_xgb_idx, 'Mean_R2']),
             xytext=(df_xgb.loc[peak_xgb_idx, 'Distance'] + 0.5, df_xgb.loc[peak_xgb_idx, 'Mean_R2'] + 0.05),
             arrowprops=dict(arrowstyle='->', color='red'),
             fontsize=9, color='red')

# ---- Plot 3: 象限-距离 热力图 (AL的beta系数) ----
# 先计算每个单独ROI的OLS结果，然后做热力图
ax3 = axes[1, 0]
roi_beta_map = np.full((4, 11), np.nan)
for roi in range(1, 45):
    q = (roi - 1) // 11
    k = (roi - 1) % 11
    dist = 1.0 + k * 0.5
    
    den_col = f'Cone_Density_ROI_{roi}'
    bvr_col = f'Blood_Vessel_Ratio_ROI_{roi}'
    
    # 过滤有效数据
    mask = (df[den_col].notna()) & (df[bvr_col] <= 0.25)
    df_roi = df[mask]
    if len(df_roi) < 10:
        continue
    
    y_roi = df_roi[den_col].values
    X_roi = df_roi[feature_cols].values
    
    # 标准化
    scaler_roi = StandardScaler()
    X_roi_s = scaler_roi.fit_transform(X_roi)
    y_roi_s = (y_roi - y_roi.mean()) / y_roi.std()
    
    X_roi_s = sm.add_constant(X_roi_s, has_constant='add')
    try:
        m = sm.OLS(y_roi_s, X_roi_s).fit()
        roi_beta_map[q, k] = m.params[1]  # AL系数
    except:
        pass

im = ax3.imshow(roi_beta_map, cmap='RdBu_r', aspect='auto', vmin=-0.8, vmax=0.8)
ax3.set_yticks(range(4))
ax3.set_yticklabels(['Q1', 'Q2', 'Q3', 'Q4'])
ax3.set_xticks(range(11))
ax3.set_xticklabels([f'{1.0 + i*0.5:.1f}' for i in range(11)])
ax3.set_xlabel('Distance from Fovea (mm)', fontsize=10)
ax3.set_ylabel('Quadrant', fontsize=10)
ax3.set_title('C. AL Effect Heatmap (Standardized beta)', fontsize=11, fontweight='bold')
plt.colorbar(im, ax=ax3, label='beta (AL)')

# ---- Plot 4: SHAP Summary Plot ----
ax4 = axes[1, 1]
# 画SHAP特征重要性柱状图
shap_importance_sorted = shap_importance.sort_values('Mean_SHAP', ascending=True)
ax4.barh(shap_importance_sorted['Feature'], shap_importance_sorted['Mean_SHAP'], color='#2ecc71', edgecolor='black')
ax4.set_xlabel('Mean |SHAP Value|', fontsize=10)
ax4.set_title(f'D. SHAP Importance at {best_dist_xgb}mm (Best Predictive Distance)', fontsize=11, fontweight='bold')

plt.tight_layout(rect=[0, 0.03, 1, 0.95])
fig_path = os.path.join(OUT_DIR, "SR0530_Analysis_Overview.png")
plt.savefig(fig_path, dpi=300, bbox_inches='tight')
print(f"  --> 综合图表已保存: {fig_path}")

# ---- SHAP Summary Plot (详细版) ----
fig2, ax_shap = plt.subplots(figsize=(10, 6))
shap.summary_plot(shap_values, best_X, feature_names=feature_names_short, show=False)
fig2_path = os.path.join(OUT_DIR, "SR0530_SHAP_Summary.png")
plt.tight_layout()
plt.savefig(fig2_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"  --> SHAP详细图已保存: {fig2_path}")

# ==========================================
# 7. 保存结果表格
# ==========================================
print("\n" + "=" * 70)
print("Step 7: 保存结果表格")
print("=" * 70)

# 合并结果
df_summary = pd.merge(df_ols, df_xgb, on='Distance')
df_summary = df_summary[['Distance', 'Beta_AL', 'P_AL', 'T_AL', 'R2', 'Mean_R2', 'Std_R2']]
df_summary.columns = ['Distance(mm)', 'Beta_AL', 'P_AL', 'T_AL', 'OLS_R2', 'XGB_CV_R2', 'XGB_CV_R2_std']

csv_path = os.path.join(OUT_DIR, "SR0530_Results_Summary.csv")
df_summary.to_csv(csv_path, index=False, encoding='utf-8-sig')
print(f"  --> 结果汇总表: {csv_path}")

shap_path = os.path.join(OUT_DIR, "SR0530_SHAP_Importance.csv")
shap_importance.to_csv(shap_path, index=False, encoding='utf-8-sig')
print(f"  --> SHAP重要性表: {shap_path}")

print("\n" + "=" * 70)
print("分析完成！")
print("=" * 70)
