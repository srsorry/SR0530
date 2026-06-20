"""
SR_ML_best_model_diagnostics.py
识别 HP 寻优中 Test R² 最高的机器学习模型，并输出过拟合诊断图：
1) Learning Curves（训练/验证 R² 与 RMSE 随样本量变化）
2) SHAP summary plot（特征影响分布）
"""

import os
import glob
import ast
import warnings
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupKFold, learning_curve
from sklearn.pipeline import Pipeline
from sklearn.svm import SVR
from sklearn.ensemble import RandomForestRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.linear_model import Lasso, ElasticNet, Ridge
from sklearn.metrics import r2_score, mean_squared_error, make_scorer
from xgboost import XGBRegressor

from scipy import stats

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
MODE_LABEL = 'q1plus'
N_FOLDS = 5

USE_Y_STD = {
    'SVM': False, 'Random_Forest': False, 'XGBoost': False,
    'Neural_Network': True, 'Lasso': False, 'ElasticNet': False, 'Ridge': False
}

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    print("shap not installed, SHAP plot will be skipped.")


# ============================================================
# 工具函数（与现有脚本保持一致）
# ============================================================
def load_subject_mapping(data_dir):
    df_ref = pd.read_csv(os.path.join(data_dir, 'data1.csv'))
    mapping = {}
    for _, row in df_ref.iterrows():
        mapping[row['Eye_Label']] = row['Subject_ID']
        mapping[row['Subject_ID']] = row['Subject_ID']
    return mapping


def load_distance_data(data_dir):
    """读取 44 个 ROI 文件，按距离聚合。"""
    all_data = {}
    for f in sorted(glob.glob(os.path.join(data_dir, 'data*.csv'))):
        df = pd.read_csv(f)
        dist = df['Eccentricity (mm)'].iloc[0]
        if dist not in all_data:
            all_data[dist] = []
        all_data[dist].append(df)
    return all_data


def aggregate_distance(dfs, eye_to_subject, min_quadrants=1):
    """按 Subject_ID + Eye 聚合象限密度。"""
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

    if min_quadrants == 4:
        merged = merged[merged['N_Quadrants'] == 4].copy()
    else:
        merged = merged[merged['N_Quadrants'] >= min_quadrants].copy()

    # 2. 从第一个包含该眼的象限提取固定协变量
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
    for col in cols:
        if df[col].isna().any():
            df[col].fillna(df[col].median(), inplace=True)
    return df


def get_model_builder(model_name):
    """返回模型构建函数。"""
    builders = {
        'SVM': lambda p: Pipeline([('s', StandardScaler()), ('v', SVR(**p))]),
        'Random_Forest': lambda p: Pipeline([
            ('s', StandardScaler()),
            ('rf', RandomForestRegressor(**p, random_state=RANDOM_STATE, n_jobs=1))
        ]),
        'XGBoost': lambda p: XGBRegressor(**p, random_state=RANDOM_STATE, verbosity=0),
        'Neural_Network': lambda p: Pipeline([
            ('s', StandardScaler()),
            ('nn', MLPRegressor(**p, max_iter=5000, early_stopping=True,
                                validation_fraction=0.15, n_iter_no_change=20,
                                random_state=RANDOM_STATE))
        ]),
        'Lasso': lambda p: Pipeline([('s', StandardScaler()), ('m', Lasso(**p, random_state=RANDOM_STATE, max_iter=10000))]),
        'ElasticNet': lambda p: Pipeline([('s', StandardScaler()), ('m', ElasticNet(**p, random_state=RANDOM_STATE, max_iter=10000))]),
        'Ridge': lambda p: Pipeline([('s', StandardScaler()), ('m', Ridge(**p, random_state=RANDOM_STATE))]),
    }
    return builders[model_name]


def rmse_score(y_true, y_pred):
    return -np.sqrt(mean_squared_error(y_true, y_pred))


RMSE_SCORER = make_scorer(rmse_score, greater_is_better=True)


# ============================================================
# 诊断图生成
# ============================================================
def plot_learning_curves(model, X, y, groups, feature_names, model_name, use_y_std, out_prefix):
    """生成 R² 与 RMSE 的学习曲线。"""
    train_sizes = np.linspace(0.2, 1.0, 5)
    cv = GroupKFold(n_splits=N_FOLDS)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # R² learning curve
    train_sizes_abs, train_scores, test_scores = learning_curve(
        model, X, y, groups=groups, train_sizes=train_sizes,
        cv=cv, scoring='r2', random_state=RANDOM_STATE, n_jobs=1
    )
    train_mean = np.mean(train_scores, axis=1)
    train_std = np.std(train_scores, axis=1)
    test_mean = np.mean(test_scores, axis=1)
    test_std = np.std(test_scores, axis=1)

    ax = axes[0]
    ax.plot(train_sizes_abs, train_mean, 'o-', color='blue', label='Training R²')
    ax.fill_between(train_sizes_abs, train_mean - train_std, train_mean + train_std, alpha=0.1, color='blue')
    ax.plot(train_sizes_abs, test_mean, 'o-', color='green', label='Validation R²')
    ax.fill_between(train_sizes_abs, test_mean - test_std, test_mean + test_std, alpha=0.1, color='green')
    ax.axhline(0, color='gray', linestyle='--', linewidth=0.8)
    ax.set_xlabel('Training Set Size')
    ax.set_ylabel('R²')
    ax.set_title(f'Learning Curve (R²) - {model_name}')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # RMSE learning curve
    train_sizes_abs2, train_scores2, test_scores2 = learning_curve(
        model, X, y, groups=groups, train_sizes=train_sizes,
        cv=cv, scoring=RMSE_SCORER, random_state=RANDOM_STATE, n_jobs=1
    )
    train_mean2 = -np.mean(train_scores2, axis=1)
    train_std2 = np.std(train_scores2, axis=1)
    test_mean2 = -np.mean(test_scores2, axis=1)
    test_std2 = np.std(test_scores2, axis=1)

    ax = axes[1]
    ax.plot(train_sizes_abs2, train_mean2, 'o-', color='blue', label='Training RMSE')
    ax.fill_between(train_sizes_abs2, train_mean2 - train_std2, train_mean2 + train_std2, alpha=0.1, color='blue')
    ax.plot(train_sizes_abs2, test_mean2, 'o-', color='green', label='Validation RMSE')
    ax.fill_between(train_sizes_abs2, test_mean2 - test_std2, test_mean2 + test_std2, alpha=0.1, color='green')
    ax.set_xlabel('Training Set Size')
    ax.set_ylabel('RMSE')
    ax.set_title(f'Learning Curve (RMSE) - {model_name}')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    path = os.path.join(OUT_DIR, f'{out_prefix}_Learning_Curves.png')
    plt.savefig(path, dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(FIG_DIR, os.path.basename(path)), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  --> Saved learning curves: {path}")
    return path


def plot_shap_summary(model, X, y, feature_names, model_name, out_prefix):
    """生成 SHAP summary plot。"""
    if not SHAP_AVAILABLE:
        print("  SHAP not available, skipping SHAP summary plot.")
        return None

    try:
        # 确保 X 是 DataFrame
        if isinstance(X, np.ndarray):
            X_df = pd.DataFrame(X, columns=feature_names)
        else:
            X_df = X.copy()

        explainer = shap.Explainer(model.predict, X_df)
        shap_values = explainer(X_df)

        fig, ax = plt.subplots(figsize=(10, 6))
        shap.summary_plot(shap_values, X_df, show=False)
        plt.title(f'SHAP Summary - {model_name}')
        plt.tight_layout()
        path = os.path.join(OUT_DIR, f'{out_prefix}_SHAP_Summary.png')
        plt.savefig(path, dpi=300, bbox_inches='tight')
        plt.savefig(os.path.join(FIG_DIR, os.path.basename(path)), dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  --> Saved SHAP summary: {path}")
        return path
    except Exception as e:
        print(f"  SHAP summary failed: {e}")
        return None


def generate_diagnostics_report(best_row, learning_curve_path, shap_path, out_prefix):
    """生成简短诊断报告。"""
    md = []
    md.append(f"# SR0530 最佳机器学习模型过拟合诊断报告（{MODE_LABEL}）\n\n")
    md.append("> **目标**：对 HP 寻优中 Test R² 最高的模型进行过拟合评估（Learning Curves + SHAP）。\n\n")

    md.append("## 一、最佳模型信息\n\n")
    md.append(f"- **数据组**：{best_row['Data_Group']}\n")
    md.append(f"- **距离**：{best_row['Distance_mm']:.1f} mm\n")
    md.append(f"- **方案**：{best_row['Schema']}\n")
    md.append(f"- **模型**：{best_row['Model']}\n")
    md.append(f"- **Test R²**：{best_row['test_r2']:.3f}\n")
    md.append(f"- **RMSE**：{best_row['test_rmse']:.1f}\n")
    md.append(f"- **MAPE**：{best_row['test_mape']:.2f}%\n")
    md.append(f"- **最佳参数**：{best_row['Best_Params']}\n")
    md.append(f"- **样本量**：{int(best_row['N_Eyes'])} 眼 / {int(best_row['N_Subjects'])} subjects\n\n")

    md.append("## 二、过拟合判读（Learning Curves）\n\n")
    if learning_curve_path:
        fname = os.path.basename(learning_curve_path)
        md.append(f"![Learning Curves](FIG/{fname})\n\n")
    md.append("1. **训练曲线与验证曲线差距**：若训练 R² 显著高于验证 R²，且随样本量增加差距仍大，提示过拟合。\n")
    md.append("2. **收敛趋势**：若验证 R² 随样本量增加仍在上升，提示增加样本可能提升泛化性能。\n")
    md.append("3. **RMSE 曲线**：训练 RMSE 低于验证 RMSE 是正常的；差距过大同样提示过拟合。\n\n")

    md.append("## 三、特征影响（SHAP Summary）\n\n")
    if shap_path:
        fname = os.path.basename(shap_path)
        md.append(f"![SHAP Summary](FIG/{fname})\n\n")
    else:
        md.append("SHAP summary plot 未生成（可能未安装 shap 或模型不支持）。\n\n")
    md.append("- SHAP summary 展示每个特征对模型预测的贡献分布。\n")
    md.append("- 颜色表示特征值高低（红=高，蓝=低），横轴表示 SHAP 值（对预测的影响方向与幅度）。\n\n")

    md.append("---\n\n")
    md.append("*Report generated by SR_ML_best_model_diagnostics.py*\n")

    md_path = os.path.join(REPORT_DIR, f'{out_prefix}_Report.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(''.join(md))
    print(f"  --> Report: {md_path}")
    return md_path


# ============================================================
# 主程序
# ============================================================
def main():
    print("=" * 80)
    print("SR0530 Best ML Model Diagnostics")
    print(f"Mode: {MODE_LABEL}")
    print("=" * 80)

    # 1. 读取 HP 结果并找出最佳模型
    results_csv = os.path.join(OUT_DIR, f'SR0530_HP_Tuning_Results_{MODE_LABEL}.csv')
    df_results = pd.read_csv(results_csv)
    best_idx = df_results['test_r2'].idxmax()
    best_row = df_results.loc[best_idx]

    print(f"\n最佳模型：{best_row['Data_Group']} / {best_row['Distance_mm']:.1f} mm / "
          f"{best_row['Schema']} / {best_row['Model']}")
    print(f"Test R2 = {best_row['test_r2']:.3f}")

    # 2. 加载数据
    data_group = best_row['Data_Group']
    data_dir = DATA_DIRS[data_group]
    eye_to_subject = load_subject_mapping(data_dir)
    all_data = load_distance_data(data_dir)
    dist = best_row['Distance_mm']

    if dist not in all_data:
        raise ValueError(f"Distance {dist} not found in data")

    df = aggregate_distance(all_data[dist], eye_to_subject, min_quadrants=1)
    schema_name = best_row['Schema']
    feat_short = SCHEMA[schema_name]
    feat_full = [FEATURE_ALL[s] for s in feat_short]
    df_sub = fill_na(df.copy(), feat_full)

    X = df_sub[feat_full]
    y = df_sub[TARGET_COL]
    groups = df_sub['Real_Subject_ID'].values

    print(f"Loaded {len(df_sub)} eyes / {len(np.unique(groups))} subjects")
    print(f"Features: {feat_full}")

    # 3. 构建最佳模型
    model_name = best_row['Model']
    best_params = ast.literal_eval(best_row['Best_Params'])
    model_builder = get_model_builder(model_name)
    model = model_builder(best_params)

    # 4. 生成学习曲线
    out_prefix = f'SR0530_Best_Model_{data_group}_{dist:.1f}mm_{schema_name}_{model_name}_{MODE_LABEL}'
    lc_path = plot_learning_curves(model, X, y, groups, feat_full, model_name,
                                    USE_Y_STD[model_name], out_prefix)

    # 5. 生成 SHAP summary
    # 需要在全量数据上拟合模型
    fitted_model = model.fit(X, y)
    shap_path = plot_shap_summary(fitted_model, X, y, feat_full, model_name, out_prefix)

    # 6. 生成报告
    generate_diagnostics_report(best_row, lc_path, shap_path, out_prefix)

    print("\n" + "=" * 80)
    print("Best model diagnostics complete!")
    print("=" * 80)


if __name__ == '__main__':
    main()
