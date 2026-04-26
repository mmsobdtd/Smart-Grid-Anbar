import streamlit as st
import pandas as pd
import numpy as np
import time
import requests
from datetime import datetime

# --- 1. إعدادات الربط والتبليغ ---
BOT_TOKEN = "8732709590:AAG8kxcfijO6ZpjmIjk2Rj_JFxB5gNMarZs"
CHAT_ID = "5625855161"

LOCATIONS = {
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

# --- 2. التنسيق البصري (نفس الستايل القديم) ---
st.set_page_config(page_title="Al-Anbar Smart Grid - Final", layout="wide")

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
    .wire-line { height: 5px; background: #dee2e6; margin-top: 40px; }
    .wire-alert { background: #e03131 !important; box-shadow: 0 0 10px #e03131; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. إدارة الحالة (Session State) ---
if 'msg_history' not in st.session_state: st.session_state.msg_history = []
if 'last_alert_count' not in st.session_state: st.session_state.last_alert_count = 0
for i in range(1, 5):
    if f'inj_{i}' not in st.session_state: st.session_state[f'inj_{i}'] = False

# --- 4. واجهة العرض الرئيسية ---
st.markdown("<h1 class='main-header'>⚡ نظام الرصد والتبليغ الذكي (تتبع المنازل)</h1>", unsafe_allow_html=True)
st.markdown("<div class='sub-header'>إعداد الطلبة: محمد نبيل بردان | مشتاق طالب جلال</div>", unsafe_allow_html=True)
st.divider()

# حاويات التحديث
metrics_area = st.empty()
map_area = st.empty()
report_area = st.empty()

# --- 5. حلقة التحديث المنطقية ---
THEFT_MAP = {1: 4.150, 2: 8.320, 3: 11.450, 4: 15.600}
LEGAL_LOAD_BASE = 108.40  

# تبويب للتقرير (اختياري بالأسفل للحفاظ على الشكل القديم)
with st.expander("📄 عرض التقرير الفني للمشروع (Technical Report)"):
    st.write("""
    **GRADUATION PROJECT REPORT: SMART GRID MONITORING**
    **1. Introduction:** This project addresses power theft in Iraq, which causes $12B in annual losses.
    **2. Methodology:** Based on the Energy Balancing Algorithm and IoT networking.
    **3. Integration:** Real-time alerting via Telegram and Google Maps GPS tracking.
    """)

while True:
    # حساب البيانات
    active_indices = [i for i in range(1, 5) if st.session_state[f'inj_{i}']]
    total_theft_kw = sum([THEFT_MAP[i] for i in active_indices])
    current_legal = LEGAL_LOAD_BASE + np.random.uniform(-0.1, 0.1)
    transformer_out = current_legal + total_theft_kw + (current_legal * 0.02)
    loss_h = int(total_theft_kw * 50)
    loss_m = loss_h * 24 * 30

    # أ. تحديث المقاييس
    with metrics_area.container():
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("قدرة المحولة", f"{transformer_out:.2f} kW")
        m2.metric("القدرة المسروقة", f"{total_theft_kw:.2f} kW", delta=f"{len(active_indices)} نقاط" if active_indices else None, delta_color="inverse")
        m3.metric("مجموع سحب البيوت", f"{current_legal:.2f} kW")
        m4.metric("خسارة الشهر (IQD)", f"{loss_m:,}")
        st.divider()

    # ب. تحديث الخريطة التفاعلية (مع إصلاح تعليق الأزرار)
    with map_area.container():
        street_cols = st.columns([1, 0.8, 1, 0.8, 1, 0.8, 1, 0.8, 1])
        street_cols[0].markdown("<div class='node-box'>🏢<br><b>المحولة</b></div>", unsafe_allow_html=True)
        
        for i in range(1, 5):
            street_cols[2*i-1].markdown(f"<div class='house-box'>🏠<br><small>بيت {i}</small></div>", unsafe_allow_html=True)
            with street_cols[2*i]:
                is_on = st.session_state[f'inj_{i}']
                style = "node-box theft-active" if is_on else "node-box"
                st.markdown(f"<div class='{style}'>🗼<br><small>{LOCATIONS[i]['desc']}</small></div>", unsafe_allow_html=True)
                # الإصلاح: استخدام st.button مع rerun فوري لضمان الاستجابة
                if st.button("إيقاف" if is_on else "حقن", key=f"btn_{i}"):
                    st.session_state[f'inj_{i}'] = not st.session_state[f'inj_{i}']
                    st.rerun()
        street_cols[8].markdown("<div class='house-box'>🏠<br><small>بيت 5</small></div>", unsafe_allow_html=True)

    # ج. نظام الأتمتة والتبليغ
    with report_area.container():
        st.divider()
        c_l, c_r = st.columns([1, 1])
        with c_l:
            st.markdown(f"**تكلفة الهدر المالي:** <span style='color:red; font-size:20px; font-weight:bold;'>{loss_h:,} IQD/h</span>", unsafe_allow_html=True)
            with st.expander("📂 سجل البلاغات"):
                for m in st.session_state.msg_history[:3]: st.write(f"🔹 {m}")
        
        with c_r:
            if active_indices:
                if len(active_indices) != st.session_state.last_alert_count:
                    t_str = datetime.now().strftime("%H:%M:%S")
                    msg = f"🚨 *تنبيه من شبكة الأنبار*\n"
                    msg += f"📍 الموقع: {', '.join([LOCATIONS[idx]['desc'] for idx in active_indices])}\n"
                    msg += f"⚡ القدرة: {total_theft_kw:.2f} kW\n"
                    # تصحيح رابط الخريطة ليعمل بشكل حقيقي
                    lat_c = LOCATIONS[active_indices[0]]['lat']
                    lon_c = LOCATIONS[active_indices[0]]['lon']
                    msg += f"📍 [فتح الموقع على الخريطة](https://www.google.com/maps?q={lat_c},{lon_c})\n"
                    msg += f"🕒 الوقت: {t_str}"
                    
                    if send_telegram_msg(msg):
                        st.session_state.msg_history.insert(0, f"[{t_str}] تم التبليغ عن {len(active_indices)} نقاط")
                        st.toast("📱 تم إرسال الموقع للموبايل")
                    st.session_state.last_alert_count = len(active_indices)
            else:
                st.session_state.last_alert_count = 0
                st.success("🛡️ الشبكة مستقرة وآمنة.")

    time.sleep(1)
    
