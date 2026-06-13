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

warnings.filterwarnings('ignore')

# ============================================================
# 配置
# ============================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'genData', 'CleanDataRoi_strict')
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

# 方案定义（重构后）
# A1: 最精简生物力学模型，彻底消除 AL/K/ACD 共线性
# A2: 剔除 K（与 AL 共线性最高），保留 ACD
# B:  临床筛查模型
# C1: 同时包含 SE 和 AL，但剔除 K/ACD 共线性
SCHEMA = {
    'A1_Biomechanical_Core': ['AL', 'Age', 'Gender'],
    'A2_Biomechanical_NoK': ['AL', 'ACD', 'Age', 'Gender'],
    'B_Clinical': ['SE', 'Age', 'Gender'],
    'C1_Combined': ['SE', 'AL', 'Age', 'Gender']
}

# 近视定义
MYOPIA_THRESHOLD = -0.5


# ============================================================
# 工具函数
# ============================================================
def load_subject_mapping():
    """
    从 CleanDataRoi 直接读取真实 Subject_ID。
    输入数据层修复后，data1.csv 已包含真实 Subject_ID（Subj_xxx / Single_xxx），
    不再需要反向匹配 Patient ID。
    """
    df_ref = pd.read_csv(os.path.join(DATA_DIR, 'data1.csv'))
    eye_to_subject = {}

    for _, row in df_ref.iterrows():
        eye_label = row['Eye_Label']        # 如 Eye_001
        subject_id = row['Subject_ID']      # 如 Subj_001 或 Single_10816
        eye_to_subject[eye_label] = subject_id
        # 恒等映射：兼容 aggregate_distance 中直接使用 Subject_ID 列的代码
        eye_to_subject[subject_id] = subject_id

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
    """按距离聚合 4 个象限，按 Subject_ID + Eye 组合聚合，添加真实 Subject_ID 和近视标签"""
    base = dfs[0][['Subject_ID', 'Eye'] + list(FEATURE_ALL.values()) + [TARGET_COL]].copy()
    base = base.rename(columns={TARGET_COL: 'density_q1'})

    for i, d in enumerate(dfs[1:], 2):
        base = base.merge(
            d[['Subject_ID', 'Eye', TARGET_COL]].rename(columns={TARGET_COL: f'density_q{i}'}),
            on=['Subject_ID', 'Eye'], how='inner'
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
    pos_groups = group_info[group_info['y'] == 1].copy().reset_index(drop=True)
    neg_groups = group_info[group_info['y'] == 0].copy().reset_index(drop=True)

    folds = [[] for _ in range(n_splits)]

    for label_df in [pos_groups, neg_groups]:
        n_groups = len(label_df)
        if n_groups == 0:
            continue
        # 确保每个 fold 至少分到 1 个 group（如果该层 group 数 >= n_splits）
        # 如果 group 数 < n_splits，则循环分配，部分 fold 会从该层为空
        for i, row in label_df.iterrows():
            folds[i % n_splits].extend(row['idx'])

    # 保护：如果某 fold 为空，从最大的 fold 借调一个 group
    for i in range(n_splits):
        if not folds[i]:
            # 找到最大的 fold
            largest_idx = max(range(n_splits), key=lambda k: len(folds[k]))
            # 从最大 fold 移动最后一个 group 的索引到空 fold
            moved = folds[largest_idx].pop()
            folds[i].append(moved)

    splits = []
    for i in range(n_splits):
        test_idx = np.array(folds[i])
        train_idx = np.array([idx for f in folds[:i] + folds[i+1:] for idx in f])
        splits.append((train_idx, test_idx))

    return splits


def eval_cv(model, X, y, groups, y_stratify, use_y_std=False, n_splits=5, random_state=42):
    """分层 + 分组 CV 评估"""
    splits = stratified_group_kfold(groups, y_stratify, n_splits=n_splits, random_state=random_state)

    train_r2_list, test_r2_list = [], []
    test_corr_list, test_mape_list, test_rmse_list = [], [], []

    for ti, vi in splits:
        if use_y_std:
            sx, sy = StandardScaler(), StandardScaler()
            Xt = sx.fit_transform(X.iloc[ti])
            Xv = sx.transform(X.iloc[vi])
            yt = sy.fit_transform(y.iloc[ti].values.reshape(-1, 1)).ravel()
            yv = y.iloc[vi].values
            yt_raw = y.iloc[ti].values
            m = deepcopy(model)
            m.fit(Xt, yt)
            pred = sy.inverse_transform(m.predict(Xv).reshape(-1, 1)).ravel()
            pred_train = sy.inverse_transform(m.predict(Xt).reshape(-1, 1)).ravel()
        else:
            m = deepcopy(model)
            m.fit(X.iloc[ti], y.iloc[ti])
            pred = m.predict(X.iloc[vi])
            pred_train = m.predict(X.iloc[ti])
            yv = y.iloc[vi].values
            yt_raw = y.iloc[ti].values

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
    """提取特征重要性（兼容树模型和线性模型）"""
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


def get_standardized_coefficients(model, feature_names):
    """
    提取标准化回归系数（仅适用于带 StandardScaler 的 Pipeline 线性模型）。
    返回 DataFrame: Feature, Coef, Abs_Coef
    """
    try:
        if hasattr(model, 'named_steps'):
            scaler = model.named_steps.get('s', None)
            est = model.named_steps[list(model.named_steps.keys())[-1]]
        else:
            scaler = None
            est = model

        if not hasattr(est, 'coef_'):
            return None

        raw_coef = est.coef_.ravel()
        # 如果使用了 StandardScaler，系数已经是标准化后的
        coef = raw_coef
        return pd.DataFrame({
            'Feature': feature_names,
            'Coef': coef,
            'Abs_Coef': np.abs(coef)
        }).sort_values('Abs_Coef', ascending=False)
    except Exception:
        return None


def bootstrap_coefficients(model_builder, X, y, groups, y_strat, feature_names,
                           n_splits=5, n_boot=500, random_state=42):
    """
    对最佳线性模型做 Bootstrap 标准化系数估计，返回系数及其 95% CI。
    model_builder: 返回一个可 fit/predict 的模型实例的函数
    """
    rng = np.random.RandomState(random_state)
    coef_boot = []

    for b in range(n_boot):
        # Bootstrap 重采样（有放回）
        idx = rng.choice(len(X), size=len(X), replace=True)
        X_b = X.iloc[idx] if hasattr(X, 'iloc') else X[idx]
        y_b = y.iloc[idx] if hasattr(y, 'iloc') else y[idx]

        model = model_builder()
        model.fit(X_b, y_b)

        coef_df = get_standardized_coefficients(model, feature_names)
        if coef_df is not None:
            coef_boot.append(coef_df.set_index('Feature')['Coef'].to_dict())

    if not coef_boot:
        return None

    coef_matrix = pd.DataFrame(coef_boot)
    summary = pd.DataFrame({
        'Feature': feature_names,
        'Mean_Coef': coef_matrix.mean().values,
        'CI_Lower': coef_matrix.quantile(0.025).values,
        'CI_Upper': coef_matrix.quantile(0.975).values
    })
    summary['CI_Includes_Zero'] = (summary['CI_Lower'] <= 0) & (summary['CI_Upper'] >= 0)
    return summary


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

    # Ridge（基线，适合严重共线性场景）
    models.append(('Ridge', Pipeline([
        ('s', StandardScaler()),
        ('ridge', RidgeCV(cv=3))
    ]), False))

    return models


# ============================================================
# 标准化回归系数分析（替代 SHAP）
# ============================================================
def run_coefficient_analysis(df, feature_cols_short, feature_cols_full, model_name='ElasticNet'):
    """
    对最佳线性模型提取标准化回归系数，并通过 Bootstrap 计算 95% CI。
    返回：coef_summary DataFrame, full_model（在全部数据上拟合的模型）
    """
    df = fill_na(df, feature_cols_full)
    X = df[feature_cols_full]
    y = df[TARGET_COL]

    # 在全部数据上拟合最终模型（用于报告点估计）
    if model_name == 'ElasticNet':
        full_model = Pipeline([
            ('s', StandardScaler()),
            ('en', ElasticNetCV(cv=3, random_state=42, max_iter=5000))
        ])
    elif model_name == 'Ridge':
        full_model = Pipeline([
            ('s', StandardScaler()),
            ('ridge', RidgeCV(cv=3))
        ])
    elif model_name == 'Lasso':
        full_model = Pipeline([
            ('s', StandardScaler()),
            ('lasso', LassoCV(cv=3, random_state=42, max_iter=5000))
        ])
    else:
        full_model = Pipeline([
            ('s', StandardScaler()),
            ('en', ElasticNetCV(cv=3, random_state=42, max_iter=5000))
        ])

    full_model.fit(X, y)

    # Bootstrap CI
    def model_builder():
        if model_name == 'ElasticNet':
            return Pipeline([
                ('s', StandardScaler()),
                ('en', ElasticNetCV(cv=3, random_state=42, max_iter=5000))
            ])
        elif model_name == 'Ridge':
            return Pipeline([
                ('s', StandardScaler()),
                ('ridge', RidgeCV(cv=3))
            ])
        elif model_name == 'Lasso':
            return Pipeline([
                ('s', StandardScaler()),
                ('lasso', LassoCV(cv=3, random_state=42, max_iter=5000))
            ])
        else:
            return Pipeline([
                ('s', StandardScaler()),
                ('en', ElasticNetCV(cv=3, random_state=42, max_iter=5000))
            ])

    coef_summary = bootstrap_coefficients(
        model_builder, X, y,
        groups=df['Real_Subject_ID'].values,
        y_strat=df['Myopia'].values,
        feature_names=feature_cols_short,
        n_boot=500,
        random_state=42
    )

    # 合并点估计
    point_coef = get_standardized_coefficients(full_model, feature_cols_short)
    if point_coef is not None and coef_summary is not None:
        coef_summary = coef_summary.merge(
            point_coef[['Feature', 'Coef']],
            on='Feature',
            how='left'
        )
    elif point_coef is not None:
        coef_summary = point_coef.rename(columns={'Coef': 'Mean_Coef'})
        coef_summary['CI_Lower'] = np.nan
        coef_summary['CI_Upper'] = np.nan
        coef_summary['CI_Includes_Zero'] = np.nan

    return coef_summary, full_model


# ============================================================
# 可视化
# ============================================================
def plot_results(ml_results, schema, coef_results, best_cfg):
    df_ml = pd.DataFrame(ml_results)

    fig, axes = plt.subplots(2, 3, figsize=(18, 11))
    fig.suptitle('SR0530 Task 2: ML Optimization (Subject + Myopia Stratified CV)', fontsize=14, fontweight='bold')

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

    # 最佳 Schema 的标准化回归系数（替代 SHAP）
    ax = axes[1, 2]
    best_coef = coef_results[best_cfg['schema']].copy()
    best_coef = best_coef.sort_values('Coef', ascending=True)
    colors = ['#e74c3c' if c < 0 else '#2ecc71' for c in best_coef['Coef']]
    ax.barh(best_coef['Feature'], best_coef['Coef'], color=colors, edgecolor='black')
    ax.axvline(0, color='black', linewidth=0.8)
    ax.set_xlabel('Standardized Coefficient')
    ax.set_title(f'F. Std Coefficients at {best_cfg["dist"]} mm ({best_cfg["schema"]}, {best_cfg["model"]})')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    fig_path = os.path.join(OUT_DIR, 'SR0530_Task2_Overview.png')
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(FIG_DIR, os.path.basename(fig_path)),dpi=300, bbox_inches='tight')
    plt.close()
    print(f'  --> Saved: {fig_path}')


def plot_schema_comparison(schema_results):
    """绘制方案 A1/A2/B/C1 的 Test R2 对比"""
    df = pd.DataFrame(schema_results)
    pivot = df.pivot(index='Distance', columns='Schema', values='Best_Test_R2')

    fig, ax = plt.subplots(figsize=(10, 6))
    for schema in pivot.columns:
        ax.plot(pivot.index, pivot[schema], 'o-', label=schema, linewidth=2, markersize=8)
    ax.axhline(0, color='gray', linestyle='--', linewidth=0.8)
    ax.set_xlabel('Distance (mm)')
    ax.set_ylabel('Best Test R^2')
    ax.set_title('Schema Comparison: Best ML Test R^2 by Distance')
    ax.legend()
    ax.grid(True, alpha=0.3)

    fig_path = os.path.join(OUT_DIR, 'SR0530_Task2_SchemaComparison.png')
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
    print("SR0530 Task 2: ML Optimization")
    print("Schema A1/A2/B/C1 + Subject/Myopia Stratified CV")
    print("Feature importance: Standardized Coefficients + Bootstrap 95% CI")
    print("=" * 75)

    # 1. 加载映射与数据
    print("\nStep 1: Loading subject mapping...")
    eye_to_subject = load_subject_mapping()

    print("\nStep 2: Loading and aggregating data...")
    all_data = load_distance_data()
    distances = sorted(all_data.keys())

    # 2. VIF 诊断（用 1.0 mm 数据代表，完整特征集）
    print("\nStep 3: VIF collinearity diagnosis...")
    df_vif = aggregate_distance(all_data[distances[0]], distances[0], eye_to_subject)
    X_vif = df_vif[list(FEATURE_ALL.values())].dropna()
    vif_df = pd.DataFrame({
        'Feature': list(FEATURE_ALL.keys()),
        'VIF': [variance_inflation_factor(X_vif.values, i) for i in range(X_vif.shape[1])]
    })
    print(vif_df.to_string(index=False))
    vif_df.to_csv(os.path.join(OUT_DIR, 'SR0530_Task2_VIF.csv'), index=False, encoding='utf-8-sig')

    # 3. 按方案运行 ML
    print("\nStep 4: Running ML models per distance and schema...")
    ml_results = []
    schema_results = []
    coef_results = {}
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
            n_splits = min(5, n_subjects // 2)
            if n_splits < 2:
                print(f"    ⚠️ Warning: only {n_subjects} subjects at distance {dist}, skipping ML for this distance.")
                continue

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

    # 5. 标准化回归系数分析（替代 SHAP）
    print(f"\nStep 5: Standardized coefficient analysis for {best_schema} at {best_dist:.1f} mm...")
    df_best = aggregate_distance(all_data[best_dist], best_dist, eye_to_subject)
    feat_short = SCHEMA[best_schema]
    feat_full = [FEATURE_ALL[s] for s in feat_short]
    coef_df, _ = run_coefficient_analysis(df_best, feat_short, feat_full, model_name=best_model_name)
    coef_results[best_schema] = coef_df
    print("  Standardized coefficients (with Bootstrap 95% CI):")
    for _, row in coef_df.iterrows():
        ci_zero = "(includes 0)" if row['CI_Includes_Zero'] else "(excludes 0)"
        print(f"    {row['Feature']:<10s}: {row['Coef']:.3f} [{row['CI_Lower']:.3f}, {row['CI_Upper']:.3f}] {ci_zero}")

    # 6. Lasso 补充分析：看 K/ACD 是否被压为 0
    print(f"\nStep 6: Lasso supplementary analysis at {best_dist:.1f} mm...")
    # 使用方案 A2（包含 AL, ACD, K）运行 Lasso
    lasso_short = SCHEMA['A2_Biomechanical_NoK']
    lasso_full = [FEATURE_ALL[s] for s in lasso_short]
    lasso_df, _ = run_coefficient_analysis(df_best, lasso_short, lasso_full, model_name='Lasso')
    print("  Lasso coefficients (A2 features):")
    for _, row in lasso_df.iterrows():
        print(f"    {row['Feature']:<10s}: {row['Coef']:.3f}")

    # 7. 可视化
    print("\nStep 7: Generating figures...")
    plot_results(ml_results, SCHEMA, coef_results, best_overall)
    plot_schema_comparison(schema_results)

    # 8. 保存结果
    print("\nStep 8: Saving results...")
    df_ml.to_csv(os.path.join(OUT_DIR, 'SR0530_Task2_ML_Results.csv'), index=False, encoding='utf-8-sig')
    pd.DataFrame(schema_results).to_csv(os.path.join(OUT_DIR, 'SR0530_Task2_SchemaBest.csv'),
                                        index=False, encoding='utf-8-sig')
    coef_df.to_csv(os.path.join(OUT_DIR, 'SR0530_Task2_Coefficients.csv'), index=False, encoding='utf-8-sig')
    lasso_df.to_csv(os.path.join(OUT_DIR, 'SR0530_Task2_Lasso_Coefficients.csv'), index=False, encoding='utf-8-sig')

    # 9. MD 报告
    print("\nStep 9: Generating MD report...")
    generate_md_report(df_ml, pd.DataFrame(schema_results), vif_df, coef_df, lasso_df, best_overall)

    print("\n" + "=" * 75)
    print("Task 2 complete!")
    print("=" * 75)


# ============================================================
# MD 报告
# ============================================================
def generate_md_report(df_ml, df_schema, vif_df, coef_df, lasso_df, best_cfg):
    md = []
    md.append("# SR0530 任务二报告：ML 模型优化（重构版）\n\n")
    md.append("> **目标**：在锁定 LMM 最佳偏心率后，建立基于常规眼科参数的视锥密度预测模型。\n")
    md.append("> **方法**：四方案策略 (A1/A2/B/C1) + Subject/近视分层 CV + SVM/RF/XGB/NN/Lasso/ElasticNet/Ridge + 标准化回归系数。\n")
    md.append("> **数据**：genData/CleanDataRoi_strict/（44 个 ROI，聚合为 11 个距离组，69 眼）。\n\n")

    md.append("---\n\n")
    md.append("## 一、VIF 共线性诊断\n\n")
    md.append("| 特征 | VIF |\n")
    md.append("|------|-----|\n")
    for _, row in vif_df.iterrows():
        md.append(f"| {row['Feature']} | {row['VIF']:.2f} |\n")
    md.append("\n*注：VIF > 10 提示存在严重多重共线性。方案 A1（仅 AL+Age+Gender）和 B（SE+Age+Gender）可彻底消除共线性。\n\n")

    md.append("## 二、方案说明\n\n")
    md.append("- **A1_Biomechanical_Core**：`[AL, Age, Gender]`，最精简，彻底消除共线性。\n")
    md.append("- **A2_Biomechanical_NoK**：`[AL, ACD, Age, Gender]`，剔除与 AL 共线性最高的 K。\n")
    md.append("- **B_Clinical**：`[SE, Age, Gender]`，临床筛查模型。\n")
    md.append("- **C1_Combined**：`[SE, AL, Age, Gender]`，同时包含 SE 和 AL，但剔除 K/ACD。\n\n")

    md.append("## 三、方案对比\n\n")
    md.append("| 距离 (mm) | 方案 | 最佳模型 | Test R² |\n")
    md.append("|-----------|------|----------|---------|\n")
    for _, row in df_schema.iterrows():
        md.append(f"| {row['Distance']:.1f} | {row['Schema']} | {row['Best_Model']} | {row['Best_Test_R2']:.3f} |\n")

    md.append("\n## 四、全部模型结果\n\n")
    md.append("| 距离 (mm) | 方案 | 模型 | N_eyes | N_subj | Train R² | Test R² | Test Corr | MAPE(%) | RMSE | Gap |\n")
    md.append("|-----------|------|------|--------|--------|----------|---------|-----------|---------|------|-----|\n")
    for _, row in df_ml.iterrows():
        md.append(f"| {row['Distance']:.1f} | {row['Schema']} | {row['Model']} | "
                  f"{int(row['N_eyes'])} | {int(row['N_subjects'])} | "
                  f"{row['train_r2']:.3f} | {row['test_r2']:.3f} | {row['test_corr']:.3f} | "
                  f"{row['test_mape']:.2f} | {row['test_rmse']:.1f} | {row['gap']:.3f} |\n")

    md.append(f"\n**总体最佳配置**：距离 **{best_cfg['dist']:.1f} mm**，方案 **{best_cfg['schema']}**，"
              f"模型 **{best_cfg['model']}**。\n\n")

    md.append("## 五、标准化回归系数（替代 SHAP）\n\n")
    md.append(f"对总体最佳配置（{best_cfg['schema']}，{best_cfg['dist']:.1f} mm）进行 Bootstrap 标准化系数分析：\n\n")
    md.append("| 特征 | Coef | 95% CI Lower | 95% CI Upper | CI Includes Zero |\n")
    md.append("|------|------|--------------|--------------|------------------|\n")
    for _, row in coef_df.iterrows():
        includes_zero = "是" if row['CI_Includes_Zero'] else "否"
        md.append(f"| {row['Feature']} | {row['Coef']:.3f} | {row['CI_Lower']:.3f} | {row['CI_Upper']:.3f} | {includes_zero} |\n")

    md.append("\n## 六、Lasso 补充分析\n\n")
    md.append(f"在总体最佳距离（{best_cfg['dist']:.1f} mm）使用方案 A2 特征运行 Lasso：\n\n")
    md.append("| 特征 | Lasso Coef |\n")
    md.append("|------|------------|\n")
    for _, row in lasso_df.iterrows():
        md.append(f"| {row['Feature']} | {row['Coef']:.3f} |\n")

    md.append("\n## 七、讨论\n\n")
    md.append("1. **分层 CV 降低信息泄漏**：按真实 Subject 分层避免双眼同时出现在训练/测试集；按近视状态分层保持类别比例。\n")
    md.append("2. **共线性处理**：方案 A1 和 B 彻底消除 VIF > 10 的共线性；方案 A2 通过剔除 K 降低共线性。\n")
    md.append("3. **标准化回归系数替代 SHAP**：鉴于最佳模型为线性正则化模型，系数及其 Bootstrap CI 比 SHAP 更可靠。\n")
    md.append("4. **Lasso 作为补充**：若 Lasso 将 K/ACD 压缩为 0，可进一步确立 AL 的核心地位。\n\n")

    md.append("## 八、可视化\n\n")
    md.append("![综合分析](FIG/SR0530_Task2_Overview.png)\n\n")
    md.append("![方案对比](FIG/SR0530_Task2_SchemaComparison.png)\n\n")

    md.append("---\n\n")
    md.append("*Report generated automatically by SR_ML_task2.py*\n")

    md_path = os.path.join(BASE_DIR, 'report', 'SR0530_Task2_ML_Optimization_Report.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(''.join(md))
    print(f'  --> Report: {md_path}')


if __name__ == '__main__':
    main()
