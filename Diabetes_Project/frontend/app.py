import streamlit as st
import numpy as np
import requests
import os
import json
import base64
import streamlit.components.v1 as components

# --- 1. 設定後端連線 ---
# 從環境變數抓取，如果沒設定預設用 localhost (方便本地測試)
# 在 Docker Compose 裡我們會設定成 http://backend:8000
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# --- 2. 定義欄位名稱對照表 (Frontend -> Backend NHANES Codes) ---
# 左邊是你前端的變數名，右邊是模型訓練時用的 NHANES 代碼
NAME_MAPPING = {
    "age": "RIDAGEYR",
    "gender": "RIAGENDR",
    "height_cm": "BMXHT",
    "weight_kg": "BMXWT",
    "bmi": "BMXBMI",
    "waist_cm": "BMXWAIST",
    "systolic_avg": "systolic_avg",   # 後端這兩個是用 avg 命名的
    "diastolic_avg": "diastolic_avg",
    "fasting_glucose": "LBXGLU",
    "insulin": "LBXIN",
    "HbA1c": "LBXGH",
    "total_cholesterol": "LBXTC",
    "HDL": "LBDHDD",
    "LDL": "LBDLDL",
    "triglycerides": "LBXTR",
    "ever_smoked": "SMQ020",
    "alcohol_drinks": "ALQ130",
    "moderate_activity": "PAQ665", # 或 PAQ650，視你訓練時選哪一個
    "vigorous_activity": "PAQ650", # 或 PAQ665
    "family_diabetes": "MCQ300C",
    "general_health": "HUQ010",
    "Sleep_Hours": "Sleep_Hours"
}

st.set_page_config(page_title="HealthShield", layout="wide")

# 初始化 session state 用於分頁管理
if "page" not in st.session_state:
    st.session_state["page"] = "input"
if "prediction_result" not in st.session_state:
    st.session_state["prediction_result"] = None

# ==========================================
#  頁面 1: 輸入表單 (Input Form)
# ==========================================
if st.session_state["page"] == "input":
    st.markdown(
        """
        <h1 style="margin-bottom: 0.2em;">Welcome to HealthShield</h1>
        <p style="font-size: 1.2em; color: #555;">
            Know Your Diabetes Risk, Take Control of Your Health
        </p>
        """,
        unsafe_allow_html=True
    )
    st.divider()

    # ---------- Helper ----------
    def number_input_with_missing(label, min_val, max_val, key, step=0.1):
        value = st.number_input(label, min_value=min_val, max_value=max_val, value=None, step=step, key=key)
        unknown = st.checkbox("I don't know", key=f"{key}_unknown")
        if unknown: return None
        return value

    # ---------- Demographics ----------
    st.header("Basic Information / 基本資料")
    col_age, col_gender = st.columns(2)
    with col_age:
        age = st.number_input(
        label="Age",
        min_value=1,
        max_value=120,
        value=None, # 可以將其設為 None 讓用戶必須輸入
        step=1,
        key="age" # 使用新的 key
    )

    with col_gender: # 這是為了視覺上的對齊，因為 number_input_with_missing 佔用更多垂直空間
        gender = st.selectbox("Gender / 性別", ["male", "female"], index=None)

    st.divider()
    # ---------- Body Measurements ----------
    st.header("Body Measurements / 身體測量")
    col_h, col_w, col_bmi = st.columns(3)
    with col_h:
        height_cm = number_input_with_missing(
            label="Height / 身高 (cm) ",
            min_val=30.0,
            max_val=250.0,
            key="height_cm",
            step=0.1
        )

    with col_w:
        weight_kg = number_input_with_missing(
            label="Weight / 體重 (kg)",
            min_val=3.0,
            max_val=250.0,
            key="weight_kg",
            step=0.1
        )
        
    # 計算 BMI
    if height_cm is not None and weight_kg is not None:
        # BMI = 體重 (kg) / [身高 (m)]²
        height_m = height_cm / 100
        if height_m > 0:
            bmi = round(weight_kg / (height_m ** 2), 1)
        else:
            # 避免除以零
            bmi = 0.0
    else:
        bmi = None

    # 使用 st.metric 顯示 BMI 數值
    with col_bmi:
        if bmi is not None:
            st.metric(
                label="BMI / 身體質量指數", 
                value=bmi
            )
        else:
            st.metric(
                label="BMI / 身體質量指數", 
                value="--",
                delta="請輸入身高/體重" # 顯示缺省符號
            )

    # 腰圍保持在下一行，因為它是獨立的測量項目
    waist_cm = number_input_with_missing(
        label="Waist Circumference / 腰圍 (cm)",
        min_val=10.0,
        max_val=200.0,
        key="waist_cm"
    )

    st.divider()
    # ---------- Family & Lifestyle ----------
    st.header("Family History & Lifestyle / 家族病史 & 生活作息")
    c1, c2 = st.columns(2)
    with c1:
        family_diabetes = st.selectbox(
        "Does a close relative have diabetes? / 您的近親是否患有糖尿病嗎？",
        options=["yes", "no", "I don't know"],
        index=None
        )
        
        moderate_activity = st.selectbox(
            "Do you do moderate-intensity sports or fitness activities (e.g., brisk walking, swimming) weekly? / 您每週有從事中等強度運動或健身活動嗎 (例如快走、游泳)？",
            options=["yes", "no", "I don't know"],
            index=None
        )

        alcohol_drinks = number_input_with_missing(
            label="What is your average alcoholic drinks per day? / 您平均每天飲用多少酒精飲品？",
            min_val=0.0,
            max_val=90.0,
            key="alcohol_drinks",
            step=0.5
        )
    with c2:
        st.write("")
        ever_smoked = st.selectbox(
            "Have you ever smoked? / 您是否曾經吸菸？" ,
            options=["yes", "no", "I don't know"],
            index=None
        )

        vigorous_activity = st.selectbox(
            "Do you do vigorous-intensity sports or fitness activities (e.g., running, basketball) weekly? / 您每週有從事高強度運動或健身活動嗎 (例如跑步、籃球)？",
            options=["yes", "no", "I don't know"],
            index=None
        )
        
        Sleep_Hours = number_input_with_missing(
            label="How long do you sleep per night (hours)? / 您每晚睡眠時長（小時）是多久？",
            min_val=0.0,
            max_val=17.0,
            key="Sleep_Hours",
            step=0.1
        )
        
    general_health = st.selectbox(
        "How is your self-reported health status? (1=Poor, 5=Excellent) / 您的自評健康狀況如何？(1=差, 5=極佳)",
        options=[
            5,  
            4,  
            3,  
            2, 
            1, 
            "I don't know" 
        ],
        index=None
    )
    
    st.divider()
    # ---------- Blood Pressure ----------
    st.header("Blood Pressure / 血壓")
    c3, c4 = st.columns(2)
    with c3:
        systolic_avg = number_input_with_missing(
        label="Systolic Blood Pressure / 收縮壓 (mmHg)",
        min_val=50.0,
        max_val=250.0,
        key="systolic_avg",
        step=1.0
    )
        
    with c4:
        diastolic_avg = number_input_with_missing(
        label="Diastolic Blood Pressure / 舒張壓 (mmHg)",
        min_val=0.0,
        max_val=140.0,
        key="diastolic_avg",
        step=1.0
    )

    st.divider()
    # ---------- Blood Tests ----------
    st.header("Blood Test Results / 血液檢查結果")
    c5, c6, c7 = st.columns(3)
    with c5:
        fasting_glucose = number_input_with_missing(
        label="Fasting Glucose / 空腹血糖 (mg/dL)",
        min_val=15.0,
        max_val=600.0,
        key="fasting_glucose",
        step=1.0
        )

        total_cholesterol = number_input_with_missing(
            label="Total Cholesterol / 總膽固醇 (mg/dL)",
            min_val=50.0,
            max_val=850.0,
            key="total_cholesterol",
            step=1.0
        )

        triglycerides = number_input_with_missing(
            label="Triglycerides / 三酸甘油脂 (mg/dL)",
            min_val=10.0,
            max_val=3000.0,
            key="triglycerides",
            step=1.0
        )
        
    with c6:
        insulin = number_input_with_missing(
            label="Insulin / 胰島素 (µU/mL)",
            min_val=0.0,
            max_val=700.0,
            key="insulin",
            step=0.1
        )

        HDL = number_input_with_missing(
            label="HDL Cholesterol / HDL 膽固醇 (mg/dL)",
            min_val=5.0,
            max_val=250.0,
            key="HDL",
            step=1.0
        )
        
    with c7:
        HbA1c = number_input_with_missing(
            label="HbA1c / 糖化血色素 (%)",
            min_val=0.0,
            max_val=20.0,
            key="HbA1c",
            step=0.1
        )

        LDL = number_input_with_missing(
            label="LDL Cholesterol / LDL 膽固醇 (mg/dL)",
            min_val=5.0,
            max_val=400.0,
            key="LDL",
            step=1.0
        )

    st.divider()
    # 收集輸入
    user_input = {
        "age": age, "gender": gender, "height_cm": height_cm, "weight_kg": weight_kg, "bmi": bmi,
        "waist_cm": waist_cm, "systolic_avg": systolic_avg, "diastolic_avg": diastolic_avg,
        "fasting_glucose": fasting_glucose, "insulin": insulin, "HbA1c": HbA1c,
        "total_cholesterol": total_cholesterol, "HDL": HDL, "LDL": LDL, "triglycerides": triglycerides,
        "ever_smoked": ever_smoked, "alcohol_drinks": alcohol_drinks,
        "moderate_activity": moderate_activity, "vigorous_activity": vigorous_activity,
        "family_diabetes": family_diabetes, "general_health": general_health, "Sleep_Hours": Sleep_Hours
    }

    # 驗證邏輯 (這裡保留你原本寫得很棒的邏輯)
    missing_fields = []
    for k, v in user_input.items():
        if k == 'bmi': continue
        if v is None and not st.session_state.get(f"{k}_unknown", False):
            missing_fields.append(k)

    if st.button("Get My Prediction → / 獲取我的預測結果 →"):
        if missing_fields:
            st.error(f"Please fill: {', '.join(missing_fields)}")
        else:
            # --- 數據清理與轉換 ---
            cleaned = user_input.copy()
            binary_map = {'yes': 1, 'no': 2, "I don't know": None}
            gender_map = {'male': 1, 'female': 2}
            
            # 套用清理邏輯
            for k in ["ever_smoked", "moderate_activity", "vigorous_activity", "family_diabetes"]:
                if isinstance(cleaned[k], str): cleaned[k] = binary_map.get(cleaned[k].lower())
            if isinstance(cleaned["gender"], str):
                cleaned["gender"] = gender_map.get(cleaned["gender"].lower())
            for k, v in cleaned.items():
                if v == "I don't know": cleaned[k] = None

            # ★★★ 關鍵步驟：轉換成後端看不懂的變數名稱 ★★★
            payload = {}
            for frontend_key, backend_key in NAME_MAPPING.items():
                if frontend_key in cleaned:
                    payload[backend_key] = cleaned[frontend_key]

            # 呼叫 API
            try:
                with st.spinner("Analyzing with AI Model..."):
                    response = requests.post(f"{BACKEND_URL}/predict", json=payload)
                
                if response.status_code == 200:
                    st.session_state["prediction_result"] = response.json()
                    st.session_state["page"] = "result" # 跳轉頁面
                    st.rerun() # 強制刷新
                else:
                    st.error(f"Backend Error: {response.text}")
            except Exception as e:
                st.error(f"Connection Failed: {e}")

# ==========================================
#  頁面 2: 結果顯示 (Result Page)
# ==========================================
elif st.session_state["page"] == "result":
    res = st.session_state["prediction_result"]
    
    st.button("← Back to Calculator / 回到前一頁", on_click=lambda: st.session_state.update({"page": "input"}))
    
    st.markdown("<h1 style='text-align: center;'>Prediction Results / 預測結果</h1>", unsafe_allow_html=True)
    
    # 顯示機率
    prob = res['probability']
    color = "#d32f2f" if prob > 0.5 else "#388e3c"
    risk_level = "HIGH RISK / 高度風險"
    if prob <= 0.3:
        risk_level = "LOW RISK / 低度風險"
    elif prob <= 0.7:
        risk_level = "MEDIUM RISK / 中度風險"
    
    st.markdown(f"""
        <div style='text-align: center; padding: 30px; border-radius: 15px; background-color: #f0f2f6; border: 2px solid {color};'>
            <h3 style='color: #555;'>Diabetes Probability</h3>
            <h1 style='color: {color}; font-size: 4em; margin: 0;'>{prob*100:.1f}%</h1>
            <h3 style='color: {color}; letter-spacing: 2px;'>{risk_level}</h3>
        </div>
    """, unsafe_allow_html=True)

    # 建議
    if res.get("advice"):
        st.subheader("📋 Recommendations / 建議")
        for item in res["advice"]: st.info(item)

    # SHAP 圖表
    if "shap_local" in res:
        st.markdown("---")
        st.header("🔍 Why this result? (AI Explanation) / 個人風險分析")
        st.markdown("Understanding the key factors driving this prediction. / 了解影響糖尿病的重要因素")
        
        shap_data = res["shap_local"]
        tab1, tab2 = st.tabs(["Waterfall Plot (Factor Contribution) / 風險累積圖", "Force Plot (Risk Push/Pull) / 風險拔河圖"])
        
        with tab1:
            st.caption("How each value pushes the risk up (Red) or down (Blue) from the average. / 您的風險是如何累積的？")
            
            # 加入解釋文字 (使用 st.info 讓它看起來像個提示框)
            st.info("""
            這張圖展示了從「平均值」到「您的預測值」的過程：
            - 🟥 **紅色長條**：代表**推高**風險的因素（如 BMI、血糖數值）。
            - 🟦 **藍色長條**：代表**降低**風險的保護因素（如年齡、運動習慣）。
            
            您可以清楚看到是哪幾個關鍵指標將您的風險數值推高或拉低的。
            """)
            
            if "waterfall" in shap_data:
                img = base64.b64decode(shap_data['waterfall'])
                st.image(img, width="stretch")
        
        with tab2:
            st.caption("Visualizing the balance of risk factors. / 風險因子 vs 保護因子")

            st.info("""
            這是一場風險的拔河比賽：
            - **紅色力量** ➡️：試圖將預測結果推向「高風險」。
            - **藍色力量** ⬅️：試圖將預測結果拉回「低風險」。
            
            中間的交界處就是兩股力量平衡後的最終結果。條狀越寬，代表該特徵的影響力越大。
            """)
            
            if "force_html" in shap_data:
                components.html(shap_data['force_html'], height=100, scrolling=True)

    st.markdown("---")
    st.header("📊 Global Explanation / 模型整體解釋")
    st.write("The most important features for whole people.")

    # 呼叫後端 API 拿圖
    try:
        # 注意：這裡是 GET 請求
        resp = requests.get(f"{BACKEND_URL}/global_shap")
        
        if resp.status_code == 200:
            plots = resp.json()
            
            tab1, tab2 = st.tabs(["Beeswarm / 特徵影響力", "Bar / 重要性排名"])
            
            with tab1:
                if "beeswarm" in plots:
                    # 解碼並顯示
                    img_data = base64.b64decode(plots['beeswarm'])
                    st.image(img_data, caption="紅點代表數值高，藍點代表數值低；越往右邊代表風險越高。", width="stretch")
                else:
                    st.info("暫無圖表數據")
                    
            with tab2:
                if "bar" in plots:
                    img_data = base64.b64decode(plots['bar'])
                    st.image(img_data, caption="特徵重要性平均排名", width="stretch")
                else:
                    st.info("暫無圖表數據")
                    
    except Exception as e:
        st.error(f"無法載入圖表: {e}")
