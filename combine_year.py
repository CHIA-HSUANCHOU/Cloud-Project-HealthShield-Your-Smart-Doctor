import pandas as pd
from pathlib import Path
import seaborn as sns
import matplotlib.pyplot as plt
"""
TARGET_YEARS = [
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
"""

TARGET_YEARS = [
    "nhanes_20072008",
    "nhanes_20092010",
    "nhanes_20112012",
    "nhanes_20132014",
    "nhanes_20152016",
    "nhanes_20172018",
]

TARGET_COLUMNS = [
    "SEQN", "DIQ010", "RIDAGEYR", "RIAGENDR", "BMXHT", "BMXWT", "BMXBMI", "BMXWAIST", 
    "BPXSY1", "BPXDI1", "BPXSY2", "BPXDI2", "BPXSY3", "BPXDI3", 
    "LBXGLU", "LBXIN", "LBXGH", "LBXTC", "LBDHDD", "LBDLDL", "LBXTR",
    "SMQ020", "MCQ300C", "ALQ130", "PAQ665", "PAQ650", "SLD012", "HUQ010" # 注意：將 SLD010H 和 SLD012 替換為 SLEEP_HOURS
]


# ---- 讀取所有 cleaned.csv、篩選欄位、標準化欄位並計算缺失率 ----
def collect_all_data(root: Path):
    dfs = []
    missing_by_folder = {}  # {folderName: {column: missing%}}

    # 定義要合併的欄位名稱及其目標名稱
    SLEEP_COLS = ["SLD010H", "SLD012"]
    TARGET_SLEEP_NAME = "SLD012"

    for folder_name in TARGET_YEARS:
        folder = root / folder_name
        if not folder.exists():
            print(f"⚠ 找不到資料夾：{folder_name}")
            continue

        cleaned_csv = folder / f"{folder.name}_cleaned.csv"
        if not cleaned_csv.exists():
            print(f"⚠ 找不到 cleaned.csv：{cleaned_csv}")
            continue

        print(f"📥 讀取：{cleaned_csv}")
        df = pd.read_csv(
            cleaned_csv,
            dtype=str,
            # 包含了空字串、空格、Tab、句點和常見的NA表示
            na_values=["", " ", "  ", "\t", ".", "NA", "N/A"], 
            low_memory=False
        )

        # --- 1. 加入資料來源欄位 (先加入，方便後續篩選和追蹤) ----
        df["Source"] = folder_name.replace("nhanes_", "")

        # --- 2. 欄位標準化/合併 (SLD010H, SLD012 -> SLD012) ---
        
        # 找出當前 DF 中存在的睡眠相關欄位
        existing_sleep_cols = [col for col in SLEEP_COLS if col in df.columns]
        
        if existing_sleep_cols:
            # 找到 DF 中存在的睡眠欄位中，與目標名稱不同的那個（即 SLD010H）
            col_to_rename = [col for col in existing_sleep_cols if col != TARGET_SLEEP_NAME]
            
            if col_to_rename:
                # 執行重命名 (例如: 將 SLD010H 重命名為 SLD012)
                df = df.rename(columns={col_to_rename[0]: TARGET_SLEEP_NAME})
                # 為了避免重複欄位，刪除被重命名的原始欄位（如果 SLD010H 也存在於 TARGET_COLUMNS 中則會出錯，但我們已經從 TARGET_COLUMNS 刪除 SLD010H 了）
        
        # --- 3. 篩選所需的欄位 ---
        # 確保要篩選的欄位清單包含 TARGET_COLUMNS 和 'Source'
        required_cols = [col for col in TARGET_COLUMNS if col in df.columns] + ["Source"]

        # 只保留所需欄位。使用 .copy() 避免 SettingWithCopyWarning
        df = df[required_cols].copy() 


        # --- 4. 計算缺失率 ----
        miss_pct = df.drop(columns=["Source"]).isnull().mean() * 100
        missing_by_folder[folder_name] = miss_pct.to_dict()

        dfs.append(df)

    if not dfs:
        raise FileNotFoundError("❌ 沒有成功讀到任何 cleaned CSV")

    print("\n✔ 完成所有 cleaned CSV 讀取、篩選及標準化")
    return dfs, missing_by_folder

def merge_all(dfs):
    print("➡ 合併所有年份的資料（outer union）")
    merged = pd.concat(dfs, ignore_index=True, sort=False)
    print(f"✔ 合併完成：{merged.shape[0]} 列, {merged.shape[1]} 欄位")
    return merged


def save_missing_matrix(missing_by_folder, output_path):

    # 轉成 DataFrame：row=folder, column=col_name
    df_missing = pd.DataFrame.from_dict(missing_by_folder, orient="index")
    df_missing = df_missing.sort_index()

    df_missing.to_csv(output_path)
    print(f"✔ 輸出各年份缺失比例矩陣：{output_path}")

# ---- 畫 heatmap ----
def plot_heatmap(missing_csv_path):

    df = pd.read_csv(missing_csv_path, index_col=0)

    # 取出數字年份
    df["sort_key"] = df.index.str.extract(r"(\d+)$").astype(int)
    df = df.sort_values("sort_key").drop(columns=["sort_key"])

    # 欄位依平均缺失率排序
    df = df[df.mean().sort_values(ascending=False).index]

    # 補 NaN → 代表該年份沒有此欄，視為 0%
    df = df.fillna(0)

    plt.figure(figsize=(20, 12))

    sns.heatmap(
        df,
        cmap="Reds",
        linewidths=0.2,
        linecolor="gray",
        cbar_kws={"label": "Missing %"},
    )

    plt.title("Missing Percentage Heatmap by Cycle and Column", fontsize=16)
    plt.xlabel("Column")
    plt.ylabel("NHANES Cycle")

    plt.tight_layout()
    plt.savefig("missing_heatmap.png", dpi=300)
    plt.show()

    print("✔ 已輸出 missing_heatmap.png")

# ---- 畫 heatmap ----
def plot_heatmap_new(missing_csv_path):
    
    # 您希望放在最前面的欄位清單
    target_cols = [
        "DIQ010", # diabetes (糖尿病)
        "MCQ160C",
        "MCQ160E",
        "MCQ160F",
        "MCQ160N",
        "MCQ080",
        "MCQ010",
        "MCQ035",
    ]

    df = pd.read_csv(missing_csv_path, index_col=0)

    # 取出數字年份
    df["sort_key"] = df.index.str.extract(r"(\d+)$").astype(int)
    df = df.sort_values("sort_key").drop(columns=["sort_key"])

    # --- 1. 自訂欄位排序邏輯 ---
    all_cols = list(df.columns)
    
    # 確保所有目標欄位都在 DataFrame 中
    existing_target_cols = [col for col in target_cols if col in all_cols]
    
    # 計算其餘欄位的平均缺失率並降序排序
    remaining_cols = [col for col in all_cols if col not in existing_target_cols]
    
    # 其餘欄位依平均缺失率排序
    sorted_remaining_cols = df[remaining_cols].mean().sort_values(ascending=False).index.tolist()
    
    # 最終欄位順序：目標欄位 + 剩餘排序欄位
    final_col_order = existing_target_cols + sorted_remaining_cols
    df = df[final_col_order]
    
    # 將 NaN 替換為 100 (代表該欄位在該週期中『從未出現』，視為 100% 缺失)
    df_for_heatmap = df.fillna(100) 
    
    # --- 2. 準備顯示的文字標籤 ---
    # 準備一個與 df_for_heatmap 相同形狀的字串矩陣，顯示缺失百分比
    # 將數字格式化為帶有百分號的字串 (例如：50.0%)
    annot_data = df_for_heatmap.map(lambda x: f"{x:.0f}%")
    
    plt.figure(figsize=(20, 12))
    
    sns.heatmap(
        df_for_heatmap,
        cmap="Reds",
        linewidths=0.2,
        linecolor="gray",
        cbar_kws={"label": "Missing %"},
        vmin=0, 
        vmax=100, 
        # 【重要修改】設定 annot=True 並傳入格式化後的字串矩陣
        annot=annot_data,
        fmt="", # fmt 設為空字串，以使用我們自訂的字串矩陣
        annot_kws={"fontsize": 7} # 設定字體大小以防擁擠
    )
    
    plt.title("Missing Percentage Heatmap by Cycle and Column (Custom Order)", fontsize=16)
    plt.xlabel("Column")
    plt.ylabel("NHANES Cycle")

    plt.tight_layout()
    plt.savefig("missing_heatmap_annotated.png", dpi=300)
    plt.show()

    print("✔ 已輸出 missing_heatmap_annotated.png (自訂排序及標籤)")

# ---- 主流程 ----
def main():
    root = Path(".").resolve()

    dfs, missing_by_folder = collect_all_data(root)

    # ---- 合併所有年度 ----
    merged = merge_all(dfs)
    merged_path = root / "ALL_NHANES_MERGED_20072018.csv"
    merged.to_csv(merged_path, index=False)
    print(f"✔ ALL_NHANES_MERGED.csv 已輸出到：{merged_path}")

    # ---- 儲存各年份的缺失矩陣 ----
    missing_matrix_path = root / "missing_year_per_20072018.csv"
    save_missing_matrix(missing_by_folder, missing_matrix_path)

    # ---- 合併後整體缺失 ----
    merged_missing_pct = (merged.isnull().mean() * 100).sort_values(ascending=False)
    merged_missing_df = merged_missing_pct.to_frame("MissingPercent")
    merged_missing_df.to_csv(root / "missing_all_20072018.csv")
    print("✔ 已輸出 missing_all.csv（整體缺失率）")

    # ---- 畫 heatmap ----
    # plot_heatmap(missing_matrix_path)


if __name__ == "__main__":
    main()
    #missing_matrix_path = Path(".").resolve()/ "missing_year.csv"
    #plot_heatmap_new(missing_matrix_path)