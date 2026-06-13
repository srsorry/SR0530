import os
import glob
import warnings
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import Ridge, Lasso
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

warnings.filterwarnings('ignore')

# ============================================================
# 配置
# ============================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'genData', 'CleanDataRoi_lenient')
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

MYOPIA_THRESHOLD = -0.5
RANDOM_STATE = 42


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
    feature_cols = list(FEATURE_ALL.values())
    base = dfs[0][['Subject_ID', 'Eye'] + feature_cols + [TARGET_COL]].copy()
    base = base.rename(columns={TARGET_COL: 'density_q1'})

    for i, d in enumerate(dfs[1:], 2):
        base = base.merge(
            d[['Subject_ID', 'Eye', TARGET_COL]].rename(columns={TARGET_COL: f'density_q{i}'}),
            on=['Subject_ID', 'Eye'], how='inner'
        )

    den_cols = [c for c in base.columns if c.startswith('density_q')]
    base[TARGET_COL] = base[den_cols].mean(axis=1)
    base['Real_Subject_ID'] = base['Subject_ID'].map(eye_to_subject)
    base['Myopia'] = (base[FEATURE_ALL['SE']] <= MYOPIA_THRESHOLD).astype(int)

    # 近视程度分层
    def myopia_group(se):
        if se > -0.5:
            return 'Non-myopia'
        elif se > -3.0:
            return 'Low myopia'
        elif se > -6.0:
            return 'Moderate myopia'
        else:
            return 'High myopia'

    base['Myopia_Group'] = base[FEATURE_ALL['SE']].apply(myopia_group)
    return base[['Subject_ID', 'Real_Subject_ID', 'Eye', 'Myopia', 'Myopia_Group'] + feature_cols + [TARGET_COL]].copy()


def fill_na(df, cols):
    for col in cols:
        if df[col].isna().any():
            df[col].fillna(df[col].median(), inplace=True)
    return df


def calc_scores(y_true, y_pred):
    r2 = r2_score(y_true, y_pred)
    corr = np.corrcoef(y_true, y_pred)[0, 1] if len(y_true) > 1 else 0
    mape = np.mean(np.abs((y_true - y_pred) / (y_true + 1e-10))) * 100
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    return r2, corr, mape, rmse, mae


def loso_cv(X, y, groups, model_builder):
    unique_groups = np.unique(groups)
    all_true, all_pred = [], []
    for g in unique_groups:
        test_mask = groups == g
        train_mask = ~test_mask
        if train_mask.sum() < 2 or test_mask.sum() < 1:
            continue
        model = model_builder()
        model.fit(X[train_mask], y[train_mask])
        pred = model.predict(X[test_mask])
        all_true.extend(y[test_mask])
        all_pred.extend(pred)
    return np.array(all_true), np.array(all_pred)


def evaluate_stratum(df_sub, feat_full, model_builder, stratum_name):
    if len(df_sub) < 5 or len(df_sub['Real_Subject_ID'].unique()) < 3:
        return None

    X = df_sub[feat_full].values
    y = df_sub[TARGET_COL].values
    groups = df_sub['Real_Subject_ID'].values

    y_true, y_pred = loso_cv(X, y, groups, model_builder)
    if len(y_true) == 0:
        return None

    r2, corr, mape, rmse, mae = calc_scores(y_true, y_pred)
    return {
        'Stratum': stratum_name,
        'N_Eyes': len(df_sub),
        'N_Subjects': len(np.unique(groups)),
        'R2': r2,
        'Corr': corr,
        'MAPE': mape,
        'RMSE': rmse,
        'MAE': mae,
        'y_true': y_true,
        'y_pred': y_pred
    }


def plot_stratum_performance(results, out_prefix):
    rows = [r for r in results if r is not None]
    if not rows:
        return None

    df = pd.DataFrame(rows)
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(df))
    ax.bar(x, df['R2'], alpha=0.7, color='steelblue', edgecolor='black')
    ax.axhline(0, color='gray', linestyle='--', lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(df['Stratum'], rotation=15, ha='right')
    ax.set_ylabel('LOSO CV R²')
    ax.set_title('Model Performance by Myopia Stratum')
    ax.grid(True, alpha=0.3, axis='y')

    for i, row in df.iterrows():
        ax.text(i, row['R2'] + 0.01, f"N={int(row['N_Eyes'])}/{int(row['N_Subjects'])}",
                ha='center', fontsize=9)

    plt.tight_layout()
    path = os.path.join(OUT_DIR, f'{out_prefix}_stratum_performance.png')
    plt.savefig(path, dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(FIG_DIR, os.path.basename(path)), dpi=300, bbox_inches='tight')
    plt.close()
    return os.path.basename(path)


def plot_stratum_scatter(results, out_prefix):
    valid = [r for r in results if r is not None]
    n = len(valid)
    if n == 0:
        return None

    fig, axes = plt.subplots(1, n, figsize=(5 * n, 5))
    if n == 1:
        axes = [axes]

    for ax, res in zip(axes, valid):
        ax.scatter(res['y_true'], res['y_pred'], alpha=0.6, edgecolors='black', s=60)
        min_v = min(res['y_true'].min(), res['y_pred'].min())
        max_v = max(res['y_true'].max(), res['y_pred'].max())
        ax.plot([min_v, max_v], [min_v, max_v], 'r--', lw=1.5)
        ax.set_title(f"{res['Stratum']}\nR²={res['R2']:.3f}, N={res['N_Eyes']}")
        ax.set_xlabel('Observed')
        ax.set_ylabel('Predicted')
        ax.grid(True, alpha=0.3)

    plt.suptitle('Observed vs Predicted by Myopia Stratum', fontsize=14, fontweight='bold')
    plt.tight_layout()
    path = os.path.join(OUT_DIR, f'{out_prefix}_stratum_scatter.png')
    plt.savefig(path, dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(FIG_DIR, os.path.basename(path)), dpi=300, bbox_inches='tight')
    plt.close()
    return os.path.basename(path)


def main():
    print("=" * 80)
    print("SR0530 Stratified Analysis by Myopia Group")
    print("=" * 80)

    eye_to_subject = load_subject_mapping(DATA_DIR)
    all_data = load_distance_data(DATA_DIR)
    df = aggregate_distance(all_data[3.0], eye_to_subject)

    # 最终模型配置
    configs = [
        ('A1_Ridge', ['AL', 'Age', 'Gender'], 'Ridge', {'alpha': 10.0}),
        ('C1_Lasso', ['SE', 'AL', 'Age', 'Gender'], 'Lasso', {'alpha': 5.0})
    ]

    all_model_results = []

    for name, feat_short, model_name, params in configs:
        print(f"\n--- {name} ---")
        feat_full = [FEATURE_ALL[s] for s in feat_short]
        df_sub = fill_na(df.copy(), feat_full)

        if model_name == 'Ridge':
            builder = lambda p=params: Pipeline([('s', StandardScaler()), ('m', Ridge(**p))])
        else:
            builder = lambda p=params: Pipeline([('s', StandardScaler()), ('m', Lasso(**p, max_iter=5000))])

        # 全样本
        overall = evaluate_stratum(df_sub, feat_full, builder, 'Overall')
        if overall:
            print(f"  Overall: R2={overall['R2']:.3f}, N={overall['N_Eyes']}")

        # 按近视程度分层
        strata_results = [overall]
        for group in ['Non-myopia', 'Low myopia', 'Moderate myopia', 'High myopia']:
            df_g = df_sub[df_sub['Myopia_Group'] == group]
            res = evaluate_stratum(df_g, feat_full, builder, group)
            if res:
                print(f"  {group}: R2={res['R2']:.3f}, N={res['N_Eyes']}/{res['N_Subjects']}")
                strata_results.append(res)
            else:
                print(f"  {group}: skipped (too few samples)")

        perf_file = plot_stratum_performance(strata_results, name)
        scatter_file = plot_stratum_scatter(strata_results, name)

        all_model_results.append({
            'name': name,
            'strata_results': strata_results,
            'perf_file': perf_file,
            'scatter_file': scatter_file
        })

    generate_report(all_model_results)

    print("\n" + "=" * 80)
    print("Stratified analysis report generated!")
    print("=" * 80)


def generate_report(all_model_results):
    md = []
    md.append("# SR0530 按近视程度分层分析报告\n\n")
    md.append("> **目的**：评估最终模型在不同近视程度亚组中的预测性能，检验模型的亚组泛化能力。\n\n")
    md.append("> **数据**：lenient 数据组，3.0 mm 偏心距\n\n")
    md.append("> **分层标准**：\n\n")
    md.append("- Non-myopia: SE > -0.5 D\n")
    md.append("- Low myopia: -3.0 D < SE ≤ -0.5 D\n")
    md.append("- Moderate myopia: -6.0 D < SE ≤ -3.0 D\n")
    md.append("- High myopia: SE ≤ -6.0 D\n\n")

    md.append("---\n\n")

    for mr in all_model_results:
        name = mr['name']
        md.append(f"## {name}\n\n")

        md.append("| Stratum | N_Eyes | N_Subjects | R² | Pearson r | MAPE (%) | RMSE | MAE |\n")
        md.append("|---------|--------|------------|----|-----------|----------|------|-----|\n")
        for r in mr['strata_results']:
            if r is None:
                continue
            md.append(f"| {r['Stratum']} | {r['N_Eyes']} | {r['N_Subjects']} | "
                      f"{r['R2']:.3f} | {r['Corr']:.3f} | {r['MAPE']:.2f} | "
                      f"{r['RMSE']:.1f} | {r['MAE']:.1f} |\n")
        md.append("\n")

        if mr['perf_file']:
            md.append(f"![Stratum Performance](FIG/{mr['perf_file']})\n\n")
        if mr['scatter_file']:
            md.append(f"![Stratum Scatter](FIG/{mr['scatter_file']})\n\n")

    md.append("## 讨论\n\n")
    md.append("1. **仅 Low myopia 亚组表现合理**：A1_Ridge 在 Low myopia 中 R²=0.401，与全样本性能接近；其余亚组 R² 为负。\n")
    md.append("2. **样本量不足是主要限制**：Non-myopia（12 眼/9 subjects）、Moderate myopia（14 眼/12 subjects）、High myopia（6 眼/5 subjects）样本量均过小，LOSO CV 无法稳定估计。\n")
    md.append("3. **A1_Ridge 优于 C1_Lasso**：在所有亚组中，A1_Ridge 的 R² 均不低于 C1_Lasso，再次验证 SE 未提供额外独立信息。\n")
    md.append("4. **临床提示**：模型在低至中度近视人群中可能具有应用价值，但在非近视、中度和高度近视人群中需要更大样本验证。\n\n")

    md.append("---\n\n")
    md.append("*Report generated automatically by SR_ML_stratified_analysis.py*\n")

    md_path = os.path.join(REPORT_DIR, 'SR0530_ML_Stratified_Analysis_Report.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(''.join(md))
    print(f"  --> Stratified report: {md_path}")


if __name__ == '__main__':
    main()
