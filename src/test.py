import pandas as pd
import numpy as np
import os
import re
import glob


def flatten_patient_to_44_rois(file_path):
    """
    读取单病历，将44个ROI点完全水平展开为一行，
    如果缺失某ROI则打印警告并用 NaN 填充。
    """
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"⚠️ 读取文件失败 {file_path}: {e}")
        return None

    if df.empty or len(df) < 2:
        return None

    # ==========================================
    # 1. 提取全局基础信息
    # ==========================================
    base_info = df.iloc[0]

    name = str(base_info.get('患者姓名', 'Unknown')).strip()
    fig_num = str(base_info.get('图像编号', '')).strip()
    eye_str = str(base_info.get('眼别', '')).strip().upper()
    gender = 1 if str(base_info.get('性别', '')).strip() == '男' else 0

    # 计算年龄
    try:
        birthday_str = str(base_info.get('生日', '')).replace('-', '/').strip()
        birthday = pd.to_datetime(birthday_str, errors='coerce')

        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', os.path.basename(file_path))
        exam_date = pd.to_datetime(date_match.group(1)) if date_match else pd.Timestamp.now()

        if pd.notna(birthday) and pd.notna(exam_date):
            age = exam_date.year - birthday.year - ((exam_date.month, exam_date.day) < (birthday.month, birthday.day))
        else:
            age = np.nan
    except Exception:
        age = np.nan

    # 判断来源
    source_class = 0 if 'normal' in file_path.lower() else 1

    # ==========================================
    # 2. 清洗微观数据并进行 ROI 缺失检查
    # ==========================================
    data = df.iloc[1:].copy()

    # 数据格式清洗 (根据上一步要求，不进行血管占比剔除，保留所有数据)
    data['血管占比'] = data['血管占比'].astype(str).str.replace('%', '', regex=False).astype(float) / 100.0
    data['离散度'] = data['离散度'].astype(str).str.replace('%', '', regex=False).astype(float)
    data['规则性'] = data['规则性'].astype(str).str.replace('%', '', regex=False).astype(float)
    data['细胞密度(/mm2)'] = data['细胞密度(/mm2)'].astype(float)
    data['细胞间距(μm)'] = data['细胞间距(μm)'].astype(float)

    # 精准提取 ROI 编号 (从 ROI001 提取出整数 1)
    data['roi_num'] = data['整图或ROI'].astype(str).str.extract(r'(\d+)').astype(float)
    data = data.dropna(subset=['roi_num'])
    data['roi_num'] = data['roi_num'].astype(int)

    # 🌟 缺失值检查机制：预期包含 1 到 44 的所有 ROI
    existing_rois = set(data['roi_num'].tolist())
    expected_rois = set(range(1, 45))
    missing_rois = expected_rois - existing_rois

    if missing_rois:
        print(
            f"⚠️ 警告: 患者 [{name}] (ID: {fig_num}, {eye_str}) 丢失了 {len(missing_rois)} 个 ROI 数据，缺失编号为: {sorted(list(missing_rois))}")

    # ==========================================
    # 3. 将 44 个 ROI 水平拉平组装
    # ==========================================
    features = {
        'Patient_ID': fig_num,
        'Eye': eye_str,
        'Age': age,
        'Gender': gender,
        'Source_Class': source_class,
        'Eye_Type_Num': 1 if eye_str == 'OD' else 0,
        'Field_Size': base_info.get('视场大小', np.nan)
    }

    # 为了快速查找，将 roi_num 设为索引
    data_indexed = data.set_index('roi_num')

    # 循环 1 到 44，将每一项特征展开并规范命名
    for i in range(1, 45):
        if i in data_indexed.index:
            row = data_indexed.loc[i]
            # 防御机制：如果表格里不小心有两个同名的 ROI，取第一个
            if isinstance(row, pd.DataFrame):
                row = row.iloc[0]

            features[f'Blood_Vessel_Ratio_ROI_{i}'] = row['血管占比']
            features[f'Cone_Density_ROI_{i}'] = row['细胞密度(/mm2)']
            features[f'Cone_Spacing_ROI_{i}'] = row['细胞间距(μm)']
            features[f'Cone_Dispersion_ROI_{i}'] = row['离散度']
            features[f'Cone_Regularity_ROI_{i}'] = row['规则性']
        else:
            # 对于确实丢失的 ROI，填充 NaN 保持矩阵结构不变
            features[f'Blood_Vessel_Ratio_ROI_{i}'] = np.nan
            features[f'Cone_Density_ROI_{i}'] = np.nan
            features[f'Cone_Spacing_ROI_{i}'] = np.nan
            features[f'Cone_Dispersion_ROI_{i}'] = np.nan
            features[f'Cone_Regularity_ROI_{i}'] = np.nan

    return features


# ========== 测试与批量拉平区 ==========
if __name__ == "__main__":
    all_files = glob.glob('../orgData/srx-ao-slo/*.csv') + glob.glob('../orgData/Normal/*.csv')

    flattened_dataset = []

    print(f"开始批量拉平读取，共找到 {len(all_files)} 个文件...\n" + "-" * 50)

    for f in all_files:
        patient_row = flatten_patient_to_44_rois(f)
        if patient_row is not None:
            flattened_dataset.append(patient_row)

    if flattened_dataset:
        df_ml = pd.DataFrame(flattened_dataset)

        print("-" * 50)
        print(f"✅ 拉平完成！最终生成的机器学习矩阵形状 (Samples, Features): {df_ml.shape}")
        print("该矩阵包含：\n- 1 行 = 1 个患者的 1 只眼\n- 全局特征 + (44 个区域 × 5 种指标) = 近 230 个特征列！")

        # 打印头几行与头几个 ROI 预览一下
        preview_cols = ['Patient_ID', 'Eye', 'Source_Class', 'Cone_Density_ROI_1', 'Cone_Density_ROI_44']
        # 防御性展示：确保列存在
        show_cols = [c for c in preview_cols if c in df_ml.columns]
        print("\n---> 数据预览 (截取首尾 ROI 列):")
        print(df_ml[show_cols].head())