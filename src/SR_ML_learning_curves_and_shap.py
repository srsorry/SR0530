"""
SR0530 Learning Curves + SHAP + Overfitting Assessment
针对 71 眼 lenient 数据集，对推荐方案的 7 个 ML 模型绘制学习曲线、SHAP 图，并评估过拟合。
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
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.svm import SVR
from sklearn.ensemble import RandomForestRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.linear_model import Lasso, ElasticNet, Ridge
from sklearn.metrics import r2_score, mean_squared_error
from xgboost import XGBRegressor

import shap
shap.initjs()

warnings.filterwarnings('ignore')

# ============================================================
# 配置
# ============================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'genData', 'CleanDataRoi_lenient')
OUT_DIR = os.path.join(BASE_DIR, 'genData', 'sum')
REPORT_DIR = os.path.join(BASE_DIR, 'report')
FIG_DIR = os.path.join(REPORT_DIR, 'FIG', 'LC_SHAP')
os.makedirs(FIG_DIR, exist_ok=True)

RESULTS_CSV = os.path.join(OUT_DIR, 'SR0530_HP_Tuning_Results_lenient_ALK.csv')
K_RESULTS_CSV = os.path.join(OUT_DIR, 'SR0530_HP_Tuning_Results_q1plus_K.csv')

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

# 推荐方案（可由用户调整）
SELECTED_CONFIGS = [
    {'distance': 1.5, 'schema': 'C1_Combined_ALK'},
    {'distance': 1.5, 'schema': 'A2_Biomechanical_ALK'},
    {'distance': 1.5, 'schema': 'C1_Combined_K'},
    {'distance': 3.0, 'schema': 'A2_Biomechanical_ALK'},
]

# 显式 schema -> 特征键列表
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

# 模型构造器（与 tuning 脚本一致）
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
    raise ValueError(model_name)


USE_Y_STD = {
    'SVM': False, 'Random_Forest': False, 'XGBoost': False,
    'Neural_Network': True, 'Lasso': False, 'ElasticNet': False, 'Ridge': False
}

MODEL_LIST = ['SVM', 'Random_Forest', 'XGBoost', 'Neural_Network', 'Lasso', 'ElasticNet', 'Ridge']


# ============================================================
# 数据加载与聚合
# ============================================================
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


# ============================================================
# 学习曲线
# ============================================================
def plot_learning_curve(model_name, model_builder, X, y, groups, y_stratify, use_y_std=False,
                        n_splits=5, train_sizes=np.linspace(0.2, 1.0, 8), random_state=42):
    """返回训练集比例、train R2、val R2 列表。"""
    unique_groups = np.unique(groups)
    n_groups = len(unique_groups)
    n_splits = min(n_splits, n_groups // 2)
    if n_splits < 2:
        n_splits = 2

    rng = np.random.RandomState(random_state)
    group_df = pd.DataFrame({'group': unique_groups, 'y': [int(pd.Series(y_stratify[groups == g]).mode()[0]) for g in unique_groups]})
    group_df = group_df.sample(frac=1, random_state=random_state).reset_index(drop=True)
    pos = group_df[group_df['y'] == 1].reset_index(drop=True)
    neg = group_df[group_df['y'] == 0].reset_index(drop=True)
    folds = [[] for _ in range(n_splits)]
    for df_label in [pos, neg]:
        for i, row in df_label.iterrows():
            folds[i % n_splits].append(row['group'])
    for i in range(n_splits):
        if not folds[i]:
            non_empty = [k for k in range(n_splits) if len(folds[k]) > 0 and k != i]
            largest = max(non_empty, key=lambda k: len(folds[k]))
            folds[i].append(folds[largest].pop())

    train_scores_all, val_scores_all = [], []
    for i in range(n_splits):
        test_groups = folds[i]
        train_groups = [g for f in folds[:i] + folds[i+1:] for g in f]
        test_idx = np.array([idx for g in test_groups for idx in np.where(groups == g)[0]])
        train_idx_full = np.array([idx for g in train_groups for idx in np.where(groups == g)[0]])

        if len(train_idx_full) < 5 or len(test_idx) < 1:
            continue

        train_scores, val_scores = [], []
        for frac in train_sizes:
            n_train = max(1, int(len(train_idx_full) * frac))
            train_idx = train_idx_full[:n_train]

            model = model_builder()
            if use_y_std:
                sx, sy = StandardScaler(), StandardScaler()
                Xt = sx.fit_transform(X.iloc[train_idx])
                Xv = sx.transform(X.iloc[test_idx])
                yt = sy.fit_transform(y.iloc[train_idx].values.reshape(-1, 1)).ravel()
                yv = y.iloc[test_idx].values
                model.fit(Xt, yt)
                pred_train = sy.inverse_transform(model.predict(Xt).reshape(-1, 1)).ravel()
                pred_val = sy.inverse_transform(model.predict(Xv).reshape(-1, 1)).ravel()
            else:
                model.fit(X.iloc[train_idx], y.iloc[train_idx])
                pred_train = model.predict(X.iloc[train_idx])
                pred_val = model.predict(X.iloc[test_idx])

            train_scores.append(r2_score(y.iloc[train_idx].values, pred_train))
            val_scores.append(r2_score(y.iloc[test_idx].values, pred_val))
        train_scores_all.append(train_scores)
        val_scores_all.append(val_scores)

    train_mean = np.mean(train_scores_all, axis=0)
    val_mean = np.mean(val_scores_all, axis=0)
    return train_sizes, train_mean, val_mean


# ============================================================
# SHAP
# ============================================================
def compute_shap(model_name, model, X_train, X_sample=None, use_y_std=False):
    """计算 SHAP values，返回 Explanation 对象。"""
    if X_sample is None:
        X_sample = X_train

    if model_name in ['Lasso', 'ElasticNet', 'Ridge']:
        # 线性模型：coef * (X - mean)
        scaler = model.named_steps['s']
        reg = model.named_steps.get('lasso') or model.named_steps.get('en') or model.named_steps.get('ridge')
        X_scaled = scaler.transform(X_sample)
        coef = reg.coef_
        shap_vals = X_scaled * coef
        base_val = reg.intercept_
        if use_y_std:
            base_val = base_val  # 已经在标准化空间
        expl = shap.Explanation(values=shap_vals, base_values=base_val, data=X_sample.values, feature_names=list(X_sample.columns))
        return expl

    if model_name == 'Random_Forest':
        explainer = shap.TreeExplainer(model.named_steps['rf'])
        shap_vals = explainer.shap_values(X_sample.values)
        return shap.Explanation(values=shap_vals, base_values=explainer.expected_value, data=X_sample.values, feature_names=list(X_sample.columns))

    if model_name == 'XGBoost':
        explainer = shap.TreeExplainer(model)
        shap_vals = explainer.shap_values(X_sample.values)
        return shap.Explanation(values=shap_vals, base_values=explainer.expected_value, data=X_sample.values, feature_names=list(X_sample.columns))

    if model_name == 'SVM':
        # 使用 KernelExplainer，采样背景数据
        bg = shap.sample(X_train, min(30, len(X_train)), random_state=42)
        explainer = shap.KernelExplainer(lambda x: model.predict(pd.DataFrame(x, columns=X_train.columns)), bg.values)
        shap_vals = explainer.shap_values(X_sample.values, nsamples=100)
        return shap.Explanation(values=np.array(shap_vals), base_values=explainer.expected_value, data=X_sample.values, feature_names=list(X_sample.columns))

    if model_name == 'Neural_Network':
        # 使用 DeepExplainer（sklearn MLP 不直接支持，改用 KernelExplainer）
        bg = shap.sample(X_train, min(30, len(X_train)), random_state=42)
        explainer = shap.KernelExplainer(lambda x: model.predict(pd.DataFrame(x, columns=X_train.columns)), bg.values)
        shap_vals = explainer.shap_values(X_sample.values, nsamples=100)
        return shap.Explanation(values=np.array(shap_vals), base_values=explainer.expected_value, data=X_sample.values, feature_names=list(X_sample.columns))

    return None


# ============================================================
# 主程序
# ============================================================
def main():
    print("=" * 80)
    print("SR0530 Learning Curves + SHAP + Overfitting Assessment")
    print("Data: lenient (71 eyes) | Schemes: selected ALK/K variants")
    print("=" * 80)

    df_results_alk = pd.read_csv(RESULTS_CSV)
    df_results_k = pd.read_csv(K_RESULTS_CSV)
    df_results = pd.concat([df_results_alk, df_results_k], ignore_index=True)
    df_results = df_results[df_results['Data_Group'] == 'lenient'].copy()
    eye_to_subject = load_subject_mapping(DATA_DIR)
    all_data = load_distance_data(DATA_DIR)

    summary_records = []
    report_images = []

    for cfg in SELECTED_CONFIGS:
        dist = cfg['distance']
        schema = cfg['schema']
        print(f"\n--- Distance {dist:.1f} mm | Schema {schema} ---")

        df = aggregate_distance(all_data[dist], eye_to_subject)
        feat_short = schema.split('_')  # This won't work; need schema-to-features mapping
        # Build mapping from SCHEMA in tuning results - infer from feature list
        # We reconstruct feature list by looking at results CSV for this schema
        schema_rows = df_results[(df_results['Distance_mm'] == dist) & (df_results['Schema'] == schema)]
        if schema_rows.empty:
            print(f"  -> No tuning results for {schema} at {dist}, skipping")
            continue

        # 使用显式映射获取特征列表
        if schema not in SCHEMA_FEATURES:
            print(f"  -> Unknown schema {schema}, skipping")
            continue
        feat_keys = SCHEMA_FEATURES[schema]
        feat_full = [FEATURE_ALL[k] for k in feat_keys]
        df_sub = fill_na(df.copy(), feat_full)
        X = df_sub[feat_full]
        y = df_sub[TARGET_COL]
        groups = df_sub['Real_Subject_ID'].values
        y_strat = df_sub['Myopia'].values

        n_subjects = len(np.unique(groups))
        n_eyes = len(df_sub)
        print(f"  N={n_eyes} eyes/{n_subjects} subjects | Features={feat_full}")

        # Plot directory
        plot_prefix = f"{dist:.1f}mm_{schema}"

        # Learning curves for all 7 models
        fig, axes = plt.subplots(2, 4, figsize=(20, 10))
        axes = axes.flatten()
        lc_data = {}
        for idx, model_name in enumerate(MODEL_LIST):
            ax = axes[idx]
            row = schema_rows[schema_rows['Model'] == model_name]
            if row.empty:
                ax.set_title(f"{model_name}\n(no result)")
                ax.axis('off')
                continue
            params = eval(row.iloc[0]['Best_Params'])
            builder = lambda p=params, m=model_name: build_model(m, p)

            train_sizes, train_r2, val_r2 = plot_learning_curve(
                model_name, builder, X, y, groups, y_strat,
                use_y_std=USE_Y_STD[model_name], random_state=RANDOM_STATE
            )
            lc_data[model_name] = {'train_sizes': train_sizes, 'train_r2': train_r2, 'val_r2': val_r2}
            ax.plot(train_sizes, train_r2, 'o-', label='Train', color='C0')
            ax.plot(train_sizes, val_r2, 's-', label='Validation', color='C1')
            ax.axhline(0, color='gray', linestyle='--', linewidth=0.8)
            ax.set_xlabel('Training fraction')
            ax.set_ylabel('R²')
            ax.set_title(model_name)
            ax.legend()
            ax.grid(True, alpha=0.3)

            gap = train_r2[-1] - val_r2[-1]
            summary_records.append({
                'Distance_mm': dist,
                'Schema': schema,
                'Model': model_name,
                'N_Eyes': n_eyes,
                'N_Subjects': n_subjects,
                'Final_Train_R2': train_r2[-1],
                'Final_Val_R2': val_r2[-1],
                'LC_Gap': gap,
                'Converged': abs(train_r2[-1] - train_r2[-2]) < 0.05 and abs(val_r2[-1] - val_r2[-2]) < 0.05
            })

        for idx in range(len(MODEL_LIST), len(axes)):
            axes[idx].axis('off')

        plt.suptitle(f'Learning Curves: {schema} at {dist:.1f} mm (lenient)', fontsize=14, fontweight='bold')
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        lc_path = os.path.join(FIG_DIR, f'LC_{plot_prefix}.png')
        plt.savefig(lc_path, dpi=300, bbox_inches='tight')
        plt.close()
        report_images.append(('Learning Curves', lc_path))
        print(f"  -> Saved: {lc_path}")

        # SHAP for selected interpretable models (top 2 by validation R2)
        top_models = schema_rows.nlargest(2, 'test_r2')['Model'].tolist()
        for model_name in top_models:
            row = schema_rows[schema_rows['Model'] == model_name].iloc[0]
            params = eval(row['Best_Params'])
            model = build_model(model_name, params)
            if USE_Y_STD[model_name]:
                sx, sy = StandardScaler(), StandardScaler()
                Xt = sx.fit_transform(X)
                yt = sy.fit_transform(y.values.reshape(-1, 1)).ravel()
                model.fit(Xt, yt)
            else:
                model.fit(X, y)
                sx = None

            # Sample for SHAP (max 50)
            X_sample = X.sample(min(50, len(X)), random_state=RANDOM_STATE)
            X_train_for_shap = X

            try:
                expl = compute_shap(model_name, model, X_train_for_shap, X_sample, use_y_std=USE_Y_STD[model_name])
                if expl is not None:
                    fig, ax = plt.subplots(figsize=(10, 6))
                    shap.plots.beeswarm(expl, show=False, max_display=10)
                    plt.title(f'SHAP: {model_name} | {schema} | {dist:.1f} mm')
                    plt.tight_layout()
                    shap_path = os.path.join(FIG_DIR, f'SHAP_{plot_prefix}_{model_name}.png')
                    plt.savefig(shap_path, dpi=300, bbox_inches='tight')
                    plt.close()
                    report_images.append((f'SHAP {model_name}', shap_path))
                    print(f"  -> Saved: {shap_path}")
            except Exception as e:
                print(f"  -> SHAP failed for {model_name}: {e}")

    # Save summary CSV
    df_summary = pd.DataFrame(summary_records)
    summary_csv = os.path.join(OUT_DIR, 'SR0530_LC_Overfitting_Summary.csv')
    df_summary.to_csv(summary_csv, index=False, encoding='utf-8-sig')
    print(f"\nSaved summary: {summary_csv}")

    # Generate report
    generate_report(df_summary, report_images, SELECTED_CONFIGS)

    print("\n" + "=" * 80)
    print("Learning curves + SHAP complete!")
    print("=" * 80)


# ============================================================
# 报告生成
# ============================================================
def generate_report(df_summary, report_images, configs):
    md = []
    md.append("# SR0530 学习曲线、SHAP 与过拟合评估报告\n\n")
    md.append("> **目标**：对 71 眼 lenient 数据集上的推荐方案，绘制各 ML 模型的学习曲线，评估过拟合程度，并对表现最好的模型生成 SHAP 解释图。\n\n")
    md.append("> **数据**：lenient（71 眼 / 46 subjects），象限策略为 ≥1 象限可用。\n\n")
    md.append("---\n\n")

    md.append("## 一、评估的方案与距离\n\n")
    for cfg in configs:
        md.append(f"- **{cfg['schema']}** at **{cfg['distance']:.1f} mm**\n")
    md.append("\n")

    md.append("## 二、过拟合评估汇总\n\n")
    md.append("| 距离 (mm) | 方案 | 模型 | Final Train R² | Final Val R² | LC Gap | 是否收敛 | 过拟合判断 |\n")
    md.append("|-----------|------|------|----------------|--------------|--------|----------|------------|\n")
    for _, row in df_summary.iterrows():
        gap = row['LC_Gap']
        if gap < 0.05:
            verdict = "良好"
        elif gap < 0.15:
            verdict = "轻度过拟合"
        elif gap < 0.30:
            verdict = "中度过拟合"
        else:
            verdict = "重度过拟合"
        converged = "是" if row['Converged'] else "否"
        md.append(f"| {row['Distance_mm']:.1f} | {row['Schema']} | {row['Model']} | "
                  f"{row['Final_Train_R2']:.3f} | {row['Final_Val_R2']:.3f} | "
                  f"{gap:.3f} | {converged} | {verdict} |\n")
    md.append("\n")

    md.append("## 三、按方案汇总的平均过拟合 Gap\n\n")
    avg_gap = df_summary.groupby(['Distance_mm', 'Schema'])['LC_Gap'].mean().reset_index().sort_values('LC_Gap')
    md.append("| 距离 (mm) | 方案 | 平均 LC Gap |\n")
    md.append("|-----------|------|-------------|\n")
    for _, row in avg_gap.iterrows():
        md.append(f"| {row['Distance_mm']:.1f} | {row['Schema']} | {row['LC_Gap']:.3f} |\n")
    md.append("\n")

    md.append("## 四、可视化\n\n")
    seen = set()
    for label, path in report_images:
        rel_path = os.path.relpath(path, REPORT_DIR).replace('\\', '/')
        if path not in seen:
            md.append(f"### {label}: {os.path.basename(path)}\n\n")
            md.append(f"![{label}]({rel_path})\n\n")
            seen.add(path)

    md.append("## 五、关键发现与建议\n\n")
    md.append("1. **学习曲线 Gap 越小越好**：Gap < 0.05 表示模型泛化良好；Gap > 0.30 提示严重过拟合，需增加正则化或减少模型复杂度。\n")
    md.append("2. **线性模型通常更稳健**：Lasso、Ridge、ElasticNet 的 LC Gap 通常小于树模型和神经网络。\n")
    md.append("3. **SHAP 图显示特征贡献方向**：正 SHAP 值表示该特征推高预测密度，负值表示拉低。可据此解释 AL、SE、AL/K 等变量的作用方向。\n")
    md.append("4. **最终模型选择**：综合考虑 Test R²、LC Gap 和可解释性，优先选择 Gap 小且 R² 高的线性模型。\n\n")

    md.append("---\n\n")
    md.append("*Report generated automatically by SR_ML_learning_curves_and_shap.py*\n")

    md_path = os.path.join(REPORT_DIR, 'SR0530_Learning_Curves_SHAP_Report.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(''.join(md))
    print(f"  --> Report: {md_path}")


if __name__ == '__main__':
    main()
