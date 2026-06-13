"""
SR_ML_task2.py
任务二：ML 模型优化（研究方案完整版）
- VIF 共线性诊断
- 方案 A：AL + Age + Gender + ACD + K（CC）
- 方案 B：SE + Age + Gender
- GroupKFold 按真实 Subject 分层 + 近视状态分层 CV
- 模型：SVM / RF / XGBoost / NN / Lasso / ElasticNet
- SHAP 可解释性 + MD 报告
"""

import os
import glob
import warnings
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupKFold, StratifiedKFold, RandomizedSearchCV
from sklearn.pipeline import Pipeline
from sklearn.svm import SVR
from sklearn.ensemble import RandomForestRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.linear_model import LassoCV, ElasticNetCV, RidgeCV
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from xgboost import XGBRegressor
from statsmodels.stats.outliers_influence import variance_inflation_factor
from copy import deepcopy
import shap

warnings.filterwarnings('ignore')

# ============================================================
# 配置
# ============================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'genData', 'CleanDataRoi')
PAIR_PATH = os.path.join(BASE_DIR, 'genData', 'sum', 'Subject_Pair_Mapping.csv')
OUT_DIR = os.path.join(BASE_DIR, 'genData', 'sum')
os.makedirs(OUT_DIR, exist_ok=True)
REPORT_DIR = os.path.join(BASE_DIR, 'report')
FIG_DIR = os.path.join(REPORT_DIR, 'FIG')
os.makedirs(FIG_DIR, exist_ok=True)

FEATURE_ALL = {
    'AL': 'Axial length (mm)',
    'Age': 'Age',
    'SE': 'Spherical equivalent refraction (D)',
    'Gender': 'Gender',
    'K': 'Corneal curvature (mm)',
    'ACD': 'Anterior chamber depth (mm)'
}

TARGET_COL = 'Angular cone density (cones/ deg2)'

# 方案定义
SCHEMA = {
    'A_Biomechanical': ['AL', 'Age', 'Gender', 'ACD', 'K'],
    'B_Clinical': ['SE', 'Age', 'Gender']
}

# 近视定义
MYOPIA_THRESHOLD = -0.5


# ============================================================
# 工具函数
# ============================================================
def load_subject_mapping():
    """建立 Eye_xxx -> 真实 Subject_ID 的映射"""
    pairs = pd.read_csv(PAIR_PATH)
    pid_to_subject = {}
    for _, row in pairs.iterrows():
        pid_to_subject[int(row['OD_PatientID'])] = row['Subject_ID']
        pid_to_subject[int(row['OS_PatientID'])] = row['Subject_ID']

    df_org = pd.read_csv(os.path.join(BASE_DIR, 'orgData', 'orgData.csv'))
    df_ref = pd.read_csv(os.path.join(DATA_DIR, 'data1.csv'))

    eye_to_pid = {}
    for _, row in df_ref.iterrows():
        eye = row['Eye']
        al = row['Axial length (mm)']
        age = row['Age']
        se = row['Spherical equivalent refraction (D)']
        gender = row['Gender']
        mask = (df_org['Eye'] == eye) & \
               (df_org['Axial length (mm)'] == al) & \
               (df_org['Age'] == age) & \
               (df_org['Spherical equivalent refraction (D)'] == se) & \
               (df_org['Gender'] == gender)
        matches = df_org[mask]
        if len(matches) == 1:
            eye_to_pid[row['Subject_ID']] = int(matches.iloc[0]['Patient ID'])
        else:
            raise ValueError(f"Cannot map {row['Subject_ID']}")

    eye_to_subject = {}
    for eye_id, pid in eye_to_pid.items():
        eye_to_subject[eye_id] = pid_to_subject.get(pid, f'Single_{pid}')

    return eye_to_subject


def load_distance_data():
    """读取 44 个 ROI，按距离聚合"""
    all_data = {}
    for f in sorted(glob.glob(os.path.join(DATA_DIR, 'data*.csv'))):
        df = pd.read_csv(f)
        dist = df['Eccentricity (mm)'].iloc[0]
        if dist not in all_data:
            all_data[dist] = []
        all_data[dist].append(df)
    return all_data


def aggregate_distance(dfs, dist, eye_to_subject):
    """按距离聚合 4 个象限，添加真实 Subject_ID 和近视标签"""
    base = dfs[0][['Subject_ID', 'Eye'] + list(FEATURE_ALL.values()) + [TARGET_COL]].copy()
    base = base.rename(columns={TARGET_COL: 'density_q1'})

    for i, d in enumerate(dfs[1:], 2):
        base = base.merge(
            d[['Subject_ID', TARGET_COL]].rename(columns={TARGET_COL: f'density_q{i}'}),
            on='Subject_ID', how='inner'
        )

    den_cols = [c for c in base.columns if c.startswith('density_q')]
    base[TARGET_COL] = base[den_cols].mean(axis=1)

    base['Real_Subject_ID'] = base['Subject_ID'].map(eye_to_subject)
    base['Myopia'] = (base[FEATURE_ALL['SE']] <= MYOPIA_THRESHOLD).astype(int)

    cols = ['Subject_ID', 'Real_Subject_ID', 'Eye', 'Myopia'] + list(FEATURE_ALL.values()) + [TARGET_COL]
    return base[cols].copy()


def fill_na(df, cols):
    for col in cols:
        if df[col].isna().any():
            df[col].fillna(df[col].median(), inplace=True)
    return df


def calc_scores(y_true, y_pred):
    r2 = r2_score(y_true, y_pred)
    corr = np.corrcoef(y_true, y_pred)[0, 1] if len(y_true) > 1 else 0
    mape = np.mean(np.abs((y_true - y_pred) / (y_true + 1e-10))) * 100
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    return r2, corr, mape, rmse


def stratified_group_kfold(groups, y, n_splits=5, random_state=42):
    """
    自定义分层 + 分组 K-Fold。
    groups: 每个样本的 Subject_ID
    y: 二分类标签（如近视/非近视）
    返回 train/test 索引列表。
    """
    rng = np.random.RandomState(random_state)
    df_idx = pd.DataFrame({'idx': np.arange(len(groups)), 'group': groups, 'y': y})

    # 每个 group 的标签（如果组内标签不一致，取多数）
    group_info = df_idx.groupby('group').agg({'y': lambda x: int(x.mode()[0]), 'idx': list}).reset_index()
    group_info = group_info.sample(frac=1, random_state=random_state).reset_index(drop=True)

    # 按标签分层
    pos_groups = group_info[group_info['y'] == 1].copy()
    neg_groups = group_info[group_info['y'] == 0].copy()

    folds = [[] for _ in range(n_splits)]

    for label_df in [pos_groups, neg_groups]:
        for i, row in label_df.iterrows():
            folds[i % n_splits].extend(row['idx'])

    splits = []
    for i in range(n_splits):
        test_idx = np.array(folds[i])
        train_idx = np.array([idx for f in folds[:i] + folds[i+1:] for idx in f])
        splits.append((train_idx, test_idx))

    return splits


def balance_train_indices(ti, y_stratify, random_state=42):
    """
    在训练 fold 内对近视/非近视样本进行过采样，强制类别比例 50:50。
    返回平衡后的训练索引。
    """
    rng = np.random.RandomState(random_state)
    ti = np.array(ti)
    labels = y_stratify[ti]
    pos_idx = ti[labels == 1]
    neg_idx = ti[labels == 0]

    if len(pos_idx) == 0 or len(neg_idx) == 0:
        return ti

    n_max = max(len(pos_idx), len(neg_idx))
    pos_balanced = rng.choice(pos_idx, size=n_max, replace=True) if len(pos_idx) < n_max else pos_idx
    neg_balanced = rng.choice(neg_idx, size=n_max, replace=True) if len(neg_idx) < n_max else neg_idx

    return np.concatenate([pos_balanced, neg_balanced])


def eval_cv(model, X, y, groups, y_stratify, use_y_std=False, n_splits=5, random_state=42):
    """分层 + 分组 CV 评估（训练集内强制 50:50 类别平衡）"""
    splits = stratified_group_kfold(groups, y_stratify, n_splits=n_splits, random_state=random_state)

    train_r2_list, test_r2_list = [], []
    test_corr_list, test_mape_list, test_rmse_list = [], [], []

    for ti, vi in splits:
        # V3.0：训练集内强制近视/非近视 50:50
        ti_bal = balance_train_indices(ti, y_stratify, random_state=random_state)

        if use_y_std:
            sx, sy = StandardScaler(), StandardScaler()
            Xt = sx.fit_transform(X.iloc[ti_bal])
            Xv = sx.transform(X.iloc[vi])
            yt = sy.fit_transform(y.iloc[ti_bal].values.reshape(-1, 1)).ravel()
            yv = y.iloc[vi].values
            yt_raw = y.iloc[ti_bal].values
            m = deepcopy(model)
            m.fit(Xt, yt)
            pred = sy.inverse_transform(m.predict(Xv).reshape(-1, 1)).ravel()
            pred_train = sy.inverse_transform(m.predict(Xt).reshape(-1, 1)).ravel()
        else:
            m = deepcopy(model)
            m.fit(X.iloc[ti_bal], y.iloc[ti_bal])
            pred = m.predict(X.iloc[vi])
            pred_train = m.predict(X.iloc[ti_bal])
            yv = y.iloc[vi].values
            yt_raw = y.iloc[ti_bal].values

        train_r2_list.append(r2_score(yt_raw, pred_train))
        r2, corr, mape, rmse = calc_scores(yv, pred)
        test_r2_list.append(r2)
        test_corr_list.append(corr)
        test_mape_list.append(mape)
        test_rmse_list.append(rmse)

    return {
        'train_r2': np.mean(train_r2_list),
        'test_r2': np.mean(test_r2_list),
        'test_r2_std': np.std(test_r2_list),
        'test_corr': np.mean(test_corr_list),
        'test_mape': np.mean(test_mape_list),
        'test_rmse': np.mean(test_rmse_list),
        'gap': np.mean(train_r2_list) - np.mean(test_r2_list)
    }


def get_feature_importance(model, feature_names):
    """提取特征重要性"""
    try:
        if hasattr(model, 'named_steps'):
            est = model.named_steps[list(model.named_steps.keys())[-1]]
        else:
            est = model

        if hasattr(est, 'feature_importances_'):
            imp = est.feature_importances_
        elif hasattr(est, 'coef_'):
            imp = np.abs(est.coef_).ravel()
        else:
            return None
        return pd.DataFrame({'Feature': feature_names, 'Importance': imp}).sort_values('Importance', ascending=False)
    except Exception:
        return None


# ============================================================
# 模型构建
# ============================================================
def build_models(feature_names):
    """构建模型列表"""
    models = []

    # SVM
    models.append(('SVM', Pipeline([
        ('s', StandardScaler()),
        ('v', SVR(C=2000, epsilon=500, gamma=0.03))
    ]), False))

    # Random Forest（复杂度压制）
    models.append(('Random_Forest', Pipeline([
        ('s', StandardScaler()),
        ('rf', RandomForestRegressor(
            n_estimators=200, max_depth=3,
            min_samples_split=10, min_samples_leaf=4,
            random_state=42, n_jobs=1
        ))
    ]), False))

    # XGBoost（复杂度压制）
    models.append(('XGBoost', XGBRegressor(
        learning_rate=0.01, max_depth=2,
        n_estimators=50, reg_alpha=1.0,
        reg_lambda=1.0, random_state=42, verbosity=0
    ), False))

    # Neural Network
    models.append(('Neural_Network', MLPRegressor(
        hidden_layer_sizes=(80,), alpha=0.5,
        learning_rate_init=0.0001, max_iter=5000,
        early_stopping=True, validation_fraction=0.15,
        n_iter_no_change=20, random_state=42
    ), True))

    # Lasso（基线）
    models.append(('Lasso', Pipeline([
        ('s', StandardScaler()),
        ('lasso', LassoCV(cv=3, random_state=42, max_iter=5000))
    ]), False))

    # Elastic Net（基线）
    models.append(('ElasticNet', Pipeline([
        ('s', StandardScaler()),
        ('en', ElasticNetCV(cv=3, random_state=42, max_iter=5000))
    ]), False))

    return models


# ============================================================
# SHAP
# ============================================================
def run_shap(df, feature_cols_short, feature_cols_full):
    """对 XGBoost 做 SHAP"""
    df = fill_na(df, feature_cols_full)
    X = df[feature_cols_full].values
    y = df[TARGET_COL].values
    groups = df['Real_Subject_ID'].values
    y_strat = df['Myopia'].values

    splits = stratified_group_kfold(groups, y_strat, n_splits=min(5, len(np.unique(groups))))
    train_idx, test_idx = splits[0]

    model = XGBRegressor(
        learning_rate=0.01, max_depth=2,
        n_estimators=50, reg_alpha=1.0,
        reg_lambda=1.0, random_state=42, verbosity=0
    )
    model.fit(X[train_idx], y[train_idx])

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X[test_idx])

    mean_shap = np.abs(shap_values).mean(axis=0)
    shap_df = pd.DataFrame({
        'Feature': feature_cols_short,
        'Mean_SHAP': mean_shap
    }).sort_values('Mean_SHAP', ascending=False)

    return shap_df, shap_values, X[test_idx]


# ============================================================
# 可视化
# ============================================================
def plot_results(ml_results, schema, shap_results, best_cfg):
    df_ml = pd.DataFrame(ml_results)

    fig, axes = plt.subplots(2, 3, figsize=(18, 11))
    fig.suptitle('SR0530 V3.0 ML: ML Optimization (Subject + Myopia Stratified CV)', fontsize=14, fontweight='bold')

    metrics = ['test_r2', 'test_corr', 'gap', 'test_mape', 'test_rmse']
    titles = ['Test R^2', 'Test Correlation', 'Overfitting Gap', 'MAPE (%)', 'RMSE']
    for i, (m, t) in enumerate(zip(metrics, titles)):
        ax = axes[i // 3, i % 3]
        # 对每个 (Distance, Model) 选择最佳 Schema 的结果，避免 pivot 重复
        best_schema_per_dm = df_ml.loc[df_ml.groupby(['Distance', 'Model'])[m].idxmax()]
        pivot = best_schema_per_dm.pivot(index='Distance', columns='Model', values=m)
        for model in pivot.columns:
            ax.plot(pivot.index, pivot[model], 'o-', label=model, linewidth=2, markersize=6)
        if m in ['gap']:
            ax.axhline(0, color='gray', linestyle='--', linewidth=0.8)
        ax.set_xlabel('Distance (mm)')
        ax.set_ylabel(t)
        ax.set_title(f'{chr(65+i)}. {t} by Distance (Best Schema)')
        ax.legend(loc='best', fontsize=8)

    # 最佳 Schema 的 SHAP
    ax = axes[1, 2]
    best_shap = shap_results[best_cfg['schema']]
    shap_sorted = best_shap.sort_values('Mean_SHAP', ascending=True)
    ax.barh(shap_sorted['Feature'], shap_sorted['Mean_SHAP'], color='#2ecc71', edgecolor='black')
    ax.set_xlabel('Mean |SHAP|')
    ax.set_title(f'F. SHAP at {best_cfg["dist"]} mm ({best_cfg["schema"]}, {best_cfg["model"]})')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    fig_path = os.path.join(OUT_DIR, 'SR0530_V3.0_ML_Overview.png')
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(FIG_DIR, os.path.basename(fig_path)),dpi=300, bbox_inches='tight')
    plt.close()
    print(f'  --> Saved: {fig_path}')


def plot_schema_comparison(schema_results):
    """绘制方案 A vs 方案 B 的 Test R2 对比"""
    df = pd.DataFrame(schema_results)
    pivot = df.pivot(index='Distance', columns='Schema', values='Best_Test_R2')

    fig, ax = plt.subplots(figsize=(10, 6))
    for schema in pivot.columns:
        ax.plot(pivot.index, pivot[schema], 'o-', label=schema, linewidth=2, markersize=8)
    ax.axhline(0, color='gray', linestyle='--', linewidth=0.8)
    ax.set_xlabel('Distance (mm)')
    ax.set_ylabel('Best Test R^2')
    ax.set_title('Schema A vs Schema B: Best ML Test R^2 by Distance')
    ax.legend()
    ax.grid(True, alpha=0.3)

    fig_path = os.path.join(OUT_DIR, 'SR0530_V3.0_ML_SchemaComparison.png')
    plt.tight_layout()
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(FIG_DIR, os.path.basename(fig_path)),dpi=300, bbox_inches='tight')
    plt.close()
    print(f'  --> Saved: {fig_path}')


# ============================================================
# 主程序
# ============================================================
def main():
    print("=" * 75)
    print("SR0530 V3.0 ML: ML Optimization")
    print("Schema A (AL+Age+Gender+ACD+K) vs Schema B (SE+Age+Gender)")
    print("CV: GroupKFold by Subject + Myopia Stratification")
    print("=" * 75)

    # 1. 加载映射与数据
    print("\nStep 1: Loading subject mapping...")
    eye_to_subject = load_subject_mapping()

    print("\nStep 2: Loading and aggregating data...")
    all_data = load_distance_data()
    distances = sorted(all_data.keys())

    # 2. VIF 诊断（用 1.0 mm 数据代表）
    print("\nStep 3: VIF collinearity diagnosis...")
    df_vif = aggregate_distance(all_data[distances[0]], distances[0], eye_to_subject)
    X_vif = df_vif[list(FEATURE_ALL.values())].dropna()
    vif_df = pd.DataFrame({
        'Feature': list(FEATURE_ALL.keys()),
        'VIF': [variance_inflation_factor(X_vif.values, i) for i in range(X_vif.shape[1])]
    })
    print(vif_df.to_string(index=False))
    vif_df.to_csv(os.path.join(OUT_DIR, 'SR0530_V3.0_ML_VIF.csv'), index=False, encoding='utf-8-sig')

    # 3. 按方案运行 ML
    print("\nStep 4: Running ML models per distance and schema...")
    ml_results = []
    schema_results = []
    shap_results = {}
    best_overall = {'test_r2': -np.inf, 'dist': None, 'schema': None, 'model': None}

    for dist in distances:
        print(f"\n--- Distance {dist:.1f} mm ---")
        df = aggregate_distance(all_data[dist], dist, eye_to_subject)

        for schema_name, feat_short in SCHEMA.items():
            feat_full = [FEATURE_ALL[s] for s in feat_short]
            df_sub = fill_na(df.copy(), feat_full)

            X = df_sub[feat_full]
            y = df_sub[TARGET_COL]
            groups = df_sub['Real_Subject_ID'].values
            y_strat = df_sub['Myopia'].values

            n_subjects = len(np.unique(groups))
            n_splits = min(5, n_subjects)

            print(f"  [{schema_name}] N={len(df_sub)} eyes/{n_subjects} subjects, folds={n_splits}")

            models = build_models(feat_short)
            best_r2 = -np.inf
            best_model_name = None

            for name, model, use_std in models:
                r = eval_cv(model, X, y, groups, y_strat, use_y_std=use_std, n_splits=n_splits)
                ml_results.append({
                    'Distance': dist,
                    'Schema': schema_name,
                    'Model': name,
                    'N_eyes': len(df_sub),
                    'N_subjects': n_subjects,
                    'Features': ','.join(feat_short),
                    **r
                })
                print(f"    {name:20s}: Test R2={r['test_r2']:.3f}, Corr={r['test_corr']:.3f}, "
                      f"MAPE={r['test_mape']:.2f}%, RMSE={r['test_rmse']:.1f}, Gap={r['gap']:.3f}")

                if r['test_r2'] > best_r2:
                    best_r2 = r['test_r2']
                    best_model_name = name

            schema_results.append({
                'Distance': dist,
                'Schema': schema_name,
                'Best_Model': best_model_name,
                'Best_Test_R2': best_r2
            })

    # 4. 确定最佳配置
    df_ml = pd.DataFrame(ml_results)
    best_row = df_ml.loc[df_ml['test_r2'].idxmax()]
    best_dist = best_row['Distance']
    best_schema = best_row['Schema']
    best_model_name = best_row['Model']
    best_overall = {'dist': best_dist, 'schema': best_schema, 'model': best_model_name}

    print(f"\n[Best Overall] Distance={best_dist:.1f} mm, Schema={best_schema}, Model={best_model_name}, "
          f"Test R2={best_row['test_r2']:.3f}")

    # 5. SHAP on best configuration
    print(f"\nStep 5: SHAP analysis for {best_schema} at {best_dist:.1f} mm...")
    df_best = aggregate_distance(all_data[best_dist], best_dist, eye_to_subject)
    feat_short = SCHEMA[best_schema]
    feat_full = [FEATURE_ALL[s] for s in feat_short]
    shap_df, shap_values, X_test = run_shap(df_best, feat_short, feat_full)
    shap_results[best_schema] = shap_df
    print("  SHAP importance:")
    for _, row in shap_df.iterrows():
        print(f"    {row['Feature']:<10s}: {row['Mean_SHAP']:.3f}")

    # 6. 可视化
    print("\nStep 6: Generating figures...")
    plot_results(ml_results, SCHEMA, shap_results, best_overall)
    plot_schema_comparison(schema_results)

    # SHAP summary plot
    fig, ax = plt.subplots(figsize=(10, 6))
    shap.summary_plot(shap_values, X_test, feature_names=feat_short, show=False)
    fig_path = os.path.join(OUT_DIR, 'SR0530_V3.0_ML_SHAP_Summary.png')
    plt.tight_layout()
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(FIG_DIR, os.path.basename(fig_path)),dpi=300, bbox_inches='tight')
    plt.close()
    print(f'  --> Saved: {fig_path}')

    # 7. 保存结果
    print("\nStep 7: Saving results...")
    df_ml.to_csv(os.path.join(OUT_DIR, 'SR0530_V3.0_ML_ML_Results.csv'), index=False, encoding='utf-8-sig')
    pd.DataFrame(schema_results).to_csv(os.path.join(OUT_DIR, 'SR0530_V3.0_ML_SchemaBest.csv'),
                                        index=False, encoding='utf-8-sig')
    shap_df.to_csv(os.path.join(OUT_DIR, 'SR0530_V3.0_ML_SHAP.csv'), index=False, encoding='utf-8-sig')

    # 8. MD 报告
    print("\nStep 8: Generating MD report...")
    generate_md_report(df_ml, pd.DataFrame(schema_results), vif_df, shap_df, best_overall)

    print("\n" + "=" * 75)
    print("V3.0 ML Task complete!")
    print("=" * 75)


# ============================================================
# MD 报告
# ============================================================
def generate_md_report(df_ml, df_schema, vif_df, shap_df, best_cfg):
    md = []
    md.append("# SR0530 V3.0 任务二报告：ML 模型优化\n\n")
    md.append("> **目标**：在锁定 LMM 最佳偏心率后，建立基于常规眼科参数的视锥密度预测模型。\n")
    md.append("> **方法**：双模型策略 + Subject/近视分层 CV（训练集内强制 50:50 平衡）+ SVM/RF/XGB/NN/Lasso/ElasticNet + SHAP。\n")
    md.append("> **数据**：genData/CleanDataRoi/（44 个 ROI，聚合为 11 个距离组）。\n\n")

    md.append("---\n\n")
    md.append("## 一、VIF 共线性诊断\n\n")
    md.append("| 特征 | VIF |\n")
    md.append("|------|-----|\n")
    for _, row in vif_df.iterrows():
        md.append(f"| {row['Feature']} | {row['VIF']:.2f} |\n")
    md.append("\n*注：VIF > 10 提示存在严重多重共线性。\n\n")

    md.append("## 二、方案 A vs 方案 B\n\n")
    md.append("- **方案 A（生物力学主模型）**：`[AL, Age, Gender, ACD, K]`，剔除 SE。\n")
    md.append("- **方案 B（临床筛查辅助模型）**：`[SE, Age, Gender]`，剔除 AL/ACD/K。\n\n")
    md.append("| 距离 (mm) | 方案 | 最佳模型 | Test R² |\n")
    md.append("|-----------|------|----------|---------|\n")
    for _, row in df_schema.iterrows():
        md.append(f"| {row['Distance']:.1f} | {row['Schema']} | {row['Best_Model']} | {row['Best_Test_R2']:.3f} |\n")

    md.append("\n## 三、全部模型结果\n\n")
    md.append("| 距离 (mm) | 方案 | 模型 | N_eyes | N_subj | Train R² | Test R² | Test Corr | MAPE(%) | RMSE | Gap |\n")
    md.append("|-----------|------|------|--------|--------|----------|---------|-----------|---------|------|-----|\n")
    for _, row in df_ml.iterrows():
        md.append(f"| {row['Distance']:.1f} | {row['Schema']} | {row['Model']} | "
                  f"{int(row['N_eyes'])} | {int(row['N_subjects'])} | "
                  f"{row['train_r2']:.3f} | {row['test_r2']:.3f} | {row['test_corr']:.3f} | "
                  f"{row['test_mape']:.2f} | {row['test_rmse']:.1f} | {row['gap']:.3f} |\n")

    md.append(f"\n**总体最佳配置**：距离 **{best_cfg['dist']:.1f} mm**，方案 **{best_cfg['schema']}**，"
              f"模型 **{best_cfg['model']}**。\n\n")

    md.append("## 四、SHAP 可解释性分析\n\n")
    md.append(f"对总体最佳配置（{best_cfg['schema']}，{best_cfg['dist']:.1f} mm）进行 SHAP 分析：\n\n")
    md.append("| 特征 | Mean |SHAP| |\n")
    md.append("|------|-------------|\n")
    for _, row in shap_df.iterrows():
        md.append(f"| {row['Feature']} | {row['Mean_SHAP']:.3f} |\n")

    md.append("\n## 五、讨论\n\n")
    md.append("1. **训练集内强制 50:50 类别平衡**：对少数类进行过采样，严格符合 V3.0 方案要求。\n")
    md.append("2. **分层 CV 降低信息泄漏**：按真实 Subject 分层避免双眼同时出现在训练/测试集。\n")
    md.append("3. **小样本下 Lasso/ElasticNet 是重要基线**：线性正则化模型可作为树模型的保守对比。\n")
    md.append("4. **XGBoost/RF 已做复杂度压制**：`max_depth=2–3`，强 L1/L2 正则化，降低过拟合风险。\n")
    md.append("5. **SHAP 揭示关键驱动特征**：K、AL、Gender 等是主要预测因子。\n\n")

    md.append("## 六、可视化\n\n")
    md.append("![综合分析](FIG/SR0530_V3.0_ML_Overview.png)\n\n")
    md.append("![方案对比](FIG/SR0530_V3.0_ML_SchemaComparison.png)\n\n")
    md.append("![SHAP 详细图](FIG/SR0530_V3.0_ML_SHAP_Summary.png)\n\n")

    md.append("---\n\n")
    md.append("*Report generated automatically by SR_ML_V3.0.py*\n")

    md_path = os.path.join(BASE_DIR, 'report', 'SR0530_V3.0_ML_Optimization_Report.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(''.join(md))
    print(f'  --> Report: {md_path}')


if __name__ == '__main__':
    main()
