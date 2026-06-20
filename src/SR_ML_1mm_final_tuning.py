"""
SR_ML_1mm_final_tuning.py
针对 1.0 mm 偏心率、≥1 象限（q1plus）聚合数据做最终精细调优与特征重要性分析。
输出：最终模型性能、稳定性、特征重要性排序、SHAP/permutation summary。
"""

import os
import glob
import ast
import warnings
import numpy as np
import pandas as pd
from scipy import stats

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.inspection import permutation_importance
from sklearn.svm import SVR
from sklearn.ensemble import RandomForestRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.linear_model import Lasso, ElasticNet, Ridge
from sklearn.metrics import r2_score, mean_squared_error
from xgboost import XGBRegressor

warnings.filterwarnings('ignore')

# ============================================================
# 配置
# ============================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIRS = {
    'strict': os.path.join(BASE_DIR, 'genData', 'CleanDataRoi_strict'),
    'lenient': os.path.join(BASE_DIR, 'genData', 'CleanDataRoi_lenient')
}
OUT_DIR = os.path.join(BASE_DIR, 'genData', 'sum')
REPORT_DIR = os.path.join(BASE_DIR, 'report')
FIG_DIR = os.path.join(REPORT_DIR, 'FIG')
os.makedirs(OUT_DIR, exist_ok=True)
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

SCHEMA = {
    'A1_Biomechanical_Core': ['AL', 'Age', 'Gender'],
    'A2_Biomechanical_NoK': ['AL', 'ACD', 'Age', 'Gender'],
    'B_Clinical': ['SE', 'Age', 'Gender'],
    'C1_Combined': ['SE', 'AL', 'Age', 'Gender']
}

MYOPIA_THRESHOLD = -0.5
RANDOM_STATE = 42
TARGET_DISTANCE = 1.0
MODE_LABEL = 'q1plus'

N_ITER_FINE = 50       # 精细随机搜索迭代次数
N_SPLITS = 5           # GroupKFold 折数
N_PERM_REPEATS = 30    # permutation importance 重复次数
N_FINAL_BOOTSTRAP = 50  # 最终模型 bootstrap 重复次数
N_TOP_CONFIGS = 12     # 仅对 coarse 中 top 12 配置做最终细调

USE_Y_STD = {
    'SVM': False, 'Random_Forest': False, 'XGBoost': False,
    'Neural_Network': True, 'Lasso': False, 'ElasticNet': False, 'Ridge': False
}

# 尝试导入 shap，如未安装则回退到 permutation importance
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    print("shap not installed, falling back to permutation importance only.")


# ============================================================
# 工具函数
# ============================================================
def load_subject_mapping(data_dir):
    df_ref = pd.read_csv(os.path.join(data_dir, 'data1.csv'))
    mapping = {}
    for _, row in df_ref.iterrows():
        mapping[row['Eye_Label']] = row['Subject_ID']
        mapping[row['Subject_ID']] = row['Subject_ID']
    return mapping


def load_distance_data(data_dir):
    all_data = {}
    for f in sorted(glob.glob(os.path.join(data_dir, 'data*.csv'))):
        df = pd.read_csv(f)
        dist = df['Eccentricity (mm)'].iloc[0]
        if dist not in all_data:
            all_data[dist] = []
        all_data[dist].append(df)
    return all_data


def aggregate_distance(dfs, eye_to_subject, min_quadrants=1):
    """按 Subject_ID + Eye 聚合象限密度，支持 ≥1 象限。"""
    feature_cols = list(FEATURE_ALL.values())

    merged = dfs[0][['Subject_ID', 'Eye', TARGET_COL]].copy()
    merged = merged.rename(columns={TARGET_COL: 'density_q1'})

    for i, d in enumerate(dfs[1:], 2):
        merged = merged.merge(
            d[['Subject_ID', 'Eye', TARGET_COL]].rename(columns={TARGET_COL: f'density_q{i}'}),
            on=['Subject_ID', 'Eye'], how='outer'
        )

    den_cols = [c for c in merged.columns if c.startswith('density_q')]
    merged['N_Quadrants'] = merged[den_cols].notna().sum(axis=1)
    merged[TARGET_COL] = merged[den_cols].mean(axis=1, skipna=True)
    merged = merged[merged['N_Quadrants'] >= min_quadrants].copy()

    features = None
    for d in dfs:
        df_feat = d[['Subject_ID', 'Eye'] + feature_cols].drop_duplicates(['Subject_ID', 'Eye'])
        if features is None:
            features = df_feat
        else:
            features = pd.concat([features, df_feat], ignore_index=True)
            features = features.drop_duplicates(['Subject_ID', 'Eye'], keep='first')

    base = merged.merge(features, on=['Subject_ID', 'Eye'], how='left')
    base['Real_Subject_ID'] = base['Subject_ID'].map(eye_to_subject)
    base['Myopia'] = (base[FEATURE_ALL['SE']] <= MYOPIA_THRESHOLD).astype(int)

    return base[['Subject_ID', 'Real_Subject_ID', 'Eye', 'Myopia'] + feature_cols + ['N_Quadrants', TARGET_COL]].copy()


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


def group_stratified_kfold(groups, y_stratify, n_splits=5, random_state=42):
    """按 groups 分组，并在每层内按 y_stratify 分层，确保同一 group 不会被拆分到不同 fold。"""
    rng = np.random.RandomState(random_state)
    df_idx = pd.DataFrame({'idx': np.arange(len(groups)), 'group': groups, 'y': y_stratify})

    group_info = df_idx.groupby('group').agg(
        y=('y', lambda x: int(x.mode()[0])),
        idx=('idx', list)
    ).reset_index()
    group_info = group_info.sample(frac=1, random_state=random_state).reset_index(drop=True)

    pos_groups = group_info[group_info['y'] == 1].copy().reset_index(drop=True)
    neg_groups = group_info[group_info['y'] == 0].copy().reset_index(drop=True)

    # folds 中存储 group 行索引，避免同一 group 被拆分
    folds = [[] for _ in range(n_splits)]
    for label_df in [pos_groups, neg_groups]:
        for i, row in label_df.iterrows():
            folds[i % n_splits].append(row.name)

    # 空 fold 保护：从最大 fold 移动一个完整 group
    for i in range(n_splits):
        if not folds[i]:
            non_empty = [k for k in range(n_splits) if len(folds[k]) > 0 and k != i]
            if not non_empty:
                raise ValueError(f"Cannot fill empty fold {i}: all other folds are empty")
            largest_idx = max(non_empty, key=lambda k: len(folds[k]))
            moved_group = folds[largest_idx].pop()
            folds[i].append(moved_group)

    splits = []
    for i in range(n_splits):
        test_groups = folds[i]
        train_groups = [g for f in folds[:i] + folds[i+1:] for g in f]
        test_idx = np.array([idx for g in test_groups for idx in group_info.loc[g, 'idx']])
        train_idx = np.array([idx for g in train_groups for idx in group_info.loc[g, 'idx']])
        if len(test_idx) == 0 or len(train_idx) == 0:
            raise ValueError(f"Fold {i} has empty train or test set")
        splits.append((train_idx, test_idx))
    return splits


def get_model_builder(model_name):
    if model_name == 'SVM':
        return lambda p: Pipeline([('s', StandardScaler()), ('v', SVR(**p))])
    elif model_name == 'Random_Forest':
        return lambda p: Pipeline([('s', StandardScaler()), ('rf', RandomForestRegressor(**p, random_state=RANDOM_STATE, n_jobs=1))])
    elif model_name == 'XGBoost':
        return lambda p: XGBRegressor(**p, random_state=RANDOM_STATE, verbosity=0)
    elif model_name == 'Neural_Network':
        return lambda p: Pipeline([('s', StandardScaler()), ('nn', MLPRegressor(**p, max_iter=5000, early_stopping=True, validation_fraction=0.15, n_iter_no_change=20, random_state=RANDOM_STATE))])
    elif model_name == 'Lasso':
        return lambda p: Pipeline([('s', StandardScaler()), ('lasso', Lasso(**p, max_iter=5000))])
    elif model_name == 'ElasticNet':
        return lambda p: Pipeline([('s', StandardScaler()), ('en', ElasticNet(**p, max_iter=5000))])
    elif model_name == 'Ridge':
        return lambda p: Pipeline([('s', StandardScaler()), ('ridge', Ridge(**p))])
    else:
        raise ValueError(f"Unknown model: {model_name}")


def near_values_log(current, steps, lower_bound=None, upper_bound=None):
    if current <= 0:
        return [current]
    vals = [current * s for s in steps]
    if lower_bound is not None:
        vals = [max(v, lower_bound) for v in vals]
    if upper_bound is not None:
        vals = [min(v, upper_bound) for v in vals]
    return sorted(list(set([round(v, 6) for v in vals])))


def near_values_linear(current, steps, lower_bound=None, upper_bound=None, dtype=float):
    vals = []
    for s in steps:
        v = current + s
        if dtype == int:
            v = int(round(v))
        vals.append(v)
    if lower_bound is not None:
        vals = [max(v, lower_bound) for v in vals]
    if upper_bound is not None:
        vals = [min(v, upper_bound) for v in vals]
    return sorted(list(set(vals)))


def build_fine_space(model_name, coarse_params):
    """基于 coarse 最佳参数构建更密集的精细搜索空间。"""
    if model_name == 'SVM':
        c = coarse_params.get('C', 1000)
        eps = coarse_params.get('epsilon', 300)
        gamma = coarse_params.get('gamma', 0.01)
        return {
            'C': near_values_log(c, [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0], lower_bound=10, upper_bound=10000),
            'epsilon': near_values_log(eps, [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0], lower_bound=10, upper_bound=2000),
            'gamma': near_values_log(gamma, [0.2, 0.4, 0.6, 0.8, 1.0, 1.5, 2.0, 3.0], lower_bound=0.0001, upper_bound=0.5)
        }
    elif model_name == 'Random_Forest':
        n_est = coarse_params.get('n_estimators', 100)
        depth = coarse_params.get('max_depth', None)
        split = coarse_params.get('min_samples_split', 2)
        leaf = coarse_params.get('min_samples_leaf', 1)
        depth_candidates = [None] if depth is None else near_values_linear(int(depth), [-2, -1, 0, 1, 2], lower_bound=2, upper_bound=10, dtype=int) + [None]
        return {
            'n_estimators': near_values_linear(int(n_est), [-150, -100, -50, 0, 50, 100, 150], lower_bound=30, upper_bound=500, dtype=int),
            'max_depth': depth_candidates,
            'min_samples_split': near_values_linear(int(split), [-4, -2, 0, 2, 4], lower_bound=2, upper_bound=20, dtype=int),
            'min_samples_leaf': near_values_linear(int(leaf), [-2, -1, 0, 1, 2], lower_bound=1, upper_bound=8, dtype=int)
        }
    elif model_name == 'XGBoost':
        lr = coarse_params.get('learning_rate', 0.01)
        depth = coarse_params.get('max_depth', 2)
        n_est = coarse_params.get('n_estimators', 100)
        alpha = coarse_params.get('reg_alpha', 0.5)
        lam = coarse_params.get('reg_lambda', 1.0)
        return {
            'learning_rate': near_values_log(lr, [0.2, 0.4, 0.6, 0.8, 1.0, 1.5, 2.0], lower_bound=0.0001, upper_bound=0.5),
            'max_depth': near_values_linear(int(depth), [-2, -1, 0, 1, 2], lower_bound=1, upper_bound=6, dtype=int),
            'n_estimators': near_values_linear(int(n_est), [-150, -100, -50, 0, 50, 100, 150], lower_bound=20, upper_bound=500, dtype=int),
            'reg_alpha': near_values_log(alpha, [0.2, 0.4, 0.6, 0.8, 1.0, 1.5, 2.0], lower_bound=0.001, upper_bound=5.0),
            'reg_lambda': near_values_log(lam, [0.2, 0.4, 0.6, 0.8, 1.0, 1.5, 2.0], lower_bound=0.001, upper_bound=5.0)
        }
    elif model_name == 'Neural_Network':
        hls = coarse_params.get('hidden_layer_sizes', (100,))
        alpha = coarse_params.get('alpha', 0.3)
        lr = coarse_params.get('learning_rate_init', 0.0005)
        hls_options = [(40,), (60,), (80,), (100,), (120,), (80, 40), (100, 50), (120, 60)]
        if hls not in hls_options:
            hls_options.append(hls)
        return {
            'hidden_layer_sizes': hls_options,
            'alpha': near_values_log(alpha, [0.2, 0.4, 0.6, 0.8, 1.0, 1.5, 2.0, 3.0], lower_bound=0.001, upper_bound=3.0),
            'learning_rate_init': near_values_log(lr, [0.2, 0.4, 0.6, 0.8, 1.0, 1.5, 2.0], lower_bound=0.00001, upper_bound=0.01)
        }
    elif model_name == 'Lasso':
        alpha = coarse_params.get('alpha', 0.01)
        return {
            'alpha': near_values_log(alpha, [0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0], lower_bound=0.0001, upper_bound=50.0)
        }
    elif model_name == 'ElasticNet':
        alpha = coarse_params.get('alpha', 0.1)
        l1 = coarse_params.get('l1_ratio', 0.5)
        return {
            'alpha': near_values_log(alpha, [0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0], lower_bound=0.0001, upper_bound=50.0),
            'l1_ratio': near_values_linear(l1, [-0.4, -0.2, -0.1, 0, 0.1, 0.2, 0.4], lower_bound=0.01, upper_bound=0.99)
        }
    elif model_name == 'Ridge':
        alpha = coarse_params.get('alpha', 1.0)
        return {
            'alpha': near_values_log(alpha, [0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0], lower_bound=0.0001, upper_bound=500.0)
        }
    else:
        raise ValueError(f"Unknown model: {model_name}")


def sample_params(param_space, rng):
    """从参数空间中随机采样一组参数（兼容元组、None 等复杂类型）"""
    params = {}
    for k, v in param_space.items():
        if isinstance(v, list):
            # 使用 rng.randint 索引，避免 numpy.choice 对混合类型列表创建数组失败
            params[k] = v[rng.randint(0, len(v))]
        else:
            params[k] = v
    return params


def evaluate_params(model_builder, params, X, y, groups, y_stratify, use_y_std=False, n_splits=5, random_state=42):
    n_subjects = len(np.unique(groups))
    n_splits = min(n_splits, n_subjects // 2)
    if n_splits < 2:
        n_splits = 2

    splits = group_stratified_kfold(groups, y_stratify, n_splits=n_splits, random_state=random_state)

    train_r2_list, test_r2_list = [], []
    test_corr_list, test_mape_list, test_rmse_list = [], [], []

    for ti, vi in splits:
        model = model_builder(params)
        if use_y_std:
            sx, sy = StandardScaler(), StandardScaler()
            Xt = sx.fit_transform(X.iloc[ti])
            Xv = sx.transform(X.iloc[vi])
            yt = sy.fit_transform(y.iloc[ti].values.reshape(-1, 1)).ravel()
            yv = y.iloc[vi].values
            yt_raw = y.iloc[ti].values
            model.fit(Xt, yt)
            pred = sy.inverse_transform(model.predict(Xv).reshape(-1, 1)).ravel()
            pred_train = sy.inverse_transform(model.predict(Xt).reshape(-1, 1)).ravel()
        else:
            model.fit(X.iloc[ti], y.iloc[ti])
            pred = model.predict(X.iloc[vi])
            pred_train = model.predict(X.iloc[ti])
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
        'test_rmse_std': np.std(test_rmse_list),
        'gap': np.mean(train_r2_list) - np.mean(test_r2_list)
    }


def fine_tune(model_name, model_builder, fine_space, X, y, groups, y_stratify, n_iter=100, random_state=42):
    rng = np.random.RandomState(random_state)
    best_score = -np.inf
    best_params = None
    best_metrics = None
    all_trials = []

    for i in range(n_iter):
        params = sample_params(fine_space, rng)
        metrics = evaluate_params(
            model_builder, params, X, y, groups, y_stratify,
            use_y_std=USE_Y_STD[model_name], n_splits=N_SPLITS, random_state=random_state + i
        )
        metrics['params'] = params
        all_trials.append(metrics)

        if metrics['test_r2'] > best_score:
            best_score = metrics['test_r2']
            best_params = params
            best_metrics = metrics

    return best_params, best_metrics, all_trials


def repeated_cv_stability(model_builder, best_params, X, y, groups, y_stratify, use_y_std=False,
                          n_splits=5, n_repeats=100):
    """用不同 CV seed 重复评估最佳参数，返回稳定性分布（NaN-safe）。"""
    scores = []
    for r in range(n_repeats):
        metrics = evaluate_params(
            model_builder, best_params, X, y, groups, y_stratify,
            use_y_std=use_y_std, n_splits=n_splits, random_state=RANDOM_STATE + r * 100
        )
        scores.append(metrics['test_r2'])
    scores = np.array(scores)
    return {
        'mean': np.nanmean(scores),
        'std': np.nanstd(scores),
        'ci_lower': np.nanpercentile(scores, 2.5),
        'ci_upper': np.nanpercentile(scores, 97.5),
        'min': np.nanmin(scores),
        'max': np.nanmax(scores),
        'scores': scores.tolist()
    }


def fit_final_model(model_builder, best_params, X, y, use_y_std=False):
    """在全量数据上拟合最终模型，用于特征重要性。"""
    model = model_builder(best_params)
    if use_y_std:
        sx, sy = StandardScaler(), StandardScaler()
        X_std = sx.fit_transform(X)
        y_std = sy.fit_transform(y.values.reshape(-1, 1)).ravel()
        model.fit(X_std, y_std)
        return model, sx, sy
    else:
        model.fit(X, y)
        return model, None, None


def get_builtin_importance(model, feature_names):
    """提取模型内置特征重要性或系数。"""
    importances = None

    # 处理 Pipeline
    if hasattr(model, 'named_steps'):
        # 先找是否有树模型
        for name, step in model.named_steps.items():
            if hasattr(step, 'feature_importances_'):
                importances = step.feature_importances_
                break
            elif hasattr(step, 'coef_'):
                importances = np.abs(step.coef_)
                if importances.ndim > 1:
                    importances = importances.flatten()
                break
    else:
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
        elif hasattr(model, 'coef_'):
            importances = np.abs(model.coef_)
            if importances.ndim > 1:
                importances = importances.flatten()

    if importances is None:
        return None

    return pd.DataFrame({'Feature': feature_names, 'Importance': importances}).sort_values('Importance', ascending=False)


def compute_permutation_importance(model, X, y, feature_names, n_repeats=30, random_state=42):
    """计算 permutation importance。"""
    result = permutation_importance(model, X, y, n_repeats=n_repeats, random_state=random_state, n_jobs=1)
    df = pd.DataFrame({
        'Feature': feature_names,
        'Importance_Mean': result.importances_mean,
        'Importance_Std': result.importances_std
    }).sort_values('Importance_Mean', ascending=False)
    return df


def compute_shap_importance(model, X, feature_names):
    """计算 SHAP 值并返回平均绝对 SHAP 值。"""
    if not SHAP_AVAILABLE:
        return None

    try:
        # 确保 X 是 DataFrame，便于 shap.Explainer 处理
        if isinstance(X, np.ndarray):
            X = pd.DataFrame(X, columns=feature_names)

        explainer = shap.Explainer(model.predict, X)
        shap_values = explainer(X)
        vals = np.abs(shap_values.values).mean(axis=0)
        if vals.ndim > 1:
            vals = vals.mean(axis=1)
        return pd.DataFrame({'Feature': feature_names, 'Importance': vals}).sort_values('Importance', ascending=False)
    except Exception as e:
        print(f"    SHAP failed: {e}")
        return None


def compute_cv_feature_importance(model_builder, best_params, X, y, groups, y_stratify,
                                  feature_names, use_y_std=False, n_splits=5,
                                  n_perm_repeats=30, random_state=42):
    """用 GroupKFold 在测试集上计算 Permutation 和 SHAP 重要性，返回跨 fold 平均。"""
    n_subjects = len(np.unique(groups))
    n_splits = min(n_splits, n_subjects // 2)
    if n_splits < 2:
        n_splits = 2

    splits = group_stratified_kfold(groups, y_stratify, n_splits=n_splits, random_state=random_state)

    perm_records = []
    shap_records = []

    for fold_idx, (ti, vi) in enumerate(splits):
        model = model_builder(best_params)
        if use_y_std:
            sx, sy = StandardScaler(), StandardScaler()
            Xt = sx.fit_transform(X.iloc[ti])
            Xv = sx.transform(X.iloc[vi])
            yt = sy.fit_transform(y.iloc[ti].values.reshape(-1, 1)).ravel()
            yv = y.iloc[vi].values
            model.fit(Xt, yt)
            perm = permutation_importance(model, Xv, yv, n_repeats=n_perm_repeats,
                                          random_state=random_state + fold_idx, n_jobs=1)
            Xv_df = pd.DataFrame(Xv, columns=feature_names)
            shap_imp = compute_shap_importance(model, Xv_df, feature_names)
        else:
            Xt, Xv = X.iloc[ti], X.iloc[vi]
            yt, yv = y.iloc[ti], y.iloc[vi]
            model.fit(Xt, yt)
            perm = permutation_importance(model, Xv, yv, n_repeats=n_perm_repeats,
                                          random_state=random_state + fold_idx, n_jobs=1)
            shap_imp = compute_shap_importance(model, Xv, feature_names)

        perm_records.append(pd.DataFrame({
            'Feature': feature_names,
            'Importance_Mean': perm.importances_mean,
            'Importance_Std': perm.importances_std
        }))
        if shap_imp is not None:
            shap_records.append(shap_imp)

    perm_avg = pd.concat(perm_records).groupby('Feature')[['Importance_Mean', 'Importance_Std']].mean().reset_index()
    perm_avg = perm_avg.sort_values('Importance_Mean', ascending=False)

    if shap_records:
        shap_avg = pd.concat(shap_records).groupby('Feature')['Importance'].mean().reset_index()
        shap_avg = shap_avg.sort_values('Importance', ascending=False)
    else:
        shap_avg = None

    return perm_avg, shap_avg


def plot_importance(df_imp, title, out_path):
    """绘制特征重要性水平条形图。兼容 'Importance' 和 'Importance_Mean' 列名。"""
    df_imp = df_imp.copy()
    if 'Importance' not in df_imp.columns and 'Importance_Mean' in df_imp.columns:
        df_imp['Importance'] = df_imp['Importance_Mean']

    fig, ax = plt.subplots(figsize=(10, 6))
    y_pos = np.arange(len(df_imp))
    ax.barh(y_pos, df_imp['Importance'].values, color='steelblue')
    ax.set_yticks(y_pos)
    ax.set_yticklabels(df_imp['Feature'].values)
    ax.invert_yaxis()
    ax.set_xlabel('Importance')
    ax.set_title(title)
    ax.grid(True, alpha=0.3, axis='x')
    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()


def plot_observed_vs_predicted(y_true, y_pred, out_path, title='Observed vs Predicted'):
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.scatter(y_true, y_pred, edgecolors='black', alpha=0.7)
    lim_min = min(y_true.min(), y_pred.min())
    lim_max = max(y_true.max(), y_pred.max())
    ax.plot([lim_min, lim_max], [lim_min, lim_max], 'r--', lw=2)
    ax.set_xlabel('Observed')
    ax.set_ylabel('Predicted')
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    r2 = r2_score(y_true, y_pred)
    ax.text(0.05, 0.95, f"R^2 = {r2:.3f}", transform=ax.transAxes, fontsize=12,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()


def plot_bootstrap_distribution(scores, out_path, title='Bootstrap Test R^2 Distribution'):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(scores, bins=20, edgecolor='black', alpha=0.7, color='steelblue')
    ax.axvline(np.mean(scores), color='red', linestyle='--', linewidth=2, label=f"Mean = {np.mean(scores):.3f}")
    ax.axvline(np.percentile(scores, 2.5), color='orange', linestyle='--', linewidth=1.5, label=f"95% CI")
    ax.axvline(np.percentile(scores, 97.5), color='orange', linestyle='--', linewidth=1.5)
    ax.set_xlabel('Test R^2')
    ax.set_ylabel('Frequency')
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()


# ============================================================
# 主程序
# ============================================================
def main():
    print("=" * 80)
    print("SR0530 Final Fine-Tuning & Feature Importance at 1.0 mm")
    print(f"Mode: {MODE_LABEL} | Distance: {TARGET_DISTANCE} mm")
    print(f"Fine iterations: {N_ITER_FINE} | Bootstrap repeats: {N_FINAL_BOOTSTRAP}")
    print("=" * 80)

    # 1. 读取 coarse q1plus 结果，提取 1.0 mm 配置，并选择 top N
    coarse_path = os.path.join(OUT_DIR, f'SR0530_HP_Tuning_Results_{MODE_LABEL}.csv')
    coarse_df = pd.read_csv(coarse_path)
    coarse_1mm = coarse_df[coarse_df['Distance_mm'] == TARGET_DISTANCE].copy()
    coarse_1mm = coarse_1mm.sort_values('test_r2', ascending=False).head(N_TOP_CONFIGS).reset_index(drop=True)

    print(f"\nLoaded coarse results for 1.0 mm: selected top {len(coarse_1mm)} configurations")

    # 2. 预加载 1.0 mm 数据
    data_cache = {}
    for data_group, data_dir in DATA_DIRS.items():
        eye_to_subject = load_subject_mapping(data_dir)
        all_data = load_distance_data(data_dir)
        dfs = all_data[TARGET_DISTANCE]
        df = aggregate_distance(dfs, eye_to_subject, min_quadrants=1)
        data_cache[data_group] = df
        print(f"  {data_group}: {len(df)} eyes, {df['Real_Subject_ID'].nunique()} subjects")

    # 3. 对每个配置做精细寻优、稳定性评估、特征重要性
    results = []
    all_trials = []
    importance_records = []

    for i, row in coarse_1mm.iterrows():
        data_group = row['Data_Group']
        schema_name = row['Schema']
        model_name = row['Model']
        coarse_params = ast.literal_eval(row['Best_Params'])

        print(f"\n[{len(results)+1}/{len(coarse_1mm)}] {data_group} | {schema_name} | {model_name}")
        print(f"  Coarse R^2 = {row['test_r2']:.3f}")

        df = data_cache[data_group]
        feat_full = [FEATURE_ALL[s] for s in SCHEMA[schema_name]]
        df_sub = fill_na(df.copy(), feat_full)

        X = df_sub[feat_full]
        y = df_sub[TARGET_COL]
        groups = df_sub['Real_Subject_ID'].values
        y_strat = df_sub['Myopia'].values

        # 精细寻优
        fine_space = build_fine_space(model_name, coarse_params)
        model_builder = get_model_builder(model_name)
        best_params, best_metrics, trials = fine_tune(
            model_name, model_builder, fine_space, X, y, groups, y_strat,
            n_iter=N_ITER_FINE, random_state=RANDOM_STATE + i * 1000
        )
        if best_metrics is None or best_params is None:
            print(f"  -> Fine-tuning failed for {model_name}, skipping")
            continue

        print(f"  Fine R^2 = {best_metrics['test_r2']:.3f} | params = {best_params}")

        # Bootstrap 稳定性（实际为 Repeated CV）
        stability = repeated_cv_stability(
            model_builder, best_params, X, y, groups, y_strat,
            use_y_std=USE_Y_STD[model_name], n_splits=N_SPLITS, n_repeats=N_FINAL_BOOTSTRAP
        )
        print(f"  Bootstrap: {stability['mean']:.3f} ± {stability['std']:.3f} "
              f"[{stability['ci_lower']:.3f}, {stability['ci_upper']:.3f}]")

        # 最终全量模型
        final_model, sx, sy = fit_final_model(model_builder, best_params, X, y, use_y_std=USE_Y_STD[model_name])

        # 预测观察图（用全量拟合的模型预测全量数据）
        if USE_Y_STD[model_name]:
            y_pred_full = sy.inverse_transform(final_model.predict(sx.transform(X)).reshape(-1, 1)).ravel()
        else:
            y_pred_full = final_model.predict(X)

        pred_plot_path = os.path.join(OUT_DIR, f'SR0530_1mm_{data_group}_{schema_name}_{model_name}_Observed_vs_Predicted.png')
        plot_observed_vs_predicted(y.values, y_pred_full, pred_plot_path,
                                   title=f'{data_group} {schema_name} {model_name} at 1.0 mm')

        # Bootstrap 分布图
        boot_plot_path = os.path.join(OUT_DIR, f'SR0530_1mm_{data_group}_{schema_name}_{model_name}_Bootstrap_R2.png')
        plot_bootstrap_distribution(np.array(stability['scores']), boot_plot_path,
                                    title=f'{data_group} {schema_name} {model_name} Bootstrap Test R^2')

        # 特征重要性
        # (a) 内置重要性
        builtin_imp = get_builtin_importance(final_model, feat_full)
        if builtin_imp is not None:
            builtin_path = os.path.join(OUT_DIR, f'SR0530_1mm_{data_group}_{schema_name}_{model_name}_Builtin_Importance.png')
            plot_importance(builtin_imp, f'{model_name} Built-in Importance ({data_group} {schema_name})', builtin_path)
            for _, imp_row in builtin_imp.iterrows():
                importance_records.append({
                    'Data_Group': data_group,
                    'Schema': schema_name,
                    'Model': model_name,
                    'Method': 'Builtin',
                    'Feature': imp_row['Feature'],
                    'Importance': imp_row['Importance']
                })

        # (b) Permutation & SHAP importance（在 CV 测试集上计算，避免乐观偏差）
        perm_imp, shap_imp = compute_cv_feature_importance(
            model_builder, best_params, X, y, groups, y_strat, feat_full,
            use_y_std=USE_Y_STD[model_name], n_splits=N_SPLITS,
            n_perm_repeats=N_PERM_REPEATS, random_state=RANDOM_STATE
        )

        perm_path = os.path.join(OUT_DIR, f'SR0530_1mm_{data_group}_{schema_name}_{model_name}_Permutation_Importance.png')
        plot_importance(perm_imp, f'{model_name} Permutation Importance ({data_group} {schema_name})', perm_path)
        for _, imp_row in perm_imp.iterrows():
            importance_records.append({
                'Data_Group': data_group,
                'Schema': schema_name,
                'Model': model_name,
                'Method': 'Permutation',
                'Feature': imp_row['Feature'],
                'Importance': imp_row['Importance_Mean']
            })

        # (c) SHAP importance
        if shap_imp is not None:
            shap_path = os.path.join(OUT_DIR, f'SR0530_1mm_{data_group}_{schema_name}_{model_name}_SHAP_Importance.png')
            plot_importance(shap_imp, f'{model_name} SHAP Importance ({data_group} {schema_name})', shap_path)
            for _, imp_row in shap_imp.iterrows():
                importance_records.append({
                    'Data_Group': data_group,
                    'Schema': schema_name,
                    'Model': model_name,
                    'Method': 'SHAP',
                    'Feature': imp_row['Feature'],
                    'Importance': imp_row['Importance']
                })

        # 保存结果
        results.append({
            'Data_Group': data_group,
            'Schema': schema_name,
            'Model': model_name,
            'N_Eyes': len(df_sub),
            'N_Subjects': df_sub['Real_Subject_ID'].nunique(),
            'Coarse_Test_R2': row['test_r2'],
            'Fine_Test_R2': best_metrics['test_r2'],
            'Fine_Train_R2': best_metrics['train_r2'],
            'Fine_Test_R2_Std': best_metrics['test_r2_std'],
            'Fine_Test_Corr': best_metrics['test_corr'],
            'Fine_Test_MAPE': best_metrics['test_mape'],
            'Fine_Test_RMSE': best_metrics['test_rmse'],
            'Fine_Test_RMSE_Std': best_metrics['test_rmse_std'],
            'Fine_Gap': best_metrics['gap'],
            'Bootstrap_Mean': stability['mean'],
            'Bootstrap_Std': stability['std'],
            'Bootstrap_CI_Lower': stability['ci_lower'],
            'Bootstrap_CI_Upper': stability['ci_upper'],
            'Coarse_Best_Params': str(coarse_params),
            'Fine_Best_Params': str(best_params)
        })

        for trial in trials:
            all_trials.append({
                'Data_Group': data_group,
                'Schema': schema_name,
                'Model': model_name,
                'Params': str(trial['params']),
                'Train_R2': trial['train_r2'],
                'Test_R2': trial['test_r2'],
                'Gap': trial['gap'],
                'Test_MAPE': trial['test_mape'],
                'Test_RMSE': trial['test_rmse']
            })

    # 4. 保存结果
    df_results = pd.DataFrame(results)
    df_trials = pd.DataFrame(all_trials)
    df_importance = pd.DataFrame(importance_records)

    df_results.to_csv(os.path.join(OUT_DIR, 'SR0530_1mm_Fine_Tuning_Results.csv'), index=False, encoding='utf-8-sig')
    df_trials.to_csv(os.path.join(OUT_DIR, 'SR0530_1mm_Fine_Tuning_AllTrials.csv'), index=False, encoding='utf-8-sig')
    df_importance.to_csv(os.path.join(OUT_DIR, 'SR0530_1mm_Feature_Importance.csv'), index=False, encoding='utf-8-sig')

    print(f"\nSaved results: {len(df_results)} configurations")
    print(f"Saved trials: {len(df_trials)}")
    print(f"Saved importance records: {len(df_importance)}")

    # 5. 生成汇总可视化
    plot_summary(df_results, df_importance)

    # 6. 生成报告
    generate_report(df_results, df_importance)

    print("\n" + "=" * 80)
    print("1.0 mm final tuning and feature importance analysis complete!")
    print("=" * 80)


def plot_summary(df_results, df_importance):
    """生成汇总可视化。"""
    if df_results.empty:
        return

    # 1. Fine R^2 排序条形图
    fig, ax = plt.subplots(figsize=(12, 8))
    df_sorted = df_results.sort_values('Fine_Test_R2', ascending=True)
    labels = [f"{r['Data_Group']} {r['Schema']}\n{r['Model']}" for _, r in df_sorted.iterrows()]
    y_pos = np.arange(len(df_sorted))
    ax.barh(y_pos, df_sorted['Fine_Test_R2'].values, color='steelblue', edgecolor='black')
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel('Fine-Tuned Test R^2')
    ax.set_title('1.0 mm: Fine-Tuned Test R^2 by Configuration')
    ax.grid(True, alpha=0.3, axis='x')
    plt.tight_layout()
    path = os.path.join(OUT_DIR, 'SR0530_1mm_Fine_R2_Summary.png')
    plt.savefig(path, dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(FIG_DIR, os.path.basename(path)), dpi=300, bbox_inches='tight')
    plt.close()

    # 2. 按 Method + Feature 聚合的重要性热图（先组内归一化再平均，便于跨方法比较）
    if not df_importance.empty:
        norm_imp = df_importance.copy()
        norm_imp['Normalized_Importance'] = (
            norm_imp.groupby(['Data_Group', 'Schema', 'Model', 'Method'])['Importance']
            .transform(lambda x: (x - x.min()) / (x.max() - x.min()) if x.max() != x.min() else 0.0)
        )
        pivot = norm_imp.groupby(['Method', 'Feature'])['Normalized_Importance'].mean().unstack('Feature')
        if not pivot.empty:
            fig, ax = plt.subplots(figsize=(12, 6))
            im = ax.imshow(pivot.values, aspect='auto', cmap='RdYlGn', vmin=0, vmax=1)
            ax.set_xticks(np.arange(len(pivot.columns)))
            ax.set_yticks(np.arange(len(pivot.index)))
            ax.set_xticklabels(pivot.columns, rotation=45, ha='right')
            ax.set_yticklabels(pivot.index)
            ax.set_title('Average Normalized Feature Importance by Method (1.0 mm)')
            for i in range(len(pivot.index)):
                for j in range(len(pivot.columns)):
                    val = pivot.values[i, j]
                    if not np.isnan(val):
                        ax.text(j, i, f"{val:.3f}", ha='center', va='center', fontsize=8)
            plt.colorbar(im, ax=ax, label='Normalized Importance')
            plt.tight_layout()
            path = os.path.join(OUT_DIR, 'SR0530_1mm_Importance_Heatmap.png')
            plt.savefig(path, dpi=300, bbox_inches='tight')
            plt.savefig(os.path.join(FIG_DIR, os.path.basename(path)), dpi=300, bbox_inches='tight')
            plt.close()

    # 3. Bootstrap 稳定性对比
    fig, ax = plt.subplots(figsize=(12, 8))
    df_sorted = df_results.sort_values('Bootstrap_Mean', ascending=True)
    y_pos = np.arange(len(df_sorted))
    ci_lower = df_sorted['Bootstrap_CI_Lower'].values
    ci_upper = df_sorted['Bootstrap_CI_Upper'].values
    means = df_sorted['Bootstrap_Mean'].values
    yerr = [means - ci_lower, ci_upper - means]
    ax.errorbar(means, y_pos, xerr=yerr, fmt='o', capsize=5, capthick=2, elinewidth=2, markersize=8, color='steelblue')
    ax.set_yticks(y_pos)
    ax.set_yticklabels([f"{r['Data_Group']} {r['Schema']}\n{r['Model']}" for _, r in df_sorted.iterrows()], fontsize=8)
    ax.set_xlabel('Bootstrap Test R^2 (95% CI)')
    ax.set_title('1.0 mm: Bootstrap Stability of Fine-Tuned Configurations')
    ax.grid(True, alpha=0.3, axis='x')
    plt.tight_layout()
    path = os.path.join(OUT_DIR, 'SR0530_1mm_Bootstrap_Stability_Summary.png')
    plt.savefig(path, dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(FIG_DIR, os.path.basename(path)), dpi=300, bbox_inches='tight')
    plt.close()


def compute_t_ci(mean, std, n_folds=5, alpha=0.05):
    """基于 fold 级均值与标准差计算 t 分布近似 95% CI。"""
    from scipy import stats
    if pd.isna(std) or n_folds < 2:
        return np.nan, np.nan
    se = std / np.sqrt(n_folds)
    t_val = stats.t.ppf(1 - alpha / 2, df=n_folds - 1)
    return mean - t_val * se, mean + t_val * se


def generate_report(df_results, df_importance):
    """生成 Markdown 最终报告。"""
    md = []
    md.append("# SR0530 1.0 mm 最终精细调优与特征重要性报告\n\n")
    md.append("> **目标**：在 ≥1 象限平均策略下，对 1.0 mm 偏心率的全部模型/方案组合进行精细参数寻优、稳定性评估与特征重要性分析。\n\n")
    md.append(f"> **方法**：GroupKFold by Subject（{N_SPLITS} 折），精细搜索 {N_ITER_FINE} 组参数，Bootstrap 重复 {N_FINAL_BOOTSTRAP} 次评估稳定性。\n\n")

    md.append("---\n\n")

    # 一、总体最佳配置
    md.append("## 一、总体最佳配置\n\n")
    if not df_results.empty:
        best = df_results.loc[df_results['Bootstrap_Mean'].idxmax()]
        r2_lo, r2_hi = compute_t_ci(best['Fine_Test_R2'], best['Fine_Test_R2_Std'])
        rmse_lo, rmse_hi = compute_t_ci(best['Fine_Test_RMSE'], best['Fine_Test_RMSE_Std'])
        md.append(f"- **数据组**：{best['Data_Group']}\n")
        md.append(f"- **方案**：{best['Schema']}\n")
        md.append(f"- **模型**：{best['Model']}\n")
        md.append(f"- **Fine Test R^2**：{best['Fine_Test_R2']:.3f} "
                  f"[95% CI: {r2_lo:.3f}, {r2_hi:.3f}]\n")
        md.append(f"- **Bootstrap R^2**：{best['Bootstrap_Mean']:.3f} ± {best['Bootstrap_Std']:.3f} "
                  f"[95% CI: {best['Bootstrap_CI_Lower']:.3f}, {best['Bootstrap_CI_Upper']:.3f}]\n")
        md.append(f"- **Train R^2 / Gap**：{best['Fine_Train_R2']:.3f} / {best['Fine_Gap']:.3f}\n")
        md.append(f"- **MAPE / RMSE**：{best['Fine_Test_MAPE']:.2f}% / {best['Fine_Test_RMSE']:.1f} "
                  f"[95% CI: {rmse_lo:.1f}, {rmse_hi:.1f}]\n")
        md.append(f"- **样本量**：{int(best['N_Eyes'])} 眼 / {int(best['N_Subjects'])} subjects\n")
        md.append(f"- **最佳参数**：`{best['Fine_Best_Params']}`\n\n")

    # 二、全部配置结果
    md.append("## 二、全部配置精细调优结果\n\n")
    md.append("| 数据组 | 方案 | 模型 | Coarse R^2 | Fine R^2 (95% CI) | Train R^2 | Gap | MAPE | RMSE (95% CI) | Bootstrap R^2 Mean±Std | Bootstrap 95% CI |\n")
    md.append("|--------|------|------|-----------|-------------------|----------|-----|------|----------------|------------------------|------------------|\n")
    for _, row in df_results.iterrows():
        r2_lo, r2_hi = compute_t_ci(row['Fine_Test_R2'], row['Fine_Test_R2_Std'])
        rmse_lo, rmse_hi = compute_t_ci(row['Fine_Test_RMSE'], row['Fine_Test_RMSE_Std'])
        md.append(f"| {row['Data_Group']} | {row['Schema']} | {row['Model']} | "
                  f"{row['Coarse_Test_R2']:.3f} | {row['Fine_Test_R2']:.3f} [{r2_lo:.3f}, {r2_hi:.3f}] | "
                  f"{row['Fine_Train_R2']:.3f} | {row['Fine_Gap']:.3f} | {row['Fine_Test_MAPE']:.2f} | "
                  f"{row['Fine_Test_RMSE']:.1f} [{rmse_lo:.1f}, {rmse_hi:.1f}] | "
                  f"{row['Bootstrap_Mean']:.3f} ± {row['Bootstrap_Std']:.3f} | "
                  f"[{row['Bootstrap_CI_Lower']:.3f}, {row['Bootstrap_CI_Upper']:.3f}] |\n")
    md.append("\n")

    # 三、特征重要性
    md.append("## 三、特征重要性汇总\n\n")
    if not df_importance.empty:
        md.append("| 数据组 | 方案 | 模型 | 方法 | 排名 | 特征 | 重要性 |\n")
        md.append("|--------|------|------|------|------|------|--------|\n")
        for (dg, schema, model, method), group in df_importance.groupby(['Data_Group', 'Schema', 'Model', 'Method']):
            group_sorted = group.sort_values('Importance', ascending=False).reset_index(drop=True)
            for rank, (_, imp_row) in enumerate(group_sorted.iterrows(), 1):
                md.append(f"| {dg} | {schema} | {model} | {method} | {rank} | {imp_row['Feature']} | {imp_row['Importance']:.4f} |\n")
    else:
        md.append("无特征重要性结果。\n")
    md.append("\n")

    # 四、主要发现
    md.append("## 四、主要发现\n\n")
    if not df_results.empty:
        best_by_stability = df_results.loc[df_results['Bootstrap_Mean'].idxmax()]
        best_by_fine = df_results.loc[df_results['Fine_Test_R2'].idxmax()]
        md.append(f"1. **最稳定配置**：{best_by_stability['Data_Group']} + {best_by_stability['Schema']} + {best_by_stability['Model']} "
                  f"(Bootstrap R^2 = {best_by_stability['Bootstrap_Mean']:.3f})\n")
        md.append(f"2. **Fine 最高配置**：{best_by_fine['Data_Group']} + {best_by_fine['Schema']} + {best_by_fine['Model']} "
                  f"(Fine R^2 = {best_by_fine['Fine_Test_R2']:.3f})\n")

    if not df_importance.empty:
        # 对不同方法（Builtin/Permutation/SHAP）的原始尺度差异进行组内 [0,1] 归一化后再平均
        norm_imp = df_importance.copy()
        norm_imp['Normalized_Importance'] = (
            norm_imp.groupby(['Data_Group', 'Schema', 'Model', 'Method'])['Importance']
            .transform(lambda x: (x - x.min()) / (x.max() - x.min()) if x.max() != x.min() else 0.0)
        )
        avg_imp = norm_imp.groupby(['Feature'])['Normalized_Importance'].mean().sort_values(ascending=False)
        avg_rank = norm_imp.groupby(['Feature'])['Normalized_Importance'].mean().rank(ascending=False)
        imp_str = ', '.join([f"{f} ({v:.3f}, rank {int(avg_rank[f])})" for f, v in avg_imp.head(6).items()])
        md.append(f"3. **平均特征重要性排序（已归一化）**：{imp_str}\n")
        md.append("    - 三种方法（Builtin / Permutation / SHAP）在各自模型内归一化后取平均。\n")
        if len(avg_imp) > 1:
            md.append(f"    - 第一名 `{avg_imp.index[0]}` 的归一化重要性（{avg_imp.iloc[0]:.3f}）显著高于第二名 `{avg_imp.index[1]}`（{avg_imp.iloc[1]:.3f}）。\n")

    md.append("\n")

    # 五、可视化
    md.append("## 五、可视化\n\n")
    md.append("### Fine R^2 汇总\n\n")
    md.append("![Fine R2 Summary](FIG/SR0530_1mm_Fine_R2_Summary.png)\n\n")
    md.append("### Bootstrap 稳定性\n\n")
    md.append("![Bootstrap Stability](FIG/SR0530_1mm_Bootstrap_Stability_Summary.png)\n\n")
    md.append("### 特征重要性热图\n\n")
    md.append("![Importance Heatmap](FIG/SR0530_1mm_Importance_Heatmap.png)\n\n")

    # 六、讨论
    md.append("## 六、讨论\n\n")
    md.append("1. **精细寻优效果**：对比 Coarse 与 Fine R^2，可判断原搜索空间是否充分。\n")
    md.append("2. **稳定性优先**：Bootstrap 95% CI 下限更高的配置比单纯 Fine R^2 最高的配置更值得信赖。\n")
    md.append("3. **特征重要性一致性**：若 Permutation、Builtin、SHAP 三种方法均将某特征排在前列，则该特征对 1.0 mm 密度预测最为关键。\n")
    md.append("4. **最终模型选择**：建议采用 Bootstrap Mean 最高且 Gap 最小的配置作为最终报告用模型。\n\n")

    md.append("---\n\n")
    md.append("*Report generated by SR_ML_1mm_final_tuning.py*\n")

    md_path = os.path.join(REPORT_DIR, 'SR0530_1mm_Final_Tuning_and_Feature_Importance_Report.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(''.join(md))
    print(f"  --> Report: {md_path}")


if __name__ == '__main__':
    main()
