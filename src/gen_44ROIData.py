import pandas as pd
import numpy as np
import os

# ==========================================
# 可配置常量
# ==========================================
# 角密度异常值阈值 (cones/deg^2)；任意 ROI 超过此值则剔除该眼
ANGULAR_DENSITY_OUTLIER_THRESHOLD = 7000

# 血管占比质量控制阈值
BLOOD_VESSEL_RATIO_THRESHOLD = 0.25


def fix_unit_mm(val, param_name):
    """
    稳健的单位转换：基于临床合理范围判断角膜曲率和前房深度的单位。
    - 角膜曲率正常范围约 6-9 mm
    - 前房深度正常范围约 2-4 mm
    """
    if pd.isna(val):
        return val

    if param_name in ['Corneal curvature (mm)', 'Anterior chamber depth (mm)']:
        # 如果值小于 0.01，大概率是米 (m) -> 转换为毫米
        if val < 0.01:
            fixed = val * 1000.0
            print(f"   🔄 单位转换: {param_name} 原始值 {val:.6f} -> {fixed:.6f} (m -> mm)")
            return fixed
        # 如果值大于 100，大概率是微米 (um) -> 转换为毫米
        elif val > 100.0:
            fixed = val / 1000.0
            print(f"   🔄 单位转换: {param_name} 原始值 {val:.6f} -> {fixed:.6f} (um -> mm)")
            return fixed

    return val


def get_patient_signature(row):
    """
    提取患者的基线生理指纹，用于跨文件绝对对齐 Subject_ID。
    仅在无法通过 Patient_ID 直接映射时作为回退方案。
    """
    return (
        round(row.get('Axial length (mm)', 0), 4),
        row.get('Age', 0),
        row.get('Spherical equivalent refraction (D)', 0),
        row.get('Gender', 0),
        round(row.get('Corneal curvature (mm)', 0), 4),
        round(row.get('Anterior chamber depth (mm)', 0), 4)
    )


def load_subject_mapping(pair_path='../genData/sum/Subject_Pair_Mapping.csv'):
    """
    读取 Subject_Pair_Mapping.csv，建立 Patient_ID -> Subject_ID 的稳定映射。
    """
    patient_to_subject = {}

    if not os.path.exists(pair_path):
        print(f"⚠️ 警告: 找不到 {pair_path}，将无法映射真实 Subject_ID，只能回退到生理指纹。")
        return patient_to_subject

    pairs = pd.read_csv(pair_path)

    # 兼容可能的列名大小写
    col_aliases = {
        'od': ['OD_PatientID', 'od_patientid', 'OD_Patient_ID'],
        'os': ['OS_PatientID', 'os_patientid', 'OS_Patient_ID'],
        'subject': ['Subject_ID', 'subject_id', 'SubjectID']
    }

    def find_col(candidates):
        for c in candidates:
            matches = [col for col in pairs.columns if col.lower() == c.lower()]
            if matches:
                return matches[0]
        return None

    od_col = find_col(col_aliases['od'])
    os_col = find_col(col_aliases['os'])
    subj_col = find_col(col_aliases['subject'])

    if not all([od_col, os_col, subj_col]):
        print(f"⚠️ 警告: Subject_Pair_Mapping.csv 缺少必要列 (OD/OS/Subject_ID)，无法建立映射。")
        return patient_to_subject

    for _, row in pairs.iterrows():
        subject_id = str(row[subj_col]).strip()
        for pid_col in [od_col, os_col]:
            pid = row[pid_col]
            if pd.notna(pid):
                # 统一为字符串，去除 .0 后缀
                pid_str = str(int(float(pid))) if str(pid).replace('.', '').replace('-', '').isdigit() else str(pid).strip()
                patient_to_subject[pid_str] = subject_id

    print(f"✅ 已加载 Subject 映射: {len(patient_to_subject)} 个 Patient_ID -> {pairs[subj_col].nunique()} 个 Subject_ID")
    return patient_to_subject


def generate_44_roi_datasets(df_master, out_dir="data_44_ROIs", blacklist_mode="strict"):
    """
    将包含所有 44 个 ROI 的宽表，彻底拆分为 44 个独立的 dataX.csv 文件。
    每个文件对应 1 个具体的 ROI 区域。

    参数:
        blacklist_mode: "strict" 或 "lenient"
            - strict: 任意单个 ROI 的 Angular Density > 阈值则剔除该眼 (默认, 69 眼)
            - lenient: 仅当某距离的 4 象限平均 Angular Density > 阈值才剔除该眼 (71 眼)
    """
    print("=" * 75)
    print(f"🗂️ 开始将 44 个 ROI 独立存储为 44 个 CSV 文件至 {out_dir}/ ...")
    print(f"   -> 黑名单模式: {blacklist_mode} (阈值: {ANGULAR_DENSITY_OUTLIER_THRESHOLD})")

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # ==========================================
    # 1. 加载 Patient_ID -> Subject_ID 映射
    # ==========================================
    patient_to_subject = load_subject_mapping()

    # ==========================================
    # 2. 全局分配连续的 Subject_ID (保持绝对对齐)
    # ==========================================
    all_patient_ids = set()
    blacklist_patient_ids = set()
    fallback_sigs = set()

    # 异常值扫描
    for _, row in df_master.iterrows():
        patient_id = str(row.get('Patient ID', '')).strip()
        if patient_id:
            all_patient_ids.add(patient_id)

        if blacklist_mode == "strict":
            # strict: 任意单个 ROI 的 Angular Density > 阈值则剔除
            for roi in range(1, 45):
                ang_col = f'Angular_Cone_Density_ROI_{roi}'
                if pd.notna(row.get(ang_col)) and row.get(ang_col) > ANGULAR_DENSITY_OUTLIER_THRESHOLD:
                    if patient_id:
                        blacklist_patient_ids.add(patient_id)
                    else:
                        fallback_sigs.add(get_patient_signature(row))
                    break
        else:
            # lenient: 仅当某距离的 4 象限平均 Angular Density > 阈值才剔除
            # 只纳入血管占比 <= 阈值的 ROI，与 DataCheck.py 逻辑一致
            for dist_idx in range(11):
                roi_nums = [dist_idx + 1, dist_idx + 12, dist_idx + 23, dist_idx + 34]
                valid_vals = []
                for roi in roi_nums:
                    ang_col = f'Angular_Cone_Density_ROI_{roi}'
                    bvr_col = f'Blood_Vessel_Ratio_ROI_{roi}'
                    ang_val = row.get(ang_col)
                    bvr_val = row.get(bvr_col)
                    if pd.notna(ang_val) and pd.notna(bvr_val) and bvr_val <= BLOOD_VESSEL_RATIO_THRESHOLD:
                        valid_vals.append(ang_val)
                if valid_vals and (sum(valid_vals) / len(valid_vals)) > ANGULAR_DENSITY_OUTLIER_THRESHOLD:
                    if patient_id:
                        blacklist_patient_ids.add(patient_id)
                    else:
                        fallback_sigs.add(get_patient_signature(row))
                    break

    # 收集剔除日志
    outlier_log = []
    for _, row in df_master.iterrows():
        patient_id = str(row.get('Patient ID', '')).strip()
        eye = str(row.get('Eye', '')).strip()

        if blacklist_mode == "strict":
            for roi in range(1, 45):
                ang_col = f'Angular_Cone_Density_ROI_{roi}'
                val = row.get(ang_col)
                if pd.notna(val) and val > ANGULAR_DENSITY_OUTLIER_THRESHOLD:
                    outlier_log.append({
                        'Patient_ID': patient_id,
                        'Eye': eye,
                        'ROI_Number': roi,
                        'Angular_Density': val,
                        'Threshold': ANGULAR_DENSITY_OUTLIER_THRESHOLD,
                        'Exclusion_Reason': f'Strict: Single_ROI_Angular_Density > {ANGULAR_DENSITY_OUTLIER_THRESHOLD}'
                    })
        else:
            for dist_idx in range(11):
                roi_nums = [dist_idx + 1, dist_idx + 12, dist_idx + 23, dist_idx + 34]
                valid_vals = []
                for roi in roi_nums:
                    ang_col = f'Angular_Cone_Density_ROI_{roi}'
                    bvr_col = f'Blood_Vessel_Ratio_ROI_{roi}'
                    ang_val = row.get(ang_col)
                    bvr_val = row.get(bvr_col)
                    if pd.notna(ang_val) and pd.notna(bvr_val) and bvr_val <= BLOOD_VESSEL_RATIO_THRESHOLD:
                        valid_vals.append(ang_val)
                if valid_vals and (sum(valid_vals) / len(valid_vals)) > ANGULAR_DENSITY_OUTLIER_THRESHOLD:
                    avg_val = sum(valid_vals) / len(valid_vals)
                    outlier_log.append({
                        'Patient_ID': patient_id,
                        'Eye': eye,
                        'ROI_Number': f'Distance_{1.0 + dist_idx * 0.5}mm',
                        'Angular_Density': avg_val,
                        'Threshold': ANGULAR_DENSITY_OUTLIER_THRESHOLD,
                        'Exclusion_Reason': f'Lenient: Distance_Avg_Angular_Density > {ANGULAR_DENSITY_OUTLIER_THRESHOLD}'
                    })
                    break

    valid_patient_ids = sorted(list(all_patient_ids - blacklist_patient_ids))

    # 生成 Eye_xxx 映射（按 Patient_ID 排序，稳定可复现）
    eye_id_map = {pid: f"Eye_{i + 1:03d}" for i, pid in enumerate(valid_patient_ids)}

    # 回退映射：当 Patient_ID 为空时，用生理指纹生成临时 ID
    fallback_sig_map = {sig: f"Eye_TMP_{i + 1:03d}" for i, sig in enumerate(sorted(fallback_sigs))}

    print(f"🔍 剔除极端异常后，共锁定 {len(valid_patient_ids)} 名有效患者（另有 {len(fallback_sigs)} 个无 Patient_ID 的回退样本）。")
    print(f"   -> 黑名单患者数: {len(blacklist_patient_ids)}")
    print("-" * 75)

    # 保存剔除日志
    sum_dir = '../genData/sum'
    os.makedirs(sum_dir, exist_ok=True)
    log_suffix = 'strict' if blacklist_mode == 'strict' else 'lenient'
    if outlier_log:
        pd.DataFrame(outlier_log).to_csv(
            os.path.join(sum_dir, f'outlier_exclusion_log_{log_suffix}.csv'),
            index=False,
            encoding='utf-8-sig'
        )
        print(f"📝 已保存异常值剔除日志: {sum_dir}/outlier_exclusion_log_{log_suffix}.csv (共 {len(outlier_log)} 条)")

    # ==========================================
    # 3. 遍历 1 到 44，生成独立的 dataX.csv
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
            patient_id = str(row.get('Patient ID', '')).strip()

            # 黑名单检查
            if patient_id and patient_id in blacklist_patient_ids:
                continue

            # 获取稳定的 Eye_xxx 标签
            if patient_id and patient_id in eye_id_map:
                eye_label = eye_id_map[patient_id]
            else:
                sig = get_patient_signature(row)
                if sig in fallback_sig_map:
                    eye_label = fallback_sig_map[sig]
                else:
                    continue

            # 获取真实 Subject_ID
            subject_id = patient_to_subject.get(patient_id, f"Single_{patient_id}" if patient_id else eye_label)

            # 质量控制：必须存在血管遮挡率且 <= 阈值，密度不为 NaN
            if (bvr_col in row and pd.notna(row[bvr_col]) and row[bvr_col] <= BLOOD_VESSEL_RATIO_THRESHOLD) and pd.notna(row.get(den_col)):

                # 修复单位问题
                r1_val = row.get('Cornea curvature (mm)', np.nan)
                r1_val = fix_unit_mm(r1_val, 'Corneal curvature (mm)')
                acd_val = row.get('Anterior chamber depth (mm)', np.nan)
                acd_val = fix_unit_mm(acd_val, 'Anterior chamber depth (mm)')

                # 写入标准化的列名（去掉了末尾的 ROI 编号，让下游模型读取时更通用）
                records.append({
                    'Subject_ID': subject_id,
                    'Eye_Label': eye_label,
                    'Patient_ID': patient_id if patient_id else np.nan,
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
            df_roi = df_roi.sort_values(by=['Subject_ID', 'Eye']).reset_index(drop=True)

            out_file = os.path.join(out_dir, f"data{roi}.csv")
            df_roi.to_csv(out_file, index=False, encoding='utf-8-sig')

            # 为了控制台不刷屏太严重，我们可以格式化输出
            print(
                f"✅ 生成 {f'data{roi}.csv':<10} | 偏心率: {distance_mm:.1f}mm | 象限: {quadrant.split(' ')[0]:<2} | 有效行数: {len(df_roi)}")
        else:
            print(f"⚠️ 警告: ROI {roi} 的区域中所有患者的数据均被剔除或缺失！")

    print("=" * 75)
    print(f"📁 完美！44 个独立的标准数据集均已输出至: {out_dir}/")

    return eye_id_map, patient_to_subject


# ========== 测试执行 ==========
if __name__ == "__main__":
    # 假设你已经有了计算完 Angular Density 的原始大宽表 df_with_angular
    df_master = pd.read_csv("../orgData/orgDataWithAng.csv")

    # 生成两套 44 ROI 数据：严格模式 (69 眼) 和 宽松模式 (71 眼)
    configs = [
        ('strict', '../genData/CleanDataRoi_strict', '../genData/sum/Eye_to_Subject_Mapping_strict.csv'),
        ('lenient', '../genData/CleanDataRoi_lenient', '../genData/sum/Eye_to_Subject_Mapping_lenient.csv'),
    ]

    for mode, out_dir, mapping_path in configs:
        print("\n" + "=" * 75)
        print(f"🚀 开始生成 {mode.upper()} 模式数据...")
        print("=" * 75)
        eye_id_map, patient_to_subject = generate_44_roi_datasets(
            df_master,
            out_dir=out_dir,
            blacklist_mode=mode
        )

        # 生成权威 ID 对照表
        if eye_id_map:
            mapping_records = []
            for pid, eye_label in eye_id_map.items():
                mapping_records.append({
                    'Eye_Label': eye_label,
                    'Patient_ID': pid,
                    'Subject_ID': patient_to_subject.get(pid, f"Single_{pid}"),
                })
            df_mapping = pd.DataFrame(mapping_records).sort_values('Eye_Label').reset_index(drop=True)
            df_mapping.to_csv(mapping_path, index=False, encoding='utf-8-sig')
            print(f"📁 已生成权威 ID 对照表: {mapping_path}")

    print("\n" + "=" * 75)
    print("🎉 两套 44 ROI 数据生成完毕！")
    print("=" * 75)
    pass
