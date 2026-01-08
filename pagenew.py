import streamlit as st

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

# ---------- Helper (修改後的函數，將 I don't know 納入 selectbox) ----------
def input_or_select_unknown(label, min_val, max_val, key, step=0.1):
    
    # 步驟 1: 使用 st.selectbox 讓使用者選擇填寫方式
    options = ["Enter Value / 輸入數值", "I don't know / 我不知道"]
    
    # 保持 label 顯示在 selectbox 上方
    choice = st.selectbox(
        label,
        options=options,
        index=0, # 預設選擇 'Enter Value'
        key=f"{key}_choice"
    )
    
    # 步驟 2: 如果選擇 'I don't know'，直接返回 None
    if choice == "I don't know / 我不知道":
        # 佔位符確保垂直對齊
        st.write("") 
        return None
        
    # 步驟 3: 如果選擇 'Enter Value'，則顯示數字輸入框
    else:
        # 顯示一個沒有標籤的 st.number_input，只讓用戶看到數字輸入框
        value = st.number_input(
            " ", 
            min_value=min_val,
            max_val=max_val,
            value=None,
            step=step,
            key=key,
            label_visibility="collapsed" # 隱藏 number_input 自身的標籤
        )
        return value

# --------------------------------------------------------------------------


# ---------- Demographics ----------
st.header("Basic Information")

# 使用 2 欄佈局
col_age, col_gender = st.columns(2)

with col_age:
    # 年齡：不使用 I don't know 選項 (必填)
    age = st.number_input(
        label="Age / 年齡 (years)",
        min_value=1,
        max_value=120,
        value=None, 
        step=1,
        key="age_standard" 
    )

with col_gender:
    # 這裡無需額外的 st.write() 來對齊，因為 age 不再有 checkbox
    gender = st.selectbox(
        "Gender / 性別",
        options=["male", "female", "unknown"],
        index=None
    )


st.divider()
# ---------- Body Measurements ----------
st.header("Body Measurements")

# 使用 3 欄佈局 (身高、體重、BMI)
col_height, col_weight, col_bmi = st.columns(3)

with col_height:
    # 🎯 變更：使用新的函數
    height_cm = input_or_select_unknown(
        label="Height / 身高 (cm) ",
        min_val=30.0,
        max_val=250.0,
        key="height_cm",
        step=0.1
    )

with col_weight:
    # 🎯 變更：使用新的函數
    weight_kg = input_or_select_unknown(
        label="Weight / 體重 (kg)",
        min_val=3.0,
        max_val=250.0,
        key="weight_kg",
        step=0.1
    )

# 計算 BMI
if height_cm is not None and weight_kg is not None:
    height_m = height_cm / 100
    bmi = round(weight_kg / (height_m ** 2), 1) if height_m > 0 else 0.0
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
            delta="請輸入身高/體重" 
        )

# 腰圍保持在下一行
# 🎯 變更：使用新的函數
waist_cm = input_or_select_unknown(
    label="Waist Circumference / 腰圍 (cm)",
    min_val=10.0,
    max_val=200.0,
    key="waist_cm"
)

st.divider()
# ---------- Family history & Habits ----------
st.header("Family History & Lifestyle")

# 設置 2 欄佈局來組織習慣和健康狀況
col_a, col_b = st.columns(2)

# Col A: 家族史, 吸菸, 飲酒
with col_a:
    family_diabetes = st.selectbox(
        "Family history of diabetes",
        options=["yes", "no", "I don't know"],
        index=None
    )
    
    ever_smoked = st.selectbox(
        "Have you ever smoked?",
        options=["yes", "no", "I don't know"],
        index=None
    )
    
    # 🎯 變更：使用新的函數
    alcohol_drinks = input_or_select_unknown(
        label="Average alcoholic drinks per day",
        min_val=0.0,
        max_val=90.0,
        key="alcohol_drinks",
        step=0.5
    )


# Col B: 活動, 睡眠, 自評健康
with col_b:
    moderate_activity = st.selectbox(
        "Moderate physical activity (每周)",
        options=["yes", "no", "I don't know"],
        index=None
    )

    vigorous_activity = st.selectbox(
        "Vigorous physical activity (每周)",
        options=["yes", "no", "I don't know"],
        index=None
    )
    
    # 🎯 變更：使用新的函數
    Sleep_Hours = input_or_select_unknown(
        label="Sleep duration (hours per night)",
        min_val=0.0,
        max_val=17.0,
        key="sleep_time",
        step=0.5
    )
    
general_health = st.selectbox(
    "Self-reported health status (1=Poor, 5=Excellent)",
    options=[
        "5",
        "4",
        "3",
        "2",
        "1",
        "I don't know"
    ],
    index=None
)

st.divider()
# ---------- Blood Pressure ----------
st.header("Blood Pressure")

# 使用 2 欄佈局
col_systolic, col_diastolic = st.columns(2)

with col_systolic:
    # 🎯 變更：使用新的函數
    systolic_avg = input_or_select_unknown(
        label="Systolic Blood Pressure / 收縮壓 (mmHg)",
        min_val=50.0,
        max_val=250.0,
        key="systolic_avg",
        step=1.0
    )

with col_diastolic:
    # 🎯 變更：使用新的函數
    diastolic_avg = input_or_select_unknown(
        label="Diastolic Blood Pressure / 舒張壓 (mmHg)",
        min_val=0.0,
        max_val=140.0,
        key="diastolic_avg",
        step=1.0
    )

st.divider()
# ---------- Blood Test Results ----------
st.header("Blood Test Results")

# 使用 3 欄佈局來容納 7 個數值，分兩行
col_test1, col_test2, col_test3 = st.columns(3)

with col_test1:
    # 🎯 變更：使用新的函數
    fasting_glucose = input_or_select_unknown(
        label="Fasting Glucose / 空腹血糖 (mg/dL)",
        min_val=15.0,
        max_val=600.0,
        key="fasting_glucose",
        step=1.0
    )

    # 🎯 變更：使用新的函數
    total_cholesterol = input_or_select_unknown(
        label="Total Cholesterol (mg/dL)",
        min_val=50.0,
        max_val=850.0,
        key="total_cholesterol",
        step=1.0
    )

    # 🎯 變更：使用新的函數
    triglycerides = input_or_select_unknown(
        label="Triglycerides / 三酸甘油脂 (mg/dL)",
        min_val=10.0,
        max_val=3000.0,
        key="triglycerides",
        step=1.0
    )


with col_test2:
    # 🎯 變更：使用新的函數
    insulin = input_or_select_unknown(
        label="Insulin / 胰島素 (µU/mL)",
        min_val=0.0,
        max_val=700.0,
        key="insulin",
        step=0.1
    )

    # 🎯 變更：使用新的函數
    HDL = input_or_select_unknown(
        label="HDL Cholesterol (mg/dL)",
        min_val=5.0,
        max_val=250.0,
        key="HDL",
        step=1.0
    )


with col_test3:
    # 🎯 變更：使用新的函數
    HbA1c = input_or_select_unknown(
        label="HbA1c (%)",
        min_val=0.0,
        max_val=20.0,
        key="HbA1c",
        step=0.1
    )

    # 🎯 變更：使用新的函數
    LDL = input_or_select_unknown(
        label="LDL Cholesterol (mg/dL)",
        min_val=5.0,
        max_val=400.0,
        key="LDL",
        step=1.0
    )

# ---------- Summary ----------
st.divider()
# 使用 st.expander 將 Debug 資訊收合，讓頁面更乾淨
with st.expander("Input Summary (Debug / Preview)"):
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
        
    st.write(user_input)

# ---------- Next Page ----------
st.divider()
if st.button("Next → P2"):
    st.session_state["p1_data"] = user_input
    st.session_state["page"] = "P2"