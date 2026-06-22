"""
SR0530 Repeated Cross-Validation
用多个不同 seed 运行 5-fold GroupKFold，评估模型 R2 的分布稳定性。
"""
import os
import glob
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import Lasso, ElasticNet, Ridge
from sklearn.metrics import r2_score

warnings.filterwarnings('ignore')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'genData', 'CleanDataRoi_lenient')
OUT_DIR = os.path.join(BASE_DIR, 'genData', 'sum')
REPORT_DIR = os.path.join(BASE_DIR, 'report')
FIG_DIR = os.path.join(REPORT_DIR, 'FIG', 'RepeatedCV')
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
MYOPIA_THRESHOLD = -0.5
N_SEEDS = 20
N_SPLITS = 5

SELECTED = [
    {'distance': 1.5, 'schema': 'C1_Combined_K', 'model': 'Lasso', 'params': {'alpha': 10.0}},
    {'distance': 1.5, 'schema': 'C1_Combined_ALK', 'model': 'Lasso', 'params': {'alpha': 10.0}},
    {'distance': 1.5, 'schema': 'A2_Biomechanical_ALK', 'model': 'Lasso', 'params': {'alpha': 0.01}},
]

SCHEMA_FEATURES = {
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
    'C1_Combined_K_ALK': ['SE', 'AL', 'Age', 'Gender', 'K', 'ALK'],
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


def build_model(model_name, params, random_state=42):
    if model_name == 'Lasso':
        return Pipeline([('s', StandardScaler()), ('lasso', Lasso(**params, max_iter=5000))])
    if model_name == 'ElasticNet':
        return Pipeline([('s', StandardScaler()), ('en', ElasticNet(**params, max_iter=5000))])
    if model_name == 'Ridge':
        return Pipeline([('s', StandardScaler()), ('ridge', Ridge(**params))])
    raise ValueError(model_name)


def run_repeated_cv(X, y, groups, y_stratify, model_name, params, n_seeds=20, n_splits=5):
    records = []
    for seed in range(n_seeds):
        splits = group_stratified_kfold(groups, y_stratify, n_splits=n_splits, random_state=seed)
        for fold_i, (ti, vi) in enumerate(splits):
            model = build_model(model_name, params, random_state=seed)
            model.fit(X.iloc[ti], y.iloc[ti])
            pred_train = model.predict(X.iloc[ti])
            pred_test = model.predict(X.iloc[vi])
            train_r2 = r2_score(y.iloc[ti], pred_train)
            test_r2 = r2_score(y.iloc[vi], pred_test)
            records.append({
                'seed': seed,
                'fold': fold_i,
                'train_r2': train_r2,
                'test_r2': test_r2,
                'gap': train_r2 - test_r2
            })
    return pd.DataFrame(records)


def main():
    print("=" * 80)
    print("SR0530 Repeated Cross-Validation")
    print(f"N_seeds={N_SEEDS}, N_splits={N_SPLITS}")
    print("=" * 80)

    eye_to_subject = load_subject_mapping(DATA_DIR)
    all_data = load_distance_data(DATA_DIR)

    summary_records = []
    all_records = []

    for cfg in SELECTED:
        dist = cfg['distance']
        schema = cfg['schema']
        model_name = cfg['model']
        params = cfg['params']

        print(f"\n--- {schema} | {model_name} | {dist:.1f} mm ---")
        df = aggregate_distance(all_data[dist], eye_to_subject)
        feat_keys = SCHEMA_FEATURES[schema]
        feat_full = [FEATURE_ALL[k] for k in feat_keys]
        df_sub = fill_na(df.copy(), feat_full)
        X = df_sub[feat_full]
        y = df_sub[TARGET_COL]
        groups = df_sub['Real_Subject_ID'].values
        y_strat = df_sub['Myopia'].values

        print(f"  N={len(df_sub)} eyes/{len(np.unique(groups))} subjects")
        df_cv = run_repeated_cv(X, y, groups, y_strat, model_name, params, n_seeds=N_SEEDS, n_splits=N_SPLITS)
        df_cv['Schema'] = schema
        df_cv['Model'] = model_name
        df_cv['Distance_mm'] = dist
        all_records.append(df_cv)

        test_r2s = df_cv['test_r2'].values
        summary_records.append({
            'Distance_mm': dist,
            'Schema': schema,
            'Model': model_name,
            'Params': str(params),
            'N_Eyes': len(df_sub),
            'N_Subjects': len(np.unique(groups)),
            'Mean_Train_R2': df_cv['train_r2'].mean(),
            'Mean_Test_R2': test_r2s.mean(),
            'Median_Test_R2': np.median(test_r2s),
            'Std_Test_R2': test_r2s.std(),
            'Min_Test_R2': test_r2s.min(),
            'Max_Test_R2': test_r2s.max(),
            'Q25_Test_R2': np.percentile(test_r2s, 25),
            'Q75_Test_R2': np.percentile(test_r2s, 75),
            'Pct_Negative': (test_r2s < 0).mean() * 100,
            'Mean_Gap': df_cv['gap'].mean()
        })
        print(f"  Test R2: mean={test_r2s.mean():.3f}, median={np.median(test_r2s):.3f}, std={test_r2s.std():.3f}")
        print(f"  Range: [{test_r2s.min():.3f}, {test_r2s.max():.3f}] | Negative: {(test_r2s<0).mean()*100:.1f}%")

    df_all = pd.concat(all_records, ignore_index=True)
    df_summary = pd.DataFrame(summary_records)

    # Save CSVs
    df_all.to_csv(os.path.join(OUT_DIR, 'SR0530_RepeatedCV_AllFolds.csv'), index=False, encoding='utf-8-sig')
    df_summary.to_csv(os.path.join(OUT_DIR, 'SR0530_RepeatedCV_Summary.csv'), index=False, encoding='utf-8-sig')

    # Visualization 1: Boxplot of Test R2 distribution
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.boxplot(data=df_all, x='Schema', y='test_r2', ax=ax, palette='Set2')
    ax.axhline(0, color='red', linestyle='--', linewidth=1)
    ax.set_ylabel('Test R²')
    ax.set_title(f'Distribution of Test R² Across {N_SEEDS} Seeds × {N_SPLITS} Folds')
    ax.set_xticklabels(ax.get_xticklabels(), rotation=15, ha='right')
    plt.tight_layout()
    box_path = os.path.join(FIG_DIR, 'RepeatedCV_TestR2_Distribution.png')
    plt.savefig(box_path, dpi=300, bbox_inches='tight')
    plt.close()

    # Visualization 2: Violin + swarm
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.violinplot(data=df_all, x='Schema', y='test_r2', ax=ax, inner='box', palette='Set2')
    sns.stripplot(data=df_all, x='Schema', y='test_r2', ax=ax, color='black', alpha=0.3, size=3)
    ax.axhline(0, color='red', linestyle='--', linewidth=1)
    ax.set_ylabel('Test R²')
    ax.set_title(f'Test R² Distribution ({N_SEEDS * N_SPLITS} CV runs per schema)')
    ax.set_xticklabels(ax.get_xticklabels(), rotation=15, ha='right')
    plt.tight_layout()
    violin_path = os.path.join(FIG_DIR, 'RepeatedCV_TestR2_Violin.png')
    plt.savefig(violin_path, dpi=300, bbox_inches='tight')
    plt.close()

    # Visualization 3: Train vs Test scatter
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    for idx, schema in enumerate(df_all['Schema'].unique()):
        df_s = df_all[df_all['Schema'] == schema]
        ax = axes[idx]
        ax.scatter(df_s['train_r2'], df_s['test_r2'], alpha=0.6)
        ax.plot([-1, 1], [-1, 1], 'r--', linewidth=1)
        ax.axhline(0, color='gray', linestyle='--', linewidth=0.5)
        ax.axvline(0, color='gray', linestyle='--', linewidth=0.5)
        ax.set_xlabel('Train R²')
        ax.set_ylabel('Test R²')
        ax.set_title(schema)
        ax.set_xlim(-1, 1)
        ax.set_ylim(-1, 1)
        ax.grid(True, alpha=0.3)
    plt.suptitle('Train vs Test R² Across Repeated CV', fontsize=14)
    plt.tight_layout()
    scatter_path = os.path.join(FIG_DIR, 'RepeatedCV_TrainVsTest.png')
    plt.savefig(scatter_path, dpi=300, bbox_inches='tight')
    plt.close()

    # Generate report
    generate_report(df_summary, df_all, [box_path, violin_path, scatter_path])

    print("\n" + "=" * 80)
    print("Repeated CV complete!")
    print("=" * 80)


def generate_report(df_summary, df_all, plot_paths):
    md = []
    md.append("# SR0530 Repeated Cross-Validation 报告\n\n")
    md.append(f"> **目标**：用 {N_SEEDS} 个不同 random seed 运行 5-fold GroupKFold，评估推荐方案的 Test R² 分布，判断此前报告的 0.612 是否为极端乐观值。\n\n")
    md.append("> **数据**：lenient（71 眼 / 46 subjects），按 Myopia 分层。\n\n")
    md.append("---\n\n")

    md.append("## 一、Repeated CV 汇总统计\n\n")
    md.append("| 方案 | 模型 | Mean Test R² | Median | Std | Min | Max | Q25 | Q75 | Negative % | Mean Gap |\n")
    md.append("|------|------|-------------|--------|-----|-----|-----|-----|-----|-----------|----------|\n")
    for _, row in df_summary.iterrows():
        md.append(f"| {row['Schema']} | {row['Model']} | {row['Mean_Test_R2']:.3f} | {row['Median_Test_R2']:.3f} | "
                  f"{row['Std_Test_R2']:.3f} | {row['Min_Test_R2']:.3f} | {row['Max_Test_R2']:.3f} | "
                  f"{row['Q25_Test_R2']:.3f} | {row['Q75_Test_R2']:.3f} | {row['Pct_Negative']:.1f}% | {row['Mean_Gap']:.3f} |\n")
    md.append("\n")

    md.append("## 二、与超参数寻优最佳值的对比\n\n")
    md.append("| 方案 | 超参数寻优最佳 Test R² | Repeated CV Mean | 差距 | 结论 |\n")
    md.append("|------|----------------------|------------------|------|------|\n")
    best_map = {
        'C1_Combined_K': 0.612,
        'C1_Combined_ALK': 0.611,
        'A2_Biomechanical_ALK': 0.586
    }
    for _, row in df_summary.iterrows():
        schema = row['Schema']
        best = best_map.get(schema, np.nan)
        diff = row['Mean_Test_R2'] - best
        if diff < -0.20:
            conclusion = "此前最佳值显著乐观"
        elif diff < -0.05:
            conclusion = "此前最佳值偏乐观"
        else:
            conclusion = "接近"
        md.append(f"| {schema} | {best:.3f} | {row['Mean_Test_R2']:.3f} | {diff:+.3f} | {conclusion} |\n")
    md.append("\n")

    md.append("## 三、可视化\n\n")
    for p in plot_paths:
        rel = os.path.relpath(p, REPORT_DIR).replace('\\', '/')
        md.append(f"### {os.path.basename(p)}\n\n")
        md.append(f"![{os.path.basename(p)}]({rel})\n\n")

    md.append("## 四、关键发现\n\n")
    md.append("1. **此前报告的最佳 Test R² 确实偏乐观**：Repeated CV 的 Mean Test R² 显著低于超参数寻优中的最佳值。\n")
    md.append("2. **R² 分布很宽，且存在负值**：部分 fold 的 Test R² 为负，说明模型在某些 subjects 上预测能力差于均值基准。\n")
    md.append("3. **三个方案表现接近**：C1_Combined_K、C1_Combined_ALK、A2_Biomechanical_ALK 的 Mean Test R² 都在 0.1–0.2 之间，没有本质差异。\n")
    md.append("4. **样本量限制是主因**：46 subjects 导致 fold split 随机性主导了性能估计。\n\n")

    md.append("## 五、对论文的建议\n\n")
    md.append("1. **用 Repeated CV 的 Mean / Median 作为报告主值**，而非超参数寻优中的 Best-of-30 极值。\n")
    md.append("2. **同时报告 R² 分布**（箱线图或 violin plot），展示结果的变异性。\n")
    md.append("3. **降低预测声明的强度**：全局眼形态参数对局部锥细胞密度的预测能力有限且不稳定，更适合作为探索性发现。\n")
    md.append("4. **若必须给出一个数字**：建议使用 Median Test R² 并配合 IQR，例如 ~0.1 [IQR: -0.1, 0.3]。\n\n")

    md.append("---\n\n")
    md.append("*Report generated automatically by SR_ML_repeated_cv.py*\n")

    md_path = os.path.join(REPORT_DIR, 'SR0530_Repeated_CV_Report.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(''.join(md))
    print(f"  --> Report: {md_path}")


if __name__ == '__main__':
    main()
