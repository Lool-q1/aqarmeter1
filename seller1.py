import streamlit as st
import pandas as pd
import joblib
import json
import numpy as np
import shap
import base64

# تحميل النموذج والمقياس
model = joblib.load("best_model.pkl")
scaler = joblib.load("scaler.pkl")

with open("district_map.json", encoding="utf-8") as f:
    district_map = json.load(f)

st.set_page_config(page_title="عقارميتر - منصة البائع", layout="centered")

# --- الشعار ---
def load_logo_base64(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

logo_base64 = load_logo_base64("logo.png")

st.markdown(
    f"""
    <div style="display: flex; justify-content: center; margin-top: -70px; margin-bottom: -50px;">
        <img src="data:image/png;base64,{logo_base64}" style="width: 320px;" />
    </div>
    """, unsafe_allow_html=True
)

# --- العنوان الرئيسي ---
st.markdown("""
<h2 style='text-align: center; color: #5e3c88;'>نظام ذكي يساعد على تحديد سعر العقار بدقة</h2>
<p style='text-align: center; color: #555; font-size: 16px;'>أدخل تفاصيل العقار وسنقوم بتوقع السعر المناسب بناءً على البيانات المدخلة</p>
""", unsafe_allow_html=True)


# --- تنسيق الصندوق البنفسجي ---
st.markdown("""
    <style>
    section[data-testid="stForm"] {
        background-color: #faf5ff;
        border: 2px solid #b497bd;
        border-radius: 15px;
        padding: 30px;
        box-shadow: 0 0 12px #d6c0e4;
        margin-top: 20px;
    }
    </style>
""", unsafe_allow_html=True)
st.markdown("""
<style>
/* ✅ تغيير لون خط التقدم (اللي كان برتقالي) إلى بني */
[data-baseweb="slider"] > div > div:nth-child(3) {
    background: #A47148 !important; /* لون بني أنيق */
}

/* ✅ تغيّير لون النقطة (المؤشر) إذا تبين */
[data-baseweb="slider"] [role="slider"] {
    background-color: #b497bd !important;
    border: 1px solid #b497bd !important;
}
</style>
""", unsafe_allow_html=True)




district_names = list(district_map.keys())

# ✅ تنسيق محاذاة جميع العناصر داخل الفورم إلى اليمين
st.markdown("""
<style>
section[data-testid="stForm"] {
    direction: rtl;
    text-align: right;
}
label, .stTextInput label, .stNumberInput label, .stSelectbox label, .stSlider label {
    text-align: right !important;
    display: block;
}
</style>
""", unsafe_allow_html=True)

# --- النموذج ---
with st.form("prediction_form"):
    st.markdown("<h4 style='text-align: right;'>:أدخل تفاصيل العقار</h4>", unsafe_allow_html=True)

    area = st.number_input("المساحة (م²)", min_value=50)
    category = st.selectbox("نوع العقار", [3, 6], format_func=lambda x: "فيلا" if x == 3 else "شقة")
    beds = st.number_input("عدد الغرف", min_value=0)
    livings = st.number_input("عدد الصالات", min_value=0)
    wc = st.number_input("عدد دورات المياه", min_value=0)
    kitchen = st.number_input("عدد المطابخ", min_value=0)
    street_width = st.number_input("عرض الشارع", min_value=5)
    district = st.selectbox("الحي", options=district_names)
    distance_to_school = st.slider("المسافة لأقرب مدرسة (متر)", 0, 40000, 1000)
    distance_to_hospital = st.slider("المسافة لأقرب مستشفى (متر)", 0, 40000, 1000)
    distance_to_mall = st.slider("المسافة لأقرب مول (متر)", 0, 40000, 1000)
    distance_to_park = st.slider("المسافة لأقرب حديقة (متر)", 0, 40000, 1000)
    distance_to_grocery = st.slider("المسافة لأقرب بقالة (متر)", 0, 3000, 500)

    submitted = st.form_submit_button("تقدير السعر")

    if submitted:
        input_data = pd.DataFrame([{
            "distance_to_school": distance_to_school,
            "distance_to_hospital": distance_to_hospital,
            "distance_to_mall": distance_to_mall,
            "district_encoded": district_map[district],
            "distance_to_park": distance_to_park,
            "distance_to_grocery": distance_to_grocery,
            "area": area,
            "beds": beds,
            "livings": livings,
            "wc": wc,
            "category": category,
            "street_width": street_width,
        }])

        scaled_input = scaler.transform(input_data)
        prediction_log = model.predict(scaled_input)
        prediction = np.expm1(prediction_log[0])

        st.success(f"السعر المتوقع: {prediction:,.0f} ريال سعودي")

        # --- تفسير SHAP ---
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(scaled_input)
        shap_row = shap_values[0]

        ترجمة_الميزات = {
            "distance_to_school": "قربه من المدرسة",
            "distance_to_hospital": "قربه من المستشفى",
            "distance_to_mall": "قربه من المول",
            "distance_to_park": "قربه من الحديقة",
            "distance_to_grocery": "قربه من البقالة",
            "district_encoded": "وقوعه في حي معروف",
            "area": "مساحته المناسبة",
            "beds": "عدد الغرف الملائم",
            "livings": "وجود أكثر من صالة",
            "wc": "وجود دورات مياه متعددة",
            "category": "كونه من نوع مميز",
            "street_width": "عرض الشارع المناسب",
        }

        عوامل_إيجابية = []
        for feature_name, shap_val in zip(input_data.columns, shap_row):
            if shap_val >= 0.001 and feature_name in ترجمة_الميزات:
                عوامل_إيجابية.append(ترجمة_الميزات[feature_name])

        if عوامل_إيجابية:
            التفاصيل = "، و".join(عوامل_إيجابية)
            st.markdown("### تفسير السعر المتوقع")
            st.info(f"العقار يتميز بـ {التفاصيل}، مما ساهم في رفع قيمته السوقية.")








