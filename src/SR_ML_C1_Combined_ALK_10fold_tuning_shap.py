"""
SR0530 C1_Combined_ALK 10-fold GroupKFold 超参数寻优 + SHAP 报告

- 仅针对 C1_Combined_ALK 方案（SE + AL + Age + Gender + AL/K）
- 使用 lenient 数据组（71 眼 / 46 subjects）
- 10-fold GroupKFold by Subject，按 Myopia 分层
- 对最佳配置绘制 Cross-Validated SHAP summary
- 输出报告：R² / RMSE / MAPE 及最佳参数
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
from sklearn.linear_model import Lasso, ElasticNet, Ridge
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from xgboost import XGBRegressor

import shap
warnings.filterwarnings('ignore')

# ============================================================
# 配置
# ============================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'genData', 'CleanDataRoi_lenient')
OUT_DIR = os.path.join(BASE_DIR, 'genData', 'sum')
REPORT_DIR = os.path.join(BASE_DIR, 'report')
FIG_DIR = os.path.join(REPORT_DIR, 'FIG', 'C1_Combined_ALK_10fold')
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

SCHEMA = {'C1_Combined_ALK': ['SE', 'AL', 'Age', 'Gender', 'ALK']}

MYOPIA_THRESHOLD = -0.5
RANDOM_STATE = 42
N_ITER = 30
N_SPLITS = 10

MODE_LABEL = 'C1_Combined_ALK_10fold'

# ============================================================
# 参数搜索空间
# ============================================================
PARAM_SPACE = {
    'SVM': {
        'model': lambda p: Pipeline([('s', StandardScaler()), ('v', SVR(**p))]),
        'params': {
            'C': [100, 500, 1000, 2000, 5000],
            'epsilon': [100, 300, 500, 800, 1000],
            'gamma': [0.001, 0.005, 0.01, 0.03, 0.05, 0.1]
        }
    },
    'Random_Forest': {
        'model': lambda p: Pipeline([('s', StandardScaler()), ('rf', RandomForestRegressor(**p, random_state=RANDOM_STATE, n_jobs=1))]),
        'params': {
            'n_estimators': [50, 100, 200, 300],
            'max_depth': [2, 3, 4, 5, None],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4]
        }
    },
    'XGBoost': {
        'model': lambda p: XGBRegressor(**p, random_state=RANDOM_STATE, verbosity=0),
        'params': {
            'learning_rate': [0.001, 0.005, 0.01, 0.05, 0.1],
            'max_depth': [1, 2, 3, 4],
            'n_estimators': [30, 50, 100, 200],
            'reg_alpha': [0.1, 0.5, 1.0, 2.0],
            'reg_lambda': [0.1, 0.5, 1.0, 2.0]
        }
    },
    'Neural_Network': {
        'model': lambda p: Pipeline([('s', StandardScaler()), ('nn', MLPRegressor(**p, max_iter=5000, early_stopping=True, validation_fraction=0.15, n_iter_no_change=20, random_state=RANDOM_STATE))]),
        'params': {
            'hidden_layer_sizes': [(40,), (60,), (80,), (100,), (80, 40)],
            'alpha': [0.1, 0.3, 0.5, 1.0],
            'learning_rate_init': [0.0001, 0.0005, 0.001]
        }
    },
    'Lasso': {
        'model': lambda p: Pipeline([('s', StandardScaler()), ('lasso', Lasso(**p, max_iter=5000))]),
        'params': {
            'alpha': [0.001, 0.01, 0.1, 1.0, 10.0]
        }
    },
    'ElasticNet': {
        'model': lambda p: Pipeline([('s', StandardScaler()), ('en', ElasticNet(**p, max_iter=5000))]),
        'params': {
            'alpha': [0.001, 0.01, 0.1, 1.0],
            'l1_ratio': [0.1, 0.3, 0.5, 0.7, 0.9]
        }
    },
    'Ridge': {
        'model': lambda p: Pipeline([('s', StandardScaler()), ('ridge', Ridge(**p))]),
        'params': {
            'alpha': [0.01, 0.1, 1.0, 10.0, 100.0]
        }
    }
}

USE_Y_STD = {
    'SVM': False, 'Random_Forest': False, 'XGBoost': False,
    'Neural_Network': True, 'Lasso': False, 'ElasticNet': False, 'Ridge': False
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


def calc_scores(y_true, y_pred):
    r2 = r2_score(y_true, y_pred)
    corr = np.corrcoef(y_true, y_pred)[0, 1] if len(y_true) > 1 else 0
    mape = np.mean(np.abs((y_true - y_pred) / (y_true + 1e-10))) * 100
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    return r2, corr, mape, rmse


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


def evaluate_params(model_builder, params, X, y, groups, y_stratify, use_y_std=False, n_splits=10, random_state=42):
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
        'test_r2_std': np.std(test_r2_list, ddof=1),
        'test_corr': np.mean(test_corr_list),
        'test_mape': np.mean(test_mape_list),
        'test_rmse': np.mean(test_rmse_list),
        'test_rmse_std': np.std(test_rmse_list, ddof=1),
        'gap': np.mean(train_r2_list) - np.mean(test_r2_list),
        'fold_test_r2': test_r2_list,
        'fold_test_rmse': test_rmse_list
    }


def tune_model(model_name, model_config, X, y, groups, y_stratify, n_iter=30, random_state=42):
    rng = np.random.RandomState(random_state)
    best_score = -np.inf
    best_params = None
    best_metrics = None

    all_trials = []

    for i in range(n_iter):
        params = sample_params(model_config['params'], rng)
        metrics = evaluate_params(
            model_config['model'], params, X, y, groups, y_stratify,
            use_y_std=USE_Y_STD[model_name], n_splits=N_SPLITS, random_state=random_state + i
        )
        metrics['params'] = params
        all_trials.append(metrics)

        if metrics['test_r2'] > best_score:
            best_score = metrics['test_r2']
            best_params = params
            best_metrics = metrics

    return best_params, best_metrics, all_trials


# ============================================================
# SHAP 计算（Cross-Validated Method B）
# ============================================================
def build_model_obj(model_name, params):
    if model_name == 'SVM':
        return Pipeline([('s', StandardScaler()), ('v', SVR(**params))])
    if model_name == 'Random_Forest':
        return Pipeline([('s', StandardScaler()), ('rf', RandomForestRegressor(**params, random_state=RANDOM_STATE, n_jobs=1))])
    if model_name == 'XGBoost':
        return XGBRegressor(**params, random_state=RANDOM_STATE, verbosity=0)
    if model_name == 'Neural_Network':
        return Pipeline([('s', StandardScaler()), ('nn', MLPRegressor(**params, max_iter=5000, early_stopping=True, validation_fraction=0.15, n_iter_no_change=20, random_state=RANDOM_STATE))])
    if model_name == 'Lasso':
        return Pipeline([('s', StandardScaler()), ('lasso', Lasso(**params, max_iter=5000))])
    if model_name == 'ElasticNet':
        return Pipeline([('s', StandardScaler()), ('en', ElasticNet(**params, max_iter=5000))])
    if model_name == 'Ridge':
        return Pipeline([('s', StandardScaler()), ('ridge', Ridge(**params))])
    raise ValueError(model_name)


def compute_linear_shap(model, X_sample):
    scaler = model.named_steps['s']
    reg = model.named_steps.get('lasso') or model.named_steps.get('en') or model.named_steps.get('ridge')
    X_scaled = scaler.transform(X_sample)
    shap_vals = X_scaled * reg.coef_
    base_val = reg.intercept_
    return shap.Explanation(
        values=shap_vals,
        base_values=np.full(len(X_sample), base_val),
        data=X_sample.values,
        feature_names=list(X_sample.columns)
    )


def cross_validated_shap(model_name, params, X, y, groups, y_stratify, n_splits=10, random_state=42, sample_size=100):
    splits = group_stratified_kfold(groups, y_stratify, n_splits=n_splits, random_state=random_state)

    all_shap_exps = []
    for ti, vi in splits:
        model = build_model_obj(model_name, params)
        X_train, X_test = X.iloc[ti], X.iloc[vi]
        y_train = y.iloc[ti]

        if USE_Y_STD[model_name]:
            sx, sy = StandardScaler(), StandardScaler()
            Xt = sx.fit_transform(X_train)
            Xv = sx.transform(X_test)
            yt = sy.fit_transform(y_train.values.reshape(-1, 1)).ravel()
            model.fit(Xt, yt)
        else:
            model.fit(X_train, y_train)
            Xv = X_test

        if model_name in ['Lasso', 'ElasticNet', 'Ridge']:
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
            # SVM / Neural Network: use KernelExplainer on background + subset
            background = shap.sample(X_train, min(50, len(X_train)), random_state=random_state)
            explainer = shap.KernelExplainer(model.predict, background)
            sample_X = X_test.iloc[:min(sample_size, len(X_test))]
            sv = explainer.shap_values(sample_X.values, nsamples=100)
            exp = shap.Explanation(
                values=np.asarray(sv),
                base_values=np.full(len(sample_X), explainer.expected_value),
                data=sample_X.values,
                feature_names=list(sample_X.columns)
            )
        all_shap_exps.append(exp)

    # 合并
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
def compute_t_ci(mean, std, n_folds=10, alpha=0.05):
    if pd.isna(std) or n_folds < 2:
        return np.nan, np.nan
    se = std / np.sqrt(n_folds)
    t_val = stats.t.ppf(1 - alpha / 2, df=n_folds - 1)
    return mean - t_val * se, mean + t_val * se


def main():
    print("=" * 80)
    print("SR0530 C1_Combined_ALK 10-fold Hyperparameter Tuning + SHAP")
    print(f"Data group: lenient (71 eyes / 46 subjects)")
    print(f"Schema: C1_Combined_ALK (SE + AL + Age + Gender + AL/K)")
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

        schema_name = 'C1_Combined_ALK'
        feat_short = SCHEMA[schema_name]
        feat_full = [FEATURE_ALL[s] for s in feat_short]
        df_sub = fill_na(df.copy(), feat_full)

        X = df_sub[feat_full]
        y = df_sub[TARGET_COL]
        groups = df_sub['Real_Subject_ID'].values
        y_strat = df_sub['Myopia'].values

        n_subjects = len(np.unique(groups))
        n_eyes = len(df_sub)
        print(f"  N={n_eyes} eyes/{n_subjects} subjects")

        if n_subjects < 4:
            print(f"  -> Skipping: too few subjects ({n_subjects})")
            continue

        for model_name, model_config in PARAM_SPACE.items():
            print(f"  Tuning {model_name}...", end=' ', flush=True)
            best_params, best_metrics, trials = tune_model(
                model_name, model_config, X, y, groups, y_strat,
                n_iter=N_ITER, random_state=RANDOM_STATE
            )
            if best_metrics is None or best_params is None:
                print(f"-> {model_name}: all iterations failed, skipping")
                continue
            print(f"Best R2={best_metrics['test_r2']:.3f}")

            results.append({
                'Data_Group': 'lenient',
                'Distance_mm': dist,
                'Schema': schema_name,
                'Model': model_name,
                'N_Eyes': n_eyes,
                'N_Subjects': n_subjects,
                'Best_Params': str(best_params),
                **{k: v for k, v in best_metrics.items() if not isinstance(v, list)}
            })

            for trial in trials:
                all_trials.append({
                    'Data_Group': 'lenient',
                    'Distance_mm': dist,
                    'Schema': schema_name,
                    'Model': model_name,
                    'Params': str(trial['params']),
                    'Train_R2': trial['train_r2'],
                    'Test_R2': trial['test_r2'],
                    'Test_R2_Std': trial['test_r2_std'],
                    'Gap': trial['gap'],
                    'Test_MAPE': trial['test_mape'],
                    'Test_RMSE': trial['test_rmse'],
                    'Test_RMSE_Std': trial['test_rmse_std']
                })

    df_results = pd.DataFrame(results)
    df_trials = pd.DataFrame(all_trials)

    results_csv = os.path.join(OUT_DIR, f'SR0530_HP_Tuning_Results_{MODE_LABEL}.csv')
    trials_csv = os.path.join(OUT_DIR, f'SR0530_HP_Tuning_AllTrials_{MODE_LABEL}.csv')
    df_results.to_csv(results_csv, index=False, encoding='utf-8-sig')
    df_trials.to_csv(trials_csv, index=False, encoding='utf-8-sig')
    print(f"\nSaved: {results_csv}")
    print(f"Saved: {trials_csv}")

    # 对最佳配置生成 SHAP
    if not df_results.empty:
        best_row = df_results.loc[df_results['test_r2'].idxmax()]
        best_dist = best_row['Distance_mm']
        best_model = best_row['Model']
        best_params = eval(best_row['Best_Params'])

        print(f"\nGenerating SHAP for best config: {best_model} @ {best_dist:.1f} mm")
        df = aggregate_distance(all_data[best_dist], eye_to_subject, min_quadrants=1)
        feat_full = [FEATURE_ALL[s] for s in SCHEMA['C1_Combined_ALK']]
        df_sub = fill_na(df.copy(), feat_full)
        X = df_sub[feat_full]
        y = df_sub[TARGET_COL]
        groups = df_sub['Real_Subject_ID'].values
        y_strat = df_sub['Myopia'].values

        exp = cross_validated_shap(best_model, best_params, X, y, groups, y_strat, n_splits=N_SPLITS, random_state=RANDOM_STATE)
        shap_path = os.path.join(FIG_DIR, f'SR0530_{MODE_LABEL}_SHAP_Best_{best_model}_{best_dist:.1f}mm.png')
        plot_shap_summary(exp, f'C1_Combined_ALK {best_model} @ {best_dist:.1f} mm (10-fold CV SHAP)', shap_path)
        print(f"  -> SHAP saved: {shap_path}")

    # 生成报告
    generate_report(df_results, best_row if not df_results.empty else None, shap_path if not df_results.empty else None)

    print("\n" + "=" * 80)
    print("Done!")
    print("=" * 80)


# ============================================================
# 报告生成
# ============================================================
def generate_report(df_results, best_row, shap_path):
    md = []
    md.append(f"# SR0530 C1_Combined_ALK 十折超参数寻优报告\n\n")
    md.append("> **目标**：在 lenient 数据组（71 眼 / 46 subjects）上，仅针对 **C1_Combined_ALK** 方案（SE + AL + Age + Gender + AL/K）进行 10-fold GroupKFold by Subject 超参数寻优，并输出 SHAP 解释、R² 与 RMSE。\n\n")
    md.append("> **交叉验证**：10-fold GroupKFold by Subject，按 Myopia 分层；置信区间基于 10 个 fold 的标准差（t₀.₀₂₅,₉ = 2.262）。\n\n")
    md.append("> **搜索策略**：Random Search，每模型 30 组参数。\n\n")
    md.append("---\n\n")

    # 总体最佳
    md.append("## 一、总体最佳配置\n\n")
    if best_row is not None:
        r2_lo, r2_hi = compute_t_ci(best_row['test_r2'], best_row['test_r2_std'], n_folds=N_SPLITS)
        rmse_lo, rmse_hi = compute_t_ci(best_row['test_rmse'], best_row['test_rmse_std'], n_folds=N_SPLITS)
        md.append(f"- **数据组**：{best_row['Data_Group']}\n")
        md.append(f"- **距离**：{best_row['Distance_mm']:.1f} mm\n")
        md.append(f"- **方案**：{best_row['Schema']}\n")
        md.append(f"- **模型**：{best_row['Model']}\n")
        md.append(f"- **最佳 Test R²**：{best_row['test_r2']:.3f} [95% CI: {r2_lo:.3f}, {r2_hi:.3f}]\n")
        md.append(f"- **最佳 Test RMSE**：{best_row['test_rmse']:.1f} [95% CI: {rmse_lo:.1f}, {rmse_hi:.1f}]\n")
        md.append(f"- **MAPE**：{best_row['test_mape']:.2f}%\n")
        md.append(f"- **Gap**：{best_row['gap']:.3f}\n")
        md.append(f"- **最佳参数**：{best_row['Best_Params']}\n")
        md.append(f"- **样本量**：{int(best_row['N_Eyes'])} 眼 / {int(best_row['N_Subjects'])} subjects\n\n")
    else:
        md.append("- 未产生有效结果。\n\n")

    # 各距离结果
    md.append("## 二、各距离最佳结果（C1_Combined_ALK）\n\n")
    md.append("| 距离 (mm) | 最佳模型 | Test R² (95% CI) | RMSE (95% CI) | MAPE (%) | Gap | 最佳参数 |\n")
    md.append("|-----------|---------|------------------|----------------|----------|-----|---------|\n")
    for dist in sorted(df_results['Distance_mm'].unique()):
        df_d = df_results[df_results['Distance_mm'] == dist]
        best = df_d.loc[df_d['test_r2'].idxmax()]
        r2_lo, r2_hi = compute_t_ci(best['test_r2'], best['test_r2_std'], n_folds=N_SPLITS)
        rmse_lo, rmse_hi = compute_t_ci(best['test_rmse'], best['test_rmse_std'], n_folds=N_SPLITS)
        md.append(f"| {best['Distance_mm']:.1f} | {best['Model']} | "
                  f"{best['test_r2']:.3f} [{r2_lo:.3f}, {r2_hi:.3f}] | "
                  f"{best['test_rmse']:.1f} [{rmse_lo:.1f}, {rmse_hi:.1f}] | "
                  f"{best['test_mape']:.2f} | {best['gap']:.3f} | {best['Best_Params']} |\n")
    md.append("\n")

    # 每个模型最佳结果
    md.append("## 三、每个模型最佳结果\n\n")
    md.append("| 模型 | 最佳距离 | Test R² (95% CI) | RMSE (95% CI) | MAPE (%) | Gap | 最佳参数 |\n")
    md.append("|------|---------|------------------|----------------|----------|-----|---------|\n")
    for model_name in sorted(df_results['Model'].unique()):
        df_m = df_results[df_results['Model'] == model_name]
        best = df_m.loc[df_m['test_r2'].idxmax()]
        r2_lo, r2_hi = compute_t_ci(best['test_r2'], best['test_r2_std'], n_folds=N_SPLITS)
        rmse_lo, rmse_hi = compute_t_ci(best['test_rmse'], best['test_rmse_std'], n_folds=N_SPLITS)
        md.append(f"| {best['Model']} | {best['Distance_mm']:.1f} mm | "
                  f"{best['test_r2']:.3f} [{r2_lo:.3f}, {r2_hi:.3f}] | "
                  f"{best['test_rmse']:.1f} [{rmse_lo:.1f}, {rmse_hi:.1f}] | "
                  f"{best['test_mape']:.2f} | {best['gap']:.3f} | {best['Best_Params']} |\n")
    md.append("\n")

    # 全距离完整表格
    md.append("## 四、全距离 / 全模型结果汇总\n\n")
    md.append("| 距离 (mm) | 模型 | Test R² | Test RMSE | MAPE (%) | Gap | 最佳参数 |\n")
    md.append("|-----------|------|---------|-----------|----------|-----|---------|\n")
    for _, row in df_results.sort_values(['Distance_mm', 'test_r2'], ascending=[True, False]).iterrows():
        md.append(f"| {row['Distance_mm']:.1f} | {row['Model']} | {row['test_r2']:.3f} | "
                  f"{row['test_rmse']:.1f} | {row['test_mape']:.2f} | {row['gap']:.3f} | {row['Best_Params']} |\n")
    md.append("\n")

    # SHAP 图
    md.append("## 五、SHAP 解释图\n\n")
    if shap_path is not None:
        rel_path = os.path.relpath(shap_path, REPORT_DIR).replace('\\', '/')
        md.append(f"最佳配置：**{best_row['Model']} @ {best_row['Distance_mm']:.1f} mm**\n\n")
        md.append(f"![SHAP Summary]({rel_path})\n\n")
    else:
        md.append("- 未生成 SHAP 图。\n\n")

    # 讨论
    md.append("## 六、讨论\n\n")
    md.append("1. **十折 vs 五折**：10-fold 保留了按 subject 分组的分层结构，fold-level 估计更细，但样本量较小（46 subjects）时部分 fold 可能仅含 4–5 个 subject，R² 波动仍较大。\n")
    md.append("2. **AL/K 的角色**：在 C1_Combined 已包含 AL 的前提下，AL/K 与 K 可互换， peak 性能通常出现在 1.5 mm 附近。\n")
    md.append("3. **SHAP 解读**：SHAP summary 展示各特征对预测密度的边际贡献，可据此判断 AL/K 是否带来独立于 AL 的解释力。\n")
    md.append("4. **过拟合信号**：若 Gap（Train R² − Test R²）较大，提示模型在该配置下过拟合，应优先选择 Gap 小且 Test R² 高的线性模型。\n\n")

    md.append("---\n\n")
    md.append("*Report generated automatically by SR_ML_C1_Combined_ALK_10fold_tuning_shap.py*\n")

    md_path = os.path.join(REPORT_DIR, f'SR0530_C1_Combined_ALK_10fold_Tuning_SHAP_Report.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(''.join(md))
    print(f"\n  --> Report: {md_path}")


if __name__ == '__main__':
    main()
