"""
SR0530：基于 71 眼的 FIGA 风格 MLR 偏残差图

参考 gen_figA.py / genData/FIGA/FIGA.pdf 的风格，将原图拆成两份：
- 图 4：1.0 mm 处，线密度和角密度随 AL 的多重线性回归偏残差图
- 图 5：1.5–6.0 mm 处，线密度随 AL 的多重线性回归偏残差图（多距离叠加）

方法：
- 对每个距离分别拟合 MLR：Density ~ AL + Age + Gender + SER + K + ACD
- 绘制 component-plus-residual（偏残差）图：
    y_partial = Y - X_other @ beta_other = residual + beta_AL * AL
    x = AL（原始尺度）
- 回归线斜率即 MLR 中 AL 的系数；图例标注 AL 系数的 P 值。
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

from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings('ignore')

# ============================================================
# 配置
# ============================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'genData', 'CleanDataRoi_lenient')
OUT_DIR = os.path.join(BASE_DIR, 'report', 'FIG', 'FigA_MLR_Split')
os.makedirs(OUT_DIR, exist_ok=True)

FEATURE_ALL = {
    'AL': 'Axial length (mm)',
    'Age': 'Age',
    'SE': 'Spherical equivalent refraction (D)',
    'Gender': 'Gender',
    'K': 'Corneal curvature (mm)',
    'ACD': 'Anterior chamber depth (mm)',
}
LINEAR_DEN = 'Linear cone density (cones/ mm2)'
ANGULAR_DEN = 'Angular cone density (cones/ deg2)'
DIST_COL = 'Eccentricity (mm)'

covariates = ['Age', 'SE', 'Gender', 'K', 'ACD']  # 除 AL 外的协变量
AL = 'AL'

# 颜色映射（参考 FIGA 的 turbo，但按距离均匀取色）
CMAP = plt.cm.turbo

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


def aggregate_distance(dfs):
    """对一个距离的所有 quadrant 数据取平均，每个 Eye 一行"""
    # 选取数值型密度列和特征列
    feature_cols = list(FEATURE_ALL.values())
    den_cols = [LINEAR_DEN, ANGULAR_DEN]

    # 合并所有 quadrant
    df_all = pd.concat(dfs, ignore_index=True)

    # 按 Subject_ID + Eye 分组，对密度和特征取平均
    agg_dict = {c: 'mean' for c in feature_cols + den_cols}
    df_sub = df_all.groupby(['Subject_ID', 'Eye'], as_index=False).agg(agg_dict)

    # 去除缺失
    df_sub = df_sub.dropna(subset=feature_cols + den_cols)
    return df_sub


def encode_features(df):
    """构造 MLR 用的 X（包含 AL 和协变量）和标准化版本"""
    X = df[[FEATURE_ALL[c] for c in [AL] + covariates]].copy()
    # Gender 已经是 0/1 数值
    return X


def fit_mlr_get_al_effect(X, y):
    """
    拟合 MLR y ~ AL + covariates，返回 AL 的偏残差、系数、P 值等。
    使用标准误和 t 分布计算 AL 系数的 P 值。
    """
    model = LinearRegression().fit(X, y)
    y_pred = model.predict(X)
    residual = y - y_pred

    n, p = X.shape
    # 计算标准误
    X_with_intercept = np.column_stack([np.ones(n), X.values])
    mse = np.sum(residual ** 2) / (n - p - 1)
    cov_beta = mse * np.linalg.inv(X_with_intercept.T @ X_with_intercept)
    # AL 是第 1 列（intercept 为 0）
    se_al = np.sqrt(cov_beta[1, 1])
    beta_al = model.coef_[0]
    t_stat = beta_al / se_al
    p_val = 2 * (1 - stats.t.cdf(np.abs(t_stat), df=n - p - 1))

    # 偏残差：y 扣除其他协变量贡献后的残差 + beta_al * AL
    # 等价于 residual + beta_al * AL
    al_idx = 0
    other_coef = model.coef_.copy()
    other_coef[al_idx] = 0
    partial_residual = y - (X.values @ other_coef + model.intercept_)

    return {
        'model': model,
        'beta_al': beta_al,
        'se_al': se_al,
        'p_al': p_val,
        't_al': t_stat,
        'partial_residual': partial_residual,
        'al_values': X.iloc[:, al_idx].values,
        'residual': residual,
        'r2': model.score(X, y),
        'n': n
    }


def plot_figure4(df_10, out_path):
    """图 4：1.0 mm 处线密度 + 角密度 vs AL 的偏残差图"""
    fig, axes = plt.subplots(2, 1, figsize=(9, 12))

    X = encode_features(df_10)

    for ax, den_col, title_suffix, ylabel in zip(
        axes,
        [LINEAR_DEN, ANGULAR_DEN],
        ['Linear Density', 'Angular Density'],
        ['Linear Cone Density (cones/mm²)', 'Angular Cone Density (cones/deg²)']
    ):
        y = df_10[den_col].values
        res = fit_mlr_get_al_effect(X, y)

        x = res['al_values']
        y_part = res['partial_residual']
        beta = res['beta_al']
        p = res['p_al']
        sig = p < 0.05

        color = '#4DA6FF'
        ax.scatter(x, y_part, c=color, edgecolors='black', s=70, alpha=0.85, linewidth=0.8, zorder=3)

        x_line = np.linspace(x.min(), x.max(), 100)
        y_line = beta * x_line  # 偏残差图回归线过原点
        lw = 2.5 if sig else 1.5
        ls = '-' if sig else ':'
        ax.plot(x_line, y_line, color='black', linewidth=lw, linestyle=ls, zorder=2)

        # 文本框
        eq_text = f"β = {beta:.2f}\nP = {p:.4f}\nR² = {res['r2']:.3f}"
        if p < 0.0001:
            eq_text = f"β = {beta:.2f}\nP < 0.0001\nR² = {res['r2']:.3f}"
        ax.text(
            0.97, 0.97, eq_text,
            transform=ax.transAxes, fontsize=11,
            verticalalignment='top', horizontalalignment='right',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='white', edgecolor='gray', alpha=0.95)
        )

        ax.set_xlabel('Axial Length (mm)', fontsize=14, fontweight='bold')
        ax.set_ylabel(ylabel, fontsize=14, fontweight='bold')
        ax.set_title(f'1.0 mm: {title_suffix} vs AL (after MLR)', fontsize=15, pad=10)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.tick_params(labelsize=12)
        ax.grid(True, alpha=0.12, linestyle='-')

    axes[0].text(-0.12, 1.05, 'A', transform=axes[0].transAxes, fontsize=22, fontweight='bold', va='top')
    axes[1].text(-0.12, 1.05, 'B', transform=axes[1].transAxes, fontsize=22, fontweight='bold', va='top')

    plt.tight_layout()
    plt.savefig(out_path, format='pdf', bbox_inches='tight', pad_inches=0.2, facecolor='white')
    plt.savefig(out_path.replace('.pdf', '.png'), dpi=300, bbox_inches='tight', pad_inches=0.2, facecolor='white')
    plt.close()


def plot_figure5(all_data, out_path):
    """图 5：1.5–6.0 mm 线密度 vs AL 的偏残差图（多距离叠加）"""
    target_dists = [d for d in sorted(all_data.keys()) if 1.5 <= d <= 6.0]
    n_dists = len(target_dists)
    colors = CMAP(np.linspace(0.15, 0.85, n_dists))

    fig, ax = plt.subplots(1, 1, figsize=(10, 8))

    stats_list = []

    for i, dist in enumerate(target_dists):
        df_sub = aggregate_distance(all_data[dist])
        X = encode_features(df_sub)
        y = df_sub[LINEAR_DEN].values
        res = fit_mlr_get_al_effect(X, y)

        x = res['al_values']
        y_part = res['partial_residual']
        beta = res['beta_al']
        p = res['p_al']
        sig = p < 0.05

        ax.scatter(x, y_part, c=[colors[i]], edgecolors='black', s=50, alpha=0.85,
                   linewidth=0.5, zorder=3)

        x_line = np.linspace(x.min(), x.max(), 100)
        y_line = beta * x_line
        lw = 2.0 if sig else 1.5
        ls = '-' if sig else ':'
        ax.plot(x_line, y_line, color='black', linewidth=lw, linestyle=ls, zorder=2)

        stats_list.append({
            'dist': dist,
            'beta': beta,
            'p': p,
            'sig': sig,
            'n': res['n']
        })

    ax.set_xlabel('Axial Length (mm)', fontsize=15, fontweight='bold')
    ax.set_ylabel('Linear Cone Density (cones/mm²)', fontsize=15, fontweight='bold')
    ax.set_title('1.5–6.0 mm: Linear Density vs AL (after MLR)', fontsize=16, pad=12)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(labelsize=12)
    ax.grid(True, alpha=0.12, linestyle='-')

    # 图例
    handles = []
    for i, s in enumerate(stats_list):
        txt = f"{s['dist']:.1f} mm {'*' if s['sig'] else ''}P = {s['p']:.4f}"
        if s['p'] < 0.0001:
            txt = f"{s['dist']:.1f} mm {'*' if s['sig'] else ''}P < 0.0001"
        handles.append(
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=colors[i],
                       markersize=9, markeredgecolor='black', markeredgewidth=0.5, label=txt)
        )
    ax.legend(handles=handles, loc='upper left', bbox_to_anchor=(1.02, 1.0),
              fontsize=10, frameon=False, title='Eccentricity', title_fontsize=12)

    plt.tight_layout(rect=[0, 0, 0.72, 1])
    plt.savefig(out_path, format='pdf', bbox_inches='tight', pad_inches=0.2, facecolor='white')
    plt.savefig(out_path.replace('.pdf', '.png'), dpi=300, bbox_inches='tight', pad_inches=0.2, facecolor='white')
    plt.close()


def main():
    print("=" * 80)
    print("SR0530 FIGA-style MLR Split Figures (71 eyes)")
    print("=" * 80)

    all_data = load_distance_data(DATA_DIR)

    # 图 4：1.0 mm
    df_10 = aggregate_distance(all_data[1.0])
    fig4_path = os.path.join(OUT_DIR, 'SR0530_FigA_Task4_1.0mm_MLR.pdf')
    plot_figure4(df_10, fig4_path)
    print(f"  Figure 4 saved: {fig4_path}")
    print(f"    1.0 mm Linear: n={len(df_10)}")
    print(f"    1.0 mm Angular: n={len(df_10)}")

    # 图 5：1.5–6.0 mm
    fig5_path = os.path.join(OUT_DIR, 'SR0530_FigA_Task5_1.5to6.0mm_MLR.pdf')
    plot_figure5(all_data, fig5_path)
    print(f"  Figure 5 saved: {fig5_path}")

    # 汇总 CSV
    summary = []
    for dist in [1.0] + [d for d in sorted(all_data.keys()) if 1.5 <= d <= 6.0]:
        df_sub = aggregate_distance(all_data[dist])
        X = encode_features(df_sub)

        for den_col, den_name in [(LINEAR_DEN, 'Linear'), (ANGULAR_DEN, 'Angular')]:
            # 1.0 mm 做两种密度；1.5–6.0 mm 只做线密度
            if dist == 1.0 or den_name == 'Linear':
                y = df_sub[den_col].values
                res = fit_mlr_get_al_effect(X, y)
                summary.append({
                    'Distance_mm': dist,
                    'Density_Type': den_name,
                    'N': res['n'],
                    'AL_Beta': res['beta_al'],
                    'AL_SE': res['se_al'],
                    'AL_t': res['t_al'],
                    'AL_P': res['p_al'],
                    'R2': res['r2']
                })

    summary_df = pd.DataFrame(summary)
    csv_path = os.path.join(OUT_DIR, 'SR0530_FigA_MLR_Coefficients.csv')
    summary_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"  Coefficients CSV: {csv_path}")
    print(summary_df.to_string(index=False))

    print("\n" + "=" * 80)
    print("Done!")
    print("=" * 80)


if __name__ == '__main__':
    main()
