"""
从已保存的 1.0 mm 结果重新生成汇总图与报告（不重新训练）。
"""
import os
import sys
import runpy

# 确保项目路径在 sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

# 加载模块以获取配置和函数
spec = runpy.run_path(os.path.join(BASE_DIR, 'src', 'SR_ML_1mm_final_tuning.py'),
                      init_globals={'__name__': '__regen__'})

import pandas as pd

OUT_DIR = spec['OUT_DIR']
REPORT_DIR = spec['REPORT_DIR']
FIG_DIR = spec['FIG_DIR']
plot_summary = spec['plot_summary']
generate_report = spec['generate_report']

# 读取已保存的结果
df_results = pd.read_csv(os.path.join(OUT_DIR, 'SR0530_1mm_Fine_Tuning_Results.csv'), encoding='utf-8-sig')
df_importance = pd.read_csv(os.path.join(OUT_DIR, 'SR0530_1mm_Feature_Importance.csv'), encoding='utf-8-sig')

print("Regenerating summary plots and report from saved results...")
plot_summary(df_results, df_importance)
generate_report(df_results, df_importance)
print("Done.")
