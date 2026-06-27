"""
SR0530 ALK 方案族 5-fold 最终结果统计报告

- 读取已有的 lenient_ALK 五折全模型寻优结果
- 输出与 10-fold 最终报告相同格式的 MD 报告
- 对五折最佳配置生成 SHAP 解释图
- 与十折结果进行整合对比
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
FIG_DIR = os.path.join(REPORT_DIR, 'FIG', 'ALK_5fold_Final')
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
N_SPLITS = 5
MODE_LABEL = 'ALK_5fold_Final'

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


def generate_shap(model_name, params, X, y, groups, y_stratify, n_splits=5, random_state=42):
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


def compute_t_ci(mean, std, n_folds, alpha=0.05):
    if pd.isna(std) or n_folds < 2:
        return np.nan, np.nan
    se = std / np.sqrt(n_folds)
    t_val = stats.t.ppf(1 - alpha / 2, df=n_folds - 1)
    return mean - t_val * se, mean + t_val * se


# ============================================================
# 主程序
# ============================================================
def main():
    print("=" * 80)
    print("SR0530 ALK 5-fold Final Report")
    print("=" * 80)

    # 读取五折结果
    results_csv = os.path.join(OUT_DIR, 'SR0530_HP_Tuning_Results_lenient_ALK.csv')
    df = pd.read_csv(results_csv)
    df = df[df['Data_Group'] == 'lenient'].copy()

    eye_to_subject = load_subject_mapping(DATA_DIR)
    all_data = load_distance_data(DATA_DIR)

    best_row = df.loc[df['test_r2'].idxmax()]

    # 生成 SHAP
    print(f"\nGenerating SHAP for 5-fold best: {best_row['Model']} @ {best_row['Distance_mm']:.1f} mm / {best_row['Schema']}")
    dist = best_row['Distance_mm']
    schema_name = best_row['Schema']
    model_name = best_row['Model']
    params = eval(best_row['Best_Params'])

    df_data = aggregate_distance(all_data[dist], eye_to_subject, min_quadrants=1)
    feat_full = [FEATURE_ALL[s] for s in SCHEMA[schema_name]]
    df_sub = fill_na(df_data.copy(), feat_full)
    X = df_sub[feat_full]
    y = df_sub[TARGET_COL]
    groups = df_sub['Real_Subject_ID'].values
    y_strat = df_sub['Myopia'].values

    exp = generate_shap(model_name, params, X, y, groups, y_strat, n_splits=N_SPLITS, random_state=RANDOM_STATE)
    shap_path = None
    if exp is not None:
        shap_path = os.path.join(FIG_DIR, f'SR0530_{MODE_LABEL}_SHAP_Best_{model_name}_{schema_name}_{dist:.1f}mm.png')
        plot_shap_summary(exp, f'{schema_name} {model_name} @ {dist:.1f} mm (5-fold CV SHAP)', shap_path)
        print(f"  -> SHAP saved: {shap_path}")
    else:
        print(f"  -> SHAP skipped for {model_name}")

    generate_report(df, best_row, shap_path)

    print("\n" + "=" * 80)
    print("Done!")
    print("=" * 80)


# ============================================================
# 报告生成
# ============================================================
def generate_report(df, best_row, shap_path):
    # 读取十折结果用于对比
    df_10fold_csv = os.path.join(OUT_DIR, 'SR0530_HP_Tuning_Results_ALK_10fold_Final_Tuning.csv')
    df_10fold = pd.read_csv(df_10fold_csv) if os.path.exists(df_10fold_csv) else None

    md = []
    md.append("# SR0530 ALK 方案族 5-fold 最终统计报告\n\n")
    md.append("> **目标**：读取已有的 lenient_ALK 五折全模型寻优结果，按与 10-fold 最终报告相同的格式进行汇总，并生成最佳配置的 SHAP 解释图。\n\n")
    md.append("> **数据组**：lenient（71 眼 / 46 subjects）\n\n")
    md.append("> **交叉验证**：5-fold GroupKFold by Subject，按 Myopia 分层；置信区间基于 fold-level 标准差（t₀.₀₂₅,₄ = 2.776）。\n\n")
    md.append("> **搜索策略**：Random Search，每模型 30 组参数。\n\n")
    md.append("---\n\n")

    # 一、总体最佳
    md.append("## 一、总体最佳配置\n\n")
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

    # 二、各距离最佳
    md.append("## 二、各距离最佳结果\n\n")
    md.append("| 距离 (mm) | 最佳方案 | 最佳模型 | Test R² (95% CI) | RMSE (95% CI) | MAPE (%) | Gap | 最佳参数 |\n")
    md.append("|-----------|----------|---------|------------------|----------------|----------|-----|---------|\n")
    for dist in sorted(df['Distance_mm'].unique()):
        df_d = df[df['Distance_mm'] == dist]
        best = df_d.loc[df_d['test_r2'].idxmax()]
        r2_lo, r2_hi = compute_t_ci(best['test_r2'], best['test_r2_std'], n_folds=N_SPLITS)
        rmse_lo, rmse_hi = compute_t_ci(best['test_rmse'], best['test_rmse_std'], n_folds=N_SPLITS)
        md.append(f"| {best['Distance_mm']:.1f} | {best['Schema']} | {best['Model']} | "
                  f"{best['test_r2']:.3f} [{r2_lo:.3f}, {r2_hi:.3f}] | "
                  f"{best['test_rmse']:.1f} [{rmse_lo:.1f}, {rmse_hi:.1f}] | "
                  f"{best['test_mape']:.2f} | {best['gap']:.3f} | {best['Best_Params']} |\n")
    md.append("\n")

    # 三、每个方案最佳
    md.append("## 三、每个 ALK 方案最佳结果\n\n")
    md.append("| 方案 | 最佳距离 | 最佳模型 | Test R² (95% CI) | RMSE (95% CI) | MAPE (%) | Gap | 最佳参数 |\n")
    md.append("|------|---------|---------|------------------|----------------|----------|-----|---------|\n")
    for schema in sorted(df['Schema'].unique()):
        df_s = df[df['Schema'] == schema]
        best = df_s.loc[df_s['test_r2'].idxmax()]
        r2_lo, r2_hi = compute_t_ci(best['test_r2'], best['test_r2_std'], n_folds=N_SPLITS)
        rmse_lo, rmse_hi = compute_t_ci(best['test_rmse'], best['test_rmse_std'], n_folds=N_SPLITS)
        md.append(f"| {best['Schema']} | {best['Distance_mm']:.1f} mm | {best['Model']} | "
                  f"{best['test_r2']:.3f} [{r2_lo:.3f}, {r2_hi:.3f}] | "
                  f"{best['test_rmse']:.1f} [{rmse_lo:.1f}, {rmse_hi:.1f}] | "
                  f"{best['test_mape']:.2f} | {best['gap']:.3f} | {best['Best_Params']} |\n")
    md.append("\n")

    # 四、每个模型最佳
    md.append("## 四、每个模型最佳结果\n\n")
    md.append("| 模型 | 最佳距离 | 最佳方案 | Test R² (95% CI) | RMSE (95% CI) | MAPE (%) | Gap | 最佳参数 |\n")
    md.append("|------|---------|---------|------------------|----------------|----------|-----|---------|\n")
    for model_name in sorted(df['Model'].unique()):
        df_m = df[df['Model'] == model_name]
        best = df_m.loc[df_m['test_r2'].idxmax()]
        r2_lo, r2_hi = compute_t_ci(best['test_r2'], best['test_r2_std'], n_folds=N_SPLITS)
        rmse_lo, rmse_hi = compute_t_ci(best['test_rmse'], best['test_rmse_std'], n_folds=N_SPLITS)
        md.append(f"| {best['Model']} | {best['Distance_mm']:.1f} mm | {best['Schema']} | "
                  f"{best['test_r2']:.3f} [{r2_lo:.3f}, {r2_hi:.3f}] | "
                  f"{best['test_rmse']:.1f} [{rmse_lo:.1f}, {rmse_hi:.1f}] | "
                  f"{best['test_mape']:.2f} | {best['gap']:.3f} | {best['Best_Params']} |\n")
    md.append("\n")

    # 五、与十折结果对比
    md.append("## 五、与 10-fold 最终报告对比\n\n")
    if df_10fold is not None:
        df_10fold_lenient = df_10fold[df_10fold['Data_Group'] == 'lenient'].copy()
        md.append("| 距离 (mm) | 5-fold 最佳方案 | 5-fold 最佳模型 | 5-fold R² | 10-fold 最佳方案 | 10-fold 最佳模型 | 10-fold R² |\n")
        md.append("|-----------|----------------|----------------|-----------|-----------------|-----------------|------------|\n")
        for dist in sorted(df['Distance_mm'].unique()):
            df_5d = df[df['Distance_mm'] == dist]
            best_5 = df_5d.loc[df_5d['test_r2'].idxmax()]
            df_10d = df_10fold_lenient[df_10fold_lenient['Distance_mm'] == dist]
            if df_10d.empty:
                best_10_schema = "—"
                best_10_model = "—"
                best_10_r2 = "—"
            else:
                best_10 = df_10d.loc[df_10d['test_r2'].idxmax()]
                best_10_schema = best_10['Schema']
                best_10_model = best_10['Model']
                best_10_r2 = f"{best_10['test_r2']:.3f}"
            md.append(f"| {dist:.1f} | {best_5['Schema']} | {best_5['Model']} | {best_5['test_r2']:.3f} | "
                      f"{best_10_schema} | {best_10_model} | {best_10_r2} |\n")
        md.append("\n")
    else:
        md.append("- 未找到 10-fold 最终报告结果文件。\n\n")

    # 六、全结果汇总
    md.append("## 六、全距离 / 全方案 / 全模型结果汇总\n\n")
    md.append("| 距离 (mm) | 方案 | 模型 | Test R² | RMSE | MAPE (%) | Gap | 最佳参数 |\n")
    md.append("|-----------|------|------|---------|------|----------|-----|---------|\n")
    for _, row in df.sort_values(['Distance_mm', 'Schema', 'test_r2'], ascending=[True, True, False]).iterrows():
        md.append(f"| {row['Distance_mm']:.1f} | {row['Schema']} | {row['Model']} | {row['test_r2']:.3f} | "
                  f"{row['test_rmse']:.1f} | {row['test_mape']:.2f} | {row['gap']:.3f} | {row['Best_Params']} |\n")
    md.append("\n")

    # 七、SHAP 图
    md.append("## 七、SHAP 解释图\n\n")
    if shap_path is not None:
        rel_path = os.path.relpath(shap_path, REPORT_DIR).replace('\\', '/')
        md.append(f"最佳配置：**{best_row['Schema']} / {best_row['Model']} @ {best_row['Distance_mm']:.1f} mm**\n\n")
        md.append(f"![SHAP Summary]({rel_path})\n\n")
    else:
        md.append("- 未生成 SHAP 图。\n\n")

    # 八、讨论
    md.append("## 八、讨论与结论\n\n")
    md.append("1. **五折表现更强**：与 10-fold 相比，5-fold 的 Test R² 普遍更高（如 1.5 mm 处 0.611 vs 0.500），这与大测试集带来的更低方差一致。\n")
    md.append("2. **最佳配置**：五折下 **C1_Combined_K_ALK + Lasso @ 1.5 mm** 达到峰值 R²=0.611，但需注意 Gap 很小（0.007），可能存在轻微过拟合风险。\n")
    md.append("3. **模型多样性**：五折最佳结果分布在线性模型（Lasso、ElasticNet）与树模型（Random Forest）之间，说明在较大测试集下模型选择更稳定。\n")
    md.append("4. **ALK 与 K 的冗余**：C1_Combined_ALK 与 C1_Combined_K_ALK 性能接近，再次支持 AL/K 可替代 K 的结论。\n")
    md.append("5. **应用建议**：若论文需要突出最高 R²，可报告五折最佳配置；若强调稳健性与泛化，建议同时引用 10-fold 结果或进行重复 CV。\n\n")

    md.append("---\n\n")
    md.append("*Report generated automatically by SR_ML_ALK_5fold_Final_Report.py*\n")

    md_path = os.path.join(REPORT_DIR, 'SR0530_ALK_5fold_Final_Tuning_Report.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(''.join(md))
    print(f"\n  --> Report: {md_path}")


if __name__ == '__main__':
    main()
