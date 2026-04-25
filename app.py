import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime

# --- 1. إعدادات الهوية البصرية (Professional White Theme) ---
st.set_page_config(page_title="Al-Anbar Smart Grid v11", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #212529; }
    .main-header { text-align: center; color: #1e3a8a; font-weight: bold; margin-bottom: 20px; }
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
    .stMetric { background: #f1f3f5; padding: 10px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة البيانات والحالة (Session State) ---
# تباين واقعي لأحمال التجاوز (kW) بناءً على طبيعة المنطقة
THEFT_VALUES = {1: 3.850, 2: 7.420, 3: 10.150, 4: 14.300}

for i in range(1, 5):
    if f'pole_{i}_theft' not in st.session_state:
        st.session_state[f'pole_{i}_theft'] = False
if 'msg_history' not in st.session_state: st.session_state.msg_history = []

# --- 3. المحرك الهندسي والحسابات ---
BASE_LEGAL_LOAD = 108.400 # القدرة الشرعية المسجلة للبيوت (kW)
active_thefts = [i for i in range(1, 5) if st.session_state[f'pole_{i}_theft']]
total_theft_power = sum([THEFT_VALUES[i] for i in active_thefts])

# إجمالي قدرة المحولة = القدرة الشرعية + التجاوز + فاقد فني (2.5%)
transformer_power = BASE_LEGAL_LOAD + total_theft_power + (BASE_LEGAL_LOAD * 0.025)

# الحسابات المالية (50 دينار لكل كيلو واط ساعة)
hourly_loss = int(total_theft_power * 50)
monthly_loss = hourly_loss * 24 * 30

# --- 4. واجهة العرض الرئيسية ---
st.markdown("<h1 class='main-header'>⚡ نظام الرصد الآلي للشبكة الذكية - محافظة الأنبار</h1>", unsafe_allow_html=True)
st.markdown("<center>مشروع المراقبة اللحظية وكشف الهدر المالي | جامعة الأنبار - كلية الهندسة</center>", unsafe_allow_html=True)
st.divider()

# داشبورد المقاييس (Power Balance)
st.subheader("📋 موازنة القدرة اللحظية (KCL Balance)")
m1, m2, m3, m4 = st.columns(4)
m1.metric("قدرة المحولة (P_source)", f"{round(transformer_power, 2)} kW")
m2.metric("مجموع البيوت (P_legal)", f"{BASE_LEGAL_LOAD} kW")
m3.metric("القدرة المسروقة", f"{round(total_theft_power, 2)} kW", delta=f"{len(active_thefts)} مواقع", delta_color="inverse")
m4.metric("الخسارة المالية/ساعة", f"{hourly_loss:,} IQD")

st.divider()

# --- 5. خارطة الشارع والتحكم (Visual Map) ---
st.subheader("📍 الخارطة التفاعلية وتحديد المواقع")
st.write("استخدم الأزرار أسفل الأعمدة لمحاكاة ربط أحمال غير قانونية في مناطق محددة.")

street_cols = st.columns([1.2, 0.5, 1, 0.5, 1, 0.5, 1, 0.5, 1])

# 1. المحولة
with street_cols[0]:
    st.markdown("<div class='node-box'>🏬<br><b>المحولة 01</b><br><small>الرمادي - المستودع</small></div>", unsafe_allow_html=True)

# 2. توليد الأعمدة والأسلاك والبيوت
for i in range(1, 5):
    # تمثيل السلك (Wire)
    with street_cols[2*i - 1]:
        is_th = st.session_state[f'pole_{i}_theft']
        st.markdown(f"<div class='wire-line {'wire-alert' if is_th else ''}'></div>", unsafe_allow_html=True)
    
    # تمثيل العقدة (Pole)
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
        # أزرار التحكم المختصرة
        btn_label = "إيقاف 🟢" if is_th else "حقن 🔴"
        if st.button(btn_label, key=f"btn_{i}"):
            st.session_state[f'pole_{i}_theft'] = not st.session_state[f'pole_{i}_theft']
            st.rerun()

st.divider()

# --- 6. نظام الأتمتة (الإرسال التلقائي بعد 3 ثواني) ---
st.subheader("🛡️ نظام الاستجابة والتبليغ التلقائي")
col_fin, col_auto = st.columns([1, 1])

with col_fin:
    st.markdown("### 💰 التقرير المالي للهدر")
    st.write(f"الخسارة الشهرية المتوقعة: **{monthly_loss:,} دينار عراقي**")
    st.progress(total_theft_power/60 if total_theft_power < 60 else 1.0, text=f"نسبة التجاوز من قدرة المحولة: {int((total_theft_power/transformer_power)*100)}%")

with col_auto:
    if len(active_thefts) > 0:
        # محاكاة ذكية للتأخير الزمني (3 ثواني)
        with st.status("🔍 جاري تحليل التجاوز المكتشف...", expanded=True) as status:
            st.write("تحليل فرق القدرة بين المحولة والعدادات...")
            time.sleep(1.0)
            st.write(f"تحديد المواقع: {', '.join([f'عامود {i}' for i in active_thefts])}")
            time.sleep(1.0)
            st.write("توليد تقرير البلاغ النهائي...")
            time.sleep(1.0)
            status.update(label="✅ تم إرسال البلاغ للمهندس المقيم!", state="complete", expanded=False)
        
        # إضافة البلاغ للسجل التاريخي
        t_now = datetime.now().strftime("%H:%M:%S")
        loc_str = ", ".join([f"بين بيت {i} و {i+1}" for i in active_thefts])
        report = f"[{t_now}] تنبيه: سرقة بقيمة {total_theft_power}kW في المواقع: ({loc_str})"
        
        if not st.session_state.msg_history or report.split(']')[1] != st.session_state.msg_history[0].split(']')[1]:
            st.session_state.msg_history.insert(0, report)
            st.toast(f"🚨 بلاغ عاجل للمهندس المقيم!", icon="📧")
    else:
        st.success("🛡️ نظام المراقبة: الشبكة سليمة ولا توجد تجاوزات حالياً.")

# سجل الرسائل الصادرة
with st.expander("📂 سجل البلاغات الصادرة (Outgoing Alerts)"):
    if st.session_state.msg_history:
        for msg in st.session_state.msg_history[:5]:
            st.write(f"🔹 {msg}")
    else:
        st.write("السجل فارغ.")

st.divider()
st.markdown("<center>إعداد الطالب: محمد نبيل - جامعة الأنبار - قسم الكهرباء | 2026</center>", unsafe_allow_html=True)
