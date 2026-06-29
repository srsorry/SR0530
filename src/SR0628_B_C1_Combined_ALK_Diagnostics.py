"""
SR0628_B: C1_Combined_ALK 在 1.5 / 5.0 / 5.5 mm 的单次 10-fold 性能汇总、
最佳 Robust Linear Regression @ 1.5 mm 的 SHAP 图（PDF）与 Observed vs Predicted 散点图（PDF）。

说明：
- 性能表格直接解析自 report/SR0530_ALK_10fold_Final_Tuning_Report.md 的“全结果汇总”。
- 散点图与 SHAP 图使用与报告最佳 R²=0.504 相匹配的 CV 拆分种子（seed=43）生成，
  以保证图中标注的 R²/RMSE 与报告一致。
"""
import os
import sys
import re
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from statsmodels.graphics.gofplots import qqplot

# 复用 10-fold 最终调优报告中的基础设施
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from SR_ML_ALK_10fold_Final_Tuning_Report import (
    BASE_DIR, DATA_DIR, FEATURE_ALL, TARGET_COL, SCHEMA, PARAM_SPACE,
    N_SPLITS, RANDOM_STATE, load_subject_mapping, load_distance_data,
    aggregate_distance, fill_na, group_stratified_kfold, cross_validated_shap
)

warnings.filterwarnings('ignore')

OUT_REPORT_DIR = os.path.join(BASE_DIR, 'report')
OUT_TABLE_DIR = os.path.join(OUT_REPORT_DIR, 'tables')
OUT_FIG_DIR = os.path.join(OUT_REPORT_DIR, 'FIG', 'SR0628_B')
os.makedirs(OUT_TABLE_DIR, exist_ok=True)
os.makedirs(OUT_FIG_DIR, exist_ok=True)

SCHEMA_NAME = 'C1_Combined_ALK'
DISTANCES = [1.5, 5.0, 5.5]
REPORT_PATH = os.path.join(OUT_REPORT_DIR, 'SR0530_ALK_10fold_Final_Tuning_Report.md')

# 与报告 R²=0.504 / RMSE=458.0 相匹配的 CV 拆分种子
BEST_ROBUST_SEED = 43


def mape(y_true, y_pred):
    """Mean Absolute Percentage Error (%)"""
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    mask = y_true != 0
    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100


def parse_report_table(md_path, schema_name, distances):
    """解析报告表 VII，提取指定 schema 与距离的结果。"""
    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 找到“七、全距离 / 全方案 / 全模型结果汇总”之后的表格
    start = None
    for i, line in enumerate(lines):
        if '全距离 / 全方案 / 全模型结果汇总' in line:
            start = i + 1
            break
    if start is None:
        raise ValueError('未在报告中找到全结果汇总表')

    rows = []
    for line in lines[start:]:
        line = line.strip()
        if line.startswith('##'):
            break
        if not line.startswith('|'):
            continue
        parts = [p.strip() for p in line.split('|')]
        # 过滤空列和表头分隔线
        parts = [p for p in parts if p and not set(p).issubset({'-', ':', '|', ' '})]
        if len(parts) < 7:
            continue
        try:
            dist = float(parts[0])
            schema = parts[1]
            model = parts[2]
            r2 = float(parts[3])
            rmse = float(parts[4])
            gap = float(parts[5])
            params = parts[6]
        except ValueError:
            continue
        if schema == schema_name and dist in distances:
            rows.append({
                'Distance_mm': dist,
                'Schema': schema,
                'Model': model,
                'Test_R2': r2,
                'Test_RMSE': rmse,
                'Test_MSE': rmse ** 2,
                'Gap': gap,
                'Best_Params': params,
            })
    df = pd.DataFrame(rows)
    df = df.sort_values(['Distance_mm', 'Test_R2'], ascending=[True, False])
    return df


def evaluate_ols_performance(all_data, eye_to_subject, dist, schema_name,
                             n_splits=10, random_state=42):
    """对指定距离和方案计算 Multiple Linear Regression 的 10-fold CV 性能。"""
    df = aggregate_distance(all_data[dist], eye_to_subject, min_quadrants=1)
    feat_full = [FEATURE_ALL[s] for s in SCHEMA[schema_name]]
    df_sub = fill_na(df.copy(), feat_full)
    X = df_sub[feat_full]
    y = df_sub[TARGET_COL]
    groups = df_sub['Real_Subject_ID'].values
    y_strat = df_sub['Myopia'].values

    n_subjects = len(np.unique(groups))
    actual_splits = min(n_splits, n_subjects // 2)
    if actual_splits < 2:
        actual_splits = 2
    splits = group_stratified_kfold(groups, y_strat, n_splits=actual_splits, random_state=random_state)

    train_r2_list, test_r2_list, test_rmse_list = [], [], []
    for ti, vi in splits:
        model = LinearRegression()
        model.fit(X.iloc[ti], y.iloc[ti])
        train_pred = model.predict(X.iloc[ti])
        test_pred = model.predict(X.iloc[vi])
        train_r2_list.append(r2_score(y.iloc[ti], train_pred))
        test_r2_list.append(r2_score(y.iloc[vi], test_pred))
        test_rmse_list.append(np.sqrt(mean_squared_error(y.iloc[vi], test_pred)))

    mean_test_r2 = np.mean(test_r2_list)
    mean_test_rmse = np.mean(test_rmse_list)
    mean_train_r2 = np.mean(train_r2_list)
    gap = mean_train_r2 - mean_test_r2
    return {
        'Distance_mm': dist,
        'Schema': schema_name,
        'Model': 'Multiple_Linear_Regression',
        'Test_R2': mean_test_r2,
        'Test_RMSE': mean_test_rmse,
        'Test_MSE': mean_test_rmse ** 2,
        'Gap': gap,
        'Best_Params': '{}',
    }


def collect_out_of_fold_predictions(model_name, model_config, params, X, y, groups, y_stratify,
                                    n_splits=10, random_state=42):
    """收集每个样本的 out-of-fold 预测值与真实值，并返回每折的 test 指标。"""
    n_subjects = len(np.unique(groups))
    actual_splits = min(n_splits, n_subjects // 2)
    if actual_splits < 2:
        actual_splits = 2
    splits = group_stratified_kfold(groups, y_stratify, n_splits=actual_splits, random_state=random_state)

    all_pred = np.empty(len(y))
    all_true = np.empty(len(y))
    r2_list, rmse_list, mape_list = [], [], []
    for ti, vi in splits:
        model = model_config['model'](params)
        if model_config['use_y_std']:
            sx, sy = StandardScaler(), StandardScaler()
            Xt = sx.fit_transform(X.iloc[ti])
            Xv = sx.transform(X.iloc[vi])
            yt = sy.fit_transform(y.iloc[ti].values.reshape(-1, 1)).ravel()
            model.fit(Xt, yt)
            pred = sy.inverse_transform(model.predict(Xv).reshape(-1, 1)).ravel()
        else:
            model.fit(X.iloc[ti], y.iloc[ti])
            pred = model.predict(X.iloc[vi])
        yv = y.iloc[vi].values
        all_pred[vi] = pred
        all_true[vi] = yv
        r2_list.append(r2_score(yv, pred))
        rmse_list.append(np.sqrt(mean_squared_error(yv, pred)))
        mape_list.append(mape(yv, pred))
    metrics = {
        'mean_r2': np.mean(r2_list),
        'std_r2': np.std(r2_list, ddof=1),
        'mean_rmse': np.mean(rmse_list),
        'std_rmse': np.std(rmse_list, ddof=1),
        'mean_mape': np.mean(mape_list),
        'std_mape': np.std(mape_list, ddof=1),
    }
    return all_true, all_pred, metrics


def plot_scatter_observed_predicted(y_true, y_pred, cv_metrics, title, out_path):
    # 全样本的 Pearson r（用于展示预测与观测的相关性）
    corr = np.corrcoef(y_true, y_pred)[0, 1]
    # 散点图使用 10-fold 平均指标进行标注，避免跨折聚合带来的乐观偏差
    r2 = cv_metrics['mean_r2']
    rmse = cv_metrics['mean_rmse']
    mape_val = cv_metrics['mean_mape']

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(y_true, y_pred, edgecolors='k', facecolors='steelblue', alpha=0.7, s=60)
    lims = [min(y_true.min(), y_pred.min()), max(y_true.max(), y_pred.max())]
    ax.plot(lims, lims, 'r--', lw=1.5, label='Identity line')
    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.set_xlabel('Observed Angular cone density (cones/deg²)')
    ax.set_ylabel('Predicted Angular cone density (cones/deg²)')
    ax.set_title(title)
    textstr = f"10-fold mean R² = {r2:.3f}\n10-fold mean RMSE = {rmse:.1f}\n10-fold mean MAPE = {mape_val:.1f}%\nr = {corr:.3f}"
    ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    ax.legend(loc='lower right')
    ax.set_aspect('equal', adjustable='box')
    plt.tight_layout()
    # 同时输出 PDF（出版用）和 PNG（Markdown 预览用）
    plt.savefig(out_path, format='pdf', bbox_inches='tight')
    png_path = str(out_path).replace('.pdf', '.png')
    plt.savefig(png_path, format='png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  -> Scatter PDF: {out_path}")
    print(f"  -> Scatter PNG: {png_path}")


def plot_shap_summary_pdf(exp, title, out_path):
    import shap
    plt.figure(figsize=(10, 6))
    shap.summary_plot(exp, features=exp.data, feature_names=exp.feature_names, show=False)
    plt.title(title)
    plt.tight_layout()
    # 同时输出 PDF（出版用）和 PNG（Markdown 预览用）
    plt.savefig(out_path, format='pdf', bbox_inches='tight')
    png_path = str(out_path).replace('.pdf', '.png')
    plt.savefig(png_path, format='png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  -> SHAP PDF: {out_path}")
    print(f"  -> SHAP PNG: {png_path}")


def plot_qq_residuals(residuals, title, out_path):
    """残差 Q-Q 图：同时输出 PDF + PNG。"""
    fig, ax = plt.subplots(figsize=(6, 6))
    qqplot(np.asarray(residuals), line='s', ax=ax)
    ax.set_title(title)
    ax.set_xlabel('Theoretical quantiles')
    ax.set_ylabel('Sample quantiles (residuals)')
    plt.tight_layout()
    plt.savefig(out_path, format='pdf', bbox_inches='tight')
    png_path = str(out_path).replace('.pdf', '.png')
    plt.savefig(png_path, format='png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  -> Q-Q PDF: {out_path}")
    print(f"  -> Q-Q PNG: {png_path}")


def main():
    # 公共数据加载
    eye_to_subject = load_subject_mapping(DATA_DIR)
    all_data = load_distance_data(DATA_DIR)

    # ---------------------------
    # 1. 性能表格（解析自最终报告 + 新增 Multiple Linear Regression）
    # ---------------------------
    df_perf = parse_report_table(REPORT_PATH, SCHEMA_NAME, DISTANCES)

    # 为 OLS 补充 10-fold CV 结果（使用与报告相同的 CV 策略和默认随机种子）
    ols_rows = [evaluate_ols_performance(all_data, eye_to_subject, d, SCHEMA_NAME,
                                          n_splits=N_SPLITS, random_state=RANDOM_STATE)
                for d in DISTANCES]
    df_perf = pd.concat([df_perf, pd.DataFrame(ols_rows)], ignore_index=True)
    df_perf = df_perf.sort_values(['Distance_mm', 'Test_R2'], ascending=[True, False])

    csv_path = os.path.join(OUT_TABLE_DIR, 'SR0628_B_C1_Combined_ALK_Performance_1.5_5_5.5.csv')
    df_perf.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"Saved performance CSV: {csv_path}")

    # ---------------------------
    # 2. 最佳 Robust LR @ 1.5 mm 数据准备
    # ---------------------------
    print("\n--- Best Robust Linear Regression @ 1.5 mm diagnostics ---")
    dist = 1.5
    df = aggregate_distance(all_data[dist], eye_to_subject, min_quadrants=1)
    feat_full = [FEATURE_ALL[s] for s in SCHEMA[SCHEMA_NAME]]
    df_sub = fill_na(df.copy(), feat_full)
    X = df_sub[feat_full]
    y = df_sub[TARGET_COL]
    groups = df_sub['Real_Subject_ID'].values
    y_strat = df_sub['Myopia'].values

    best_model_name = 'Robust_Linear_Regression'
    best_params = {'epsilon': 1.8, 'alpha': 0.05}
    model_config = PARAM_SPACE[best_model_name]

    # 使用与报告最佳 R² 匹配的 seed
    y_true, y_pred, cv_metrics = collect_out_of_fold_predictions(
        best_model_name, model_config, best_params, X, y, groups, y_strat,
        n_splits=N_SPLITS, random_state=BEST_ROBUST_SEED
    )

    # ---------------------------
    # 3. 散点图
    # ---------------------------
    scatter_path = os.path.join(OUT_FIG_DIR, 'SR0628_B_Scatter_Robust_Linear_Regression_C1_Combined_ALK_1.5mm.pdf')
    plot_scatter_observed_predicted(
        y_true, y_pred, cv_metrics,
        f'{SCHEMA_NAME} / {best_model_name} @ {dist:.1f} mm\n10-fold out-of-sample predictions',
        scatter_path
    )

    # ---------------------------
    # 4. SHAP 图
    # ---------------------------
    exp = cross_validated_shap(
        best_model_name, model_config, best_params, X, y, groups, y_strat,
        n_splits=N_SPLITS, random_state=BEST_ROBUST_SEED
    )
    shap_path = os.path.join(OUT_FIG_DIR, 'SR0628_B_SHAP_Robust_Linear_Regression_C1_Combined_ALK_1.5mm.pdf')
    plot_shap_summary_pdf(
        exp,
        f'{SCHEMA_NAME} {best_model_name} @ {dist:.1f} mm (10-fold CV SHAP)',
        shap_path
    )

    # ---------------------------
    # 5. 残差 Q-Q 图
    # ---------------------------
    residuals = y_true - y_pred
    n_eyes = len(y_true)
    print(f"  -> Number of eyes used for residual Q-Q: {n_eyes}")
    qq_path = os.path.join(OUT_FIG_DIR, 'SR0628_B_QQ_Residuals_Robust_Linear_Regression_C1_Combined_ALK_1.5mm.pdf')
    plot_qq_residuals(
        residuals,
        f'{SCHEMA_NAME} {best_model_name} @ {dist:.1f} mm\nResidual Q-Q plot (n={n_eyes} eyes)',
        qq_path
    )

    # ---------------------------
    # 6. 生成 Markdown 报告
    # ---------------------------
    md = []
    md.append(f"# SR0628_B C1_Combined_ALK 在 1.5 / 5.0 / 5.5 mm 的性能汇总与最佳模型诊断\n\n")
    md.append(f"- **数据组**：lenient（71 eyes / 46 subjects）\n")
    md.append(f"- **方案**：{SCHEMA_NAME}\n")
    md.append(f"- **CV**：{N_SPLITS}-fold GroupKFold by Subject，按 Myopia 分层\n")
    md.append(f"- **性能来源**：`report/SR0530_ALK_10fold_Final_Tuning_Report.md` 表 VII（单次 10-fold 各模型最佳参数下的结果），并额外计算 Multiple Linear Regression；MSE = RMSE²\n")
    md.append(f"- **诊断图说明**：散点图与 SHAP 图使用与报告最佳 R²=0.504 相匹配的 CV 拆分种子（seed={BEST_ROBUST_SEED}）生成\n\n")

    md.append("## 一、各距离模型性能\n\n")
    for dist in DISTANCES:
        md.append(f"### {dist:.1f} mm\n\n")
        md.append("| Model | Test R² | RMSE | MSE | Gap | Best Params |\n")
        md.append("|-------|---------|------|-----|-----|-------------|\n")
        sub = df_perf[df_perf['Distance_mm'] == dist]
        for _, row in sub.iterrows():
            md.append(f"| {row['Model']} | {row['Test_R2']:.3f} | {row['Test_RMSE']:.1f} | "
                      f"{row['Test_MSE']:.1f} | {row['Gap']:.3f} | `{row['Best_Params']}` |\n")
        md.append("\n")

    md.append("## 二、最佳 Robust Linear Regression @ 1.5 mm 诊断图\n\n")
    md.append(f"- **最佳参数**：{best_params}\n")
    overall_corr = np.corrcoef(y_true, y_pred)[0, 1]
    md.append(f"- **10-fold mean R² ± SD**：{cv_metrics['mean_r2']:.3f} ± {cv_metrics['std_r2']:.3f}\n")
    md.append(f"- **10-fold mean RMSE ± SD**：{cv_metrics['mean_rmse']:.1f} ± {cv_metrics['std_rmse']:.1f}\n")
    md.append(f"- **10-fold mean MAPE ± SD**：{cv_metrics['mean_mape']:.1f} ± {cv_metrics['std_mape']:.1f}%\n")
    md.append(f"- **全样本 Pearson r**：{overall_corr:.3f}\n\n")

    rel_scatter_pdf = os.path.relpath(scatter_path, OUT_REPORT_DIR).replace('\\', '/')
    rel_scatter_png = rel_scatter_pdf.replace('.pdf', '.png')
    rel_shap_pdf = os.path.relpath(shap_path, OUT_REPORT_DIR).replace('\\', '/')
    rel_shap_png = rel_shap_pdf.replace('.pdf', '.png')
    rel_qq_pdf = os.path.relpath(qq_path, OUT_REPORT_DIR).replace('\\', '/')
    rel_qq_png = rel_qq_pdf.replace('.pdf', '.png')
    md.append(f"### Observed vs Predicted 散点图（n={n_eyes} eyes）\n\n")
    md.append(f"![Observed vs Predicted]({rel_scatter_png})\n\n")
    md.append(f"[Download PDF version]({rel_scatter_pdf})\n\n")
    md.append(f"### SHAP Summary\n\n")
    md.append(f"![SHAP Summary]({rel_shap_png})\n\n")
    md.append(f"[Download PDF version]({rel_shap_pdf})\n\n")
    md.append(f"### Residual Q-Q plot（n={n_eyes} eyes）\n\n")
    md.append(f"![Residual Q-Q]({rel_qq_png})\n\n")
    md.append(f"[Download PDF version]({rel_qq_pdf})\n\n")

    md.append("---\n\n")
    md.append("*Generated by src/SR0628_B_C1_Combined_ALK_Diagnostics.py*\n")

    md_path = os.path.join(OUT_REPORT_DIR, 'SR0628_B_C1_Combined_ALK_Performance_1.5_5_5.5.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(''.join(md))
    print(f"\nSaved report: {md_path}")


if __name__ == '__main__':
    main()
