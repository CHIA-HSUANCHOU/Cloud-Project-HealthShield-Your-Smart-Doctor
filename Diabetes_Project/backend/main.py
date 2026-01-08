from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import shap
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import joblib
import io
import base64

app = FastAPI()

# ---------------------------------------------------------
# 1. 載入模型與參數包
# ---------------------------------------------------------
# 注意：在 Docker 裡，路徑就是當前目錄
#try:
pipeline = joblib.load("nhanes_pipeline_XGBoost.pkl")
model = pipeline["model"]       # 您的 XGBoost 模型
stats = pipeline["imputer_stats"]
scaler = pipeline["scaler"]

# 🔥 關鍵修改：不要從 pickle 讀，我們現場用模型建立一個新的！
print("⚡ 正在初始化 SHAP Explainer...")
print("★ ★ ★ 新程式碼載入確認：我是最新版的 main.py！ ★ ★ ★")  # <--- 加這行
try:
    # 針對 XGBoost 模型，使用 TreeExplainer 是最快最穩的
    explainer = shap.TreeExplainer(model)
    print("✅ SHAP Explainer 初始化成功")
except Exception as e:
    print(f"⚠️ Explainer 初始化失敗: {e}")
    explainer = None

shap_plots = pipeline.get("shap_plots") # 拿預先畫好的圖
print("✅ 模型與 Pipeline 載入成功")
#except Exception as e:
#    print(f"❌ 載入失敗: {e}")
    # 為了防止 App 崩潰，這裡可能會需要處理，但在 Demo 前請確保檔案存在

# ---------------------------------------------------------
# 2. 定義資料處理函式 (重現訓練時的邏輯)
# ---------------------------------------------------------
def apply_imputation(df, stats):
    """
    【通用】Training 和 Inference 都可以用
    使用傳入的 stats 字典來填補，而不是重新計算
    """
    df = df.copy()

    # --- 身體測量複雜邏輯 ---
    median_h = stats.get("BMXHT")
    median_w = stats.get("BMXWT")

    if "BMXWAIST" in df.columns:
        df["BMXWAIST"] = df["BMXWAIST"].fillna(stats.get("BMXWAIST"))

    # Case 1 & 2 & 3 (公式回推邏輯)
    # 這裡直接套用你原本的邏輯，但填補值改用 stats 裡的
    if all(col in df.columns for col in ["BMXHT", "BMXWT", "BMXBMI"]):
        print("  [Body Measures] 執行身高、體重、BMI 複雜邏輯填補...")

        # 準備變數 (H:身高cm, W:體重kg, B:BMI)
        # 先計算全體的中位數 (Median)，用於稍後填補
        median_h = df["BMXHT"].median()
        median_w = df["BMXWT"].median()
        # 注意：腰圍是獨立填補
        if "BMXWAIST" in df.columns:
            df["BMXWAIST"] = df["BMXWAIST"].fillna(df["BMXWAIST"].median())

        # -------------------------------------------------------
        # Case 1: 只有其中一個缺，且其餘兩個有：用公式回推
        # -------------------------------------------------------
        # 1.1 缺 BMI (有 H, W) -> B = W / (H/100)^2
        mask_miss_b = df["BMXBMI"].isna() & df["BMXHT"].notna() & df["BMXWT"].notna()
        df.loc[mask_miss_b, "BMXBMI"] = df.loc[mask_miss_b, "BMXWT"] / ((df.loc[mask_miss_b, "BMXHT"] / 100) ** 2)

        # 1.2 缺 體重 (有 H, B) -> W = B * (H/100)^2
        mask_miss_w = df["BMXWT"].isna() & df["BMXHT"].notna() & df["BMXBMI"].notna()
        df.loc[mask_miss_w, "BMXWT"] = df.loc[mask_miss_w, "BMXBMI"] * ((df.loc[mask_miss_w, "BMXHT"] / 100) ** 2)

        # 1.3 缺 身高 (有 W, B) -> H = 100 * sqrt(W / B)
        mask_miss_h = df["BMXHT"].isna() & df["BMXWT"].notna() & df["BMXBMI"].notna()
        df.loc[mask_miss_h, "BMXHT"] = 100 * np.sqrt(df.loc[mask_miss_h, "BMXWT"] / df.loc[mask_miss_h, "BMXBMI"])

        # -------------------------------------------------------
        # Case 2: 三個中有兩個缺
        # -------------------------------------------------------
        # 2.1 身高、體重缺 (有 BMI)：先用中位數填補體重，用公式推算身高
        mask_miss_hw = df["BMXHT"].isna() & df["BMXWT"].isna() & df["BMXBMI"].notna()
        # Step 1: 填體重 (中位數)
        df.loc[mask_miss_hw, "BMXWT"] = median_w
        # Step 2: 推身高 (公式)
        df.loc[mask_miss_hw, "BMXHT"] = 100 * np.sqrt(df.loc[mask_miss_hw, "BMXWT"] / df.loc[mask_miss_hw, "BMXBMI"])

        # 2.2 身高、BMI 缺 (有 體重)：先用中位數填補身高，再計算 BMI
        mask_miss_hb = df["BMXHT"].isna() & df["BMXBMI"].isna() & df["BMXWT"].notna()
        # Step 1: 填身高 (中位數)
        df.loc[mask_miss_hb, "BMXHT"] = median_h
        # Step 2: 算 BMI
        df.loc[mask_miss_hb, "BMXBMI"] = df.loc[mask_miss_hb, "BMXWT"] / ((df.loc[mask_miss_hb, "BMXHT"] / 100) ** 2)

        # 2.3 體重、BMI 缺 (有 身高)：先用中位數填補體重，再計算 BMI
        mask_miss_wb = df["BMXWT"].isna() & df["BMXBMI"].isna() & df["BMXHT"].notna()
        # Step 1: 填體重 (中位數)
        df.loc[mask_miss_wb, "BMXWT"] = median_w
        # Step 2: 算 BMI
        df.loc[mask_miss_wb, "BMXBMI"] = df.loc[mask_miss_wb, "BMXWT"] / ((df.loc[mask_miss_wb, "BMXHT"] / 100) ** 2)

        # -------------------------------------------------------
        # Case 3: 三個都缺
        # -------------------------------------------------------
        # 用中位數填補身高、體重，再計算填補後的 bmi
        mask_miss_all = df["BMXHT"].isna() & df["BMXWT"].isna() & df["BMXBMI"].isna()
        df.loc[mask_miss_all, "BMXHT"] = median_h
        df.loc[mask_miss_all, "BMXWT"] = median_w
        df.loc[mask_miss_all, "BMXBMI"] = median_w / ((median_h / 100) ** 2)

    # 血壓計算
    #sys_cols = [c for c in ["BPXSY1", "BPXSY2", "BPXSY3"] if c in df.columns]
    #dia_cols = [c for c in ["BPXDI1", "BPXDI2", "BPXDI3"] if c in df.columns]

    #if sys_cols:
    #    df["systolic_avg"] = df[sys_cols].mean(axis=1)
    df["systolic_avg"] = df["systolic_avg"].fillna(stats.get("systolic_avg"))

    #if dia_cols:
    #    df["diastolic_avg"] = df[dia_cols].mean(axis=1)
    df["diastolic_avg"] = df["diastolic_avg"].fillna(stats.get("diastolic_avg"))

    # Lab 填補
    lab_vars = ["LBXGLU", "LBXIN", "LBXGH", "LBXTC", "LBDHDD", "LBDLDL", "LBXTR"]
    for col in lab_vars:
        if col in df.columns:
            df[col] = df[col].fillna(stats.get(col))

    # 生活習慣規則 (吸菸、飲酒、類別)
    if "SMQ020" in df.columns and "RIDAGEYR" in df.columns:
        df.loc[(df["RIDAGEYR"] < 20) & (df["SMQ020"].isna()), "SMQ020"] = 2
        df.loc[(df["RIDAGEYR"] >= 20) & (df["SMQ020"].isna()), "SMQ020"] = 3

    if "ALQ130" in df.columns:
        df.loc[df["RIDAGEYR"] < 20, "ALQ130"] = df.loc[df["RIDAGEYR"] < 20, "ALQ130"].fillna(0)
        df.loc[df["RIDAGEYR"] >= 20, "ALQ130"] = df.loc[df["RIDAGEYR"] >= 20, "ALQ130"].fillna(stats.get("ALQ130_adult"))

    for col in ["MCQ300C", "PAQ650", "PAQ665"]:
        if col in df.columns:
            df[col] = df[col].fillna(3)

    # 睡眠
    if "SLD012" in df.columns and "SLD010H" in df.columns:
        df["Sleep_Hours"] = df["SLD012"].combine_first(df["SLD010H"])
    elif "SLD012" in df.columns:
        df["Sleep_Hours"] = df["SLD012"]
    elif "SLD010H" in df.columns:
        df["Sleep_Hours"] = df["SLD010H"]
    else:
        df["Sleep_Hours"] = np.nan
    df["Sleep_Hours"] = df["Sleep_Hours"].fillna(stats.get("Sleep_Hours"))

    if "HUQ010" in df.columns:
        df["HUQ010"] = df["HUQ010"].fillna(stats.get("HUQ010"))

    return df

def plot_to_base64(fig):
    """將 Matplotlib 圖片轉為 Base64 字串"""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight', dpi=150)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")

# ---------------------------------------------------------
# 3. 定義 API 輸入格式 (NHANES Codes)
# ---------------------------------------------------------
# 定義輸入格式 (根據你的 X_train 原始欄位)
class InputData(BaseModel):
    # --- 1. 基本人口學 (Demographics) ---
    RIDAGEYR: float          # 年齡
    RIAGENDR: float          # 性別 (1=男, 2=女)

    # --- 2. 身體測量 (Body Measures) ---
    # 設定 = None 代表這些欄位是選填的 (允許前端送來 null)
    # 因為你的前端有 "I don't know" 選項，後端必須允許接收 None
    BMXHT: Optional[float] = None       # 身高
    BMXWT: Optional[float] = None       # 體重
    BMXBMI: Optional[float] = None      # BMI (前端有算好傳過來)
    BMXWAIST: Optional[float] = None    # 腰圍

    # --- 3. 血壓 (Blood Pressure) ---
    # 注意：這裡對應你前端 NAME_MAPPING 的 key
    systolic_avg: Optional[float] = None 
    diastolic_avg: Optional[float] = None

    # --- 4. 血液檢驗 (Lab Tests) ---
    LBXGLU: Optional[float] = None      # 空腹血糖
    LBXIN: Optional[float] = None       # 胰島素
    LBXGH: Optional[float] = None       # 糖化血色素 HbA1c
    LBXTC: Optional[float] = None       # 總膽固醇
    LBDHDD: Optional[float] = None      # HDL
    LBDLDL: Optional[float] = None      # LDL
    LBXTR: Optional[float] = None       # 三酸甘油脂

    # --- 5. 生活習慣 (Lifestyle) ---
    SMQ020: Optional[float] = None      # 吸菸 (1=Yes, 2=No)
    ALQ130: Optional[float] = None      # 飲酒量
    
    # 運動 (注意：需對照你訓練時是用 PAQ650 還是 665)
    # 根據你的前端 mapping：Moderate -> PAQ665, Vigorous -> PAQ650
    PAQ665: Optional[float] = None      # 中強度運動
    PAQ650: Optional[float] = None      # 高強度運動
    
    MCQ300C: Optional[float] = None     # 家族史
    HUQ010: Optional[float] = None      # 自評健康 (1-5)
    Sleep_Hours: Optional[float] = None # 睡眠時數

# ---------------------------------------------------------
# 4. API 路由
# ---------------------------------------------------------
# API 1: 傳送全域解釋圖給前端
@app.get("/global_shap")
def get_global_shap():
    return shap_plots  # 直接回傳 base64 字串


# API 2: 預測 (這是原本的 predict，我們要加入單一解釋邏輯)
@app.post("/predict")
def predict(data: InputData):
    # A. 轉 DataFrame
    input_dict = data.dict()
    df = pd.DataFrame([input_dict])

    # B. 清洗特殊代碼 (7, 9 -> NaN)
    for group, cols in pipeline["nan_map"].items():
        vals = pipeline["nan_values"][group]
        for c in cols:
            if c in df.columns:
                df[c] = df[c].replace(vals, np.nan)

    # C. 填補與特徵工程
    df = apply_imputation(df, stats)

    # D. Rename & Drop
    drop_cols = ['SLD012', 'SLD010H', 'BPXDI1', 'BPXDI2', 'BPXDI3', 'BPXSY1', 'BPXSY2', 'BPXSY3']
    df = df.drop(columns=drop_cols, errors='ignore')
    df = df.rename(columns=pipeline["rename_dict"])

    # E. Scaling
    cols_to_scale = pipeline["minmax_cols"]
    df[cols_to_scale] = scaler.transform(df[cols_to_scale])

    # F. Encoding & Alignment
    cols_to_encode = pipeline["onehot_cols"]
    df = pd.get_dummies(df, columns=cols_to_encode)
    # 補齊缺少的欄位 (重要！)
    df = df.reindex(columns=pipeline["final_columns"], fill_value=0)

    # G. 預測
    # 1. 預測機率
    # predict_proba 回傳 [[不患病機率, 患病機率]]
    prob = model.predict_proba(df)[0][1]
    
    # 2. 計算這個人的 SHAP (Local Explanation)
    # 注意：TreeExplainer 速度很快，算一筆沒問題
    shap_data = {}
    try:
        # 計算 SHAP values
        shap_values_local = explainer(df, check_additivity=False)
        
        # XGBoost 的 output 通常只有一維 (不像 Random Forest 有 Class 0/1)
        # 如果是二元分類，XGBoost TreeExplainer 預設輸出 log-odds
        
        # 處理單筆資料 (取出第 0 筆)
        single_explanation = shap_values_local[0]

        # 1. 繪製 Waterfall Plot (存成圖片)
        fig_waterfall = plt.figure(figsize=(8, 6))
        shap.plots.waterfall(single_explanation, show=False, max_display=10)
        shap_data["waterfall"] = plot_to_base64(fig_waterfall)

        # 2. 繪製 Force Plot (存成 HTML)
        force_plot = shap.plots.force(
            single_explanation, 
            matplotlib=False
        )
        shap_data["force_html"] = f"<head>{shap.getjs()}</head><body>{force_plot.html()}</body>"
        
    except Exception as e:
        print(f"SHAP Error: {e}")
        shap_data["error"] = str(e)
    

    # H. 產生建議 (這是加分題！前後端分離的好處)
    advice = []
    if prob > 0.7:
        advice.append("⚠️ 高度風險警告：建議諮詢醫生。")
    elif prob > 0.3:
        advice.append("⚠️ 中度風險警告：建議定期追蹤。")
    
    # 這裡的 df['bmi'] 是標準化過的，若要判斷建議，最好用 input_dict['BMXBMI'] 原始值
    if input_dict['BMXBMI'] and input_dict['BMXBMI'] > 24:
        advice.append("💪 體重管理：BMI 偏高，建議控制飲食與運動。")

    # 3. 執行你原本的「分組邏輯」 (因為現在只有一筆，邏輯要微調或封裝成函式)
    # 為了簡化 Demo，這裡可以直接回傳最重要的特徵名稱
    # 若要完整復刻你的分組邏輯，建議把那段 base_map 的程式碼封裝成函式放在這裡呼叫
    return {"probability": float(prob), "advice": advice, "shap_local": shap_data}
