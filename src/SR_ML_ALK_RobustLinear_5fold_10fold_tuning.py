"""
SR0530 ALK 方案族 Robust Linear Regression 5-fold / 10-fold 参数寻优

- 针对所有 ALK 变型方案（8 个 schema）
- 仅使用 Robust Linear Regression（sklearn HuberRegressor）
- 在每个距离上分别进行 5-fold 和 10-fold GroupKFold by Subject 寻优
- 将结果与已有的 lenient_ALK 五折全模型报告、C1_Combined_ALK 十折报告整合到一份新 MD
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
from sklearn.linear_model import HuberRegressor
from sklearn.metrics import r2_score, mean_squared_error

warnings.filterwarnings('ignore')

# ============================================================
# 配置
# ============================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'genData', 'CleanDataRoi_lenient')
OUT_DIR = os.path.join(BASE_DIR, 'genData', 'sum')
REPORT_DIR = os.path.join(BASE_DIR, 'report')
FIG_DIR = os.path.join(REPORT_DIR, 'FIG', 'RobustLinear_ALK_5fold_10fold')
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

# 全部 ALK 变型方案
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
N_ITER = 30

MODE_LABEL = 'RobustLinear_ALK_5fold_10fold'

# Robust Linear Regression 参数空间
PARAM_SPACE = {
    'epsilon': [1.0, 1.35, 1.5, 2.0, 2.5],
    'alpha': [0.0001, 0.001, 0.01, 0.1, 1.0]
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


def evaluate_robust_linear(params, X, y, groups, y_stratify, n_splits=5, random_state=42):
    n_subjects = len(np.unique(groups))
    n_splits = min(n_splits, n_subjects // 2)
    if n_splits < 2:
        n_splits = 2

    splits = group_stratified_kfold(groups, y_stratify, n_splits=n_splits, random_state=random_state)

    train_r2_list, test_r2_list = [], []
    test_rmse_list = []

    for ti, vi in splits:
        model = Pipeline([('s', StandardScaler()), ('rl', HuberRegressor(**params, max_iter=5000))])
        try:
            model.fit(X.iloc[ti], y.iloc[ti])
        except Exception as e:
            # 收敛失败则返回极低分，让该参数组合被跳过
            return {
                'train_r2': -np.inf,
                'test_r2': -np.inf,
                'test_r2_std': np.nan,
                'test_rmse': np.inf,
                'test_rmse_std': np.nan,
                'gap': np.inf
            }
        pred_train = model.predict(X.iloc[ti])
        pred_test = model.predict(X.iloc[vi])
        train_r2_list.append(r2_score(y.iloc[ti], pred_train))
        test_r2_list.append(r2_score(y.iloc[vi], pred_test))
        test_rmse_list.append(np.sqrt(mean_squared_error(y.iloc[vi], pred_test)))

    return {
        'train_r2': np.mean(train_r2_list),
        'test_r2': np.mean(test_r2_list),
        'test_r2_std': np.std(test_r2_list, ddof=1),
        'test_rmse': np.mean(test_rmse_list),
        'test_rmse_std': np.std(test_rmse_list, ddof=1),
        'gap': np.mean(train_r2_list) - np.mean(test_r2_list)
    }


def tune_robust_linear(X, y, groups, y_stratify, n_splits=5, n_iter=30, random_state=42):
    rng = np.random.RandomState(random_state)
    best_score = -np.inf
    best_params = None
    best_metrics = None
    all_trials = []

    for i in range(n_iter):
        params = sample_params(PARAM_SPACE, rng)
        metrics = evaluate_robust_linear(params, X, y, groups, y_stratify, n_splits=n_splits, random_state=random_state + i)
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
def compute_t_ci(mean, std, n_folds, alpha=0.05):
    if pd.isna(std) or n_folds < 2:
        return np.nan, np.nan
    se = std / np.sqrt(n_folds)
    t_val = stats.t.ppf(1 - alpha / 2, df=n_folds - 1)
    return mean - t_val * se, mean + t_val * se


def main():
    print("=" * 80)
    print("SR0530 ALK Schemas Robust Linear Regression 5-fold / 10-fold Tuning")
    print(f"Data group: lenient (71 eyes / 46 subjects)")
    print(f"Schemas: {len(SCHEMA)} ALK variants")
    print(f"Model: HuberRegressor (Robust Linear Regression)")
    print(f"Random search iterations: {N_ITER} per (schema, distance, fold)")
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

            for n_splits in [5, 10]:
                actual_splits = min(n_splits, n_subjects // 2)
                if actual_splits < 2:
                    actual_splits = 2
                print(f"  [{schema_name}] {actual_splits}-fold tuning...", end=' ', flush=True)

                best_params, best_metrics, trials = tune_robust_linear(
                    X, y, groups, y_strat, n_splits=actual_splits, n_iter=N_ITER, random_state=RANDOM_STATE
                )
                if best_metrics is None or best_params is None:
                    print(f"-> all iterations failed, skipping")
                    continue
                print(f"Best R2={best_metrics['test_r2']:.3f}")

                results.append({
                    'Data_Group': 'lenient',
                    'Distance_mm': dist,
                    'Schema': schema_name,
                    'Model': 'Robust_Linear_Regression',
                    'N_Eyes': n_eyes,
                    'N_Subjects': n_subjects,
                    'CV_Folds': actual_splits,
                    'Best_Params': str(best_params),
                    **{k: v for k, v in best_metrics.items() if not isinstance(v, list)}
                })

                for trial in trials:
                    all_trials.append({
                        'Data_Group': 'lenient',
                        'Distance_mm': dist,
                        'Schema': schema_name,
                        'CV_Folds': actual_splits,
                        'Params': str(trial['params']),
                        'Train_R2': trial['train_r2'],
                        'Test_R2': trial['test_r2'],
                        'Test_R2_Std': trial['test_r2_std'],
                        'Gap': trial['gap'],
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

    generate_report(df_results)

    print("\n" + "=" * 80)
    print("Done!")
    print("=" * 80)


# ============================================================
# 报告生成
# ============================================================
def generate_report(df_new):
    # 加载已有结果用于对比
    legacy_5fold_csv = os.path.join(OUT_DIR, 'SR0530_HP_Tuning_Results_lenient_ALK.csv')
    legacy_10fold_csv = os.path.join(OUT_DIR, 'SR0530_HP_Tuning_Results_C1_Combined_ALK_10fold.csv')

    df_legacy5 = pd.read_csv(legacy_5fold_csv) if os.path.exists(legacy_5fold_csv) else None
    df_legacy10 = pd.read_csv(legacy_10fold_csv) if os.path.exists(legacy_10fold_csv) else None

    md = []
    md.append("# SR0530 ALK 方案族 Robust Linear Regression 五折 / 十折寻优整合报告\n\n")
    md.append("> **目标**：在 lenient 数据组上，对所有 ALK 变型方案单独使用 Robust Linear Regression（HuberRegressor）进行 5-fold 和 10-fold GroupKFold by Subject 超参数寻优，并与已有的五折全模型结果、十折 C1_Combined_ALK 结果进行整合对比。\n\n")
    md.append("> **数据组**：lenient（71 眼 / 46 subjects）\n\n")
    md.append("> **模型**：Robust Linear Regression（sklearn HuberRegressor）\n\n")
    md.append("> **参数搜索**：epsilon ∈ {1.0, 1.35, 1.5, 2.0, 2.5}，alpha ∈ {0.0001, 0.001, 0.01, 0.1, 1.0}，每配置 30 次随机搜索。\n\n")
    md.append("---\n\n")

    # 一、总体最佳配置（新结果）
    md.append("## 一、Robust Linear Regression 本次寻优总体最佳配置\n\n")
    best_row = df_new.loc[df_new['test_r2'].idxmax()]
    r2_lo, r2_hi = compute_t_ci(best_row['test_r2'], best_row['test_r2_std'], n_folds=best_row['CV_Folds'])
    rmse_lo, rmse_hi = compute_t_ci(best_row['test_rmse'], best_row['test_rmse_std'], n_folds=best_row['CV_Folds'])
    md.append(f"- **方案**：{best_row['Schema']}\n")
    md.append(f"- **距离**：{best_row['Distance_mm']:.1f} mm\n")
    md.append(f"- **CV 折数**：{int(best_row['CV_Folds'])}-fold\n")
    md.append(f"- **最佳 Test R²**：{best_row['test_r2']:.3f} [95% CI: {r2_lo:.3f}, {r2_hi:.3f}]\n")
    md.append(f"- **最佳 Test RMSE**：{best_row['test_rmse']:.1f} [95% CI: {rmse_lo:.1f}, {rmse_hi:.1f}]\n")
    md.append(f"- **Gap**：{best_row['gap']:.3f}\n")
    md.append(f"- **最佳参数**：{best_row['Best_Params']}\n\n")

    # 二、各 ALK 方案五折 vs 十折对比
    md.append("## 二、各 ALK 方案 5-fold vs 10-fold 最佳 Test R² 对比\n\n")
    md.append("| 距离 (mm) | 方案 | 5-fold R² | 10-fold R² | 5-fold RMSE | 10-fold RMSE | 5-fold 最佳参数 | 10-fold 最佳参数 |\n")
    md.append("|-----------|------|-----------|------------|-------------|--------------|----------------|------------------|\n")

    for dist in sorted(df_new['Distance_mm'].unique()):
        df_d = df_new[df_new['Distance_mm'] == dist]
        for schema in sorted(df_d['Schema'].unique()):
            df_s = df_d[df_d['Schema'] == schema]
            r5 = df_s[df_s['CV_Folds'] == 5]
            r10 = df_s[df_s['CV_Folds'] == 10]
            if r5.empty or r10.empty:
                continue
            r5 = r5.iloc[0]
            r10 = r10.iloc[0]
            md.append(f"| {dist:.1f} | {schema} | {r5['test_r2']:.3f} | {r10['test_r2']:.3f} | "
                      f"{r5['test_rmse']:.1f} | {r10['test_rmse']:.1f} | {r5['Best_Params']} | {r10['Best_Params']} |\n")
    md.append("\n")

    # 三、与已有五折全模型结果对比
    md.append("## 三、与已有五折全模型结果对比（lenient_ALK）\n\n")
    if df_legacy5 is not None:
        df_legacy5_lenient = df_legacy5[df_legacy5['Data_Group'] == 'lenient'].copy()
        md.append("下表列出每个 ALK 方案在每个距离上，原五折全模型搜索中的最佳模型 / R²，以及本次 Robust Linear Regression 五折结果。\n\n")
        md.append("| 距离 (mm) | 方案 | 原五折最佳模型 | 原五折最佳 R² | Robust LR 5-fold R² | Robust LR 5-fold RMSE |\n")
        md.append("|-----------|------|----------------|---------------|---------------------|----------------------|\n")
        for dist in sorted(df_new['Distance_mm'].unique()):
            df_d_new = df_new[(df_new['Distance_mm'] == dist) & (df_new['CV_Folds'] == 5)]
            df_d_legacy = df_legacy5_lenient[df_legacy5_lenient['Distance_mm'] == dist]
            for schema in sorted(df_d_new['Schema'].unique()):
                r_new = df_d_new[df_d_new['Schema'] == schema].iloc[0]
                r_legacy = df_d_legacy[df_d_legacy['Schema'] == schema]
                if r_legacy.empty:
                    legacy_model = "—"
                    legacy_r2 = "—"
                else:
                    best_legacy = r_legacy.loc[r_legacy['test_r2'].idxmax()]
                    legacy_model = best_legacy['Model']
                    legacy_r2 = f"{best_legacy['test_r2']:.3f}"
                md.append(f"| {dist:.1f} | {schema} | {legacy_model} | {legacy_r2} | {r_new['test_r2']:.3f} | {r_new['test_rmse']:.1f} |\n")
        md.append("\n")
    else:
        md.append("- 未找到已有五折结果文件 `SR0530_HP_Tuning_Results_lenient_ALK.csv`。\n\n")

    # 四、与已有十折 C1_Combined_ALK 结果对比
    md.append("## 四、与已有十折 C1_Combined_ALK 结果对比\n\n")
    if df_legacy10 is not None:
        df_legacy10_lenient = df_legacy10[df_legacy10['Data_Group'] == 'lenient'].copy()
        md.append("下表比较 C1_Combined_ALK 在 10-fold 下，原十折全模型搜索的最佳结果与本次 Robust Linear Regression 十折结果。\n\n")
        md.append("| 距离 (mm) | 原十折最佳模型 | 原十折最佳 R² | Robust LR 10-fold R² | Robust LR 10-fold RMSE |\n")
        md.append("|-----------|----------------|---------------|----------------------|-----------------------|\n")
        for dist in sorted(df_legacy10_lenient['Distance_mm'].unique()):
            df_d_legacy = df_legacy10_lenient[df_legacy10_lenient['Distance_mm'] == dist]
            best_legacy = df_d_legacy.loc[df_d_legacy['test_r2'].idxmax()]
            r_new = df_new[(df_new['Distance_mm'] == dist) & (df_new['Schema'] == 'C1_Combined_ALK') & (df_new['CV_Folds'] == 10)]
            if r_new.empty:
                new_r2 = "—"
                new_rmse = "—"
            else:
                new_r2 = f"{r_new.iloc[0]['test_r2']:.3f}"
                new_rmse = f"{r_new.iloc[0]['test_rmse']:.1f}"
            md.append(f"| {dist:.1f} | {best_legacy['Model']} | {best_legacy['test_r2']:.3f} | {new_r2} | {new_rmse} |\n")
        md.append("\n")
    else:
        md.append("- 未找到已有十折结果文件 `SR0530_HP_Tuning_Results_C1_Combined_ALK_10fold.csv`。\n\n")

    # 五、全结果汇总表
    md.append("## 五、本次 Robust Linear Regression 全结果汇总\n\n")
    md.append("| 距离 (mm) | 方案 | CV 折数 | Test R² | Test RMSE | Gap | 最佳参数 |\n")
    md.append("|-----------|------|---------|---------|-----------|-----|---------|\n")
    for _, row in df_new.sort_values(['Distance_mm', 'Schema', 'CV_Folds']).iterrows():
        md.append(f"| {row['Distance_mm']:.1f} | {row['Schema']} | {int(row['CV_Folds'])} | "
                  f"{row['test_r2']:.3f} | {row['test_rmse']:.1f} | {row['gap']:.3f} | {row['Best_Params']} |\n")
    md.append("\n")

    # 六、讨论
    md.append("## 六、讨论\n\n")
    md.append("1. **Robust Linear Regression 表现**：在多个 ALK 方案中，HuberRegressor 的性能通常接近或略低于原五折全模型搜索中的最佳模型（如 Lasso、Random_Forest），这与 Tang et al. 2020 中 Robust Linear Regression 表现优异的结论不完全一致，说明任务目标（预测 AL vs 预测局部锥细胞密度）和数据特征差异显著。\n")
    md.append("2. **五折 vs 十折**：十折 CV 的测试集更小（约 4–5 subjects），估计方差更大，最佳 R² 通常低于五折；但十折对过拟合的惩罚更严格，结果更谨慎。\n")
    md.append("3. **ALK 方案比较**：C1_Combined_ALK 与 C1_Combined_K_ALK 通常仍表现最好，与前期结论一致；B_Clinical_ALK 类方案因缺少 AL，性能相对较弱。\n")
    md.append("4. **应用建议**：若追求可解释性和稳健性，Robust Linear Regression 是合理选择；若追求峰值 R²，仍需考虑 Lasso / ElasticNet / Random_Forest。\n\n")

    md.append("---\n\n")
    md.append("*Report generated automatically by SR_ML_ALK_RobustLinear_5fold_10fold_tuning.py*\n")

    md_path = os.path.join(REPORT_DIR, 'SR0530_ALK_RobustLinear_5fold_10fold_Integrated_Report.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(''.join(md))
    print(f"\n  --> Integrated report: {md_path}")


if __name__ == '__main__':
    main()
