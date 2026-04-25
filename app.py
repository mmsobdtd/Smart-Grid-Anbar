import streamlit as st
import pandas as pd
import numpy as np
import time
import requests
from datetime import datetime

# --- 1. إعدادات الربط والتبليغ ---
BOT_TOKEN = "8732709590:AAG8kxcfijO6ZpjmIjk2Rj_JFxB5gNMarZs"
CHAT_ID = "5625855161"

# إحداثيات افتراضية دقيقة (منطقة جامعة الأنبار - الرمادي)
POLE_LOCATIONS = {
    1: {"lat": 33.4245, "lon": 43.2678, "desc": "قرب البوابة الرئيسية"},
    2: {"lat": 33.4255, "lon": 43.2688, "desc": "خلف عمادة كلية الهندسة"},
    3: {"lat": 33.4265, "lon": 43.2698, "desc": "قرب المختبرات المركزية"},
    4: {"lat": 33.4275, "lon": 43.2708, "desc": "نهاية ممر الأقسام العلمية"}
}

def send_telegram_msg(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload, timeout=5)
        return True
    except:
        return False

# --- 2. التنسيق البصري ---
st.set_page_config(page_title="Al-Anbar Smart Grid - GPS Edition", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .main-header { text-align: center; color: #1e3a8a; font-weight: bold; margin-bottom: 5px; }
    .sub-header { text-align: center; color: #444; font-size: 18px; margin-bottom: 15px; }
    .node-box {
        background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 12px;
        padding: 10px; text-align: center;
    }
    .theft-active { border: 2px solid #e03131 !important; background-color: #fff5f5 !important; }
    .wire-line { height: 5px; background: #dee2e6; margin-top: 45px; }
    .wire-alert { background: #e03131 !important; box-shadow: 0 0 8px #e03131; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. تهيئة البيانات ---
THEFT_MAP = {1: 4.150, 2: 8.320, 3: 11.450, 4: 15.600}
LEGAL_LOAD_BASE = 108.40  
if 'msg_history' not in st.session_state: st.session_state.msg_history = []
if 'last_alert_count' not in st.session_state: st.session_state.last_alert_count = 0

# --- 4. واجهة العرض الرئيسية ---
st.markdown("<h1 class='main-header'>⚡ نظام الرصد والتحليل الآلي (نسخة التتبع المكاني)</h1>", unsafe_allow_html=True)
st.markdown("<div class='sub-header'>إعداد الطلبة: محمد نبيل بردان | مشتاق طالب جلال</div>", unsafe_allow_html=True)
st.divider()

# لوحة السيطرة
st.subheader("🕹️ لوحة حقن التجاوزات")
c1, c2, c3, c4 = st.columns(4)
with c1: t1 = st.toggle("تجاوز عامود 1", key="t1")
with c2: t2 = st.toggle("تجاوز عامود 2", key="t2")
with c3: t3 = st.toggle("تجاوز عامود 3", key="t3")
with c4: t4 = st.toggle("تجاوز عامود 4", key="t4")

st.divider()

metrics_area = st.empty()
map_area = st.empty()
report_area = st.empty()

# --- 5. حلقة التحديث المستمر ---
while True:
    active_indices = [i for i, t in enumerate([t1, t2, t3, t4], 1) if t]
    total_theft_kw = sum([THEFT_MAP[i] for i in active_indices])
    current_legal = LEGAL_LOAD_BASE + np.random.uniform(-0.1, 0.1)
    transformer_out = current_legal + total_theft_kw + (current_legal * 0.02)
    
    # حساب نسبة الهدر
    loss_percent = (total_theft_kw / transformer_out * 100) if transformer_out > 0 else 0
    loss_h = int(total_theft_kw * 50)

    with metrics_area.container():
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("قدرة المحولة", f"{transformer_out:.2f} kW")
        m2.metric("القدرة المسروقة", f"{total_theft_kw:.2f} kW", delta=f"{loss_percent:.1f}% خسارة", delta_color="inverse")
        m3.metric("سحب البيوت", f"{current_legal:.2f} kW")
        m4.metric("خسارة الساعة", f"{loss_h:,} IQD")
        st.divider()

    with map_area.container():
        st.subheader("📍 الخارطة التفاعلية ونقاط التوزيع")
        map_cols = st.columns([1.2, 0.5, 1, 0.5, 1, 0.5, 1, 0.5, 1])
        map_cols[0].markdown("<div class='node-box'>🏢<br><b>المحولة</b></div>", unsafe_allow_html=True)
        for i in range(1, 5):
            is_active = i in active_indices
            map_cols[2*i-1].markdown(f"<div class='wire-line {'wire-alert' if is_active else ''}'></div>", unsafe_allow_html=True)
            style = "node-box theft-active" if is_active else "node-box"
            map_cols[2*i].markdown(f"<div class='{style}'>🗼<br><b>عـامود {i}</b><br><small>{POLE_LOCATIONS[i]['desc']}</small></div>", unsafe_allow_html=True)
        st.divider()

    with report_area.container():
        c_l, c_r = st.columns([1, 1])
        with c_r:
            if active_indices:
                with st.status("🔍 تحليل الموقع الجغرافي وإرسال الإحداثيات...", expanded=False) as status:
                    time.sleep(1.5)
                    status.update(label="✅ تم إرسال تقرير GPS للمهندس مشتاق!", state="complete")
                
                t_str = datetime.now().strftime("%H:%M:%S")
                
                # بناء الرسالة المحسنة مع رابط الخريطة
                msg_body = f"🚨 *بلاغ طوارئ - سرقة طاقة*\n\n"
                msg_body += f"📍 *المواقع المصابة:* {', '.join([f'عامود {i}' for i in active_indices])}\n"
                msg_body += f"📊 *قدرة التجاوز:* {total_theft_kw:.2f} kW\n"
                msg_body += f"📉 *نسبة الهدر:* {loss_percent:.1f}%\n"
                msg_body += f"💰 *الخسارة:* {loss_h:,} دينار/ساعة\n\n"
                msg_body += f"🗺️ *روابط المواقع على الخريطة:*\n"
                
                for idx in active_indices:
                    lat, lon = POLE_LOCATIONS[idx]['lat'], POLE_LOCATIONS[idx]['lon']
                    google_maps_link = f"https://www.google.com/maps?q={lat},{lon}"
                    msg_body += f"• [موقع عامود {idx}]({google_maps_link})\n"
                
                msg_body += f"\n🕒 *الوقت:* {t_str}"

                if len(active_indices) != st.session_state.last_alert_count:
                    if send_telegram_msg(msg_body):
                        st.session_state.msg_history.insert(0, f"[{t_str}] تم إرسال إحداثيات GPS لـ {len(active_indices)} مواقع")
                        st.toast("📍 تم إرسال الخارطة للموبايل")
                    st.session_state.last_alert_count = len(active_indices)
            else:
                st.session_state.last_alert_count = 0
                st.success("🛡️ النظام: الشبكة مستقرة ومؤمنة بالكامل.")
        
        with c_l:
            with st.expander("📂 سجل الرسائل الجغرافية"):
                for m in st.session_state.msg_history[:5]: st.write(f"🔹 {m}")

    time.sleep(1)
    
