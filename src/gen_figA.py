#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
SR0530 Figure A：71 眼 lenient 数据
- 1.0 mm 单独成图（Linear + Angular density vs AL）
- 其余 10 个距离（1.5–6.0 mm）绘制在同一张图内
================================================================================
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
# 让 PDF 中的文字以可编辑字体（Type 42 TrueType）嵌入，而非默认的 Type 3 轮廓字体
plt.rcParams['pdf.fonttype'] = 42
# Calibri 为首选字体；中文回退到 SimHei / Microsoft YaHei
plt.rcParams['font.sans-serif'] = ['Calibri', 'SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
from scipy import stats
import os
import re
import sys

# 强制 stdout 使用 UTF-8，避免 Windows 终端中文乱码
sys.stdout.reconfigure(encoding='utf-8')

# ========================== 用户自定义参数 ==========================
# 脚本所在目录的上一级即项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(BASE_DIR, 'genData', 'CleanDataRoi_lenient')
FILE_PATTERN = 'data*.csv'

OUTPUT_DIR = os.path.join(BASE_DIR, 'report', 'FIG', 'FIGA')

# P 值显示控制参数
P_VALUE_STYLE = 'auto'           # 'auto' / 'scientific' / 'float'
P_VALUE_FLOAT_DECIMALS = 5
P_VALUE_SCI_DECIMALS = 2

COLORMAP = plt.cm.turbo
FIGSIZE = (12, 13)

PNG_DPI = 1200
FIGURE_DPI = 150

# 输出文件名
OUTPUT_1MM = 'FIGA_1.0deg'
OUTPUT_OTHERS = 'FIGA_1.5-6.0deg'

# 异常值阈值（角密度 > 10000 视为异常）
ANGULAR_OUTLIER_THRESHOLD = 1e4


# ========================== 辅助函数 ==========================
def format_p_value(p):
    """根据全局参数格式化 P 值"""
    if P_VALUE_STYLE == 'scientific':
        return f"{p:.{P_VALUE_SCI_DECIMALS}e}"
    elif P_VALUE_STYLE == 'auto':
        if p < 0.001:
            return f"{p:.{P_VALUE_SCI_DECIMALS}e}"
        else:
            return f"{p:.{P_VALUE_FLOAT_DECIMALS}f}"
    else:
        return f"{p:.{P_VALUE_FLOAT_DECIMALS}f}"


def load_and_aggregate(data_dir, file_pattern='data*.csv'):
    """
    读取 44 个 ROI 文件，按 Subject_ID + Eccentricity 聚合（象限取平均），
    返回 {distance: DataFrame} 字典，并按距离从小到大排序。
    """
    if not os.path.exists(data_dir):
        raise FileNotFoundError(f"找不到文件夹: {data_dir}，请确保路径正确！")

    file_paths = sorted(
        [os.path.join(data_dir, f) for f in os.listdir(data_dir)
         if f.startswith('data') and f.endswith('.csv')],
        key=lambda f: int(re.search(r'\d+', os.path.basename(f)).group())
    )

    if not file_paths:
        raise FileNotFoundError(f"在 {data_dir} 中未找到匹配文件: {file_pattern}")

    # 1. 合并所有 ROI 文件
    dfs = []
    for fp in file_paths:
        df = pd.read_csv(fp)
        dfs.append(df)
    df_all = pd.concat(dfs, ignore_index=True)

    # 2. 全局异常值剔除：角密度 > 阈值的整行剔除
    n_before = len(df_all)
    df_all = df_all[df_all['Angular cone density (cones/ deg2)'] <= ANGULAR_OUTLIER_THRESHOLD].copy()
    n_after = len(df_all)
    if n_before != n_after:
        print(f"[WARN] 全局异常值剔除: {n_before - n_after} 行 (Angular density > {ANGULAR_OUTLIER_THRESHOLD})")

    # 3. 按 Subject_ID + Eccentricity 聚合（同一距离的多个象限取平均）
    # 眼形态参数对每个 Subject 相同，取 first；密度类指标取平均
    agg_dict = {
        'Axial length (mm)': 'first',
        'Age': 'first',
        'Gender': 'first',
        'Spherical equivalent refraction (D)': 'first',
        'Corneal curvature (mm)': 'first',
        'Anterior chamber depth (mm)': 'first',
        'Linear cone density (cones/ mm2)': 'mean',
        'Angular cone density (cones/ deg2)': 'mean',
        'Cone spacing': 'mean',
        'Cone dispersion': 'mean',
        'Cone regularity': 'mean',
        'Blood Vessel Ratio': 'mean',
        'Eye': 'first',
        'Eye_Label': 'first',
        'Patient_ID': 'first',
    }

    grouped = df_all.groupby(['Subject_ID', 'Eye', 'Eccentricity (mm)'], as_index=False).agg(agg_dict)

    # 4. 按距离拆分为字典
    distance_dict = {}
    for dist, gdf in grouped.groupby('Eccentricity (mm)'):
        distance_dict[float(dist)] = gdf.reset_index(drop=True)

    # 按距离排序
    distance_dict = dict(sorted(distance_dict.items()))
    print(f"[OK] 已加载并聚合 {len(distance_dict)} 个距离: {list(distance_dict.keys())}")

    return distance_dict


def draw_figure_1mm(distance_dict):
    """1.0 mm 单独成图"""
    dist = 1.0
    if dist not in distance_dict:
        raise KeyError(f"数据中不存在 {dist}°")

    df = distance_dict[dist]
    color = COLORMAP(0.15)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    plt.rcParams['figure.dpi'] = FIGURE_DPI
    plt.rcParams['savefig.dpi'] = PNG_DPI

    # ---- Linear ----
    ax = axes[0]
    x = df['Axial length (mm)'].values
    y = df['Linear cone density (cones/ mm2)'].values
    slope, intercept, r, p, _ = stats.linregress(x, y)
    sig = p < 0.05

    ax.scatter(x, y, c=[color], s=70, zorder=3,
               edgecolors='none', alpha=0.85)
    x_line = np.linspace(x.min(), x.max(), 100)
    ax.plot(x_line, slope * x_line + intercept,
            color='black', linewidth=2.0 if sig else 1.5,
            linestyle='-' if sig else ':', zorder=2)

    ax.set_xlabel('Axial Length (mm)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Linear Cone Density (cones/mm²)', fontsize=14, fontweight='bold')
    ax.set_title(f'1.0°', fontsize=16, fontweight='bold')
    ax.tick_params(labelsize=12)
    ax.grid(True, alpha=0.12, linestyle='-')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # 统计文本
    textstr = (
        f"n = {len(x)}\n"
        f"R² = {r**2:.3f}\n"
        f"Slope = {slope:.1f}\n"
        f"P = {format_p_value(p)}{' *' if sig else ''}"
    )
    ax.text(0.05, 0.95, textstr, transform=ax.transAxes,
            fontsize=12, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    # ---- Angular ----
    ax = axes[1]
    y = df['Angular cone density (cones/ deg2)'].values
    slope, intercept, r, p, _ = stats.linregress(x, y)
    sig = p < 0.05

    ax.scatter(x, y, c=[color], s=70, zorder=3,
               edgecolors='none', alpha=0.85, marker='o')
    ax.plot(x_line, slope * x_line + intercept,
            color='black', linewidth=2.0 if sig else 1.5,
            linestyle='-' if sig else ':', zorder=2)

    ax.set_xlabel('Axial Length (mm)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Angular Cone Density (cones/deg²)', fontsize=14, fontweight='bold')
    ax.set_title(f'1.0°', fontsize=16, fontweight='bold')
    ax.tick_params(labelsize=12)
    ax.grid(True, alpha=0.12, linestyle='-')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    textstr = (
        f"n = {len(x)}\n"
        f"R² = {r**2:.3f}\n"
        f"Slope = {slope:.1f}\n"
        f"P = {format_p_value(p)}{' *' if sig else ''}"
    )
    ax.text(0.05, 0.95, textstr, transform=ax.transAxes,
            fontsize=12, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    fig.tight_layout()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_pdf = os.path.join(OUTPUT_DIR, f"{OUTPUT_1MM}.pdf")
    fig.savefig(out_pdf, format='pdf', bbox_inches='tight', pad_inches=0.2, facecolor='white')
    out_png = os.path.join(OUTPUT_DIR, f"{OUTPUT_1MM}.png")
    fig.savefig(out_png, format='png', dpi=300, bbox_inches='tight', pad_inches=0.2, facecolor='white')
    print(f"[OK] 1.0° 图已保存: {out_pdf}")

    return fig


def draw_figure_others(distance_dict):
    """1.5–6.0 mm 十个距离绘制在同一张图内"""
    other_dists = [d for d in distance_dict.keys() if d != 1.0]
    if not other_dists:
        print("[WARN] 没有除 1.0° 之外的距离数据")
        return None

    n = len(other_dists)
    colors = COLORMAP(np.linspace(0.15, 0.85, n))

    plt.rcParams['figure.dpi'] = FIGURE_DPI
    plt.rcParams['savefig.dpi'] = PNG_DPI
    fig, axes = plt.subplots(2, 1, figsize=FIGSIZE)

    # ==================== 子图 A：Linear Density ====================
    axA = axes[0]
    stats_A = []

    for i, dist in enumerate(other_dists):
        df = distance_dict[dist]
        x = df['Axial length (mm)'].values
        y = df['Linear cone density (cones/ mm2)'].values

        slope, intercept, r, p, _ = stats.linregress(x, y)
        sig = p < 0.05

        axA.scatter(x, y, c=[colors[i]], s=50, zorder=3,
                    edgecolors='none', alpha=0.85)

        x_line = np.linspace(x.min(), x.max(), 100)
        axA.plot(x_line, slope * x_line + intercept,
                 color='black', linewidth=2.0 if sig else 1.5,
                 linestyle='-' if sig else ':', zorder=2)

        stats_A.append({
            'label': f"{dist:.1f}°", 'slope': slope, 'r2': r ** 2,
            'p': p, 'sig': sig, 'n': len(x)
        })

    axA.set_xlabel('Axial Length (mm)', fontsize=15, fontweight='bold')
    axA.set_ylabel('Linear Cone Density (cones/mm²)', fontsize=15, fontweight='bold')
    axA.text(-0.08, 1.05, 'A', transform=axA.transAxes, fontsize=22, fontweight='bold', va='top')
    axA.tick_params(labelsize=12)
    axA.grid(True, alpha=0.12, linestyle='-')
    axA.spines['top'].set_visible(False)
    axA.spines['right'].set_visible(False)

    handles_A = []
    for i, s in enumerate(stats_A):
        formatted_p = format_p_value(s['p'])
        txt = f"{s['label']} {'*' if s['sig'] else ''}P = {formatted_p}"
        handles_A.append(
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=colors[i],
                       markersize=9, label=txt)
        )
    axA.legend(handles=handles_A, loc='upper left', bbox_to_anchor=(1.02, 1.0),
               fontsize=11, frameon=False, title='Eccentricity', title_fontsize=12)

    # ==================== 子图 B：Angular Density ====================
    axB = axes[1]
    stats_B = []

    for i, dist in enumerate(other_dists):
        df = distance_dict[dist]
        x = df['Axial length (mm)'].values
        y = df['Angular cone density (cones/ deg2)'].values

        slope, intercept, r, p, _ = stats.linregress(x, y)
        sig = p < 0.05

        axB.scatter(x, y, c=[colors[i]], s=50, zorder=3,
                    edgecolors='none', alpha=0.85)

        x_line = np.linspace(x.min(), x.max(), 100)
        axB.plot(x_line, slope * x_line + intercept,
                 color='black', linewidth=2.0 if sig else 1.5,
                 linestyle='-' if sig else ':', zorder=2)

        stats_B.append({
            'label': f"{dist:.1f}°", 'slope': slope, 'r2': r ** 2,
            'p': p, 'sig': sig, 'n': len(x)
        })

    axB.set_xlabel('Axial Length (mm)', fontsize=15, fontweight='bold')
    axB.set_ylabel('Angular Cone Density (cones/deg²)', fontsize=15, fontweight='bold')
    axB.text(-0.08, 1.05, 'B', transform=axB.transAxes, fontsize=22, fontweight='bold', va='top')
    axB.tick_params(labelsize=12)
    axB.grid(True, alpha=0.12, linestyle='-')
    axB.spines['top'].set_visible(False)
    axB.spines['right'].set_visible(False)

    handles_B = []
    for i, s in enumerate(stats_B):
        formatted_p = format_p_value(s['p'])
        txt = f"{s['label']} {'*' if s['sig'] else ''}P = {formatted_p}"
        handles_B.append(
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=colors[i],
                       markersize=9, label=txt)
        )
    axB.legend(handles=handles_B, loc='upper left', bbox_to_anchor=(1.02, 1.0),
               fontsize=11, frameon=False, title='Eccentricity', title_fontsize=12)

    # ==================== 排版保护与出图 ====================
    fig.tight_layout(rect=[0, 0, 0.75, 1])

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_pdf = os.path.join(OUTPUT_DIR, f"{OUTPUT_OTHERS}.pdf")
    fig.savefig(out_pdf, format='pdf', bbox_inches='tight', pad_inches=0.2, facecolor='white')
    out_png = os.path.join(OUTPUT_DIR, f"{OUTPUT_OTHERS}.png")
    fig.savefig(out_png, format='png', dpi=300, bbox_inches='tight', pad_inches=0.2, facecolor='white')

    print(f"[OK] 1.5–6.0 mm 图已保存: {out_pdf}")

    return fig


# ========================== 主程序 ==========================
def main():
    distance_dict = load_and_aggregate(DATA_DIR, FILE_PATTERN)

    # 1.0 mm 单独成图
    draw_figure_1mm(distance_dict)

    # 其余 10 个距离（1.5–6.0 mm）绘制在同一张图内
    draw_figure_others(distance_dict)


if __name__ == '__main__':
    main()
