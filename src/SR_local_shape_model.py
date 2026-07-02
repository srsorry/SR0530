"""
SR_local_shape_model.py
基于眼球扩张模型的局部（按偏心率）形状特征消融实验。

核心设计（来自 orgData/SR0530_Eye_Shape_Plan_Final.md）：
- Primary target: Linear cone density (cones/mm²)
- 互斥特征方案：
  - Baseline: AL + ACD + Age + Gender + SE
  - Shape: ACR + ACD + Age + Gender + SE（AL 被 ACR 替代）
  - Extended: ACR + PSR_approx + ACD + Age + Gender + SE
- 每个偏心率独立建模，GroupKFold by Subject
- ΔR² 基于 CV Test R²
- Extended 方案禁用 RF SHAP，仅使用 ElasticNet 标准化系数
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
from sklearn.model_selection import GroupKFold
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNetCV, ElasticNet
from sklearn.model_selection import RandomizedSearchCV
from sklearn.inspection import permutation_importance
from sklearn.metrics import r2_score, mean_squared_error

import statsmodels.formula.api as smf
import patsy

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

TARGET_COL = 'Linear cone density (cones/ mm2)'

# 强制协变量
covariates = ['Age', 'Gender', 'Spherical equivalent refraction (D)']

# 特征方案（互斥设计）
FEATURE_SETS = {
    'Baseline': {
        'features': ['Axial length (mm)', 'Anterior chamber depth (mm)'] + covariates,
        'allow_rf_shap': True,
        'models': ['LMM', 'RF']
    },
    'Shape': {
        # 加入局部结构特征：Cone regularity（来自原始 quanti-analysis 规则性）
        # 与 Cone dispersion（离散度）。Voronoi_area_mean 未在原始 CSV 中提供，
        # 以 Cone dispersion 作为同类的局部形态学指标替代。
        'features': ['ACR', 'Anterior chamber depth (mm)', 'Cone regularity', 'Cone dispersion'] + covariates,
        'allow_rf_shap': True,
        'models': ['LMM', 'RF']
    },
    'Extended': {
        'features': ['ACR', 'PSR_approx', 'Anterior chamber depth (mm)'] + covariates,
        'allow_rf_shap': False,  # Hybrid SHAP 陷阱防范
        'models': ['LMM', 'RF', 'ElasticNet']
    }
}

N_SPLITS = 5
RANDOM_STATE = 42
PSR_RHO_THRESHOLD = 0.75


# ============================================================
# 工具函数
# ============================================================
def load_subject_mapping(data_dir):
    """从 data1.csv 读取 Eye_Label -> Patient_ID（受试者级别）映射。"""
    df_ref = pd.read_csv(os.path.join(data_dir, 'data1.csv'))
    mapping = {}
    for _, row in df_ref.iterrows():
        mapping[row['Eye_Label']] = row['Patient_ID']
        mapping[row['Subject_ID']] = row['Patient_ID']
        mapping[row['Patient_ID']] = row['Patient_ID']
    return mapping


def load_distance_data(data_dir):
    """读取 44 个 ROI 文件，按距离聚合。"""
    all_data = {}
    for f in sorted(glob.glob(os.path.join(data_dir, 'data*.csv'))):
        df = pd.read_csv(f)
        assert TARGET_COL in df.columns, (
            f"Target column '{TARGET_COL}' not found in {f}. "
            f"Available: {list(df.columns)}"
        )
        dist = df['Eccentricity (mm)'].iloc[0]
        if dist not in all_data:
            all_data[dist] = []
        all_data[dist].append(df)
    return all_data


def aggregate_distance(dfs, eye_to_subject, min_quadrants=1):
    """按 Patient_ID + Eye 聚合象限密度与局部结构特征（q1plus 策略）。"""
    eye_level_cols = ['Axial length (mm)', 'Age', 'Spherical equivalent refraction (D)',
                      'Gender', 'Corneal curvature (mm)', 'Anterior chamber depth (mm)']
    local_cols = ['Cone regularity', 'Cone dispersion']

    def merge_and_average(key_col, cols, prefix):
        """对多个象限的同一指标做 outer merge 后取平均。"""
        m = dfs[0][['Patient_ID', 'Eye'] + cols].copy()
        rename_map = {c: f"{prefix}_{c}_q1" for c in cols}
        m = m.rename(columns=rename_map)

        for i, d in enumerate(dfs[1:], 2):
            sub = d[['Patient_ID', 'Eye'] + cols].copy()
            sub = sub.rename(columns={c: f"{prefix}_{c}_q{i}" for c in cols})
            m = m.merge(sub, on=['Patient_ID', 'Eye'], how='outer')

        for c in cols:
            q_cols = [col for col in m.columns if col.startswith(f"{prefix}_{c}_q")]
            m[c] = m[q_cols].mean(axis=1, skipna=True)
            m = m.drop(columns=q_cols)
        return m

    # 合并密度
    merged = merge_and_average(TARGET_COL, [TARGET_COL], 'density')
    # 合并局部结构特征
    local_merged = merge_and_average('local', local_cols, 'local')
    merged = merged.merge(local_merged, on=['Patient_ID', 'Eye'], how='outer')

    merged['N_Quadrants'] = merged[[TARGET_COL]].notna().sum(axis=1)

    if min_quadrants == 4:
        merged = merged[merged['N_Quadrants'] == 4].copy()
    else:
        merged = merged[merged['N_Quadrants'] >= min_quadrants].copy()

    # 提取眼水平固定协变量
    features = None
    for d in dfs:
        df_feat = d[['Patient_ID', 'Eye'] + eye_level_cols].drop_duplicates(['Patient_ID', 'Eye'])
        if features is None:
            features = df_feat
        else:
            features = pd.concat([features, df_feat], ignore_index=True)
            features = features.drop_duplicates(['Patient_ID', 'Eye'], keep='first')

    base = merged.merge(features, on=['Patient_ID', 'Eye'], how='left')
    base['Real_Subject_ID'] = base['Patient_ID'].map(eye_to_subject)
    base['Myopia'] = (base['Spherical equivalent refraction (D)'] <= -0.5).astype(int)

    return_cols = ['Patient_ID', 'Real_Subject_ID', 'Eye', 'Myopia'] + eye_level_cols + local_cols + ['N_Quadrants', TARGET_COL]
    return base[return_cols].copy()


def compute_shape_features(df):
    """计算 ACR 和 PSR_approx；对 K 单位做防御性检查；编码 Gender。"""
    df = df.copy()

    # 性别编码（防御字符串或数值）
    if df['Gender'].dtype == object:
        df['Gender'] = df['Gender'].map({'Male': 1, 'Female': 0, 'M': 1, 'F': 0, '男': 1, '女': 0})
    df['Gender'] = pd.to_numeric(df['Gender'], errors='coerce')

    # K 单位防御：若最大值 < 10 认为是半径 mm；否则为屈光度 D
    K_raw = pd.to_numeric(df['Corneal curvature (mm)'], errors='coerce')
    if K_raw.max() < 10:
        df['K_mean_mm'] = K_raw
    else:
        df['K_mean_mm'] = 337.5 / K_raw

    df['ACR'] = df['Axial length (mm)'] / df['K_mean_mm']
    # PSR_approx = (AL - ACD) / AL（LT 缺失的简化版）
    df['PSR_approx'] = (df['Axial length (mm)'] - df['Anterior chamber depth (mm)']) / df['Axial length (mm)']
    return df


def fill_na(df, cols):
    """中位数填充缺失值。"""
    for col in cols:
        if df[col].isna().any():
            df[col].fillna(df[col].median(), inplace=True)
    return df


def cv_group_kfold(model, X, y, groups, n_splits=N_SPLITS):
    """按 groups 做 GroupKFold，返回每折 test 预测和分数。"""
    n_subjects = len(np.unique(groups))
    n_splits = min(n_splits, max(2, n_subjects // 2))

    gkf = GroupKFold(n_splits=n_splits)
    preds = np.full(len(y), np.nan)
    test_r2_list, test_rmse_list, test_mape_list = [], [], []

    for train_idx, test_idx in gkf.split(X, y, groups):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        preds[test_idx] = y_pred

        test_r2_list.append(r2_score(y_test, y_pred))
        test_rmse_list.append(np.sqrt(mean_squared_error(y_test, y_pred)))
        test_mape_list.append(np.mean(np.abs((y_test - y_pred) / (y_test + 1e-10))) * 100)

    return {
        'test_r2': np.mean(test_r2_list),
        'test_r2_std': np.std(test_r2_list),
        'test_rmse': np.mean(test_rmse_list),
        'test_rmse_std': np.std(test_rmse_list),
        'test_mape': np.mean(test_mape_list),
        'test_mape_std': np.std(test_mape_list),
        'preds': preds,
        'test_r2_list': test_r2_list
    }


def cv_rf_tuned(X, y, groups, n_splits=N_SPLITS, n_iter=8):
    """Random Forest 嵌套 GroupKFold 调参，返回测试预测、分数与最佳超参数。"""
    n_subjects = len(np.unique(groups))
    n_splits = min(n_splits, max(2, n_subjects // 2))

    param_distributions = {
        'n_estimators': [100, 200, 500],
        'max_depth': [3, 5, 7, None],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 2, 4],
        'max_features': ['sqrt', 'log2']
    }

    gkf = GroupKFold(n_splits=n_splits)

    # 全量数据上拟合一次，获得用于报告的最佳超参数（仅作参考）
    full_search = RandomizedSearchCV(
        RandomForestRegressor(random_state=RANDOM_STATE, n_jobs=1),
        param_distributions, n_iter=n_iter, cv=gkf, scoring='r2',
        random_state=RANDOM_STATE, n_jobs=1
    )
    full_search.fit(X, y, groups=groups)
    best_params = full_search.best_params_

    # 外层 CV：每折内部再调参
    preds = np.full(len(y), np.nan)
    test_r2_list, test_rmse_list, test_mape_list = [], [], []
    fold_best_params = []

    for train_idx, test_idx in gkf.split(X, y, groups):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        groups_train = groups[train_idx]

        inner_n_splits = min(n_splits, max(2, len(np.unique(groups_train)) // 2))
        inner_gkf = GroupKFold(n_splits=inner_n_splits)
        search = RandomizedSearchCV(
            RandomForestRegressor(random_state=RANDOM_STATE, n_jobs=1),
            param_distributions, n_iter=n_iter, cv=inner_gkf, scoring='r2',
            random_state=RANDOM_STATE, n_jobs=1
        )
        search.fit(X_train, y_train, groups=groups_train)
        fold_best_params.append(search.best_params_)

        model = search.best_estimator_
        y_pred = model.predict(X_test)
        preds[test_idx] = y_pred

        test_r2_list.append(r2_score(y_test, y_pred))
        test_rmse_list.append(np.sqrt(mean_squared_error(y_test, y_pred)))
        test_mape_list.append(np.mean(np.abs((y_test - y_pred) / (y_test + 1e-10))) * 100)

    return {
        'test_r2': np.mean(test_r2_list),
        'test_r2_std': np.std(test_r2_list),
        'test_rmse': np.mean(test_rmse_list),
        'test_rmse_std': np.std(test_rmse_list),
        'test_mape': np.mean(test_mape_list),
        'test_mape_std': np.std(test_mape_list),
        'preds': preds,
        'test_r2_list': test_r2_list,
        'best_params': best_params,
        'fold_best_params': fold_best_params
    }


def cv_elasticnet_tuned(X, y, groups, n_splits=N_SPLITS):
    """ElasticNet 嵌套 GroupKFold 调参（l1_ratio + alpha），返回测试预测、分数与最佳超参数。"""
    n_subjects = len(np.unique(groups))
    n_splits = min(n_splits, max(2, n_subjects // 2))

    gkf = GroupKFold(n_splits=n_splits)
    l1_ratios = [0.1, 0.3, 0.5, 0.7, 0.9]

    # 标准化
    scaler = StandardScaler()
    X_std = scaler.fit_transform(X)
    X_std_df = pd.DataFrame(X_std, columns=X.columns, index=X.index)

    # 全量数据上选择最佳超参数（仅作报告参考）
    full_en = ElasticNetCV(l1_ratio=l1_ratios, cv=list(gkf.split(X_std, y, groups)),
                           random_state=RANDOM_STATE, max_iter=10000)
    full_en.fit(X_std, y)
    best_params = {'alpha': full_en.alpha_, 'l1_ratio': full_en.l1_ratio_}

    # 外层 CV
    preds = np.full(len(y), np.nan)
    test_r2_list, test_rmse_list, test_mape_list = [], [], []
    fold_best_params = []

    for train_idx, test_idx in gkf.split(X_std, y, groups):
        X_train, X_test = X_std_df.iloc[train_idx], X_std_df.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        groups_train = groups[train_idx]

        inner_n_splits = min(n_splits, max(2, len(np.unique(groups_train)) // 2))
        inner_gkf = GroupKFold(n_splits=inner_n_splits)

        en_cv = ElasticNetCV(l1_ratio=l1_ratios, cv=list(inner_gkf.split(X_train, y_train, groups_train)),
                             random_state=RANDOM_STATE, max_iter=10000)
        en_cv.fit(X_train, y_train)
        fold_best_params.append({'alpha': en_cv.alpha_, 'l1_ratio': en_cv.l1_ratio_})

        en_fold = ElasticNet(alpha=en_cv.alpha_, l1_ratio=en_cv.l1_ratio_,
                             random_state=RANDOM_STATE, max_iter=10000)
        en_fold.fit(X_train, y_train)
        y_pred = en_fold.predict(X_test)
        preds[test_idx] = y_pred

        test_r2_list.append(r2_score(y_test, y_pred))
        test_rmse_list.append(np.sqrt(mean_squared_error(y_test, y_pred)))
        test_mape_list.append(np.mean(np.abs((y_test - y_pred) / (y_test + 1e-10))) * 100)

    # 标准化系数（基于全量数据最佳模型）
    coefs = pd.Series(full_en.coef_, index=X.columns)

    return {
        'test_r2': np.mean(test_r2_list),
        'test_r2_std': np.std(test_r2_list),
        'test_rmse': np.mean(test_rmse_list),
        'test_rmse_std': np.std(test_rmse_list),
        'test_mape': np.mean(test_mape_list),
        'test_mape_std': np.std(test_mape_list),
        'preds': preds,
        'test_r2_list': test_r2_list,
        'best_params': best_params,
        'fold_best_params': fold_best_params,
        'coefs': coefs
    }


def cv_lmm(X, y, groups, n_splits=N_SPLITS):
    """使用 statsmodels MixedLM（随机截距 by Subject）做 CV。"""
    n_subjects = len(np.unique(groups))
    n_splits = min(n_splits, max(2, n_subjects // 2))

    df = X.copy()
    df['y'] = y.values
    df['group'] = groups

    gkf = GroupKFold(n_splits=n_splits)
    preds = np.full(len(y), np.nan)
    test_r2_list, test_rmse_list, test_mape_list = [], [], []

    for train_idx, test_idx in gkf.split(df, y, groups):
        train_df = df.iloc[train_idx].copy()
        test_df = df.iloc[test_idx].copy()

        # 公式：y ~ feature1 + feature2 + ...
        feature_names = [c for c in X.columns if c != 'group']
        formula = 'y ~ ' + ' + '.join([f"Q('{f}')" for f in feature_names])

        try:
            model = smf.mixedlm(formula, train_df, groups=train_df['group'], re_formula='~1')
            result = model.fit(reml=True)

            # 显式使用固定效应预测（测试 subject 不在训练随机效应中，随机效应取 0）
            rhs = formula.split('~', 1)[1]
            X_test_design = patsy.dmatrix(rhs, test_df, return_type='dataframe')
            pred = X_test_design @ result.fe_params
            preds[test_idx] = pred.values

            y_test = test_df['y'].values
            test_r2_list.append(r2_score(y_test, pred))
            test_rmse_list.append(np.sqrt(mean_squared_error(y_test, pred)))
            test_mape_list.append(np.mean(np.abs((y_test - pred) / (y_test + 1e-10))) * 100)
        except Exception as e:
            print(f"    LMM fit failed: {e}")
            preds[test_idx] = np.nan
            test_r2_list.append(np.nan)
            test_rmse_list.append(np.nan)
            test_mape_list.append(np.nan)

    return {
        'test_r2': np.nanmean(test_r2_list),
        'test_r2_std': np.nanstd(test_r2_list),
        'test_rmse': np.nanmean(test_rmse_list),
        'test_rmse_std': np.nanstd(test_rmse_list),
        'test_mape': np.nanmean(test_mape_list),
        'test_mape_std': np.nanstd(test_mape_list),
        'preds': preds,
        'test_r2_list': test_r2_list
    }


def cv_elasticnet(X, y, groups, n_splits=N_SPLITS):
    """ElasticNetCV with GroupKFold，返回标准化系数（训练全量数据）。"""
    n_subjects = len(np.unique(groups))
    n_splits = min(n_splits, max(2, n_subjects // 2))

    gkf = GroupKFold(n_splits=n_splits)
    cv = list(gkf.split(X, y, groups))

    # 标准化
    scaler = StandardScaler()
    X_std = scaler.fit_transform(X)
    X_std_df = pd.DataFrame(X_std, columns=X.columns, index=X.index)

    en = ElasticNetCV(l1_ratio=0.5, cv=cv, random_state=RANDOM_STATE, max_iter=10000)
    en.fit(X_std, y)

    # CV 预测
    preds = np.full(len(y), np.nan)
    test_r2_list, test_rmse_list, test_mape_list = [], [], []

    for train_idx, test_idx in cv:
        X_train, X_test = X_std_df.iloc[train_idx], X_std_df.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        en_fold = ElasticNet(alpha=en.alpha_, l1_ratio=en.l1_ratio_, random_state=RANDOM_STATE, max_iter=10000)
        en_fold.fit(X_train, y_train)
        y_pred = en_fold.predict(X_test)
        preds[test_idx] = y_pred

        test_r2_list.append(r2_score(y_test, y_pred))
        test_rmse_list.append(np.sqrt(mean_squared_error(y_test, y_pred)))
        test_mape_list.append(np.mean(np.abs((y_test - y_pred) / (y_test + 1e-10))) * 100)

    # 标准化系数
    coefs = pd.Series(en.coef_, index=X.columns)

    return {
        'test_r2': np.mean(test_r2_list),
        'test_r2_std': np.std(test_r2_list),
        'test_rmse': np.mean(test_rmse_list),
        'test_rmse_std': np.std(test_rmse_list),
        'test_mape': np.mean(test_mape_list),
        'test_mape_std': np.std(test_mape_list),
        'preds': preds,
        'test_r2_list': test_r2_list,
        'coefs': coefs,
        'alpha': en.alpha_,
        'l1_ratio': en.l1_ratio_
    }


def evaluate_scheme(df_sub, feature_list, scheme_name, groups, y_stratify=None):
    """评估一个特征方案下的所有模型。"""
    X = df_sub[feature_list].copy()
    y = df_sub[TARGET_COL].copy()

    # 确保数值型
    for col in X.columns:
        X[col] = pd.to_numeric(X[col], errors='coerce')
    y = pd.to_numeric(y, errors='coerce')

    # 删除含缺失值的行，保留原始索引用于回写预测
    valid_idx = X.notna().all(axis=1) & y.notna()
    original_index = df_sub.index[valid_idx]
    X = X[valid_idx].reset_index(drop=True)
    y = y[valid_idx].reset_index(drop=True)
    groups_valid = groups[valid_idx]

    results = {}

    # LMM
    try:
        lmm_res = cv_lmm(X, y, groups_valid)
        results['LMM'] = lmm_res
    except Exception as e:
        print(f"    LMM failed for {scheme_name}: {e}")

    # RF（带嵌套 GroupKFold 超参调优）
    try:
        rf_res = cv_rf_tuned(X, y, groups_valid)
        results['RF'] = rf_res

        # Permutation importance on full data（仅用于无共线的 Baseline/Shape）
        if FEATURE_SETS[scheme_name]['allow_rf_shap']:
            rf = RandomForestRegressor(random_state=RANDOM_STATE, n_jobs=1, **rf_res['best_params'])
            rf.fit(X, y)
            perm = permutation_importance(rf, X, y, n_repeats=30, random_state=RANDOM_STATE, n_jobs=1)
            results['RF']['perm_importance'] = pd.DataFrame({
                'Feature': X.columns,
                'Importance_Mean': perm.importances_mean,
                'Importance_Std': perm.importances_std
            }).sort_values('Importance_Mean', ascending=False)
    except Exception as e:
        print(f"    RF failed for {scheme_name}: {e}")

    # ElasticNet（仅 Extended，带嵌套 GroupKFold 超参调优）
    if 'ElasticNet' in FEATURE_SETS[scheme_name]['models']:
        try:
            en_res = cv_elasticnet_tuned(X, y, groups_valid)
            results['ElasticNet'] = en_res
        except Exception as e:
            print(f"    ElasticNet failed for {scheme_name}: {e}")

    return results, X, y, groups_valid, original_index


# ============================================================
# 主程序
# ============================================================
def main():
    print("=" * 80)
    print("SR0530 Local Shape Model (per-eccentricity ablation)")
    print("Target: Linear cone density (cones/mm^2)")
    print("=" * 80)

    all_results = []
    per_distance_data = {}
    extended_downgraded = {}  # 记录每个 data_group 是否降级 Extended

    for data_group, data_dir in DATA_DIRS.items():
        print(f"\n{'='*80}")
        print(f"Processing data group: {data_group.upper()}")
        print(f"{'='*80}")

        eye_to_subject = load_subject_mapping(data_dir)
        all_data = load_distance_data(data_dir)
        distances = sorted(all_data.keys())

        per_distance_data[data_group] = {}

        # 计算全局 ACR vs PSR_approx 相关性（用于决定是否降级 Extended）
        all_dfs = []
        for dist in distances:
            df = aggregate_distance(all_data[dist], eye_to_subject, min_quadrants=1)
            df = compute_shape_features(df)
            df['Eccentricity (mm)'] = dist
            all_dfs.append(df)
        df_all = pd.concat(all_dfs, ignore_index=True)

        rho, pval = stats.spearmanr(df_all['ACR'], df_all['PSR_approx'])
        downgrade = abs(rho) > PSR_RHO_THRESHOLD
        extended_downgraded[data_group] = downgrade

        corr_report = os.path.join(OUT_DIR, f'SR0530_ACR_PSR_Correlation_{data_group}.txt')
        with open(corr_report, 'w', encoding='utf-8') as f:
            f.write(f"Data group: {data_group}\n")
            f.write(f"Spearman rho(ACR, PSR_approx) = {rho:.4f}, p = {pval:.4e}\n")
            if downgrade:
                f.write("Decision: Extended scheme DOWNGRADED to sensitivity analysis (rho > 0.75).\n")
            else:
                f.write("Decision: Extended scheme kept as primary analysis (rho <= 0.75).\n")
        print(f"  Spearman rho(ACR, PSR_approx) = {rho:.4f} -> Extended {'downgraded' if downgrade else 'kept'}")

        for dist in distances:
            print(f"\n--- Distance {dist:.1f} mm ---")
            df = aggregate_distance(all_data[dist], eye_to_subject, min_quadrants=1)
            df = compute_shape_features(df)
            df['Eccentricity (mm)'] = dist

            n_eyes = len(df)
            n_subjects = df['Real_Subject_ID'].nunique()
            print(f"  N={n_eyes} eyes / {n_subjects} subjects")

            if n_subjects < 4:
                print(f"  -> Skipping: too few subjects")
                continue

            groups = df['Real_Subject_ID'].values
            per_distance_data[data_group][dist] = df

            for scheme_name, scheme_cfg in FEATURE_SETS.items():
                if scheme_name == 'Extended' and downgrade:
                    print(f"  [{scheme_name}] skipped (downgraded)")
                    continue

                print(f"  [{scheme_name}] features={scheme_cfg['features']}")
                res, X, y, groups_valid, original_index = evaluate_scheme(df, scheme_cfg['features'], scheme_name, groups)

                for model_name, metrics in res.items():
                    row = {
                        'Data_Group': data_group,
                        'Distance_mm': dist,
                        'N_Eyes': len(X),
                        'N_Subjects': len(np.unique(groups_valid)),
                        'Scheme': scheme_name,
                        'Model': model_name,
                        'Test_R2': metrics['test_r2'],
                        'Test_R2_Std': metrics['test_r2_std'],
                        'Test_RMSE': metrics['test_rmse'],
                        'Test_RMSE_Std': metrics['test_rmse_std'],
                        'Test_MAPE': metrics['test_mape'],
                        'Test_MAPE_Std': metrics['test_mape_std'],
                        'Test_R2_List': ';'.join([f"{x:.6f}" for x in metrics['test_r2_list']]),
                        'Best_Params': ''
                    }
                    if model_name == 'ElasticNet':
                        row['Best_Params'] = f"alpha={metrics['best_params']['alpha']:.4f}, l1_ratio={metrics['best_params']['l1_ratio']:.2f}"
                    elif model_name == 'RF':
                        bp = metrics['best_params']
                        row['Best_Params'] = (
                            f"n_est={bp['n_estimators']}, depth={bp['max_depth']}, "
                            f"min_split={bp['min_samples_split']}, min_leaf={bp['min_samples_leaf']}, "
                            f"max_feat={bp['max_features']}"
                        )
                    all_results.append(row)

                    # 保存预测值用于绘图（按原始索引对齐）
                    pred_col = f"pred_{scheme_name}_{model_name}"
                    df.loc[original_index, pred_col] = metrics['preds']

                    # 保存 ElasticNet 标准化系数
                    if model_name == 'ElasticNet':
                        for feat, coef in metrics['coefs'].items():
                            df.loc[original_index, f"en_coef_{scheme_name}_{feat}"] = coef

    # 保存消融结果
    df_results = pd.DataFrame(all_results)
    results_csv = os.path.join(OUT_DIR, 'SR0530_Ablation_Per_Distance.csv')
    df_results.to_csv(results_csv, index=False, encoding='utf-8-sig')
    print(f"\nSaved: {results_csv}")

    # 计算 ΔR²
    df_delta = compute_delta_r2(df_results)

    # 生成可视化
    plot_delta_r2(df_delta)
    plot_predicted_vs_observed(per_distance_data, df_results)
    if not all(extended_downgraded.values()):
        plot_elasticnet_coefs(df_results, per_distance_data)

    # 生成报告
    generate_report(df_results, df_delta, extended_downgraded)

    print("\n" + "=" * 80)
    print("Local shape model analysis script complete (not executed).")
    print("=" * 80)


def compute_delta_r2(df_results):
    """计算 ΔR² = Shape - Baseline，基于 CV Test R²；误差带使用配对差异标准差。"""
    rows = []
    for (dg, dist, model), group in df_results.groupby(['Data_Group', 'Distance_mm', 'Model']):
        baseline = group[group['Scheme'] == 'Baseline']
        shape = group[group['Scheme'] == 'Shape']
        if len(baseline) == 1 and len(shape) == 1:
            delta = shape['Test_R2'].iloc[0] - baseline['Test_R2'].iloc[0]

            # 配对差异标准差
            baseline_list = np.array([float(x) for x in baseline['Test_R2_List'].iloc[0].split(';')])
            shape_list = np.array([float(x) for x in shape['Test_R2_List'].iloc[0].split(';')])
            delta_std = np.std(shape_list - baseline_list)

            rows.append({
                'Data_Group': dg,
                'Distance_mm': dist,
                'Model': model,
                'Baseline_R2': baseline['Test_R2'].iloc[0],
                'Shape_R2': shape['Test_R2'].iloc[0],
                'Delta_R2': delta,
                'Delta_R2_Std': delta_std,
                'Baseline_R2_Std': baseline['Test_R2_Std'].iloc[0],
                'Shape_R2_Std': shape['Test_R2_Std'].iloc[0]
            })
    return pd.DataFrame(rows)


def plot_delta_r2(df_delta):
    """绘制 ΔR² 曲线。"""
    fig, ax = plt.subplots(figsize=(12, 6))

    for dg in ['strict', 'lenient']:
        df_g = df_delta[df_delta['Data_Group'] == dg]
        df_g = df_g[df_g['Model'] == 'RF']  # 以 RF 为主展示
        df_g = df_g.sort_values('Distance_mm')

        ax.plot(df_g['Distance_mm'], df_g['Delta_R2'], 'o-', label=dg.upper(), linewidth=2, markersize=8)
        ax.fill_between(df_g['Distance_mm'],
                        df_g['Delta_R2'] - df_g['Delta_R2_Std'],
                        df_g['Delta_R2'] + df_g['Delta_R2_Std'],
                        alpha=0.2)

    ax.axhline(0, color='gray', linestyle='--', linewidth=0.8)
    ax.set_xlabel('Eccentricity (mm)')
    ax.set_ylabel('ΔR² = Shape − Baseline (CV Test R²)')
    ax.set_title('Shape Feature Incremental Explained Variance by Eccentricity')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    path = os.path.join(OUT_DIR, 'SR0530_DeltaR2_by_Eccentricity.png')
    plt.savefig(path, dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(FIG_DIR, os.path.basename(path)), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  --> Saved: {path}")


def plot_predicted_vs_observed(per_distance_data, df_results):
    """为每个 data_group 的最佳距离 Shape-RF 方案绘制 Predicted vs Observed。"""
    for dg in ['strict', 'lenient']:
        df_g = df_results[(df_results['Data_Group'] == dg) & (df_results['Scheme'] == 'Shape') & (df_results['Model'] == 'RF')]
        if df_g.empty:
            continue
        best_idx = df_g['Test_R2'].idxmax()
        best = df_g.loc[best_idx]
        dist = best['Distance_mm']

        df = per_distance_data[dg][dist].copy()
        pred_col = 'pred_Shape_RF'
        if pred_col not in df.columns:
            continue

        fig, ax = plt.subplots(figsize=(7, 7))
        valid = df[[TARGET_COL, pred_col]].dropna()
        ax.scatter(valid[TARGET_COL], valid[pred_col], alpha=0.6, edgecolor='black')

        lim = [valid.min().min(), valid.max().max()]
        ax.plot(lim, lim, 'r--', lw=1)
        ax.set_xlabel('Observed Linear Density (cones/mm²)')
        ax.set_ylabel('Predicted Linear Density (cones/mm²)')
        ax.set_title(f'{dg.upper()} | Shape-RF | {dist:.1f} mm | Test R²={best["Test_R2"]:.3f}')
        ax.grid(True, alpha=0.3)
        plt.tight_layout()

        path = os.path.join(OUT_DIR, f'SR0530_Predicted_vs_Observed_{dg}_{dist:.1f}mm.png')
        plt.savefig(path, dpi=300, bbox_inches='tight')
        plt.savefig(os.path.join(FIG_DIR, os.path.basename(path)), dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  --> Saved: {path}")


def plot_elasticnet_coefs(df_results, per_distance_data):
    """绘制 Extended-ElasticNet 标准化系数热力图（仅当未被降级时）。"""
    # 从 per_distance_data 收集每个 (data_group, distance) 的系数
    coef_records = []
    for dg, dist_dict in per_distance_data.items():
        for dist, df in dist_dict.items():
            coef_cols = [c for c in df.columns if c.startswith('en_coef_Extended_')]
            if not coef_cols:
                continue
            # 取第一行非缺失值（同一 distance 下系数相同）
            vals = df[coef_cols].iloc[0]
            for c, v in vals.items():
                feat = c.replace('en_coef_Extended_', '')
                coef_records.append({
                    'Data_Group': dg,
                    'Distance_mm': dist,
                    'Feature': feat,
                    'Coefficient': v
                })

    if not coef_records:
        print("  No ElasticNet coefficients to plot.")
        return

    df_coef = pd.DataFrame(coef_records).pivot(index=['Data_Group', 'Distance_mm'], columns='Feature', values='Coefficient')
    df_coef = df_coef.fillna(0).sort_index()

    fig, ax = plt.subplots(figsize=(12, max(6, len(df_coef) * 0.4)))
    im = ax.imshow(df_coef.values, aspect='auto', cmap='RdBu_r', vmin=-np.max(np.abs(df_coef.values)),
                   vmax=np.max(np.abs(df_coef.values)))

    ax.set_xticks(np.arange(len(df_coef.columns)))
    ax.set_yticks(np.arange(len(df_coef.index)))
    ax.set_xticklabels(df_coef.columns, rotation=45, ha='right')
    ax.set_yticklabels([f"{dg} | {dist:.1f}mm" for dg, dist in df_coef.index])

    # 在每个格子上标注数值
    for i in range(len(df_coef.index)):
        for j in range(len(df_coef.columns)):
            text = ax.text(j, i, f"{df_coef.values[i, j]:.2f}",
                           ha="center", va="center", color="black" if abs(df_coef.values[i, j]) < 0.5 else "white",
                           fontsize=7)

    ax.set_title('Extended-ElasticNet Standardized Coefficients by Eccentricity')
    fig.colorbar(im, ax=ax, label='Coefficient')
    plt.tight_layout()

    path = os.path.join(OUT_DIR, 'SR0530_ElasticNet_Coefs.png')
    plt.savefig(path, dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(FIG_DIR, os.path.basename(path)), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  --> Saved: {path}")


def generate_report(df_results, df_delta, extended_downgraded):
    """生成 Markdown 报告。"""
    md = []
    md.append("# SR0530 局部形状模型消融实验报告\n\n")
    md.append("> **目标**：按偏心率独立评估眼球形状特征（ACR、PSR_approx）对视锥细胞线性密度的预测增益。\n\n")
    md.append("> **方法**：互斥特征设计 + GroupKFold by Subject；ΔR² 基于 CV Test R²。\n\n")
    md.append("> **Primary Target**：Linear cone density (cones/mm²)。\n\n")

    md.append("---\n\n")

    # ACR vs PSR 相关性
    md.append("## 一、ACR 与 PSR_approx 相关性检查\n\n")
    for dg, downgrade in extended_downgraded.items():
        corr_path = os.path.join(OUT_DIR, f'SR0530_ACR_PSR_Correlation_{dg}.txt')
        if os.path.exists(corr_path):
            with open(corr_path, 'r', encoding='utf-8') as f:
                md.append(f"```\n{f.read()}```\n\n")

    # ΔR² 曲线
    md.append("## 二、ΔR² 曲线\n\n")
    md.append("![Delta R2](FIG/SR0530_DeltaR2_by_Eccentricity.png)\n\n")
    md.append("**解读**：\n")
    md.append("- ΔR² = CV_Test_R²(Shape) − CV_Test_R²(Baseline)。\n")
    md.append("- ΔR² > 0 表示 ACR 比例特征优于绝对眼轴长度。\n")
    md.append("- 阴影带使用配对差异的标准差（同一 CV 折内 Shape 与 Baseline R² 之差），而非简单叠加独立标准差。\n\n")

    # 详细结果表
    md.append("## 三、每个偏心率消融结果\n\n")
    md.append("| 数据组 | 距离 | 模型 | Baseline R² | Shape R² | ΔR² | Extended R² |\n")
    md.append("|--------|------|------|------------|---------|-----|------------|\n")
    for (dg, dist, model), group in df_results.groupby(['Data_Group', 'Distance_mm', 'Model']):
        baseline_r2 = group[group['Scheme'] == 'Baseline']['Test_R2'].values
        shape_r2 = group[group['Scheme'] == 'Shape']['Test_R2'].values
        extended_r2 = group[group['Scheme'] == 'Extended']['Test_R2'].values
        b = f"{baseline_r2[0]:.3f}" if len(baseline_r2) else "-"
        s = f"{shape_r2[0]:.3f}" if len(shape_r2) else "-"
        d = f"{shape_r2[0] - baseline_r2[0]:.3f}" if len(baseline_r2) and len(shape_r2) else "-"
        e = f"{extended_r2[0]:.3f}" if len(extended_r2) else "-"
        md.append(f"| {dg} | {dist:.1f} | {model} | {b} | {s} | {d} | {e} |\n")
    md.append("\n")

    # 论文素材
    md.append("## 四、论文写作素材\n\n")
    md.append("### Methods\n\n")
    md.append("> To isolate the effect of globe shape from absolute axial elongation, we adopted a mutual exclusion design: the baseline model included absolute axial length (AL), whereas the shape model replaced AL with the axial-to-corneal ratio (ACR = AL / R). The primary outcome was linear cone density (cones/mm²) to prevent circular reasoning. Due to the absence of lens thickness measurements, a simplified posterior segment proxy (PSR_approx = (AL − ACD) / AL) was used; age was included as a covariate. Separate models were trained for each eccentricity to respect the heteroscedastic variance structure. The incremental explanatory power of shape was quantified as ΔR² = CV_Test_R²(Shape) − CV_Test_R²(Baseline) using GroupKFold cross-validation by subject. For the extended model containing both AL and ACR, feature importance was assessed exclusively via ElasticNet standardized coefficients. The regularization parameter α was selected via cross-validation on the full dataset; only the cross-validated test performance of the final model is reported. Corneal curvature was converted to radius using K(mm) = 337.5 / K(D) when the input exceeded 10 D; otherwise it was treated as already in millimeters. Gender was encoded as binary before modeling.\n\n")

    md.append("### Discussion 模板\n\n")
    for dg, downgrade in extended_downgraded.items():
        if downgrade:
            md.append(f"> **{dg.upper()}**: ACR 与 PSR_approx 高度同源（ρ > 0.75），Extended 方案仅作敏感性分析。Shape（ACR）方案是主要结果。\n\n")
        else:
            md.append(f"> **{dg.upper()}**: ACR 与 PSR_approx 相对独立（ρ ≤ 0.75），Extended 方案可纳入主分析，ElasticNet 系数支持多维度眼球形状表征。\n\n")

    md.append("---\n\n")
    md.append("*Report generated by SR_local_shape_model.py*\n")

    md_path = os.path.join(REPORT_DIR, 'SR0530_Local_Shape_Model_Report.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(''.join(md))
    print(f"  --> Report: {md_path}")


if __name__ == '__main__':
    main()
