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

def load_logo_base64(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

logo_base64 = load_logo_base64("logo.png")

st.markdown(
    f"""
    <div style="display: flex; justify-content: center; margin-top: -90px; margin-bottom: -90px;">
        <img src="data:image/png;base64,{logo_base64}" style="width: 280px;" />
    </div>
    """, unsafe_allow_html=True
)

st.markdown("<h2 style='text-align: center; color:#4b0082;'>نظام ذكي يساعد على تحديد سعر العقار بدقة</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>أدخل تفاصيل العقار وسنقوم بتوقع السعر المناسب بناءً على البيانات المدخلة</p>", unsafe_allow_html=True)
st.markdown("<br><br><br>", unsafe_allow_html=True)

left_col, right_col = st.columns([1.8, 1.2])

with left_col:
    district = st.selectbox(" ", options=district_names, label_visibility="collapsed")
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
                icon=folium.Icon(color='purple', icon="home")
            ).add_to(m)

            services_in_district = df_services[df_services["district"] == district]
            service_types = {
                "مدرسة": ("school_lat", "school_lon", 'darkpurple', "graduation-cap"),
                "مستشفى": ("hospital_lat", "hospital_lon", 'darkpurple', "plus-square"),
                "مول": ("mall_lat", "mall_lon",'darkpurple', "shopping-bag"),
                "حديقة": ("park_lat", "park_lon",'darkpurple', "tree"),
                "بقالة": ("grocery_lat", "grocery_lon",'darkpurple', "shopping-cart")
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

if "user_location" in st.session_state:
    user_location = st.session_state["user_location"]
    with st.container():
        center_col = st.columns([0.2, 0.6, 0.2])[1]
        with center_col:
            st.markdown("<h4 style='text-align:center;'>المسافات إلى أقرب الخدمات</h4>", unsafe_allow_html=True)
            row_all = st.columns(5)
            row_all[0].text_input("مدرسة", f"{distances['مدرسة']} متر", disabled=True)
            row_all[1].text_input("مستشفى", f"{distances['مستشفى']} متر", disabled=True)
            row_all[2].text_input("مول", f"{distances['مول']} متر", disabled=True)
            row_all[3].text_input("حديقة", f"{distances['حديقة']} متر", disabled=True)
            row_all[4].text_input("بقالة", f"{distances['بقالة']} متر", disabled=True)

    st.markdown("<br>", unsafe_allow_html=True)
    spacer, col1, col2 = st.columns([0.3, 0.1, 0.4])
    with col1:
        submit_clicked = st.button(" تقدير السعر")
    with col2:
        if st.button("إعادة تحديد الموقع"):
            st.session_state.pop("user_location", None)
            st.rerun()
else:
    submit_clicked = False

with right_col:
    with st.container():
        # عنوان الإكسباندر يمين
        st.markdown("""
            <style>
                div[data-testid="stExpander"] summary {
                    direction: rtl;
                    text-align: right;
                    font-size: 1.1rem;
                    font-weight: bold;
                    color: #4b0082;
                }
            </style>
        """, unsafe_allow_html=True)

        with st.expander("أدخل تفاصيل العقار", expanded=True):
            # تصغير المسافات لأقصى حد
            st.markdown("""
                <style>
                    div[data-testid="stVerticalBlock"] {
                        gap: 1px !important;
                        padding-bottom: 0px !important;
                    }
                    div[data-testid="stVerticalBlock"] label,
                    p {
                        margin-bottom: 1px !important;
                        margin-top: 2px !important;
                        font-size: 15px;
                    }
                </style>
            """, unsafe_allow_html=True)

            st.markdown("<p style='text-align: right;'>المساحة (م²)</p>", unsafe_allow_html=True)
            area = st.number_input("", min_value=50, max_value=1830, key="area")

            st.markdown("<p style='text-align: right;'>نوع العقار</p>", unsafe_allow_html=True)
            category = st.selectbox("", [3, 6], format_func=lambda x: "فيلا" if x == 3 else "شقة", key="cat")

            st.markdown("<p style='text-align: right;'>عدد الغرف</p>", unsafe_allow_html=True)
            beds = st.number_input("", min_value=0, max_value=7, key="beds")

            st.markdown("<p style='text-align: right;'>عدد الصالات</p>", unsafe_allow_html=True)
            livings = st.number_input("", min_value=0, max_value=7, key="livings")

            st.markdown("<p style='text-align: right;'>عدد دورات المياه</p>", unsafe_allow_html=True)
            wc = st.number_input("", min_value=0, max_value=5, key="wc")

            st.markdown("<p style='text-align: right;'>عدد المطابخ</p>", unsafe_allow_html=True)
            kitchen = st.number_input("", min_value=0, max_value=1, key="kitchen")

            st.markdown("<p style='text-align: right;'>عرض الشارع</p>", unsafe_allow_html=True)
            street_width = st.number_input("", min_value=5, max_value=100, key="street")

# الزر الخارجي موجود مسبقًا:
# submit_clicked = st.button("📊 تقدير السعر")

if submit_clicked and user_location:
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
    prediction = model.predict(scaled_input)[0] 



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

    with st.container():
        center_col = st.columns([0.2, 0.6, 0.2])[1]
        with center_col:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<h4 style='text-align: right; color:black;'>السعر المتوقع</h4>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f"""
            <div style='text-align: center; background-color: #d4edda; padding: 12px; border-radius: 5px; font-size: 18px; font-weight: bold; color: #155724;'>
               <span style='direction: rtl;'>{prediction:,.0f} ريال سعودي</span>
            </div>
            """, unsafe_allow_html=True)


            if عوامل_إيجابية:
                التفاصيل = "، و".join(عوامل_إيجابية)
                st.markdown("<h4 style='text-align: right;'>التفسير</h4>", unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown(f"""
                <div style='text-align: right; background-color: #e8f0fe; padding: 10px; border-radius: 5px;'>
                العقار يتميز بـ {التفاصيل}، مما ساهم في رفع قيمته السوقية.
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<h4 style='text-align: right;'>تحليل العوامل المؤثرة</h4>", unsafe_allow_html=True)

            shap_df = pd.DataFrame({
                'العامل': [ترجمة_الميزات[f] for f in input_data.columns],
                'التأثير': shap_row
            }).sort_values(by="العامل")
            st.line_chart(shap_df.set_index("العامل"))



