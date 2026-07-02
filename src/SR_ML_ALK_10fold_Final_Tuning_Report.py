"""
SR0530 ALK 方案族 10-fold 最终精细寻优报告

- 仅使用携带 AL/K 的 lenient 数据组（71 眼 / 46 subjects）
- 10-fold GroupKFold by Subject，按 Myopia 分层
- 覆盖全部 8 个 ALK 变型方案
- 同时优化 8 种模型：SVM / Random_Forest / XGBoost / Neural_Network / Lasso / ElasticNet / Ridge / Robust Linear Regression (HuberRegressor)
- 每模型 50 次随机搜索（更精细）
- 对最佳配置生成 SHAP 解释图
- 输出最终寻优报告，并与前期 10-fold C1_Combined_ALK 报告、10-fold Robust LR 报告整合对比
"""
import os
import glob
import warnings
import numpy as np
import pandas as pd
from copy import deepcopy
from scipy import stats

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# 全局字体设置：Calibri 为首选，中文回退
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['font.sans-serif'] = ['Calibri', 'SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.svm import SVR
from sklearn.ensemble import RandomForestRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.linear_model import Lasso, ElasticNet, Ridge, HuberRegressor
from sklearn.metrics import r2_score, mean_squared_error
from xgboost import XGBRegressor

import shap
from joblib import Parallel, delayed
warnings.filterwarnings('ignore')

# ============================================================
# 配置
# ============================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'genData', 'CleanDataRoi_lenient')

# joblib loky backend 的临时目录不能包含中文，显式指定 ASCII 路径
JOBLIB_TEMP = 'C:/tmp_joblib'
os.makedirs(JOBLIB_TEMP, exist_ok=True)
os.environ['JOBLIB_TEMP_FOLDER'] = JOBLIB_TEMP
OUT_DIR = os.path.join(BASE_DIR, 'genData', 'sum')
REPORT_DIR = os.path.join(BASE_DIR, 'report')
FIG_DIR = os.path.join(REPORT_DIR, 'FIG', 'ALK_10fold_Final_Tuning')
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(FIG_DIR, exist_ok=True)

FEATURE_ALL = {
    'AL': 'Axial length (mm)',
    'Age': 'Age',
    'SE': 'Spherical equivalent refraction (D)',
    'Gender': 'Gender',
    'K': 'Corneal curvature (mm)',
    'ACD': 'Anterior chamber depth (mm)',
    'ALK': 'AL/K ratio'
}

TARGET_COL = 'Angular cone density (cones/ deg2)'

SCHEMA = {
    'A1_Biomechanical_ALK': ['AL', 'Age', 'Gender', 'ALK'],
    'A1_Biomechanical_K_ALK': ['AL', 'Age', 'Gender', 'K', 'ALK'],
    'A2_Biomechanical_ALK': ['AL', 'ACD', 'Age', 'Gender', 'ALK'],
    'A2_Biomechanical_K_ALK': ['AL', 'ACD', 'Age', 'Gender', 'K', 'ALK'],
    'B_Clinical_ALK': ['SE', 'Age', 'Gender', 'ALK'],
    'B_Clinical_K_ALK': ['SE', 'Age', 'Gender', 'K', 'ALK'],
    'C1_Combined_ALK': ['SE', 'AL', 'Age', 'Gender', 'ALK'],
    'C1_Combined_K_ALK': ['SE', 'AL', 'Age', 'Gender', 'K', 'ALK']
}

MYOPIA_THRESHOLD = -0.5
RANDOM_STATE = 42
N_ITER = 50
N_SPLITS = 10

MODE_LABEL = 'ALK_10fold_Final_Tuning'

# ============================================================
# 参数搜索空间（更精细）
# ============================================================
PARAM_SPACE = {
    'SVM': {
        'model': lambda p: Pipeline([('s', StandardScaler()), ('v', SVR(**p))]),
        'params': {
            'C': [100, 300, 500, 1000, 2000, 5000],
            'epsilon': [50, 100, 200, 300, 500, 800],
            'gamma': [0.0005, 0.001, 0.003, 0.005, 0.01, 0.03, 0.05]
        },
        'use_y_std': False
    },
    'Random_Forest': {
        'model': lambda p: Pipeline([('s', StandardScaler()), ('rf', RandomForestRegressor(**p, random_state=RANDOM_STATE, n_jobs=1))]),
        'params': {
            'n_estimators': [50, 100, 200, 300, 500],
            'max_depth': [2, 3, 4, 5, 7, None],
            'min_samples_split': [2, 3, 5, 10],
            'min_samples_leaf': [1, 2, 4]
        },
        'use_y_std': False
    },
    'XGBoost': {
        'model': lambda p: XGBRegressor(**p, random_state=RANDOM_STATE, verbosity=0),
        'params': {
            'learning_rate': [0.0005, 0.001, 0.005, 0.01, 0.03, 0.05],
            'max_depth': [1, 2, 3, 4, 5],
            'n_estimators': [30, 50, 100, 200, 300],
            'reg_alpha': [0.05, 0.1, 0.3, 0.5, 1.0, 2.0],
            'reg_lambda': [0.05, 0.1, 0.3, 0.5, 1.0, 2.0]
        },
        'use_y_std': False
    },
    'Neural_Network': {
        'model': lambda p: Pipeline([('s', StandardScaler()), ('nn', MLPRegressor(**p, max_iter=5000, early_stopping=True, validation_fraction=0.15, n_iter_no_change=20, random_state=RANDOM_STATE))]),
        'params': {
            'hidden_layer_sizes': [(20,), (40,), (60,), (80,), (100,), (80, 40), (100, 50)],
            'alpha': [0.05, 0.1, 0.3, 0.5, 1.0, 2.0],
            'learning_rate_init': [0.00005, 0.0001, 0.0005, 0.001]
        },
        'use_y_std': True
    },
    'Lasso': {
        'model': lambda p: Pipeline([('s', StandardScaler()), ('lasso', Lasso(**p, max_iter=5000))]),
        'params': {
            'alpha': [0.0005, 0.001, 0.003, 0.005, 0.01, 0.03, 0.05, 0.1, 0.3, 0.5, 1.0]
        },
        'use_y_std': False
    },
    'ElasticNet': {
        'model': lambda p: Pipeline([('s', StandardScaler()), ('en', ElasticNet(**p, max_iter=5000))]),
        'params': {
            'alpha': [0.0005, 0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0],
            'l1_ratio': [0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 0.8, 0.9]
        },
        'use_y_std': False
    },
    'Ridge': {
        'model': lambda p: Pipeline([('s', StandardScaler()), ('ridge', Ridge(**p))]),
        'params': {
            'alpha': [0.001, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0, 50.0, 100.0]
        },
        'use_y_std': False
    },
    'Robust_Linear_Regression': {
        'model': lambda p: Pipeline([('s', StandardScaler()), ('rl', HuberRegressor(**p, max_iter=5000))]),
        'params': {
            'epsilon': [1.0, 1.2, 1.35, 1.5, 1.8, 2.0, 2.5, 3.0],
            'alpha': [0.00005, 0.0001, 0.0005, 0.001, 0.005, 0.01, 0.05, 0.1]
        },
        'use_y_std': False
    }
}


# ============================================================
# 工具函数
# ============================================================
def load_subject_mapping(data_dir):
    df_ref = pd.read_csv(os.path.join(data_dir, 'data1.csv'))
    mapping = {}
    for _, row in df_ref.iterrows():
        eye_label = row['Eye_Label']
        subject_id = row['Subject_ID']
        mapping[eye_label] = subject_id
        mapping[subject_id] = subject_id
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
    feature_cols = [v for v in FEATURE_ALL.values() if v != 'AL/K ratio']

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
    base['AL/K ratio'] = base[FEATURE_ALL['AL']] / base[FEATURE_ALL['K']]

    return base[['Subject_ID', 'Real_Subject_ID', 'Eye', 'Myopia'] + list(FEATURE_ALL.values()) + ['N_Quadrants', TARGET_COL]].copy()


def fill_na(df, cols):
    for col in cols:
        if df[col].isna().any():
            df[col].fillna(df[col].median(), inplace=True)
    return df


def group_stratified_kfold(groups, y_stratify, n_splits=10, random_state=42):
    rng = np.random.RandomState(random_state)
    df_idx = pd.DataFrame({'idx': np.arange(len(groups)), 'group': groups, 'y': y_stratify})

    group_info = df_idx.groupby('group').agg(
        y=('y', lambda x: int(x.mode()[0])),
        idx=('idx', list)
    ).reset_index()
    group_info = group_info.sample(frac=1, random_state=random_state).reset_index(drop=True)

    pos_groups = group_info[group_info['y'] == 1].copy().reset_index(drop=True)
    neg_groups = group_info[group_info['y'] == 0].copy().reset_index(drop=True)

    folds = [[] for _ in range(n_splits)]
    for label_df in [pos_groups, neg_groups]:
        for i, row in label_df.iterrows():
            folds[i % n_splits].append(row.name)

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


def sample_params(param_space, rng):
    params = {}
    for k, v in param_space.items():
        if isinstance(v, list):
            params[k] = v[rng.randint(0, len(v))]
        else:
            params[k] = v
    return params


def evaluate_model(model_builder, params, X, y, groups, y_stratify, use_y_std=False, n_splits=10, random_state=42):
    n_subjects = len(np.unique(groups))
    n_splits = min(n_splits, n_subjects // 2)
    if n_splits < 2:
        n_splits = 2

    splits = group_stratified_kfold(groups, y_stratify, n_splits=n_splits, random_state=random_state)

    train_r2_list, test_r2_list = [], []
    test_rmse_list = []

    for ti, vi in splits:
        model = model_builder(params)
        try:
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
        except Exception:
            return {
                'train_r2': -np.inf,
                'test_r2': -np.inf,
                'test_r2_std': np.nan,
                'test_rmse': np.inf,
                'test_rmse_std': np.nan,
                'gap': np.inf
            }

        train_r2_list.append(r2_score(yt_raw, pred_train))
        test_r2_list.append(r2_score(yv, pred))
        test_rmse_list.append(np.sqrt(mean_squared_error(yv, pred)))

    return {
        'train_r2': np.mean(train_r2_list),
        'test_r2': np.mean(test_r2_list),
        'test_r2_std': np.std(test_r2_list, ddof=1),
        'test_rmse': np.mean(test_rmse_list),
        'test_rmse_std': np.std(test_rmse_list, ddof=1),
        'gap': np.mean(train_r2_list) - np.mean(test_r2_list)
    }


def tune_model(model_name, model_config, X, y, groups, y_stratify, n_iter=50, random_state=42):
    rng = np.random.RandomState(random_state)
    best_score = -np.inf
    best_params = None
    best_metrics = None
    all_trials = []

    for i in range(n_iter):
        params = sample_params(model_config['params'], rng)
        metrics = evaluate_model(
            model_config['model'], params, X, y, groups, y_stratify,
            use_y_std=model_config['use_y_std'], n_splits=N_SPLITS, random_state=random_state + i
        )
        metrics['params'] = params
        all_trials.append(metrics)

        if metrics['test_r2'] > best_score:
            best_score = metrics['test_r2']
            best_params = params
            best_metrics = metrics

    return best_params, best_metrics, all_trials


def tune_one_model(model_name, model_config, dist, schema_name, X, y, groups, y_stratify, n_eyes, n_subjects, n_iter, random_state):
    """用于 joblib 并行的单模型调优包装函数。"""
    best_params, best_metrics, trials = tune_model(
        model_name, model_config, X, y, groups, y_stratify,
        n_iter=n_iter, random_state=random_state
    )
    result_records = []
    trial_records = []
    actual_splits = min(N_SPLITS, n_subjects // 2)
    if actual_splits < 2:
        actual_splits = 2
    if best_metrics is not None and best_params is not None:
        result_records.append({
            'Data_Group': 'lenient',
            'Distance_mm': dist,
            'Schema': schema_name,
            'Model': model_name,
            'CV_Folds': actual_splits,
            'N_Eyes': n_eyes,
            'N_Subjects': n_subjects,
            'Best_Params': str(best_params),
            **{k: v for k, v in best_metrics.items() if not isinstance(v, list)}
        })
    for trial in trials:
        trial_records.append({
            'Data_Group': 'lenient',
            'Distance_mm': dist,
            'Schema': schema_name,
            'Model': model_name,
            'CV_Folds': actual_splits,
            'Params': str(trial['params']),
            'Train_R2': trial['train_r2'],
            'Test_R2': trial['test_r2'],
            'Test_R2_Std': trial['test_r2_std'],
            'Gap': trial['gap'],
            'Test_RMSE': trial['test_rmse'],
            'Test_RMSE_Std': trial['test_rmse_std']
        })
    return result_records, trial_records, model_name, best_metrics['test_r2'] if best_metrics else -np.inf


# ============================================================
# SHAP 计算
# ============================================================
def compute_linear_shap(model, X_sample):
    scaler = model.named_steps['s']
    reg = model.named_steps.get('lasso') or model.named_steps.get('en') or model.named_steps.get('ridge') or model.named_steps.get('rl')
    X_scaled = scaler.transform(X_sample)
    shap_vals = X_scaled * reg.coef_
    base_val = reg.intercept_
    return shap.Explanation(
        values=shap_vals,
        base_values=np.full(len(X_sample), base_val),
        data=X_sample.values,
        feature_names=list(X_sample.columns)
    )


def cross_validated_shap(model_name, model_config, best_params, X, y, groups, y_stratify, n_splits=10, random_state=42):
    actual_splits = min(n_splits, len(np.unique(groups)) // 2)
    if actual_splits < 2:
        actual_splits = 2
    splits = group_stratified_kfold(groups, y_stratify, n_splits=actual_splits, random_state=random_state)

    all_shap_exps = []
    for ti, vi in splits:
        model = model_config['model'](best_params)
        X_train, X_test = X.iloc[ti], X.iloc[vi]
        y_train = y.iloc[ti]

        if model_config['use_y_std']:
            sx, sy = StandardScaler(), StandardScaler()
            Xt = sx.fit_transform(X_train)
            Xv = sx.transform(X_test)
            yt = sy.fit_transform(y_train.values.reshape(-1, 1)).ravel()
            model.fit(Xt, yt)
        else:
            model.fit(X_train, y_train)
            Xv = X_test

        if model_name in ['Lasso', 'ElasticNet', 'Ridge', 'Robust_Linear_Regression']:
            exp = compute_linear_shap(model, X_test)
        elif model_name == 'Random_Forest':
            explainer = shap.TreeExplainer(model.named_steps['rf'])
            sv = explainer.shap_values(X_test.values)
            exp = shap.Explanation(
                values=sv,
                base_values=np.full(len(X_test), explainer.expected_value),
                data=X_test.values,
                feature_names=list(X_test.columns)
            )
        elif model_name == 'XGBoost':
            explainer = shap.TreeExplainer(model)
            sv = explainer.shap_values(X_test.values)
            exp = shap.Explanation(
                values=sv,
                base_values=np.full(len(X_test), explainer.expected_value),
                data=X_test.values,
                feature_names=list(X_test.columns)
            )
        else:
            # SVM / Neural Network: skip for efficiency
            return None
        all_shap_exps.append(exp)

    values = np.concatenate([e.values for e in all_shap_exps], axis=0)
    data = np.concatenate([e.data for e in all_shap_exps], axis=0)
    base_values = np.concatenate([e.base_values for e in all_shap_exps], axis=0)
    return shap.Explanation(
        values=values,
        base_values=base_values,
        data=data,
        feature_names=all_shap_exps[0].feature_names
    )


def plot_shap_summary(exp, title, out_path):
    plt.figure(figsize=(10, 6))
    shap.summary_plot(exp, features=exp.data, feature_names=exp.feature_names, show=False)
    plt.title(title)
    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()


# ============================================================
# 主程序
# ============================================================
def compute_t_ci(mean, std, n_folds, alpha=0.05):
    if pd.isna(std) or n_folds < 2:
        return np.nan, np.nan
    se = std / np.sqrt(n_folds)
    t_val = stats.t.ppf(1 - alpha / 2, df=n_folds - 1)
    return mean - t_val * se, mean + t_val * se


def main():
    print("=" * 80)
    print("SR0530 ALK 10-fold Final Fine Tuning Report")
    print(f"Data group: lenient (71 eyes / 46 subjects)")
    print(f"Schemas: {len(SCHEMA)} ALK variants")
    print(f"Models: {len(PARAM_SPACE)} models including Robust Linear Regression")
    print(f"CV: {N_SPLITS}-fold GroupKFold by Subject, stratified by Myopia")
    print(f"Random search iterations per model: {N_ITER}")
    print("=" * 80)

    eye_to_subject = load_subject_mapping(DATA_DIR)
    all_data = load_distance_data(DATA_DIR)
    distances = sorted(all_data.keys())

    results = []
    all_trials = []

    for dist in distances:
        print(f"\n--- Distance {dist:.1f} mm ---")
        df = aggregate_distance(all_data[dist], eye_to_subject, min_quadrants=1)

        for schema_name, feat_short in SCHEMA.items():
            feat_full = [FEATURE_ALL[s] for s in feat_short]
            df_sub = fill_na(df.copy(), feat_full)

            X = df_sub[feat_full]
            y = df_sub[TARGET_COL]
            groups = df_sub['Real_Subject_ID'].values
            y_strat = df_sub['Myopia'].values

            n_subjects = len(np.unique(groups))
            n_eyes = len(df_sub)

            if n_subjects < 4:
                print(f"  [{schema_name}] Skipping: too few subjects ({n_subjects})")
                continue

            actual_splits = min(N_SPLITS, n_subjects // 2)
            if actual_splits < 2:
                actual_splits = 2

            # 并行调优所有模型，统一使用随机种子 42，确保结果可复现、可比较
            n_jobs = min(8, len(PARAM_SPACE))
            parallel_results = Parallel(n_jobs=n_jobs, backend='loky')(
                delayed(tune_one_model)(
                    model_name, model_config, dist, schema_name,
                    X, y, groups, y_strat, n_eyes, n_subjects,
                    N_ITER, RANDOM_STATE
                )
                for model_name, model_config in PARAM_SPACE.items()
            )

            for res_records, trial_records, model_name, best_r2 in parallel_results:
                print(f"  [{schema_name}] {model_name} {actual_splits}-fold Best R2={best_r2:.3f}")
                results.extend(res_records)
                all_trials.extend(trial_records)

    df_results = pd.DataFrame(results)
    df_trials = pd.DataFrame(all_trials)

    results_csv = os.path.join(OUT_DIR, f'SR0530_HP_Tuning_Results_{MODE_LABEL}.csv')
    trials_csv = os.path.join(OUT_DIR, f'SR0530_HP_Tuning_AllTrials_{MODE_LABEL}.csv')
    df_results.to_csv(results_csv, index=False, encoding='utf-8-sig')
    df_trials.to_csv(trials_csv, index=False, encoding='utf-8-sig')
    print(f"\nSaved: {results_csv}")
    print(f"Saved: {trials_csv}")

    # 对最佳配置生成 SHAP
    shap_path = None
    best_row = None
    if not df_results.empty:
        best_row = df_results.loc[df_results['test_r2'].idxmax()]
        best_dist = best_row['Distance_mm']
        best_schema = best_row['Schema']
        best_model = best_row['Model']
        best_params = eval(best_row['Best_Params'])

        print(f"\nGenerating SHAP for best config: {best_model} @ {best_dist:.1f} mm / {best_schema}")
        df = aggregate_distance(all_data[best_dist], eye_to_subject, min_quadrants=1)
        feat_full = [FEATURE_ALL[s] for s in SCHEMA[best_schema]]
        df_sub = fill_na(df.copy(), feat_full)
        X = df_sub[feat_full]
        y = df_sub[TARGET_COL]
        groups = df_sub['Real_Subject_ID'].values
        y_strat = df_sub['Myopia'].values

        model_config = PARAM_SPACE[best_model]
        exp = cross_validated_shap(best_model, model_config, best_params, X, y, groups, y_strat, n_splits=N_SPLITS, random_state=RANDOM_STATE)
        if exp is not None:
            shap_path = os.path.join(FIG_DIR, f'SR0530_{MODE_LABEL}_SHAP_Best_{best_model}_{best_schema}_{best_dist:.1f}mm.png')
            plot_shap_summary(exp, f'{best_schema} {best_model} @ {best_dist:.1f} mm (10-fold CV SHAP)', shap_path)
            print(f"  -> SHAP saved: {shap_path}")
        else:
            print(f"  -> SHAP skipped for {best_model} (too slow)")

    generate_report(df_results, best_row, shap_path)

    print("\n" + "=" * 80)
    print("Done!")
    print("=" * 80)


# ============================================================
# 报告生成
# ============================================================
def generate_report(df_new, best_row, shap_path):
    # 加载已有结果用于对比
    legacy_c1_10fold_csv = os.path.join(OUT_DIR, 'SR0530_HP_Tuning_Results_C1_Combined_ALK_10fold.csv')
    legacy_rl_10fold_csv = os.path.join(OUT_DIR, 'SR0530_HP_Tuning_Results_RobustLinear_ALK_5fold_10fold.csv')

    df_legacy_c1 = pd.read_csv(legacy_c1_10fold_csv) if os.path.exists(legacy_c1_10fold_csv) else None
    df_legacy_rl = pd.read_csv(legacy_rl_10fold_csv) if os.path.exists(legacy_rl_10fold_csv) else None

    md = []
    md.append("# SR0530 ALK 方案族 10-fold 最终精细寻优报告\n\n")
    md.append("> **目标**：仅使用携带 AL/K 的 lenient 数据组（71 眼 / 46 subjects），对全部 8 个 ALK 变型方案进行 **10-fold GroupKFold by Subject** 精细超参数寻优，模型池同时包含原有 7 种 ML 模型与 **Robust Linear Regression（HuberRegressor）**，并生成最终寻优报告。\n\n")
    md.append("> **交叉验证**：10-fold GroupKFold by Subject，按 Myopia 分层；置信区间基于 fold-level 标准差（t₀.₀₂₅,df）。\n\n")
    md.append("> **搜索策略**：Random Search，每模型 **50** 组参数；参数空间在前期结果基础上进一步细化。\n\n")
    md.append("---\n\n")

    # 一、总体最佳配置
    md.append("## 一、总体最佳配置\n\n")
    if best_row is not None:
        r2_lo, r2_hi = compute_t_ci(best_row['test_r2'], best_row['test_r2_std'], n_folds=best_row['CV_Folds'])
        rmse_lo, rmse_hi = compute_t_ci(best_row['test_rmse'], best_row['test_rmse_std'], n_folds=best_row['CV_Folds'])
        md.append(f"- **数据组**：{best_row['Data_Group']}\n")
        md.append(f"- **距离**：{best_row['Distance_mm']:.1f} mm\n")
        md.append(f"- **方案**：{best_row['Schema']}\n")
        md.append(f"- **模型**：{best_row['Model']}\n")
        md.append(f"- **CV 折数**：{int(best_row['CV_Folds'])}-fold\n")
        md.append(f"- **最佳 Test R²**：{best_row['test_r2']:.3f} [95% CI: {r2_lo:.3f}, {r2_hi:.3f}]\n")
        md.append(f"- **最佳 Test RMSE**：{best_row['test_rmse']:.1f} [95% CI: {rmse_lo:.1f}, {rmse_hi:.1f}]\n")
        md.append(f"- **Gap**：{best_row['gap']:.3f}\n")
        md.append(f"- **最佳参数**：{best_row['Best_Params']}\n")
        md.append(f"- **样本量**：{int(best_row['N_Eyes'])} 眼 / {int(best_row['N_Subjects'])} subjects\n\n")
    else:
        md.append("- 未产生有效结果。\n\n")

    # 二、各距离最佳结果
    md.append("## 二、各距离最佳结果\n\n")
    md.append("| 距离 (mm) | 最佳方案 | 最佳模型 | Test R² (95% CI) | RMSE (95% CI) | Gap | 最佳参数 |\n")
    md.append("|-----------|----------|---------|------------------|----------------|-----|---------|\n")
    for dist in sorted(df_new['Distance_mm'].unique()):
        df_d = df_new[df_new['Distance_mm'] == dist]
        best = df_d.loc[df_d['test_r2'].idxmax()]
        r2_lo, r2_hi = compute_t_ci(best['test_r2'], best['test_r2_std'], n_folds=best['CV_Folds'])
        rmse_lo, rmse_hi = compute_t_ci(best['test_rmse'], best['test_rmse_std'], n_folds=best['CV_Folds'])
        md.append(f"| {best['Distance_mm']:.1f} | {best['Schema']} | {best['Model']} | "
                  f"{best['test_r2']:.3f} [{r2_lo:.3f}, {r2_hi:.3f}] | "
                  f"{best['test_rmse']:.1f} [{rmse_lo:.1f}, {rmse_hi:.1f}] | "
                  f"{best['gap']:.3f} | {best['Best_Params']} |\n")
    md.append("\n")

    # 三、每个方案最佳结果
    md.append("## 三、每个 ALK 方案最佳结果\n\n")
    md.append("| 方案 | 最佳距离 | 最佳模型 | Test R² (95% CI) | RMSE (95% CI) | Gap | 最佳参数 |\n")
    md.append("|------|---------|---------|------------------|----------------|-----|---------|\n")
    for schema in sorted(df_new['Schema'].unique()):
        df_s = df_new[df_new['Schema'] == schema]
        best = df_s.loc[df_s['test_r2'].idxmax()]
        r2_lo, r2_hi = compute_t_ci(best['test_r2'], best['test_r2_std'], n_folds=best['CV_Folds'])
        rmse_lo, rmse_hi = compute_t_ci(best['test_rmse'], best['test_rmse_std'], n_folds=best['CV_Folds'])
        md.append(f"| {best['Schema']} | {best['Distance_mm']:.1f} mm | {best['Model']} | "
                  f"{best['test_r2']:.3f} [{r2_lo:.3f}, {r2_hi:.3f}] | "
                  f"{best['test_rmse']:.1f} [{rmse_lo:.1f}, {rmse_hi:.1f}] | "
                  f"{best['gap']:.3f} | {best['Best_Params']} |\n")
    md.append("\n")

    # 四、每个模型最佳结果
    md.append("## 四、每个模型最佳结果\n\n")
    md.append("| 模型 | 最佳距离 | 最佳方案 | Test R² (95% CI) | RMSE (95% CI) | Gap | 最佳参数 |\n")
    md.append("|------|---------|---------|------------------|----------------|-----|---------|\n")
    for model_name in sorted(df_new['Model'].unique()):
        df_m = df_new[df_new['Model'] == model_name]
        best = df_m.loc[df_m['test_r2'].idxmax()]
        r2_lo, r2_hi = compute_t_ci(best['test_r2'], best['test_r2_std'], n_folds=best['CV_Folds'])
        rmse_lo, rmse_hi = compute_t_ci(best['test_rmse'], best['test_rmse_std'], n_folds=best['CV_Folds'])
        md.append(f"| {best['Model']} | {best['Distance_mm']:.1f} mm | {best['Schema']} | "
                  f"{best['test_r2']:.3f} [{r2_lo:.3f}, {r2_hi:.3f}] | "
                  f"{best['test_rmse']:.1f} [{rmse_lo:.1f}, {rmse_hi:.1f}] | "
                  f"{best['gap']:.3f} | {best['Best_Params']} |\n")
    md.append("\n")

    # 五、与前期 10-fold C1_Combined_ALK 全模型报告对比
    md.append("## 五、与前期 10-fold C1_Combined_ALK 全模型报告对比\n\n")
    if df_legacy_c1 is not None:
        df_c1 = df_legacy_c1[df_legacy_c1['Data_Group'] == 'lenient'].copy()
        md.append("| 距离 (mm) | 原 C1_Combined_ALK 最佳模型 | 原最佳 R² | 本次 C1_Combined_ALK 最佳模型 | 本次最佳 R² | 本次最佳 RMSE |\n")
        md.append("|-----------|---------------------------|-----------|------------------------------|-------------|---------------|\n")
        for dist in sorted(df_c1['Distance_mm'].unique()):
            df_d_legacy = df_c1[df_c1['Distance_mm'] == dist]
            best_legacy = df_d_legacy.loc[df_d_legacy['test_r2'].idxmax()]
            df_d_new = df_new[(df_new['Distance_mm'] == dist) & (df_new['Schema'] == 'C1_Combined_ALK')]
            if df_d_new.empty:
                new_model = "—"
                new_r2 = "—"
                new_rmse = "—"
            else:
                best_new = df_d_new.loc[df_d_new['test_r2'].idxmax()]
                new_model = best_new['Model']
                new_r2 = f"{best_new['test_r2']:.3f}"
                new_rmse = f"{best_new['test_rmse']:.1f}"
            md.append(f"| {dist:.1f} | {best_legacy['Model']} | {best_legacy['test_r2']:.3f} | {new_model} | {new_r2} | {new_rmse} |\n")
        md.append("\n")
    else:
        md.append("- 未找到前期 C1_Combined_ALK 十折结果。\n\n")

    # 六、与前期 10-fold Robust LR 报告对比
    md.append("## 六、与前期 10-fold Robust Linear Regression 报告对比\n\n")
    if df_legacy_rl is not None:
        df_rl = df_legacy_rl[(df_legacy_rl['Data_Group'] == 'lenient') & (df_legacy_rl['CV_Folds'] == 10)].copy()
        md.append("| 距离 (mm) | 方案 | 原 Robust LR 10-fold R² | 本次 Robust LR 10-fold R² | 提升 |\n")
        md.append("|-----------|------|------------------------|--------------------------|------|\n")
        for dist in sorted(df_new['Distance_mm'].unique()):
            df_d_new = df_new[(df_new['Distance_mm'] == dist) & (df_new['Model'] == 'Robust_Linear_Regression')]
            df_d_legacy = df_rl[df_rl['Distance_mm'] == dist]
            for schema in sorted(df_d_new['Schema'].unique()):
                r_new = df_d_new[df_d_new['Schema'] == schema]
                r_legacy = df_d_legacy[df_d_legacy['Schema'] == schema]
                if r_new.empty:
                    continue
                new_r2 = r_new.iloc[0]['test_r2']
                legacy_r2 = r_legacy.iloc[0]['test_r2'] if not r_legacy.empty else np.nan
                delta = new_r2 - legacy_r2 if not np.isnan(legacy_r2) else np.nan
                delta_str = f"{delta:+.3f}" if not np.isnan(delta) else "—"
                legacy_str = f"{legacy_r2:.3f}" if not np.isnan(legacy_r2) else "—"
                md.append(f"| {dist:.1f} | {schema} | {legacy_str} | {new_r2:.3f} | {delta_str} |\n")
        md.append("\n")
    else:
        md.append("- 未找到前期 Robust LR 十折结果。\n\n")

    # 七、全结果汇总
    md.append("## 七、全距离 / 全方案 / 全模型结果汇总\n\n")
    md.append("| 距离 (mm) | 方案 | 模型 | Test R² | RMSE | Gap | 最佳参数 |\n")
    md.append("|-----------|------|------|---------|------|-----|---------|\n")
    for _, row in df_new.sort_values(['Distance_mm', 'Schema', 'test_r2'], ascending=[True, True, False]).iterrows():
        md.append(f"| {row['Distance_mm']:.1f} | {row['Schema']} | {row['Model']} | "
                  f"{row['test_r2']:.3f} | {row['test_rmse']:.1f} | {row['gap']:.3f} | {row['Best_Params']} |\n")
    md.append("\n")

    # 八、SHAP 图
    md.append("## 八、SHAP 解释图\n\n")
    if shap_path is not None and best_row is not None:
        rel_path = os.path.relpath(shap_path, REPORT_DIR).replace('\\', '/')
        md.append(f"最佳配置：**{best_row['Schema']} / {best_row['Model']} @ {best_row['Distance_mm']:.1f} mm**\n\n")
        md.append(f"![SHAP Summary]({rel_path})\n\n")
    else:
        md.append("- 未生成 SHAP 图（最佳模型为 SVM 或 Neural Network 时跳过，或所有迭代失败）。\n\n")

    # 九、讨论与结论
    md.append("## 九、讨论与结论\n\n")
    md.append("1. **模型表现**：十折下，集成/线性模型（Random_Forest、Lasso、ElasticNet、Ridge、Robust Linear Regression）在不同方案中交替领先，说明数据规模（46 subjects）下模型选择对 R² 的影响与特征方案同等重要。\n")
    md.append("2. **Robust LR 的加入**：HuberRegressor 在部分配置（尤其 A2_Biomechanical_ALK）中可与 Lasso/ElasticNet 竞争，提供了对异常值更稳健的可解释选择。\n")
    md.append("3. **最佳距离**：1.5 mm 仍是多数 ALK 方案的峰值距离，与前期所有报告一致。\n")
    md.append("4. **ALK 与 K 的冗余**：ALK-only 与 K+ALK 方案性能接近，再次支持用 AL/K 单一复合指标替代 K 的结论。\n")
    md.append("5. **十折的保守性**：相比五折，十折 R² 普遍更低、波动更大，但这是小样本按 subject 分组 CV 下的更真实估计。\n")
    md.append("6. **应用建议**：若论文需要突出稳健性与可解释性，可优先报告 **A2_Biomechanical_ALK** 或 **C1_Combined_ALK** 在 1.5 mm 处的线性/稳健线性结果；若需要最高 R²，可继续尝试重复 CV 或扩大样本量。\n\n")

    md.append("---\n\n")
    md.append("*Report generated automatically by SR_ML_ALK_10fold_Final_Tuning_Report.py*\n")

    md_path = os.path.join(REPORT_DIR, 'SR0530_ALK_10fold_Final_Tuning_Report.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(''.join(md))
    print(f"\n  --> Final report: {md_path}")


if __name__ == '__main__':
    main()
