import streamlit as st
import pandas as pd
import numpy as np
import time
import requests
from datetime import datetime

# --- 1. إعدادات التلغرام (شغالة تمام) ---
TOKEN = "8732709590:AAG8kxcfijO6ZpjmIjk2Rj_JFxB5gNMarZs"
ID = "5625855161"

POLES = {
    1: {"desc": "بين بيت 1 و 2", "lat": 33.4245, "lon": 43.2678},
    2: {"desc": "بين بيت 2 و 3", "lat": 33.4255, "lon": 43.2688},
    3: {"desc": "بين بيت 3 و 4", "lat": 33.4265, "lon": 43.2698},
    4: {"desc": "بين بيت 4 و 5", "lat": 33.4275, "lon": 43.2708}
}

def notify_me(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
    except:
        pass

# --- 2. ستايل الواجهة (مرتب وبسيط) ---
st.set_page_config(page_title="Al-Anbar Smart Grid", layout="wide")

st.markdown("""
    <style>
    .metric-card { background: #f9f9f9; border-left: 5px solid #1e3a8a; padding: 10px; border-radius: 5px; }
    .theft-card { background: #fff5f5; border: 2px solid #ff4b4b; border-radius: 10px; padding: 10px; text-align: center; }
    .safe-card { background: #f0fdf4; border: 1px solid #22c55e; border-radius: 10px; padding: 10px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. تهيئة البيانات (Session State) ---
if 'theft' not in st.session_state: st.session_state.theft = {1: False, 2: False, 3: False, 4: False}
if 'last_count' not in st.session_state: st.session_state.last_count = 0

# العنوان
st.title("⚡ Automated Grid Monitoring & Analysis")
st.write("**إعداد: محمد نبيل بردان & مشتاق طالب جلال**")

# تقسيم التبويبات
tab1, tab2 = st.tabs(["📊 المراقبة والتحكم", "📄 التقرير الفني"])

with tab2:
    st.markdown("""
    ### Project Technical Report (English)
    **1. Introduction:** This project detects power theft in Al-Anbar grid using IoT. 
    **2. Methodology:** We use Energy Balance ($P_{total} - \sum P_{legal}$) to find the theft. 
    **3. Protocols:** HTTP/HTTPS, REST API, and Google Maps for GPS tracking.
    **4. Conclusion:** Our system reduces the $12B annual loss in Iraq by identifying theft points in real-time.
    """)

with tab1:
    # --- أزرار التحكم (خارج اللوب عشان تكون مستقرة) ---
    st.subheader("🕹️ لوحة حقن التجاوزات")
    ctrl_cols = st.columns(4)
    for i in range(1, 5):
        with ctrl_cols[i-1]:
            state = st.session_state.theft[i]
            if st.button("إيقاف" if state else f"حقن عمود {i}", key=f"btn_{i}"):
                st.session_state.theft[i] = not st.session_state.theft[i]
                st.rerun()

    st.divider()
    
    # --- حاويات العرض اللحظي ---
    stat_box = st.empty()
    map_box = st.empty()

    # قيم الحسابات
    POWER_VALS = {1: 4.15, 2: 8.32, 3: 11.45, 4: 15.60}
    BASE = 108.40

    # حلقة التحديث (فقط للنتائج)
    while True:
        active = [k for k, v in st.session_state.theft.items() if v]
        total_stolen = sum([POWER_VALS[i] for i in active])
        current_legal = BASE + np.random.uniform(-0.1, 0.1)
        total_p = current_legal + total_stolen + (current_legal * 0.02)
        loss_money = int(total_stolen * 50)

        # تحديث الأرقام
        with stat_box.container():
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("قدرة المحولة", f"{total_p:.2f} kW")
            m2.metric("القدرة المسروقة", f"{total_stolen:.2f} kW", delta=f"{len(active)} تجاوز")
            m3.metric("سحب البيوت", f"{current_legal:.2f} kW")
            m4.metric("الخسارة/ساعة", f"{loss_money:,} IQD")

        # تحديث شكل العواميد
        with map_box.container():
            st.write("### حالة الشارع (Real-time View)")
            cols = st.columns([1, 0.6, 1, 0.6, 1, 0.6, 1, 0.6, 1])
            cols[0].info("🏢\nالمحولة")
            for i in range(1, 5):
                cols[2*i-1].success(f"🏠\nبيت {i}")
                with cols[2*i]:
                    if st.session_state.theft[i]:
                        st.markdown(f"<div class='theft-card'>🗼<br>{POLES[i]['desc']}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='safe-card'>🗼<br>{POLES[i]['desc']}</div>", unsafe_allow_html=True)
            cols[8].success("🏠\nبيت 5")

        # التبليغ (فقط عند حدوث تغيير)
        if len(active) != st.session_state.last_count:
            if active:
                t = datetime.now().strftime("%H:%M:%S")
                msg = f"🚨 *تجاوز جديد في الشبكة*\nالموقع: {', '.join([POLES[x]['desc'] for x in active])}\nالحمل: {total_stolen:.2f} kW\n📍 [خريطة جوجل](http://maps.google.com/maps?q={POLES[active[0]]['lat']},{POLES[active[0]]['lon']})\n🕒 {t}"
                notify_me(msg)
                st.toast("تم إرسال إشعار للموبايل!")
            st.session_state.last_count = len(active)

        time.sleep(1)
        
