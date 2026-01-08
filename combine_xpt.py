import pandas as pd
from pathlib import Path

# 每個模組要取哪些欄位
MODULES = {
    "DIQ":["SEQN","DIQ010"]
    ,
    "MCQ": [
        "SEQN","MCQ010","MCQ035","MCQ300A","MCQ300B","MCQ300C",
         "MCQ160c", "MCQ160e", "MCQ160f", "MCQ160n", "MCQ080" 
    ],
    "DEMO": [
        "SEQN","RIDAGEYR","RIAGENDR","RIDRETH1",
        "DMDEDUC2","DMDEDUC3","DMDMARTL","INDFMINC"
    ],
    "BMX": ["SEQN","BMXHT","BMXWT","BMXBMI","BMXWAIST","BMXTRI","BMXSUB"],
    "SMQ": ["SEQN","SMQ020","SMQ040"],
    "SLQ": ["SEQN","SLQ050","SLD012", "SLD010H"],
    "HUQ": ["SEQN","HUQ010","HUQ050"],
    "PAQ": ["SEQN","PAD680","PAQ560", "PAQ665", "PAQ650"],
    "ALQ": ["SEQN","ALQ130"],
    "GLU": ["SEQN","LBXGLU","LBXIN"],
    "TCHOL": ["SEQN","LBXTC"],
    "HDL": ["SEQN","LBDHDD"],
    "TRIGLY": ["SEQN","LBDLDL","LBXTR"],
    "BPX": ["SEQN","BPXSY1","BPXDI1","BPXSY2","BPXDI2","BPXSY3","BPXDI3"],
    "AL_IGE": ["SEQN","LBXIGE","LBXID1","LBXID2","LBXIE1","LBXIE5"],
    "COT": ["SEQN","LBXCOT"],
    "VID": ["SEQN","LBDVIDMS"],
    "PBCD": ["SEQN","LBXBCD","LBXBPB","LBXTHG"],
    "UAS": ["SEQN","URXUAS"],
    "UHG": ["SEQN","URXUHG"],
    "RDQ": ["SEQN","RDQ070","RDQ090","RDQ100"],
    "SMQFAM": ["SEQN","SMD410"],
    "INS": ["SEQN","LBXIN"],
    "GHB": ["SEQN","LBXGH"]
}
# 全部欄位統一轉大寫
MODULES = {mod: [c.upper() for c in cols] for mod, cols in MODULES.items()}

# ----------------------------------------
# 特例 LAB mapping（只做這三個）
# ----------------------------------------
LAB_SPECIAL = {
    "nhanes_19992000": {
        "glucose_file": "LAB10AM.XPT",
        "lipid_file": "LAB13.XPT",
        "blood_file":"LAB06.XPT",
        "LDL_file":"LAB13AM.XPT",
        "HbAlc_file":"LAB10.XPT"
    },
    "nhanes_20012002": {
        "glucose_file": "L10AM_B.XPT",
        "lipid_file": "L13_B.XPT",
        "blood_file":"L06_B.XPT",
        "LDL_file":"L13AM_B.XPT",
        "HbAlc_file":"L10_B.XPT"
    },
    "nhanes_20032004": {
        "glucose_file": "L10AM_C.XPT",
        "lipid_file": "L13_C.XPT",
        "blood_file":"L06BMT_C.XPT",
        "LDL_file":"L13AM_C.XPT",
        "HbAlc_file":"L10_C.XPT"
       
    },


}

# 所有 cycle 資料夾
CYCLES = [
    "nhanes_19992000",
    "nhanes_20012002",
    "nhanes_20032004",
    "nhanes_20052006",
    "nhanes_20072008",
    "nhanes_20092010",
    "nhanes_20112012",
    "nhanes_20132014",
    "nhanes_20152016",
    "nhanes_20172018",
    "nhanes_20172020",
    "nhanes_20212023",
]


def load_xpt(folder, module):
    """從資料夾讀取模組檔案，自動找 MCQ_D / MCQ_E / P_MCQ 等檔名"""
    folder = Path(folder)

    # 嘗試尋找各種可能檔名
    patterns = [
        f"{module}_*.XPT",
        f"{module}.XPT",
        f"P_{module}.XPT",
    ]

    for pattern in patterns:
        files = list(folder.glob(pattern))
        if files:
            df = pd.read_sas(files[0], format="xport")

            # 強制轉成大寫
            df.columns = df.columns.str.upper()

            # MODULES 欄位也會是大寫，因此比對沒問題
            cols = [c for c in MODULES[module] if c in df.columns]
            return df[cols]


    print(f"[警告] {folder} 找不到 {module} 檔案")
    return None

# ----------------------------------------
# 特例 LAB 處理
# ----------------------------------------
def load_special_lab(folder_name):
    if folder_name not in LAB_SPECIAL:
        return None

    folder = Path(folder_name)
    files = LAB_SPECIAL[folder_name]

    dfs = []

    # GLU / INS / LDL / TG
    f1 = folder / files["glucose_file"]
    if f1.exists():
        df1 = pd.read_sas(f1, format="xport")
        df1.columns = df1.columns.str.upper()
        cols = [c for c in ["SEQN", "LBXGLU", "LBXIN"] if c in df1.columns]
        dfs.append(df1[cols])

    # TC / HDL
    f2 = folder / files["lipid_file"]
    if f2.exists():
        df2 = pd.read_sas(f2, format="xport")
        df2.columns = df2.columns.str.upper()
        cols = [c for c in ["SEQN", "LBXTC", "LBDHDD"] if c in df2.columns]
        dfs.append(df2[cols])

    # blood
    f3 = folder / files["blood_file"]
    if f3.exists():
        df3 = pd.read_sas(f3, format="xport")
        df3.columns = df3.columns.str.upper()
        cols = [c for c in ["SEQN", "LBXBPB", "LBXTHG", "LBXBCD", "LBXCOT"] if c in df3.columns]
        dfs.append(df3[cols])
    
    # LDL
    f4 = folder / files["LDL_file"]
    if f4.exists():
        df4 = pd.read_sas(f4, format="xport")
        df4.columns = df4.columns.str.upper()
        cols = [c for c in ["SEQN", "LBDLDL", "LBXTR"] if c in df4.columns]
        dfs.append(df4[cols])
    
    # HbAlc
    f5 = folder / files["HbAlc_file"]
    if f5.exists():
        df5 = pd.read_sas(f5, format="xport")
        df5.columns = df5.columns.str.upper()
        cols = [c for c in ["SEQN", "LBXGH"] if c in df5.columns]
        dfs.append(df5[cols])
    
    # 合併
    if not dfs:
        return None

    lab = dfs[0]
    for d in dfs[1:]:
        lab = lab.merge(d, on="SEQN", how="left")

    return lab


# 安全 merge：避免欄位重複 (_x, _y)
def safe_merge(merged, df):
    """只合併 merged 中不存在的欄位，避免覆蓋，也避免 _x/_y"""
    # 找出 df 中 merged 尚未擁有的欄位（除了 SEQN）
    new_cols = [c for c in df.columns if c != "SEQN" and c not in merged.columns]

    # 如果沒有需要新增的欄位，直接跳過
    if not new_cols:
        print("→ 所有欄位已存在，跳過合併")
        return merged

    print(f"→ 合併新欄位: {new_cols}")

    # 保留 SEQN + 新欄位
    df_to_merge = df[["SEQN"] + new_cols]

    # 做安全 merge
    return merged.merge(df_to_merge, on="SEQN", how="left")



# ----------------------------------------
# Cycle 更新邏輯
# ----------------------------------------
def update_cycle(folder_name):
    folder = Path(folder_name)

    # 指定舊 CSV 名稱
    cycle_id = folder_name.replace("nhanes_", "")
    expected_csv = folder / f"nhanes_merged_data_{cycle_id}.csv"

    # ---------------------------------------------------------
    # ① 如果有舊 CSV → 用舊 CSV 當 base
    # ---------------------------------------------------------
    if expected_csv.exists():
        print(f"\n=== 更新 {folder_name}，使用舊檔：{expected_csv.name} ===")
        merged = pd.read_csv(expected_csv)

    # ---------------------------------------------------------
    # ② 如果沒有舊 CSV → 從零開始建立 merged，先讀 DEMO（有 SEQN）
    # ---------------------------------------------------------
    else:
        print(f"\n=== {folder_name} 沒有舊 CSV，自動建立新的 merged ===")

        demo = load_xpt(folder, "DEMO")
        if demo is None:
            print(f"[錯誤] {folder_name} 找不到 DEMO，無法建立 merged")
            return

        # 只留下 SEQN，不保留 DEMO 的其他欄位
        merged = demo[["SEQN"]].copy()
        print(f"→ 使用 DEMO 建立 baseline（僅 SEQN，共 {len(merged)} 筆）")


    # 先處理一般模組
    # 一般模組（不含 LAB 四個）
    for module in MODULES:
        if module in ["GLU", "TCHOL", "HDL", "TRIGLY"]:
            continue

        df = load_xpt(folder, module)
        if df is not None:
            merged = safe_merge(merged, df)

    # LAB 特例（三個 cycle）
    lab_df = load_special_lab(folder_name)
    if lab_df is not None:
        print("→ 特例 LAB 合併")
        merged = safe_merge(merged, lab_df)

    # LAB 一般年份
    else:
        for mod in ["GLU", "TCHOL", "HDL", "TRIGLY"]:
            df = load_xpt(folder, mod)
            if df is not None:
                merged = safe_merge(merged, df)

    out_file = folder / f"{folder.name}_updated.csv"
    merged.to_csv(out_file, index=False)
    print(f"✔ 已輸出：{out_file}")

    # ----------------------------------------
    # 缺失值統計
    # ----------------------------------------
    missing_count = merged.isnull().sum()
    missing_pct = (missing_count / len(merged)) * 100

    missing_table = pd.DataFrame({
        "MissingCount": missing_count,
        "MissingPercent": missing_pct
    }).sort_values(by="MissingPercent", ascending=False)

    # 儲存缺失值表格
    missing_file = folder / f"{folder.name}_missing_report.csv"
    missing_table.to_csv(missing_file)
    print(f"✔ 缺失值統計已輸出：{missing_file}")


# ----------------------------------------
# 主程式
# ----------------------------------------
for c in CYCLES:
    if Path(c).exists():
        update_cycle(c)


