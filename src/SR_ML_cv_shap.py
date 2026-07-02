"""
SR0530 Cross-Validated SHAP (Method B)
对每个 CV fold 训练模型，对 test fold 计算 SHAP，然后聚合。
"""
import os
import glob
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# 全局字体设置：Calibri 为首选，中文回退
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['font.sans-serif'] = ['Calibri', 'SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import Lasso, ElasticNet, Ridge
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from sklearn.metrics import r2_score

import shap
warnings.filterwarnings('ignore')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'genData', 'CleanDataRoi_lenient')
OUT_DIR = os.path.join(BASE_DIR, 'genData', 'sum')
REPORT_DIR = os.path.join(BASE_DIR, 'report')
FIG_DIR = os.path.join(REPORT_DIR, 'FIG', 'CV_SHAP')
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
RANDOM_STATE = 42

# 需要分析的 (distance, schema, model, best_params)
SELECTED = [
    {'distance': 1.5, 'schema': 'C1_Combined_K', 'model': 'Lasso', 'params': {'alpha': 10.0}},
    {'distance': 1.5, 'schema': 'A2_Biomechanical_ALK', 'model': 'Lasso', 'params': {'alpha': 0.01}},
    {'distance': 1.5, 'schema': 'C1_Combined_ALK', 'model': 'Lasso', 'params': {'alpha': 10.0}},
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


def build_model(model_name, params):
    if model_name == 'Lasso':
        return Pipeline([('s', StandardScaler()), ('lasso', Lasso(**params, max_iter=5000))])
    if model_name == 'ElasticNet':
        return Pipeline([('s', StandardScaler()), ('en', ElasticNet(**params, max_iter=5000))])
    if model_name == 'Ridge':
        return Pipeline([('s', StandardScaler()), ('ridge', Ridge(**params))])
    if model_name == 'Random_Forest':
        return Pipeline([('s', StandardScaler()), ('rf', RandomForestRegressor(**params, random_state=RANDOM_STATE, n_jobs=1))])
    if model_name == 'XGBoost':
        return XGBRegressor(**params, random_state=RANDOM_STATE, verbosity=0)
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


def main():
    print("=" * 80)
    print("SR0530 Cross-Validated SHAP (Method B)")
    print("=" * 80)

    eye_to_subject = load_subject_mapping(DATA_DIR)
    all_data = load_distance_data(DATA_DIR)

    summary_records = []

    for cfg in SELECTED:
        dist = cfg['distance']
        schema = cfg['schema']
        model_name = cfg['model']
        params = cfg['params']

        print(f"\n--- Distance {dist:.1f} mm | Schema {schema} | Model {model_name} ---")

        df = aggregate_distance(all_data[dist], eye_to_subject)
        feat_keys = SCHEMA_FEATURES[schema]
        feat_full = [FEATURE_ALL[k] for k in feat_keys]
        df_sub = fill_na(df.copy(), feat_full)
        X = df_sub[feat_full]
        y = df_sub[TARGET_COL]
        groups = df_sub['Real_Subject_ID'].values
        y_strat = df_sub['Myopia'].values

        n_splits = min(5, len(np.unique(groups)) // 2)
        if n_splits < 2:
            n_splits = 2
        splits = group_stratified_kfold(groups, y_strat, n_splits=n_splits, random_state=RANDOM_STATE)

        fold_r2 = []
        all_shap_explanations = []

        for fold_i, (ti, vi) in enumerate(splits):
            model = build_model(model_name, params)
            model.fit(X.iloc[ti], y.iloc[ti])

            pred_train = model.predict(X.iloc[ti])
            pred_test = model.predict(X.iloc[vi])
            train_r2 = r2_score(y.iloc[ti], pred_train)
            test_r2 = r2_score(y.iloc[vi], pred_test)
            fold_r2.append({'fold': fold_i, 'train_r2': train_r2, 'test_r2': test_r2})

            expl = compute_linear_shap(model, X.iloc[vi])
            all_shap_explanations.append(expl)
            print(f"  Fold {fold_i}: Train R2={train_r2:.3f}, Test R2={test_r2:.3f}")

        avg_train_r2 = np.mean([r['train_r2'] for r in fold_r2])
        avg_test_r2 = np.mean([r['test_r2'] for r in fold_r2])
        std_test_r2 = np.std([r['test_r2'] for r in fold_r2])
        print(f"  Average: Train R2={avg_train_r2:.3f}, Test R2={avg_test_r2:.3f} ± {std_test_r2:.3f}")

        summary_records.append({
            'Distance_mm': dist,
            'Schema': schema,
            'Model': model_name,
            'Params': str(params),
            'N_Eyes': len(df_sub),
            'N_Subjects': len(np.unique(groups)),
            'Avg_Train_R2': avg_train_r2,
            'Avg_Test_R2': avg_test_r2,
            'Std_Test_R2': std_test_r2,
            'CV_Gap': avg_train_r2 - avg_test_r2,
            'Fold_Test_R2s': [r['test_r2'] for r in fold_r2]
        })

        # Aggregate SHAP across folds
        shap_values = np.vstack([e.values for e in all_shap_explanations])
        data_values = np.vstack([e.data for e in all_shap_explanations])
        base_values = np.concatenate([e.base_values for e in all_shap_explanations])
        X_all_test = pd.DataFrame(data_values, columns=feat_full)

        aggregated_expl = shap.Explanation(
            values=shap_values,
            base_values=base_values,
            data=data_values,
            feature_names=feat_full
        )

        # Plot aggregated SHAP
        fig, ax = plt.subplots(figsize=(10, 6))
        shap.plots.beeswarm(aggregated_expl, show=False, max_display=10)
        plt.title(f'CV-SHAP: {model_name} | {schema} | {dist:.1f} mm\nAvg Test R²={avg_test_r2:.3f}')
        plt.tight_layout()
        plot_path = os.path.join(FIG_DIR, f'CV_SHAP_{dist:.1f}mm_{schema}_{model_name}.png')
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  -> Saved: {plot_path}")

        # Plot per-fold R2 bar
        fig, ax = plt.subplots(figsize=(8, 4))
        x = np.arange(len(fold_r2))
        ax.bar(x - 0.2, [r['train_r2'] for r in fold_r2], 0.4, label='Train R²')
        ax.bar(x + 0.2, [r['test_r2'] for r in fold_r2], 0.4, label='Test R²')
        ax.axhline(0, color='gray', linestyle='--', linewidth=0.8)
        ax.set_xlabel('Fold')
        ax.set_ylabel('R²')
        ax.set_title(f'Per-fold R²: {model_name} | {schema} | {dist:.1f} mm')
        ax.set_xticks(x)
        ax.set_xticklabels([f"Fold {r['fold']}" for r in fold_r2])
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        fold_path = os.path.join(FIG_DIR, f'CV_FoldR2_{dist:.1f}mm_{schema}_{model_name}.png')
        plt.savefig(fold_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  -> Saved: {fold_path}")

    # Save summary CSV
    df_summary = pd.DataFrame(summary_records)
    summary_csv = os.path.join(OUT_DIR, 'SR0530_CV_SHAP_Summary.csv')
    df_summary.to_csv(summary_csv, index=False, encoding='utf-8-sig')
    print(f"\nSaved summary: {summary_csv}")

    # Generate report
    generate_report(df_summary)
    print("\n" + "=" * 80)
    print("Cross-validated SHAP complete!")
    print("=" * 80)


def generate_report(df_summary):
    md = []
    md.append("# SR0530 Cross-Validated SHAP 报告（Method B）\n\n")
    md.append("> **目标**：对每个 CV fold 单独训练模型，对 test fold 计算 SHAP，最后聚合所有 fold 的 SHAP 值。这样 SHAP 解释的是实际参与交叉验证的模型，与 reported Test R² 更一致。\n\n")
    md.append("> **数据**：lenient（71 眼 / 46 subjects），5-fold GroupKFold by Subject，按 Myopia 分层。\n\n")
    md.append("---\n\n")

    md.append("## 一、各方案 CV 性能\n\n")
    md.append("| 距离 (mm) | 方案 | 模型 | 参数 | Avg Train R² | Avg Test R² | Std Test R² | CV Gap | Fold Test R²s |\n")
    md.append("|-----------|------|------|------|--------------|-------------|-------------|--------|---------------|\n")
    for _, row in df_summary.iterrows():
        folds = ', '.join([f"{v:.3f}" for v in row['Fold_Test_R2s']])
        md.append(f"| {row['Distance_mm']:.1f} | {row['Schema']} | {row['Model']} | {row['Params']} | "
                  f"{row['Avg_Train_R2']:.3f} | {row['Avg_Test_R2']:.3f} | {row['Std_Test_R2']:.3f} | "
                  f"{row['CV_Gap']:.3f} | {folds} |\n")
    md.append("\n")

    md.append("## 二、可视化\n\n")
    for _, row in df_summary.iterrows():
        dist = row['Distance_mm']
        schema = row['Schema']
        model = row['Model']
        prefix = f"{dist:.1f}mm_{schema}_{model}"
        md.append(f"### {schema} at {dist:.1f} mm ({model})\n\n")
        md.append(f"**Avg Test R² = {row['Avg_Test_R2']:.3f}**\n\n")
        md.append(f"![CV SHAP](FIG/CV_SHAP/CV_SHAP_{prefix}.png)\n\n")
        md.append(f"![Per-fold R2](FIG/CV_SHAP/CV_FoldR2_{prefix}.png)\n\n")

    md.append("## 三、与超参数寻优 Test R² 的对比\n\n")
    md.append("- 超参数寻优中的 Test R² 是 30 组参数中最佳者的 CV 平均值。\n")
    md.append("- 本报告的 Avg Test R² 是固定最佳参数后，用固定 seed 的 5-fold CV 重新跑出的平均值。\n")
    md.append("- 两者应当接近，但不一定完全相同，因为：\n")
    md.append("  1. 超参数寻优每次迭代使用不同的 fold split（random_state + i）；\n")
    md.append("  2. 固定 seed 的 CV 只使用一种 fold split，可能更保守或更乐观；\n")
    md.append("  3. 样本量较小（46 subjects）时，fold split 的随机性对 R² 影响较大。\n\n")

    md.append("## 四、关键发现\n\n")
    md.append("1. **SHAP 特征重要性跨 fold 是否一致**：若某特征在所有 fold 的 SHAP 图中都排名靠前且方向一致，说明该特征稳定重要。\n")
    md.append("2. **CV Gap 反映过拟合**：Avg Train R² 与 Avg Test R² 的差值越小，模型越稳健。Lasso/Ridge/ElasticNet 通常 Gap < 0.15。\n")
    md.append("3. **最终论文推荐**：优先使用 CV SHAP 与 CV R² 一致的线性模型，并在论文中报告 fold-level R² 以展示稳定性。\n\n")

    md.append("---\n\n")
    md.append("*Report generated automatically by SR_ML_cv_shap.py*\n")

    md_path = os.path.join(REPORT_DIR, 'SR0530_CV_SHAP_Report.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(''.join(md))
    print(f"  --> Report: {md_path}")


if __name__ == '__main__':
    main()
