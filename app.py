import streamlit as st
import pandas as pd
import numpy as np
import time
import requests
from datetime import datetime

# --- 1. إعدادات الربط الحقيقي (Data Integration) ---
BOT_TOKEN = "8732709590:AAG8kxcfijO6ZpjmIjk2Rj_JFxB5gNMarZs"
CHAT_ID = "5625855161"

def send_telegram_msg(text):
    """دالة الإرسال الفوري لنظام التنبيه الجوال"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload, timeout=5)
        return True
    except:
        return False

# --- 2. التنسيق البصري (Professional Engineering Layout) ---
st.set_page_config(page_title="Al-Anbar Smart Grid SCADA", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #212529; }
    .main-header { text-align: center; color: #1e3a8a; font-weight: bold; margin-bottom: 5px; }
    .sub-header { text-align: center; color: #444; font-size: 19px; margin-bottom: 20px; }
    .node-box {
        background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 12px;
        padding: 10px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .theft-active { border: 2px solid #e03131 !important; background-color: #fff5f5 !important; }
    .wire-line { height: 5px; background: #dee2e6; margin-top: 45px; position: relative; }
    .wire-alert { background: #e03131 !important; box-shadow: 0 0 8px #e03131; }
    .financial-card {
        background: #f1f3f5; padding: 15px; border-radius: 10px;
        border-right: 5px solid #228be6; text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. تهيئة البيانات الهندسية ---
THEFT_MAP = {1: 4.150, 2: 8.320, 3: 11.450, 4: 15.600}
LEGAL_LOAD_BASE = 108.40  
IQD_RATE = 50             

if 'msg_history' not in st.session_state: st.session_state.msg_history = []
if 'last_alert_count' not in st.session_state: st.session_state.last_alert_count = 0

# --- 4. واجهة العرض الرئيسية ---
st.markdown("<h1 class='main-header'>⚡ نظام الرصد الآلي للشبكة الذكية - محافظة الأنبار</h1>", unsafe_allow_html=True)
st.markdown("<div class='sub-header'>إعداد الطلبة: محمد نبيل بردان | مشتاق طالب جلال</div>", unsafe_allow_html=True)
st.markdown("<center>جامعة الأنبار - كلية الهندسة - قسم الكهرباء</center>", unsafe_allow_html=True)
st.divider()

# القائمة الجانبية
with st.sidebar:
    st.header("🎮 وحدة حقن التجاوز")
    st.write("فعل التجاوز لاختبار الإرسال اللحظي:")
    t1 = st.toggle("تجاوز عامود 1")
    t2 = st.toggle("تجاوز عامود 2")
    t3 = st.toggle("تجاوز عامود 3")
    t4 = st.toggle("تجاوز عامود 4")
    st.divider()
    if st.button("🗑️ مسح سجل البلاغات"):
        st.session_state.msg_history = []

# حاويات التحديث اللحظي
metrics_area = st.empty()
map_area = st.empty()
report_area = st.empty()

# --- 5. حلقة التشغيل والتحديث المستمر ---
while True:
    active_indices = [i for i, t in enumerate([t1, t2, t3, t4], 1) if t]
    
    total_theft_kw = sum([THEFT_MAP[i] for i in active_indices])
    current_legal = LEGAL_LOAD_BASE + np.random.uniform(-0.1, 0.1)
    transformer_out = current_legal + total_theft_kw + (current_legal * 0.02)
    
    loss_h = int(total_theft_kw * IQD_RATE)
    loss_d = loss_h * 24
    loss_m = loss_d * 30

    with metrics_area.container():
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("قدرة المحولة الكلية", f"{transformer_out:.2f} kW")
        m2.metric("القدرة المسروقة", f"{total_theft_kw:.2f} kW", delta=f"{len(active_indices)} مواقع" if active_indices else None, delta_color="inverse")
        m3.metric("خسارة اليوم (IQD)", f"{loss_d:,}")
        m4.metric("خسارة الشهر (IQD)", f"{loss_m:,}")
        st.divider()

    with map_area.container():
        st.subheader("📍 خارطة المسار الكهربائي وتحديد المواقع")
        map_cols = st.columns([1.2, 0.5, 1, 0.5, 1, 0.5, 1, 0.5, 1])
        map_cols[0].markdown("<div class='node-box'>🏢<br><b>المحولة</b></div>", unsafe_allow_html=True)
        for i in range(1, 5):
            is_active = i in active_indices
            map_cols[2*i-1].markdown(f"<div class='wire-line {'wire-alert' if is_active else ''}'></div>", unsafe_allow_html=True)
            style = "node-box theft-active" if is_active else "node-box"
            map_cols[2*i].markdown(f"<div class='{style}'>🗼<br><b>عـامود {i}</b><br><small>بين {i} و {i+1}</small></div>", unsafe_allow_html=True)
        st.divider()

    with report_area.container():
        c_left, c_right = st.columns([1, 1])
        c_left.markdown(f"<div class='financial-card'><b>التكلفة المفقودة حالياً:</b><br><span style='font-size: 26px; color: #e03131; font-weight: bold;'>{loss_h:,} دينار / ساعة</span></div>", unsafe_allow_html=True)
        
        with c_right:
            if active_indices:
                with st.status("🔍 جاري تحليل التجاوز والتبليغ...", expanded=False) as status:
                    time.sleep(1.5)
                    st.write("تم رصد فرق في تدفق القدرة..")
                    time.sleep(1.5)
                    status.update(label="✅ تم الإرسال لموبايل المهندس مشتاق!", state="complete")
                
                t_str = datetime.now().strftime("%H:%M:%S")
                loc_names = ", ".join([f"عامود {i}" for i in active_indices])
                
                # إعداد الرسالة الرسمية
                full_msg = f"🚨 *تنبيه أمني - شبكة الأنبار*\n\n" \
                           f"تم رصد تجاوز في: {loc_names}\n" \
                           f"القدرة المفقودة: {total_theft_kw:.2f} kW\n" \
                           f"الخسارة المالية: {loss_h} IQD/h\n" \
                           f"الوقت: {t_str}"
                
                # الإرسال الفعلي عند التغيير
                if len(active_indices) != st.session_state.last_alert_count:
                    if send_telegram_msg(full_msg):
                        st.session_state.msg_history.insert(0, f"[{t_str}] تم الإرسال: {loc_names}")
                        st.toast("📱 وصلت الرسالة لتليجرام!", icon="✅")
                    st.session_state.last_alert_count = len(active_indices)
            else:
                st.session_state.last_alert_count = 0
                st.success("🛡️ نظام المراقبة: الشبكة مستقرة وآمنة.")

        with st.expander("📂 سجل الرسائل الصادرة"):
            for m in st.session_state.msg_history[:5]: st.write(f"🔹 {m}")
    
    time.sleep(1)
