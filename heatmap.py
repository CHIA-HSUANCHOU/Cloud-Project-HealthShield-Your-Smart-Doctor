import pandas as pd
from pathlib import Path
import seaborn as sns
import matplotlib.pyplot as plt


def calculate_single_conditional_missingness(df, condition_col):
    """
    計算在移除特定 condition_col 缺失值的列之後，其他變數的缺失率。
    """
    
    df_copy = df.copy()
    
    if 'Source' not in df_copy.columns:
        # Source 欄位是用來分組（nhanes_20012002）的，必須存在。
        print("❌ 錯誤：DataFrame 必須包含 'Source' 欄位來區分年份週期。")
        return None
        
    # 移除 condition_col 中有缺失值的列
    df_conditional = df_copy.dropna(subset=[condition_col], how='any')
    
    print(f"  ✔ 針對 {condition_col} 篩選完成：原始 {df.shape[0]} 列，篩選後剩餘 {df_conditional.shape[0]} 列。")
    
    # 排除 Source 和條件欄位本身，來計算剩餘變數的缺失率
    cols_to_check = [col for col in df_conditional.columns if col not in ['Source', condition_col]]
    
    missing_by_folder_conditional = {}
    
    # 按 'Source'（年份）分組，計算缺失率
    for folder_name, group in df_conditional.groupby('Source'):
        # 計算每個變數在該年份組內的缺失率
        miss_pct = group[cols_to_check].isnull().mean() * 100
        missing_by_folder_conditional[f"nhanes_{folder_name}"] = miss_pct.to_dict()
        
    # 轉成 DataFrame：row=folder, column=col_name
    df_missing_conditional = pd.DataFrame.from_dict(missing_by_folder_conditional, orient="index")
    
    return df_missing_conditional


def plot_conditional_missing_heatmap(df_missing, condition_col):
    """
    繪製單一條件缺失率 Heatmap
    """
    # 取出數字年份進行排序
    df_missing["sort_key"] = df_missing.index.str.extract(r"(\d+)$").astype(int)
    df_missing = df_missing.sort_values("sort_key").drop(columns=["sort_key"])
    
    # 欄位依平均缺失率排序
    df_missing = df_missing[df_missing.mean().sort_values(ascending=False).index]
    
    # 將 NaN 替換為 100 (代表該欄位在該週期中『從未出現』)
    df_for_heatmap = df_missing.fillna(100) 
    
    # 準備顯示的文字標籤（無小數點）
    annot_data = df_for_heatmap.map(lambda x: f"{x:.0f}%")
    
    plt.figure(figsize=(20, 12))
    
    sns.heatmap(
        df_for_heatmap,
        cmap="Reds",
        linewidths=0.2,
        linecolor="gray",
        cbar_kws={"label": "Conditional Missing %"},
        vmin=0, 
        vmax=100, 
        annot=annot_data,
        fmt="", 
        annot_kws={"fontsize": 6} 
    )
    
    title_str = f"Conditional Missing % Heatmap (Condition: No NaN in {condition_col})"
    plt.title(title_str, fontsize=16)
    plt.xlabel(f"Columns (Excluding Source and {condition_col})")
    plt.ylabel("NHANES Cycle")

    plt.tight_layout()
    output_filename = f"conditional_missing_heatmap_{condition_col}.png"
    plt.savefig(output_filename, dpi=300)
    plt.close() # 關閉圖形以避免佔用記憶體
    
    print(f"  ✔ 已輸出 {output_filename}")


def run_all_conditional_plots(merged_data_path, condition_columns):
    
    # 確保所有欄位名稱大寫一致（以應對您的輸入）
    condition_columns = [col.upper() for col in condition_columns]
    
    print(f"📥 讀取合併資料：{merged_data_path}")
    try:
        # 讀取合併資料。dtype=str 是為了確保 NaN 能夠被正確識別
        df = pd.read_csv(merged_data_path, dtype=str)
    except FileNotFoundError:
        print(f"❌ 錯誤：找不到檔案 {merged_data_path}。請確認檔案路徑是否正確。")
        return

    # 檢查所有條件欄位是否都存在於 DataFrame 中
    missing_cols = [col for col in condition_columns if col not in df.columns]
    if missing_cols:
        print(f"❌ 錯誤：以下條件欄位在合併資料中不存在：{', '.join(missing_cols)}")
        return

    print(f"🚀 開始繪製 {len(condition_columns)} 個條件缺失率 Heatmap...")
    for col in condition_columns:
        print(f"\n--- 處理條件變數: {col} ---")
        
        # 1. 計算條件缺失矩陣
        df_missing = calculate_single_conditional_missingness(df, col)
        
        if df_missing is not None:
            # 2. 繪製 Heatmap
            plot_conditional_missing_heatmap(df_missing, col)

    print("\n🎉 所有條件缺失率 Heatmap 已繪製完成。")

if __name__ == "__main__":
    
    # 您希望作為條件的欄位清單
    #condition_columns = [
    #    "DIQ010", 
    #    "MCQ160C", # 假設您的 CSV 欄位名稱是大寫
    #    "MCQ160E",
    #    "MCQ160F",
    #    "MCQ160N",
    #    "MCQ080",
    #    "MCQ010",
        # "MCQ035", # 您最新清單中移除了 MCQ035
    #]
    condition_columns = [
        "DIQ010", 
    ]
    
    # 確保合併檔案路徑正確
    MERGED_DATA_PATH = Path(".").resolve() / "ALL_NHANES_MERGED_20072018.csv"
    
    # 運行分析
    run_all_conditional_plots(MERGED_DATA_PATH, condition_columns)    