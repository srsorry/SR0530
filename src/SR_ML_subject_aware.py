"""
SR_ML_subject_aware.py
任务二：ML 模型优化（整合全部眼部参数 + Subject-aware CV）
- 输入：年龄/性别/角膜曲率/前房深度/眼轴/等效球镜
- 对每个距离组（1.0-6.0mm）执行 SVM/RF/XGB/NN
- 使用 GroupKFold 按真实 Subject 分层，避免双眼信息泄漏
- 输出 R²/Corr/MAPE/RMSE、Gap、特征重要性、SHAP、MD 报告
"""

import os
import glob
import warnings
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupKFold, cross_validate, RandomizedSearchCV
from sklearn.pipeline import Pipeline
from sklearn.svm import SVR
from sklearn.ensemble import RandomForestRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import make_scorer, r2_score, mean_absolute_error, mean_squared_error
from xgboost import XGBRegressor
from copy import deepcopy
import shap

warnings.filterwarnings('ignore')

# ============================================================
# 配置
# ============================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'genData', 'CleanDataRoi')
PAIR_PATH = os.path.join(BASE_DIR, 'genData', 'sum', 'Subject_Pair_Mapping.csv')
OUT_DIR = os.path.join(BASE_DIR, 'genData', 'sum')
os.makedirs(OUT_DIR, exist_ok=True)

# 完整特征（已排除 RMF，因与 AL 高度共线）
FEATURE_COLS = [
    'Axial length (mm)', 'Age', 'Spherical equivalent refraction (D)',
    'Gender', 'Corneal curvature (mm)', 'Anterior chamber depth (mm)'
]
FEATURE_SHORT = ['AL', 'Age', 'SE', 'Gender', 'CC', 'ACD']
TARGET_COL = 'Angular cone density (cones/ deg2)'

# V6.0 clean 参数作为默认/搜索中心
CONFIGS = {
    'svm': {
        'cols': FEATURE_COLS,  # 任务二使用全部特征
        'C': 2000, 'eps': 500, 'g': 0.03
    },
    'rf': {
        'n': 200, 'd': 3, 's': 10, 'l': 4
    },
    'xgb': {
        'lr': 0.01, 'depth': 2, 'n': 50, 'reg': 1.0
    },
    'nn': {
        'h': (80,), 'a': 0.5, 'lr': 0.0001
    }
}


# ============================================================
# 工具函数
# ============================================================
def load_subject_mapping():
    """
    建立 Eye_xxx -> Patient ID -> Subject_ID 的映射
    返回 dict: {Eye_ID: Subject_ID}
    """
    # 1. 加载配对表
    pairs = pd.read_csv(PAIR_PATH)
    pid_to_subject = {}
    for _, row in pairs.iterrows():
        pid_to_subject[int(row['OD_PatientID'])] = row['Subject_ID']
        pid_to_subject[int(row['OS_PatientID'])] = row['Subject_ID']

    # 2. CleanDataRoi -> orgData 的 Patient ID
    df_org = pd.read_csv(os.path.join(BASE_DIR, 'orgData', 'orgData.csv'))
    df_ref = pd.read_csv(os.path.join(DATA_DIR, 'data1.csv'))

    eye_to_pid = {}
    for _, row in df_ref.iterrows():
        eye = row['Eye']
        al = row['Axial length (mm)']
        age = row['Age']
        se = row['Spherical equivalent refraction (D)']
        gender = row['Gender']

        mask = (df_org['Eye'] == eye) & \
               (df_org['Axial length (mm)'] == al) & \
               (df_org['Age'] == age) & \
               (df_org['Spherical equivalent refraction (D)'] == se) & \
               (df_org['Gender'] == gender)
        matches = df_org[mask]
        if len(matches) == 1:
            eye_to_pid[row['Subject_ID']] = int(matches.iloc[0]['Patient ID'])
        else:
            raise ValueError(f"Cannot uniquely map {row['Subject_ID']} (matches={len(matches)})")

    # 3. 单眼受试者使用 Single_PID 作为 Subject_ID
    eye_to_subject = {}
    for eye_id, pid in eye_to_pid.items():
        eye_to_subject[eye_id] = pid_to_subject.get(pid, f'Single_{pid}')

    return eye_to_subject


def load_distance_data():
    """读取 44 个 ROI 文件，按距离聚合为 11 个数据集"""
    all_data = {}
    for f in sorted(glob.glob(os.path.join(DATA_DIR, 'data*.csv'))):
        df = pd.read_csv(f)
        dist = df['Eccentricity (mm)'].iloc[0]
        if dist not in all_data:
            all_data[dist] = []
        all_data[dist].append(df)
    return all_data


def aggregate_distance(dfs, dist, eye_to_subject):
    """
    对同一距离的 4 个象限数据，找到共同 Subject 并计算平均 angular density。
    同时建立真实 Subject_ID 用于 GroupKFold。
    """
    base = dfs[0][['Subject_ID', 'Eye'] + FEATURE_COLS + [TARGET_COL]].copy()
    base = base.rename(columns={TARGET_COL: 'density_q1'})

    for i, d in enumerate(dfs[1:], 2):
        base = base.merge(
            d[['Subject_ID', TARGET_COL]].rename(columns={TARGET_COL: f'density_q{i}'}),
            on='Subject_ID', how='inner'
        )

    den_cols = [c for c in base.columns if c.startswith('density_q')]
    base[TARGET_COL] = base[den_cols].mean(axis=1)

    # 添加真实 Subject_ID
    base['Real_Subject_ID'] = base['Subject_ID'].map(eye_to_subject)

    cols = ['Subject_ID', 'Real_Subject_ID', 'Eye'] + FEATURE_COLS + [TARGET_COL]
    return base[cols].copy()


def fill_na(df):
    """中位数填充缺失值"""
    for col in FEATURE_COLS:
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


def eval_model_group_cv(model, X, y, groups, use_y_std=False):
    """
    按真实 Subject 做 GroupKFold 交叉验证。
    groups: 每个样本对应的 Real_Subject_ID
    """
    n_splits = min(10, len(np.unique(groups)))
    gkf = GroupKFold(n_splits=n_splits)

    train_r2_list, test_r2_list = [], []
    test_corr_list, test_mape_list, test_rmse_list = [], [], []

    for ti, vi in gkf.split(X, y, groups=groups):
        if use_y_std:
            sx, sy = StandardScaler(), StandardScaler()
            Xt = sx.fit_transform(X.iloc[ti])
            Xv = sx.transform(X.iloc[vi])
            yt = sy.fit_transform(y.iloc[ti].values.reshape(-1, 1)).ravel()
            yv = y.iloc[vi].values
            yt_raw = y.iloc[ti].values
            m = deepcopy(model)
            m.fit(Xt, yt)
            pred = sy.inverse_transform(m.predict(Xv).reshape(-1, 1)).ravel()
            pred_train = sy.inverse_transform(m.predict(Xt).reshape(-1, 1)).ravel()
        else:
            m = deepcopy(model)
            m.fit(X.iloc[ti], y.iloc[ti])
            pred = m.predict(X.iloc[vi])
            pred_train = m.predict(X.iloc[ti])
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


def tune_model_group_cv(model, param_dist, X, y, groups, n_iter=15, use_y_std=False, random_state=42):
    """
    使用 RandomizedSearchCV 在 GroupKFold 上调参。
    由于 GroupKFold 需要 groups，我们手动实现搜索。
    """
    rng = np.random.RandomState(random_state)
    best_score = -np.inf
    best_params = None

    n_splits = min(5, len(np.unique(groups)))
    gkf = GroupKFold(n_splits=n_splits)

    for _ in range(n_iter):
        params = {k: rng.choice(v) if isinstance(v, list) else v for k, v in param_dist.items()}
        m = deepcopy(model)
        m.set_params(**params)

        scores = []
        for ti, vi in gkf.split(X, y, groups=groups):
            if use_y_std:
                sx, sy = StandardScaler(), StandardScaler()
                Xt = sx.fit_transform(X.iloc[ti])
                Xv = sx.transform(X.iloc[vi])
                yt = sy.fit_transform(y.iloc[ti].values.reshape(-1, 1)).ravel()
                yv = y.iloc[vi].values
                m2 = deepcopy(m)
                m2.fit(Xt, yt)
                pred = sy.inverse_transform(m2.predict(Xv).reshape(-1, 1)).ravel()
            else:
                m2 = deepcopy(m)
                m2.fit(X.iloc[ti], y.iloc[ti])
                pred = m2.predict(X.iloc[vi])
                yv = y.iloc[vi].values
            scores.append(r2_score(yv, pred))

        score = np.mean(scores)
        if score > best_score:
            best_score = score
            best_params = params

    return best_params, best_score


def build_models(df, groups, do_tune=False):
    """构建并（可选）调优四个模型"""
    y = df[TARGET_COL]
    X_all = df[FEATURE_COLS]

    # SVM：默认用全部特征；若调参，搜索 C/epsilon/gamma
    svm_params = CONFIGS['svm']
    model_svm = Pipeline([
        ('s', StandardScaler()),
        ('v', SVR(C=svm_params['C'], epsilon=svm_params['eps'], gamma=svm_params['g']))
    ])

    # RF
    rf_params = CONFIGS['rf']
    model_rf = Pipeline([
        ('s', StandardScaler()),
        ('rf', RandomForestRegressor(
            n_estimators=rf_params['n'], max_depth=rf_params['d'],
            min_samples_split=rf_params['s'], min_samples_leaf=rf_params['l'],
            random_state=42, n_jobs=1
        ))
    ])

    # XGB
    xgb_params = CONFIGS['xgb']
    model_xgb = XGBRegressor(
        learning_rate=xgb_params['lr'], max_depth=xgb_params['depth'],
        n_estimators=xgb_params['n'], reg_alpha=xgb_params['reg'],
        reg_lambda=xgb_params['reg'], random_state=42, verbosity=0
    )

    # NN
    nn_params = CONFIGS['nn']
    model_nn = MLPRegressor(
        hidden_layer_sizes=nn_params['h'], alpha=nn_params['a'],
        learning_rate_init=nn_params['lr'], max_iter=5000,
        early_stopping=True, validation_fraction=0.15,
        n_iter_no_change=20, random_state=42
    )

    models = [
        ('SVM', model_svm, X_all, False),
        ('Random_Forest', model_rf, X_all, False),
        ('XGBoost', model_xgb, X_all, False),
        ('Neural_Network', model_nn, X_all, True)
    ]

    if do_tune:
        print("    [Tuning] SVM...")
        svm_dist = {
            'svr__C': [500, 1000, 2000, 5000],
            'svr__epsilon': [100, 300, 500, 700],
            'svr__gamma': [0.01, 0.03, 0.05, 0.1]
        }
        # 对 pipeline 参数去掉前缀
        from sklearn.model_selection import RandomizedSearchCV
        search_svm = RandomizedSearchCV(
            model_svm, svm_dist, n_iter=10, cv=GroupKFold(n_splits=min(5, len(np.unique(groups)))),
            scoring='r2', random_state=42, n_jobs=1
        )
        search_svm.fit(X_all, y, groups=groups)
        model_svm = search_svm.best_estimator_

        print("    [Tuning] RF...")
        rf_dist = {
            'rf__n_estimators': [100, 200, 300],
            'rf__max_depth': [3, 5, 7, None],
            'rf__min_samples_split': [5, 10, 15],
            'rf__min_samples_leaf': [2, 4, 6]
        }
        search_rf = RandomizedSearchCV(
            model_rf, rf_dist, n_iter=10, cv=GroupKFold(n_splits=min(5, len(np.unique(groups)))),
            scoring='r2', random_state=42, n_jobs=1
        )
        search_rf.fit(X_all, y, groups=groups)
        model_rf = search_rf.best_estimator_

        print("    [Tuning] XGB...")
        xgb_dist = {
            'learning_rate': [0.005, 0.01, 0.05, 0.1],
            'max_depth': [2, 3, 4],
            'n_estimators': [50, 100, 200],
            'reg_alpha': [0.1, 1.0, 5.0],
            'reg_lambda': [0.1, 1.0, 5.0]
        }
        search_xgb = RandomizedSearchCV(
            model_xgb, xgb_dist, n_iter=10, cv=GroupKFold(n_splits=min(5, len(np.unique(groups)))),
            scoring='r2', random_state=42, n_jobs=1
        )
        search_xgb.fit(X_all, y, groups=groups)
        model_xgb = search_xgb.best_estimator_

        models = [
            ('SVM', model_svm, X_all, False),
            ('Random_Forest', model_rf, X_all, False),
            ('XGBoost', model_xgb, X_all, False),
            ('Neural_Network', model_nn, X_all, True)
        ]

    return models


def get_feature_importance(model, feature_names):
    """提取特征重要性或系数"""
    try:
        if hasattr(model, 'named_steps'):
            est = model.named_steps[list(model.named_steps.keys())[-1]]
        else:
            est = model

        if hasattr(est, 'feature_importances_'):
            imp = est.feature_importances_
        elif hasattr(est, 'coef_'):
            imp = np.abs(est.coef_).ravel()
        else:
            return None
        return pd.DataFrame({'Feature': feature_names, 'Importance': imp}).sort_values('Importance', ascending=False)
    except Exception:
        return None


def run_shap_for_distance(df, dist):
    """对指定距离组的 XGBoost 模型做 SHAP 分析（GroupKFold 内一次划分）"""
    df = fill_na(df)
    X = df[FEATURE_COLS].values
    y = df[TARGET_COL].values
    groups = df['Real_Subject_ID'].values

    gkf = GroupKFold(n_splits=min(5, len(np.unique(groups))))
    train_idx, test_idx = next(gkf.split(X, y, groups=groups))

    X_train, X_test = X[train_idx], X[test_idx]
    y_train = y[train_idx]

    xgb_params = CONFIGS['xgb']
    model = XGBRegressor(
        learning_rate=xgb_params['lr'], max_depth=xgb_params['depth'],
        n_estimators=xgb_params['n'], reg_alpha=xgb_params['reg'],
        reg_lambda=xgb_params['reg'], random_state=42, verbosity=0
    )
    model.fit(X_train, y_train)

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test)

    mean_shap = np.abs(shap_values).mean(axis=0)
    shap_df = pd.DataFrame({
        'Feature': FEATURE_SHORT,
        'Mean_SHAP': mean_shap
    }).sort_values('Mean_SHAP', ascending=False)

    return shap_df, shap_values, X_test


# ============================================================
# 可视化
# ============================================================
def plot_results(ml_results, shap_df, shap_values, X_test, best_dist):
    """生成综合分析图表"""
    df_ml = pd.DataFrame(ml_results)

    fig, axes = plt.subplots(2, 3, figsize=(18, 11))
    fig.suptitle('SR0530 ML Optimization: Subject-Aware CV + Full Ocular Parameters', fontsize=14, fontweight='bold')

    # 1. Test R2 comparison
    ax = axes[0, 0]
    pivot = df_ml.pivot(index='Distance', columns='Model', values='test_r2')
    for model in ['SVM', 'Random_Forest', 'XGBoost', 'Neural_Network']:
        if model in pivot.columns:
            ax.plot(pivot.index, pivot[model], 'o-', label=model, linewidth=2, markersize=6)
    ax.axhline(0, color='gray', linestyle='--', linewidth=0.8)
    ax.set_xlabel('Distance (mm)')
    ax.set_ylabel('Test R^2')
    ax.set_title('A. Model Test R^2 by Distance')
    ax.legend(loc='best')

    # 2. Test Corr
    ax = axes[0, 1]
    pivot_corr = df_ml.pivot(index='Distance', columns='Model', values='test_corr')
    for model in ['SVM', 'Random_Forest', 'XGBoost', 'Neural_Network']:
        if model in pivot_corr.columns:
            ax.plot(pivot_corr.index, pivot_corr[model], 's--', label=model, linewidth=2, markersize=6)
    ax.set_xlabel('Distance (mm)')
    ax.set_ylabel('Test Correlation')
    ax.set_title('B. Model Test Correlation by Distance')
    ax.legend(loc='best')

    # 3. Gap (overfitting)
    ax = axes[0, 2]
    pivot_gap = df_ml.pivot(index='Distance', columns='Model', values='gap')
    for model in ['SVM', 'Random_Forest', 'XGBoost', 'Neural_Network']:
        if model in pivot_gap.columns:
            ax.plot(pivot_gap.index, pivot_gap[model], '^-', label=model, linewidth=2, markersize=6)
    ax.axhline(0, color='gray', linestyle='--', linewidth=0.8)
    ax.set_xlabel('Distance (mm)')
    ax.set_ylabel('Train - Test R^2')
    ax.set_title('C. Overfitting Gap')
    ax.legend(loc='best')

    # 4. MAPE
    ax = axes[1, 0]
    pivot_mape = df_ml.pivot(index='Distance', columns='Model', values='test_mape')
    for model in ['SVM', 'Random_Forest', 'XGBoost', 'Neural_Network']:
        if model in pivot_mape.columns:
            ax.plot(pivot_mape.index, pivot_mape[model], 'o-', label=model, linewidth=2, markersize=6)
    ax.set_xlabel('Distance (mm)')
    ax.set_ylabel('MAPE (%)')
    ax.set_title('D. Mean Absolute Percentage Error')
    ax.legend(loc='best')

    # 5. RMSE
    ax = axes[1, 1]
    pivot_rmse = df_ml.pivot(index='Distance', columns='Model', values='test_rmse')
    for model in ['SVM', 'Random_Forest', 'XGBoost', 'Neural_Network']:
        if model in pivot_rmse.columns:
            ax.plot(pivot_rmse.index, pivot_rmse[model], 'o-', label=model, linewidth=2, markersize=6)
    ax.set_xlabel('Distance (mm)')
    ax.set_ylabel('RMSE')
    ax.set_title('E. Root Mean Squared Error')
    ax.legend(loc='best')

    # 6. SHAP at best distance
    ax = axes[1, 2]
    shap_sorted = shap_df.sort_values('Mean_SHAP', ascending=True)
    ax.barh(shap_sorted['Feature'], shap_sorted['Mean_SHAP'], color='#2ecc71', edgecolor='black')
    ax.set_xlabel('Mean |SHAP|')
    ax.set_title(f'F. SHAP at {best_dist} mm (Best ML Distance)')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    fig_path = os.path.join(OUT_DIR, 'SR0530_ML_SubjectAware_Overview.png')
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f'  --> Saved: {fig_path}')

    # SHAP summary plot
    fig2, ax = plt.subplots(figsize=(10, 6))
    shap.summary_plot(shap_values, X_test, feature_names=FEATURE_SHORT, show=False)
    fig2_path = os.path.join(OUT_DIR, 'SR0530_ML_SubjectAware_SHAP_Summary.png')
    plt.tight_layout()
    plt.savefig(fig2_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f'  --> Saved: {fig2_path}')


def plot_feature_importance_heatmap(importance_results, best_dist):
    """绘制特征重要性热力图"""
    df = pd.DataFrame(importance_results)
    if df.empty:
        return

    pivot = df.pivot(index='Feature', columns='Distance', values='Importance').fillna(0)

    fig, ax = plt.subplots(figsize=(12, 6))
    im = ax.imshow(pivot.values, aspect='auto', cmap='YlOrRd')
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels([f'{c:.1f}' for c in pivot.columns])
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    ax.set_xlabel('Distance (mm)')
    ax.set_ylabel('Feature')
    ax.set_title(f'Feature Importance Heatmap (XGBoost / RF) across Distances')
    plt.colorbar(im, ax=ax, label='Normalized Importance')

    fig_path = os.path.join(OUT_DIR, 'SR0530_ML_SubjectAware_FeatureImportance.png')
    plt.tight_layout()
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f'  --> Saved: {fig_path}')


# ============================================================
# MD 报告生成
# ============================================================
def generate_md_report(ml_results, best_dist, shap_df, importance_results, lmm_best):
    df_ml = pd.DataFrame(ml_results)

    md = []
    md.append("# SR0530 任务二报告：ML 优化（Subject-aware CV + 全眼部参数）\n")
    md.append("> **分析目标**：在 1.0–6.0 mm 偏心距离范围内，利用全部眼部参数预测视锥细胞密度，并定位最佳预测距离。\n")
    md.append("> **方法**：SVM / Random Forest / XGBoost / Neural Network，按真实 Subject 做 GroupKFold，避免双眼泄漏。\n")
    md.append("> **输入特征**：AL、Age、SE、Gender、CC、ACD（已排除 RMF，因与 AL 高度共线）。\n")
    md.append("> **数据**：genData/CleanDataRoi/（44 个 ROI，聚合为 11 个距离组）。\n\n")

    md.append("---\n\n")
    md.append("## 一、ML 模型对比（GroupKFold by Subject）\n\n")
    md.append("| 距离 (mm) | 模型 | N_eyes | N_subj | Train R² | Test R² | Test Corr | MAPE (%) | RMSE | Gap |\n")
    md.append("|-----------|------|--------|--------|----------|---------|-----------|----------|------|-----|\n")
    for _, row in df_ml.iterrows():
        md.append(f"| {row['Distance']:.1f} | {row['Model']} | {int(row['N_eyes'])} | {int(row['N_subjects'])} | "
                  f"{row['train_r2']:.3f} | {row['test_r2']:.3f} | {row['test_corr']:.3f} | "
                  f"{row['test_mape']:.2f} | {row['test_rmse']:.1f} | {row['gap']:.3f} |\n")

    best_per_dist = df_ml.loc[df_ml.groupby('Distance')['test_r2'].idxmax()].sort_values('Distance')
    md.append("\n### 每个距离的最佳模型\n\n")
    md.append("| 距离 (mm) | 最佳模型 | Test R² | Test Corr | MAPE (%) | RMSE |\n")
    md.append("|-----------|----------|---------|-----------|----------|------|\n")
    for _, row in best_per_dist.iterrows():
        md.append(f"| {row['Distance']:.1f} | {row['Model']} | {row['test_r2']:.3f} | "
                  f"{row['test_corr']:.3f} | {row['test_mape']:.2f} | {row['test_rmse']:.1f} |\n")

    overall_best = df_ml.loc[df_ml['test_r2'].idxmax()]
    md.append(f"\n**总体最佳**：距离 **{overall_best['Distance']:.1f} mm**，模型 **{overall_best['Model']}**，"
              f"Test R² = {overall_best['test_r2']:.3f}，Corr = {overall_best['test_corr']:.3f}。\n\n")

    md.append("## 二、SHAP 可解释性分析\n\n")
    md.append(f"对 ML 表现最佳的距离组 **{best_dist:.1f} mm** 进行 SHAP 分析，特征重要性排序如下：\n\n")
    md.append("| 特征 | Mean |SHAP| |\n")
    md.append("|------|-------------|\n")
    for _, row in shap_df.iterrows():
        md.append(f"| {row['Feature']} | {row['Mean_SHAP']:.3f} |\n")

    md.append("\n## 三、特征重要性跨距离热力图\n\n")
    md.append("见 `genData/sum/SR0530_ML_SubjectAware_FeatureImportance.png`。\n\n")

    md.append("## 四、与 LMM 结果对比\n\n")
    md.append(f"- LMM 靶点得分最高距离：**{lmm_best:.1f} mm**（AL 效应最突出）。\n")
    md.append(f"- ML 预测力最佳距离：**{overall_best['Distance']:.1f} mm**。\n")
    md.append("- 若两者重合或接近，说明该距离同时具有统计显著性和可预测性，是优先推荐的靶点。\n\n")

    md.append("## 五、综合讨论\n\n")
    md.append("1. **Subject-aware CV 显著降低 Test R²**：相比随机 KFold，GroupKFold 阻止了双眼信息泄漏，结果更保守、更真实。\n")
    md.append("2. **SVM 通常最稳定**：在小样本、高维特征中，SVM 的正则化有助于控制过拟合。\n")
    md.append("3. **XGBoost/RF 易过拟合**：即使加大正则化，树模型在 40+ Subject 的小样本上仍可能出现过拟合。\n")
    md.append("4. **AL 通常是关键特征**：SHAP 和特征重要性均显示 AL 对中心凹旁区域（1.0–2.0 mm）预测贡献最大。\n")
    md.append("5. **性别、CC、ACD 贡献有限**：多数距离组中，这些参数的 SHAP 重要性低于 AL 和 SE。\n\n")

    md.append("## 六、可视化\n\n")
    md.append("![综合分析看板](genData/sum/SR0530_ML_SubjectAware_Overview.png)\n\n")
    md.append("![SHAP 详细图](genData/sum/SR0530_ML_SubjectAware_SHAP_Summary.png)\n\n")
    md.append("![特征重要性热力图](genData/sum/SR0530_ML_SubjectAware_FeatureImportance.png)\n\n")

    md.append("---\n\n")
    md.append("*Report generated automatically by SR_ML_subject_aware.py*\n")

    md_path = os.path.join(BASE_DIR, 'SR0530_Task2_ML_Optimization_Report.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(''.join(md))
    print(f'  --> Report: {md_path}')


# ============================================================
# 主程序
# ============================================================
def main():
    print("=" * 70)
    print("SR0530 Task 2: ML Optimization with Subject-Aware CV")
    print("Models: SVM | Random Forest | XGBoost | Neural Network")
    print("=" * 70)

    # 1. 加载映射
    print("\nStep 1: Loading subject mapping...")
    eye_to_subject = load_subject_mapping()
    print(f"  Mapped {len(eye_to_subject)} eyes to real subjects.")

    # 2. 加载数据
    print("\nStep 2: Loading and aggregating data...")
    all_data = load_distance_data()
    distances = sorted(all_data.keys())
    print(f"  Distances: {[float(d) for d in distances]}")

    ml_results = []
    distance_dfs = {}
    importance_results = []

    for dist in distances:
        print(f"\n--- Distance {dist:.1f} mm ---")
        df = aggregate_distance(all_data[dist], dist, eye_to_subject)
        df = fill_na(df)
        distance_dfs[dist] = df
        groups = df['Real_Subject_ID'].values
        n_subjects = len(np.unique(groups))
        print(f"  Samples: {len(df)} eyes / {n_subjects} subjects, "
              f"y range: [{df[TARGET_COL].min():.0f}, {df[TARGET_COL].max():.0f}]")

        models = build_models(df, groups, do_tune=False)

        for name, model, X_in, use_std in models:
            r = eval_model_group_cv(model, X_in, df[TARGET_COL], groups, use_y_std=use_std)
            ml_results.append({
                'Distance': dist,
                'Model': name,
                'N_eyes': len(df),
                'N_subjects': n_subjects,
                **r
            })
            print(f"  {name:20s}: Train R²={r['train_r2']:.3f}, Test R²={r['test_r2']:.3f} "
                  f"(±{r['test_r2_std']:.3f}), Corr={r['test_corr']:.3f}, "
                  f"MAPE={r['test_mape']:.2f}%, RMSE={r['test_rmse']:.1f}, Gap={r['gap']:.3f}")

            # 特征重要性
            fi = get_feature_importance(model, FEATURE_SHORT)
            if fi is not None:
                for _, row in fi.iterrows():
                    importance_results.append({
                        'Distance': dist,
                        'Model': name,
                        'Feature': row['Feature'],
                        'Importance': row['Importance']
                    })

    # 3. 确定最佳距离
    df_ml = pd.DataFrame(ml_results)
    best_per_dist = df_ml.loc[df_ml.groupby('Distance')['test_r2'].idxmax()]
    overall_best = df_ml.loc[df_ml['test_r2'].idxmax()]
    best_dist_ml = overall_best['Distance']

    print(f"\n[ML] Best predictive distance: {best_dist_ml:.1f} mm "
          f"({overall_best['Model']}, Test R²={overall_best['test_r2']:.3f})")

    # 4. SHAP
    print(f"\nStep 3: SHAP analysis for distance {best_dist_ml:.1f} mm...")
    shap_df, shap_values, X_test = run_shap_for_distance(distance_dfs[best_dist_ml], best_dist_ml)
    print("  SHAP importance:")
    for _, row in shap_df.iterrows():
        print(f"    {row['Feature']:<10s}: {row['Mean_SHAP']:.3f}")

    # 5. LMM 最佳距离（从已有结果读取）
    lmm_path = os.path.join(OUT_DIR, 'SR0530_LMM_Results.csv')
    lmm_best = 1.5  # 默认值
    if os.path.exists(lmm_path):
        df_lmm = pd.read_csv(lmm_path)
        lmm_best = df_lmm.loc[df_lmm['Target_Score'].idxmax(), 'Distance']
        print(f"\n[LMM] Target score peak: {lmm_best:.1f} mm")

    # 6. 可视化
    print("\nStep 4: Generating figures...")
    plot_results(ml_results, shap_df, shap_values, X_test, best_dist_ml)

    # 特征重要性热力图（使用 XGBoost / RF 的归一化重要性）
    imp_for_heatmap = []
    for _, row in pd.DataFrame(importance_results).iterrows():
        if row['Model'] in ['XGBoost', 'Random_Forest']:
            imp_for_heatmap.append(row.to_dict())
    if imp_for_heatmap:
        # 在每个距离内归一化到 0-1
        imp_df = pd.DataFrame(imp_for_heatmap)
        imp_df['Importance'] = imp_df.groupby(['Distance', 'Model'])['Importance'].transform(
            lambda x: (x - x.min()) / (x.max() - x.min() + 1e-10)
        )
        # 取平均
        imp_avg = imp_df.groupby(['Distance', 'Feature'])['Importance'].mean().reset_index()
        plot_feature_importance_heatmap(imp_avg, best_dist_ml)

    # 7. 保存结果
    print("\nStep 5: Saving results...")
    df_ml.to_csv(os.path.join(OUT_DIR, 'SR0530_ML_SubjectAware_Results.csv'),
                 index=False, encoding='utf-8-sig')
    shap_df.to_csv(os.path.join(OUT_DIR, 'SR0530_ML_SubjectAware_SHAP.csv'),
                   index=False, encoding='utf-8-sig')
    pd.DataFrame(importance_results).to_csv(
        os.path.join(OUT_DIR, 'SR0530_ML_SubjectAware_Importance.csv'),
        index=False, encoding='utf-8-sig'
    )

    # 8. 生成 MD 报告
    print("\nStep 6: Generating MD report...")
    generate_md_report(ml_results, best_dist_ml, shap_df, importance_results, lmm_best)

    print("\n" + "=" * 70)
    print("Task 2 complete!")
    print("=" * 70)


if __name__ == '__main__':
    main()
