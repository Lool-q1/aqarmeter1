import streamlit as st
import pandas as pd
import folium
from PIL import Image
from streamlit_folium import folium_static
import base64
import random

st.set_page_config(page_title="عقارميتر – خريطة العقارات", layout="wide")


st.markdown("""<style>
/* خلفية الشريط الجانبي */
    [data-testid="stSidebar"] {
        background-color: #E6DAF0 !important;
    }

    /* منع التمرير داخل بعض العناصر */
    .css-1lcbmhc.e1fqkh3o9 {
        overflow: hidden !important;
    }

    /* ارتفاع الخريطة */
    iframe {
        height: 750px !important;
    }

    /* محاذاة النصوص في الشريط الجانبي لليمين */
    [data-testid="stSidebar"] * {
        text-align: right !important;
        direction: rtl !important;
    }

    /* محاذاة عناوين subheader */
    .css-1aumxhk.e1fqkh3o5 {
        text-align: right !important;
    }
    </style>
""", unsafe_allow_html=True)



def load_logo_base64(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

logo_base64 = load_logo_base64("logo.png")

st.markdown(
    f"""
    <div style="display: flex; justify-content: center; margin-top: -40px; margin-bottom: 0px;">
        <img src="data:image/png;base64,{logo_base64}" style="width: 200px;" />
    </div>
    """, unsafe_allow_html=True
)

df = pd.read_csv("sample_real_estate_data.csv")
type_map = {3: "فيلا", 6: "شقة"}
df["نوع العقار"] = df["category"].map(type_map)

لون_شقة = "#8D6E97"
لون_فيلا = "#A47148"
df["نوع العقار"] = df["category"].map({3: "فيلا", 6: "شقة"})
df = df.dropna(subset=["district", "price", "distance_to_school", "distance_to_grocery"])

cheapest_villas = df[df["نوع العقار"] == "فيلا"].copy()
cheapest_villas = cheapest_villas.loc[cheapest_villas.groupby("district")["price"].idxmin()]
cheapest_villas = cheapest_villas.sort_values(by="price").head(5)
j0 = [
    f"🌟 أرخص فيلا في {row['district']} بـ {int(row['price']):,} ريال فقط، تبعد {int(row['distance_to_school'])}م عن المدرسة — <a href='?selected={i}'>عرض العقار</a>"
    for i, row in cheapest_villas.iterrows()
]

# أرخص شقق
cheapest_apartments = df[df["نوع العقار"] == "شقة"].copy()
cheapest_apartments = cheapest_apartments.loc[cheapest_apartments.groupby("district")["price"].idxmin()]
cheapest_apartments = cheapest_apartments.sort_values(by="price").head(5)
j1 = [
    f"فرصة! شقة في {row['district']} بـ {int(row['price']):,} ريال فقط، تبعد {int(row['distance_to_school'])}م عن المدرسة — <a href='?selected={i}'>عرض العقار</a>"
    for i, row in cheapest_apartments.iterrows()
]

avg_prices = df[df["نوع العقار"] == "شقة"].groupby("district")["price"].mean().sort_values(ascending=False).head(5)
j2 = [
    f"متوسط سعر الشقق في {dist} هو {int(price):,} ريال"
    for dist, price in avg_prices.items()
]

near_grocery = df[df["distance_to_grocery"] < 300].sort_values("distance_to_grocery").head(5)
j3 = [
    f" عقار في {row['district']} يبعد {int(row['distance_to_grocery'])}م فقط عن البقالة — <a href='?selected={i}'>عرض العقار</a>"
    for i, row in near_grocery.iterrows()
]

motasafa = df[(df["beds"] >= 4) & (df["price"] < 1000000)].sort_values("price").head(5)
j4 = [
    f"{row['نوع العقار']} في {row['district']} بـ {int(row['price']):,} ريال يحتوي على {int(row['beds'])} غرف و{int(row['wc'])} حمامات — <a href='?selected={i}'>عرض العقار</a>"
    for i, row in motasafa.iterrows()
]

all_msgs = j0 + j1 + j2 + j3 + j4
if all_msgs:
    content = "".join([
        f"<span style='margin-left: 80px;'>{msg}</span>"
        for msg in all_msgs
    ])
else:
    content = "<span style='color:white;'>لا توجد بيانات لعرض الأخبار حالياً.</span>"

# ✅ تيكر متجدد، بني فاتح، مستمر بدون توقف
st.markdown(f"""
    <style>
    .ticker-container {{
        background-color: #F3E1C7;
        padding: 12px 0;
        overflow: hidden;
        position: relative;
        border-radius: 12px;
        margin-bottom: 25px;
        direction: rtl;
    }}
    .ticker-content {{
        display: inline-block;
        white-space: nowrap;
        animation: ticker-scroll 200s linear infinite;
        font-size: 17px;
        color: #4B3832;
    }}
    .ticker-content span {{
        margin-left: 80px;
    }}
    @keyframes ticker-scroll {{
        0% {{ transform: translateX(100%); }}
        100% {{ transform: translateX(-100%); }}
    }}
    </style>
    <div class="ticker-container">
        <div class="ticker-content">
            {content}
        </div>
    </div>
""", unsafe_allow_html=True)

# الشريط الجانبي للفلاتر
st.sidebar.markdown("## خيارات البحث")
col1, col2 = st.sidebar.columns(2)
with col1:
    نوع = st.selectbox("نوع العقار", ["الكل", "شقة", "فيلا"])
with col2:
    الحي = st.selectbox("الحي", ["الكل"] + sorted(df["district"].dropna().unique().tolist()))

st.sidebar.subheader("السعر المطلوب")
col3, col4 = st.sidebar.columns(2)
with col3:
    سعر_من = st.number_input("من", min_value=0, value=0, step=50000)
with col4:
    سعر_إلى = st.number_input("إلى", min_value=0, value=int(df["price"].max()), step=50000)

غرف = st.sidebar.number_input("عدد الغرف", min_value=0, max_value=int(df["beds"].max()), value=0)
صالات = st.sidebar.number_input("عدد الصالات", min_value=0, max_value=int(df["livings"].max()), value=0)
حمامات = st.sidebar.number_input("عدد الحمامات", min_value=0, max_value=int(df["wc"].max()), value=0)
مطابخ = st.sidebar.number_input("عدد المطابخ", min_value=0, max_value=int(df["kitchen"].max()), value=0)

if نوع != "الكل":
    df = df[df["نوع العقار"] == نوع]
if الحي != "الكل":
    df = df[df["district"] == الحي]

df = df[
    (df["price"] >= سعر_من) &
    (df["price"] <= سعر_إلى) &
    (df["beds"] >= غرف) &
    (df["livings"] >= صالات) &
    (df["wc"] >= حمامات) &
    (df["kitchen"] >= مطابخ)
]

selected = st.query_params.get("selected")

if df.empty or df["location.lat"].isna().all() or df["location.lng"].isna().all():
    m = folium.Map(location=[24.7136, 46.6753], zoom_start=11)
    st.warning("لا توجد عقارات مطابقة للخيارات الحالية. تم عرض الخريطة بدون أي نقاط.")
else:
    lat, lon = df["location.lat"].mean(), df["location.lng"].mean()
    m = folium.Map(location=[lat, lon], zoom_start=11)

    if selected and selected.isdigit():
        s = df.iloc[int(selected)]

        folium.CircleMarker(
            location=[s["location.lat"], s["location.lng"]],
            radius=7,
            color=لون_شقة if s["category"] == 6 else لون_فيلا,
            fill=True,
            fill_color=لون_شقة if s["category"] == 6 else لون_فيلا,
            fill_opacity=0.9,
            popup=folium.Popup(f"""
                <b>نوع:</b> {s['نوع العقار']}<br>
                <b>السعر:</b> {s['price']:,} ريال<br>
                <b>الحي:</b> {s['district']}<br>
                <b>الغرف:</b> {s['beds']} | <b>الصالات:</b> {s['livings']} | <b>الحمامات:</b> {s['wc']} | <b>المطابخ:</b> {s['kitchen']}<br>
                <b>المساحة:</b> {s['area']} م²
            """, max_width=500)
        ).add_to(m)

        الخدمات = {
            "مدرسة": ("school_lat", "school_lon", "distance_to_school", "graduation-cap"),
            "مستشفى": ("hospital_lat", "hospital_lon", "distance_to_hospital", "plus-square"),
            "مول": ("mall_lat", "mall_lon", "distance_to_mall", "shopping-bag"),
            "حديقة": ("park_lat", "park_lon", "distance_to_park", "tree"),
            "بقالة": ("grocery_lat", "grocery_lon", "distance_to_grocery", "shopping-cart")
        }

        for اسم, (lat_col, lon_col, dist_col, icon_name) in الخدمات.items():
            المسافة = f"{int(s[dist_col])} م"
            folium.Marker(
                location=[s[lat_col], s[lon_col]],
                popup=folium.Popup(f"{اسم} - {المسافة}", max_width=500),
                icon=folium.Icon(icon=icon_name, prefix="fa", color="orange")
            ).add_to(m)

    elif نوع != "الكل" or الحي != "الكل":
        for idx, row in df.iterrows():
            نص = f"""
            <b>نوع:</b> {row['نوع العقار']}<br>
            <b>السعر:</b> {row['price']:,} ريال<br>
            <b>الحي:</b> {row['district']}<br>
            <b>الغرف:</b> {row['beds']} | <b>الصالات:</b> {row['livings']} | <b>الحمامات:</b> {row['wc']} | <b>المطابخ:</b> {row['kitchen']}<br>
            <b>المساحة:</b> {row['area']} م²<br>
            <a href="?selected={idx}">عرض الخدمات القريبة</a>
            """
            folium.CircleMarker(
                location=[row["location.lat"], row["location.lng"]],
                radius=6,
                color=لون_شقة if row["category"] == 6 else لون_فيلا,
                fill=True,
                fill_color=لون_شقة if row["category"] == 6 else لون_فيلا,
                fill_opacity=0.9,
                popup=folium.Popup(نص, max_width=500)
            ).add_to(m)

folium_static(m)





