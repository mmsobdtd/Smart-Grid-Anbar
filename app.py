import streamlit as st
import pandas as pd
import numpy as np
import time
import requests
from datetime import datetime

# --- 1. إعدادات التبليغ ---
BOT_TOKEN = "8732709590:AAG8kxcfijO6ZpjmIjk2Rj_JFxB5gNMarZs"
CHAT_ID = "5625855161"

POLE_INFO = {
    1: {"desc": "بين بيت 1 و بيت 2", "lat": 33.4245, "lon": 43.2678},
    2: {"desc": "بين بيت 2 و بيت 3", "lat": 33.4255, "lon": 43.2688},
    3: {"desc": "بين بيت 3 و بيت 4", "lat": 33.4265, "lon": 43.2698},
    4: {"desc": "بين بيت 4 و بيت 5", "lat": 33.4275, "lon": 43.2708}
}

def send_telegram_msg(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload, timeout=5)
        return True
    except:
        return False

# --- 2. التنسيق البصري الاحترافي ---
st.set_page_config(page_title="Al-Anbar Smart Grid v17.5", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .main-header { text-align: center; color: #1e3a8a; font-weight: bold; margin-bottom: 5px; }
    .sub-header { text-align: center; color: #444; font-size: 18px; margin-bottom: 15px; }
    .node-box {
        background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 12px;
        padding: 10px; text-align: center; min-height: 100px;
    }
    .house-box { background: #e7f5ff; border: 1px solid #74c0fc; border-radius: 10px; padding: 5px; text-align: center; }
    .theft-active { border: 2px solid #e03131 !important; background-color: #fff5f5 !important; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; height: 40px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. إدارة الحالة (لحفظ بيانات التجاوز) ---
if 'theft_state' not in st.session_state:
    st.session_state.theft_state = {1: False, 2: False, 3: False, 4: False}
if 'msg_history' not in st.session_state:
    st.session_state.msg_history = []
if 'last_count' not in st.session_state:
    st.session_state.last_count = 0

# الواجهة الرئيسية
st.markdown("<h1 class='main-header'>⚡ نظام الرصد والتبليغ الذكي v17.5</h1>", unsafe_allow_html=True)
st.markdown("<div class='sub-header'>إعداد الطلبة: محمد نبيل بردان | مشتاق طالب جلال</div>", unsafe_allow_html=True)
st.divider()

# --- 4. تعريف الهيكل الثابت (الأزرار والبيوت) ---
# هذه المنطقة تُرسم مرة واحدة فقط لتجنب خطأ Duplicate Key
metrics_placeholder = st.empty()

# رسم الخريطة (العواميد والبيوت)
street_cols = st.columns([1, 0.8, 1, 0.8, 1, 0.8, 1, 0.8, 1])
street_cols[0].markdown("<div class='node-box'>🏢<br><b>المحولة</b></div>", unsafe_allow_html=True)

for i in range(1, 5):
    street_cols[2*i-1].markdown(f"<div class='house-box'>🏠<br><small>بيت {i}</small></div>", unsafe_allow_html=True)
    with street_cols[2*i]:
        is_active = st.session_state.theft_state[i]
        box_style = "node-box theft-active" if is_active else "node-box"
        st.markdown(f"<div class='{box_style}'>🗼<br><small>{POLE_INFO[i]['desc']}</small></div>", unsafe_allow_html=True)
        
        # الأزرار خارج اللوب المستمر
        btn_label = "إيقاف" if is_active else "حقن"
        if st.button(btn_label, key=f"btn_p_{i}"):
            st.session_state.theft_state[i] = not st.session_state.theft_state[i]
            st.rerun()

street_cols[8].markdown("<div class='house-box'>🏠<br><small>بيت 5</small></div>", unsafe_allow_html=True)

st.divider()
report_placeholder = st.empty()

# --- 5. حلقة التحديث المستمر (للبيانات فقط) ---
THEFT_VALS = {1: 4.150, 2: 8.320, 3: 11.450, 4: 15.600}
LEGAL_BASE = 108.40  

while True:
    # حساب القيم بناءً على الحالة المخزونة
    active_indices = [i for i, v in st.session_state.theft_state.items() if v]
    total_theft_kw = sum([THEFT_VALS[i] for i in active_indices])
    current_legal = LEGAL_BASE + np.random.uniform(-0.1, 0.1)
    transformer_out = current_legal + total_theft_kw + (current_legal * 0.02)
    loss_h = int(total_theft_kw * 50)

    # تحديث المقاييس العلوية بدون "رمشة"
    with metrics_placeholder.container():
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("قدرة المحولة", f"{transformer_out:.2f} kW")
        m2.metric("القدرة المسروقة", f"{total_theft_kw:.2f} kW", delta=f"{len(active_indices)} تجاوز" if active_indices else None, delta_color="inverse")
        m3.metric("سحب البيوت", f"{current_legal:.2f} kW")
        m4.metric("خسارة الساعة", f"{loss_h:,} IQD")

    # تحديث سجل البلاغات والتنبيهات
    with report_placeholder.container():
        c_left, c_right = st.columns([1, 1])
        with c_left:
            st.write(f"**حالة الهدر المالي اللحظي:** :red[{loss_h:,} دينار/ساعة]")
            with st.expander("📂 سجل البلاغات الأخيرة"):
                for m in st.session_state.msg_history[:3]: st.write(f"🔹 {m}")
        
        with c_right:
            if active_indices:
                if len(active_indices) != st.session_state.last_count:
                    t_str = datetime.now().strftime("%H:%M:%S")
                    
                    # بناء رسالة التليجرام
                    msg = f"🚨 *تنبيه تجاوز (v17.5)*\n"
                    msg += f"المواقع: {', '.join([POLE_INFO[x]['desc'] for x in active_indices])}\n"
                    msg += f"القدرة: {total_theft_kw:.2f} kW\n"
                    
                    # رابط جوجل ماب
                    lat, lon = POLE_INFO[active_indices[0]]['lat'], POLE_INFO[active_indices[0]]['lon']
                    msg += f"📍 [فتح الموقع على الخريطة](https://www.google.com/maps?q={lat},{lon})\n"
                    msg += f"🕒 الوقت: {t_str}"
                    
                    if send_telegram_msg(msg):
                        st.session_state.msg_history.insert(0, f"[{t_str}] تم التبليغ عن {len(active_indices)} نقاط")
                        st.toast("📱 تم إرسال الإحداثيات للموبايل")
                    st.session_state.last_count = len(active_indices)
            else:
                st.session_state.last_count = 0
                st.success("🛡️ النظام: الشبكة مستقرة ولا يوجد تجاوز.")

    time.sleep(1)
