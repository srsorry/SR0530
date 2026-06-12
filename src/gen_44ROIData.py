import pandas as pd
import numpy as np
import os


def get_patient_signature(row):
    """提取患者的基线生理指纹，用于跨文件绝对对齐 Subject_ID"""
    return (
        round(row.get('Axial length (mm)', 0), 4),
        row.get('Age', 0),
        row.get('Spherical equivalent refraction (D)', 0),
        row.get('Gender', 0),
        round(row.get('Corneal curvature (mm)', 0), 4),
        round(row.get('Anterior chamber depth (mm)', 0), 4)
    )


def generate_44_roi_datasets(df_master, out_dir="data_44_ROIs"):
    """
    将包含所有 44 个 ROI 的宽表，彻底拆分为 44 个独立的 dataX.csv 文件。
    每个文件对应 1 个具体的 ROI 区域。
    """
    print("=" * 75)
    print(f"🗂️ 开始将 44 个 ROI 独立存储为 44 个 CSV 文件至 {out_dir}/ ...")

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # ==========================================
    # 1. 全局分配连续的 Subject_ID (保持绝对对齐)
    # ==========================================
    all_signatures = set()
    blacklist_signatures = set()

    # 异常值扫描 (如果任意 ROI 的 Angular Density > 7000，拉黑该患者)
    for _, row in df_master.iterrows():
        sig = get_patient_signature(row)
        all_signatures.add(sig)

        for roi in range(1, 45):
            ang_col = f'Angular_Cone_Density_ROI_{roi}'
            if pd.notna(row.get(ang_col)) and row.get(ang_col) > 7000:
                blacklist_signatures.add(sig)
                break

    valid_signatures = sorted(list(all_signatures - blacklist_signatures))
    subject_id_map = {sig: f"Eye_{i + 1:03d}" for i, sig in enumerate(valid_signatures)}

    print(f"🔍 剔除极端异常后，共锁定 {len(valid_signatures)} 名有效患者。")
    print("-" * 75)

    # ==========================================
    # 2. 遍历 1 到 44，生成独立的 dataX.csv
    # ==========================================
    # 定义 4 个象限的名称
    quadrant_names = ['Q1 (ROI 1-11)', 'Q2 (ROI 12-22)', 'Q3 (ROI 23-33)', 'Q4 (ROI 34-44)']

    for roi in range(1, 45):
        # 通过数学取模运算，智能反推当前 ROI 所属的 偏心率 和 象限
        k = (roi - 1) % 11  # 0 到 10 对应距离的步长
        q_idx = (roi - 1) // 11  # 0 到 3 对应四个象限

        distance_mm = 1.0 + k * 0.5
        quadrant = quadrant_names[q_idx]

        # 锁定当前 ROI 需要读取的列名
        bvr_col = f'Blood_Vessel_Ratio_ROI_{roi}'
        den_col = f'Cone_Density_ROI_{roi}'
        ang_col = f'Angular_Cone_Density_ROI_{roi}'
        spa_col = f'Cone_Spacing_ROI_{roi}'
        dis_col = f'Cone_Dispersion_ROI_{roi}'
        reg_col = f'Cone_Regularity_ROI_{roi}'

        records = []
        for _, row in df_master.iterrows():
            sig = get_patient_signature(row)

            if sig in subject_id_map:
                subject_id = subject_id_map[sig]

                # 质量控制：必须存在血管遮挡率且 <= 25%，密度不为 NaN
                if (bvr_col in row and pd.notna(row[bvr_col]) and row[bvr_col] <= 0.25) and pd.notna(row.get(den_col)):

                    # 修复单位问题
                    r1_val = row.get('Cornea curvature (mm)', np.nan)
                    if pd.notna(r1_val) and r1_val < 0.1: r1_val *= 1000.0
                    acd_val = row.get('Anterior chamber depth (mm)', np.nan)
                    if pd.notna(acd_val) and acd_val < 0.1: acd_val *= 1000.0

                    # 写入标准化的列名（去掉了末尾的 ROI 编号，让下游模型读取时更通用）
                    records.append({
                        'Subject_ID': subject_id,
                        'Eye': row.get('Eye', 'Unknown'),
                        'Eccentricity (mm)': distance_mm,
                        'Quadrant': quadrant,
                        'ROI_Number': roi,

                        'Axial length (mm)': row.get('Axial length (mm)', np.nan),
                        'Age': row.get('Age', np.nan),
                        'Spherical equivalent refraction (D)': row.get('Spherical equivalent refraction (D)', np.nan),
                        'Gender': row.get('Gender', np.nan),
                        'Corneal curvature (mm)': r1_val,
                        'Anterior chamber depth (mm)': acd_val,
                        'Retinal magnification factor': row.get('RMF_um_per_deg', np.nan),

                        'Linear cone density (cones/ mm2)': row[den_col],
                        'Angular cone density (cones/ deg2)': row[ang_col],
                        'Cone spacing': row.get(spa_col, np.nan),
                        'Cone dispersion': row.get(dis_col, np.nan),
                        'Cone regularity': row.get(reg_col, np.nan),
                        'Blood Vessel Ratio': row[bvr_col]
                    })

        # 将当前 ROI 的数据保存为一个表
        if records:
            df_roi = pd.DataFrame(records)
            df_roi = df_roi.sort_values(by='Subject_ID').reset_index(drop=True)

            out_file = os.path.join(out_dir, f"data{roi}.csv")
            df_roi.to_csv(out_file, index=False, encoding='utf-8-sig')

            # 为了控制台不刷屏太严重，我们可以格式化输出
            print(
                f"✅ 生成 {f'data{roi}.csv':<10} | 偏心率: {distance_mm:.1f}mm | 象限: {quadrant.split(' ')[0]:<2} | 有效行数: {len(df_roi)}")
        else:
            print(f"⚠️ 警告: ROI {roi} 的区域中所有患者的数据均被剔除或缺失！")

    print("=" * 75)
    print(f"📁 完美！44 个独立的标准数据集均已输出至: {out_dir}/")


# ========== 测试执行 ==========
if __name__ == "__main__":
    # 假设你已经有了计算完 Angular Density 的原始大宽表 df_with_angular
    df_master = pd.read_csv("../orgData/orgDataWithAng.csv")
    generate_44_roi_datasets(df_master, out_dir="../genData/CleanDataRoi")
    pass