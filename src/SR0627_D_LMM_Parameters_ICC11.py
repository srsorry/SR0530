#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
SR0627_D：LMM 参数 P 值 / 绝对系数 / 相对系数 + R²(marginal/conditional) + ICC(1,1) 方差分量
================================================================================
对每个距离拟合当前 LMM：
  Angular cone density_z ~ AL_z + Age_z + SE_z + Gender + CC_z + ACD_z + Eye + (1|Subject)
输出：
  - 每个固定效应参数的 P 值、标准化回归系数（Beta）、绝对系数（AbsBeta）、
    相对系数（RelBeta = |Beta| / Σ|Beta|）
  - R²_marginal 与 R²_conditional
  - ICC(1,1) 及其 σ²_random、σ²_residual
整理为 CSV（每个距离一行）。
"""

import os
import sys
import importlib.util
import warnings
import re
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
SEQ = 'D'
FUNC_NAME = 'LMM_Parameters_ICC11'
CSV_PATH = os.path.join(OUT_DIR, f'{DATE_PREFIX}_{SEQ}_{FUNC_NAME}.csv')
MD_PATH = os.path.join(REPORT_DIR, f'{DATE_PREFIX}_{SEQ}_{FUNC_NAME}_Report.md')

# 复用 SR_LMM_revised.py 的数据准备函数
_spec = importlib.util.spec_from_file_location(
    'lmm_revised',
    os.path.join(BASE_DIR, 'src', 'SR_LMM_revised.py')
)
lmm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lmm)

TARGET_COL = lmm.TARGET_COL
FEATURE_ALL = lmm.FEATURE_ALL

# 固定效应参数顺序与显示名
PREDICTOR_META = [
    ('AL',      "Axial length (mm)"),
    ('Age',     "Age"),
    ('SE',      "Spherical equivalent refraction (D)"),
    ('Gender',  "Gender"),
    ('CC',      "Corneal curvature (mm)"),
    ('ACD',     "Anterior chamber depth (mm)"),
    ('Eye_OS',  "Eye"),
]


def param_to_label(pname):
    """将 statsmodels 参数名映射为简写标签"""
    if 'Intercept' in pname or 'Group Var' in pname:
        return None
    if 'Axial length' in pname:
        return 'AL'
    if 'Age' in pname and 'Axial' not in pname and 'Anterior' not in pname:
        return 'Age'
    if 'Spherical equivalent' in pname:
        return 'SE'
    if 'Gender' in pname:
        return 'Gender'
    if 'Corneal curvature' in pname:
        return 'CC'
    if 'Anterior chamber' in pname:
        return 'ACD'
    if 'Eye' in pname:
        return 'Eye_OS'
    return None


def calc_r2_marginal_conditional(fit):
    """从 lmm.fit 结果计算边际 R2 和条件 R2"""
    try:
        exog = fit.model.exog
        fixed_params = fit.params[fit.model.exog_names]
        fixed_pred = exog @ fixed_params
        var_fixed = np.var(fixed_pred, ddof=0)
        var_random = fit.cov_re.iloc[0, 0] if hasattr(fit, 'cov_re') else 0.0
        var_resid = fit.scale
        total = var_fixed + var_random + var_resid
        if total <= 0 or var_resid < 0 or var_fixed < 0 or var_random < 0:
            return np.nan, np.nan
        return var_fixed / total, (var_fixed + var_random) / total
    except Exception:
        return np.nan, np.nan


def extract_current_lmm_params(sub):
    """
    拟合当前 LMM，提取各参数 beta/p/abs/rel、R2_marginal、R2_conditional。
    返回 dict，键形如 AL_Beta, AL_P, AL_AbsBeta, AL_RelBeta, ...
    """
    feature_cols = list(FEATURE_ALL.values())
    zscore_cols = [TARGET_COL] + [FEATURE_ALL[c] for c in ['AL', 'Age', 'SE', 'CC', 'ACD']]

    sub = sub.copy()
    sub = lmm.fill_na(sub, feature_cols)

    # 标准化连续变量
    scalers = {}
    for col in zscore_cols:
        mu, sd = sub[col].mean(), sub[col].std()
        scalers[col] = (mu, sd)
        sub[f'{col}_z'] = (sub[col] - mu) / sd if sd > 0 else 0

    formula = ("Q('Angular cone density (cones/ deg2)_z') ~ "
               "Q('Axial length (mm)_z') + Q('Age_z') + "
               "Q('Spherical equivalent refraction (D)_z') + "
               "Q('Gender') + Q('Corneal curvature (mm)_z') + "
               "Q('Anterior chamber depth (mm)_z') + Eye")

    model = smf.mixedlm(formula, sub, groups=sub['Real_Subject_ID'])
    fit = model.fit(reml=True)

    # 提取所有非截距固定效应
    params = fit.params
    pvalues = fit.pvalues

    beta_map = {}
    p_map = {}
    abs_map = {}
    for pname in params.index:
        label = param_to_label(pname)
        if label is None:
            continue
        beta = params[pname]
        p = pvalues.get(pname, np.nan)
        beta_map[label] = beta
        p_map[label] = p
        abs_map[label] = abs(beta)

    # 相对系数：|Beta| / Σ|Beta|
    total_abs = sum(abs_map.values())
    rel_map = {k: (v / total_abs if total_abs > 0 else np.nan) for k, v in abs_map.items()}

    r2m, r2c = calc_r2_marginal_conditional(fit)

    out = {
        'R2_Marginal': r2m,
        'R2_Conditional': r2c,
    }
    for label, display in PREDICTOR_META:
        beta = beta_map.get(label, np.nan)
        p = p_map.get(label, np.nan)
        ab = abs_map.get(label, np.nan)
        rel = rel_map.get(label, np.nan)
        out[f'{label}_Beta'] = beta
        out[f'{label}_P'] = p
        out[f'{label}_AbsBeta'] = ab
        out[f'{label}_RelBeta'] = rel

    return out


def extract_icc_11(sub):
    """拟合 ICC(1,1): y ~ 1 + (1|Subject)，返回 ICC 与 σ²_random、σ²_residual"""
    try:
        fit = smf.mixedlm(f"Q('{TARGET_COL}') ~ 1", sub, groups=sub['Real_Subject_ID']).fit(reml=True)
        var_random = fit.cov_re.iloc[0, 0]
        var_resid = fit.scale
        icc = var_random / (var_random + var_resid) if (var_random + var_resid) > 0 else np.nan
        return {
            'ICC_1_1': icc,
            'VarRandom_1_1': var_random,
            'VarResidual_1_1': var_resid,
        }
    except Exception as e:
        return {
            'ICC_1_1': np.nan,
            'VarRandom_1_1': np.nan,
            'VarResidual_1_1': np.nan,
            'ICC_1_1_Error': str(e),
        }


def main():
    print('=' * 80)
    print('[INFO] 加载 lenient 数据集...')
    df_all = lmm.prepare_lmm_data('lenient', min_quadrants=1)
    distances = sorted(df_all['Distance'].unique())
    print(f'[OK] 共 {len(df_all)} 条记录，{len(distances)} 个距离')

    records = []
    for dist in distances:
        sub = df_all[df_all['Distance'] == dist].copy()
        n_eyes = len(sub)
        n_subjects = sub['Real_Subject_ID'].nunique()

        rec = {
            'Distance': dist,
            'N_eyes': n_eyes,
            'N_subjects': n_subjects,
        }

        try:
            rec.update(extract_current_lmm_params(sub))
        except Exception as e:
            print(f'  [WARN] {dist:.1f}mm current LMM failed: {e}')
            for label, _ in PREDICTOR_META:
                rec[f'{label}_Beta'] = np.nan
                rec[f'{label}_P'] = np.nan
                rec[f'{label}_AbsBeta'] = np.nan
                rec[f'{label}_RelBeta'] = np.nan
            rec['R2_Marginal'] = np.nan
            rec['R2_Conditional'] = np.nan

        rec.update(extract_icc_11(sub))
        records.append(rec)

        sig_list = []
        for label, _ in PREDICTOR_META:
            p = rec.get(f'{label}_P', np.nan)
            if pd.notna(p) and p < 0.05:
                sig_list.append(label)
        sig_str = ','.join(sig_list) if sig_list else '-'
        print(f"  {dist:.1f}mm | N={n_eyes:3d}/{n_subjects:3d} | "
              f"R2m={rec.get('R2_Marginal', np.nan):.3f} R2c={rec.get('R2_Conditional', np.nan):.3f} | "
              f"ICC(1,1)={rec.get('ICC_1_1', np.nan):.3f} | 显著: {sig_str}")

    df = pd.DataFrame(records)

    # 列顺序
    col_order = ['Distance', 'N_eyes', 'N_subjects']
    for label, _ in PREDICTOR_META:
        col_order += [f'{label}_Beta', f'{label}_P', f'{label}_AbsBeta', f'{label}_RelBeta']
    col_order += ['R2_Marginal', 'R2_Conditional',
                  'ICC_1_1', 'VarRandom_1_1', 'VarResidual_1_1']

    # 仅保留存在的列
    col_order = [c for c in col_order if c in df.columns]
    df = df[col_order]
    df.to_csv(CSV_PATH, index=False, encoding='utf-8-sig')

    # 同时生成 Markdown 便于阅读
    md = []
    md.append(f'# {DATE_PREFIX}_{SEQ}_{FUNC_NAME} 报告\n')
    md.append('> **目标**：整理当前 LMM 各参数的 P 值、绝对系数、相对系数，以及 R² 和 ICC(1,1) 方差分量。\n')
    md.append('> **数据**：lenient 数据集（71 眼 / 46 subjects），每个偏心率独立拟合。\n')
    md.append('> **模型**：`Angular cone density_z ~ AL_z + Age_z + SE_z + Gender + CC_z + ACD_z + Eye + (1|Subject)`\n')
    md.append('> **相对系数**：`|Beta| / Σ|Beta|`，反映该参数在固定效应中的相对重要性。\n')
    md.append('---\n')

    md.append('## 一、各距离完整参数表\n')
    md.append(df.to_markdown(index=False, floatfmt='.4f'))
    md.append('\n')

    md.append('## 二、列名说明\n')
    md.append('| 后缀 | 含义 |')
    md.append('|------|------|')
    md.append('| `_Beta` | 标准化回归系数（带符号） |')
    md.append('| `_P` | 对应参数的 P 值 |')
    md.append('| `_AbsBeta` | 标准化回归系数的绝对值 |')
    md.append('| `_RelBeta` | 相对系数 = |Beta| / Σ|Beta| |')
    md.append('| `R2_Marginal` | 固定效应解释的变异比例 |')
    md.append('| `R2_Conditional` | 固定效应 + 随机效应解释的变异比例 |')
    md.append('| `ICC_1_1` | 按 ICC(1,1) 计算的受试者间一致性 |')
    md.append('| `VarRandom_1_1` | ICC(1,1) 模型的受试者随机截距方差 σ²_random |')
    md.append('| `VarResidual_1_1` | ICC(1,1) 模型的残差方差 σ²_residual |')
    md.append('\n> 注：VarRandom_1_1 与 VarResidual_1_1 单位为原始 Angular cone density (cones/deg²) 的平方。\n')

    md.append('## 三、CSV 文件\n')
    md.append(f'`{CSV_PATH}`\n')

    md.append('---\n')
    md.append('*Report generated automatically by SR0627_D_LMM_Parameters_ICC11.py*\n')

    with open(MD_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))

    print(f'[OK] CSV 已保存: {CSV_PATH}')
    print(f'[OK] Markdown 已保存: {MD_PATH}')
    print('=' * 80)


if __name__ == '__main__':
    main()
