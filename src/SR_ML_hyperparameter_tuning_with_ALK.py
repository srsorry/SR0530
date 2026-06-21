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
DATA_DIR = os.path.join(BASE_DIR, 'genData', 'CleanDataRoi_lenient')
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
    'ACD': 'Anterior chamber depth (mm)',
    'ALK': 'AL/K ratio'
}

TARGET_COL = 'Angular cone density (cones/ deg2)'

# 本次只跑 lenient（71 眼），聚焦 AL/K 替换与叠加
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

# 用于对比的已有结果
BASELINE_RESULTS_CSV = os.path.join(OUT_DIR, 'SR0530_HP_Tuning_Results_q1plus.csv')
K_RESULTS_CSV = os.path.join(OUT_DIR, 'SR0530_HP_Tuning_Results_q1plus_K.csv')

MYOPIA_THRESHOLD = -0.5
RANDOM_STATE = 42
N_ITER = 30

MODE_LABEL = 'lenient_ALK'

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
    # 计算 AL/K
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


def group_stratified_kfold(groups, y_stratify, n_splits=5, random_state=42):
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


def tune_model(model_name, model_config, X, y, groups, y_stratify, n_iter=10, random_state=42):
    rng = np.random.RandomState(random_state)
    best_score = -np.inf
    best_params = None
    best_metrics = None

    all_trials = []

    for i in range(n_iter):
        params = sample_params(model_config['params'], rng)
        metrics = evaluate_params(
            model_config['model'], params, X, y, groups, y_stratify,
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
def main():
    print("=" * 80)
    print("SR0530 ML Hyperparameter Tuning: AL/K variants (lenient only)")
    print(f"Mode: {MODE_LABEL}")
    print("Data group: lenient (71 eyes)")
    print("Distances: 1.0-6.0 mm | Schemas: 8 AL/K variants | Models: 7")
    print(f"Random search iterations per model: {N_ITER}")
    print("=" * 80)

    checkpoint_results_csv = os.path.join(OUT_DIR, f'SR0530_HP_Tuning_Results_{MODE_LABEL}_checkpoint.csv')
    checkpoint_trials_csv = os.path.join(OUT_DIR, f'SR0530_HP_Tuning_AllTrials_{MODE_LABEL}_checkpoint.csv')

    if os.path.exists(checkpoint_results_csv):
        df_ckpt_results = pd.read_csv(checkpoint_results_csv)
        results = df_ckpt_results.to_dict('records')
        completed = set(df_ckpt_results['Distance_mm'].tolist())
        print(f"\nLoaded checkpoint: {len(results)} rows, {len(completed)} distances completed.")
    else:
        results = []
        completed = set()

    if os.path.exists(checkpoint_trials_csv):
        df_ckpt_trials = pd.read_csv(checkpoint_trials_csv)
        all_trials = df_ckpt_trials.to_dict('records')
    else:
        all_trials = []

    def save_checkpoint():
        pd.DataFrame(results).to_csv(checkpoint_results_csv, index=False, encoding='utf-8-sig')
        pd.DataFrame(all_trials).to_csv(checkpoint_trials_csv, index=False, encoding='utf-8-sig')
        print(f"    -> Checkpoint saved: {len(results)} results, {len(all_trials)} trials")

    eye_to_subject = load_subject_mapping(DATA_DIR)
    all_data = load_distance_data(DATA_DIR)
    distances = sorted(all_data.keys())

    for dist in distances:
        if dist in completed:
            print(f"\n--- Distance {dist:.1f} mm --- SKIPPED (already in checkpoint)")
            continue

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

            print(f"  [{schema_name}] N={n_eyes} eyes/{n_subjects} subjects")

            if n_subjects < 4:
                print(f"    -> Skipping: too few subjects ({n_subjects})")
                continue

            for model_name, model_config in PARAM_SPACE.items():
                print(f"    Tuning {model_name}...", end=' ', flush=True)
                best_params, best_metrics, trials = tune_model(
                    model_name, model_config, X, y, groups, y_strat,
                    n_iter=N_ITER, random_state=RANDOM_STATE
                )
                if best_metrics is None or best_params is None:
                    print(f"    -> {model_name}: all iterations failed, skipping")
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
                    **best_metrics
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

        save_checkpoint()

    df_results_alk = pd.DataFrame(results)
    df_trials = pd.DataFrame(all_trials)

    results_csv = os.path.join(OUT_DIR, f'SR0530_HP_Tuning_Results_{MODE_LABEL}.csv')
    trials_csv = os.path.join(OUT_DIR, f'SR0530_HP_Tuning_AllTrials_{MODE_LABEL}.csv')

    df_results_alk.to_csv(results_csv, index=False, encoding='utf-8-sig')
    df_trials.to_csv(trials_csv, index=False, encoding='utf-8-sig')
    print(f"\nSaved: {results_csv}")
    print(f"Saved: {trials_csv}")

    # 加载已有基线结果和 +K 结果用于对比
    df_results_base = pd.read_csv(BASELINE_RESULTS_CSV)
    df_results_k = pd.read_csv(K_RESULTS_CSV)
    df_results = pd.concat([df_results_base, df_results_k, df_results_alk], ignore_index=True)

    generate_visualizations(df_results, mode_label=MODE_LABEL)
    generate_report(df_results, mode_label=MODE_LABEL)

    print("\n" + "=" * 80)
    print("Hyperparameter tuning complete!")
    print("=" * 80)


# ============================================================
# 可视化
# ============================================================
def generate_visualizations(df_results, mode_label='lenient_ALK'):
    df_g = df_results[df_results['Data_Group'] == 'lenient']

    # 1. 热图：Distance vs Model，取最佳 Schema
    best_per_dm = df_g.loc[df_g.groupby(['Distance_mm', 'Model'])['test_r2'].idxmax()]
    pivot = best_per_dm.pivot(index='Distance_mm', columns='Model', values='test_r2')

    fig, ax = plt.subplots(figsize=(14, 8))
    vmax = max(0.5, np.nanmax(pivot.values))
    vmin = min(-0.5, np.nanmin(pivot.values))
    im = ax.imshow(pivot.values, aspect='auto', cmap='RdYlGn', vmin=vmin, vmax=vmax)
    ax.set_xticks(np.arange(len(pivot.columns)))
    ax.set_yticks(np.arange(len(pivot.index)))
    ax.set_xticklabels(pivot.columns, rotation=45, ha='right')
    ax.set_yticklabels([f"{d:.1f}" for d in pivot.index])
    ax.set_xlabel('Model')
    ax.set_ylabel('Distance (mm)')
    ax.set_title(f'Best Test R² by Distance and Model (lenient, {mode_label})')

    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = pivot.values[i, j]
            if not np.isnan(val):
                text_color = 'white' if abs(val) > 0.25 else 'black'
                ax.text(j, i, f"{val:.2f}", ha='center', va='center', color=text_color, fontsize=8)

    fig.colorbar(im, ax=ax, label='Test R²')
    plt.tight_layout()
    fig_path = os.path.join(OUT_DIR, f'SR0530_HP_Tuning_Heatmap_lenient_{mode_label}.png')
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(FIG_DIR, os.path.basename(fig_path)), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  --> Saved: {fig_path}")

    # 2. 方案对比：baseline vs K vs AL/K vs K+ALK
    fig, ax = plt.subplots(figsize=(14, 8))
    scheme_groups = {
        'A1 baseline': ['A1_Biomechanical_Core'],
        'A1 +K': ['A1_Biomechanical_Core_K'],
        'A1 +ALK': ['A1_Biomechanical_ALK'],
        'A1 +K+ALK': ['A1_Biomechanical_K_ALK'],
        'A2 baseline': ['A2_Biomechanical_NoK'],
        'A2 +K': ['A2_Biomechanical_WithK'],
        'A2 +ALK': ['A2_Biomechanical_ALK'],
        'A2 +K+ALK': ['A2_Biomechanical_K_ALK'],
        'C1 baseline': ['C1_Combined'],
        'C1 +K': ['C1_Combined_K'],
        'C1 +ALK': ['C1_Combined_ALK'],
        'C1 +K+ALK': ['C1_Combined_K_ALK'],
    }
    for label, schemas in scheme_groups.items():
        df_s = df_g[df_g['Schema'].isin(schemas)]
        if df_s.empty:
            continue
        best_per_d = df_s.loc[df_s.groupby('Distance_mm')['test_r2'].idxmax()]
        ax.plot(best_per_d['Distance_mm'], best_per_d['test_r2'], 'o-', label=label, linewidth=2, markersize=6)
    ax.axhline(0, color='gray', linestyle='--', linewidth=0.8)
    ax.set_xlabel('Distance (mm)')
    ax.set_ylabel('Best Test R²')
    ax.set_title(f'Schema Comparison: Baseline vs K vs AL/K vs K+ALK (lenient, {mode_label})')
    ax.legend(ncol=2, fontsize=8)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    fig_path = os.path.join(OUT_DIR, f'SR0530_HP_Tuning_SchemaComparison_{mode_label}.png')
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(FIG_DIR, os.path.basename(fig_path)), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  --> Saved: {fig_path}")


# ============================================================
# 报告生成
# ============================================================
def compute_t_ci(mean, std, n_folds=5, alpha=0.05):
    if pd.isna(std) or n_folds < 2:
        return np.nan, np.nan
    se = std / np.sqrt(n_folds)
    t_val = stats.t.ppf(1 - alpha / 2, df=n_folds - 1)
    return mean - t_val * se, mean + t_val * se


def generate_report(df_results, mode_label='lenient_ALK'):
    md = []
    md.append(f"# SR0530 ML 超参数寻优报告：AL/K 替代与叠加 K（lenient，{mode_label}）\n\n")
    md.append("> **目标**：在 71 眼 lenient 数据集上，比较用 AL/K 替代 K、以及在 K 基础上再叠加 AL/K 后，局部锥细胞密度预测能力的变化。\n\n")
    md.append("> **搜索策略**：Random Search + GroupKFold by Subject，每模型 30 组参数\n\n")
    md.append("> **象限策略**：≥1 象限可用（放宽，outer merge 取平均）\n\n")
    md.append("> **数据组**：lenient（71 眼 / 46 subjects）\n\n")
    md.append("> **置信区间说明**：Test R² 与 RMSE 后的 95% CI 基于 5-fold CV 的 fold-level 标准差，使用 t 分布近似（t₀.₀₂₅,₄ = 2.776）。\n\n")
    md.append("---\n\n")

    df_g = df_results[df_results['Data_Group'] == 'lenient'].copy()

    # 一、搜索空间
    md.append("## 一、参数搜索空间\n\n")
    md.append("| 模型 | 参数 | 搜索范围 |\n")
    md.append("|------|------|---------|\n")
    for model_name, config in PARAM_SPACE.items():
        for param_name, values in config['params'].items():
            value_str = ', '.join([str(v) for v in values])
            md.append(f"| {model_name} | {param_name} | {value_str} |\n")

    # 二、总体最佳配置
    md.append("\n## 二、总体最佳配置\n\n")
    best_row = df_g.loc[df_g['test_r2'].idxmax()]
    r2_lo, r2_hi = compute_t_ci(best_row['test_r2'], best_row['test_r2_std'])
    rmse_lo, rmse_hi = compute_t_ci(best_row['test_rmse'], best_row['test_rmse_std'])
    md.append(f"- **数据组**：{best_row['Data_Group']}\n")
    md.append(f"- **距离**：{best_row['Distance_mm']:.1f} mm\n")
    md.append(f"- **方案**：{best_row['Schema']}\n")
    md.append(f"- **模型**：{best_row['Model']}\n")
    md.append(f"- **最佳 Test R²**：{best_row['test_r2']:.3f} [95% CI: {r2_lo:.3f}, {r2_hi:.3f}]\n")
    md.append(f"- **最佳 RMSE**：{best_row['test_rmse']:.1f} [95% CI: {rmse_lo:.1f}, {rmse_hi:.1f}]\n")
    md.append(f"- **最佳参数**：{best_row['Best_Params']}\n")
    md.append(f"- **样本量**：{int(best_row['N_Eyes'])} 眼 / {int(best_row['N_Subjects'])} subjects\n\n")

    # 三、最佳结果（按距离）
    md.append("## 三、各距离最佳结果\n\n")
    md.append("| 距离 (mm) | 最佳方案 | 最佳模型 | Test R² (95% CI) | MAPE (%) | RMSE (95% CI) | Gap | 最佳参数 |\n")
    md.append("|-----------|---------|---------|------------------|----------|----------------|-----|---------|\n")
    for dist in sorted(df_g['Distance_mm'].unique()):
        df_d = df_g[df_g['Distance_mm'] == dist]
        best = df_d.loc[df_d['test_r2'].idxmax()]
        r2_lo, r2_hi = compute_t_ci(best['test_r2'], best['test_r2_std'])
        rmse_lo, rmse_hi = compute_t_ci(best['test_rmse'], best['test_rmse_std'])
        md.append(f"| {best['Distance_mm']:.1f} | {best['Schema']} | {best['Model']} | "
                  f"{best['test_r2']:.3f} [{r2_lo:.3f}, {r2_hi:.3f}] | {best['test_mape']:.2f} | "
                  f"{best['test_rmse']:.1f} [{rmse_lo:.1f}, {rmse_hi:.1f}] | "
                  f"{best['gap']:.3f} | {best['Best_Params']} |\n")
    md.append("\n")

    # 四、每个模型最佳结果
    md.append("## 四、每个模型最佳结果\n\n")
    md.append("| 模型 | 最佳距离 | 最佳方案 | Test R² (95% CI) | MAPE (%) | 最佳参数 |\n")
    md.append("|------|---------|---------|------------------|----------|---------|\n")
    for model_name in sorted(df_g['Model'].unique()):
        df_m = df_g[df_g['Model'] == model_name]
        best = df_m.loc[df_m['test_r2'].idxmax()]
        r2_lo, r2_hi = compute_t_ci(best['test_r2'], best['test_r2_std'])
        md.append(f"| {model_name} | {best['Distance_mm']:.1f} mm | {best['Schema']} | "
                  f"{best['test_r2']:.3f} [{r2_lo:.3f}, {r2_hi:.3f}] | {best['test_mape']:.2f} | {best['Best_Params']} |\n")
    md.append("\n")

    # 五、每个方案最佳结果
    md.append("## 五、每个特征方案最佳结果\n\n")
    md.append("| 方案 | 最佳距离 | 最佳模型 | Test R² (95% CI) |\n")
    md.append("|------|---------|---------|------------------|\n")
    for schema_name in df_g['Schema'].unique():
        df_s = df_g[df_g['Schema'] == schema_name]
        best = df_s.loc[df_s['test_r2'].idxmax()]
        r2_lo, r2_hi = compute_t_ci(best['test_r2'], best['test_r2_std'])
        md.append(f"| {schema_name} | {best['Distance_mm']:.1f} mm | {best['Model']} | "
                  f"{best['test_r2']:.3f} [{r2_lo:.3f}, {r2_hi:.3f}] |\n")
    md.append("\n")

    # 六、对比：baseline vs K vs AL/K vs K+ALK
    md.append("## 六、Baseline vs K vs AL/K vs K+ALK 对比\n\n")
    md.append("按方案族比较同一基础方案下加入 K、AL/K、K+AL/K 后的最佳 Test R²。\n\n")

    comparison_groups = {
        'A1': ['A1_Biomechanical_Core', 'A1_Biomechanical_Core_K', 'A1_Biomechanical_ALK', 'A1_Biomechanical_K_ALK'],
        'A2': ['A2_Biomechanical_NoK', 'A2_Biomechanical_WithK', 'A2_Biomechanical_ALK', 'A2_Biomechanical_K_ALK'],
        'B': ['B_Clinical', 'B_Clinical_K', 'B_Clinical_ALK', 'B_Clinical_K_ALK'],
        'C1': ['C1_Combined', 'C1_Combined_K', 'C1_Combined_ALK', 'C1_Combined_K_ALK']
    }

    for family, schemas in comparison_groups.items():
        md.append(f"### {family} 方案族\n\n")
        md.append("| 距离 (mm) | " + " | ".join(schemas) + " |\n")
        md.append("|-----------|" + "|".join(["---------"] * len(schemas)) + "|\n")
        for dist in sorted(df_g['Distance_mm'].unique()):
            df_d = df_g[df_g['Distance_mm'] == dist]
            row_vals = []
            for sch in schemas:
                df_s = df_d[df_d['Schema'] == sch]
                if df_s.empty:
                    row_vals.append("—")
                else:
                    best_r2 = df_s['test_r2'].max()
                    row_vals.append(f"{best_r2:.3f}")
            md.append(f"| {dist:.1f} | " + " | ".join(row_vals) + " |\n")
        md.append("\n")

    # 七、平均 R2 与提升统计
    md.append("## 七、各方案平均 Test R²（跨距离/模型）\n\n")
    md.append("| 方案 | 平均 Test R² |\n")
    md.append("|------|-------------|\n")
    schema_avg = df_g.groupby('Schema')['test_r2'].mean().sort_values(ascending=False)
    for schema, r2 in schema_avg.items():
        md.append(f"| {schema} | {r2:.3f} |\n")
    md.append("\n")

    # 八、讨论
    md.append("## 八、讨论\n\n")
    md.append("1. **AL/K 的替代效应**：若某基础方案的 AL/K 版本（*_ALK）R² 高于 K 版本（*_K），说明 AL/K 比 K 更能捕捉与局部密度相关的眼形态信息。\n")
    md.append("2. **AL/K 的叠加效应**：若 K+ALK 版本（*_K_ALK）高于单独 K 或 AL/K，说明两者提供互补信息。\n")
    md.append("3. **模型稳定性**：线性模型（Lasso/ElasticNet/Ridge）在本任务中通常更稳定，Gap 较小；树模型和神经网络可能过拟合。\n")
    md.append("4. **距离模式**：最佳预测通常出现在 1.5–2.0 mm，随距离增加 R² 下降。\n")
    md.append("5. **论文建议**：选择 R² 最高且跨距离稳定的方案作为最终模型；若 AL/K 与 K 高度相关，则优先选择更简洁的单一特征版本。\n\n")

    md.append("---\n\n")
    md.append("*Report generated automatically by SR_ML_hyperparameter_tuning_with_ALK.py*\n")

    md_path = os.path.join(REPORT_DIR, f'SR0530_ML_Hyperparameter_Tuning_{mode_label}_Report.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(''.join(md))
    print(f"  --> Report: {md_path}")


if __name__ == '__main__':
    main()
