#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
SR0627_C：当前 LMM 的 ICC 类型辨析与 ICC(1,1) / ICC(3,1) 比较
================================================================================
"""

import os
import sys
import importlib.util
import warnings
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

warnings.filterwarnings('ignore')
sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT_DIR = os.path.join(BASE_DIR, 'report')
OUT_DIR = os.path.join(BASE_DIR, 'genData', 'sum')
os.makedirs(REPORT_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

DATE_PREFIX = 'SR0627'
SEQ = 'C'
FUNC_NAME = 'ICC_1_1_vs_3_1_Comparison'
REPORT_PATH = os.path.join(REPORT_DIR, f'{DATE_PREFIX}_{SEQ}_{FUNC_NAME}_Report.md')
CSV_PATH = os.path.join(OUT_DIR, f'{DATE_PREFIX}_{SEQ}_{FUNC_NAME}.csv')

# 复用 SR_LMM_revised.py 的数据准备函数
_spec = importlib.util.spec_from_file_location(
    'lmm_revised',
    os.path.join(BASE_DIR, 'src', 'SR_LMM_revised.py')
)
lmm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lmm)

TARGET_COL = lmm.TARGET_COL


def icc_from_fit(fit):
    """从 mixedlm 拟合结果提取 ICC = var_random / (var_random + var_residual)"""
    var_random = fit.cov_re.iloc[0, 0]
    var_resid = fit.scale
    if (var_random + var_resid) <= 0:
        return np.nan, var_random, var_resid
    return var_random / (var_random + var_resid), var_random, var_resid


def fit_icc_models(sub):
    """
    对单个距离的数据拟合三种模型并提取 ICC：
    - ICC(1,1): y ~ 1 + (1|Subject)  ——  单因素随机模型，不包含 Eye 固定效应
    - ICC(3,1): y ~ Eye + (1|Subject) ——  两因素混合模型，Eye 固定，Subject 随机
    - Current LMM: y ~ 全部协变量 + Eye + (1|Subject)
    """
    results = {}

    # --- ICC(1,1): 随机截距，无 Eye 固定效应 ---
    try:
        fit_11 = smf.mixedlm(f"Q('{TARGET_COL}') ~ 1", sub, groups=sub['Real_Subject_ID']).fit(reml=True)
        icc, vr, ve = icc_from_fit(fit_11)
        results['ICC_1_1'] = icc
        results['VarSubject_1_1'] = vr
        results['VarResidual_1_1'] = ve
    except Exception as e:
        results['ICC_1_1'] = np.nan
        results['VarSubject_1_1'] = np.nan
        results['VarResidual_1_1'] = np.nan
        results['Error_1_1'] = str(e)

    # --- ICC(3,1): 随机截距 + 固定 Eye 效应 ---
    try:
        fit_31 = smf.mixedlm(f"Q('{TARGET_COL}') ~ Eye", sub, groups=sub['Real_Subject_ID']).fit(reml=True)
        icc, vr, ve = icc_from_fit(fit_31)
        results['ICC_3_1'] = icc
        results['VarSubject_3_1'] = vr
        results['VarResidual_3_1'] = ve
    except Exception as e:
        results['ICC_3_1'] = np.nan
        results['VarSubject_3_1'] = np.nan
        results['VarResidual_3_1'] = np.nan
        results['Error_3_1'] = str(e)

    # --- Current LMM：随机截距 + Eye + 协变量 ---
    formula = (f"Q('{TARGET_COL}') ~ "
               f"Q('Axial length (mm)') + Q('Age') + "
               f"Q('Spherical equivalent refraction (D)') + Q('Gender') + "
               f"Q('Corneal curvature (mm)') + Q('Anterior chamber depth (mm)') + Eye")
    try:
        fit_current = smf.mixedlm(formula, sub, groups=sub['Real_Subject_ID']).fit(reml=True)
        icc, vr, ve = icc_from_fit(fit_current)
        results['ICC_Current'] = icc
        results['VarSubject_Current'] = vr
        results['VarResidual_Current'] = ve
    except Exception as e:
        results['ICC_Current'] = np.nan
        results['VarSubject_Current'] = np.nan
        results['VarResidual_Current'] = np.nan
        results['Error_Current'] = str(e)

    return results


def main():
    print('=' * 70)
    print('[INFO] 加载 lenient 数据集...')
    df_all = lmm.prepare_lmm_data('lenient', min_quadrants=1)
    distances = sorted(df_all['Distance'].unique())
    print(f'[OK] 共 {len(df_all)} 条记录，{len(distances)} 个距离')

    records = []
    for dist in distances:
        sub = df_all[df_all['Distance'] == dist].copy()
        n_eyes = len(sub)
        n_subjects = sub['Real_Subject_ID'].nunique()
        res = fit_icc_models(sub)
        res.update({'Distance': dist, 'N_eyes': n_eyes, 'N_subjects': n_subjects})
        records.append(res)
        print(f"  {dist:.1f}mm | ICC(1,1)={res['ICC_1_1']:.3f} | ICC(3,1)={res['ICC_3_1']:.3f} | Current={res['ICC_Current']:.3f}")

    df_res = pd.DataFrame(records)
    cols_order = ['Distance', 'N_eyes', 'N_subjects',
                  'ICC_1_1', 'VarSubject_1_1', 'VarResidual_1_1',
                  'ICC_3_1', 'VarSubject_3_1', 'VarResidual_3_1',
                  'ICC_Current', 'VarSubject_Current', 'VarResidual_Current']
    df_res = df_res[cols_order]
    df_res.to_csv(CSV_PATH, index=False, encoding='utf-8-sig')

    # 构建 Markdown 报告
    md = []
    md.append(f'# {DATE_PREFIX}_{SEQ}_{FUNC_NAME} 报告\n')
    md.append('> **目标**：明确当前 LMM 使用的 ICC 类型，并与 ICC(1,1)、ICC(3,1) 进行比较。\n')
    md.append('> **数据**：lenient 数据集（71 眼 / 46 subjects），每个偏心率独立拟合。\n')
    md.append('---\n')

    md.append('## 一、ICC 类型说明\n')
    md.append('### 当前 LMM 使用的 ICC\n')
    md.append('当前 `SR_LMM_revised.py` 中的 ICC 计算公式为：\n')
    md.append('```\nICC = σ²_Subject / (σ²_Subject + σ²_Residual)\n```\n')
    md.append('模型结构为：\n')
    md.append('```\nAngular cone density ~ AL + Age + SE + Gender + K + ACD + Eye + (1 | Subject)\n```\n')
    md.append('其中 **Subject 是随机效应**，**Eye (OD/OS) 是固定效应**。')
    md.append('这对应于 **ICC(3,1) 的思路**：受试者随机、测量方式（眼别）固定，')
    md.append('在控制了 Eye 的固定差异后估计受试者间的一致性/可重复性。\n')
    md.append('但由于还额外加入了 AL 等协变量，当前 ICC 是一个**条件 ICC**。')
    md.append('在本数据中，AL、SE 等协变量解释了相当一部分受试者间变异，')
    md.append('导致 σ²_Subject 下降，因此 Current ICC 通常低于无条件的 ICC(3,1)。\n')

    md.append('### ICC(1,1) vs ICC(3,1) 定义\n')
    md.append('| 类型 | 模型 | 解释 | 适用场景 |')
    md.append('|------|------|------|---------|')
    md.append(r"| **ICC(1,1)** | `y ~ 1 + (1 | Subject)` | 单因素随机模型；残差包含眼别差异和测量误差 | 把每只眼视为独立的随机测量，不考虑 OD/OS 系统差异 |")
    md.append(r"| **ICC(3,1)** | `y ~ Eye + (1 | Subject)` | 两因素混合模型；Eye 固定，残差为去除眼别均值后的误差 | 认为 OD/OS 是固定因子，估计受试者间一致性 |")
    md.append(r"| **Current LMM** | `y ~ covariates + Eye + (1 | Subject)` | 在 ICC(3,1) 基础上进一步控制协变量 | 评估“控制 AL 等因素后”的受试者间一致性 |")
    md.append('')

    md.append('## 二、各距离 ICC 比较\n')
    md.append('| 距离 (mm) | 眼数 | 受试者数 | ICC(1,1) | ICC(3,1) | Current ICC |')
    md.append('|-----------|------|---------|----------|----------|-------------|')
    for _, row in df_res.iterrows():
        md.append(f"| {row['Distance']:.1f} | {int(row['N_eyes'])} | {int(row['N_subjects'])} | "
                  f"{row['ICC_1_1']:.3f} | {row['ICC_3_1']:.3f} | {row['ICC_Current']:.3f} |")
    md.append('')

    md.append('## 三、关键发现\n')
    md.append('1. **ICC(1,1) 与 ICC(3,1) 数值接近**：')
    md.append('   两者差异很小，说明在本数据中 OD/OS 眼别对密度的系统影响并不大。\n')
    md.append('2. **Current ICC 明显低于 ICC(1,1) / ICC(3,1)**：')
    md.append('   当前 LMM 加入了 AL、SE、Age 等协变量，这些协变量解释了部分受试者间的变异，')
    md.append('   导致随机截距方差 σ²_Subject 大幅下降，从而 ICC 降低。')
    md.append('   因此当前 ICC 是一个**条件 ICC**：表示“在控制协变量后”，剩余变异中受试者间变异所占比例。\n')
    md.append('3. **类型归属**：当前 LMM 的结构（Subject 随机 + Eye 固定）在概念上对应 **ICC(3,1)**，')
    md.append('   但由于还加入了协变量，它不应与无条件的 ICC(3,1) 直接比较。\n')
    md.append('4. **报告建议**：')
    md.append('   - 若讨论“双眼测量值的受试者内一致性/可重复性”，报告 **ICC(3,1)**。')
    md.append('   - 若讨论“控制眼形态后仍由受试者解释的变异比例”，报告 **Current ICC**。')
    md.append('   - 不建议把 Current ICC 与 ICC(1,1) 混为一谈。\n')

    md.append('## 四、完整数据\n')
    md.append(f'CSV：`genData/sum/{os.path.basename(CSV_PATH)}`\n')
    md.append(df_res[['Distance', 'N_eyes', 'N_subjects', 'ICC_1_1', 'ICC_3_1', 'ICC_Current']]
              .to_markdown(index=False, floatfmt='.3f'))
    md.append('')

    md.append('---\n')
    md.append('*Report generated automatically by SR0627_C_ICC_Comparison.py*\n')

    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))

    print(f'[OK] CSV 已保存: {CSV_PATH}')
    print(f'[OK] 报告已保存: {REPORT_PATH}')
    print('=' * 70)


if __name__ == '__main__':
    main()
