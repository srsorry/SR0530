import os
import glob
import ast
import warnings
import numpy as np
import pandas as pd
from copy import deepcopy

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.svm import SVR
from sklearn.ensemble import RandomForestRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.linear_model import Lasso, ElasticNet, Ridge
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
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

# 精细寻优配置
COARSE_RESULTS_PATH = os.path.join(OUT_DIR, 'SR0530_HP_Tuning_Results.csv')
N_TOP_CONFIGS = 12       # 从 coarse 结果中选 top 12 个唯一配置
N_ITER_FINE = 50         # 每个配置精细搜索迭代次数
N_REPEATS_STABILITY = 20 # 稳定性评估重复次数

# 是否需要对 y 做标准化（只对 NN 启用）
USE_Y_STD = {
    'SVM': False, 'Random_Forest': False, 'XGBoost': False,
    'Neural_Network': True, 'Lasso': False, 'ElasticNet': False, 'Ridge': False
}


# ============================================================
# 工具函数（复用并扩展）
# ============================================================
def load_subject_mapping(data_dir):
    """从 data1.csv 读取 Eye_Label -> Subject_ID 映射"""
    df_ref = pd.read_csv(os.path.join(data_dir, 'data1.csv'))
    mapping = {}
    for _, row in df_ref.iterrows():
        eye_label = row['Eye_Label']
        subject_id = row['Subject_ID']
        mapping[eye_label] = subject_id
        mapping[subject_id] = subject_id
    return mapping


def load_distance_data(data_dir):
    """读取 44 个 ROI 文件，按距离聚合"""
    all_data = {}
    for f in sorted(glob.glob(os.path.join(data_dir, 'data*.csv'))):
        df = pd.read_csv(f)
        dist = df['Eccentricity (mm)'].iloc[0]
        if dist not in all_data:
            all_data[dist] = []
        all_data[dist].append(df)
    return all_data


def aggregate_distance(dfs, eye_to_subject):
    """按 Subject_ID + Eye 聚合 4 个象限"""
    feature_cols = list(FEATURE_ALL.values())
    base = dfs[0][['Subject_ID', 'Eye'] + feature_cols + [TARGET_COL]].copy()
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

    return base[['Subject_ID', 'Real_Subject_ID', 'Eye', 'Myopia'] + feature_cols + [TARGET_COL]].copy()


def fill_na(df, cols):
    """中位数填充缺失值"""
    for col in cols:
        if df[col].isna().any():
            df[col].fillna(df[col].median(), inplace=True)
    return df


def calc_scores(y_true, y_pred):
    """计算 R2、Corr、MAPE、RMSE"""
    r2 = r2_score(y_true, y_pred)
    corr = np.corrcoef(y_true, y_pred)[0, 1] if len(y_true) > 1 else 0
    mape = np.mean(np.abs((y_true - y_pred) / (y_true + 1e-10))) * 100
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    return r2, corr, mape, rmse


def group_stratified_kfold(groups, y_stratify, n_splits=5, random_state=42):
    """按 groups 分组，并在每层内按 y_stratify 分层"""
    rng = np.random.RandomState(random_state)
    df_idx = pd.DataFrame({'idx': np.arange(len(groups)), 'group': groups, 'y': y_stratify})

    group_info = df_idx.groupby('group').agg({'y': lambda x: int(x.mode()[0]), 'idx': list}).reset_index()
    group_info = group_info.sample(frac=1, random_state=random_state).reset_index(drop=True)

    pos_groups = group_info[group_info['y'] == 1].copy().reset_index(drop=True)
    neg_groups = group_info[group_info['y'] == 0].copy().reset_index(drop=True)

    folds = [[] for _ in range(n_splits)]
    for label_df in [pos_groups, neg_groups]:
        for i, row in label_df.iterrows():
            folds[i % n_splits].extend(row['idx'])

    # 空 fold 保护
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


def get_model_builder(model_name):
    """返回模型构建器"""
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


# ============================================================
# 精细参数空间构建
# ============================================================
def near_values_log(current, steps, lower_bound=None, upper_bound=None):
    """在对数尺度上取 current 附近的值"""
    if current <= 0:
        return [current]
    vals = []
    for s in steps:
        vals.append(current * s)
    if lower_bound is not None:
        vals = [max(v, lower_bound) for v in vals]
    if upper_bound is not None:
        vals = [min(v, upper_bound) for v in vals]
    return sorted(list(set([round(v, 6) for v in vals])))


def near_values_linear(current, steps, lower_bound=None, upper_bound=None, dtype=float):
    """在线性尺度上取 current 附近的整数值"""
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
    """基于 coarse 最佳参数构建更密集的精细搜索空间"""
    if model_name == 'SVM':
        c = coarse_params.get('C', 1000)
        eps = coarse_params.get('epsilon', 300)
        gamma = coarse_params.get('gamma', 0.01)
        return {
            'C': near_values_log(c, [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0], lower_bound=10, upper_bound=10000),
            'epsilon': near_values_log(eps, [0.5, 0.75, 1.0, 1.5, 2.0], lower_bound=10, upper_bound=2000),
            'gamma': near_values_log(gamma, [0.2, 0.5, 0.8, 1.0, 1.5, 2.0, 3.0], lower_bound=0.0001, upper_bound=0.5)
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
            'learning_rate': near_values_log(lr, [0.2, 0.5, 0.8, 1.0, 1.5, 2.0, 3.0], lower_bound=0.0001, upper_bound=0.5),
            'max_depth': near_values_linear(int(depth), [-2, -1, 0, 1, 2], lower_bound=1, upper_bound=6, dtype=int),
            'n_estimators': near_values_linear(int(n_est), [-150, -100, -50, 0, 50, 100, 150], lower_bound=20, upper_bound=500, dtype=int),
            'reg_alpha': near_values_log(alpha, [0.2, 0.5, 0.8, 1.0, 1.5, 2.0, 3.0], lower_bound=0.001, upper_bound=5.0),
            'reg_lambda': near_values_log(lam, [0.2, 0.5, 0.8, 1.0, 1.5, 2.0, 3.0], lower_bound=0.001, upper_bound=5.0)
        }
    elif model_name == 'Neural_Network':
        hls = coarse_params.get('hidden_layer_sizes', (100,))
        alpha = coarse_params.get('alpha', 0.3)
        lr = coarse_params.get('learning_rate_init', 0.0005)
        # 在网络结构附近扩展
        hls_options = [(40,), (60,), (80,), (100,), (120,), (80, 40), (100, 50), (120, 60)]
        if hls not in hls_options:
            hls_options.append(hls)
        return {
            'hidden_layer_sizes': hls_options,
            'alpha': near_values_log(alpha, [0.2, 0.5, 0.8, 1.0, 1.5, 2.0, 3.0], lower_bound=0.001, upper_bound=3.0),
            'learning_rate_init': near_values_log(lr, [0.2, 0.5, 0.8, 1.0, 1.5, 2.0, 3.0], lower_bound=0.00001, upper_bound=0.01)
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
    """从参数空间中随机采样一组参数（兼容元组等复杂类型）"""
    import random
    params = {}
    for k, v in param_space.items():
        if isinstance(v, list):
            params[k] = random.choice(v)
        else:
            params[k] = v
    return params


def evaluate_params(model_builder, params, X, y, groups, y_stratify, use_y_std=False, n_splits=5, random_state=42):
    """对一组参数做 GroupKFold 评估，返回平均 Test R2"""
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
        'gap': np.mean(train_r2_list) - np.mean(test_r2_list)
    }


def stability_eval(model_builder, params, X, y, groups, y_stratify, use_y_std=False, n_splits=5, n_repeats=20):
    """用不同 seed 重复评估最佳参数，返回稳定性指标"""
    scores = []
    for r in range(n_repeats):
        metrics = evaluate_params(
            model_builder, params, X, y, groups, y_stratify,
            use_y_std=use_y_std, n_splits=n_splits, random_state=RANDOM_STATE + r * 100
        )
        scores.append(metrics['test_r2'])
    scores = np.array(scores)
    return {
        'stability_mean': np.mean(scores),
        'stability_std': np.std(scores),
        'stability_ci_lower': np.percentile(scores, 2.5),
        'stability_ci_upper': np.percentile(scores, 97.5),
        'stability_min': np.min(scores),
        'stability_max': np.max(scores),
        'stability_scores': scores.tolist()
    }


def fine_tune(model_name, model_builder, fine_space, X, y, groups, y_stratify, n_iter=50, random_state=42):
    """对一个模型做精细随机参数寻优"""
    rng = np.random.RandomState(random_state)
    best_score = -np.inf
    best_params = None
    best_metrics = None

    all_trials = []

    for i in range(n_iter):
        params = sample_params(fine_space, rng)
        metrics = evaluate_params(
            model_builder, params, X, y, groups, y_stratify,
            use_y_std=USE_Y_STD[model_name], random_state=random_state + i
        )
        metrics['params'] = params
        all_trials.append(metrics)

        if metrics['test_r2'] > best_score:
            best_score = metrics['test_r2']
            best_params = params
            best_metrics = metrics

    return best_params, best_metrics, all_trials


# ============================================================
# 主程序
# ============================================================
def select_top_configs(coarse_df, n_top=12):
    """从 coarse 结果中选择 top N 个唯一的 (data_group, distance, schema, model) 配置"""
    # 按组合去重，保留每个组合的最佳行
    grouped = coarse_df.loc[coarse_df.groupby(['Data_Group', 'Distance_mm', 'Schema', 'Model'])['test_r2'].idxmax()]
    # 按 test_r2 排序取 top N
    top = grouped.sort_values('test_r2', ascending=False).head(n_top).reset_index(drop=True)
    return top


def main():
    print("=" * 80)
    print("SR0530 ML Fine-Tuning on Top Configurations")
    print(f"Coarse results: {COARSE_RESULTS_PATH}")
    print(f"Top configs: {N_TOP_CONFIGS} | Fine iterations: {N_ITER_FINE} | Stability repeats: {N_REPEATS_STABILITY}")
    print("=" * 80)

    # 1. 读取 coarse 结果
    coarse_df = pd.read_csv(COARSE_RESULTS_PATH)
    top_configs = select_top_configs(coarse_df, N_TOP_CONFIGS)

    print(f"\nSelected top {len(top_configs)} configurations:")
    for i, row in top_configs.iterrows():
        print(f"  {i+1}. {row['Data_Group']} {row['Distance_mm']:.1f}mm {row['Schema']} {row['Model']} R2={row['test_r2']:.3f}")

    # 2. 预加载数据
    data_cache = {}
    for data_group, data_dir in DATA_DIRS.items():
        eye_to_subject = load_subject_mapping(data_dir)
        all_data = load_distance_data(data_dir)
        for dist, dfs in all_data.items():
            df = aggregate_distance(dfs, eye_to_subject)
            data_cache[(data_group, dist)] = df
        print(f"  -> Cached {len(all_data)} distances for {data_group}")

    # 3. 对每个 top 配置做精细寻优
    results = []
    all_trials = []

    for i, row in top_configs.iterrows():
        data_group = row['Data_Group']
        dist = row['Distance_mm']
        schema_name = row['Schema']
        model_name = row['Model']
        coarse_best_params = ast.literal_eval(row['Best_Params'])

        print(f"\n[{i+1}/{len(top_configs)}] Fine-tuning {data_group} {dist:.1f}mm {schema_name} {model_name}")
        print(f"  Coarse best params: {coarse_best_params}")

        df = data_cache[(data_group, dist)]
        feat_full = [FEATURE_ALL[s] for s in SCHEMA[schema_name]]
        df_sub = fill_na(df.copy(), feat_full)

        X = df_sub[feat_full]
        y = df_sub[TARGET_COL]
        groups = df_sub['Real_Subject_ID'].values
        y_strat = df_sub['Myopia'].values

        n_subjects = len(np.unique(groups))
        n_eyes = len(df_sub)

        if n_subjects < 4:
            print(f"  -> Skipping: too few subjects ({n_subjects})")
            continue

        # 构建精细参数空间
        fine_space = build_fine_space(model_name, coarse_best_params)
        print(f"  Fine param space: {fine_space}")

        # 运行精细寻优
        model_builder = get_model_builder(model_name)
        best_params, best_metrics, trials = fine_tune(
            model_name, model_builder, fine_space, X, y, groups, y_strat,
            n_iter=N_ITER_FINE, random_state=RANDOM_STATE + i * 1000
        )

        print(f"  Fine best R2={best_metrics['test_r2']:.3f} params={best_params}")

        # 稳定性评估
        stability = stability_eval(
            model_builder, best_params, X, y, groups, y_strat,
            use_y_std=USE_Y_STD[model_name], n_splits=5, n_repeats=N_REPEATS_STABILITY
        )
        print(f"  Stability: {stability['stability_mean']:.3f} ± {stability['stability_std']:.3f} "
              f"[{stability['stability_ci_lower']:.3f}, {stability['stability_ci_upper']:.3f}]")

        # 保存结果
        results.append({
            'Data_Group': data_group,
            'Distance_mm': dist,
            'Schema': schema_name,
            'Model': model_name,
            'N_Eyes': n_eyes,
            'N_Subjects': n_subjects,
            'Coarse_Test_R2': row['test_r2'],
            'Coarse_Best_Params': str(coarse_best_params),
            'Fine_Test_R2': best_metrics['test_r2'],
            'Fine_Train_R2': best_metrics['train_r2'],
            'Fine_Test_R2_Std': best_metrics['test_r2_std'],
            'Fine_Test_Corr': best_metrics['test_corr'],
            'Fine_Test_MAPE': best_metrics['test_mape'],
            'Fine_Test_RMSE': best_metrics['test_rmse'],
            'Fine_Gap': best_metrics['gap'],
            'Fine_Best_Params': str(best_params),
            'Stability_Mean': stability['stability_mean'],
            'Stability_Std': stability['stability_std'],
            'Stability_CI_Lower': stability['stability_ci_lower'],
            'Stability_CI_Upper': stability['stability_ci_upper'],
            'Stability_Min': stability['stability_min'],
            'Stability_Max': stability['stability_max']
        })

        # 保存所有尝试
        for trial in trials:
            all_trials.append({
                'Data_Group': data_group,
                'Distance_mm': dist,
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

    df_results.to_csv(os.path.join(OUT_DIR, 'SR0530_Fine_Tuning_Results.csv'), index=False, encoding='utf-8-sig')
    df_trials.to_csv(os.path.join(OUT_DIR, 'SR0530_Fine_Tuning_AllTrials.csv'), index=False, encoding='utf-8-sig')
    print(f"\nSaved: {os.path.join(OUT_DIR, 'SR0530_Fine_Tuning_Results.csv')}")
    print(f"Saved: {os.path.join(OUT_DIR, 'SR0530_Fine_Tuning_AllTrials.csv')}")

    # 5. 生成可视化和报告
    generate_visualizations(df_results)
    generate_report(df_results, top_configs)

    print("\n" + "=" * 80)
    print("Fine-tuning complete!")
    print("=" * 80)


# ============================================================
# 可视化
# ============================================================
def generate_visualizations(df_results):
    """生成精细寻优结果可视化"""
    if df_results.empty:
        print("  -> No results to visualize")
        return

    # 1. Coarse vs Fine Test R2 对比柱状图
    fig, ax = plt.subplots(figsize=(14, 8))
    x = np.arange(len(df_results))
    width = 0.35
    labels = [f"{r['Data_Group']}\n{r['Distance_mm']:.1f}mm\n{r['Schema']}\n{r['Model']}" for _, r in df_results.iterrows()]

    ax.bar(x - width/2, df_results['Coarse_Test_R2'], width, label='Coarse R²', alpha=0.8)
    ax.bar(x + width/2, df_results['Fine_Test_R2'], width, label='Fine R²', alpha=0.8)
    ax.axhline(0, color='gray', linestyle='--', linewidth=0.8)
    ax.set_xlabel('Configuration')
    ax.set_ylabel('Test R²')
    ax.set_title('Coarse vs Fine-Tuned Test R² for Top Configurations')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=8)
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    fig_path = os.path.join(OUT_DIR, 'SR0530_Fine_Tuning_Coarse_vs_Fine.png')
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(FIG_DIR, os.path.basename(fig_path)), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  --> Saved: {fig_path}")

    # 2. 稳定性误差条图
    fig, ax = plt.subplots(figsize=(14, 8))
    means = df_results['Stability_Mean']
    stds = df_results['Stability_Std']
    ci_lower = df_results['Stability_CI_Lower']
    ci_upper = df_results['Stability_CI_Upper']
    yerr = [means - ci_lower, ci_upper - means]

    ax.errorbar(x, means, yerr=yerr, fmt='o', capsize=5, capthick=2, elinewidth=2, markersize=8)
    ax.axhline(0, color='gray', linestyle='--', linewidth=0.8)
    ax.set_xlabel('Configuration')
    ax.set_ylabel('Test R²')
    ax.set_title(f'Stability of Fine-Tuned Configurations (N={N_REPEATS_STABILITY} repeated CV)')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=8)
    ax.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    fig_path = os.path.join(OUT_DIR, 'SR0530_Fine_Tuning_Stability.png')
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(FIG_DIR, os.path.basename(fig_path)), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  --> Saved: {fig_path}")

    # 3. Fine R2 vs Stability Std 散点图
    fig, ax = plt.subplots(figsize=(10, 7))
    scatter = ax.scatter(df_results['Fine_Test_R2'], df_results['Stability_Std'],
                         c=df_results['N_Subjects'], cmap='viridis', s=200, alpha=0.7, edgecolors='black')
    for i, row in df_results.iterrows():
        ax.annotate(f"{row['Data_Group'][:3]} {row['Distance_mm']:.1f}mm\n{row['Model']}",
                    (row['Fine_Test_R2'], row['Stability_Std']),
                    textcoords="offset points", xytext=(5, 5), fontsize=7)
    ax.set_xlabel('Fine-Tuned Test R²')
    ax.set_ylabel('Stability Std (R²)')
    ax.set_title('Performance vs Stability Trade-off')
    ax.grid(True, alpha=0.3)
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('N Subjects')
    plt.tight_layout()
    fig_path = os.path.join(OUT_DIR, 'SR0530_Fine_Tuning_Performance_vs_Stability.png')
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(FIG_DIR, os.path.basename(fig_path)), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  --> Saved: {fig_path}")


# ============================================================
# 报告生成
# ============================================================
def generate_report(df_results, top_configs):
    """生成 Markdown 精细寻优报告"""
    md = []
    md.append("# SR0530 ML 精细寻优报告（Top 配置）\n\n")
    md.append(f"> **目标**：对粗粒度寻优中表现最好的 {len(top_configs)} 个配置做精细参数寻优与稳定性评估。\n\n")
    md.append(f"> **搜索策略**：Random Search + GroupKFold by Subject，每配置 {N_ITER_FINE} 组参数\n\n")
    md.append(f"> **稳定性评估**：对最佳参数用 {N_REPEATS_STABILITY} 组不同 CV seed 重复评估\n\n")

    md.append("---\n\n")

    # 一、Top 配置来源
    md.append("## 一、从粗粒度寻优中选择的 Top 配置\n\n")
    md.append("| 排名 | 数据组 | 距离 (mm) | 方案 | 模型 | Coarse R² | Coarse 最佳参数 |\n")
    md.append("|------|--------|-----------|------|------|-----------|------------------|\n")
    for i, (_, row) in enumerate(top_configs.iterrows(), 1):
        md.append(f"| {i} | {row['Data_Group']} | {row['Distance_mm']:.1f} | {row['Schema']} | {row['Model']} | "
                  f"{row['test_r2']:.3f} | `{row['Best_Params']}` |\n")
    md.append("\n")

    # 二、总体最佳配置
    md.append("## 二、精细寻优后的总体最佳配置\n\n")
    if not df_results.empty:
        best_row = df_results.loc[df_results['Fine_Test_R2'].idxmax()]
        md.append(f"- **数据组**：{best_row['Data_Group']}\n")
        md.append(f"- **距离**：{best_row['Distance_mm']:.1f} mm\n")
        md.append(f"- **方案**：{best_row['Schema']}\n")
        md.append(f"- **模型**：{best_row['Model']}\n")
        md.append(f"- **精细后 Test R²**：{best_row['Fine_Test_R2']:.3f} (Coarse: {best_row['Coarse_Test_R2']:.3f})\n")
        md.append(f"- **Train R²**：{best_row['Fine_Train_R2']:.3f}，**Gap**：{best_row['Fine_Gap']:.3f}\n")
        md.append(f"- **MAPE**：{best_row['Fine_Test_MAPE']:.2f}%，**RMSE**：{best_row['Fine_Test_RMSE']:.1f}\n")
        md.append(f"- **最佳参数**：{best_row['Fine_Best_Params']}\n")
        md.append(f"- **稳定性**：{best_row['Stability_Mean']:.3f} ± {best_row['Stability_Std']:.3f} "
                  f"(95% CI: [{best_row['Stability_CI_Lower']:.3f}, {best_row['Stability_CI_Upper']:.3f}])\n")
        md.append(f"- **样本量**：{int(best_row['N_Eyes'])} 眼 / {int(best_row['N_Subjects'])} subjects\n\n")
    else:
        md.append("无可用结果。\n\n")

    # 三、按稳定性排序
    md.append("## 三、按稳定性排序（稳定性 = 多次 CV 的 R² 均值）\n\n")
    md.append("| 数据组 | 距离 (mm) | 方案 | 模型 | Fine R² | 稳定性 Mean | 稳定性 Std | 95% CI | Gap |\n")
    md.append("|--------|-----------|------|------|---------|-------------|------------|--------|-----|\n")
    if not df_results.empty:
        df_sorted = df_results.sort_values('Stability_Mean', ascending=False)
        for _, row in df_sorted.iterrows():
            md.append(f"| {row['Data_Group']} | {row['Distance_mm']:.1f} | {row['Schema']} | {row['Model']} | "
                      f"{row['Fine_Test_R2']:.3f} | {row['Stability_Mean']:.3f} | {row['Stability_Std']:.3f} | "
                      f"[{row['Stability_CI_Lower']:.3f}, {row['Stability_CI_Upper']:.3f}] | {row['Fine_Gap']:.3f} |\n")
    md.append("\n")

    # 四、详细结果
    md.append("## 四、全部详细结果\n\n")
    md.append("| 数据组 | 距离 (mm) | 方案 | 模型 | N_Eyes | N_Subj | Coarse R² | Fine R² | Fine Train R² | Corr | MAPE | RMSE | Gap | 稳定性 Mean±Std | 稳定性 95% CI | Fine 最佳参数 |\n")
    md.append("|--------|-----------|------|------|--------|--------|-----------|---------|---------------|------|------|------|-----|-----------------|---------------|---------------|\n")
    if not df_results.empty:
        for _, row in df_results.iterrows():
            md.append(f"| {row['Data_Group']} | {row['Distance_mm']:.1f} | {row['Schema']} | {row['Model']} | "
                      f"{int(row['N_Eyes'])} | {int(row['N_Subjects'])} | {row['Coarse_Test_R2']:.3f} | "
                      f"{row['Fine_Test_R2']:.3f} | {row['Fine_Train_R2']:.3f} | {row['Fine_Test_Corr']:.3f} | "
                      f"{row['Fine_Test_MAPE']:.2f} | {row['Fine_Test_RMSE']:.1f} | {row['Fine_Gap']:.3f} | "
                      f"{row['Stability_Mean']:.3f} ± {row['Stability_Std']:.3f} | "
                      f"[{row['Stability_CI_Lower']:.3f}, {row['Stability_CI_Upper']:.3f}] | "
                      f"`{row['Fine_Best_Params']}` |\n")
    md.append("\n")

    # 五、可视化
    md.append("## 五、可视化\n\n")
    md.append("### Coarse vs Fine-Tuned Test R²\n\n")
    md.append("![Coarse vs Fine](FIG/SR0530_Fine_Tuning_Coarse_vs_Fine.png)\n\n")
    md.append("### 稳定性评估（20 次重复 CV）\n\n")
    md.append("![Stability](FIG/SR0530_Fine_Tuning_Stability.png)\n\n")
    md.append("### 性能 vs 稳定性权衡\n\n")
    md.append("![Performance vs Stability](FIG/SR0530_Fine_Tuning_Performance_vs_Stability.png)\n\n")

    # 六、讨论
    md.append("## 六、讨论\n\n")
    md.append("1. **精细寻优效果**：对比 Coarse R² 与 Fine R²，若 Fine 显著更高，说明原搜索空间分辨率不足；若差异不大，说明原参数已接近最优。\n")
    md.append("2. **稳定性优先**：高 R² 但高 Std 的配置可能过拟合；稳定性 Mean 高且 Std 低的配置更值得信赖。\n")
    md.append("3. **样本量影响**：N_Subjects 较少的配置（如远距离）稳定性通常更差，解读需谨慎。\n")
    md.append("4. **后续建议**：从本报告中选择 Stability Mean 最高的 1–2 个配置，作为最终报告用模型。\n\n")

    md.append("---\n\n")
    md.append("*Report generated automatically by SR_ML_fine_tuning.py*\n")

    md_path = os.path.join(REPORT_DIR, 'SR0530_ML_Fine_Tuning_Report.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(''.join(md))
    print(f"  --> Report: {md_path}")


if __name__ == '__main__':
    main()
