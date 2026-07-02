"""
SR0530: 视锥细胞密度受眼部参数影响的空间异质性分析 v2
使用 CleanDataRoi 清洗数据
方法论: 按距离聚合4象限 -> OLS + XGBoost + SHAP
"""

import pandas as pd
import numpy as np
import os
import glob
import warnings
warnings.filterwarnings('ignore')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# 全局字体设置：Calibri 为首选，中文回退
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['font.sans-serif'] = ['Calibri', 'SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
# [FIXED] matplotlib.rcParams['font.sans-serif'] = ['Calibri', 'SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.impute import SimpleImputer
import xgboost as xgb
import statsmodels.api as sm
import shap

# ==========================================
# 0. 配置
# ==========================================
OUT_DIR = "genData/sum"
os.makedirs(OUT_DIR, exist_ok=True)

# ==========================================
# 1. 读取并聚合数据
# ==========================================
print("=" * 70)
print("Step 1: Reading CleanDataRoi and aggregating by distance")
print("=" * 70)

# 读取所有44个ROI文件
all_data = {}
for f in sorted(glob.glob('genData/CleanDataRoi/data*.csv')):
    df = pd.read_csv(f)
    dist = df['Eccentricity (mm)'].iloc[0]
    if dist not in all_data:
        all_data[dist] = []
    all_data[dist].append(df)

distances = sorted(all_data.keys())
print(f"Distances: {distances}")

# 对每个距离，找到共同Subject并计算4象限平均密度
distance_dfs = {}
for dist in distances:
    dfs = all_data[dist]
    
    # 以第一个象限为基础，获取眼部参数
    base = dfs[0][['Subject_ID', 'Axial length (mm)', 'Age', 
                   'Spherical equivalent refraction (D)', 'Gender',
                   'Corneal curvature (mm)', 'Anterior chamber depth (mm)']].copy()
    
    # 收集所有象限的密度
    density_cols = ['density_q1']
    base['density_q1'] = dfs[0]['Linear cone density (cones/ mm2)'].values
    
    for i, d in enumerate(dfs[1:], 2):
        base = base.merge(
            d[['Subject_ID', 'Linear cone density (cones/ mm2)']].rename(
                columns={'Linear cone density (cones/ mm2)': f'density_q{i}'}
            ),
            on='Subject_ID', how='inner'
        )
        density_cols.append(f'density_q{i}')
    
    # 计算4象限平均密度
    base['Mean_Density'] = base[density_cols].mean(axis=1)
    
    # 丢弃中间列
    base = base[['Subject_ID', 'Axial length (mm)', 'Age',
                 'Spherical equivalent refraction (D)', 'Gender',
                 'Corneal curvature (mm)', 'Anterior chamber depth (mm)',
                 'Mean_Density']]
    
    distance_dfs[dist] = base
    print(f"  {dist:.1f}mm: n={len(base)}, density_mean={base['Mean_Density'].mean():.1f}, std={base['Mean_Density'].std():.1f}")

# ==========================================
# 2. OLS 分析 (11个距离组)
# ==========================================
print("\n" + "=" * 70)
print("Step 2: OLS Multiple Linear Regression per Distance")
print("=" * 70)

feature_cols = ['Axial length (mm)', 'Anterior chamber depth (mm)',
                'Corneal curvature (mm)', 'Age',
                'Spherical equivalent refraction (D)', 'Gender']
feature_short = ['AL', 'ACD', 'CC', 'Age', 'SE', 'Gender']

ols_results = []
for dist in distances:
    df = distance_dfs[dist].copy()
    
    # 处理缺失值 (中位数填充)
    for col in feature_cols:
        if df[col].isna().any():
            df[col].fillna(df[col].median(), inplace=True)
    
    # 标准化
    scaler_X = StandardScaler()
    scaler_Y = StandardScaler()
    
    X = scaler_X.fit_transform(df[feature_cols].values)
    y = scaler_Y.fit_transform(df[['Mean_Density']].values).flatten()
    
    # OLS
    X_const = sm.add_constant(X, has_constant='add')
    model = sm.OLS(y, X_const).fit()
    
    al_beta = model.params[1]
    al_p = model.pvalues[1]
    al_t = model.tvalues[1]
    r2 = model.rsquared
    adj_r2 = model.rsquared_adj
    
    ols_results.append({
        'Distance': dist,
        'N': len(df),
        'Beta_AL': al_beta,
        'P_AL': al_p,
        'T_AL': al_t,
        'R2': r2,
        'Adj_R2': adj_r2,
    })
    
    sig = "***" if al_p < 0.001 else "**" if al_p < 0.01 else "*" if al_p < 0.05 else ""
    print(f"  {dist:.1f}mm N={len(df):2d} | beta_AL={al_beta:+.3f} | p={al_p:.4f} {sig:3s} | t={al_t:+.2f} | R2={r2:.3f}")

df_ols = pd.DataFrame(ols_results)

best_ols = df_ols.loc[df_ols['Beta_AL'].abs().idxmax()]
print(f"\n[OLS] AL effect peak: {best_ols['Distance']} mm (|beta|={best_ols['Beta_AL']:.3f}, p={best_ols['P_AL']:.4f})")

# ==========================================
# 3. XGBoost 分析 (11个距离组, 5-Fold CV)
# ==========================================
print("\n" + "=" * 70)
print("Step 3: XGBoost Regression per Distance (5-Fold CV)")
print("=" * 70)

xgb_results = []
models = {}
shap_data = {}

kf = KFold(n_splits=5, shuffle=True, random_state=42)

for dist in distances:
    df = distance_dfs[dist].copy()
    
    # 处理缺失值
    for col in feature_cols:
        if df[col].isna().any():
            df[col].fillna(df[col].median(), inplace=True)
    
    X = df[feature_cols].values
    y = df['Mean_Density'].values
    
    fold_r2 = []
    fold_rmse = []
    best_r2 = -np.inf
    best_model = None
    best_X_test = None
    
    for train_idx, test_idx in kf.split(X):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        model = xgb.XGBRegressor(
            n_estimators=50,
            max_depth=2,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=1.0,
            reg_lambda=1.0,
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
    
    print(f"  {dist:.1f}mm | CV R2={mean_r2:+.3f}+/-{std_r2:.3f} | RMSE={mean_rmse:.1f}")

df_xgb = pd.DataFrame(xgb_results)

# 找R2最高的（最接近0或正的）
# 由于可能全是负的，找最大的（最接近0的）
best_xgb_idx = df_xgb['Mean_R2'].idxmax()
best_dist_xgb = df_xgb.loc[best_xgb_idx, 'Distance']
print(f"\n[XGBoost] Best predictive distance: {best_dist_xgb} mm (CV R2={df_xgb.loc[best_xgb_idx, 'Mean_R2']:.3f})")

# ==========================================
# 4. SHAP 分析 (最佳距离组)
# ==========================================
print("\n" + "=" * 70)
print("Step 4: SHAP Explainability")
print("=" * 70)

best_model = models[best_dist_xgb]
best_X = shap_data[best_dist_xgb]

try:
    explainer = shap.TreeExplainer(best_model)
    shap_values = explainer.shap_values(best_X)
    
    mean_shap = np.abs(shap_values).mean(axis=0)
    shap_importance = pd.DataFrame({
        'Feature': feature_short,
        'Mean_SHAP': mean_shap
    }).sort_values('Mean_SHAP', ascending=False)
    
    print(f"\nSHAP importance at {best_dist_xgb}mm:")
    for _, row in shap_importance.iterrows():
        print(f"  {row['Feature']:<10s} | {row['Mean_SHAP']:.3f}")
    has_shap = True
except Exception as e:
    print(f"SHAP failed: {e}")
    has_shap = False
    shap_importance = None

# ==========================================
# 5. 可视化
# ==========================================
print("\n" + "=" * 70)
print("Step 5: Generating figures")
print("=" * 70)

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('SR0530: Spatial Heterogeneity of Cone Density vs Ocular Parameters', 
             fontsize=13, fontweight='bold')

# Plot 1: OLS beta_AL
ax1 = axes[0, 0]
colors = ['#e74c3c' if p < 0.05 else '#95a5a6' for p in df_ols['P_AL']]
bars = ax1.bar([str(d) for d in df_ols['Distance']], df_ols['Beta_AL'], 
               color=colors, edgecolor='black', linewidth=0.5)
ax1.axhline(0, color='black', linewidth=0.8)
ax1.set_xlabel('Distance from Fovea (mm)', fontsize=10)
ax1.set_ylabel('Standardized beta (Axial Length)', fontsize=10)
ax1.set_title('A. OLS: Standardized beta of AL', fontsize=11, fontweight='bold')
ax1.tick_params(axis='x', rotation=45)

max_idx = df_ols['Beta_AL'].abs().idxmax()
ax1.annotate(f"Peak: {df_ols.loc[max_idx, 'Distance']}mm\nbeta={df_ols.loc[max_idx, 'Beta_AL']:.3f}",
             xy=(max_idx, df_ols.loc[max_idx, 'Beta_AL']),
             xytext=(max_idx, df_ols.loc[max_idx, 'Beta_AL'] + 0.1),
             arrowprops=dict(arrowstyle='->', color='red'),
             fontsize=9, color='red', ha='center')

# Plot 2: R2 comparison
ax2 = axes[0, 1]
ax2.plot(df_ols['Distance'], df_ols['R2'], 'o-', color='#3498db', label='OLS R2', linewidth=2, markersize=6)
ax2.plot(df_xgb['Distance'], df_xgb['Mean_R2'], 's--', color='#e74c3c', label='XGBoost CV R2', linewidth=2, markersize=6)
ax2.fill_between(df_xgb['Distance'], 
                 df_xgb['Mean_R2'] - df_xgb['Std_R2'], 
                 df_xgb['Mean_R2'] + df_xgb['Std_R2'], 
                 color='#e74c3c', alpha=0.15)
ax2.set_xlabel('Distance from Fovea (mm)', fontsize=10)
ax2.set_ylabel('R2', fontsize=10)
ax2.set_title('B. Predictive Power: OLS vs XGBoost', fontsize=11, fontweight='bold')
ax2.legend(loc='best')
ax2.axhline(0, color='gray', linestyle='--', linewidth=0.8)

# Plot 3: t-value / significance
ax3 = axes[1, 0]
t_colors = ['#2ecc71' if p < 0.05 else '#95a5a6' for p in df_ols['P_AL']]
ax3.bar([str(d) for d in df_ols['Distance']], np.abs(df_ols['T_AL']), color=t_colors, edgecolor='black')
ax3.set_xlabel('Distance from Fovea (mm)', fontsize=10)
ax3.set_ylabel('|t-value| for AL', fontsize=10)
ax3.set_title('C. Statistical Significance of AL Effect', fontsize=11, fontweight='bold')
ax3.tick_params(axis='x', rotation=45)
ax3.axhline(1.96, color='red', linestyle='--', linewidth=1, label='p=0.05 threshold')
ax3.legend()

# Plot 4: SHAP or Feature correlation
ax4 = axes[1, 1]
if has_shap and shap_importance is not None:
    shap_sorted = shap_importance.sort_values('Mean_SHAP', ascending=True)
    ax4.barh(shap_sorted['Feature'], shap_sorted['Mean_SHAP'], color='#2ecc71', edgecolor='black')
    ax4.set_xlabel('Mean |SHAP|', fontsize=10)
    ax4.set_title(f'D. SHAP Importance at {best_dist_xgb}mm', fontsize=11, fontweight='bold')
else:
    # Fallback: show correlation heatmap at best distance
    df_best = distance_dfs[best_dist_xgb]
    corr_vals = df_best[feature_cols + ['Mean_Density']].corr()['Mean_Density'].drop('Mean_Density')
    corr_vals.index = feature_short
    corr_vals = corr_vals.sort_values(key=abs, ascending=True)
    colors = ['#e74c3c' if v < 0 else '#3498db' for v in corr_vals.values]
    ax4.barh(corr_vals.index, corr_vals.values, color=colors, edgecolor='black')
    ax4.set_xlabel('Pearson r', fontsize=10)
    ax4.set_title(f'D. Correlations at {best_dist_xgb}mm', fontsize=11, fontweight='bold')
    ax4.axvline(0, color='black', linewidth=0.8)

plt.tight_layout(rect=[0, 0.03, 1, 0.95])
fig_path = os.path.join(OUT_DIR, "SR0530_Analysis_Overview_v2.png")
plt.savefig(fig_path, dpi=300, bbox_inches='tight')
print(f"  --> Saved: {fig_path}")
plt.close()

# SHAP detailed plot
if has_shap:
    fig2, ax = plt.subplots(figsize=(10, 6))
    shap.summary_plot(shap_values, best_X, feature_names=feature_short, show=False)
    fig2_path = os.path.join(OUT_DIR, "SR0530_SHAP_Summary_v2.png")
    plt.tight_layout()
    plt.savefig(fig2_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  --> Saved: {fig2_path}")

# ==========================================
# 6. 保存结果
# ==========================================
print("\n" + "=" * 70)
print("Step 6: Saving results")
print("=" * 70)

df_summary = pd.merge(df_ols, df_xgb, on='Distance')
df_summary = df_summary[['Distance', 'N', 'Beta_AL', 'P_AL', 'T_AL', 'R2', 'Mean_R2', 'Std_R2']]
df_summary.columns = ['Distance_mm', 'N', 'Beta_AL', 'P_AL', 'T_AL', 'OLS_R2', 'XGB_CV_R2', 'XGB_CV_R2_std']

csv_path = os.path.join(OUT_DIR, "SR0530_Results_Summary_v2.csv")
df_summary.to_csv(csv_path, index=False, encoding='utf-8-sig')
print(f"  --> Summary: {csv_path}")

if has_shap and shap_importance is not None:
    shap_path = os.path.join(OUT_DIR, "SR0530_SHAP_Importance_v2.csv")
    shap_importance.to_csv(shap_path, index=False, encoding='utf-8-sig')
    print(f"  --> SHAP: {shap_path}")

print("\n" + "=" * 70)
print("Analysis complete!")
print("=" * 70)
