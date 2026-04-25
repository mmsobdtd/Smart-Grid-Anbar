import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime

# --- 1. إعدادات الهوية البصرية ---
st.set_page_config(page_title="Smart Grid Al-Anbar - Live", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .main-header { text-align: center; color: #1e3a8a; font-weight: bold; margin-bottom: 5px; }
    .sub-header { text-align: center; color: #495057; font-size: 18px; margin-bottom: 15px; }
    .node-box {
        background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 12px;
        padding: 10px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .theft-active { border: 2px solid #e03131 !important; background-color: #fff5f5 !important; }
    .wire-line { height: 5px; background: #dee2e6; margin-top: 45px; }
    .wire-alert { background: #e03131 !important; box-shadow: 0 0 8px #e03131; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. تهيئة الحالة ---
THEFT_VALUES = {1: 4.15, 2: 8.32, 3: 11.45, 4: 15.60}
if 'msg_history' not in st.session_state: st.session_state.msg_history = []

# --- 3. واجهة المستخدم الثابتة ---
st.markdown("<h1 class='main-header'>⚡ نظام الرصد الآلي للشبكة الذكية - محافظة الأنبار</h1>", unsafe_allow_html=True)
st.markdown("<div class='sub-header'>إعداد الطلبة: محمد نبيل بردان | مشتاق طالب جلال</div>", unsafe_allow_html=True)
st.markdown("<center>جامعة الأنبار - كلية الهندسة - قسم الكهرباء</center>", unsafe_allow_html=True)

st.divider()

# القائمة الجانبية للتحكم
with st.sidebar:
    st.header("🕹️ لوحة التحكم")
    st.write("فعل التجاوزات لمراقبة التحديث اللحظي:")
    t1 = st.toggle("تجاوز عامود 1", key="t1")
    t2 = st.toggle("تجاوز عامود 2", key="t2")
    t3 = st.toggle("تجاوز عامود 3", key="t3")
    t4 = st.toggle("تجاوز عامود 4", key="t4")
    
    st.divider()
    if st.button("🗑️ تصفير السجل"):
        st.session_state.msg_history = []

# إنشاء حاويات فارغة للتحديث اللحظي (Placeholder)
metrics_placeholder = st.empty()
map_placeholder = st.empty()
report_placeholder = st.empty()

# --- 4. حلقة التحديث اللحظي (بدون وميض) ---
while True:
    # حسابات المحرك الهندسي
    active_thefts = []
    if t1: active_thefts.append(1)
    if t2: active_thefts.append(2)
    if t3: active_thefts.append(3)
    if t4: active_thefts.append(4)
    
    total_theft_power = sum([THEFT_VALUES[i] for i in active_thefts])
    base_legal = 108.4 + np.random.uniform(-0.5, 0.5) # محاكاة تغير أحمال بسيط
    transformer_power = base_legal + total_theft_power + (base_legal * 0.02)
    
    loss_hour = int(total_theft_power * 50)
    loss_day = loss_hour * 24
    loss_month = loss_day * 30

    # تحديث المقاييس (Metrics)
    with metrics_placeholder.container():
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("قدرة المحولة", f"{round(transformer_power, 2)} kW")
        m2.metric("القدرة المسروقة", f"{round(total_theft_power, 2)} kW", delta=f"{len(active_thefts)} مواقع", delta_color="inverse")
        m3.metric("خسارة اليوم (IQD)", f"{loss_day:,}")
        m4.metric("خسارة الشهر (IQD)", f"{loss_month:,}")
        st.divider()

    # تحديث الخريطة (Map)
    with map_placeholder.container():
        st.subheader("📍 الخارطة التفاعلية (تحديث لحظي)")
        cols = st.columns([1.2, 0.5, 1, 0.5, 1, 0.5, 1, 0.5, 1])
        
        # المحولة
        cols[0].markdown("<div class='node-box'>🏢<br><b>المحولة 01</b></div>", unsafe_allow_html=True)
        
        # الأعمدة والأسلاك
        for i in range(1, 5):
            is_th = i in active_thefts
            # سلك
            cols[2*i-1].markdown(f"<div class='wire-line {'wire-alert' if is_th else ''}'></div>", unsafe_allow_html=True)
            # عامود
            style = "node-box theft-active" if is_th else "node-box"
            cols[2*i].markdown(f"<div class='{style}'>🗼<br><b>عـامود {i}</b><br><small>بين {i} و {i+1}</small></div>", unsafe_allow_html=True)
        st.divider()

    # تحديث البلاغات والخسائر
    with report_placeholder.container():
        c_left, c_right = st.columns([1, 1])
        with c_left:
            st.markdown(f"""
            <div style='background:#e7f5ff; padding:15px; border-radius:10px; border-right:5px solid #228be6;'>
                <b>خسارة الساعة الحالية:</b><br>
                <span style='font-size:24px; color:#e03131;'>{loss_hour:,} دينار / ساعة</span>
            </div>
            """, unsafe_allow_html=True)
        
        with c_right:
            if len(active_thefts) > 0:
                st.error(f"🚨 تنبيه: تم رصد تجاوز في {len(active_thefts)} مواقع. جاري إرسال الإحداثيات للمهندس...")
                t_now = datetime.now().strftime("%H:%M:%S")
                report = f"[{t_now}] سرقة في {[f'ع{i}' for i in active_thefts]} | {loss_hour} IQD/h"
                if not st.session_state.msg_history or report.split(']')[1] != st.session_state.msg_history[0].split(']')[1]:
                    st.session_state.msg_history.insert(0, report)
            else:
                st.success("🛡️ الشبكة آمنة: لا توجد تجاوزات حالياً.")
        
        with st.expander("📂 سجل الرسائل الصادرة للمهندس"):
            for m in st.session_state.msg_history[:5]: st.write(f"🔹 {m}")

    # سرعة التحديث (ثانية واحدة لضمان السلاسة)
    time.sleep(1)
    
