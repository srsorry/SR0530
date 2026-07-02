import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 全局字体设置：Calibri 为首选，中文回退
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['font.sans-serif'] = ['Calibri', 'SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
import statsmodels.api as sm
import statsmodels.formula.api as smf


def standardize(series):
    """Z-score 标准化：(x - mean) / std，用于提取标准化回归系数 (r)"""
    return (series - series.mean()) / series.std(ddof=1)


def plot_figure2_gee_only_wide(csv_path="data0.csv"):
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
    out_file = "Figure2_GEE_Only_Forest_Multiline_Wide.pdf"
    plt.savefig(out_file, bbox_inches='tight', facecolor='white')
    print(f"✅ X轴拉宽版图表已成功生成！矢量图保存在: {out_file}")

    plt.show()


if __name__ == "__main__":
    plot_figure2_gee_only_wide("../genData/CleanData/data0.csv")