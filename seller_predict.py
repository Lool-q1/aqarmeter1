import streamlit as st
import pandas as pd
import joblib
import json
import numpy as np

model = joblib.load("best_model.pkl")
scaler = joblib.load("scaler.pkl")

with open("district_map.json", encoding="utf-8") as f:
    district_map = json.load(f)

st.set_page_config(page_title="عقارميتر - منصة البائع", layout="centered")
st.title("📊 عقارميتر - تقدير السعر للبائع")
st.markdown("أدخل تفاصيل العقار وسنقوم بتوقع السعر المناسب بناءً على بيانات السوق في الرياض.")

# ترتيب الأحياء حسب الملف
district_names = list(district_map.keys())

# 🏗️ إدخالات المستخدم
st.subheader("📌 أدخل تفاصيل العقار:")

with st.form("prediction_form"):
    col1, col2 = st.columns(2)
    with col1:
        area = st.number_input("📐 المساحة (م²)", min_value=50)
        category = st.selectbox("🏠 نوع العقار", [3, 6], format_func=lambda x: "فيلا" if x == 3 else "شقة")
        beds = st.number_input("🛏️ عدد الغرف", min_value=0)
        livings = st.number_input("🛋️ عدد الصالات", min_value=0)
        wc = st.number_input("🚿 عدد دورات المياه", min_value=0)

    with col2:
        kitchen = st.number_input("🍽️ عدد المطابخ", min_value=0)
        street_width = st.number_input("🛣️ عرض الشارع", min_value=5)
        district = st.selectbox("📍 الحي", options=district_names)
        distance_to_school = st.slider("🏫 المسافة لأقرب مدرسة (متر)", 0, 5000, 1000)
        distance_to_hospital = st.slider("🏥 المسافة لأقرب مستشفى (متر)", 0, 5000, 1000)
        distance_to_mall = st.slider("🛍️ المسافة لأقرب مول (متر)", 0, 5000, 1000)
        distance_to_park = st.slider("🌳 المسافة لأقرب حديقة (متر)", 0, 5000, 1000)
        distance_to_grocery = st.slider("🛒 المسافة لأقرب بقالة (متر)", 0, 3000, 500)

    submitted = st.form_submit_button("🔮 تقدير السعر")
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
            "street_width": street_width
        }])

        scaled_input = scaler.transform(input_data)
        prediction_log = model.predict(scaled_input)
        prediction = np.expm1(prediction_log[0])

        st.success(f" السعر المتوقع: {prediction:,.0f} ريال")

