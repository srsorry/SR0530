"""
SR_update_hp_report_with_ci.py
基于现有 HP 寻优结果 CSV，为报告补充 Test R² 的 95% CI（t 分布近似），并重新生成 Markdown 报告。
注意：当前 CSV 未保存 RMSE 的 fold-level 标准差，因此 RMSE 暂无法补充 95% CI。
"""

import os
import numpy as np
import pandas as pd
from scipy import stats

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE_DIR, 'genData', 'sum')
REPORT_DIR = os.path.join(BASE_DIR, 'report')
FIG_DIR = os.path.join(REPORT_DIR, 'FIG')
MODE_LABEL = 'q1plus'
N_FOLDS = 5
ALPHA = 0.05


def compute_t_ci(mean, std, n_folds=N_FOLDS, alpha=ALPHA):
    """基于 fold 级均值与标准差计算 t 分布近似 95% CI。"""
    if pd.isna(std) or n_folds < 2:
        return np.nan, np.nan
    se = std / np.sqrt(n_folds)
    t_val = stats.t.ppf(1 - alpha / 2, df=n_folds - 1)
    return mean - t_val * se, mean + t_val * se


def fmt_r2_ci(row):
    lo, hi = compute_t_ci(row['test_r2'], row['test_r2_std'])
    return f"{row['test_r2']:.3f}<br>[{lo:.3f}, {hi:.3f}]"


def fmt_rmse_ci(row):
    if 'test_rmse_std' in row and pd.notna(row['test_rmse_std']):
        lo, hi = compute_t_ci(row['test_rmse'], row['test_rmse_std'])
        return f"{row['test_rmse']:.1f}<br>[{lo:.1f}, {hi:.1f}]"
    return f"{row['test_rmse']:.1f}"


def generate_report_with_ci(df_results, mode_label='q1plus'):
    mode_desc = {
        'q4': '≥4 象限完整（不放宽，inner merge）',
        'q1plus': '≥1 象限可用（放宽，outer merge 取平均）'
    }.get(mode_label, mode_label)

    md = []
    md.append(f"# SR0530 ML 超参数寻优报告（{mode_desc}）\n\n")
    md.append("> **目标**：针对每种 ML 方法，在 strict（69 眼）和 lenient（71 眼）两套数据上做超参数寻优，比较最佳参数与结果。\n\n")
    md.append("> **搜索策略**：Random Search + GroupKFold by Subject，每模型 30 组参数\n\n")
    md.append(f"> **象限策略**：{mode_desc}\n\n")
    md.append("> **数据组**：`CleanDataRoi_strict/`（任意 ROI >7000 剔除）和 `CleanDataRoi_lenient/`（距离平均 >7000 剔除）\n\n")
    md.append("> **置信区间说明**：Test R² 与 RMSE 后的 95% CI 均基于 5-fold CV 的 fold-level 标准差，使用 t 分布近似（t₀.₀₂₅,₄ = 2.776）。若某列无 std，则该列不附 CI。\n\n")

    md.append("---\n\n")

    # 一、搜索空间（保持不变，从原脚本复制）
    md.append("## 一、参数搜索空间\n\n")
    md.append("| 模型 | 参数 | 搜索范围 |\n")
    md.append("|------|------|---------|\n")
    md.append("| SVM | C | 100, 500, 1000, 2000, 5000 |\n")
    md.append("| SVM | epsilon | 100, 300, 500, 800, 1000 |\n")
    md.append("| SVM | gamma | 0.001, 0.005, 0.01, 0.03, 0.05, 0.1 |\n")
    md.append("| Random_Forest | n_estimators | 50, 100, 200, 300 |\n")
    md.append("| Random_Forest | max_depth | 2, 3, 4, 5, None |\n")
    md.append("| Random_Forest | min_samples_split | 2, 5, 10 |\n")
    md.append("| Random_Forest | min_samples_leaf | 1, 2, 4 |\n")
    md.append("| XGBoost | learning_rate | 0.001, 0.005, 0.01, 0.05, 0.1 |\n")
    md.append("| XGBoost | max_depth | 1, 2, 3, 4 |\n")
    md.append("| XGBoost | n_estimators | 30, 50, 100, 200 |\n")
    md.append("| XGBoost | reg_alpha | 0.1, 0.5, 1.0, 2.0 |\n")
    md.append("| XGBoost | reg_lambda | 0.1, 0.5, 1.0, 2.0 |\n")
    md.append("| Neural_Network | hidden_layer_sizes | (40,), (60,), (80,), (100,), (80, 40) |\n")
    md.append("| Neural_Network | alpha | 0.1, 0.3, 0.5, 1.0 |\n")
    md.append("| Neural_Network | learning_rate_init | 0.0001, 0.0005, 0.001 |\n")
    md.append("| Lasso | alpha | 0.001, 0.01, 0.1, 1.0, 10.0 |\n")
    md.append("| ElasticNet | alpha | 0.001, 0.01, 0.1, 1.0 |\n")
    md.append("| ElasticNet | l1_ratio | 0.1, 0.3, 0.5, 0.7, 0.9 |\n")
    md.append("| Ridge | alpha | 0.01, 0.1, 1.0, 10.0, 100.0 |\n")

    # 二、总体最佳配置
    md.append("\n## 二、总体最佳配置\n\n")
    best_row = df_results.loc[df_results['test_r2'].idxmax()]
    r2_lo, r2_hi = compute_t_ci(best_row['test_r2'], best_row['test_r2_std'])
    rmse_ci_str = ""
    if 'test_rmse_std' in best_row and pd.notna(best_row['test_rmse_std']):
        rmse_lo, rmse_hi = compute_t_ci(best_row['test_rmse'], best_row['test_rmse_std'])
        rmse_ci_str = f" [95% CI: {rmse_lo:.1f}, {rmse_hi:.1f}]"
    md.append(f"- **数据组**：{best_row['Data_Group']}\n")
    md.append(f"- **距离**：{best_row['Distance_mm']:.1f} mm\n")
    md.append(f"- **方案**：{best_row['Schema']}\n")
    md.append(f"- **模型**：{best_row['Model']}\n")
    md.append(f"- **最佳 Test R²**：{best_row['test_r2']:.3f} [95% CI: {r2_lo:.3f}, {r2_hi:.3f}]\n")
    md.append(f"- **最佳 RMSE**：{best_row['test_rmse']:.1f}{rmse_ci_str}\n")
    md.append(f"- **最佳参数**：{best_row['Best_Params']}\n")
    md.append(f"- **样本量**：{int(best_row['N_Eyes'])} 眼 / {int(best_row['N_Subjects'])} subjects\n\n")

    # 三、每个数据组的最佳结果
    md.append("## 三、每个数据组的最佳结果（按距离）\n\n")
    for data_group in ['strict', 'lenient']:
        md.append(f"### {data_group.upper()} 数据组\n\n")
        md.append("| 距离 (mm) | 最佳方案 | 最佳模型 | Test R² (95% CI) | MAPE (%) | RMSE (95% CI) | Gap | 最佳参数 |\n")
        md.append("|-----------|---------|---------|------------------|----------|----------------|-----|---------|\n")

        df_g = df_results[df_results['Data_Group'] == data_group]
        for dist in sorted(df_g['Distance_mm'].unique()):
            df_d = df_g[df_g['Distance_mm'] == dist]
            best = df_d.loc[df_d['test_r2'].idxmax()]
            r2_lo, r2_hi = compute_t_ci(best['test_r2'], best['test_r2_std'])
            rmse_ci_str = f"{best['test_rmse']:.1f}"
            if 'test_rmse_std' in best and pd.notna(best['test_rmse_std']):
                rmse_lo, rmse_hi = compute_t_ci(best['test_rmse'], best['test_rmse_std'])
                rmse_ci_str = f"{best['test_rmse']:.1f} [{rmse_lo:.1f}, {rmse_hi:.1f}]"
            md.append(f"| {best['Distance_mm']:.1f} | {best['Schema']} | {best['Model']} | "
                      f"{best['test_r2']:.3f} [{r2_lo:.3f}, {r2_hi:.3f}] | {best['test_mape']:.2f} | "
                      f"{rmse_ci_str} | {best['gap']:.3f} | `{best['Best_Params']}` |\n")
        md.append("\n")

    # 四、每个模型在每个数据组的最佳结果
    md.append("## 四、每个模型在每个数据组的最佳结果\n\n")
    md.append("| 数据组 | 模型 | 最佳距离 | 最佳方案 | Test R² (95% CI) | MAPE (%) | 最佳参数 |\n")
    md.append("|--------|------|---------|---------|------------------|----------|---------|\n")
    for data_group in ['strict', 'lenient']:
        df_g = df_results[df_results['Data_Group'] == data_group]
        for model_name in sorted(df_g['Model'].unique()):
            df_m = df_g[df_g['Model'] == model_name]
            best = df_m.loc[df_m['test_r2'].idxmax()]
            r2_lo, r2_hi = compute_t_ci(best['test_r2'], best['test_r2_std'])
            md.append(f"| {data_group} | {model_name} | {best['Distance_mm']:.1f} mm | {best['Schema']} | "
                      f"{best['test_r2']:.3f} [{r2_lo:.3f}, {r2_hi:.3f}] | {best['test_mape']:.2f} | "
                      f"`{best['Best_Params']}` |\n")
    md.append("\n")

    # 五、每个方案的最佳结果
    md.append("## 五、每个特征方案的最佳结果\n\n")
    md.append("| 方案 | 数据组 | 最佳距离 | 最佳模型 | Test R² (95% CI) |\n")
    md.append("|------|--------|---------|---------|------------------|\n")
    for schema_name in df_results['Schema'].unique():
        df_s = df_results[df_results['Schema'] == schema_name]
        best = df_s.loc[df_s['test_r2'].idxmax()]
        r2_lo, r2_hi = compute_t_ci(best['test_r2'], best['test_r2_std'])
        md.append(f"| {schema_name} | {best['Data_Group']} | {best['Distance_mm']:.1f} mm | {best['Model']} | "
                  f"{best['test_r2']:.3f} [{r2_lo:.3f}, {r2_hi:.3f}] |\n")
    md.append("\n")

    # 六、详细结果表
    md.append("## 六、全部详细结果\n\n")
    md.append("| 数据组 | 距离 | 方案 | 模型 | N_Eyes | N_Subj | Train R² | Test R² (95% CI) | Corr | MAPE | RMSE (95% CI) | Gap | 最佳参数 |\n")
    md.append("|--------|------|------|------|--------|--------|----------|------------------|------|------|----------------|-----|---------|\n")
    for _, row in df_results.iterrows():
        r2_lo, r2_hi = compute_t_ci(row['test_r2'], row['test_r2_std'])
        rmse_ci_str = f"{row['test_rmse']:.1f}"
        if 'test_rmse_std' in row and pd.notna(row['test_rmse_std']):
            rmse_lo, rmse_hi = compute_t_ci(row['test_rmse'], row['test_rmse_std'])
            rmse_ci_str = f"{row['test_rmse']:.1f} [{rmse_lo:.1f}, {rmse_hi:.1f}]"
        md.append(f"| {row['Data_Group']} | {row['Distance_mm']:.1f} | {row['Schema']} | {row['Model']} | "
                  f"{int(row['N_Eyes'])} | {int(row['N_Subjects'])} | {row['train_r2']:.3f} | "
                  f"{row['test_r2']:.3f} [{r2_lo:.3f}, {r2_hi:.3f}] | {row['test_corr']:.3f} | {row['test_mape']:.2f} | "
                  f"{rmse_ci_str} | {row['gap']:.3f} | `{row['Best_Params']}` |\n")

    # 七、可视化
    md.append("\n## 七、可视化\n\n")
    md.append(f"### Strict 数据组：Distance × Model 热图 ({mode_label})\n\n")
    md.append(f"![Strict Heatmap](FIG/SR0530_HP_Tuning_Heatmap_strict_{mode_label}.png)\n\n")
    md.append(f"### Lenient 数据组：Distance × Model 热图 ({mode_label})\n\n")
    md.append(f"![Lenient Heatmap](FIG/SR0530_HP_Tuning_Heatmap_lenient_{mode_label}.png)\n\n")
    md.append(f"### Strict vs Lenient 各模型对比 ({mode_label})\n\n")
    md.append(f"![Strict vs Lenient](FIG/SR0530_HP_Tuning_Strict_vs_Lenient_{mode_label}.png)\n\n")
    md.append(f"### 方案对比 ({mode_label})\n\n")
    md.append(f"![Schema Comparison](FIG/SR0530_HP_Tuning_SchemaComparison_{mode_label}.png)\n\n")

    # 八、讨论
    md.append("## 八、讨论\n\n")
    md.append("1. **数据组差异**：strict 模式移除了局部 ROI 异常值，数据更干净；lenient 模式保留了更多样本但可能混入异常。\n")
    md.append("2. **最佳参数稳定性**：如果某模型在 strict 和 lenient 下的最佳参数差异很大，提示该模型对异常值敏感。\n")
    md.append("3. **方案选择**：各方案表现因距离和数据组而异，最佳方案需结合 Test R²、Gap 和参数稳定性综合判断，具体见上述结果表。\n")
    md.append("4. **置信区间解释**：R² 与 RMSE 的 95% CI 反映 5-fold CV fold 间变异；R² CI 跨越 0 或 RMSE CI 范围过大，均提示该配置泛化能力不稳定。\n\n")

    md.append("---\n\n")
    md.append("*Report generated automatically by SR_update_hp_report_with_ci.py*\n")

    md_path = os.path.join(REPORT_DIR, f'SR0530_ML_Hyperparameter_Tuning_{mode_label}_Report.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(''.join(md))
    print(f"  --> Report: {md_path}")


def main():
    csv_path = os.path.join(OUT_DIR, f'SR0530_HP_Tuning_Results_{MODE_LABEL}.csv')
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"结果 CSV 不存在：{csv_path}")

    df_results = pd.read_csv(csv_path)
    print(f"Loaded {len(df_results)} rows from {csv_path}")

    # 确保 test_r2_std 存在
    if 'test_r2_std' not in df_results.columns:
        raise ValueError("CSV 中缺少 test_r2_std 列，无法计算 R² CI")

    generate_report_with_ci(df_results, mode_label=MODE_LABEL)
    print("HP report updated with 95% CI for R2.")


if __name__ == '__main__':
    main()
