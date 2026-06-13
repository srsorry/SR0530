import pandas as pd
import numpy as np
from cal_ACD import add_angular_density
import os
import re
OUTPUT_DIR = '../genData'

def generate_baseline_table_total(df):


    # 映射分组名称
    if 'Source_Class' in df.columns:
        df['Group'] = df['Source_Class'].map({0: 'Normal', 1: 'ASO'})
    else:
        print("未找到 Source_Class 列！")
        return

    normal_df = df[df['Group'] == 'Normal']
    aso_df = df[df['Group'] == 'ASO']

    # 计算样本量 N
    n_total = len(df)
    n_normal = len(normal_df)
    n_aso = len(aso_df)

    results = []

    # ==========================================
    # 1. 眼别 (OD / OS)
    # ==========================================
    od_total = len(df[df['Eye'] == 'OD'])
    os_total = len(df[df['Eye'] == 'OS'])
    od_normal = len(normal_df[normal_df['Eye'] == 'OD'])
    os_normal = len(normal_df[normal_df['Eye'] == 'OS'])
    od_aso = len(aso_df[aso_df['Eye'] == 'OD'])
    os_aso = len(aso_df[aso_df['Eye'] == 'OS'])

    results.append({
        '眼部/人口学参数': '眼别分布 (右眼 OD / 左眼 OS)',
        f'Total (N={n_total})': f"{od_total} / {os_total}",
        f'Normal (N={n_normal})': f"{od_normal} / {os_normal}",
        f'ASO (N={n_aso})': f"{od_aso} / {os_aso}"
    })

    # ==========================================
    # 2. 性别 (男 / 女)
    # ==========================================
    # 假设 1 代表男，0 代表女
    male_total = len(df[df['Gender'] == 1])
    female_total = len(df[df['Gender'] == 0])
    male_normal = len(normal_df[normal_df['Gender'] == 1])
    female_normal = len(normal_df[normal_df['Gender'] == 0])
    male_aso = len(aso_df[aso_df['Gender'] == 1])
    female_aso = len(aso_df[aso_df['Gender'] == 0])

    results.append({
        '眼部/人口学参数': '性别分布 (男 / 女)',
        f'Total (N={n_total})': f"{male_total} / {female_total}",
        f'Normal (N={n_normal})': f"{male_normal} / {female_normal}",
        f'ASO (N={n_aso})': f"{male_aso} / {female_aso}"
    })

    # ==========================================
    # 3. 连续型变量 (年龄、眼轴、等效球镜等)
    # ==========================================
    continuous_vars = {
        'Age': '年龄 (岁)',
        'Axial length (mm)': '眼轴长度 (axial_len, mm)',
        'Cornea curvature (mm)': '角膜曲率 (r1, mm)',
        'Anterior chamber depth (mm)': '前房深度 (acd, mm)',
        'Spherical equivalent refraction (D)': '等效球镜 (ser, D)'
    }

    # 如果表格里有 RMF，自动补充
    if 'RMF' in df.columns or 'rmf' in df.columns:
        rmf_col = 'RMF' if 'RMF' in df.columns else 'rmf'
        continuous_vars[rmf_col] = 'RMF'

    for col, display_name in continuous_vars.items():
        if col in df.columns:
            # 分别提取 总体、Normal组、ASO组 的有效数据 (丢弃缺失值)
            t_data = df[col].dropna()
            n_data = normal_df[col].dropna()
            a_data = aso_df[col].dropna()

            # 计算各自的均值与标准差
            mean_t, std_t = t_data.mean(), t_data.std()
            mean_n, std_n = n_data.mean(), n_data.std()
            mean_a, std_a = a_data.mean(), a_data.std()

            results.append({
                '眼部/人口学参数': display_name,
                f'Total (N={n_total})': f"{mean_t:.2f} ± {std_t:.2f}" if not np.isnan(mean_t) else "N/A",
                f'Normal (N={n_normal})': f"{mean_n:.2f} ± {std_n:.2f}" if not np.isnan(mean_n) else "N/A",
                f'ASO (N={n_aso})': f"{mean_a:.2f} ± {std_a:.2f}" if not np.isnan(mean_a) else "N/A"
            })

    # ==========================================
    # 打印与保存
    # ==========================================
    result_df = pd.DataFrame(results)

    print("\n" + "=" * 70)
    print(result_df.to_string(index=False))
    print("=" * 70)

    # 保存为 CSV
    out_file = "../genData/sum/临床特征统计表.csv"
    result_df.to_csv(out_file, index=False, encoding='utf-8-sig')

    return result_df


def generate_11_distance_datasets(df_with_angular, output_dir="../genData/distance_datasets"):
    """
    【注意：此 11 距离文件流当前未被分析脚本直接读取，主流程使用 gen_44ROIData.py 生成的 44 ROI 文件】
    针对 11 个空间距离，求 4 个象限（剔除异常血管）的各项微观特征平均值，
    并严格按照要求的格式输出为 data0.csv 到 data10.csv。
    该函数保留为备用/快速查看用途。
    """
    print("=" * 70)
    print("📊 开始生成终极格式的 11 个子数据集 (data0.csv - data10.csv)...")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for k in range(11):
        # 精准定位当前距离对应的 4 个象限 ROI 编号
        roi_nums = [k + 1, k + 12, k + 23, k + 34]
        distance_mm = 1.0 + k * 0.5

        records = []
        for index, row in df_with_angular.iterrows():
            # 临时存放 4 个象限的各项微观指标
            valid_linear = []
            valid_angular = []
            valid_spacing = []
            valid_dispersion = []
            valid_regularity = []

            # 遍历四个象限，进行血管和缺失值筛查
            for roi in roi_nums:
                bvr_col = f'Blood_Vessel_Ratio_ROI_{roi}'
                if bvr_col in row and pd.notna(row[bvr_col]) and row[bvr_col] <= 0.25:

                    den_col = f'Cone_Density_ROI_{roi}'
                    ang_col = f'Angular_Cone_Density_ROI_{roi}'
                    spa_col = f'Cone_Spacing_ROI_{roi}'
                    dis_col = f'Cone_Dispersion_ROI_{roi}'
                    reg_col = f'Cone_Regularity_ROI_{roi}'

                    # 确保细胞密度不是缺失的
                    if pd.notna(row.get(den_col)):
                        valid_linear.append(row[den_col])
                        valid_angular.append(row[ang_col])

                        # 把间距、离散度和规则性也加进来（如果存在的话）
                        if pd.notna(row.get(spa_col)): valid_spacing.append(row[spa_col])
                        if pd.notna(row.get(dis_col)): valid_dispersion.append(row[dis_col])
                        if pd.notna(row.get(reg_col)): valid_regularity.append(row[reg_col])

            # 如果该距离下至少有一个象限有效，则计算平均并记录
            if valid_linear:
                # 处理单位：如果你的表里是米(0.007)，在存入 CSV 时转回毫米(7.0)
                r1_val = row.get('Cornea curvature (mm)', np.nan)
                if pd.notna(r1_val) and r1_val < 0.1:
                    r1_val = r1_val * 1000.0

                acd_val = row.get('Anterior chamber depth (mm)', np.nan)
                if pd.notna(acd_val) and acd_val < 0.1:
                    acd_val = acd_val * 1000.0

                records.append({
                    'Axial length (mm)': row.get('Axial length (mm)', np.nan),
                    'Age': row.get('Age', np.nan),
                    'Eye': row.get('Eye',np.nan),
                    'Spherical equivalent refraction (D)': row.get('Spherical equivalent refraction (D)', np.nan),
                    'Gender': row.get('Gender', np.nan),
                    'Corneal curvature (mm)': r1_val,
                    'Anterior chamber depth (mm)': acd_val,
                    'Retinal magnification factor': row.get('RMF_um_per_deg', np.nan),

                    # 聚合计算平均值
                    'Linear cone density (cones/ mm2)': np.mean(valid_linear),
                    'Angular cone density (cones/ deg2)': np.mean(valid_angular),
                    'Cone spacing': np.mean(valid_spacing) if valid_spacing else np.nan,
                    'Cone dispersion': np.mean(valid_dispersion) if valid_dispersion else np.nan,
                    'Cone regularity': np.mean(valid_regularity) if valid_regularity else np.nan
                })

        # 存入文件
        if records:
            df_k = pd.DataFrame(records)
            # 为了确保数据的纯净度，如果有少数人的等效球镜或者其它核心参数是缺失的，可以在这里 dropna (可选)
            # df_k = df_k.dropna()

            out_file = os.path.join(output_dir, f"data{k}.csv")
            df_k.to_csv(out_file, index=False, encoding='utf-8-sig')

            print(f"✅ 生成 data{k:<2}.csv | 距离: {distance_mm:.1f}mm | 输出行数: {len(df_k)}")
        else:
            print(f"⚠️ 警告: 距离 {distance_mm:.1f}mm 没有符合条件的数据。")

    print("=" * 70)
    print(f"📁 完美！11 个标准格式的数据集均已输出至: {output_dir}")


def get_patient_signature(row):
    """
    提取患者的“生理指纹”。
    由于这 6 个基线特征对于同一只眼睛是绝对固定且唯一的，
    我们可以用它们组合成一个元组，在跨文件时精准识别同一个人。
    """
    return (
        round(row['Axial length (mm)'], 4),
        row['Age'],
        row['Spherical equivalent refraction (D)'],
        row['Gender'],
        round(row['Corneal curvature (mm)'], 4),
        round(row['Anterior chamber depth (mm)'], 4)
    )


def clean_data():
    """
    【注意：此 11 距离文件流当前未被分析脚本直接读取，主流程使用 gen_44ROIData.py 生成的 44 ROI 文件】
    该函数保留为备用/快速查看用途。
    """
    print("=" * 70)
    print("🧹 开始执行智能跨文件数据清洗与连续 Subject_ID 映射 (含排序输出)...")

    DATA_DIR = '../genData/distance_datasets'
    OUT_DIR = '../genData/CleanData'

    if not os.path.exists(DATA_DIR):
        raise FileNotFoundError(f"找不到文件夹: {DATA_DIR}，请确保路径正确！")

    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR)

    file_paths = []
    for f in os.listdir(DATA_DIR):
        if f.startswith('data') and f.endswith('.csv'):
            file_paths.append(os.path.join(DATA_DIR, f))

    file_paths.sort(key=lambda f: int(re.search(r'\d+', os.path.basename(f)).group()))

    if not file_paths:
        print("⚠️ 未找到任何 data*.csv 文件！")
        return

    # ==========================================
    # 第一阶段：全局扫描，建立统一的患者花名册和黑名单
    # ==========================================
    all_signatures = set()
    blacklist_signatures = set()

    for fp in file_paths:
        df = pd.read_csv(fp)
        for _, row in df.iterrows():
            sig = get_patient_signature(row)
            all_signatures.add(sig)

            if row.get('Angular cone density (cones/ deg2)', 0) > 7000:
                blacklist_signatures.add(sig)

    # 剔除黑名单后的纯净“生理指纹”池
    valid_signatures = sorted(list(all_signatures - blacklist_signatures))

    # 生成全局连续的 Subject_ID 映射字典 (从 Eye_001 到 Eye_N)
    subject_id_map = {sig: f"Eye_{i + 1:03d}" for i, sig in enumerate(valid_signatures)}

    print(f"🔍 全局扫描完毕：")
    print(f"   -> 发现异常患者(全局剔除): {len(blacklist_signatures)} 名")
    print(f"   -> 剩余纯净有效患者总数 : {len(valid_signatures)} 名 (已分配 Eye_001 - Eye_{len(valid_signatures):03d})")
    print("-" * 70)

    # ==========================================
    # 第二阶段：逐文件追加特征、排序并保存
    # ==========================================
    for fp in file_paths:
        filename = os.path.basename(fp)
        k = int(re.search(r'\d+', filename).group())
        ecc_value = 1.0 + k * 0.5

        df = pd.read_csv(fp)
        cleaned_records = []

        for _, row in df.iterrows():
            sig = get_patient_signature(row)

            if sig in subject_id_map:
                row_dict = row.to_dict()

                # 强制将 Subject_ID 和 Eccentricity 放在最前面
                new_row = {
                    'Subject_ID': subject_id_map[sig],
                    'Eccentricity (mm)': ecc_value
                }
                new_row.update(row_dict)
                cleaned_records.append(new_row)

        # 转换为 DataFrame
        if cleaned_records:
            df_cleaned = pd.DataFrame(cleaned_records)

            # ==========================================
            # 🌟 新增核心：对 DataFrame 按 Subject_ID 排序
            # ==========================================
            df_cleaned = df_cleaned.sort_values(by='Subject_ID').reset_index(drop=True)

            # 保存
            out_file = os.path.join(OUT_DIR, filename)
            df_cleaned.to_csv(out_file, index=False, encoding='utf-8-sig')
            print(f"✅ 保存 {filename:<10} | 偏心率: {ecc_value:>4.1f} mm | 匹配有效样本: {len(df_cleaned)}")
        else:
            print(f"⚠️ {filename} 清洗后无有效数据！")

    print("=" * 70)
    print(f"📁 带有排序后连续 Subject_ID 的数据已保存至: {OUT_DIR}")

# ========== 测试执行区 ==========
if __name__ == "__main__":
    df = pd.read_csv('../orgData/orgData.csv')
    #加入角密度信息
    df = add_angular_density(df)
    df.to_csv('../orgData/orgDataWithAng.csv', index=False, encoding='utf-8-sig')

    # 11组数据
    generate_11_distance_datasets(df)
    clean_data()




    generate_baseline_table_total(df)


