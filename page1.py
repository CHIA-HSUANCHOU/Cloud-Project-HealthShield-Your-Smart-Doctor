import streamlit as st
import numpy as np

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
    value = st.number_input(
        label,
        min_value=min_val,
        max_value=max_val,
        value=None,
        step=step,
        key=key
    )

    unknown = st.checkbox(
        "I don't know",
        key=f"{key}_unknown"
    )

    if unknown:
        return None
    return value


# ---------- Demographics ----------
st.header("Basic Information")

# 使用 2 欄佈局
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

with col_gender:
    # 這是為了視覺上的對齊，因為 number_input_with_missing 佔用更多垂直空間

    gender = st.selectbox(
        "Gender / 性別",
        options=["male", "female"],
        index=None
    )

st.divider()
# ---------- Body Measurements ----------
st.header("Body Measurements")

# 使用 st.columns 將輸入欄位並排顯示
col_height, col_weight, col_bmi = st.columns(3)

with col_height:
    height_cm = number_input_with_missing(
        label="Height / 身高 (cm) ",
        min_val=30.0,
        max_val=250.0,
        key="height_cm",
        step=0.1
    )

with col_weight:
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
# ---------- Family history & Habits ----------
st.header("Family History & Lifestyle")

col_a, col_b = st.columns(2)

# Col A: 家族史, 吸菸, 飲酒
with col_a:
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


# Col B: 活動, 睡眠, 自評健康
with col_b:
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
st.header("Blood Pressure")

col_systolic, col_diastolic = st.columns(2)

with col_systolic:
    systolic_avg = number_input_with_missing(
        label="Systolic Blood Pressure / 收縮壓 (mmHg)",
        min_val=50.0,
        max_val=250.0,
        key="systolic_avg",
        step=1.0
    )

with col_diastolic:
    diastolic_avg = number_input_with_missing(
        label="Diastolic Blood Pressure / 舒張壓 (mmHg)",
        min_val=0.0,
        max_val=140.0,
        key="diastolic_avg",
        step=1.0
    )

st.divider()
# ---------- Blood Pressure ----------
st.header("Blood Test Results")

col_test1, col_test2, col_test3 = st.columns(3)

with col_test1:
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


with col_test2:
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


with col_test3:
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

# ---------- Summary ----------
st.divider()
user_input = {
    "age": age,
    "gender": gender,
    "height_cm": height_cm,
    "weight_kg": weight_kg,
    "bmi": bmi,
    "waist_cm": waist_cm,
    "systolic_avg": systolic_avg,
    "diastolic_avg": diastolic_avg,

    "fasting_glucose":fasting_glucose,
    "insulin":insulin,
    "HbA1c":HbA1c,
    "total_cholesterol":total_cholesterol,
    "HDL":HDL,
    "LDL":LDL,
    "triglycerides":triglycerides,
    
    "ever_smoked":ever_smoked,
    "alcohol_drinks":alcohol_drinks,
    "moderate_activity":moderate_activity,
    "vigorous_activity":vigorous_activity,
    "family_diabetes":family_diabetes,
    "general_health":general_health,
    "Sleep_Hours": Sleep_Hours,
}

# 使用 st.expander 隱藏 Debug 資訊
# --- 數據清理函數 ---
def clean_input_data(user_input):
    """
    將使用者輸入字典中的類別型/字串變數轉換為數值格式 (1, 0, np.nan)。
    """
    cleaned_data = user_input.copy()

    # 規則 1: 通用二元變數 (Yes/No/I don't know)
    binary_map = {
        'yes': 1,
        'no': 2,
        "I don't know": np.nan,
    }

    # 規則 2: 性別 (Gender)
    # 將 'unknown' 視為缺失值 (np.nan)，'male' 設為 1，'female' 設為 0
    gender_map = {
        'male': 1,
        'female': 2,
    }

    # --- 應用轉換規則 ---

    # 1. 應用通用二元變數轉換
    # 根據您的 user_input 字典，以下欄位需要轉換
    binary_keys = [
        "ever_smoked", 
        "moderate_activity", 
        "vigorous_activity", 
        "family_diabetes"
    ]
    
    for key in binary_keys:
        value = cleaned_data.get(key)
        if isinstance(value, str):
            # 使用 .get() 處理可能的 'I don't know'
            cleaned_data[key] = binary_map.get(value.lower(), value)

    # 2. 應用性別轉換
    gender_value = cleaned_data.get("gender")
    if isinstance(gender_value, str):
        cleaned_data["gender"] = gender_map.get(gender_value.lower(), gender_value)
    
    # 3. 處理所有 None/未輸入的值（包括 number_input_with_missing 勾選 I don't know 時返回的 None）
    for key, value in cleaned_data.items():
        if value is None or (isinstance(value, str) and value == "I don't know"):
            cleaned_data[key] = np.nan
            
    return cleaned_data
error_placeholder = st.empty()



FIELD_DISPLAY_NAMES = {
    "age": "Age",
    "gender": "Gender",
    "height_cm": "Height",
    "weight_kg": "Weight",
    "waist_cm": "Waist Circumference",
    "systolic_avg": "Systolic Blood Pressure",
    "diastolic_avg": "Diastolic Blood Pressure",
    "fasting_glucose": "Fasting Glucose",
    "insulin": "Insulin",
    "HbA1c": "HbA1c",
    "total_cholesterol": "Total Cholesterol",
    "HDL": "HDL Cholesterol",
    "LDL": "LDL Cholesterol",
    "triglycerides": "Triglycerides",
    "ever_smoked": "Have you ever smoked?",
    "alcohol_drinks": "What is your average alcoholic drinks per day?",
    "moderate_activity": "Do you do moderate-intensity sports or fitness activities weekly?",
    "vigorous_activity": "Do you do vigorous-intensity sports or fitness activities weekly?",
    "family_diabetes": "Does a close relative have diabetes? ",
    "general_health": "How is your self-reported health status?",
    "Sleep_Hours": "How long do you sleep per night (hours)?",
}

# 數據驗證/傳輸按鈕
if st.button("Get My Prediction → / 獲取我的預測結果 →"):
    
    # 1. 執行全面驗證
    missing_fields_display = []
    
    # 遍歷所有輸入欄位
    for key, value in user_input.items():
        
        # 排除 BMI 的檢查，因為它是計算結果
        if key == 'bmi':
            continue

        #  檢查：如果值是 None (NULL, 未填寫, 或勾選了 I don't know)
        # 或選擇了 'unknown'
        unknown_checked = st.session_state.get(f"{key}_unknown", False)

        # 只有「沒填 + 沒勾 unknown」才算錯
        if value is None and not unknown_checked:
            display_name = FIELD_DISPLAY_NAMES.get(key, key)
            missing_fields_display.append(display_name)

    
    # 2. 處理驗證結果
    if missing_fields_display:
        # 顯示警告訊息，並阻止跳轉
        st.error(
            f"Please fill all columns.：\n\n{', '.join(missing_fields_display)}"
        )
        
    else:
        # 3. 數據清理和跳轉 (只有在驗證通過時才執行)
        error_placeholder.empty() # 清除任何舊的錯誤訊息
        
        cleaned_data = clean_input_data(user_input)
        
        st.session_state["p1_data"] = cleaned_data
        st.session_state["page"] = "P2"

## ---------------- Debug --------------------
#with st.expander("Input Summary / 輸入彙總 (Debug / Preview)"):
#    st.subheader("Raw Data:")
#    st.write(user_input)
#    st.subheader("Cleaned Data (Ready for ML Model):")
    # 在 Debug 區預覽轉換後的數據
#    st.write(clean_input_data(user_input))


## ----------------page 2 ------------------------------
# 1. 從 Session State 讀取第一頁傳來的數據
#data_for_prediction = st.session_state.get("p1_data")

#if data_for_prediction is not None:
    # 2. 進行模型預測 (例如：使用 Scikit-learn 或其他模型)
    # prediction_result = your_model.predict(data_for_prediction)

    # 3. 顯示結果和建議
    #st.header("Prediction Results / 預測結果")
    # ... 顯示預測分數和風險等級
