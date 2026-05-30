import numpy as np
import pandas as pd


def cal_rmf_vectorized(axial_len_m, r1_m, acd_m):
    """
    向量化计算 RMF (Retinal Magnification Factor)
    注意：传入的所有参数必须是 国际标准单位 (米, m)
    输出：q (单位: µm/deg)
    """
    P_spec = 0
    lens_roc_f = 10.2e-3
    lens_roc_b = -6e-3

    n_1, n_2, n_3, n_4, n_5 = 1, 1.38, 1.3374, 1.42, 1.336
    t_1 = 14e-3
    t_2 = 0.535e-3
    t_4 = 4e-3
    t_3 = acd_m - t_2
    T = acd_m + t_4

    phi_1 = P_spec
    phi_2 = (n_2 - n_1) / r1_m
    phi_3 = (n_3 - n_2) / (0.8831 * r1_m)
    phi_4 = (n_4 - n_3) / lens_roc_f
    phi_5 = (n_5 - n_4) / lens_roc_b

    # 🌟 核心优化：使用 numpy 数组进行全矩阵追踪
    y = np.ones_like(axial_len_m, dtype=float)
    nu = np.zeros_like(axial_len_m, dtype=float)

    phi_l = [phi_1, phi_2, phi_3, phi_4, phi_5]
    t_list = [t_1, t_2, t_3, t_4]
    n_list = [n_1, n_2, n_3, n_4, n_5]

    # 光线追迹
    for i in range(4):
        nu = nu - y * phi_l[i]
        y = y + nu * t_list[i] / n_list[i]

    nu = nu - y * phi_l[4]

    # 计算基点
    bfl = -y * n_5 / nu
    H2F2 = -n_5 / nu
    F1H1 = H2F2 / n_5

    # 第二节点到视网膜的距离
    N2 = T + bfl - F1H1
    N2_retina = 1000 * (axial_len_m - N2)  # 转为 mm

    # RMF (微米/度)
    q = 1000 * N2_retina * np.tan(np.pi / 180)

    return q


def add_angular_density(df):
    """
    给宽表计算 RMF 并转化为角密度 (cells/deg²)，
    严格检查光学参数，如遇缺失则打印患者信息和原因，并将其直接剔除。
    """
    print("=" * 70)
    print("📐 开始计算 RMF 与 角度细胞密度 (Angular Cone Density)...")

    # 拷贝一份数据，防止直接修改原始 df 报错
    df = df.copy()

    # 核心光学参数列名
    critical_cols = [
        'Axial length (mm)',
        'Cornea curvature (mm)',
        'Anterior chamber depth (mm)'
    ]

    # ==========================================
    # 1. 严格缺失值检查与剔除
    # ==========================================
    # 找出在关键光学列中有任意一个缺失值 (NaN) 的行
    missing_mask = df[critical_cols].isna().any(axis=1)
    problematic_rows = df[missing_mask]

    if not problematic_rows.empty:
        print(f"⚠️ 警告: 检测到 {len(problematic_rows)} 个样本缺失光学参数，将被剔除！\n")
        print("【剔除名单与原因】:")

        for index, row in problematic_rows.iterrows():
            # 兼容不同的 ID 命名习惯
            pid = row.get('Patient_ID', row.get('Patient ID', 'Unknown'))
            eye = row.get('Eye', 'Unknown')

            reasons = []
            if pd.isna(row.get('Axial length (mm)')):
                reasons.append("缺失 眼轴长度")
            if pd.isna(row.get('Cornea curvature (mm)')):
                reasons.append("缺失 角膜曲率 (r1)")
            if pd.isna(row.get('Anterior chamber depth (mm)')):
                reasons.append("缺失 前房深度 (acd)")

            reason_str = "，".join(reasons)
            print(f" 🚫 剔除 -> 患者号: {pid:^8} | 眼别: {eye} | 原因: {reason_str}")

        # 正式从 DataFrame 中剔除这些行，并重置索引
        df = df.dropna(subset=critical_cols).reset_index(drop=True)
        print(f"\n📉 剔除完成，剩余完美有效样本量: {len(df)} 个")
    else:
        print("✅ 所有样本的光学参数均完整，无剔除。")

    # 防御机制：如果剔除完数据空了，直接停止
    if df.empty:
        print("❌ 错误：剔除后没有任何剩余数据参与计算！")
        return df

    # ==========================================
    # 2. 精准单位对齐与计算
    # ==========================================
    # 将眼轴转为米，角膜和前房保持原本的米
    al_m = df['Axial length (mm)'] / 1000.0
    r1_m = df['Cornea curvature (mm)'] / 1000.0
    acd_m = df['Anterior chamber depth (mm)'] / 1000.0

    # 3. 向量化批量计算 RMF (µm/deg)
    # 这里的 cal_rmf_vectorized 函数就是之前为你写好的那个向量化光线追踪函数
    df['RMF_um_per_deg'] = cal_rmf_vectorized(al_m, r1_m, acd_m)

    # 4. 转换角密度
    density_cols = [col for col in df.columns if 'Cone_Density_ROI_' in col]

    for col in density_cols:
        new_col_name = col.replace('Cone_Density', 'Angular_Cone_Density')
        # 公式：线性密度 * (RMF / 1000)^2 = 细胞数/度²
        df[new_col_name] = df[col] * (df['RMF_um_per_deg'] / 1000.0) ** 2

    print(f"\n✅ 转换成功！共生成了 {len(density_cols)} 个 角密度 (cells/deg²) 特征。")
    print(f"💡 计算出的 RMF 范围: {df['RMF_um_per_deg'].min():.2f} ~ {df['RMF_um_per_deg'].max():.2f} µm/deg")
    print("=" * 70)

    return df

# df = pd.read_csv('../orgData/orgData.csv')
# df1 = add_angular_density(df)
# pass
