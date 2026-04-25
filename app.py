import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime

# --- 1. إعدادات الهوية البصرية (Professional White Theme) ---
st.set_page_config(page_title="Al-Anbar Smart Grid - Project", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #212529; }
    .main-header { text-align: center; color: #1e3a8a; font-weight: bold; margin-bottom: 5px; }
    .sub-header { text-align: center; color: #495057; font-size: 18px; margin-bottom: 20px; }
    .node-box {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 15px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        transition: 0.3s;
    }
    .theft-active {
        border: 2px solid #e03131 !important;
        background-color: #fff5f5 !important;
        box-shadow: 0 0 10px rgba(224, 49, 49, 0.2);
    }
    .wire-line {
        height: 5px;
        background: #dee2e6;
        margin-top: 50px;
        position: relative;
    }
    .wire-alert { background: #e03131 !important; box-shadow: 0 0 8px #e03131; }
    .financial-card {
        background: #e7f5ff;
        padding: 15px;
        border-radius: 10px;
        border-right: 5px solid #228be6;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة البيانات والحالة (Session State) ---
THEFT_VALUES = {1: 4.150, 2: 8.320, 3: 11.450, 4: 15.600}

for i in range(1, 5):
    if f'pole_{i}_theft' not in st.session_state:
        st.session_state[f'pole_{i}_theft'] = False
if 'msg_history' not in st.session_state: st.session_state.msg_history = []

# --- 3. المحرك الهندسي والمالي ---
BASE_LEGAL_LOAD = 108.400 # kW
active_thefts = [i for i in range(1, 5) if st.session_state[f'pole_{i}_theft']]
total_theft_power = sum([THEFT_VALUES[i] for i in active_thefts])

# إجمالي قدرة المحولة
transformer_power = BASE_LEGAL_LOAD + total_theft_power + (BASE_LEGAL_LOAD * 0.025)

# الحسابات المالية (50 دينار لكل كيلو واط ساعة)
rate = 50
loss_hour = int(total_theft_power * rate)
loss_day = loss_hour * 24
loss_month = loss_day * 30

# --- 4. واجهة العرض الرئيسية ---
st.markdown("<h1 class='main-header'>⚡ نظام الرصد الآلي للشبكة الذكية - محافظة الأنبار</h1>", unsafe_allow_html=True)
st.markdown("<div class='sub-header'>إعداد الطلبة: محمد نبيل بردان | مشتاق طالب جلال</div>", unsafe_allow_html=True)
st.markdown("<center>جامعة الأنبار - كلية الهندسة - قسم الكهرباء</center>", unsafe_allow_html=True)
st.divider()

# داشبورد المقاييس (Power & Money)
st.subheader("📊 لوحة القياس والتحليل المالي اللحظي")
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
col_m1.metric("قدرة المحولة الكلية", f"{round(transformer_power, 2)} kW")
col_m2.metric("القدرة المسروقة", f"{round(total_theft_power, 2)} kW", delta=f"{len(active_thefts)} مواقع", delta_color="inverse")
col_m3.metric("خسارة اليوم (IQD)", f"{loss_day:,}")
col_m4.metric("خسارة الشهر (IQD)", f"{loss_month:,}")

st.divider()

# --- 5. خارطة الشارع والتحكم (Visual Map) ---
st.subheader("📍 الخارطة التفاعلية وتحديد مواقع التجاوز")
street_cols = st.columns([1.2, 0.5, 1, 0.5, 1, 0.5, 1, 0.5, 1])

# المحولة
with street_cols[0]:
    st.markdown("<div class='node-box'>🏬<br><b>المحولة 01</b><br><small>منطقة المستودع</small></div>", unsafe_allow_html=True)

# الأعمدة والأسلاك
for i in range(1, 5):
    with street_cols[2*i - 1]:
        is_th = st.session_state[f'pole_{i}_theft']
        st.markdown(f"<div class='wire-line {'wire-alert' if is_th else ''}'></div>", unsafe_allow_html=True)
    
    with street_cols[2*i]:
        is_th = st.session_state[f'pole_{i}_theft']
        style = "node-box theft-active" if is_th else "node-box"
        st.markdown(f"""
            <div class='{style}'>
                <div style='font-size: 30px;'>🗼</div>
                <b>عـامود {i}</b><br>
                <small>بين بيت {i} و {i+1}</small>
            </div>
            """, unsafe_allow_html=True)
        # أزرار التحكم
        btn_label = "إيقاف 🟢" if is_th else "حقن 🔴"
        if st.button(btn_label, key=f"btn_{i}"):
            st.session_state[f'pole_{i}_theft'] = not st.session_state[f'pole_{i}_theft']
            st.rerun()

st.divider()

# --- 6. نظام الأتمتة والتقارير ---
st.subheader("🛡️ نظام الاستجابة الذكي والتبليغ")
col_left, col_right = st.columns([1, 1])

with col_left:
    st.markdown("### 💰 تفصيل الهدر المالي")
    st.markdown(f"""
    <div class='financial-card'>
        <b>التكلفة المفقودة حالياً:</b><br>
        <span style='font-size: 24px; color: #e03131;'>{loss_hour:,} دينار / ساعة</span><br>
        <small>بناءً على تيار تجاوز كلي قدره {round(total_theft_power, 2)} kW</small>
    </div>
    """, unsafe_allow_html=True)

with col_right:
    if len(active_thefts) > 0:
        with st.status("🔍 جاري معالجة البيانات...", expanded=True) as status:
            st.write("تحليل فرق القدرة...")
            time.sleep(1.0)
            st.write("تحديد الموقع الجغرافي...")
            time.sleep(1.0)
            st.write("إرسال البلاغ للمهندس...")
            time.sleep(1.0)
            status.update(label="✅ تم التبليغ عن التجاوز بنجاح!", state="complete", expanded=False)
        
        # تسجيل البلاغ
        t_now = datetime.now().strftime("%H:%M:%S")
        loc_str = ", ".join([f"عامود {i}" for i in active_thefts])
        report = f"[{t_now}] بلاغ: سرقة في {loc_str} | الخسارة: {loss_hour} IQD/h"
        
        if not st.session_state.msg_history or report.split(']')[1] != st.session_state.msg_history[0].split(']')[1]:
            st.session_state.msg_history.insert(0, report)
            st.toast(f"🚨 تم تنبيه المهندس المقيم!", icon="📧")
    else:
        st.success("🛡️ الشبكة آمنة: لا توجد تجاوزات مكتشفة في الوقت الحالي.")

# سجل البلاغات
with st.expander("📂 سجل الرسائل الصادرة"):
    if st.session_state.msg_history:
        for msg in st.session_state.msg_history[:5]:
            st.write(f"🔹 {msg}")
    else:
        st.write("السجل فارغ.")

st.divider()
st.markdown("<center>نظام المراقبة الذكي - إعداد الطلبة: محمد نبيل بردان & مشتاق طالب جلال | 2026</center>", unsafe_allow_html=True)
