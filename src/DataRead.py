import pandas as pd
import numpy as np
import os
import glob
import re

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
        'Patient ID': fig_num,
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


def load_and_clean_axial_data(axial_files):
    axial_dfs = []

    for f in axial_files:
        df = pd.read_csv(f)

        # 强力清洗列名：去除前后的空格、制表符、换行符（防止肉眼看不见的特殊字符导致 KeyError）
        df.columns = df.columns.str.strip().str.replace('\n', '').str.replace('\r', '')

        # 🌟 Debug 打印：看看实际清洗后的列名到底是什么
        print(f"\n---> 正在读取眼轴文件: {f}")
        print(f"---> 包含的列名有: {df.columns.tolist()}")

        # 1. 自动标注来源 (Normal 或 ASO)
        # 观察你的文件名，有一个叫 'axial_normal.xlsx - Sheet1.csv'
        # 我们根据文件名中是否包含 'normal' (不区分大小写) 来打标签
        file_name = os.path.basename(f).lower()
        if 'normal' in file_name:
            df['Source'] = 'Normal'
            df['Source_Class'] = 0  # 机器学习常用的数值型标签
        else:
            df['Source'] = 'ASO'
            df['Source_Class'] = 1

        axial_dfs.append(df)

    if not axial_dfs:
        print("警告：没有找到任何眼轴数据文件！请检查路径。")
        return pd.DataFrame()  # 返回空表防报错

    axial_df = pd.concat(axial_dfs, ignore_index=True)

    # ⚠️ 这里的列名需要根据你上面 print 出来的实际结果进行修改！
    id_col = 'Patient ID'  # 如果打印出来叫 'ID'，请改为 'ID'
    eye_col = 'Eye'  # 如果打印出来叫 '眼别'，请改为 '眼别'
    age_col = 'Age'  # 假设表里的列名叫 'Age' 或 '年龄'
    gender_col = 'Gender'  # 假设表里的列名叫 'Gender' 或 '性别'

    # 清洗 ID 格式 (如果找不到列，先跳过防止报错崩溃，方便看 debug 信息)
    if id_col in axial_df.columns:
        axial_df[id_col] = axial_df[id_col].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    else:
        print(f"⚠️ 严重警告: 在表头中找不到名为 '{id_col}' 的列，请务必根据打印结果修改 id_col 变量！")

    # 清理 Eye 字段：统一大写，修正 0S 为 OS
    if eye_col in axial_df.columns:
        axial_df[eye_col] = axial_df[eye_col].astype(str).str.strip().str.upper()
        axial_df[eye_col] = axial_df[eye_col].replace('0S', 'OS')

    # 把 年龄、性别、来源 全部加入我们要保留的特征列表中
    desired_cols = [
        id_col, eye_col,
        age_col, gender_col,  # 新增：年龄与性别
        'Source', 'Source_Class',  # 新增：数据来源
        'Spherical equivalent refraction (D)',
        'Axial length (mm)',
        'Cornea curvature (mm)',
        'Anterior chamber depth (mm)'
    ]

    # 防御性编程：如果你的表格里暂缺某些列（比如还没改age_col名字），这段代码只保留真实存在的列，不会报错
    cols_to_keep = [c for c in desired_cols if c in axial_df.columns]

    # 如果核心去重键存在，则去重；否则直接返回
    if id_col in cols_to_keep and eye_col in cols_to_keep:
        return axial_df[cols_to_keep].drop_duplicates(subset=[id_col, eye_col])
    else:
        return axial_df[cols_to_keep]


def merge_and_diagnose(df_patients, df_axial):
    """
    合并患者特征表与眼轴表，并详细打印出无法匹配的数据诊断报告。

    参数:
    df_patients: 包含了拉平后微观特征(ROI 1-44)的宽表 DataFrame
    df_axial: 包含了眼轴长度等信息的 DataFrame
    """
    df_patients['Patient ID'] = df_patients['Patient ID'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    df_axial['Patient ID'] = df_axial['Patient ID'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

    # 统一眼别格式，防患于未然
    df_patients['Eye'] = df_patients['Eye'].astype(str).str.strip().str.upper()
    df_axial['Eye'] = df_axial['Eye'].astype(str).str.strip().str.upper()

    print("=" * 50)
    print("开始数据合并与匹配诊断...")

    duplicates = df_patients[df_patients.duplicated(subset=['Patient ID', 'Eye'], keep=False)]

    if duplicates.empty:
        print("✅ 完美！左表中没有发现任何重复的患者眼部数据。")

    else:
        # 统计到底有多少组重复数据
        dup_groups = duplicates.groupby(['Patient ID', 'Eye']).size().reset_index(name='出现次数')

        print(f"⚠️ 警告: 发现 {len(dup_groups)} 组重复录入的患者数据！")
        print("-" * 30)

        for _, row in dup_groups.iterrows():
            print(f"   -> ID: {row['Patient ID']}, Eye: {row['Eye']}  (共出现了 {row['出现次数']} 次)")


    
    print("=" * 50)
    print("开始数据合并与匹配诊断...")
    print(f"参与合并的患者记录数 (左表): {len(df_patients)}")
    print(f"参与合并的眼轴记录数 (右表): {len(df_axial)}")

    # 1. 解决列名冲突：剔除 df_axial 中与 df_patients 重复的基础信息列
    # 只保留关键的医学测量指标和合并主键
    cols_to_drop = ['Gender', 'Source', 'Source_Class']
    # 防御性剔除：确保这些列确实存在才剔除
    cols_to_drop = [c for c in cols_to_drop if c in df_axial.columns]
    df_axial_clean = df_axial.drop(columns=cols_to_drop)

    # 2. 执行外连接，并开启匹配指示器
    # how='outer' 保证任何一边的数据都不会被直接丢弃
    merged_df = pd.merge(
        df_patients,
        df_axial_clean,
        on=['Patient ID', 'Eye'],
        how='outer',
        indicator=True
    )

    # 2.5 处理年龄列冲突：以眼轴表（右表）中的 Age 为权威年龄
    # merge 后可能出现 Age_x（来自 df_patients）和 Age_y（来自 df_axial）
    if 'Age_x' in merged_df.columns and 'Age_y' in merged_df.columns:
        # 权威年龄来自眼轴文件；若缺失则回退到文件计算年龄
        merged_df['Age'] = merged_df['Age_y'].fillna(merged_df['Age_x'])
        merged_df = merged_df.drop(columns=['Age_x', 'Age_y'])
    # 若只有一边有 Age，列名保持不变

    # 3. 诊断报告提取
    matched = merged_df[merged_df['_merge'] == 'both']
    missing_axial = merged_df[merged_df['_merge'] == 'left_only']
    missing_patient = merged_df[merged_df['_merge'] == 'right_only']

    print("\n" + "=" * 50)
    print("📊 合并诊断报告")
    print("=" * 50)
    print(f"✅ 完美匹配的数据行数: {len(matched)}")

    print(f"\n⚠️ 有患者特征，但【缺少眼轴数据】的行数: {len(missing_axial)}")
    if not missing_axial.empty:
        print("未匹配名单 (Patient ID, Eye):")
        for _, row in missing_axial.iterrows():
            print(f"   -> ID: {row['Patient ID']}, Eye: {row['Eye']}")

    print(f"\n⚠️ 有眼轴数据，但【缺少患者特征CSV】的行数: {len(missing_patient)}")
    if not missing_patient.empty:
        print("未匹配名单 (Patient ID, Eye):")
        for _, row in missing_patient.iterrows():
            print(f"   -> ID: {row['Patient ID']}, Eye: {row['Eye']}")

    # 4. 将丢弃情况写入审计日志
    os.makedirs('../genData/sum', exist_ok=True)
    exclusion_log = []
    for _, row in missing_axial.iterrows():
        exclusion_log.append({
            'Patient_ID': row['Patient ID'],
            'Eye': row['Eye'],
            'Reason': 'missing_axial'
        })
    for _, row in missing_patient.iterrows():
        exclusion_log.append({
            'Patient_ID': row['Patient ID'],
            'Eye': row['Eye'],
            'Reason': 'missing_patient_csv'
        })
    if exclusion_log:
        pd.DataFrame(exclusion_log).to_csv(
            '../genData/sum/merge_exclusion_log.csv',
            index=False,
            encoding='utf-8-sig'
        )
        print(f"\n📝 已保存合并丢弃日志: ../genData/sum/merge_exclusion_log.csv (共 {len(exclusion_log)} 条)")

    print("\n" + "=" * 50)
    print(f"🚀 最终生成的机器学习宽表形状: {matched.shape}")
    print("提示：对于没有眼轴数据的患者，其对应眼轴特征列已自动填充为 NaN。")
    print("后续可使用 sklearn 的 SimpleImputer 进行缺失值插补。")
    print("=" * 50)

    return matched



axial_files = glob.glob('../orgData/AxialLength/*.csv')  # 或者把 Excel 转成了 csv 的文件路径
df_axial = load_and_clean_axial_data(axial_files)

test_files = glob.glob('../orgData/srx-ao-slo/*.csv') + glob.glob('../orgData/Normal/*.csv')

dataset = []
for f in test_files:
    # print(f"正在处理文件: {f}")
    res = flatten_patient_to_44_rois(f)
    if res:
        dataset.append(res)

if dataset:
    df_test = pd.DataFrame(dataset)
else:
    print("未能成功提取数据，请检查文件路径或文件内容。")

df = merge_and_diagnose(df_test,df_axial)
df.to_csv('../orgData/orgData.csv', index=False, encoding='utf-8-sig')


pass