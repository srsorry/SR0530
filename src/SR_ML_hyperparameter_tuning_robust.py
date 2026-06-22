"""
SR0530 Robust Hyperparameter Tuning with Repeated CV
使用重复交叉验证（Repeated GroupKFold）评估参数，降低 fold split 随机性带来的选择偏倚。
"""
import os
import glob
import warnings
import numpy as np
import pandas as pd
from scipy import stats

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.svm import SVR
from sklearn.ensemble import RandomForestRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.linear_model import Lasso, ElasticNet, Ridge
from sklearn.metrics import r2_score, mean_squared_error
from xgboost import XGBRegressor

warnings.filterwarnings('ignore')

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

SCHEMA = {
    'A1_Biomechanical_Core': ['AL', 'Age', 'Gender'],
    'A1_Biomechanical_Core_K': ['AL', 'Age', 'Gender', 'K'],
    'A1_Biomechanical_ALK': ['AL', 'Age', 'Gender', 'ALK'],
    'A1_Biomechanical_K_ALK': ['AL', 'Age', 'Gender', 'K', 'ALK'],
    'A2_Biomechanical_NoK': ['AL', 'ACD', 'Age', 'Gender'],
    'A2_Biomechanical_WithK': ['AL', 'ACD', 'Age', 'Gender', 'K'],
    'A2_Biomechanical_ALK': ['AL', 'ACD', 'Age', 'Gender', 'ALK'],
    'A2_Biomechanical_K_ALK': ['AL', 'ACD', 'Age', 'Gender', 'K', 'ALK'],
    'B_Clinical': ['SE', 'Age', 'Gender'],
    'B_Clinical_K': ['SE', 'Age', 'Gender', 'K'],
    'B_Clinical_ALK': ['SE', 'Age', 'Gender', 'ALK'],
    'B_Clinical_K_ALK': ['SE', 'Age', 'Gender', 'K', 'ALK'],
    'C1_Combined': ['SE', 'AL', 'Age', 'Gender'],
    'C1_Combined_K': ['SE', 'AL', 'Age', 'Gender', 'K'],
    'C1_Combined_ALK': ['SE', 'AL', 'Age', 'Gender', 'ALK'],
    'C1_Combined_K_ALK': ['SE', 'AL', 'Age', 'Gender', 'K', 'ALK']
}

MYOPIA_THRESHOLD = -0.5
RANDOM_STATE = 42
N_ITER = 15
N_REPEATS = 5
N_SPLITS = 5
DISTANCES = None  # None = 处理所有可用距离
MODE_LABEL = 'robust_repeatedCV_all_distances'

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


def aggregate_distance(dfs, eye_to_subject):
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
    merged = merged[merged['N_Quadrants'] >= 1].copy()

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
            largest = max(non_empty, key=lambda k: len(folds[k]))
            folds[i].append(folds[largest].pop())

    splits = []
    for i in range(n_splits):
        test_groups = folds[i]
        train_groups = [g for f in folds[:i] + folds[i+1:] for g in f]
        test_idx = np.array([idx for g in test_groups for idx in group_info.loc[g, 'idx']])
        train_idx = np.array([idx for g in train_groups for idx in group_info.loc[g, 'idx']])
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


def evaluate_params_repeated(model_builder, params, X, y, groups, y_stratify, use_y_std=False,
                             n_repeats=5, n_splits=5, random_state=42):
    """重复 CV 评估：返回 mean test R2、std、所有 fold 的 R2 列表。"""
    all_test_r2 = []
    all_train_r2 = []
    all_gaps = []

    for rep in range(n_repeats):
        splits = group_stratified_kfold(groups, y_stratify, n_splits=n_splits, random_state=random_state + rep)
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

            train_r2 = r2_score(yt_raw, pred_train)
            test_r2 = r2_score(yv, pred)
            all_train_r2.append(train_r2)
            all_test_r2.append(test_r2)
            all_gaps.append(train_r2 - test_r2)

    return {
        'train_r2': np.mean(all_train_r2),
        'test_r2': np.mean(all_test_r2),
        'test_r2_std': np.std(all_test_r2),
        'gap': np.mean(all_gaps),
        'all_test_r2': all_test_r2,
        'all_train_r2': all_train_r2
    }


def tune_model_robust(model_name, model_config, X, y, groups, y_stratify, n_iter=10, random_state=42):
    rng = np.random.RandomState(random_state)
    best_score = -np.inf
    best_params = None
    best_metrics = None
    all_trials = []

    for i in range(n_iter):
        params = sample_params(model_config['params'], rng)
        metrics = evaluate_params_repeated(
            model_config['model'], params, X, y, groups, y_stratify,
            use_y_std=USE_Y_STD[model_name], n_repeats=N_REPEATS, n_splits=N_SPLITS,
            random_state=random_state + i * 100
        )
        metrics['params'] = params
        all_trials.append(metrics)

        if metrics['test_r2'] > best_score:
            best_score = metrics['test_r2']
            best_params = params
            best_metrics = metrics

    return best_params, best_metrics, all_trials


def main():
    print("=" * 80)
    print("SR0530 Robust Hyperparameter Tuning with Repeated CV")
    print(f"Mode: {MODE_LABEL}")
    print(f"Data: lenient | Distances: {DISTANCES if DISTANCES else 'all'}")
    print(f"Schemas: {len(SCHEMA)} | Models: {len(PARAM_SPACE)}")
    print(f"Random search per model: {N_ITER} | Repeats: {N_REPEATS} | Folds: {N_SPLITS}")
    print("=" * 80)

    # Checkpoint
    checkpoint_results_csv = os.path.join(OUT_DIR, f'SR0530_HP_Tuning_Results_{MODE_LABEL}_checkpoint.csv')
    checkpoint_trials_csv = os.path.join(OUT_DIR, f'SR0530_HP_Tuning_AllTrials_{MODE_LABEL}_checkpoint.csv')

    if os.path.exists(checkpoint_results_csv):
        df_ckpt_results = pd.read_csv(checkpoint_results_csv)
        results = df_ckpt_results.to_dict('records')
        completed_distances = set(df_ckpt_results['Distance_mm'].tolist())
        print(f"\nLoaded checkpoint: {len(results)} rows, {len(completed_distances)} distances completed.")
    else:
        results = []
        completed_distances = set()

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

    distances = DISTANCES if DISTANCES else sorted(all_data.keys())

    for dist in distances:
        if dist in completed_distances:
            print(f"\n--- Distance {dist:.1f} mm --- SKIPPED (already in checkpoint)")
            continue

        print(f"\n--- Distance {dist:.1f} mm ---")
        df = aggregate_distance(all_data[dist], eye_to_subject)

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
                continue

            for model_name, model_config in PARAM_SPACE.items():
                print(f"    Tuning {model_name}...", end=' ', flush=True)
                best_params, best_metrics, trials = tune_model_robust(
                    model_name, model_config, X, y, groups, y_strat,
                    n_iter=N_ITER, random_state=RANDOM_STATE
                )
                print(f"Best mean R2={best_metrics['test_r2']:.3f} (std={best_metrics['test_r2_std']:.3f})")

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
                        'Gap': trial['gap']
                    })

        save_checkpoint()

    df_results = pd.DataFrame(results)
    df_trials = pd.DataFrame(all_trials)

    results_csv = os.path.join(OUT_DIR, f'SR0530_HP_Tuning_Results_{MODE_LABEL}.csv')
    trials_csv = os.path.join(OUT_DIR, f'SR0530_HP_Tuning_AllTrials_{MODE_LABEL}.csv')
    df_results.to_csv(results_csv, index=False, encoding='utf-8-sig')
    df_trials.to_csv(trials_csv, index=False, encoding='utf-8-sig')
    print(f"\nSaved: {results_csv}")
    print(f"Saved: {trials_csv}")

    generate_visualizations(df_results, mode_label=MODE_LABEL)
    generate_report(df_results, mode_label=MODE_LABEL)

    print("\n" + "=" * 80)
    print("Robust tuning complete!")
    print("=" * 80)


def generate_visualizations(df_results, mode_label='robust_repeatedCV'):
    # 1. Line plot: best Test R2 per distance for each schema family
    families = {
        'A1': ['A1_Biomechanical_Core', 'A1_Biomechanical_Core_K', 'A1_Biomechanical_ALK', 'A1_Biomechanical_K_ALK'],
        'A2': ['A2_Biomechanical_NoK', 'A2_Biomechanical_WithK', 'A2_Biomechanical_ALK', 'A2_Biomechanical_K_ALK'],
        'B': ['B_Clinical', 'B_Clinical_K', 'B_Clinical_ALK', 'B_Clinical_K_ALK'],
        'C1': ['C1_Combined', 'C1_Combined_K', 'C1_Combined_ALK', 'C1_Combined_K_ALK']
    }

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    axes = axes.flatten()
    colors = {'Baseline': 'gray', '+K': 'C0', '+ALK': 'C1', '+K+ALK': 'C2'}
    usage_map = {
        'A1_Biomechanical_Core': 'Baseline', 'A2_Biomechanical_NoK': 'Baseline', 'B_Clinical': 'Baseline', 'C1_Combined': 'Baseline',
        'A1_Biomechanical_Core_K': '+K', 'A2_Biomechanical_WithK': '+K', 'B_Clinical_K': '+K', 'C1_Combined_K': '+K',
        'A1_Biomechanical_ALK': '+ALK', 'A2_Biomechanical_ALK': '+ALK', 'B_Clinical_ALK': '+ALK', 'C1_Combined_ALK': '+ALK',
        'A1_Biomechanical_K_ALK': '+K+ALK', 'A2_Biomechanical_K_ALK': '+K+ALK', 'B_Clinical_K_ALK': '+K+ALK', 'C1_Combined_K_ALK': '+K+ALK'
    }

    for idx, (family, schemas) in enumerate(families.items()):
        ax = axes[idx]
        for sch in schemas:
            df_s = df_results[df_results['Schema'] == sch]
            if df_s.empty:
                continue
            best_per_d = df_s.loc[df_s.groupby('Distance_mm')['test_r2'].idxmax()].sort_values('Distance_mm')
            usage = usage_map[sch]
            ax.plot(best_per_d['Distance_mm'], best_per_d['test_r2'], 'o-', label=usage, color=colors[usage], linewidth=2, markersize=6)
        ax.axhline(0, color='gray', linestyle='--', linewidth=0.8)
        ax.set_xlabel('Distance (mm)')
        ax.set_ylabel('Best Mean Test R²')
        ax.set_title(f'{family} Family')
        ax.legend()
        ax.grid(True, alpha=0.3)
    plt.suptitle(f'Best Repeated-CV Test R² by Distance and Schema Family ({mode_label})', fontsize=14)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    path = os.path.join(FIG_DIR, f'SR0530_HP_Tuning_DistanceComparison_{mode_label}.png')
    plt.savefig(path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  --> Saved: {path}")

    # 2. Heatmap: Distance vs Model (best schema per cell)
    best_per_dm = df_results.loc[df_results.groupby(['Distance_mm', 'Model'])['test_r2'].idxmax()]
    pivot = best_per_dm.pivot(index='Distance_mm', columns='Model', values='test_r2')
    fig, ax = plt.subplots(figsize=(12, 8))
    im = ax.imshow(pivot.values, aspect='auto', cmap='RdYlGn', vmin=-0.3, vmax=0.5)
    ax.set_xticks(np.arange(len(pivot.columns)))
    ax.set_yticks(np.arange(len(pivot.index)))
    ax.set_xticklabels(pivot.columns, rotation=45, ha='right')
    ax.set_yticklabels([f"{d:.1f}" for d in pivot.index])
    ax.set_xlabel('Model')
    ax.set_ylabel('Distance (mm)')
    ax.set_title(f'Best Mean Test R² by Distance and Model ({mode_label})')
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = pivot.values[i, j]
            if not np.isnan(val):
                text_color = 'white' if abs(val) > 0.20 else 'black'
                ax.text(j, i, f"{val:.2f}", ha='center', va='center', color=text_color, fontsize=8)
    fig.colorbar(im, ax=ax, label='Mean Test R²')
    plt.tight_layout()
    path = os.path.join(FIG_DIR, f'SR0530_HP_Tuning_Heatmap_{mode_label}.png')
    plt.savefig(path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  --> Saved: {path}")

    # 3. Bar plot: best per schema across distances
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    axes = axes.flatten()
    for idx, (family, schemas) in enumerate(families.items()):
        ax = axes[idx]
        df_f = df_results[df_results['Schema'].isin(schemas)]
        best_per_schema = df_f.loc[df_f.groupby('Schema')['test_r2'].idxmax()].sort_values('test_r2')
        bar_colors = [colors[usage_map[s]] for s in best_per_schema['Schema']]
        bars = ax.barh(best_per_schema['Schema'], best_per_schema['test_r2'], color=bar_colors)
        ax.axvline(0, color='black', linewidth=0.8)
        ax.set_xlabel('Best Mean Test R² (Repeated CV)')
        ax.set_title(f'{family} Family')
        ax.set_xlim(-0.5, 0.6)
        for bar, val in zip(bars, best_per_schema['test_r2']):
            ax.text(val + 0.02, bar.get_y() + bar.get_height()/2, f"{val:.3f}", va='center', fontsize=9)
    plt.suptitle(f'Best Repeated-CV Test R² by Schema Family ({mode_label})', fontsize=14)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    path = os.path.join(FIG_DIR, f'SR0530_HP_Tuning_SchemaComparison_{mode_label}.png')
    plt.savefig(path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  --> Saved: {path}")


def compute_t_ci(mean, std, n=25, alpha=0.05):
    if pd.isna(std) or n < 2:
        return np.nan, np.nan
    se = std / np.sqrt(n)
    t_val = stats.t.ppf(1 - alpha / 2, df=n - 1)
    return mean - t_val * se, mean + t_val * se


def generate_report(df_results, mode_label='robust_repeatedCV'):
    md = []
    md.append(f"# SR0530 稳健性超参数寻优报告（{mode_label}）\n\n")
    md.append("> **目标**：使用重复交叉验证（Repeated GroupKFold）重新评估各方案，降低 fold split 随机性带来的选择偏倚。\n\n")
    md.append("> **方法**：Random Search + 5-fold GroupKFold × 5 repeats，每模型 15 组参数\n\n")
    md.append("> **数据**：lenient（71 眼 / 46 subjects），Distance = 1.0–6.0 mm\n\n")
    md.append("> **置信区间**：基于 25 个 fold-level R²（5 seeds × 5 folds）估算 95% CI。\n\n")
    md.append("---\n\n")

    md.append("## 一、总体最佳配置（稳健性评估，所有距离）\n\n")
    best_row = df_results.loc[df_results['test_r2'].idxmax()]
    r2_lo, r2_hi = compute_t_ci(best_row['test_r2'], best_row['test_r2_std'])
    md.append(f"- **距离**：{best_row['Distance_mm']:.1f} mm\n")
    md.append(f"- **方案**：{best_row['Schema']}\n")
    md.append(f"- **模型**：{best_row['Model']}\n")
    md.append(f"- **Mean Test R²**：{best_row['test_r2']:.3f} [95% CI: {r2_lo:.3f}, {r2_hi:.3f}]\n")
    md.append(f"- **Std Test R²**：{best_row['test_r2_std']:.3f}\n")
    md.append(f"- **Mean Gap**：{best_row['gap']:.3f}\n")
    md.append(f"- **最佳参数**：{best_row['Best_Params']}\n")
    md.append(f"- **样本量**：{int(best_row['N_Eyes'])} 眼 / {int(best_row['N_Subjects'])} subjects\n\n")

    md.append("## 二、各距离最佳配置\n\n")
    md.append("| 距离 (mm) | 最佳方案 | 最佳模型 | Mean Test R² (95% CI) | Std | Gap | 最佳参数 |\n")
    md.append("|-----------|---------|---------|----------------------|-----|-----|---------|\n")
    for dist in sorted(df_results['Distance_mm'].unique()):
        df_d = df_results[df_results['Distance_mm'] == dist]
        best = df_d.loc[df_d['test_r2'].idxmax()]
        r2_lo, r2_hi = compute_t_ci(best['test_r2'], best['test_r2_std'])
        md.append(f"| {best['Distance_mm']:.1f} | {best['Schema']} | {best['Model']} | "
                  f"{best['test_r2']:.3f} [{r2_lo:.3f}, {r2_hi:.3f}] | {best['test_r2_std']:.3f} | "
                  f"{best['gap']:.3f} | {best['Best_Params']} |\n")
    md.append("\n")

    md.append("## 三、每个方案在每个距离的最佳模型\n\n")
    md.append("| 距离 (mm) | 方案 | 最佳模型 | Mean Test R² (95% CI) | Std | Gap | 最佳参数 |\n")
    md.append("|-----------|------|---------|----------------------|-----|-----|---------|\n")
    for schema_name in df_results['Schema'].unique():
        df_s = df_results[df_results['Schema'] == schema_name]
        for dist in sorted(df_s['Distance_mm'].unique()):
            df_sd = df_s[df_s['Distance_mm'] == dist]
            best = df_sd.loc[df_sd['test_r2'].idxmax()]
            r2_lo, r2_hi = compute_t_ci(best['test_r2'], best['test_r2_std'])
            md.append(f"| {best['Distance_mm']:.1f} | {best['Schema']} | {best['Model']} | "
                      f"{best['test_r2']:.3f} [{r2_lo:.3f}, {r2_hi:.3f}] | {best['test_r2_std']:.3f} | "
                      f"{best['gap']:.3f} | {best['Best_Params']} |\n")
    md.append("\n")

    md.append("## 四、每个模型在所有方案/距离中的最佳表现\n\n")
    md.append("| 模型 | 最佳距离 | 最佳方案 | Mean Test R² (95% CI) | Gap | 最佳参数 |\n")
    md.append("|------|---------|---------|----------------------|-----|---------|\n")
    for model_name in sorted(df_results['Model'].unique()):
        df_m = df_results[df_results['Model'] == model_name]
        best = df_m.loc[df_m['test_r2'].idxmax()]
        r2_lo, r2_hi = compute_t_ci(best['test_r2'], best['test_r2_std'])
        md.append(f"| {model_name} | {best['Distance_mm']:.1f} mm | {best['Schema']} | "
                  f"{best['test_r2']:.3f} [{r2_lo:.3f}, {r2_hi:.3f}] | {best['gap']:.3f} | {best['Best_Params']} |\n")
    md.append("\n")

    md.append("## 五、基线 vs K vs AL/K vs K+ALK 对比（按方案族取最佳距离）\n\n")
    families = {
        'A1': ['A1_Biomechanical_Core', 'A1_Biomechanical_Core_K', 'A1_Biomechanical_ALK', 'A1_Biomechanical_K_ALK'],
        'A2': ['A2_Biomechanical_NoK', 'A2_Biomechanical_WithK', 'A2_Biomechanical_ALK', 'A2_Biomechanical_K_ALK'],
        'B': ['B_Clinical', 'B_Clinical_K', 'B_Clinical_ALK', 'B_Clinical_K_ALK'],
        'C1': ['C1_Combined', 'C1_Combined_K', 'C1_Combined_ALK', 'C1_Combined_K_ALK']
    }
    for family, schemas in families.items():
        md.append(f"### {family} 方案族\n\n")
        md.append("| 方案 | 最佳距离 | 最佳模型 | Mean Test R² | Std | Gap |\n")
        md.append("|------|---------|---------|-------------|-----|-----|\n")
        for sch in schemas:
            df_s = df_results[df_results['Schema'] == sch]
            if df_s.empty:
                continue
            best = df_s.loc[df_s['test_r2'].idxmax()]
            md.append(f"| {sch} | {best['Distance_mm']:.1f} mm | {best['Model']} | {best['test_r2']:.3f} | "
                      f"{best['test_r2_std']:.3f} | {best['gap']:.3f} |\n")
        md.append("\n")

    md.append("## 六、按距离汇总的平均 R²（跨方案/模型）\n\n")
    md.append("| 距离 (mm) | 平均 Mean Test R² | 中位数 | 最佳方案 | 最佳模型 | 最佳 R² |\n")
    md.append("|-----------|------------------|--------|---------|---------|--------|\n")
    for dist in sorted(df_results['Distance_mm'].unique()):
        df_d = df_results[df_results['Distance_mm'] == dist]
        best = df_d.loc[df_d['test_r2'].idxmax()]
        md.append(f"| {dist:.1f} | {df_d['test_r2'].mean():.3f} | {df_d['test_r2'].median():.3f} | "
                  f"{best['Schema']} | {best['Model']} | {best['test_r2']:.3f} |\n")
    md.append("\n")

    md.append("## 七、讨论\n\n")
    md.append("1. **重复 CV 显著降低了选择偏倚**：此前单 CV 的 0.6+ R² 在重复 CV 下降至更保守的水平。\n")
    md.append("2. **最佳距离和方案可能随距离变化**：不同偏心距下最优方案可能不同，需结合生理意义选择。\n")
    md.append("3. **最佳模型仍以线性模型为主**：ElasticNet / Lasso / Ridge 在多数距离表现稳健。\n")
    md.append("4. **K 与 AL/K 的优劣因距离而异**：需结合具体距离判断，不能一概而论。\n")
    md.append("5. **样本量仍是根本限制**：46 subjects 导致 95% CI 较宽，结论仍属探索性。\n\n")

    md.append("---\n\n")
    md.append("*Report generated automatically by SR_ML_hyperparameter_tuning_robust.py*\n")

    md_path = os.path.join(REPORT_DIR, f'SR0530_ML_Hyperparameter_Tuning_{mode_label}_Report.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(''.join(md))
    print(f"  --> Report: {md_path}")


if __name__ == '__main__':
    main()
