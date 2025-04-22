import streamlit as st
import base64

st.set_page_config(layout="wide")

def get_base64(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

video_base64 = get_base64("intro.mp4")
logo_base64 = get_base64("logo.png")

st.markdown(f"""
    <style>
        .video-container {{
            position: relative;
            width: 100%;
            height: auto;
        }}
        .video-container video {{
            width: 100%;
            height: auto;
        }}
        .logo-overlay {{
            position: absolute;
            top: -200px;
            left: 50%;
            transform: translate(-50%, -50%);
            animation: slideDown 2s forwards;
            z-index: 10;
            width: 370px;
            filter: brightness(0.7) contrast(1.1);
        }}
        @keyframes slideDown {{
            0% {{ top: -200px; opacity: 0; }}
            100% {{ top: 50%; opacity: 1; }}
        }}
    </style>

    <div class="video-container">
        <video autoplay muted>
            <source src="data:video/mp4;base64,{video_base64}" type="video/mp4">
        </video>
        <img src="data:image/png;base64,{logo_base64}" class="logo-overlay" />
    </div>

    <iframe id="hiddenFrame" style="display:none;"></iframe>

    <script>
        setTimeout(function() {{
            var iframe = document.getElementById('hiddenFrame');
            iframe.src = window.location.origin + "/?page=sp";
            window.location.href = iframe.src;
        }}, 5000);
    </script>
""", unsafe_allow_html=True)
