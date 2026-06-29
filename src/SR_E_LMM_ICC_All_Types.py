#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
SR0611_E：LMM 参数 + R² + ICC(1,1)/(2,1)/(3,1)/Current 方差分量 CSV 汇总
================================================================================
对每个偏心率（1.0–6.0 mm）输出：
  - 当前 LMM 所有固定效应参数的标准化系数、P 值、绝对系数、相对系数
  - R²_marginal、R²_conditional
  - ICC(1,1)、ICC(2,1)、ICC(3,1) 及当前 LMM ICC，并分别输出 σ²_random 与 σ²_residual
生成多个 CSV 文件，日期前缀使用当天日期。
"""

import os
import sys
import importlib.util
import warnings
import datetime
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.stats.anova import anova_lm

warnings.filterwarnings('ignore')
sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT_DIR = os.path.join(BASE_DIR, 'report')
OUT_DIR = os.path.join(BASE_DIR, 'genData', 'sum')
os.makedirs(REPORT_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

# 日期前缀使用当天日期（MMDD）
DATE_PREFIX = f"SR{datetime.datetime.now().strftime('%m%d')}"
SEQ = 'A'
FUNC_NAME = 'LMM_ICC_All_Types'

# 复用 SR_LMM_revised.py 的数据准备函数
_spec = importlib.util.spec_from_file_location(
    'lmm_revised',
    os.path.join(BASE_DIR, 'src', 'SR_LMM_revised.py')
)
lmm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lmm)

TARGET_COL = lmm.TARGET_COL
FEATURE_ALL = lmm.FEATURE_ALL

PREDICTOR_META = [
    ('AL', 'Axial length (mm)'),
    ('Age', 'Age'),
    ('SE', 'Spherical equivalent refraction (D)'),
    ('Gender', 'Gender'),
    ('CC', 'Corneal curvature (mm)'),
    ('ACD', 'Anterior chamber depth (mm)'),
    ('Eye_OS', 'Eye'),
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
    """计算 LMM 的边际 R2 和条件 R2"""
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


def fit_current_lmm(sub):
    """拟合当前 LMM，返回参数字典、fit 对象、目标变量标准差"""
    feature_cols = list(FEATURE_ALL.values())
    zscore_cols = [TARGET_COL] + [FEATURE_ALL[c] for c in ['AL', 'Age', 'SE', 'CC', 'ACD']]

    sub = sub.copy()
    sub = lmm.fill_na(sub, feature_cols)

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

    total_abs = sum(abs_map.values())
    rel_map = {k: (v / total_abs if total_abs > 0 else np.nan) for k, v in abs_map.items()}

    r2m, r2c = calc_r2_marginal_conditional(fit)

    out = {'R2_Marginal': r2m, 'R2_Conditional': r2c}
    for label, _ in PREDICTOR_META:
        out[f'{label}_Beta'] = beta_map.get(label, np.nan)
        out[f'{label}_P'] = p_map.get(label, np.nan)
        out[f'{label}_AbsBeta'] = abs_map.get(label, np.nan)
        out[f'{label}_RelBeta'] = rel_map.get(label, np.nan)

    sd_target = scalers[TARGET_COL][1]
    return out, fit, sd_target


def fit_icc_11(sub):
    """ICC(1,1): y ~ 1 + (1|Subject)"""
    try:
        fit = smf.mixedlm(f"Q('{TARGET_COL}') ~ 1", sub, groups=sub['Real_Subject_ID']).fit(reml=True)
        vr = fit.cov_re.iloc[0, 0]
        ve = fit.scale
        icc = vr / (vr + ve) if (vr + ve) > 0 else np.nan
        return {'ICC_1_1': icc, 'VarRandom_1_1': vr, 'VarResidual_1_1': ve}
    except Exception as e:
        return {'ICC_1_1': np.nan, 'VarRandom_1_1': np.nan, 'VarResidual_1_1': np.nan,
                'Error_1_1': str(e)}


def fit_icc_21(sub):
    """
    ICC(2,1): 两因素随机模型（Subject、Eye 均为随机效应）。
    使用 two-way ANOVA 方法 of moments 估计方差分量：
      σ²_s = (MS_Subject - MS_Error) / k_bar
      σ²_e = max((MS_Eye    - MS_Error) / n, 0)
      σ²_error = MS_Error
    其中 k_bar = 平均每只眼的重复次数（n_obs / n_subjects），n = 受试者数。
    σ²_random = σ²_s，σ²_residual = σ²_e + σ²_error。
    """
    try:
        sub = sub.copy()
        sub['Subject_cat'] = sub['Real_Subject_ID'].astype('category')
        sub['Eye_cat'] = sub['Eye'].astype('category')
        model = smf.ols(f"Q('{TARGET_COL}') ~ C(Subject_cat) + C(Eye_cat)", data=sub).fit()
        anova = anova_lm(model, typ=3)

        ms_s = anova.loc['C(Subject_cat)', 'sum_sq'] / anova.loc['C(Subject_cat)', 'df']
        ms_e = anova.loc['C(Eye_cat)', 'sum_sq'] / anova.loc['C(Eye_cat)', 'df']
        ms_err = anova.loc['Residual', 'sum_sq'] / anova.loc['Residual', 'df']

        n = sub['Real_Subject_ID'].nunique()
        k_bar = len(sub) / n

        s2_s = max((ms_s - ms_err) / k_bar, 0.0)
        s2_e = max((ms_e - ms_err) / n, 0.0)
        s2_err = ms_err

        denom = s2_s + s2_e + s2_err
        icc = s2_s / denom if denom > 0 else np.nan
        return {
            'ICC_2_1': icc,
            'VarRandom_2_1': s2_s,
            'VarResidual_2_1': s2_e + s2_err,
            'VarEye_2_1': s2_e,
            'VarError_2_1': s2_err,
        }
    except Exception as e:
        return {
            'ICC_2_1': np.nan,
            'VarRandom_2_1': np.nan,
            'VarResidual_2_1': np.nan,
            'VarEye_2_1': np.nan,
            'VarError_2_1': np.nan,
            'Error_2_1': str(e),
        }


def fit_icc_31(sub):
    """ICC(3,1): y ~ Eye + (1|Subject)"""
    try:
        fit = smf.mixedlm(f"Q('{TARGET_COL}') ~ Eye", sub, groups=sub['Real_Subject_ID']).fit(reml=True)
        vr = fit.cov_re.iloc[0, 0]
        ve = fit.scale
        icc = vr / (vr + ve) if (vr + ve) > 0 else np.nan
        return {'ICC_3_1': icc, 'VarRandom_3_1': vr, 'VarResidual_3_1': ve}
    except Exception as e:
        return {'ICC_3_1': np.nan, 'VarRandom_3_1': np.nan, 'VarResidual_3_1': np.nan,
                'Error_3_1': str(e)}


def fit_icc_current(fit, sd_target):
    """从当前 LMM fit 中提取 ICC 方差分量，并转换回原始目标变量单位"""
    try:
        vr_std = fit.cov_re.iloc[0, 0]
        ve_std = fit.scale
        sd2 = sd_target ** 2
        vr = vr_std * sd2
        ve = ve_std * sd2
        icc = vr / (vr + ve) if (vr + ve) > 0 else np.nan
        return {'ICC_Current': icc, 'VarRandom_Current': vr, 'VarResidual_Current': ve}
    except Exception as e:
        return {'ICC_Current': np.nan, 'VarRandom_Current': np.nan, 'VarResidual_Current': np.nan,
                'Error_Current': str(e)}


def build_base_record(dist, sub, lmm_params):
    """构建包含距离、样本量、LMM 参数、R² 的基础记录"""
    rec = {
        'Distance': dist,
        'N_eyes': len(sub),
        'N_subjects': sub['Real_Subject_ID'].nunique(),
    }
    rec.update(lmm_params)
    return rec


def main():
    print('=' * 80)
    print(f'[{DATE_PREFIX}] 加载 lenient 数据集并拟合模型...')
    df_all = lmm.prepare_lmm_data('lenient', min_quadrants=1)
    distances = sorted(df_all['Distance'].unique())
    print(f'[OK] 共 {len(df_all)} 条记录，{len(distances)} 个距离')

    records_params = []
    records_icc = []

    for dist in distances:
        sub = df_all[df_all['Distance'] == dist].copy()
        n_eyes = len(sub)
        n_subjects = sub['Real_Subject_ID'].nunique()

        try:
            lmm_params, fit_current, sd_target = fit_current_lmm(sub)
        except Exception as e:
            print(f'  [WARN] {dist:.1f}mm 当前 LMM 拟合失败: {e}')
            lmm_params = {'R2_Marginal': np.nan, 'R2_Conditional': np.nan}
            for label, _ in PREDICTOR_META:
                lmm_params[f'{label}_Beta'] = np.nan
                lmm_params[f'{label}_P'] = np.nan
                lmm_params[f'{label}_AbsBeta'] = np.nan
                lmm_params[f'{label}_RelBeta'] = np.nan
            fit_current = None
            sd_target = np.nan

        base = build_base_record(dist, sub, lmm_params)
        records_params.append(base.copy())

        icc11 = fit_icc_11(sub)
        icc21 = fit_icc_21(sub)
        icc31 = fit_icc_31(sub)
        icc_cur = fit_icc_current(fit_current, sd_target) if fit_current is not None else {
            'ICC_Current': np.nan, 'VarRandom_Current': np.nan, 'VarResidual_Current': np.nan}

        records_icc.append({
            'Distance': dist,
            'N_eyes': n_eyes,
            'N_subjects': n_subjects,
            'R2_Marginal': base['R2_Marginal'],
            'R2_Conditional': base['R2_Conditional'],
            **icc11,
            **icc21,
            **icc31,
            **icc_cur,
        })

        sig_list = [label for label, _ in PREDICTOR_META
                    if pd.notna(base.get(f'{label}_P')) and base[f'{label}_P'] < 0.05]
        sig_str = ','.join(sig_list) if sig_list else '-'
        print(f"  {dist:.1f}mm | N={n_eyes:3d}/{n_subjects:3d} | "
              f"R2m={base['R2_Marginal']:.3f} R2c={base['R2_Conditional']:.3f} | "
              f"ICC(1,1)={icc11.get('ICC_1_1', np.nan):.3f} "
              f"ICC(2,1)={icc21.get('ICC_2_1', np.nan):.3f} "
              f"ICC(3,1)={icc31.get('ICC_3_1', np.nan):.3f} "
              f"Current={icc_cur.get('ICC_Current', np.nan):.3f} | "
              f"显著: {sig_str}")

    # ---- 生成 DataFrame ----
    df_params = pd.DataFrame(records_params)
    df_icc = pd.DataFrame(records_icc)

    # 列顺序
    param_cols = []
    for label, _ in PREDICTOR_META:
        param_cols += [f'{label}_Beta', f'{label}_P', f'{label}_AbsBeta', f'{label}_RelBeta']

    base_cols = ['Distance', 'N_eyes', 'N_subjects'] + param_cols + ['R2_Marginal', 'R2_Conditional']
    df_params = df_params[[c for c in base_cols if c in df_params.columns]]

    # ---- 保存 CSV ----
    files = {
        f'{DATE_PREFIX}_{SEQ}_LMM_Parameters_and_R2.csv': df_params,
        f'{DATE_PREFIX}_{SEQ}_ICC_1_1.csv': pd.concat([
            df_params,
            df_icc[['ICC_1_1', 'VarRandom_1_1', 'VarResidual_1_1']]
        ], axis=1),
        f'{DATE_PREFIX}_{SEQ}_ICC_2_1.csv': pd.concat([
            df_params,
            df_icc[['ICC_2_1', 'VarRandom_2_1', 'VarResidual_2_1', 'VarEye_2_1', 'VarError_2_1']]
        ], axis=1),
        f'{DATE_PREFIX}_{SEQ}_ICC_3_1.csv': pd.concat([
            df_params,
            df_icc[['ICC_3_1', 'VarRandom_3_1', 'VarResidual_3_1']]
        ], axis=1),
        f'{DATE_PREFIX}_{SEQ}_ICC_Current.csv': pd.concat([
            df_params,
            df_icc[['ICC_Current', 'VarRandom_Current', 'VarResidual_Current']]
        ], axis=1),
        f'{DATE_PREFIX}_{SEQ}_ICC_All_Types_Summary.csv': df_icc[[
            'Distance', 'N_eyes', 'N_subjects',
            'ICC_1_1', 'VarRandom_1_1', 'VarResidual_1_1',
            'ICC_2_1', 'VarRandom_2_1', 'VarResidual_2_1',
            'ICC_3_1', 'VarRandom_3_1', 'VarResidual_3_1',
            'ICC_Current', 'VarRandom_Current', 'VarResidual_Current',
            'R2_Marginal', 'R2_Conditional'
        ]],
    }

    paths = {}
    for fname, df in files.items():
        path = os.path.join(OUT_DIR, fname)
        df.to_csv(path, index=False, encoding='utf-8-sig')
        paths[fname.replace('.csv', '')] = path
        print(f'[OK] CSV: {path}')

    # ---- Markdown 报告 ----
    md = []
    md.append(f'# {DATE_PREFIX}_{SEQ}_{FUNC_NAME} 报告\n')
    md.append('> **目标**：整理当前 LMM 各参数的 P 值、绝对系数、相对系数，R²（边际/条件），')
    md.append('以及 ICC(1,1)、ICC(2,1)、ICC(3,1) 和当前 LMM ICC 的方差分量。\n')
    md.append('> **数据**：lenient 数据集（71 眼 / 46 subjects）。\n')
    md.append('> **当前 LMM**：`Angular cone density_z ~ AL_z + Age_z + SE_z + Gender + CC_z + ACD_z + Eye + (1|Subject)`\n')
    md.append('> **相对系数**：`|Beta| / Σ|Beta|`，反映固定效应内部的相对重要性。\n')
    md.append('---\n')

    md.append('## 一、ICC 模型说明\n')
    md.append('| 类型 | 模型 | σ²_random | σ²_residual | 说明 |')
    md.append('|------|------|-----------|-------------|------|')
    md.append(r'| ICC(1,1) | `y ~ 1 + (1|Subject)` | 受试者随机截距 | 残差 | 单因素随机模型，不考虑 Eye 系统差异 |')
    md.append(r'| ICC(2,1) | Subject、Eye 均为随机 | 受试者方差 | 眼别方差 + 误差 | 两因素随机模型；眼别方差通过 ANOVA 方法 of moments 估计，负值截断为 0 |')
    md.append(r'| ICC(3,1) | `y ~ Eye + (1|Subject)` | 受试者随机截距 | 残差 | 两因素混合模型，Eye 固定 |')
    md.append('| Current | 当前 LMM | 受试者随机截距 | 残差 | 控制 AL 等协变量后的条件 ICC |')
    md.append('\n')

    md.append('## 二、各距离 LMM 参数与 R²\n')
    md.append(df_params.to_markdown(index=False, floatfmt='.4f'))
    md.append('\n')

    md.append('## 三、各距离 ICC 汇总\n')
    md.append(df_icc[[
        'Distance', 'N_eyes', 'N_subjects',
        'ICC_1_1', 'VarRandom_1_1', 'VarResidual_1_1',
        'ICC_2_1', 'VarRandom_2_1', 'VarResidual_2_1',
        'ICC_3_1', 'VarRandom_3_1', 'VarResidual_3_1',
        'ICC_Current', 'VarRandom_Current', 'VarResidual_Current',
        'R2_Marginal', 'R2_Conditional'
    ]].to_markdown(index=False, floatfmt='.4f'))
    md.append('\n')

    md.append('## 四、CSV 文件列表\n')
    for key, path in paths.items():
        md.append(f'- `{path}`\n')

    md.append('\n---\n')
    md.append(f'*Report generated automatically by {os.path.basename(__file__)}*\n')

    md_path = os.path.join(REPORT_DIR, f'{DATE_PREFIX}_{SEQ}_{FUNC_NAME}_Report.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))
    print(f'[OK] Markdown: {md_path}')
    print('=' * 80)


if __name__ == '__main__':
    main()
