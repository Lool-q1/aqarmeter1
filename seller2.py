import streamlit as st
import pandas as pd
import numpy as np
import shap
import joblib
import json
import base64
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic

model = joblib.load("best_model.pkl")
scaler = joblib.load("scaler.pkl")

with open("district_map.json", encoding="utf-8") as f:
    district_map = json.load(f)

with open("district_coordinates.json", encoding="utf-8") as f:
    district_coords = json.load(f)

df_services = pd.read_csv("RYDH_real_estate_data.csv")
district_names = list(district_map.keys())

st.set_page_config(page_title="عقارميتر", layout="wide")

st.markdown("""
    <style>
    .css-ocqkz7 {
        background-color: #F2E6F7 !important;
        padding: 20px;
        border-radius: 12px;
    }
    .css-1lcbmhc.e1fqkh3o9 {
        overflow: hidden !important;
    }
    </style>
""", unsafe_allow_html=True)

def load_logo_base64(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

logo_base64 = load_logo_base64("logo.png")

st.markdown(
    f"""
    <div style="display: flex; justify-content: center; margin-top: -70px; margin-bottom: -70px;">
        <img src="data:image/png;base64,{logo_base64}" style="width: 280px;" />
    </div>
    """, unsafe_allow_html=True
)

st.markdown("<h2 style='text-align: center; color:#4b0082;'>نظام ذكي يساعد على تحديد سعر العقار بدقة</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>أدخل تفاصيل العقار وسنقوم بتوقع السعر المناسب بناءً على البيانات المدخلة</p>", unsafe_allow_html=True)

left_col, right_col = st.columns([1.3, 1.7])

with right_col:
    district = st.selectbox("الحي", options=district_names)
    user_location = None
    distances = {}

    if district:
        lat, lon = district_coords[district]

        if "user_location" not in st.session_state:
            m = folium.Map(location=[lat, lon], zoom_start=13)
            map_result = st_folium(m, width=700, height=500, returned_objects=["last_clicked"])

            if map_result and map_result.get("last_clicked"):
                st.session_state["user_location"] = (
                    map_result["last_clicked"]["lat"],
                    map_result["last_clicked"]["lng"]
                )
                st.rerun()

        else:
            user_location = st.session_state["user_location"]
            m = folium.Map(location=user_location, zoom_start=14)

            folium.Marker(
                location=user_location,
                popup="موقع العقار",
                icon=folium.Icon(color="orange", icon="home")
            ).add_to(m)

            services_in_district = df_services[df_services["district"] == district]
            service_types = {
                "مدرسة": ("school_lat", "school_lon", "purple", "graduation-cap"),
                "مستشفى": ("hospital_lat", "hospital_lon", "purple", "plus-square"),
                "مول": ("mall_lat", "mall_lon", "purple", "shopping-bag"),
                "حديقة": ("park_lat", "park_lon", "purple", "tree"),
                "بقالة": ("grocery_lat", "grocery_lon", "purple", "shopping-cart")
            }

            for name, (lat_col, lon_col, color, icon) in service_types.items():
                service_coords = services_in_district[[lat_col, lon_col]].dropna().values
                if len(service_coords) > 0:
                    closest = min(service_coords, key=lambda coord: geodesic(user_location, coord).meters)
                    closest_distance = geodesic(user_location, closest).meters
                    distances[name] = round(closest_distance)

                    folium.Marker(
                        location=closest,
                        popup=name,
                        icon=folium.Icon(color=color, icon=icon, prefix='fa')
                    ).add_to(m)
                else:
                    distances[name] = 99999

            st_folium(m, width=700, height=500)

            st.success("تم تحديد موقع العقار!")

            if st.button("🔄 إعادة تحديد الموقع"):
                st.session_state.pop("user_location", None)
                st.rerun()

with left_col:
    with st.container():
        with st.form("prediction_form"):
            st.markdown("<h4 style='text-align: right;'>أدخل تفاصيل العقار:</h4>", unsafe_allow_html=True)

            area = st.number_input("المساحة (م²)", min_value=50)
            category = st.selectbox("نوع العقار", [3, 6], format_func=lambda x: "فيلا" if x == 3 else "شقة")
            beds = st.number_input("عدد الغرف", min_value=0)
            livings = st.number_input("عدد الصالات", min_value=0)
            wc = st.number_input("عدد دورات المياه", min_value=0)
            kitchen = st.number_input("عدد المطابخ", min_value=0)
            street_width = st.number_input("عرض الشارع", min_value=5)

            st.markdown("<h5 style='margin-top:20px;'>المسافات إلى أقرب الخدمات:</h5>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("مدرسة", value=str(distances["مدرسة"]) + " متر" if user_location else "", disabled=True)
                st.text_input("مستشفى", value=str(distances["مستشفى"]) + " متر" if user_location else "", disabled=True)
                st.text_input("مول", value=str(distances["مول"]) + " متر" if user_location else "", disabled=True)
            with col2:
                st.text_input("حديقة", value=str(distances["حديقة"]) + " متر" if user_location else "", disabled=True)
                st.text_input("بقالة", value=str(distances["بقالة"]) + " متر" if user_location else "", disabled=True)

            submitted = st.form_submit_button("تقدير السعر")

    if submitted and user_location:
      input_data = pd.DataFrame([{
        "distance_to_school": distances["مدرسة"],
        "distance_to_hospital": distances["مستشفى"],
        "distance_to_mall": distances["مول"],
        "district_encoded": district_map[district],
        "distance_to_park": distances["حديقة"],
        "distance_to_grocery": distances["بقالة"],
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

    # عمود في المنتصف
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("#### السعر المتوقع:")
        st.success(f"{prediction:,.0f} ريال سعودي")

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
            st.markdown("#### <span style='color:#4b0082;'>التفسير:</span>", unsafe_allow_html=True)
            st.info(f"<div style='text-align:center;'>{'العقار يتميز بـ ' + التفاصيل}، مما ساهم في رفع قيمته السوقية.</div>", unsafe_allow_html=True)

        shap_df = pd.DataFrame({
            'العامل': [ترجمة_الميزات[f] for f in input_data.columns],
            'التأثير': shap_row
        }).sort_values(by="العامل")

        # رسم الرسم البياني داخل العمود الأوسط بحجم مخصص
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(8, 4))
        shap_df.set_index("العامل").plot(kind="line", ax=ax)
        st.pyplot(fig)
