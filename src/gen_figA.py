#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
复现 Wang et al. 2019 Figure 5 风格图表 (已修复图例越界 + 优化P值科学计数显示)
================================================================================
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import os
import re

# ========================== 用户自定义参数 ==========================
# 【修改 1】数据目录：已更新为你指定的默认路径
DATA_DIR = '../genData/CleanData'
FILE_PATTERN = 'data*.csv'

OUTPUT_PREFIX = 'FIGA'
OUTPUT_DIR = '../genData/FIGA'

# 【修改 2】P 值显示控制参数
# 可选值:
# 'auto'       - 智能模式：P < 0.001 时用科学计数法，否则用小数
# 'scientific' - 强制全部使用科学计数法 (如 1.23e-02)
# 'float'      - 强制全部使用传统小数 (如 0.01234)
P_VALUE_STYLE = 'auto'
P_VALUE_FLOAT_DECIMALS = 5  # 小数模式下保留几位
P_VALUE_SCI_DECIMALS = 2  # 科学计数法下保留几位

# 图A（线性密度）的偏心率标签
LABELS_LINEAR = [
    "0-25 μm", "25-50 μm", "50-75 μm", "75-100 μm", "100-125 μm",
    "125-150 μm", "150-175 μm", "175-200 μm", "200-225 μm", "225-250 μm",
    "250-275 μm", "275-300 μm"
]

# 图B（角密度）的偏心率标签
LABELS_ANGULAR = [
    "0-5 min", "5-10 min", "10-15 min", "15-20 min", "20-25 min",
    "25-30 min", "30-35 min", "35-40 min", "40-45 min", "45-50 min",
    "50-55 min", "55-60 min"
]

COLORMAP = plt.cm.turbo
FIGSIZE = (12, 13)

PNG_DPI = 1200
FIGURE_DPI = 150


# ========================== 辅助函数 ==========================
def format_p_value(p):
    """根据全局参数格式化 P 值的输出"""
    if P_VALUE_STYLE == 'scientific':
        return f"{p:.{P_VALUE_SCI_DECIMALS}e}"
    elif P_VALUE_STYLE == 'auto':
        if p < 0.001:
            return f"{p:.{P_VALUE_SCI_DECIMALS}e}"
        else:
            return f"{p:.{P_VALUE_FLOAT_DECIMALS}f}"
    else:
        return f"{p:.{P_VALUE_FLOAT_DECIMALS}f}"


# ========================== 主程序 ==========================
def main():
    # 1. 寻找文件并按数字严格排序
    file_paths = []
    if not os.path.exists(DATA_DIR):
        raise FileNotFoundError(f"找不到文件夹: {DATA_DIR}，请确保路径正确！")

    for f in os.listdir(DATA_DIR):
        if f.startswith('data') and f.endswith('.csv'):
            file_paths.append(os.path.join(DATA_DIR, f))

    file_paths.sort(key=lambda f: int(re.search(r'\d+', os.path.basename(f)).group()))
    n = len(file_paths)

    if n == 0:
        raise FileNotFoundError(f"在 {DATA_DIR} 中未找到匹配文件: {FILE_PATTERN}")

    # 2. 样本级异常值预扫描 (Angular > 6100 的彻底剔除)
    blacklist_indices = set()
    for fp in file_paths:
        df = pd.read_csv(fp)
        outliers = df[df['Angular cone density (cones/ deg2)'] > 1e4]
        blacklist_indices.update(outliers.index.tolist())

    # 3. 载入并清洗数据
    cleaned_dfs = []
    for fp in file_paths:
        df = pd.read_csv(fp)
        df = df.drop(index=list(blacklist_indices), errors='ignore')
        cleaned_dfs.append(df)

    # 4. 颜色与标签映射
    colors = COLORMAP(np.linspace(0.15, 0.85, n))
    labels_A = [LABELS_LINEAR[i] if i < len(LABELS_LINEAR) else f"Group {i + 1}" for i in range(n)]
    labels_B = [LABELS_ANGULAR[i] if i < len(LABELS_ANGULAR) else f"Group {i + 1}" for i in range(n)]

    # 5. 创建画布
    plt.rcParams['figure.dpi'] = FIGURE_DPI
    plt.rcParams['savefig.dpi'] = PNG_DPI
    fig, axes = plt.subplots(2, 1, figsize=FIGSIZE)

    # ==================== 子图 A：Linear Density ====================
    axA = axes[0]
    stats_A = []
    y_vals_A = []

    for i, df in enumerate(cleaned_dfs):
        if df.empty: continue
        x = df['Axial length (mm)'].values
        y = df['Linear cone density (cones/ mm2)'].values
        y_vals_A.extend(y)

        slope, intercept, r, p, se = stats.linregress(x, y)
        sig = p < 0.05

        axA.scatter(x, y, c=[colors[i]], s=50, zorder=3,
                    edgecolors='black', linewidth=0.5, alpha=0.85)

        x_line = np.linspace(x.min(), x.max(), 100)
        y_line = slope * x_line + intercept
        lw = 2.0 if sig else 1.5
        ls = '-' if sig else ':'
        axA.plot(x_line, y_line, color='black', linewidth=lw, linestyle=ls, zorder=2)

        stats_A.append({
            'label': labels_A[i], 'slope': slope, 'r2': r ** 2, 'p': p, 'sig': sig, 'n': len(x)
        })

    # 装饰图A
    axA.set_xlabel('Axial Length (mm)', fontsize=15, fontweight='bold')
    axA.set_ylabel('Linear Cone Density (cones/mm²)', fontsize=15, fontweight='bold')
    axA.text(-0.08, 1.05, 'A', transform=axA.transAxes, fontsize=22, fontweight='bold', va='top')

    if y_vals_A:
        axA.set_ylim(np.min(y_vals_A) * 0.85, np.max(y_vals_A) * 1.10)
    axA.tick_params(labelsize=12)
    axA.grid(True, alpha=0.12, linestyle='-')
    axA.spines['top'].set_visible(False)
    axA.spines['right'].set_visible(False)

    # 图A 图例 - 应用动态 P 值格式化
    handles_A = []
    for i, s in enumerate(stats_A):
        # 使用 format_p_value 函数动态生成 P 值的字符串
        formatted_p = format_p_value(s['p'])
        txt = f"{s['label']} {'*' if s['sig'] else ''}P = {formatted_p}"
        handles_A.append(
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=colors[i],
                       markersize=9, markeredgecolor='black', markeredgewidth=0.5, label=txt)
        )
    axA.legend(handles=handles_A, loc='upper left', bbox_to_anchor=(1.02, 1.0),
               fontsize=11, frameon=False, title='Eccentricity', title_fontsize=12)

    # ==================== 子图 B：Angular Density ====================
    axB = axes[1]
    stats_B = []
    y_vals_B = []

    for i, df in enumerate(cleaned_dfs):
        if df.empty: continue
        x = df['Axial length (mm)'].values
        y = df['Angular cone density (cones/ deg2)'].values
        y_vals_B.extend(y)

        slope, intercept, r, p, se = stats.linregress(x, y)
        sig = p < 0.05

        axB.scatter(x, y, c=[colors[i]], s=50, zorder=3,
                    edgecolors='black', linewidth=0.5, alpha=0.85)

        x_line = np.linspace(x.min(), x.max(), 100)
        y_line = slope * x_line + intercept
        lw = 2.0 if sig else 1.5
        ls = '-' if sig else ':'
        axB.plot(x_line, y_line, color='black', linewidth=lw, linestyle=ls, zorder=2)

        stats_B.append({
            'label': labels_B[i], 'slope': slope, 'r2': r ** 2, 'p': p, 'sig': sig, 'n': len(x)
        })

    # 装饰图B
    axB.set_xlabel('Axial Length (mm)', fontsize=15, fontweight='bold')
    axB.set_ylabel('Angular Cone Density (cones/deg²)', fontsize=15, fontweight='bold')
    axB.text(-0.08, 1.05, 'B', transform=axB.transAxes, fontsize=22, fontweight='bold', va='top')

    if y_vals_B:
        axB.set_ylim(np.min(y_vals_B) * 0.85, np.max(y_vals_B) * 1.10)
    axB.tick_params(labelsize=12)
    axB.grid(True, alpha=0.12, linestyle='-')
    axB.spines['top'].set_visible(False)
    axB.spines['right'].set_visible(False)

    # 图B 图例 - 应用动态 P 值格式化
    handles_B = []
    for i, s in enumerate(stats_B):
        # 使用 format_p_value 函数动态生成 P 值的字符串
        formatted_p = format_p_value(s['p'])
        txt = f"{s['label']} {'*' if s['sig'] else ''}P = {formatted_p}"
        handles_B.append(
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=colors[i],
                       markersize=9, markeredgecolor='black', markeredgewidth=0.5, label=txt)
        )
    axB.legend(handles=handles_B, loc='upper left', bbox_to_anchor=(1.02, 1.0),
               fontsize=11, frameon=False, title='Eccentricity', title_fontsize=12)

    # ==================== 排版保护与出图 ====================
    fig.tight_layout(rect=[0, 0, 0.75, 1])

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_pdf = os.path.join(OUTPUT_DIR, f"{OUTPUT_PREFIX}.pdf")

    fig.savefig(out_pdf, format='pdf', bbox_inches='tight', pad_inches=0.2, facecolor='white')

    print(f"✅ 矢量 PDF 已保存: {out_pdf}")
    plt.show()


if __name__ == '__main__':
    main()