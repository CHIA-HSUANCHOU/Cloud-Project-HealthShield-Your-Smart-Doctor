NAN_MAP = {
    # 7, 9, 77, 99, 777, 999, 7777, 9999
    "group_big": ["DIQ010","MCQ160C","MCQ160E","MCQ160F","MCQ160N","MCQ080",
                  "MCQ035","SMQ020","SMQ040","SLQ050","RDQ070","RDQ100","RDQ090",
                  "SMD410","MCQ300A","MCQ300B","MCQ300C","HUQ010"],

    # 7, 9
    "group_7_9": ["DMDEDUC2", "PAQ665", "PAQ650"],

    # 77, 99
    "group_77_99": ["DMDEDUC3","INDFMINC","DMDMARTL","HUQ050", "SLD010H"],

    # 777, 999
    "group_777_999": ["ALQ130","PAQ560"],

    # 7777, 9999
    "group_7777_9999": ["PAD680"],
    "group_7777_9999": ["PAQ560"]

}

NAN_VALUES = {
    "group_big": [7,9,77,99,777,999,7777,9999],
    "group_7_9": [7,9],
    "group_77_99": [77,99],
    "group_777_999": [777,999],
    "group_7777_9999": [7777,9999],
    "group_7777_9999": [77777,99999],
}

import numpy as np

def clean_missing_values(df):
    """依欄位規則將 i don't know / refused 等特殊碼轉成 NaN"""

    for group, columns in NAN_MAP.items():
        nan_vals = NAN_VALUES[group]

        for col in columns:
            col = col.upper()
            if col in df.columns:
                df[col] = df[col].replace(nan_vals, np.nan)

    return df


from pathlib import Path
import pandas as pd

def process_clean_cycle(folder_name):

    folder = Path(folder_name)
    updated_csv = folder / f"{folder.name}_updated.csv"

    if not updated_csv.exists():
        print(f"[跳過] {folder_name} 找不到 {updated_csv.name}")
        return

    print(f"\n=== 清洗 {updated_csv.name} 中的特殊值 ===")

    df = pd.read_csv(updated_csv)

    # 應用 NaN 規則
    df_clean = clean_missing_values(df)

    # 儲存 cleaned CSV
    cleaned_csv = folder / f"{folder.name}_cleaned.csv"
    df_clean.to_csv(cleaned_csv, index=False)
    print(f"✔ 已輸出 cleaned CSV：{cleaned_csv}")

    # 重新計算缺失
    missing_count = df_clean.isnull().sum()
    missing_pct = (missing_count / len(df_clean)) * 100

    missing_table = pd.DataFrame({
        "MissingCount": missing_count,
        "MissingPercent": missing_pct
    }).sort_values(by="MissingPercent", ascending=False)

    # 存檔
    missing_csv = folder / f"{folder.name}_cleaned_missing_report.csv"
    missing_table.to_csv(missing_csv)
    print(f"✔ 已輸出新的 missing report：{missing_csv}")


# 跑你所有年份
CYCLES = [
    "nhanes_19992000","nhanes_20012002","nhanes_20032004","nhanes_20052006",
    "nhanes_20072008","nhanes_20092010","nhanes_20112012","nhanes_20132014",
    "nhanes_20152016","nhanes_20172018","nhanes_20172020","nhanes_20212023"
]

for c in CYCLES:
    if Path(c).exists():
        process_clean_cycle(c)
