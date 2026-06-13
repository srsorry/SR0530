"""
SR_ML_kimi_v2.py
Kimi 方案 v2.0：机器学习预测模型优化（对齐 SR_ML_task2.py 新策略）
- 方案 A1: [AL, Age, Gender]
- 方案 A2: [AL, ACD, Age, Gender]
- 方案 B:  [SE, Age, Gender]
- 方案 C1: [SE, AL, Age, Gender]
- CV: StratifiedGroupKFold（按 Subject 分层，按近视状态分层）
- 补充验证: LOOCV + Bootstrap optimism-corrected R2
- 模型: SVM / RF / XGBoost / Neural Network / Lasso / ElasticNet / Ridge
- 可解释性: 标准化回归系数 + Bootstrap 95% CI + Permutation Importance
- Calibration + Brier Score
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
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.svm import SVR
from sklearn.ensemble import RandomForestRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.linear_model import LassoCV, ElasticNetCV, RidgeCV
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.inspection import permutation_importance
from statsmodels.stats.outliers_influence import variance_inflation_factor
from xgboost import XGBRegressor
from copy import deepcopy
import statsmodels.api as sm

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

TARGET_COL = 'Angular cone density (cones/ deg2)'
FEATURE_ALL = {
    'AL': 'Axial length (mm)',
    'Age': 'Age',
    'SE': 'Spherical equivalent refraction (D)',
    'Gender': 'Gender',
    'K': 'Corneal curvature (mm)',
    'ACD': 'Anterior chamber depth (mm)'
}

SCHEMA = {
    'A1_Biomechanical_Core': ['AL', 'Age', 'Gender'],
    'A2_Biomechanical_NoK': ['AL', 'ACD', 'Age', 'Gender'],
    'B_Clinical': ['SE', 'Age', 'Gender'],
    'C1_Combined': ['SE', 'AL', 'Age', 'Gender']
}

MYOPIA_THRESHOLD = -0.5
RANDOM_STATE = 42
N_BOOTSTRAP = 500


# ============================================================
# 工具函数
# ============================================================
def load_subject_mapping():
    """
    从 CleanDataRoi_strict 直接读取真实 Subject_ID。
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
    """读取 44 个 ROI 文件，按距离聚合"""
    all_data = {}
    for f in sorted(glob.glob(os.path.join(DATA_DIR, 'data*.csv'))):
        df = pd.read_csv(f)
        dist = df['Eccentricity (mm)'].iloc[0]
        if dist not in all_data:
            all_data[dist] = []
        all_data[dist].append(df)
    return all_data


def aggregate_distance(dfs, dist, eye_to_subject):
    """对同一距离的 4 个象限数据取平均角密度，按 Subject_ID + Eye 聚合，并映射真实 Subject"""
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
    corr = np.corrcoef(y_true, y_pred)[0, 1] if len(y_true) > 1 else 0.0
    mape = np.mean(np.abs((y_true - y_pred) / (y_true + 1e-10))) * 100
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    brier = mean_squared_error(y_true, y_pred)
    return r2, corr, mape, rmse, mae, brier


# ============================================================
# 分层分组 CV
# ============================================================
def stratified_group_kfold(groups, y, n_splits=5, random_state=42):
    """自定义分层 + 分组 K-Fold"""
    rng = np.random.RandomState(random_state)
    df_idx = pd.DataFrame({'idx': np.arange(len(groups)), 'group': groups, 'y': y})

    group_info = df_idx.groupby('group').agg({'y': lambda x: int(x.mode()[0]), 'idx': list}).reset_index()
    group_info = group_info.sample(frac=1, random_state=random_state).reset_index(drop=True)

    pos_groups = group_info[group_info['y'] == 1].copy().reset_index(drop=True)
    neg_groups = group_info[group_info['y'] == 0].copy().reset_index(drop=True)

    folds = [[] for _ in range(n_splits)]
    for label_df in [pos_groups, neg_groups]:
        n_groups = len(label_df)
        if n_groups == 0:
            continue
        for i, row in label_df.iterrows():
            folds[i % n_splits].extend(row['idx'])

    # 保护：如果某 fold 为空，从最大的 fold 借调一个 group
    for i in range(n_splits):
        if not folds[i]:
            largest_idx = max(range(n_splits), key=lambda k: len(folds[k]))
            moved = folds[largest_idx].pop()
            folds[i].append(moved)

    splits = []
    for i in range(n_splits):
        test_idx = np.array(folds[i])
        train_idx = np.array([idx for f in folds[:i] + folds[i+1:] for idx in f])
        splits.append((train_idx, test_idx))
    return splits


# ============================================================
# 模型构建
# ============================================================
def build_models():
    models = []

    models.append(('SVM', Pipeline([
        ('s', StandardScaler()),
        ('v', SVR(C=2000, epsilon=500, gamma=0.03))
    ]), False))

    models.append(('Random_Forest', Pipeline([
        ('s', StandardScaler()),
        ('rf', RandomForestRegressor(
            n_estimators=200, max_depth=3,
            min_samples_split=10, min_samples_leaf=4,
            random_state=RANDOM_STATE, n_jobs=1
        ))
    ]), False))

    models.append(('XGBoost', XGBRegressor(
        learning_rate=0.01, max_depth=2,
        n_estimators=50, reg_alpha=1.0,
        reg_lambda=1.0, random_state=RANDOM_STATE, verbosity=0
    ), False))

    models.append(('Neural_Network', MLPRegressor(
        hidden_layer_sizes=(80,), alpha=0.5,
        learning_rate_init=0.0001, max_iter=500,
        early_stopping=True, validation_fraction=0.15,
        n_iter_no_change=10, random_state=RANDOM_STATE
    ), True))

    models.append(('Lasso', Pipeline([
        ('s', StandardScaler()),
        ('lasso', LassoCV(cv=3, random_state=RANDOM_STATE, max_iter=5000))
    ]), False))

    models.append(('ElasticNet', Pipeline([
        ('s', StandardScaler()),
        ('en', ElasticNetCV(cv=3, random_state=RANDOM_STATE, max_iter=5000))
    ]), False))

    models.append(('Ridge', Pipeline([
        ('s', StandardScaler()),
        ('ridge', RidgeCV(cv=3))
    ]), False))

    return models


# ============================================================
# 评估策略
# ============================================================
def eval_cv(model, X, y, groups, y_stratify, use_y_std=False, n_splits=5):
    """分层 + 分组 CV"""
    n_splits = min(n_splits, len(np.unique(groups)))
    if n_splits < 2:
        return None
    splits = stratified_group_kfold(groups, y_stratify, n_splits=n_splits, random_state=RANDOM_STATE)

    train_r2_list, test_r2_list = [], []
    test_corr_list, test_mape_list, test_rmse_list = [], [], []
    test_mae_list, test_brier_list = [], []

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
        r2, corr, mape, rmse, mae, brier = calc_scores(yv, pred)
        test_r2_list.append(r2)
        test_corr_list.append(corr)
        test_mape_list.append(mape)
        test_rmse_list.append(rmse)
        test_mae_list.append(mae)
        test_brier_list.append(brier)

    return {
        'train_r2': np.mean(train_r2_list),
        'test_r2': np.mean(test_r2_list),
        'test_r2_std': np.std(test_r2_list),
        'test_corr': np.mean(test_corr_list),
        'test_mape': np.mean(test_mape_list),
        'test_rmse': np.mean(test_rmse_list),
        'test_mae': np.mean(test_mae_list),
        'test_brier': np.mean(test_brier_list),
        'gap': np.mean(train_r2_list) - np.mean(test_r2_list)
    }


def eval_loocv(model, X, y, groups, use_y_std=False):
    """Leave-one-subject-out CV"""
    unique_groups = np.unique(groups)
    preds, trues = [], []

    for g in unique_groups:
        test_mask = (groups == g)
        train_mask = ~test_mask
        ti = np.where(train_mask)[0]
        vi = np.where(test_mask)[0]

        if use_y_std:
            sx, sy = StandardScaler(), StandardScaler()
            Xt = sx.fit_transform(X.iloc[ti])
            Xv = sx.transform(X.iloc[vi])
            yt = sy.fit_transform(y.iloc[ti].values.reshape(-1, 1)).ravel()
            yv = y.iloc[vi].values
            m = deepcopy(model)
            m.fit(Xt, yt)
            pred = sy.inverse_transform(m.predict(Xv).reshape(-1, 1)).ravel()
        else:
            m = deepcopy(model)
            m.fit(X.iloc[ti], y.iloc[ti])
            pred = m.predict(X.iloc[vi])
            yv = y.iloc[vi].values

        preds.extend(pred.tolist())
        trues.extend(yv.tolist())

    y_true = np.array(trues)
    y_pred = np.array(preds)
    r2, corr, mape, rmse, mae, brier = calc_scores(y_true, y_pred)
    return {
        'loocv_r2': r2,
        'loocv_corr': corr,
        'loocv_mape': mape,
        'loocv_rmse': rmse,
        'loocv_mae': mae,
        'loocv_brier': brier
    }


def eval_bootstrap(model, X, y, groups, use_y_std=False, n_bootstrap=N_BOOTSTRAP):
    """Bootstrap optimism-corrected R2"""
    unique_groups = np.unique(groups)
    n_groups = len(unique_groups)
    rng = np.random.RandomState(RANDOM_STATE)

    # Apparent performance on full data
    m_full = deepcopy(model)
    if use_y_std:
        sx_full, sy_full = StandardScaler(), StandardScaler()
        X_full_s = sx_full.fit_transform(X)
        y_full_s = sy_full.fit_transform(y.values.reshape(-1, 1)).ravel()
        m_full.fit(X_full_s, y_full_s)
        pred_full = sy_full.inverse_transform(m_full.predict(X_full_s).reshape(-1, 1)).ravel()
    else:
        m_full.fit(X, y)
        pred_full = m_full.predict(X)
    r2_app_full = r2_score(y.values, pred_full)

    optimisms = []
    for _ in range(n_bootstrap):
        sampled_groups = rng.choice(unique_groups, size=n_groups, replace=True)
        boot_idx = []
        for grp in sampled_groups:
            boot_idx.extend(np.where(groups == grp)[0].tolist())
        boot_idx = np.array(boot_idx)

        if use_y_std:
            sx, sy = StandardScaler(), StandardScaler()
            Xt = sx.fit_transform(X.iloc[boot_idx])
            yt = sy.fit_transform(y.iloc[boot_idx].values.reshape(-1, 1)).ravel()
            m = deepcopy(model)
            m.fit(Xt, yt)
            pred_boot = sy.inverse_transform(m.predict(Xt).reshape(-1, 1)).ravel()
            pred_orig = sy.inverse_transform(m.predict(sx.transform(X)).reshape(-1, 1)).ravel()
            r2_boot = r2_score(y.iloc[boot_idx].values, pred_boot)
            r2_orig = r2_score(y.values, pred_orig)
        else:
            m = deepcopy(model)
            m.fit(X.iloc[boot_idx], y.iloc[boot_idx])
            pred_boot = m.predict(X.iloc[boot_idx])
            pred_orig = m.predict(X)
            r2_boot = r2_score(y.iloc[boot_idx].values, pred_boot)
            r2_orig = r2_score(y.values, pred_orig)

        optimisms.append(r2_boot - r2_orig)

    r2_corrected = r2_app_full - np.mean(optimisms)
    return {
        'bootstrap_r2_apparent': r2_app_full,
        'bootstrap_r2_corrected': r2_corrected,
        'bootstrap_optimism': np.mean(optimisms)
    }


# ============================================================
# 标准化回归系数分析（替代 SHAP）
# ============================================================
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


def run_coefficient_analysis(df, feature_cols_short, feature_cols_full, model_name='ElasticNet'):
    """
    对最佳线性模型提取标准化回归系数，并通过 Bootstrap 计算 95% CI。
    返回：coef_summary DataFrame, full_model（在全部数据上拟合的模型）
    """
    df = fill_na(df, feature_cols_full)
    X = df[feature_cols_full]
    y = df[TARGET_COL]

    if model_name == 'ElasticNet':
        full_model = Pipeline([
            ('s', StandardScaler()),
            ('en', ElasticNetCV(cv=3, random_state=RANDOM_STATE, max_iter=5000))
        ])
    elif model_name == 'Ridge':
        full_model = Pipeline([
            ('s', StandardScaler()),
            ('ridge', RidgeCV(cv=3))
        ])
    elif model_name == 'Lasso':
        full_model = Pipeline([
            ('s', StandardScaler()),
            ('lasso', LassoCV(cv=3, random_state=RANDOM_STATE, max_iter=5000))
        ])
    else:
        full_model = Pipeline([
            ('s', StandardScaler()),
            ('en', ElasticNetCV(cv=3, random_state=RANDOM_STATE, max_iter=5000))
        ])

    full_model.fit(X, y)

    def model_builder():
        if model_name == 'ElasticNet':
            return Pipeline([
                ('s', StandardScaler()),
                ('en', ElasticNetCV(cv=3, random_state=RANDOM_STATE, max_iter=5000))
            ])
        elif model_name == 'Ridge':
            return Pipeline([
                ('s', StandardScaler()),
                ('ridge', RidgeCV(cv=3))
            ])
        elif model_name == 'Lasso':
            return Pipeline([
                ('s', StandardScaler()),
                ('lasso', LassoCV(cv=3, random_state=RANDOM_STATE, max_iter=5000))
            ])
        else:
            return Pipeline([
                ('s', StandardScaler()),
                ('en', ElasticNetCV(cv=3, random_state=RANDOM_STATE, max_iter=5000))
            ])

    coef_summary = bootstrap_coefficients(
        model_builder, X, y,
        groups=df['Real_Subject_ID'].values,
        y_strat=df['Myopia'].values,
        feature_names=feature_cols_short,
        n_boot=500,
        random_state=RANDOM_STATE
    )

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
# Permutation Importance + Calibration
# ============================================================
def run_permutation_importance(model, X_test, y_test, feature_names):
    r = permutation_importance(model, X_test, y_test, n_repeats=30, random_state=RANDOM_STATE, scoring='r2')
    imp_df = pd.DataFrame({
        'Feature': feature_names,
        'Importance_Mean': r.importances_mean,
        'Importance_Std': r.importances_std
    }).sort_values('Importance_Mean', ascending=False)
    return imp_df


def plot_calibration(y_true, y_pred, title, out_path):
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.scatter(y_true, y_pred, alpha=0.6, edgecolors='black', linewidth=0.5)

    # Lowess smoothing if available
    try:
        lowess = sm.nonparametric.lowess(y_pred, y_true, frac=0.6)
        ax.plot(lowess[:, 0], lowess[:, 1], 'r-', linewidth=2, label='Lowess smooth')
    except Exception:
        pass

    vmin, vmax = min(y_true.min(), y_pred.min()), max(y_true.max(), y_pred.max())
    ax.plot([vmin, vmax], [vmin, vmax], 'k--', linewidth=1.5, label='Perfect calibration')
    ax.set_xlabel('Observed Angular Density')
    ax.set_ylabel('Predicted Angular Density')
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(FIG_DIR, os.path.basename(out_path)), dpi=300, bbox_inches='tight')
    plt.close()


# ============================================================
# VIF
# ============================================================
def calc_vif(df, feature_short):
    feat_full = [FEATURE_ALL[s] for s in feature_short]
    X = df[feat_full].dropna()
    vif = pd.DataFrame({
        'Feature': feature_short,
        'VIF': [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]
    })
    return vif


# ============================================================
# 可视化
# ============================================================
def plot_overview(ml_results, coef_results, best_cfg):
    df_ml = pd.DataFrame(ml_results)

    fig, axes = plt.subplots(2, 3, figsize=(18, 11))
    fig.suptitle('SR0530 ML Kimi v2.0: Overview', fontsize=14, fontweight='bold')

    metrics = ['test_r2', 'test_corr', 'gap', 'test_mape', 'test_rmse']
    titles = ['Test R2', 'Test Correlation', 'Overfitting Gap', 'MAPE (%)', 'RMSE']
    for i, (m, t) in enumerate(zip(metrics, titles)):
        ax = axes[i // 3, i % 3]
        best_schema = df_ml.loc[df_ml.groupby(['Distance', 'Model'])[m].idxmax()]
        pivot = best_schema.pivot(index='Distance', columns='Model', values=m)
        for model in pivot.columns:
            ax.plot(pivot.index, pivot[model], 'o-', label=model, linewidth=2, markersize=6)
        if m == 'gap':
            ax.axhline(0, color='gray', linestyle='--', linewidth=0.8)
        ax.set_xlabel('Distance (mm)')
        ax.set_ylabel(t)
        ax.set_title(f'{chr(65+i)}. {t} by Distance (Best Schema)')
        ax.legend(loc='best', fontsize=7)

    # 最佳 Schema 的标准化回归系数（替代 SHAP）
    ax = axes[1, 2]
    best_coef = coef_results[best_cfg['schema']].copy()
    best_coef = best_coef.sort_values('Coef', ascending=True)
    colors = ['#e74c3c' if c < 0 else '#2ecc71' for c in best_coef['Coef']]
    ax.barh(best_coef['Feature'], best_coef['Coef'], color=colors, edgecolor='black')
    ax.axvline(0, color='black', linewidth=0.8)
    ax.set_xlabel('Standardized Coefficient')
    ax.set_title(f'F. Std Coefficients at {best_cfg["dist"]:.1f} mm ({best_cfg["schema"]}, {best_cfg["model"]})')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    fig_path = os.path.join(OUT_DIR, 'SR0530_kimi_v2_Overview.png')
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(FIG_DIR, os.path.basename(fig_path)), dpi=300, bbox_inches='tight')
    plt.close()
    print(f'  --> Saved: {fig_path}')


def plot_schema_comparison(schema_results):
    df = pd.DataFrame(schema_results)
    pivot = df.pivot(index='Distance', columns='Schema', values='Best_Test_R2')

    fig, ax = plt.subplots(figsize=(10, 6))
    for schema in pivot.columns:
        ax.plot(pivot.index, pivot[schema], 'o-', label=schema, linewidth=2, markersize=8)
    ax.axhline(0, color='gray', linestyle='--', linewidth=0.8)
    ax.set_xlabel('Distance (mm)')
    ax.set_ylabel('Best Test R2')
    ax.set_title('Schema Comparison: Best Test R2 by Distance')
    ax.legend()
    ax.grid(True, alpha=0.3)

    fig_path = os.path.join(OUT_DIR, 'SR0530_kimi_v2_SchemaComparison.png')
    plt.tight_layout()
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(FIG_DIR, os.path.basename(fig_path)), dpi=300, bbox_inches='tight')
    plt.close()
    print(f'  --> Saved: {fig_path}')


# ============================================================
# MD 报告
# ============================================================
def generate_md_report(df_ml, df_schema, vif_df, coef_df, lasso_df, perm_df, best_cfg, calib_stats):
    md = []
    md.append("# SR0530 ML Optimization Report (Kimi v2.0)\n\n")
    md.append("> **目标**：基于常规眼科参数建立视锥细胞密度预测模型。\n")
    md.append("> **策略**：四方案 (A1/A2/B/C1) + Subject/近视分层 CV + LOOCV + Bootstrap + 标准化回归系数。\n")
    md.append("> **数据**：genData/CleanDataRoi_strict/。\n\n")

    md.append("---\n\n")
    md.append("## 一、VIF 共线性诊断\n\n")
    md.append("| 特征 | VIF |\n|------|-----|\n")
    for _, row in vif_df.iterrows():
        md.append(f"| {row['Feature']} | {row['VIF']:.2f} |\n")
    md.append("\n*注：VIF > 10 提示严重共线性。方案 A1（仅 AL+Age+Gender）和 B（SE+Age+Gender）可彻底消除共线性。\n\n")

    md.append("## 二、方案说明\n\n")
    md.append("- **A1_Biomechanical_Core**：`[AL, Age, Gender]`，最精简，彻底消除共线性。\n")
    md.append("- **A2_Biomechanical_NoK**：`[AL, ACD, Age, Gender]`，剔除与 AL 共线性最高的 K。\n")
    md.append("- **B_Clinical**：`[SE, Age, Gender]`，临床筛查模型。\n")
    md.append("- **C1_Combined**：`[SE, AL, Age, Gender]`，同时包含 SE 和 AL，但剔除 K/ACD。\n\n")

    md.append("## 三、方案对比（每距离最佳模型 Test R2）\n\n")
    md.append("| 距离 (mm) | 方案 | 最佳模型 | Test R2 |\n")
    md.append("|-----------|------|----------|---------|\n")
    for _, row in df_schema.iterrows():
        md.append(f"| {row['Distance']:.1f} | {row['Schema']} | {row['Best_Model']} | {row['Best_Test_R2']:.3f} |\n")

    md.append("\n## 四、全部模型结果\n\n")
    md.append("| 距离 | 方案 | 模型 | N_eyes | N_subj | Train R2 | Test R2 | Corr | MAPE(%) | RMSE | MAE | Brier | Gap | LOOCV R2 | Boot R2_corr |\n")
    md.append("|------|------|------|--------|--------|----------|---------|------|---------|------|-----|-------|-----|----------|--------------|\n")
    for _, row in df_ml.iterrows():
        boot = f"{row['bootstrap_r2_corrected']:.3f}" if pd.notna(row['bootstrap_r2_corrected']) else "-"
        loo = f"{row['loocv_r2']:.3f}" if pd.notna(row['loocv_r2']) else "-"
        md.append(f"| {row['Distance']:.1f} | {row['Schema']} | {row['Model']} | "
                  f"{int(row['N_eyes'])} | {int(row['N_subjects'])} | "
                  f"{row['train_r2']:.3f} | {row['test_r2']:.3f} | {row['test_corr']:.3f} | "
                  f"{row['test_mape']:.2f} | {row['test_rmse']:.1f} | {row['test_mae']:.1f} | "
                  f"{row['test_brier']:.1f} | {row['gap']:.3f} | {loo} | {boot} |\n")

    md.append(f"\n**总体最佳配置**：距离 **{best_cfg['dist']:.1f} mm**，方案 **{best_cfg['schema']}**，"
              f"模型 **{best_cfg['model']}**，Test R2 = **{best_cfg['test_r2']:.3f}**。\n\n")

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

    md.append("\n## 七、Permutation Importance\n\n")
    md.append("| 特征 | Importance | Std |\n|------|------------|-----|\n")
    for _, row in perm_df.iterrows():
        md.append(f"| {row['Feature']} | {row['Importance_Mean']:.4f} | {row['Importance_Std']:.4f} |\n")

    md.append(f"\n## 八、Calibration（最佳模型）\n\n")
    md.append(f"- Brier Score (MSE): {calib_stats['brier']:.2f}\n")
    md.append(f"- MAE: {calib_stats['mae']:.2f}\n")
    md.append(f"- RMSE: {calib_stats['rmse']:.2f}\n\n")

    md.append("## 九、可视化\n\n")
    md.append("![Overview](FIG/SR0530_kimi_v2_Overview.png)\n\n")
    md.append("![Schema Comparison](FIG/SR0530_kimi_v2_SchemaComparison.png)\n\n")
    md.append("![Calibration](FIG/SR0530_kimi_v2_Calibration.png)\n\n")

    md.append("---\n\n")
    md.append("*Report generated by SR_ML_kimi_v2.py*\n")

    md_path = os.path.join(BASE_DIR, 'report', 'SR0530_kimi_v2_ML_Optimization_Report.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(''.join(md))
    print(f'  --> Report: {md_path}')


# ============================================================
# 主程序
# ============================================================
def run_loocv_for_index(model, X, y, groups, use_std):
    """辅助：为指定配置计算 LOOCV 并更新结果字典"""
    return eval_loocv(model, X, y, groups, use_y_std=use_std)


def get_model_by_name(name):
    for n, m, u in build_models():
        if n == name:
            return m, u
    return None, False


def main():
    print("=" * 75)
    print("SR0530 Task 2: ML Optimization (Kimi v2.0)")
    print("Schemas A1/A2/B/C1 + StratifiedGroupKFold + LOOCV + Bootstrap + Std Coefficients")
    print("=" * 75)

    print("\nStep 1: Loading subject mapping...")
    eye_to_subject = load_subject_mapping()

    print("\nStep 2: Loading and aggregating data...")
    all_data = load_distance_data()
    distances = sorted(all_data.keys())

    print("\nStep 3: VIF collinearity diagnosis (full feature set at 1.0 mm)...")
    df_vif = aggregate_distance(all_data[distances[0]], distances[0], eye_to_subject)
    vif_df = calc_vif(df_vif, list(FEATURE_ALL.keys()))
    print(vif_df.to_string(index=False))

    print("\nStep 4: Running CV for all configurations...")
    ml_results = []
    schema_results = []
    distance_dfs = {}
    best_overall = {'test_r2': -np.inf, 'dist': None, 'schema': None, 'model': None, 'index': None}
    best_per_schema = {s: {'test_r2': -np.inf, 'dist': None, 'model': None, 'index': None} for s in SCHEMA}

    for dist in distances:
        print(f"\n--- Distance {dist:.1f} mm ---")
        df = aggregate_distance(all_data[dist], dist, eye_to_subject)
        distance_dfs[dist] = df

        groups_all = df['Real_Subject_ID'].values
        n_subjects = len(np.unique(groups_all))
        n_splits = min(5, n_subjects // 2)
        if n_splits < 2:
            print(f"    ⚠️ Warning: only {n_subjects} subjects at distance {dist}, skipping ML for this distance.")
            continue

        for schema_name, feat_short in SCHEMA.items():
            feat_full = [FEATURE_ALL[s] for s in feat_short]
            df_sub = fill_na(df.copy(), feat_full)

            X = df_sub[feat_full]
            y = df_sub[TARGET_COL]
            groups = df_sub['Real_Subject_ID'].values
            y_strat = df_sub['Myopia'].values

            print(f"  [{schema_name}] N={len(df_sub)} eyes/{n_subjects} subjects, folds={n_splits}")

            models = build_models()
            best_r2 = -np.inf
            best_model_name = None

            for name, model, use_std in models:
                r_cv = eval_cv(model, X, y, groups, y_strat, use_y_std=use_std, n_splits=n_splits)
                if r_cv is None:
                    continue

                res = {
                    'Distance': dist,
                    'Schema': schema_name,
                    'Model': name,
                    'N_eyes': len(df_sub),
                    'N_subjects': n_subjects,
                    'Features': ','.join(feat_short),
                    **r_cv,
                    'loocv_r2': np.nan,
                    'loocv_corr': np.nan,
                    'loocv_mape': np.nan,
                    'loocv_rmse': np.nan,
                    'loocv_mae': np.nan,
                    'loocv_brier': np.nan,
                    'bootstrap_r2_apparent': np.nan,
                    'bootstrap_r2_corrected': np.nan,
                    'bootstrap_optimism': np.nan
                }
                idx = len(ml_results)
                ml_results.append(res)
                print(f"    {name:20s}: CV R2={r_cv['test_r2']:.3f}, "
                      f"MAPE={r_cv['test_mape']:.2f}%, RMSE={r_cv['test_rmse']:.1f}, Gap={r_cv['gap']:.3f}")

                if r_cv['test_r2'] > best_r2:
                    best_r2 = r_cv['test_r2']
                    best_model_name = name

                if r_cv['test_r2'] > best_overall['test_r2']:
                    best_overall.update({
                        'test_r2': r_cv['test_r2'],
                        'dist': dist,
                        'schema': schema_name,
                        'model': name,
                        'index': idx
                    })

                if r_cv['test_r2'] > best_per_schema[schema_name]['test_r2']:
                    best_per_schema[schema_name].update({
                        'test_r2': r_cv['test_r2'],
                        'dist': dist,
                        'model': name,
                        'index': idx
                    })

            schema_results.append({
                'Distance': dist,
                'Schema': schema_name,
                'Best_Model': best_model_name,
                'Best_Test_R2': best_r2
            })

    df_ml = pd.DataFrame(ml_results)

    print(f"\n[Best Overall] Distance={best_overall['dist']:.1f} mm, Schema={best_overall['schema']}, "
          f"Model={best_overall['model']}, Test R2={best_overall['test_r2']:.3f}")

    print("\nStep 5: LOOCV for best model per schema and best overall...")
    loocv_targets = set()
    for s, info in best_per_schema.items():
        loocv_targets.add(info['index'])
    loocv_targets.add(best_overall['index'])

    for idx in loocv_targets:
        if idx is None:
            continue
        res = ml_results[idx]
        dist = res['Distance']
        schema_name = res['Schema']
        model_name = res['Model']
        feat_short = SCHEMA[schema_name]
        feat_full = [FEATURE_ALL[s] for s in feat_short]
        df_sub = fill_na(distance_dfs[dist].copy(), feat_full)
        X = df_sub[feat_full]
        y = df_sub[TARGET_COL]
        groups = df_sub['Real_Subject_ID'].values
        model, use_std = get_model_by_name(model_name)
        r_loo = eval_loocv(model, X, y, groups, use_y_std=use_std)
        for k, v in r_loo.items():
            df_ml.loc[idx, k] = v
        print(f"  [{schema_name}, {dist:.1f}mm, {model_name}] LOOCV R2={r_loo['loocv_r2']:.3f}")

    print("\nStep 6: Bootstrap internal validation for best overall model...")
    best_dist = best_overall['dist']
    best_schema = best_overall['schema']
    best_model_name = best_overall['model']
    df_best = distance_dfs[best_dist]
    feat_short = SCHEMA[best_schema]
    feat_full = [FEATURE_ALL[s] for s in feat_short]
    df_best = fill_na(df_best, feat_full)
    X_best = df_best[feat_full]
    y_best = df_best[TARGET_COL]
    groups_best = df_best['Real_Subject_ID'].values

    best_model, best_use_std = get_model_by_name(best_model_name)
    boot_res = eval_bootstrap(best_model, X_best, y_best, groups_best, use_y_std=best_use_std, n_bootstrap=N_BOOTSTRAP)
    df_ml.loc[best_overall['index'], 'bootstrap_r2_apparent'] = boot_res['bootstrap_r2_apparent']
    df_ml.loc[best_overall['index'], 'bootstrap_r2_corrected'] = boot_res['bootstrap_r2_corrected']
    df_ml.loc[best_overall['index'], 'bootstrap_optimism'] = boot_res['bootstrap_optimism']
    print(f"  Bootstrap apparent R2={boot_res['bootstrap_r2_apparent']:.3f}, "
          f"corrected R2={boot_res['bootstrap_r2_corrected']:.3f}, "
          f"optimism={boot_res['bootstrap_optimism']:.3f}")

    print("\nStep 7: Standardized coefficient analysis on best model...")
    coef_results = {}
    coef_df, _ = run_coefficient_analysis(df_best, feat_short, feat_full, model_name=best_model_name)
    coef_results[best_schema] = coef_df
    print("  Standardized coefficients (with Bootstrap 95% CI):")
    for _, row in coef_df.iterrows():
        ci_zero = "(includes 0)" if row['CI_Includes_Zero'] else "(excludes 0)"
        print(f"    {row['Feature']:<10s}: {row['Coef']:.3f} [{row['CI_Lower']:.3f}, {row['CI_Upper']:.3f}] {ci_zero}")

    print(f"\nStep 8: Lasso supplementary analysis at {best_dist:.1f} mm...")
    lasso_short = SCHEMA['A2_Biomechanical_NoK']
    lasso_full = [FEATURE_ALL[s] for s in lasso_short]
    lasso_df, _ = run_coefficient_analysis(df_best, lasso_short, lasso_full, model_name='Lasso')
    print("  Lasso coefficients (A2 features):")
    for _, row in lasso_df.iterrows():
        print(f"    {row['Feature']:<10s}: {row['Coef']:.3f}")

    print("\nStep 9: Permutation importance on best model...")
    n_perm_splits = min(5, len(np.unique(groups_best)) // 2)
    if n_perm_splits >= 2:
        splits = stratified_group_kfold(groups_best, df_best['Myopia'].values, n_splits=n_perm_splits)
        train_idx, test_idx = splits[0]
        best_model.fit(X_best.iloc[train_idx], y_best.iloc[train_idx])
        perm_df = run_permutation_importance(best_model, X_best.iloc[test_idx], y_best.iloc[test_idx], feat_short)
    else:
        best_model.fit(X_best, y_best)
        perm_df = run_permutation_importance(best_model, X_best, y_best, feat_short)
    print(perm_df.to_string(index=False))

    print("\nStep 10: Calibration plot for best model...")
    best_model.fit(X_best, y_best)
    y_pred_calib = best_model.predict(X_best)
    calib_stats = {
        'brier': mean_squared_error(y_best, y_pred_calib),
        'mae': mean_absolute_error(y_best, y_pred_calib),
        'rmse': np.sqrt(mean_squared_error(y_best, y_pred_calib))
    }
    plot_calibration(y_best.values, y_pred_calib,
                     f"Calibration: {best_schema} at {best_dist:.1f} mm ({best_model_name})",
                     os.path.join(OUT_DIR, 'SR0530_kimi_v2_Calibration.png'))

    print("\nStep 11: Generating figures...")
    plot_overview(ml_results, coef_results, best_overall)
    plot_schema_comparison(schema_results)

    print("\nStep 12: Saving results...")
    df_ml.to_csv(os.path.join(OUT_DIR, 'SR0530_kimi_v2_ML_Results.csv'), index=False, encoding='utf-8-sig')
    pd.DataFrame(schema_results).to_csv(os.path.join(OUT_DIR, 'SR0530_kimi_v2_SchemaBest.csv'),
                                        index=False, encoding='utf-8-sig')
    coef_df.to_csv(os.path.join(OUT_DIR, 'SR0530_kimi_v2_Coefficients.csv'), index=False, encoding='utf-8-sig')
    lasso_df.to_csv(os.path.join(OUT_DIR, 'SR0530_kimi_v2_Lasso_Coefficients.csv'), index=False, encoding='utf-8-sig')
    perm_df.to_csv(os.path.join(OUT_DIR, 'SR0530_kimi_v2_PermImportance.csv'), index=False, encoding='utf-8-sig')

    print("\nStep 13: Generating MD report...")
    generate_md_report(df_ml, pd.DataFrame(schema_results), vif_df, coef_df, lasso_df, perm_df, best_overall, calib_stats)

    print("\n" + "=" * 75)
    print("Task 2 complete!")
    print("=" * 75)


if __name__ == '__main__':
    main()
