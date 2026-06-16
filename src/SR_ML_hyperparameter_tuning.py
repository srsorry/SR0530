import os
import glob
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
N_ITER = 10

# 象限聚合策略
MIN_QUADRANTS = 1  # 当前运行模式：1 = 放宽为 ≥1 象限平均；4 = 不放宽
MODE_LABEL = 'q1plus' if MIN_QUADRANTS == 1 else 'q4'

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

# 是否需要对 y 做标准化（只对 NN 启用）
USE_Y_STD = {
    'SVM': False, 'Random_Forest': False, 'XGBoost': False,
    'Neural_Network': True, 'Lasso': False, 'ElasticNet': False, 'Ridge': False
}


# ============================================================
# 工具函数
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


def aggregate_distance(dfs, eye_to_subject, min_quadrants=4):
    """
    按 Subject_ID + Eye 聚合象限密度。

    参数:
        min_quadrants: 纳入某只眼所需的最少有效象限数。
                       - 4 = 传统 inner merge，必须 4 个象限完整
                       - 1 = 只要有 ≥1 个象限即可纳入
    """
    feature_cols = list(FEATURE_ALL.values())

    # 1. 合并 4 个象限的密度（outer merge 保留所有可用象限）
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

    # 2. 按最少象限数过滤
    if min_quadrants == 4:
        merged = merged[merged['N_Quadrants'] == 4].copy()
    else:
        merged = merged[merged['N_Quadrants'] >= min_quadrants].copy()

    # 3. 从第一个包含该眼的象限提取固定协变量
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


def sample_params(param_space, rng):
    """从参数空间中随机采样一组参数（兼容元组等复杂类型）"""
    import random
    params = {}
    for k, v in param_space.items():
        if isinstance(v, list):
            # 使用 Python 原生 random.choice，可处理元组、None 等混合类型
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


def tune_model(model_name, model_config, X, y, groups, y_stratify, n_iter=10, random_state=42):
    """对一个模型做随机参数寻优"""
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
    print("SR0530 ML Hyperparameter Tuning")
    print(f"Mode: min_quadrants={MIN_QUADRANTS} ({MODE_LABEL})")
    print("Data groups: strict (69 eyes) vs lenient (71 eyes)")
    print("Distances: 1.0-6.0 mm | Schemas: A1/A2/B/C1 | Models: 7")
    print(f"Random search iterations per model: {N_ITER}")
    print("=" * 80)

    results = []
    all_trials = []

    for data_group, data_dir in DATA_DIRS.items():
        print(f"\n{'='*80}")
        print(f"Processing data group: {data_group.upper()}")
        print(f"{'='*80}")

        eye_to_subject = load_subject_mapping(data_dir)
        all_data = load_distance_data(data_dir)
        distances = sorted(all_data.keys())

        for dist in distances:
            print(f"\n--- Distance {dist:.1f} mm ---")
            df = aggregate_distance(all_data[dist], eye_to_subject, min_quadrants=MIN_QUADRANTS)

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

                    # 保存最终结果
                    results.append({
                        'Data_Group': data_group,
                        'Distance_mm': dist,
                        'Schema': schema_name,
                        'Model': model_name,
                        'N_Eyes': n_eyes,
                        'N_Subjects': n_subjects,
                        'Best_Params': str(best_params),
                        **best_metrics
                    })

                    # 保存所有尝试（用于审计）
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

    # 保存结果
    df_results = pd.DataFrame(results)
    df_trials = pd.DataFrame(all_trials)

    results_csv = os.path.join(OUT_DIR, f'SR0530_HP_Tuning_Results_{MODE_LABEL}.csv')
    trials_csv = os.path.join(OUT_DIR, f'SR0530_HP_Tuning_AllTrials_{MODE_LABEL}.csv')

    df_results.to_csv(results_csv, index=False, encoding='utf-8-sig')
    df_trials.to_csv(trials_csv, index=False, encoding='utf-8-sig')
    print(f"\nSaved: {results_csv}")
    print(f"Saved: {trials_csv}")

    # 生成可视化和报告
    generate_visualizations(df_results, mode_label=MODE_LABEL)
    generate_report(df_results, mode_label=MODE_LABEL)

    print("\n" + "=" * 80)
    print("Hyperparameter tuning complete!")
    print("=" * 80)


# ============================================================
# 可视化
# ============================================================
def generate_visualizations(df_results, mode_label='q4'):
    """生成参数寻优结果可视化"""
    # 1. 每个数据组的 best Test R2 热图（Distance vs Model，取最佳 Schema）
    for data_group in df_results['Data_Group'].unique():
        df_g = df_results[df_results['Data_Group'] == data_group]
        best_per_dm = df_g.loc[df_g.groupby(['Distance_mm', 'Model'])['test_r2'].idxmax()]
        pivot = best_per_dm.pivot(index='Distance_mm', columns='Model', values='test_r2')

        fig, ax = plt.subplots(figsize=(14, 8))
        im = ax.imshow(pivot.values, aspect='auto', cmap='RdYlGn', vmin=-0.5, vmax=0.5)
        ax.set_xticks(np.arange(len(pivot.columns)))
        ax.set_yticks(np.arange(len(pivot.index)))
        ax.set_xticklabels(pivot.columns, rotation=45, ha='right')
        ax.set_yticklabels([f"{d:.1f}" for d in pivot.index])
        ax.set_xlabel('Model')
        ax.set_ylabel('Distance (mm)')
        ax.set_title(f'Best Test R² by Distance and Model ({data_group.upper()} data, {mode_label})')

        # 在每个格子里标注数值
        for i in range(len(pivot.index)):
            for j in range(len(pivot.columns)):
                val = pivot.values[i, j]
                if not np.isnan(val):
                    text_color = 'white' if abs(val) > 0.25 else 'black'
                    ax.text(j, i, f"{val:.2f}", ha='center', va='center', color=text_color, fontsize=8)

        fig.colorbar(im, ax=ax, label='Test R²')
        plt.tight_layout()
        fig_path = os.path.join(OUT_DIR, f'SR0530_HP_Tuning_Heatmap_{data_group}_{mode_label}.png')
        plt.savefig(fig_path, dpi=300, bbox_inches='tight')
        plt.savefig(os.path.join(FIG_DIR, os.path.basename(fig_path)), dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  --> Saved: {fig_path}")

    # 2. strict vs lenient 对比折线图（每个模型，取最佳 Schema）
    fig, axes = plt.subplots(2, 4, figsize=(20, 10))
    axes = axes.flatten()

    models = sorted(df_results['Model'].unique())
    for idx, model_name in enumerate(models):
        ax = axes[idx]
        for data_group in ['strict', 'lenient']:
            df_g = df_results[(df_results['Data_Group'] == data_group) & (df_results['Model'] == model_name)]
            best_per_d = df_g.loc[df_g.groupby('Distance_mm')['test_r2'].idxmax()]
            ax.plot(best_per_d['Distance_mm'], best_per_d['test_r2'], 'o-', label=data_group, linewidth=2, markersize=6)
        ax.axhline(0, color='gray', linestyle='--', linewidth=0.8)
        ax.set_xlabel('Distance (mm)')
        ax.set_ylabel('Best Test R²')
        ax.set_title(model_name)
        ax.legend()
        ax.grid(True, alpha=0.3)

    # 隐藏多余的子图
    for idx in range(len(models), len(axes)):
        axes[idx].axis('off')

    plt.suptitle(f'Strict vs Lenient: Best Test R² by Distance for Each Model ({mode_label})', fontsize=14, fontweight='bold')
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    fig_path = os.path.join(OUT_DIR, f'SR0530_HP_Tuning_Strict_vs_Lenient_{mode_label}.png')
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(FIG_DIR, os.path.basename(fig_path)), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  --> Saved: {fig_path}")

    # 3. 最佳方案对比图
    fig, ax = plt.subplots(figsize=(12, 7))
    for schema_name in df_results['Schema'].unique():
        df_s = df_results[df_results['Schema'] == schema_name]
        best_per_d = df_s.loc[df_s.groupby('Distance_mm')['test_r2'].idxmax()]
        ax.plot(best_per_d['Distance_mm'], best_per_d['test_r2'], 'o-', label=schema_name, linewidth=2, markersize=7)
    ax.axhline(0, color='gray', linestyle='--', linewidth=0.8)
    ax.set_xlabel('Distance (mm)')
    ax.set_ylabel('Best Test R² (across models and data groups)')
    ax.set_title(f'Schema Comparison: Best Test R² by Distance ({mode_label})')
    ax.legend()
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
def generate_report(df_results, mode_label='q4'):
    """生成 Markdown 报告"""
    mode_desc = {
        'q4': '≥4 象限完整（不放宽，inner merge）',
        'q1plus': '≥1 象限可用（放宽，outer merge 取平均）'
    }.get(mode_label, mode_label)

    md = []
    md.append(f"# SR0530 ML 超参数寻优报告（{mode_desc}）\n\n")
    md.append("> **目标**：针对每种 ML 方法，在 strict（69 眼）和 lenient（71 眼）两套数据上做超参数寻优，比较最佳参数与结果。\n\n")
    md.append(f"> **搜索策略**：Random Search + GroupKFold by Subject，每模型 {N_ITER} 组参数\n\n")
    md.append(f"> **象限策略**：{mode_desc}\n\n")
    md.append("> **数据组**：`CleanDataRoi_strict/`（任意 ROI >7000 剔除）和 `CleanDataRoi_lenient/`（距离平均 >7000 剔除）\n\n")

    md.append("---\n\n")

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
    best_row = df_results.loc[df_results['test_r2'].idxmax()]
    md.append(f"- **数据组**：{best_row['Data_Group']}\n")
    md.append(f"- **距离**：{best_row['Distance_mm']:.1f} mm\n")
    md.append(f"- **方案**：{best_row['Schema']}\n")
    md.append(f"- **模型**：{best_row['Model']}\n")
    md.append(f"- **最佳 Test R²**：{best_row['test_r2']:.3f}\n")
    md.append(f"- **最佳参数**：{best_row['Best_Params']}\n")
    md.append(f"- **样本量**：{int(best_row['N_Eyes'])} 眼 / {int(best_row['N_Subjects'])} subjects\n\n")

    # 三、每个数据组的最佳结果
    md.append("## 三、每个数据组的最佳结果（按距离）\n\n")
    for data_group in ['strict', 'lenient']:
        md.append(f"### {data_group.upper()} 数据组\n\n")
        df_g = df_results[df_results['Data_Group'] == data_group]

        # 每个距离的最佳配置
        md.append("| 距离 (mm) | 最佳方案 | 最佳模型 | Test R² | MAPE (%) | RMSE | Gap | 最佳参数 |\n")
        md.append("|-----------|---------|---------|---------|----------|------|-----|---------|\n")

        for dist in sorted(df_g['Distance_mm'].unique()):
            df_d = df_g[df_g['Distance_mm'] == dist]
            best = df_d.loc[df_d['test_r2'].idxmax()]
            md.append(f"| {best['Distance_mm']:.1f} | {best['Schema']} | {best['Model']} | "
                      f"{best['test_r2']:.3f} | {best['test_mape']:.2f} | {best['test_rmse']:.1f} | "
                      f"{best['gap']:.3f} | `{best['Best_Params']}` |\n")

        md.append("\n")

    # 四、每个模型在每个数据组的最佳结果
    md.append("## 四、每个模型在每个数据组的最佳结果\n\n")
    md.append("| 数据组 | 模型 | 最佳距离 | 最佳方案 | Test R² | MAPE (%) | 最佳参数 |\n")
    md.append("|--------|------|---------|---------|---------|----------|---------|\n")
    for data_group in ['strict', 'lenient']:
        df_g = df_results[df_results['Data_Group'] == data_group]
        for model_name in sorted(df_g['Model'].unique()):
            df_m = df_g[df_g['Model'] == model_name]
            best = df_m.loc[df_m['test_r2'].idxmax()]
            md.append(f"| {data_group} | {model_name} | {best['Distance_mm']:.1f} mm | {best['Schema']} | "
                      f"{best['test_r2']:.3f} | {best['test_mape']:.2f} | `{best['Best_Params']}` |\n")
    md.append("\n")

    # 五、每个方案的最佳结果
    md.append("## 五、每个特征方案的最佳结果\n\n")
    md.append("| 方案 | 数据组 | 最佳距离 | 最佳模型 | Test R² |\n")
    md.append("|------|--------|---------|---------|----------|\n")
    for schema_name in df_results['Schema'].unique():
        df_s = df_results[df_results['Schema'] == schema_name]
        best = df_s.loc[df_s['test_r2'].idxmax()]
        md.append(f"| {schema_name} | {best['Data_Group']} | {best['Distance_mm']:.1f} mm | {best['Model']} | {best['test_r2']:.3f} |\n")
    md.append("\n")

    # 六、详细结果表
    md.append("## 六、全部详细结果\n\n")
    md.append("| 数据组 | 距离 | 方案 | 模型 | N_Eyes | N_Subj | Train R² | Test R² | Corr | MAPE | RMSE | Gap | 最佳参数 |\n")
    md.append("|--------|------|------|------|--------|--------|----------|---------|------|------|------|-----|---------|\n")
    for _, row in df_results.iterrows():
        md.append(f"| {row['Data_Group']} | {row['Distance_mm']:.1f} | {row['Schema']} | {row['Model']} | "
                  f"{int(row['N_Eyes'])} | {int(row['N_Subjects'])} | {row['train_r2']:.3f} | "
                  f"{row['test_r2']:.3f} | {row['test_corr']:.3f} | {row['test_mape']:.2f} | "
                  f"{row['test_rmse']:.1f} | {row['gap']:.3f} | `{row['Best_Params']}` |\n")

    # 七、可视化
    md.append("\n## 七、可视化\n\n")
    md.append(f"### Strict 数据组：Distance × Model 热图 ({mode_label})\n\n")
    md.append(f"![Strict Heatmap](FIG/SR0530_HP_Tuning_Heatmap_strict_{mode_label}.png)\n\n")
    md.append(f"### Lenient 数据组：Distance × Model 热图 ({mode_label})\n\n")
    md.append(f"![Lenient Heatmap](FIG/SR0530_HP_Tuning_Heatmap_lenient_{mode_label}.png)\n\n")
    md.append(f"### Strict vs Lenient 各模型对比 ({mode_label})\n\n")
    md.append(f"![Strict vs Lenient](FIG/SR0530_HP_Tuning_Strict_vs_Lenient_{mode_label}.png)\n\n")
    md.append(f"### 方案对比 ({mode_label})\n\n")
    md.append(f"![Schema Comparison](FIG/SR0530_HP_Tuning_SchemaComparison_{mode_label}.png)\n\n")

    # 八、讨论
    md.append("## 八、讨论\n\n")
    md.append("1. **数据组差异**：strict 模式移除了局部 ROI 异常值，数据更干净；lenient 模式保留了更多样本但可能混入异常。\n")
    md.append("2. **最佳参数稳定性**：如果某模型在 strict 和 lenient 下的最佳参数差异很大，提示该模型对异常值敏感。\n")
    md.append("3. **方案选择**：各方案表现因距离和数据组而异，最佳方案需结合 Test R²、Gap 和参数稳定性综合判断，具体见上述结果表。\n")
    md.append("4. **参数寻优局限**：Random Search 的 n_iter=10 是计算与精度的折中，关键模型可进一步增加迭代次数。\n\n")

    md.append("---\n\n")
    md.append("*Report generated automatically by SR_ML_hyperparameter_tuning.py*\n")

    md_path = os.path.join(REPORT_DIR, f'SR0530_ML_Hyperparameter_Tuning_{mode_label}_Report.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(''.join(md))
    print(f"  --> Report: {md_path}")


if __name__ == '__main__':
    main()
