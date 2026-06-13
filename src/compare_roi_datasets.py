import pandas as pd
import numpy as np
import os
import glob
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ============================================================
# 配置
# ============================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STRICT_DIR = os.path.join(BASE_DIR, 'genData', 'CleanDataRoi_strict')
LENIENT_DIR = os.path.join(BASE_DIR, 'genData', 'CleanDataRoi_lenient')
SUM_DIR = os.path.join(BASE_DIR, 'genData', 'sum')
REPORT_DIR = os.path.join(BASE_DIR, 'report')
FIG_DIR = os.path.join(REPORT_DIR, 'FIG')
os.makedirs(FIG_DIR, exist_ok=True)

TARGET_COL = 'Angular cone density (cones/ deg2)'
FEATURE_COLS = [
    'Axial length (mm)', 'Age', 'Spherical equivalent refraction (D)',
    'Gender', 'Corneal curvature (mm)', 'Anterior chamber depth (mm)'
]


def load_44_roi_data(data_dir):
    """读取 44 个 ROI 文件，按距离聚合"""
    all_data = {}
    for f in sorted(glob.glob(os.path.join(data_dir, 'data*.csv'))):
        df = pd.read_csv(f)
        dist = df['Eccentricity (mm)'].iloc[0]
        if dist not in all_data:
            all_data[dist] = []
        all_data[dist].append(df)
    return all_data


def aggregate_distance(dfs):
    """对同一距离的 4 个象限数据，按 Subject_ID + Eye 找到共同组合并计算平均 angular density"""
    base = dfs[0][['Subject_ID', 'Eye'] + FEATURE_COLS + [TARGET_COL]].copy()
    base = base.rename(columns={TARGET_COL: 'density_q1'})

    for i, d in enumerate(dfs[1:], 2):
        base = base.merge(
            d[['Subject_ID', 'Eye', TARGET_COL]].rename(columns={TARGET_COL: f'density_q{i}'}),
            on=['Subject_ID', 'Eye'], how='inner'
        )

    den_cols = [c for c in base.columns if c.startswith('density_q')]
    base[TARGET_COL] = base[den_cols].mean(axis=1)

    cols = ['Subject_ID', 'Eye'] + FEATURE_COLS + [TARGET_COL]
    return base[cols].copy()


def compare_sample_sizes(strict_data, lenient_data):
    """比较每个距离的有效样本量"""
    records = []
    for dist in sorted(strict_data.keys()):
        strict_agg = aggregate_distance(strict_data[dist])
        lenient_agg = aggregate_distance(lenient_data[dist])
        records.append({
            'Distance (mm)': dist,
            'Strict_N_Eyes': len(strict_agg),
            'Lenient_N_Eyes': len(lenient_agg),
            'Difference': len(lenient_agg) - len(strict_agg),
            'Strict_N_Subjects': strict_agg['Subject_ID'].nunique(),
            'Lenient_N_Subjects': lenient_agg['Subject_ID'].nunique(),
        })
    return pd.DataFrame(records)


def compare_density_distribution(strict_data, lenient_data):
    """比较每个距离的角密度分布"""
    records = []
    for dist in sorted(strict_data.keys()):
        strict_agg = aggregate_distance(strict_data[dist])
        lenient_agg = aggregate_distance(lenient_data[dist])

        strict_dens = strict_agg[TARGET_COL]
        lenient_dens = lenient_agg[TARGET_COL]

        records.append({
            'Distance (mm)': dist,
            'Strict_Mean': strict_dens.mean(),
            'Lenient_Mean': lenient_dens.mean(),
            'Strict_Std': strict_dens.std(),
            'Lenient_Std': lenient_dens.std(),
            'Strict_Median': strict_dens.median(),
            'Lenient_Median': lenient_dens.median(),
            'Strict_Min': strict_dens.min(),
            'Lenient_Min': lenient_dens.min(),
            'Strict_Max': strict_dens.max(),
            'Lenient_Max': lenient_dens.max(),
        })
    return pd.DataFrame(records)


def compare_clinical_baseline(strict_data, lenient_data):
    """比较两组的临床基线特征（取 2.5mm 距离的聚合数据为代表）"""
    dist = 2.5
    strict_agg = aggregate_distance(strict_data[dist])
    lenient_agg = aggregate_distance(lenient_data[dist])

    records = []
    for col in FEATURE_COLS:
        s = strict_agg[col].dropna()
        l = lenient_agg[col].dropna()
        records.append({
            'Feature': col,
            'Strict_Mean': s.mean(),
            'Strict_Std': s.std(),
            'Lenient_Mean': l.mean(),
            'Lenient_Std': l.std(),
            'Mean_Diff': l.mean() - s.mean(),
        })
    return pd.DataFrame(records)


def count_roi_outliers(data_dir, threshold=7000):
    """统计单个 ROI 层面角密度 > threshold 的数量"""
    total = 0
    for f in sorted(glob.glob(os.path.join(data_dir, 'data*.csv'))):
        df = pd.read_csv(f)
        total += (df[TARGET_COL] > threshold).sum()
    return total


def plot_sample_size_comparison(df_sample, out_path):
    """绘制每个距离的样本量对比图"""
    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(df_sample))
    width = 0.35

    ax.bar(x - width/2, df_sample['Strict_N_Eyes'], width, label='Strict (69 eyes)', alpha=0.8)
    ax.bar(x + width/2, df_sample['Lenient_N_Eyes'], width, label='Lenient (71 eyes)', alpha=0.8)

    ax.set_xlabel('Eccentricity (mm)')
    ax.set_ylabel('Number of Eyes')
    ax.set_title('Sample Size Comparison by Distance: Strict vs Lenient')
    ax.set_xticks(x)
    ax.set_xticklabels([f"{d:.1f}" for d in df_sample['Distance (mm)']])
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(FIG_DIR, os.path.basename(out_path)), dpi=300, bbox_inches='tight')
    plt.close()


def plot_density_comparison(df_dist, out_path):
    """绘制每个距离的角密度均值 ± 标准差对比图"""
    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(df_dist))
    width = 0.35

    ax.bar(x - width/2, df_dist['Strict_Mean'], width,
           yerr=df_dist['Strict_Std'], label='Strict (69 eyes)', alpha=0.8, capsize=3)
    ax.bar(x + width/2, df_dist['Lenient_Mean'], width,
           yerr=df_dist['Lenient_Std'], label='Lenient (71 eyes)', alpha=0.8, capsize=3)

    ax.set_xlabel('Eccentricity (mm)')
    ax.set_ylabel('Angular Cone Density (cones/deg^2)')
    ax.set_title('Angular Density Comparison by Distance: Strict vs Lenient')
    ax.set_xticks(x)
    ax.set_xticklabels([f"{d:.1f}" for d in df_dist['Distance (mm)']])
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(FIG_DIR, os.path.basename(out_path)), dpi=300, bbox_inches='tight')
    plt.close()


def main():
    print("Loading strict data...")
    strict_data = load_44_roi_data(STRICT_DIR)
    print("Loading lenient data...")
    lenient_data = load_44_roi_data(LENIENT_DIR)

    # 1. 样本量对比
    df_sample = compare_sample_sizes(strict_data, lenient_data)
    df_sample.to_csv(os.path.join(SUM_DIR, 'compare_sample_size.csv'), index=False, encoding='utf-8-sig')
    print(f"Sample size comparison saved: {len(df_sample)} distances")

    # 2. 角密度分布对比
    df_dist = compare_density_distribution(strict_data, lenient_data)
    df_dist.to_csv(os.path.join(SUM_DIR, 'compare_density_distribution.csv'), index=False, encoding='utf-8-sig')
    print(f"Density distribution comparison saved")

    # 3. 临床基线对比（以 2.5mm 为代表）
    df_baseline = compare_clinical_baseline(strict_data, lenient_data)
    df_baseline.to_csv(os.path.join(SUM_DIR, 'compare_baseline_2.5mm.csv'), index=False, encoding='utf-8-sig')
    print(f"Baseline comparison saved")

    # 4. 异常值统计
    strict_outliers = count_roi_outliers(STRICT_DIR)
    lenient_outliers = count_roi_outliers(LENIENT_DIR)
    print(f"ROI-level outliers (>7000): strict={strict_outliers}, lenient={lenient_outliers}")

    # 5. 可视化
    plot_sample_size_comparison(df_sample, os.path.join(SUM_DIR, 'compare_sample_size.png'))
    plot_density_comparison(df_dist, os.path.join(SUM_DIR, 'compare_density.png'))
    print("Plots saved")

    # 6. 生成 Markdown 报告
    md_path = os.path.join(REPORT_DIR, 'SR0530_Strict_vs_Lenient_ROI_Comparison_Report.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# SR0530 Strict vs Lenient 44 ROI 数据对比报告\n\n")
        f.write("> **对比对象**：两种角密度黑名单策略生成的 44 ROI 数据\n\n")
        f.write("> **生成时间**：2026-06-13\n\n")
        f.write("---\n\n")

        f.write("## 一、黑名单策略说明\n\n")
        f.write("- **Strict（严格模式）**：任意单个 ROI 的 Angular Density > 7000 cones/deg² 即剔除该眼。\n")
        f.write("- **Lenient（宽松模式）**：仅当某距离的 4 象限平均 Angular Density > 7000 cones/deg² 才剔除该眼。\n\n")
        f.write("差异来源：宽松模式下，局部异常 ROI 会被同距离其他象限的值稀释，因此更宽容。\n\n")

        f.write("## 二、总体样本量\n\n")
        f.write(f"- **Strict 模式**：69 只眼\n")
        f.write(f"- **Lenient 模式**：71 只眼\n")
        f.write(f"- **差异**：Lenient 比 Strict 多 2 只眼（Patient_ID: 8192, 8542）\n\n")

        def df_to_md(df):
            """简单 Markdown 表格生成器，无需 tabulate"""
            lines = []
            lines.append('| ' + ' | '.join(df.columns) + ' |')
            lines.append('|' + '|'.join(['---'] * len(df.columns)) + '|')
            for _, row in df.iterrows():
                lines.append('| ' + ' | '.join([str(v) for v in row.values]) + ' |')
            return '\n'.join(lines)

        f.write("## 三、每个距离的样本量对比\n\n")
        f.write(df_to_md(df_sample))
        f.write("\n\n")
        f.write("![Sample Size Comparison](FIG/compare_sample_size.png)\n\n")

        f.write("## 四、角密度分布对比\n\n")
        f.write(df_to_md(df_dist.round(2)))
        f.write("\n\n")
        f.write("![Angular Density Comparison](FIG/compare_density.png)\n\n")

        f.write("## 五、临床基线对比（以 2.5mm 距离为代表）\n\n")
        f.write(df_to_md(df_baseline.round(3)))
        f.write("\n\n")

        f.write("## 六、ROI 层面异常值统计\n\n")
        f.write(f"- **Strict 模式**：单个 ROI 角密度 > 7000 的数量 = {strict_outliers}\n")
        f.write(f"- **Lenient 模式**：单个 ROI 角密度 > 7000 的数量 = {lenient_outliers}\n\n")

        f.write("## 七、分析与推荐\n\n")
        # 自动推荐逻辑
        max_mean_diff = (df_dist['Lenient_Mean'] - df_dist['Strict_Mean']).abs().max()
        max_max_diff = (df_dist['Lenient_Max'] - df_dist['Strict_Max']).abs().max()

        f.write(f"- 两套数据在各距离的均值差异最大为 {max_mean_diff:.2f} cones/deg²。\n")
        f.write(f"- 最大值差异最大为 {max_max_diff:.2f} cones/deg²，主要来自 Lenient 模式保留了更多高值异常点。\n")
        f.write(f"- Lenient 模式在 ROI 层面仍保留 {lenient_outliers} 个 >7000 的异常值，而 Strict 模式已将其清除。\n\n")

        f.write("### 推荐意见\n\n")
        if lenient_outliers > strict_outliers * 2:
            f.write("**建议使用 Strict 模式（69 眼）**。理由：\n")
            f.write("1. 局部 ROI 异常值 (>7000) 很可能是血管遮挡或测量误差，不应保留。\n")
            f.write("2. 4 象限平均会掩盖局部异常，导致数据质量不可控。\n")
            f.write("3. Strict 模式更符合数据清洗的保守原则，后续 ML/LMM 结果更可靠。\n")
        else:
            f.write("两套数据差异较小，可根据后续模型稳定性选择。\n")

        f.write("\n---\n")
        f.write("*报告生成：compare_roi_datasets.py*\n")

    print(f"Report saved: {md_path}")


if __name__ == '__main__':
    main()
