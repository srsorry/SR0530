"""
SR0530：基于 71 眼的 SER 与 AL 线性回归分析

对每个偏心距离（1.0 – 6.0 mm）的可用眼子集，绘制
Spherical Equivalent Refraction (D) vs Axial Length (mm) 散点图，
并拟合线性回归，输出方程、Pearson r 与 P 值。

绘图风格参考 orgData/示意图线性回归1.docx：
- 蓝色散点、黑色边框
- 红色回归实线
- 右上角文本框显示 y = a + bx, r, P
- 清晰的 x/y 轴标签
- 图题标注距离与样本量
"""
import os
import glob
import numpy as np
import pandas as pd
from scipy import stats

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ============================================================
# 配置
# ============================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'genData', 'CleanDataRoi_lenient')
OUT_DIR = os.path.join(BASE_DIR, 'report', 'FIG', 'SER_AL_LinearRegression')
os.makedirs(OUT_DIR, exist_ok=True)

SER_COL = 'Spherical equivalent refraction (D)'
AL_COL = 'Axial length (mm)'
DIST_COL = 'Eccentricity (mm)'

# 字体设置（兼容中文标签，如果中文无法显示会回退英文）
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def load_distance_data(data_dir):
    all_data = {}
    for f in sorted(glob.glob(os.path.join(data_dir, 'data*.csv'))):
        df = pd.read_csv(f)
        dist = df[DIST_COL].iloc[0]
        if dist not in all_data:
            all_data[dist] = []
        all_data[dist].append(df)
    return all_data


def get_valid_ser_al(dfs):
    """
    取该距离下所有有效眼的 SER 与 AL。
    lenient 数据在每个距离有多个 quadrant 文件，需合并后按 Subject_ID + Eye 去重；
    只要任一眼在该距离任一分区有数据，即可纳入（与 5-fold/10-fold ML 脚本一致）。
    """
    all_records = []
    for df in dfs:
        if SER_COL in df.columns and AL_COL in df.columns:
            all_records.append(df[['Subject_ID', 'Eye', SER_COL, AL_COL]].copy())
    merged = pd.concat(all_records, ignore_index=True)
    merged = merged.drop_duplicates(subset=['Subject_ID', 'Eye'])
    merged = merged.dropna(subset=[SER_COL, AL_COL])
    return merged


def plot_one_distance(x, y, dist, n, out_path, figsize=(7, 6)):
    """绘制单距离的 SER vs AL 线性回归图"""
    # 线性回归
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

    fig, ax = plt.subplots(figsize=figsize)

    # 散点
    ax.scatter(x, y, c='#4DA6FF', edgecolors='black', s=60, alpha=0.85, linewidth=0.8, zorder=3)

    # 回归线
    x_line = np.array([x.min() - 0.5, x.max() + 0.5])
    y_line = intercept + slope * x_line
    ax.plot(x_line, y_line, color='red', linewidth=2.2, zorder=2)

    # 文本框：方程、r、P
    eq_text = f"y = {slope:.3f}x + {intercept:.3f}\nr = {r_value:.3f}\nP = {p_value:.4f}"
    if p_value < 0.0001:
        eq_text = f"y = {slope:.3f}x + {intercept:.3f}\nr = {r_value:.3f}\nP < 0.0001"
    ax.text(
        0.97, 0.97, eq_text,
        transform=ax.transAxes,
        fontsize=12,
        verticalalignment='top',
        horizontalalignment='right',
        bbox=dict(boxstyle='round,pad=0.4', facecolor='white', edgecolor='gray', alpha=0.95)
    )

    # 轴标签
    ax.set_xlabel('Spherical Equivalent Refraction (D)', fontsize=13)
    ax.set_ylabel('Axial Length (mm)', fontsize=13)

    # 标题/题注
    ax.set_title(f'Linear Regression at {dist:.1f} mm Eccentricity (n = {n})', fontsize=14, pad=12)

    # 美化
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(axis='both', which='major', labelsize=11)

    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()

    return slope, intercept, r_value, p_value


def plot_combined_grid(distances, results, out_path, nrows=3, ncols=4, figsize=(18, 14)):
    """将多个距离的子图合并成一张大图"""
    fig, axes = plt.subplots(nrows, ncols, figsize=figsize)
    axes = axes.flatten()

    for idx, ax in enumerate(axes):
        if idx < len(distances):
            dist = distances[idx]
            res = results[dist]
            x, y, n = res['x'], res['y'], res['n']
            slope, intercept, r_value, p_value = res['slope'], res['intercept'], res['r'], res['p']

            ax.scatter(x, y, c='#4DA6FF', edgecolors='black', s=40, alpha=0.85, linewidth=0.7, zorder=3)

            x_line = np.array([x.min() - 0.5, x.max() + 0.5])
            y_line = intercept + slope * x_line
            ax.plot(x_line, y_line, color='red', linewidth=2.0, zorder=2)

            eq_text = f"y = {slope:.3f}x + {intercept:.3f}\nr = {r_value:.3f}\nP = {p_value:.4f}"
            if p_value < 0.0001:
                eq_text = f"y = {slope:.3f}x + {intercept:.3f}\nr = {r_value:.3f}\nP < 0.0001"
            ax.text(
                0.97, 0.97, eq_text,
                transform=ax.transAxes,
                fontsize=9,
                verticalalignment='top',
                horizontalalignment='right',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='gray', alpha=0.95)
            )

            ax.set_xlabel('SER (D)', fontsize=10)
            ax.set_ylabel('AL (mm)', fontsize=10)
            ax.set_title(f'{dist:.1f} mm (n = {n})', fontsize=11, pad=6)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.tick_params(axis='both', which='major', labelsize=9)
        else:
            ax.axis('off')

    plt.suptitle('SER vs Axial Length Linear Regression across Eccentricities (1.0–6.0 mm)', fontsize=16, y=1.01)
    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()


def main():
    print("=" * 80)
    print("SR0530 SER vs AL Linear Regression Plots")
    print("=" * 80)

    all_data = load_distance_data(DATA_DIR)

    # 目标距离 1.0 - 6.0 mm，包含 0.5 mm 步长的所有可用距离
    target_dists = sorted([d for d in all_data.keys() if 1.0 <= d <= 6.0])

    results = {}
    summary_rows = []

    for dist in target_dists:
        df_valid = get_valid_ser_al(all_data[dist])
        x = df_valid[SER_COL].values
        y = df_valid[AL_COL].values
        n = len(x)

        out_path = os.path.join(OUT_DIR, f'SR0530_SER_AL_LinReg_{dist:.1f}mm.png')
        slope, intercept, r_value, p_value = plot_one_distance(x, y, dist, n, out_path)

        results[dist] = {
            'x': x, 'y': y, 'n': n,
            'slope': slope, 'intercept': intercept,
            'r': r_value, 'p': p_value
        }
        summary_rows.append({
            'Distance_mm': dist,
            'N': n,
            'Slope': slope,
            'Intercept': intercept,
            'R': r_value,
            'P': p_value,
            'Equation': f'y = {slope:.3f}x + {intercept:.3f}'
        })

        print(f"  {dist:.1f} mm (n={n}): y = {slope:.3f}x + {intercept:.3f}, r = {r_value:.3f}, P = {p_value:.4f}")

    # 合并图（所有 1.0-6.0 mm，3x4 布局）
    combined_path = os.path.join(OUT_DIR, 'SR0530_SER_AL_LinReg_Combined_1.0to6.0mm.png')
    plot_combined_grid(target_dists, results, combined_path, nrows=3, ncols=4)
    print(f"\n  Combined figure saved: {combined_path}")

    # 汇总 CSV
    summary_df = pd.DataFrame(summary_rows)
    summary_csv = os.path.join(OUT_DIR, 'SR0530_SER_AL_LinReg_Summary.csv')
    summary_df.to_csv(summary_csv, index=False, encoding='utf-8-sig')
    print(f"  Summary CSV saved: {summary_csv}")

    print("\n" + "=" * 80)
    print("Done!")
    print("=" * 80)


if __name__ == '__main__':
    main()
