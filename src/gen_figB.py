import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os
import statsmodels.api as sm
import statsmodels.formula.api as smf
import numpy as np

# ================= 配置区 =================
FILE_PATH = '../genData/CleanData/data0.csv'
OUTPUT_PDF1 = '../genData/FIGB/FIGB1.pdf'
OUTPUT_PDF2 = '../genData/FIGB/FIGB2.pdf'

def genFig1():
    if not os.path.exists(FILE_PATH):
        # 兼容当前目录下直接运行的情况
        FILE_PATH_FALLBACK = 'data0.csv'
        if os.path.exists(FILE_PATH_FALLBACK):
            file_to_read = FILE_PATH_FALLBACK
        else:
            raise FileNotFoundError(f"找不到数据文件，请确认路径。")
    else:
        file_to_read = FILE_PATH

    # 1. 读取数据并清理空值
    df = pd.read_csv(file_to_read)
    df = df.dropna(subset=['Axial length (mm)', 'Spherical equivalent refraction (D)'])

    # 【修改 1】：互换 X 轴和 Y 轴
    x = df['Spherical equivalent refraction (D)']
    y = df['Axial length (mm)']

    # 2. 计算皮尔逊相关系数 (r) 和 线性回归
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

    # 3. 绘图设置
    plt.figure(figsize=(8, 6), dpi=150)
    sns.set_theme(style="ticks")

    # 绘制散点图 (增加黑色的描边，使点位层次分明)
    plt.scatter(x, y, color='dodgerblue', edgecolor='black', s=60, alpha=0.8, zorder=2)

    # 绘制回归直线
    x_fit = x.sort_values()
    y_fit = slope * x_fit + intercept
    plt.plot(x_fit, y_fit, color='red', linewidth=2.5, linestyle='-', zorder=1)

    # 4. 图表美化与标签
    plt.xlabel('Spherical Equivalent Refraction (D)', fontsize=14, fontweight='bold')
    plt.ylabel('Axial Length (mm)', fontsize=14, fontweight='bold')

    # 【修改 2】：自动生成线性回归方程式并加入显示
    if p_value < 0.0001:
        p_str = "P < 0.0001"
    else:
        p_str = f"P = {p_value:.4f}"

    # 格式化方程式，自动处理截距的正负号 (例如 y = -0.3x + 24.5)
    eq_str = f"y = {slope:.3f}x {'+' if intercept > 0 else '-'} {abs(intercept):.3f}"

    # 将表达式、r值和P值组合起来
    stats_text = f"{eq_str}\nr = {r_value:.3f}\n{p_str}"

    # 在右上角显示文本框
    plt.text(0.95, 0.95, stats_text, transform=plt.gca().transAxes,
             fontsize=13, fontweight='bold',
             verticalalignment='top', horizontalalignment='right',
             bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.9, edgecolor='gray'))

    # 去除多余的顶部和右侧边框
    sns.despine()

    # 5. 保存与展示
    plt.tight_layout()
    plt.savefig(OUTPUT_PDF1, format='pdf', dpi=1200, bbox_inches='tight')
    print(f"✅ 图表已保存为高精度矢量 PDF: {OUTPUT_PDF1}")
    print(f"📊 统计结果: 表达式 {eq_str}, r = {r_value:.3f}, P 值 = {p_value:.2e}")

    plt.show()

def standardize(series):
    """Z-score 标准化：(x - mean) / std，用于提取标准化回归系数 (r)"""
    return (series - series.mean()) / series.std(ddof=1)


def genFig2(csv_path="data0.csv"):
    print("=" * 70)
    print("📊 正在读取数据，执行 GEE 多因素回归 (加宽 X 轴版)...")

    # 1. 加载数据
    df = pd.read_csv(csv_path)

    # 原始列名映射到安全的公式变量名
    var_mapping = {
        'Axial length (mm)': 'AL',
        'Age': 'Age',
        'Spherical equivalent refraction (D)': 'SER',
        'Gender': 'Gender',
        'Corneal curvature (mm)': 'CC',
        'Anterior chamber depth (mm)': 'ACD'
    }

    # 用于图表 Y 轴显示的换行字典
    display_mapping = {
        'Axial length (mm)': 'Axial length',
        'Age': 'Age',
        'Spherical equivalent refraction (D)': 'Spherical equivalent\nrefraction',
        'Gender': 'Gender',
        'Corneal curvature (mm)': 'Corneal\ncurvature',
        'Anterior chamber depth (mm)': 'Anterior chamber\ndepth'
    }

    target_orig = 'Angular cone density (cones/ deg2)'

    # 剔除缺失值
    analysis_cols = list(var_mapping.keys()) + [target_orig, 'Subject_ID']
    df_clean = df.dropna(subset=analysis_cols).copy()

    # 2. 数据 Z-score 标准化
    df_clean['Y_std'] = standardize(df_clean[target_orig])

    for orig_col, safe_col in var_mapping.items():
        df_clean[f"{safe_col}_std"] = standardize(df_clean[orig_col])

    # 3. 统计建模 (GEE 模型)
    predictors = [f"{v}_std" for v in var_mapping.values()]
    formula = "Y_std ~ " + " + ".join(predictors)

    model_all = smf.gee(formula, groups=df_clean['Subject_ID'], data=df_clean,
                        family=sm.families.Gaussian(),
                        cov_struct=sm.cov_struct.Exchangeable())
    res_all = model_all.fit()

    # 4. 提取结果
    results_list = []
    for orig_col, safe_col in var_mapping.items():
        pred_name = f"{safe_col}_std"
        display_name = display_mapping[orig_col]

        results_list.append({
            'Marker': display_name,
            'r': res_all.params[pred_name],
            'LCI': res_all.conf_int().loc[pred_name, 0],
            'UCI': res_all.conf_int().loc[pred_name, 1],
            'P': res_all.pvalues[pred_name]
        })

    res_df = pd.DataFrame(results_list)

    # 5. ================= 绘制学术森林图 =================
    plt.rcParams['font.sans-serif'] = ['Arial']
    fig, ax = plt.subplots(figsize=(9, 6.5), dpi=300)

    y_base = np.arange(len(res_df))[::-1] * 2.0

    for i, row in res_df.iterrows():
        y_pos = y_base[i]

        # 绘制黑色的误差线和方块标记
        ax.errorbar(row['r'], y_pos, xerr=[[row['r'] - row['LCI']], [row['UCI'] - row['r']]],
                    fmt='s', color='black', elinewidth=1.5,
                    capsize=5, capthick=1.5, markersize=8)

        # 显著性星号标注
        sig_star = "***" if row['P'] < 0.001 else "**" if row['P'] < 0.01 else "*" if row['P'] < 0.05 else ""

        # 文字标注
        text_str = f"r={row['r']:.2f}{sig_star}"

        # 智能避让文字：系数值大则写左边，值小则写右边
        if row['r'] > 0:
            ax.text(row['UCI'] + 0.04, y_pos, text_str, va='center', ha='left', fontsize=11, color='black')
        else:
            ax.text(row['LCI'] - 0.04, y_pos, text_str, va='center', ha='right', fontsize=11, color='black')

    # ==================================================
    # 🌟 核心图表装饰调整 🌟
    # ==================================================
    ax.axvline(x=0, color='gray', linestyle='--', linewidth=1.5, zorder=0)

    # 【新增】：强制拉宽 X 轴的显示范围，给两端留出充分的空白空间！
    # 如果你觉得还不够宽，可以改成 (-1.0, 1.0)
    ax.set_xlim(-0.8, 0.8)

    ax.set_yticks(y_base)
    ax.set_yticklabels(res_df['Marker'], fontsize=12, fontweight='bold')

    ax.set_xlabel('Standardized Regression Coefficient (r)', fontsize=13, fontweight='bold', labelpad=10)
    ax.set_title('Adjusted GEE Model for Angular Cone Density', fontsize=15, fontweight='bold', pad=15)

    # 边框优化：去掉上、右、左边框
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.tick_params(axis='y', length=0)

    plt.tight_layout()
    out_file = OUTPUT_PDF2
    plt.savefig(out_file, bbox_inches='tight', facecolor='white')
    print(f"✅ X轴拉宽版图表已成功生成！矢量图保存在: {out_file}")

    plt.show()





if __name__ == '__main__':
    genFig1()
    genFig2(FILE_PATH)