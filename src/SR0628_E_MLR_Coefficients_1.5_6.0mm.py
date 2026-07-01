"""
SR0628_E: 1.5–6.0 mm 偏心率上光感受器密度与眼部参数的多元线性回归系数

方法直接复制 SR_FigA_MLR_Split_71eyes.py 中 1.0 mm 的处理方式：
- 对每个距离分别按 Subject_ID + Eye 聚合象限
- 因变量：Linear cone density / Angular cone density
- 自变量：AL + Age + Gender + SER + K + ACD
- 使用普通最小二乘（OLS）拟合，输出各系数、P 值、标准误、95% CI、R²、样本量
"""
import os
import glob
import warnings
import numpy as np
import pandas as pd
import statsmodels.api as sm

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
# 让 PDF 中的文字以可编辑字体（Type 42 TrueType）嵌入
plt.rcParams['pdf.fonttype'] = 42

warnings.filterwarnings('ignore')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'genData', 'CleanDataRoi_lenient')
OUT_REPORT_DIR = os.path.join(BASE_DIR, 'report')
OUT_TABLE_DIR = os.path.join(OUT_REPORT_DIR, 'tables')
OUT_FIG_DIR = os.path.join(OUT_REPORT_DIR, 'FIG', 'SR0628_E')
os.makedirs(OUT_TABLE_DIR, exist_ok=True)
os.makedirs(OUT_FIG_DIR, exist_ok=True)

FEATURE_MAP = {
    'AL': 'Axial length (mm)',
    'Age': 'Age',
    'SE': 'Spherical equivalent refraction (D)',
    'Gender': 'Gender',
    'K': 'Corneal curvature (mm)',
    'ACD': 'Anterior chamber depth (mm)',
}
PREDICTORS = ['AL', 'Age', 'SE', 'Gender', 'K', 'ACD']
PREDICTOR_COLS = [FEATURE_MAP[p] for p in PREDICTORS]

LINEAR_DEN = 'Linear cone density (cones/ mm2)'
ANGULAR_DEN = 'Angular cone density (cones/ deg2)'
DIST_COL = 'Eccentricity (mm)'

TARGETS = {
    'Linear': LINEAR_DEN,
    'Angular': ANGULAR_DEN,
}


def load_distance_data(data_dir):
    all_data = {}
    for f in sorted(glob.glob(os.path.join(data_dir, 'data*.csv'))):
        df = pd.read_csv(f)
        dist = df[DIST_COL].iloc[0]
        if dist not in all_data:
            all_data[dist] = []
        all_data[dist].append(df)
    return all_data


def aggregate_distance(dfs):
    """对一个距离的所有 quadrant 数据取平均，每个 Eye 一行"""
    feature_cols = list(FEATURE_MAP.values())
    den_cols = [LINEAR_DEN, ANGULAR_DEN]
    df_all = pd.concat(dfs, ignore_index=True)
    agg_dict = {c: 'mean' for c in feature_cols + den_cols}
    df_sub = df_all.groupby(['Subject_ID', 'Eye'], as_index=False).agg(agg_dict)
    df_sub = df_sub.dropna(subset=feature_cols + den_cols)
    return df_sub


def fit_ols(df, target_col):
    """拟合 OLS，返回系数表等统计量"""
    y = df[target_col].values
    X = df[PREDICTOR_COLS].copy()
    X_const = sm.add_constant(X, has_constant='add')
    model = sm.OLS(y, X_const).fit()
    return model


def main():
    print("--- Loading lenient data ---")
    all_data = load_distance_data(DATA_DIR)
    target_dists = [d for d in sorted(all_data.keys()) if 1.5 <= d <= 6.0]
    print(f"Target distances: {target_dists}")

    rows = []
    for dist in target_dists:
        df = aggregate_distance(all_data[dist])
        n = len(df)
        print(f"\nDistance {dist:.1f} mm | n={n}")
        for target_name, target_col in TARGETS.items():
            fit = fit_ols(df, target_col)
            r2 = fit.rsquared
            adj_r2 = fit.rsquared_adj
            f_pvalue = fit.f_pvalue
            print(f"  {target_name}: R2={r2:.3f}, Adj R2={adj_r2:.3f}, F p={f_pvalue:.4g}")
            for pred_col in PREDICTOR_COLS:
                beta = fit.params[pred_col]
                se = fit.bse[pred_col]
                p = fit.pvalues[pred_col]
                ci_low, ci_high = fit.conf_int().loc[pred_col]
                rows.append({
                    'Distance_mm': dist,
                    'Density_Type': target_name,
                    'Predictor': pred_col,
                    'Beta': beta,
                    'SE': se,
                    'P_value': p,
                    'CI_Lower_95': ci_low,
                    'CI_Upper_95': ci_high,
                    'R2': r2,
                    'Adj_R2': adj_r2,
                    'F_pvalue': f_pvalue,
                    'N': n,
                })
            # 同时记录 Intercept
            beta0 = fit.params['const']
            se0 = fit.bse['const']
            p0 = fit.pvalues['const']
            ci0_low, ci0_high = fit.conf_int().loc['const']
            rows.append({
                'Distance_mm': dist,
                'Density_Type': target_name,
                'Predictor': 'Intercept',
                'Beta': beta0,
                'SE': se0,
                'P_value': p0,
                'CI_Lower_95': ci0_low,
                'CI_Upper_95': ci0_high,
                'R2': r2,
                'Adj_R2': adj_r2,
                'F_pvalue': f_pvalue,
                'N': n,
            })

    df_res = pd.DataFrame(rows)
    csv_path = os.path.join(OUT_TABLE_DIR, 'SR0628_E_MLR_Coefficients_1.5_6.0mm.csv')
    df_res.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"\nSaved coefficients CSV: {csv_path}")

    # 生成 Markdown 报告
    md = []
    md.append("# SR0628_E 1.5–6.0 mm 多元线性回归系数表\n\n")
    md.append("- **数据**：lenient（71 eyes / 46 subjects），按 `Subject_ID + Eye` 聚合象限\n")
    md.append("- **模型**：Density ~ AL + Age + Gender + SER + K + ACD\n")
    md.append("- **方法**：普通最小二乘（OLS），使用 `statsmodels`\n")
    md.append("- **因变量**：Linear cone density（cones/mm²）/ Angular cone density（cones/deg²）\n\n")

    for target_name in TARGETS.keys():
        md.append(f"## {target_name} Density\n\n")
        md.append("| Distance (mm) | Predictor | Beta | SE | P value | 95% CI | R² | Adj R² | N |\n")
        md.append("|---------------|-----------|------|----|---------|--------|----|--------|---|\n")
        sub = df_res[df_res['Density_Type'] == target_name].sort_values(['Distance_mm', 'Predictor'])
        for _, row in sub.iterrows():
            ci = f"[{row['CI_Lower_95']:.2f}, {row['CI_Upper_95']:.2f}]"
            p_str = f"{row['P_value']:.4f}" if row['P_value'] >= 0.0001 else "< 0.0001"
            md.append(f"| {row['Distance_mm']:.1f} | {row['Predictor']} | {row['Beta']:.3f} | "
                      f"{row['SE']:.3f} | {p_str} | {ci} | {row['R2']:.3f} | {row['Adj_R2']:.3f} | {int(row['N'])} |\n")
        md.append("\n")

    md.append("---\n\n")
    md.append("*Generated by src/SR0628_E_MLR_Coefficients_1.5_6.0mm.py*\n")

    md_path = os.path.join(OUT_REPORT_DIR, 'SR0628_E_MLR_Coefficients_1.5_6.0mm.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(''.join(md))
    print(f"Saved Markdown report: {md_path}")


if __name__ == '__main__':
    main()
