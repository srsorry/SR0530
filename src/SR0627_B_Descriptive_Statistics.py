#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
SR0627_B：受试者/眼基线特征描述统计表
================================================================================
"""

import os
import sys
import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, 'genData', 'CleanDataRoi_lenient', 'data1.csv')
REPORT_DIR = os.path.join(BASE_DIR, 'report')
OUT_DIR = os.path.join(BASE_DIR, 'genData', 'sum')

os.makedirs(REPORT_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

DATE_PREFIX = 'SR0627'
SEQ = 'B'
FUNC_NAME = 'Descriptive_Statistics'
REPORT_PATH = os.path.join(REPORT_DIR, f'{DATE_PREFIX}_{SEQ}_{FUNC_NAME}_Report.md')
CSV_PATH = os.path.join(OUT_DIR, f'{DATE_PREFIX}_{SEQ}_{FUNC_NAME}.csv')


def main():
    df = pd.read_csv(DATA_FILE)

    n_eyes = len(df)
    n_subjects = df['Subject_ID'].nunique()

    # Gender: 1 = male, 0 = female (来自 DataRead.py 的编码)
    n_male = (df['Gender'] == 1).sum()
    n_female = (df['Gender'] == 0).sum()
    male_pct = n_male / n_eyes * 100
    female_pct = n_female / n_eyes * 100

    def mean_sd_str(x):
        return f"{x.mean():.2f} ± {x.std(ddof=1):.2f}"

    rows = [
        ('Eyes(n)', str(n_eyes)),
        ('Subjects(n)', str(n_subjects)),
        ('Age(y）', mean_sd_str(df['Age'])),
        ('Gender(male/female)', f"{n_male} ({male_pct:.1f}%) / {n_female} ({female_pct:.1f}%)"),
        ('Axial length(mm)', mean_sd_str(df['Axial length (mm)'])),
        ('Corneal curvature(mm)', mean_sd_str(df['Corneal curvature (mm)'])),
        ('Anterior chamber depth(mm)', mean_sd_str(df['Anterior chamber depth (mm)'])),
        ('Spherical equivalent refraction(D)', mean_sd_str(df['Spherical equivalent refraction (D)'])),
        ('Retinal magnification factor(microns/deg)', mean_sd_str(df['Retinal magnification factor'])),
    ]

    res_df = pd.DataFrame(rows, columns=['Characteristic', 'Value'])
    res_df.to_csv(CSV_PATH, index=False, encoding='utf-8-sig')

    md = []
    md.append(f'# {DATE_PREFIX}_{SEQ}_{FUNC_NAME} 报告\n')
    md.append('> **数据来源**：`genData/CleanDataRoi_lenient/data1.csv`（lenient 数据集，71 眼 / 46 subjects）\n')
    md.append('---\n')
    md.append('## 受试者/眼基线特征\n')
    md.append('| Characteristic | Value |')
    md.append('|----------------|-------|')
    for _, row in res_df.iterrows():
        md.append(f"| {row['Characteristic']} | {row['Value']} |")
    md.append('')
    md.append('---\n')
    md.append('*Report generated automatically by SR0627_B_Descriptive_Statistics.py*\n')

    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))

    print(f'[OK] CSV 已保存: {CSV_PATH}')
    print(f'[OK] 报告已保存: {REPORT_PATH}')
    print('\n结果预览：')
    print(res_df.to_markdown(index=False))


if __name__ == '__main__':
    main()
