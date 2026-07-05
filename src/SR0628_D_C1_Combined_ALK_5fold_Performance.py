"""
SR0628_D: C1_Combined_ALK 在 1.5 / 5.0 / 5.5 mm 的 5-fold CV 性能汇总，
并参照 SR0628_B 的形式输出最佳模型 @ 1.5 mm 的诊断图（散点图、SHAP、残差 Q-Q）。

说明：
- 各模型使用 SR0530_ALK_5fold_Final_Tuning_Report.md（5-fold 结果）中的最佳超参数。
- 5-fold 采用 GroupKFold by Subject，按 Myopia 分层。
- 额外包含 Multiple Linear Regression。
"""
import os
import sys
import ast
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
# 让 PDF 中的文字以可编辑字体（Type 42 TrueType）嵌入，而非默认的 Type 3 轮廓字体
plt.rcParams['pdf.fonttype'] = 42
# Calibri 为首选字体；中文回退到 SimHei / Microsoft YaHei
plt.rcParams['font.sans-serif'] = ['Calibri', 'SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from statsmodels.graphics.gofplots import qqplot
import shap

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from SR_ML_ALK_10fold_Final_Tuning_Report import (
    BASE_DIR, DATA_DIR, FEATURE_ALL, TARGET_COL, SCHEMA, PARAM_SPACE,
    N_SPLITS, RANDOM_STATE, load_subject_mapping, load_distance_data,
    aggregate_distance, fill_na, group_stratified_kfold, evaluate_model,
    cross_validated_shap
)

warnings.filterwarnings('ignore')

OUT_REPORT_DIR = os.path.join(BASE_DIR, 'report')
OUT_TABLE_DIR = os.path.join(OUT_REPORT_DIR, 'tables')
OUT_FIG_DIR = os.path.join(OUT_REPORT_DIR, 'FIG', 'SR0628_D')
os.makedirs(OUT_TABLE_DIR, exist_ok=True)
os.makedirs(OUT_FIG_DIR, exist_ok=True)

SCHEMA_NAME = 'C1_Combined_ALK'
DISTANCES = [1.5, 5.0, 5.5]
FIVEFOLD_REPORT_PATH = os.path.join(OUT_REPORT_DIR, 'SR0530_ALK_5fold_Final_Tuning_Report.md')
OUT_PREFIX = 'SR0628_D_C1_Combined_ALK_5fold_Performance_1.5_5_5.5'
N_SPLITS_5 = 5


def mape(y_true, y_pred):
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    mask = y_true != 0
    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100


def parse_5fold_report_table(md_path, schema_name, distances):
    """解析 SR0530_ALK_5fold_Final_Tuning_Report.md 的全结果汇总表，
    提取指定 schema 与距离的最佳参数。
    表格列：距离 (mm) | 方案 | 模型 | Test R2 | RMSE | MAPE (%) | Gap | 最佳参数
    """
    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    start = None
    for i, line in enumerate(lines):
        if '全距离 / 全方案 / 全模型结果汇总' in line:
            start = i + 1
            break
    if start is None:
        raise ValueError('未在 5-fold 报告中找到全结果汇总表')

    records = []
    for line in lines[start:]:
        line = line.strip()
        if line.startswith('##'):
            break
        if not line.startswith('|'):
            continue
        parts = [p.strip() for p in line.split('|')]
        parts = [p for p in parts if p and not set(p).issubset({'-', ':', '|', ' '})]
        if len(parts) < 8:
            continue
        try:
            dist = float(parts[0])
            schema = parts[1]
            model = parts[2]
            r2 = float(parts[3])
            rmse = float(parts[4])
            # parts[5] = MAPE (%), skipped
            gap = float(parts[6])
            params_str = parts[7]
        except ValueError:
            continue
        if schema == schema_name and dist in distances:
            try:
                params = ast.literal_eval(params_str)
            except Exception:
                params = {}
            records.append({
                'Distance_deg': dist,
                'Schema': schema,
                'Model': model,
                'Test_R2_Report': r2,
                'Test_RMSE_Report': rmse,
                'Gap_Report': gap,
                'Best_Params': params,
            })
    return pd.DataFrame(records)


def evaluate_model_5fold(model_name, params, X, y, groups, y_stratify, n_splits=5, random_state=42):
    """对指定模型进行 5-fold CV 评估；Multiple Linear Regression 单独处理。"""
    if model_name == 'Multiple_Linear_Regression':
        use_y_std = False
        model_builder = lambda p: LinearRegression()
    else:
        cfg = PARAM_SPACE[model_name]
        use_y_std = cfg['use_y_std']
        model_builder = cfg['model']

    return evaluate_model(
        model_builder, params, X, y, groups, y_stratify,
        use_y_std=use_y_std, n_splits=n_splits, random_state=random_state
    )


def collect_out_of_fold_predictions(model_name, params, X, y, groups, y_stratify,
                                    n_splits=5, random_state=42):
    """收集 5-fold out-of-fold 预测值与真实值，并返回每折 test 指标。"""
    if model_name == 'Multiple_Linear_Regression':
        use_y_std = False
        model_builder = lambda p: LinearRegression()
    else:
        cfg = PARAM_SPACE[model_name]
        use_y_std = cfg['use_y_std']
        model_builder = cfg['model']

    n_subjects = len(np.unique(groups))
    actual_splits = min(n_splits, n_subjects // 2)
    if actual_splits < 2:
        actual_splits = 2
    splits = group_stratified_kfold(groups, y_stratify, n_splits=actual_splits, random_state=random_state)

    all_pred = np.empty(len(y))
    all_true = np.empty(len(y))
    r2_list, rmse_list, mape_list = [], [], []
    for ti, vi in splits:
        model = model_builder(params)
        if use_y_std:
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

    pooled_r2 = r2_score(all_true, all_pred)
    pooled_rmse = np.sqrt(mean_squared_error(all_true, all_pred))
    pooled_mape = mape(all_true, all_pred)
    metrics = {
        'mean_r2': np.mean(r2_list),      'std_r2': np.std(r2_list, ddof=1),
        'pooled_r2': pooled_r2,
        'mean_rmse': np.mean(rmse_list),  'std_rmse': np.std(rmse_list, ddof=1),
        'pooled_rmse': pooled_rmse,
        'mean_mape': np.mean(mape_list),  'std_mape': np.std(mape_list, ddof=1),
        'pooled_mape': pooled_mape,
    }
    return all_true, all_pred, metrics


def plot_scatter_observed_predicted(y_true, y_pred, cv_metrics, title, out_path):
    """仿 orgData/示意图-线性.png 风格：白底、黑圈、虚线为 Identity、实线为拟合线。"""
    corr = np.corrcoef(y_true, y_pred)[0, 1]
    r2 = cv_metrics.get('pooled_r2', cv_metrics['mean_r2'])
    rmse = cv_metrics.get('pooled_rmse', cv_metrics['mean_rmse'])
    mape_val = cv_metrics.get('pooled_mape', cv_metrics['mean_mape'])
    n = len(y_true)

    fig, ax = plt.subplots(figsize=(6, 6))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')

    # 坐标轴、刻度、标签设为黑色
    for spine in ax.spines.values():
        spine.set_color('black')
    ax.tick_params(colors='black', which='both')
    ax.xaxis.label.set_color('black')
    ax.yaxis.label.set_color('black')
    ax.title.set_color('black')

    # 散点：白底 + 黑边圆圈（n = 71）
    ax.scatter(y_true, y_pred, facecolors='white', edgecolors='black',
               s=70, linewidths=1.2, label='Data', zorder=3)

    lims = [min(y_true.min(), y_pred.min()), max(y_true.max(), y_pred.max())]
    # 留出 5% 边距，避免边缘点（大圆圈）被坐标轴裁切
    pad = 0.05 * (lims[1] - lims[0])
    lims = [lims[0] - pad, lims[1] + pad]

    # 虚线：Identity / 标准参考线
    ax.plot(lims, lims, 'k--', lw=1.5, label='Identity line', zorder=2)

    # 实线：实际估计线（观测-预测回归拟合）
    slope, intercept = np.polyfit(y_true, y_pred, 1)
    x_line = np.linspace(lims[0], lims[1], 100)
    y_line = slope * x_line + intercept
    ax.plot(x_line, y_line, 'k-', lw=2.5, label='Fitting line', zorder=2)

    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.set_xlabel('Observed Angular cone density (cones/deg²)')
    ax.set_ylabel('Predicted Angular cone density (cones/deg²)')
    ax.set_title(title)

    # 左上角标注 n 与指标
    textstr = f"n={n}\nR² = {r2:.3f}\nRMSE = {rmse:.1f}\nMAPE = {mape_val:.1f}%\nr = {corr:.3f}"
    ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=11,
            verticalalignment='top', color='black')

    ax.legend(loc='lower right', facecolor='white', edgecolor='black',
              labelcolor='black')
    ax.set_aspect('equal', adjustable='box')
    plt.tight_layout()
    plt.savefig(out_path, format='pdf', bbox_inches='tight', facecolor='white')
    png_path = str(out_path).replace('.pdf', '.png')
    plt.savefig(png_path, format='png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  -> Scatter PDF: {out_path}")
    print(f"  -> Scatter PNG: {png_path}")


def plot_shap_summary(exp, title, out_path):
    plt.figure(figsize=(10, 6))
    shap.summary_plot(exp, features=exp.data, feature_names=exp.feature_names, show=False)
    plt.title(title)
    plt.tight_layout()
    plt.savefig(out_path, format='pdf', bbox_inches='tight')
    png_path = str(out_path).replace('.pdf', '.png')
    plt.savefig(png_path, format='png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  -> SHAP PDF: {out_path}")
    print(f"  -> SHAP PNG: {png_path}")


def plot_qq_residuals(residuals, title, out_path):
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


def compute_y_std_per_distance(all_data, eye_to_subject, distances, min_quadrants=1):
    """计算每个距离上目标变量的标准差，用于标准化 RMSE/MSE。"""
    std_map = {}
    for dist in distances:
        df = aggregate_distance(all_data[dist], eye_to_subject, min_quadrants=min_quadrants)
        std_map[dist] = df[TARGET_COL].std(ddof=1)
    return std_map


def add_standardized_rmse_mse(df, std_map):
    """根据每个距离的目标变量标准差，添加 Test_RMSE_std 和 Test_MSE_std 列。"""
    df = df.copy()
    df['Y_Std'] = df['Distance_deg'].map(std_map)
    df['Test_RMSE_std'] = df['Test_RMSE'] / df['Y_Std']
    df['Test_MSE_std'] = df['Test_RMSE_std'] ** 2
    return df


def main():
    print("--- Loading 5-fold best params from SR0530_ALK_5fold_Final_Tuning_Report.md ---")
    df_params = parse_5fold_report_table(FIVEFOLD_REPORT_PATH, SCHEMA_NAME, DISTANCES)

    print("--- Loading data ---")
    eye_to_subject = load_subject_mapping(DATA_DIR)
    all_data = load_distance_data(DATA_DIR)
    feat_full = [FEATURE_ALL[s] for s in SCHEMA[SCHEMA_NAME]]

    # 性能表格：直接采用 5-fold 报告中的数值（这些数值来自原始 5-fold 寻优时的最佳 CV 拆分）
    rows = []
    for _, prow in df_params.iterrows():
        rows.append({
            'Distance_deg': prow['Distance_deg'],
            'Schema': SCHEMA_NAME,
            'Model': prow['Model'],
            'Test_R2': prow['Test_R2_Report'],
            'Test_RMSE': prow['Test_RMSE_Report'],
            'Test_MSE': prow['Test_RMSE_Report'] ** 2,
            'Gap': prow['Gap_Report'],
            'Best_Params': str(prow['Best_Params']),
        })

    # 额外补充 Multiple Linear Regression（无超参数），使用相同 5-fold CV 重新计算
    print(f"--- Adding Multiple Linear Regression ({N_SPLITS_5}-fold) ---")
    for dist in DISTANCES:
        df = aggregate_distance(all_data[dist], eye_to_subject, min_quadrants=1)
        df_sub = fill_na(df.copy(), feat_full)
        X = df_sub[feat_full]
        y = df_sub[TARGET_COL]
        groups = df_sub['Real_Subject_ID'].values
        y_strat = df_sub['Myopia'].values
        res_ols = evaluate_model_5fold(
            'Multiple_Linear_Regression', {}, X, y, groups, y_strat,
            n_splits=N_SPLITS_5, random_state=RANDOM_STATE
        )
        rows.append({
            'Distance_deg': dist,
            'Schema': SCHEMA_NAME,
            'Model': 'Multiple_Linear_Regression',
            'Test_R2': res_ols['test_r2'],
            'Test_RMSE': res_ols['test_rmse'],
            'Test_MSE': res_ols['test_rmse'] ** 2,
            'Gap': res_ols['gap'],
            'Best_Params': '{}',
        })
        print(f"  {dist:.1f}° | Multiple_Linear_Regression | Test R2={res_ols['test_r2']:+.3f} | RMSE={res_ols['test_rmse']:.1f} | Gap={res_ols['gap']:.3f}")

    df_perf = pd.DataFrame(rows)

    # 添加标准化 RMSE / MSE（按各距离目标变量标准差）
    y_std_map = compute_y_std_per_distance(all_data, eye_to_subject, DISTANCES)
    df_perf = add_standardized_rmse_mse(df_perf, y_std_map)

    df_perf = df_perf.sort_values(['Distance_deg', 'Test_R2'], ascending=[True, False])
    csv_path = os.path.join(OUT_TABLE_DIR, f'{OUT_PREFIX}.csv')
    df_perf.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"\nSaved 5-fold performance CSV: {csv_path}")

    # 最佳模型 @ 1.5 mm
    best_row = df_perf[df_perf['Distance_deg'] == 1.5].iloc[0]
    best_model_name = best_row['Model']
    best_params = ast.literal_eval(best_row['Best_Params']) if best_row['Best_Params'] != '{}' else {}
    print(f"\n--- Best model @ 1.5 mm: {best_model_name} ---")

    df = aggregate_distance(all_data[1.5], eye_to_subject, min_quadrants=1)
    df_sub = fill_na(df.copy(), feat_full)
    X = df_sub[feat_full]
    y = df_sub[TARGET_COL]
    groups = df_sub['Real_Subject_ID'].values
    y_strat = df_sub['Myopia'].values

    y_true, y_pred, cv_metrics = collect_out_of_fold_predictions(
        best_model_name, best_params, X, y, groups, y_strat,
        n_splits=N_SPLITS_5, random_state=RANDOM_STATE
    )

    # 散点图
    scatter_path = os.path.join(OUT_FIG_DIR, f'SR0628_D_Scatter_{best_model_name}_C1_Combined_ALK_1.5mm.pdf')
    plot_scatter_observed_predicted(
        y_true, y_pred, cv_metrics,
        f'{SCHEMA_NAME} / {best_model_name} @ 1.5 mm\n5-fold out-of-sample predictions',
        scatter_path
    )

    # SHAP 图
    if best_model_name == 'Multiple_Linear_Regression':
        # OLS 的 SHAP：用系数直接计算
        model = LinearRegression()
        model.fit(X, y)
        coefs = model.coef_
        exp_values = (X.values - X.values.mean(axis=0)) * coefs
        exp = shap.Explanation(
            values=exp_values,
            base_values=model.intercept_,
            data=X.values,
            feature_names=feat_full
        )
    else:
        exp = cross_validated_shap(
            best_model_name, PARAM_SPACE[best_model_name], best_params, X, y, groups, y_strat,
            n_splits=N_SPLITS_5, random_state=RANDOM_STATE
        )
    shap_path = os.path.join(OUT_FIG_DIR, f'SR0628_D_SHAP_{best_model_name}_C1_Combined_ALK_1.5mm.pdf')
    plot_shap_summary(
        exp,
        f'{SCHEMA_NAME} {best_model_name} @ 1.5 mm (5-fold CV SHAP)',
        shap_path
    )

    # 残差 Q-Q 图
    residuals = y_true - y_pred
    n_eyes = len(y_true)
    print(f"  -> Number of eyes used for residual Q-Q: {n_eyes}")
    qq_path = os.path.join(OUT_FIG_DIR, f'SR0628_D_QQ_Residuals_{best_model_name}_C1_Combined_ALK_1.5mm.pdf')
    plot_qq_residuals(
        residuals,
        f'{SCHEMA_NAME} {best_model_name} @ 1.5 mm\nResidual Q-Q plot (n={n_eyes} eyes)',
        qq_path
    )

    # Markdown 报告
    md = []
    md.append(f"# SR0628_D C1_Combined_ALK 在 1.5 / 5.0 / 5.5 mm 的 5-fold CV 性能汇总与最佳模型诊断\n\n")
    md.append(f"- **数据组**：lenient（71 eyes / 46 subjects）\n")
    md.append(f"- **方案**：{SCHEMA_NAME}\n")
    md.append(f"- **CV**：{N_SPLITS_5}-fold GroupKFold by Subject，按 Myopia 分层\n")
    md.append(f"- **超参数来源**：`report/SR0530_ALK_5fold_Final_Tuning_Report.md` 全结果汇总表中的 5-fold 最佳参数；MSE = RMSE²\n")
    md.append(f"- **诊断图说明**：使用默认随机种子 random_state={RANDOM_STATE} 重新生成，图中标注的 5-fold 均值可能与表中原始报告值略有差异（原始报告值为各模型 5-fold 寻优时的最佳 CV 结果）\n\n")

    md.append("## 一、各距离模型性能（5-fold）\n\n")
    md.append("> `RMSE_std` = RMSE / SD(y)，`MSE_std` = RMSE_std²；即目标变量标准化后的误差，便于跨研究比较。\n\n")
    for dist in DISTANCES:
        md.append(f"### {dist:.1f}°\n\n")
        md.append("| Model | Test R² | RMSE | MSE | RMSE_std | MSE_std | Gap | Best Params |\n")
        md.append("|-------|---------|------|-----|----------|---------|-----|-------------|\n")
        sub = df_perf[df_perf['Distance_deg'] == dist]
        for _, row in sub.iterrows():
            md.append(f"| {row['Model']} | {row['Test_R2']:.3f} | {row['Test_RMSE']:.1f} | "
                      f"{row['Test_MSE']:.1f} | {row['Test_RMSE_std']:.3f} | {row['Test_MSE_std']:.3f} | "
                      f"{row['Gap']:.3f} | `{row['Best_Params']}` |\n")
        md.append("\n")

    md.append(f"## 二、最佳 {best_model_name} @ 1.5 mm 诊断图\n\n")
    md.append(f"- **最佳参数**：{best_params}\n")
    overall_corr = np.corrcoef(y_true, y_pred)[0, 1]
    md.append(f"- **5-fold mean R² ± SD**：{cv_metrics['mean_r2']:.3f} ± {cv_metrics['std_r2']:.3f}\n")
    md.append(f"- **5-fold mean RMSE ± SD**：{cv_metrics['mean_rmse']:.1f} ± {cv_metrics['std_rmse']:.1f}\n")
    md.append(f"- **5-fold mean MAPE ± SD**：{cv_metrics['mean_mape']:.1f} ± {cv_metrics['std_mape']:.1f}%\n")
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
    md.append("*Generated by src/SR0628_D_C1_Combined_ALK_5fold_Performance.py*\n")

    md_path = os.path.join(OUT_REPORT_DIR, f'{OUT_PREFIX}.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(''.join(md))
    print(f"\nSaved 5-fold report: {md_path}")


if __name__ == '__main__':
    main()
