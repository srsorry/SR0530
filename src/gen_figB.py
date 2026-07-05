#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
SR0530 Figure B：基于 lenient 71 眼 1.0° 聚合数据
- FIGB1：SE vs AL 散点 + 线性回归
- FIGB2：GEE 多因素回归森林图（标准化 β 系数）
================================================================================
"""

import pandas as pd
import matplotlib
matplotlib.use('Agg')  # 非交互后端，适合服务器/批处理运行
import matplotlib.pyplot as plt
# 让 PDF 中的文字以可编辑字体（Type 42 TrueType）嵌入，而非默认的 Type 3 轮廓字体
plt.rcParams['pdf.fonttype'] = 42
# Calibri 为首选字体；中文回退到 SimHei / Microsoft YaHei
plt.rcParams['font.sans-serif'] = ['Calibri', 'SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
import seaborn as sns
from scipy import stats
import os
import re
import sys
import statsmodels.api as sm
import statsmodels.formula.api as smf
import numpy as np

# 强制 stdout 使用 UTF-8，避免 Windows 终端中文乱码
sys.stdout.reconfigure(encoding='utf-8')

# ================= 配置区 =================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'genData', 'CleanDataRoi_lenient')
OUTPUT_DIR = os.path.join(BASE_DIR, 'report', 'FIG', 'FIGB')
SUM_DIR = os.path.join(BASE_DIR, 'genData', 'sum')

OUTPUT_PDF1 = os.path.join(OUTPUT_DIR, 'FIGB1.pdf')
OUTPUT_PDF2 = os.path.join(OUTPUT_DIR, 'FIGB2.pdf')
OUTPUT_CSV = os.path.join(SUM_DIR, 'SR0530_FigB2_GEE_Results.csv')

ANGULAR_OUTLIER_THRESHOLD = 1e4  # 与 FigA 保持一致


def load_1mm_aggregated(data_dir):
    """
    读取 CleanDataRoi_lenient 下全部 44 个 ROI 文件，
    按 Subject_ID + Eccentricity 聚合（象限取平均），返回 1.0 mm 的 DataFrame。
    """
    if not os.path.exists(data_dir):
        raise FileNotFoundError(f"找不到数据目录: {data_dir}")

    file_paths = sorted(
        [os.path.join(data_dir, f) for f in os.listdir(data_dir)
         if f.startswith('data') and f.endswith('.csv')],
        key=lambda f: int(re.search(r'\d+', os.path.basename(f)).group())
    )
    if not file_paths:
        raise FileNotFoundError(f"在 {data_dir} 中未找到 data*.csv 文件")

    dfs = [pd.read_csv(fp) for fp in file_paths]
    df_all = pd.concat(dfs, ignore_index=True)

    # 全局异常值剔除
    n_before = len(df_all)
    df_all = df_all[df_all['Angular cone density (cones/ deg2)'] <= ANGULAR_OUTLIER_THRESHOLD].copy()
    n_after = len(df_all)
    if n_before != n_after:
        print(f"[WARN] 全局异常值剔除: {n_before - n_after} 行 (Angular density > {ANGULAR_OUTLIER_THRESHOLD})")

    # 聚合：每个 Subject 每个 Eccentricity 保留一行
    agg_dict = {
        'Axial length (mm)': 'first',
        'Age': 'first',
        'Gender': 'first',
        'Spherical equivalent refraction (D)': 'first',
        'Corneal curvature (mm)': 'first',
        'Anterior chamber depth (mm)': 'first',
        'Angular cone density (cones/ deg2)': 'mean',
        'Linear cone density (cones/ mm2)': 'mean',
        'Eye': 'first',
    }

    grouped = df_all.groupby(['Subject_ID', 'Eccentricity (mm)'], as_index=False).agg(agg_dict)

    # 取 1.0°
    df_1mm = grouped[grouped['Eccentricity (mm)'] == 1.0].copy().reset_index(drop=True)
    print(f"[OK] 已加载 1.0° 聚合数据: n = {len(df_1mm)} subjects")
    return df_1mm


def genFig1(df):
    """SE vs AL 散点 + 线性回归（每 Subject 一个点）"""
    os.makedirs(os.path.dirname(OUTPUT_PDF1), exist_ok=True)

    df = df.dropna(subset=['Axial length (mm)', 'Spherical equivalent refraction (D)']).copy()

    x = df['Spherical equivalent refraction (D)']
    y = df['Axial length (mm)']

    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

    plt.figure(figsize=(8, 6), dpi=150)
    sns.set_theme(style="ticks")
    # re-apply Calibri after sns.set_theme overrides rcParams
    plt.rcParams['pdf.fonttype'] = 42
    plt.rcParams['font.sans-serif'] = ['Calibri', 'SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    plt.scatter(x, y, color='dodgerblue', edgecolor='none', s=60, alpha=0.85, zorder=2)

    x_fit = np.linspace(x.min(), x.max(), 100)
    y_fit = slope * x_fit + intercept
    plt.plot(x_fit, y_fit, color='red', linewidth=2.5, linestyle='-', zorder=1)

    plt.xlabel('Spherical Equivalent Refraction (D)', fontsize=14, fontweight='bold')
    plt.ylabel('Axial Length (mm)', fontsize=14, fontweight='bold')

    if p_value < 0.0001:
        p_str = "P < 0.0001"
    else:
        p_str = f"P = {p_value:.4f}"

    eq_str = f"y = {slope:.3f}x {'+' if intercept > 0 else '-'} {abs(intercept):.3f}"
    stats_text = f"{eq_str}\nr = {r_value:.3f}\n{p_str}"

    plt.text(0.95, 0.95, stats_text, transform=plt.gca().transAxes,
             fontsize=13, fontweight='bold',
             verticalalignment='top', horizontalalignment='right',
             bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.9, edgecolor='gray'))

    sns.despine()
    plt.tight_layout()
    plt.savefig(OUTPUT_PDF1, format='pdf', dpi=1200, bbox_inches='tight')
    plt.savefig(OUTPUT_PDF1.replace('.pdf', '.png'), format='png', dpi=300, bbox_inches='tight')
    print(f"[OK] FIGB1 已保存: {OUTPUT_PDF1}")
    print(f"[INFO] SE vs AL: {eq_str}, r = {r_value:.3f}, P = {p_value:.2e}")


def standardize(series):
    """Z-score 标准化"""
    return (series - series.mean()) / series.std(ddof=1)


def genFig2(df):
    """GEE 多因素回归森林图（标准化 β 系数）"""
    os.makedirs(os.path.dirname(OUTPUT_PDF2), exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)

    print("=" * 70)
    print("[INFO] 正在执行 GEE 多因素回归...")

    # 变量映射
    var_mapping = {
        'Axial length (mm)': 'AL',
        'Age': 'Age',
        'Spherical equivalent refraction (D)': 'SER',
        'Gender': 'Gender',
        'Corneal curvature (mm)': 'CC',
        'Anterior chamber depth (mm)': 'ACD'
    }

    display_mapping = {
        'Axial length (mm)': 'Axial length',
        'Age': 'Age',
        'Spherical equivalent refraction (D)': 'Spherical equivalent\nrefraction',
        'Gender': 'Gender',
        'Corneal curvature (mm)': 'Corneal\ncurvature',
        'Anterior chamber depth (mm)': 'Anterior chamber\ndepth'
    }

    target_orig = 'Angular cone density (cones/ deg2)'

    analysis_cols = list(var_mapping.keys()) + [target_orig, 'Subject_ID']
    df_clean = df.dropna(subset=analysis_cols).copy()

    # 标准化
    df_clean['Y_std'] = standardize(df_clean[target_orig])
    for orig_col, safe_col in var_mapping.items():
        df_clean[f"{safe_col}_std"] = standardize(df_clean[orig_col])

    # GEE 拟合
    predictors = [f"{v}_std" for v in var_mapping.values()]
    formula = "Y_std ~ " + " + ".join(predictors)

    try:
        model_all = smf.gee(formula, groups=df_clean['Subject_ID'], data=df_clean,
                            family=sm.families.Gaussian(),
                            cov_struct=sm.cov_struct.Exchangeable())
        res_all = model_all.fit()
    except Exception as e:
        print(f"[ERROR] GEE 拟合失败: {e}")
        raise

    # 提取结果
    results_list = []
    for orig_col, safe_col in var_mapping.items():
        pred_name = f"{safe_col}_std"
        display_name = display_mapping[orig_col]

        results_list.append({
            'Marker': display_name.replace('\n', ' '),   # CSV 用单行
            'Label': display_name,                       # 绘图用换行标签
            'beta': res_all.params[pred_name],
            'LCI': res_all.conf_int().loc[pred_name, 0],
            'UCI': res_all.conf_int().loc[pred_name, 1],
            'P': res_all.pvalues[pred_name]
        })

    res_df = pd.DataFrame(results_list)
    # CSV 中不需要 Label 列（含换行），只保留 Marker
    res_df[['Marker', 'beta', 'LCI', 'UCI', 'P']].to_csv(
        OUTPUT_CSV, index=False, encoding='utf-8-sig'
    )
    print(f"[OK] GEE 结果已保存为 CSV: {OUTPUT_CSV}")

    # ================= 绘制学术森林图 =================
    plt.rcParams['font.sans-serif'] = ['Calibri', 'SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
    # 压缩纵向间距，使整体更紧凑
    fig, ax = plt.subplots(figsize=(10.5, 5.2), dpi=300)

    y_base = np.arange(len(res_df))[::-1] * 1.4

    for i, row in res_df.iterrows():
        y_pos = y_base[i]

        ax.errorbar(row['beta'], y_pos,
                    xerr=[[row['beta'] - row['LCI']], [row['UCI'] - row['beta']]],
                    fmt='s', color='black', elinewidth=1.5,
                    capsize=5, capthick=1.5, markersize=8)

        sig_star = "***" if row['P'] < 0.001 else "**" if row['P'] < 0.01 else "*" if row['P'] < 0.05 else ""
        text_str = f"β={row['beta']:.2f}{sig_star}"

        # β 值统一放在误差线右端右侧，避免与左侧 y 轴重叠
        ax.text(row['UCI'] + 0.04, y_pos, text_str, va='center', ha='left',
                fontsize=10, color='black')

    # 零效应参考线（x=0）
    ax.axvline(x=0, color='black', linestyle='--', linewidth=1.2, zorder=0)

    # 动态 X 轴范围（包含右侧 β 标签）
    x_min = min(res_df['LCI'].min(), 0)
    x_max = max(res_df['UCI'].max(), 0)
    # 预留足够右侧空间给 β 标签
    text_max = (res_df['UCI'] + 0.25).max()
    x_max = max(x_max, text_max)
    margin = 0.10 * (x_max - x_min) if x_max != x_min else 0.2
    ax.set_xlim(x_min - margin, x_max + margin)

    ax.set_yticks(y_base)
    ax.set_yticklabels(res_df['Label'], fontsize=10, fontweight='bold')

    ax.set_xlabel('Standardized Regression Coefficient (β)', fontsize=13, fontweight='bold', labelpad=10)
    ax.set_title('Adjusted GEE Model for Angular Cone Density (1.0°)', fontsize=15, fontweight='bold', pad=15)

    # 隐藏上、右边框；显示左侧 y 轴实线
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(True)
    ax.spines['left'].set_color('black')
    ax.spines['left'].set_linewidth(1.2)
    ax.spines['left'].set_position(('outward', 5))  # 略微外移，避免与误差线重叠
    ax.tick_params(axis='y', length=5, width=1.2)

    # 为左侧长标签（SER、ACD）预留充足空间
    plt.tight_layout(rect=[0.32, 0, 1, 1])
    plt.savefig(OUTPUT_PDF2, bbox_inches='tight', facecolor='white')
    plt.savefig(OUTPUT_PDF2.replace('.pdf', '.png'), format='png', dpi=300, bbox_inches='tight')
    print(f"[OK] FIGB2 已保存: {OUTPUT_PDF2}")

    return res_df


if __name__ == '__main__':
    df_1mm = load_1mm_aggregated(DATA_DIR)
    genFig1(df_1mm)
    genFig2(df_1mm)
