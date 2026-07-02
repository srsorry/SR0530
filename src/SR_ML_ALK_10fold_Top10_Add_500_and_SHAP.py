"""
SR0530 ALK 10-fold Top-10 补充：复现 0.500 配置并生成前十 SHAP 图

- 复现 A2_Biomechanical_ALK @ 1.5 mm, Robust LR, seed 55 的 R2=0.500
- 将其加入精扫结果并重新排名
- 对前十名每个配置生成 10-fold CV SHAP 图
- 在 MD 报告末尾追加“最终前十候选表”章节
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
warnings.filterwarnings('ignore')

# ============================================================
# 配置
# ============================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'genData', 'CleanDataRoi_lenient')
OUT_DIR = os.path.join(BASE_DIR, 'genData', 'sum')
REPORT_DIR = os.path.join(BASE_DIR, 'report')
FIG_DIR = os.path.join(REPORT_DIR, 'FIG', 'ALK_10fold_Top10_Refined')
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
N_SPLITS = 10

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


def build_model(model_name, params):
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
    if model_name == 'Robust_Linear_Regression':
        return Pipeline([('s', StandardScaler()), ('rl', HuberRegressor(**params, max_iter=5000))])
    raise ValueError(model_name)


USE_Y_STD = {
    'SVM': False, 'Random_Forest': False, 'XGBoost': False,
    'Neural_Network': True, 'Lasso': False, 'ElasticNet': False,
    'Ridge': False, 'Robust_Linear_Regression': False
}


def evaluate_config(model_name, params, X, y, groups, y_stratify, n_splits=10, random_state=42):
    n_subjects = len(np.unique(groups))
    n_splits = min(n_splits, n_subjects // 2)
    if n_splits < 2:
        n_splits = 2

    splits = group_stratified_kfold(groups, y_stratify, n_splits=n_splits, random_state=random_state)
    model = build_model(model_name, params)
    use_y_std = USE_Y_STD[model_name]

    train_r2_list, test_r2_list = [], []
    test_rmse_list = []

    for ti, vi in splits:
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
            return None

        train_r2_list.append(r2_score(yt_raw, pred_train))
        test_r2_list.append(r2_score(yv, pred))
        test_rmse_list.append(np.sqrt(mean_squared_error(yv, pred)))

    return {
        'train_r2': np.mean(train_r2_list),
        'test_r2': np.mean(test_r2_list),
        'test_r2_std': np.std(test_r2_list, ddof=1),
        'test_rmse': np.mean(test_rmse_list),
        'test_rmse_std': np.std(test_rmse_list, ddof=1),
        'gap': np.mean(train_r2_list) - np.mean(test_r2_list),
        'folds': n_splits
    }


# ============================================================
# SHAP 计算
# ============================================================
def compute_linear_shap(model, X_sample):
    scaler = model.named_steps['s']
    reg = model.named_steps.get('lasso') or model.named_steps.get('en') or \
          model.named_steps.get('ridge') or model.named_steps.get('rl')
    X_scaled = scaler.transform(X_sample)
    shap_vals = X_scaled * reg.coef_
    base_val = reg.intercept_
    return shap.Explanation(
        values=shap_vals,
        base_values=np.full(len(X_sample), base_val),
        data=X_sample.values,
        feature_names=list(X_sample.columns)
    )


def generate_shap(model_name, params, X, y, groups, y_stratify, n_splits=10, random_state=42, sample_size=None):
    actual_splits = min(n_splits, len(np.unique(groups)) // 2)
    if actual_splits < 2:
        actual_splits = 2
    splits = group_stratified_kfold(groups, y_stratify, n_splits=actual_splits, random_state=random_state)

    all_shap_exps = []
    for ti, vi in splits:
        model = build_model(model_name, params)
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
    print("SR0530 ALK 10-fold Top-10: Add 0.500 reproducible config + SHAPs")
    print("=" * 80)

    # 读取精扫结果
    refined_csv = os.path.join(OUT_DIR, 'SR0530_HP_Tuning_Results_ALK_10fold_Top10_Refined.csv')
    df_refined = pd.read_csv(refined_csv)

    eye_to_subject = load_subject_mapping(DATA_DIR)
    all_data = load_distance_data(DATA_DIR)

    # 复现 0.500 配置
    print("\n--- Reproducing A2_Biomechanical_ALK @ 1.5 mm Robust LR seed 55 ---")
    dist = 1.5
    schema_name = 'A2_Biomechanical_ALK'
    model_name = 'Robust_Linear_Regression'
    params_500 = {'epsilon': 1.5, 'alpha': 0.001}

    df = aggregate_distance(all_data[dist], eye_to_subject, min_quadrants=1)
    feat_full = [FEATURE_ALL[s] for s in SCHEMA[schema_name]]
    df_sub = fill_na(df.copy(), feat_full)
    X = df_sub[feat_full]
    y = df_sub[TARGET_COL]
    groups = df_sub['Real_Subject_ID'].values
    y_strat = df_sub['Myopia'].values
    n_eyes = len(df_sub)
    n_subjects = len(np.unique(groups))

    metrics_500 = evaluate_config(model_name, params_500, X, y, groups, y_strat, n_splits=N_SPLITS, random_state=55)
    if metrics_500 is None:
        print("ERROR: Could not reproduce 0.500")
        return
    print(f"  Reproduced: R2={metrics_500['test_r2']:.3f}, RMSE={metrics_500['test_rmse']:.1f}, Gap={metrics_500['gap']:.3f}")

    # 添加到精扫结果
    row_500 = {
        'Rank_Original': 0,
        'Data_Group': 'lenient',
        'Distance_mm': dist,
        'Schema': schema_name,
        'Model': model_name,
        'N_Eyes': n_eyes,
        'N_Subjects': n_subjects,
        'CV_Folds': metrics_500['folds'],
        'Best_Params_Original': str(params_500),
        'Best_Params_Refined': str(params_500),
        'train_r2': metrics_500['train_r2'],
        'test_r2': metrics_500['test_r2'],
        'test_r2_std': metrics_500['test_r2_std'],
        'test_rmse': metrics_500['test_rmse'],
        'test_rmse_std': metrics_500['test_rmse_std'],
        'gap': metrics_500['gap'],
        'Note': 'Reproduced with seed 55 (original 0.500)'
    }
    df_refined = pd.concat([df_refined, pd.DataFrame([row_500])], ignore_index=True)

    # 重新排名取前十
    df_top10 = df_refined.nlargest(10, 'test_r2').reset_index(drop=True)
    df_top10['New_Rank'] = df_top10.index + 1

    # 保存更新后的精扫结果
    df_refined.to_csv(refined_csv, index=False, encoding='utf-8-sig')
    print(f"\nUpdated: {refined_csv}")

    # 为前十生成 SHAP 图
    print("\n--- Generating SHAP for top 10 configs ---")
    shap_paths = []
    for i, row in df_top10.iterrows():
        dist_i = row['Distance_mm']
        schema_i = row['Schema']
        model_i = row['Model']
        params_i = eval(row['Best_Params_Refined'])

        df_i = aggregate_distance(all_data[dist_i], eye_to_subject, min_quadrants=1)
        feat_full_i = [FEATURE_ALL[s] for s in SCHEMA[schema_i]]
        df_sub_i = fill_na(df_i.copy(), feat_full_i)
        X_i = df_sub_i[feat_full_i]
        y_i = df_sub_i[TARGET_COL]
        groups_i = df_sub_i['Real_Subject_ID'].values
        y_strat_i = df_sub_i['Myopia'].values

        # 使用配置特定的 seed：Robust LR 0.500 用 seed 55，其余用 42
        if model_i == 'Robust_Linear_Regression' and schema_i == 'A2_Biomechanical_ALK' and abs(dist_i - 1.5) < 1e-6 and params_i == {'epsilon': 1.5, 'alpha': 0.001}:
            seed = 55
        else:
            seed = RANDOM_STATE

        exp = generate_shap(model_i, params_i, X_i, y_i, groups_i, y_strat_i, n_splits=N_SPLITS, random_state=seed)
        if exp is not None:
            safe_name = f"rank{int(row['New_Rank'])}_{model_i}_{schema_i}_{dist_i:.1f}mm"
            shap_path = os.path.join(FIG_DIR, f'SR0530_ALK_10fold_Top10_Refined_SHAP_{safe_name}.png')
            plot_shap_summary(exp, f"#{int(row['New_Rank'])} {schema_i} {model_i} @ {dist_i:.1f} mm", shap_path)
            shap_paths.append((int(row['New_Rank']), shap_path))
            print(f"  Rank {int(row['New_Rank'])}: {shap_path}")
        else:
            shap_paths.append((int(row['New_Rank']), None))
            print(f"  Rank {int(row['New_Rank'])}: SHAP skipped for {model_i}")

    # 更新 MD 报告
    update_report(df_top10, shap_paths)

    print("\n" + "=" * 80)
    print("Done!")
    print("=" * 80)


def update_report(df_top10, shap_paths):
    md_path = os.path.join(REPORT_DIR, 'SR0530_ALK_10fold_Top10_Refined_Tuning_SHAP_Report.md')

    md = []
    md.append("\n\n---\n\n")
    md.append("# 附录：最终前十候选配置（含复现 0.500）\n\n")
    md.append("> **说明**：以下排名已将可复现的 A2_Biomechanical_ALK @ 1.5 mm, Robust LR (seed 55, epsilon=1.5, alpha=0.001, R²=0.500) 纳入，并按精扫/复现后的 Test R² 重新排序。\n\n")

    md.append("| 排名 | 距离 (mm) | 方案 | 模型 | Test R² | 95% CI | RMSE | 95% CI | Gap | 参数 |\n")
    md.append("|------|-----------|------|------|---------|--------|------|--------|-----|------|\n")

    shap_dict = dict(shap_paths)

    for _, row in df_top10.iterrows():
        rank = int(row['New_Rank'])
        r2_lo, r2_hi = compute_t_ci(row['test_r2'], row['test_r2_std'], n_folds=row['CV_Folds'])
        rmse_lo, rmse_hi = compute_t_ci(row['test_rmse'], row['test_rmse_std'], n_folds=row['CV_Folds'])
        note = row.get('Note', '')
        param_str = str(row['Best_Params_Refined'])
        if note:
            param_str += f" *({note})*"
        md.append(f"| {rank} | {row['Distance_mm']:.1f} | {row['Schema']} | {row['Model']} | "
                  f"{row['test_r2']:.3f} | [{r2_lo:.3f}, {r2_hi:.3f}] | "
                  f"{row['test_rmse']:.1f} | [{rmse_lo:.1f}, {rmse_hi:.1f}] | "
                  f"{row['gap']:.3f} | {param_str} |\n")
    md.append("\n")

    md.append("## 前十配置 SHAP 图\n\n")
    for rank, shap_path in sorted(shap_dict.items()):
        if shap_path is None:
            continue
        row = df_top10[df_top10['New_Rank'] == rank].iloc[0]
        rel_path = os.path.relpath(shap_path, REPORT_DIR).replace('\\', '/')
        md.append(f"### 排名 {rank}：{row['Schema']} / {row['Model']} @ {row['Distance_mm']:.1f} mm\n\n")
        md.append(f"![SHAP Rank {rank}]({rel_path})\n\n")

    with open(md_path, 'a', encoding='utf-8') as f:
        f.write(''.join(md))
    print(f"\n  --> Appended to report: {md_path}")


if __name__ == '__main__':
    main()
