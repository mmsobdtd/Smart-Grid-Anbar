import streamlit as st
import pandas as pd
import numpy as np

# --- 1. إعدادات الصفحة والتنسيق الأبيض الاحترافي ---
st.set_page_config(page_title="Al-Anbar Grid - Final Edition", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1a1a1a; }
    .node-box {
        background: #fdfdfd;
        border: 1px solid #dee2e6;
        border-radius: 15px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .theft-active {
        border: 2px solid #e03131;
        background-color: #fff5f5;
        box-shadow: 0 0 10px rgba(224, 49, 49, 0.2);
    }
    .power-card {
        background-color: #f1f3f5;
        padding: 20px;
        border-radius: 12px;
        border-right: 5px solid #228be6;
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        font-weight: bold;
        transition: 0.3s;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. تهيئة البيانات والأزرار ---
for i in range(1, 5):
    if f'pole_{i}_theft' not in st.session_state:
        st.session_state[f'pole_{i}_theft'] = False

# ثوابت هندسية (بناءً على قدرة المحولة والأحمال)
LEGAL_HOUSES_POWER = 110.5  # مجموع قدرة البيوت الشرعية (kW)
THEFT_POWER_PER_UNIT = 25.0 # قدرة التجاوز الواحد (kW)
TECHNICAL_LOSSES = 2.4      # فاقد فني طبيعي في الأسلاك (kW)

# حساب عدد التجاوزات
active_thefts = sum([st.session_state[f'pole_{i}_theft'] for i in range(1, 5)])
total_theft_power = active_thefts * THEFT_POWER_PER_UNIT

# القدرة الكلية للمحولة
transformer_total_power = LEGAL_HOUSES_POWER + total_theft_power + TECHNICAL_LOSSES

# الحسابات المالية (سعر الـ 1kW/h هو 50 دينار)
iqd_per_kwh = 50
hourly_loss = int(total_theft_power * iqd_per_kwh)
monthly_loss = hourly_loss * 24 * 30

# --- 3. واجهة المستخدم الرئيسية ---
st.title("⚡ نظام إدارة أحمال زقاق الأنبار الذكي")
st.markdown(f"**المصمم:** المهندس محمد نبيل | **جامعة الأنبار**")

st.divider()

# قسم مقارنة القدرة (The Power Dashboard)
st.subheader("📉 موازنة القدرة اللحظية (Power Balance)")
p_col1, p_col2, p_col3 = st.columns(3)

with p_col1:
    st.markdown(f"""
    <div class='power-card'>
        <small>القدرة الخارجة من المحولة</small>
        <h2 style='color: #1c7ed6;'>{round(transformer_total_power, 1)} kW</h2>
    </div>
    """, unsafe_allow_html=True)

with p_col2:
    st.markdown(f"""
    <div class='power-card' style='border-right-color: #40c057;'>
        <small>مجموع قدرة البيوت (شرعي)</small>
        <h2 style='color: #2b8a3e;'>{LEGAL_HOUSES_POWER} kW</h2>
    </div>
    """, unsafe_allow_html=True)

with p_col3:
    color = "#e03131" if total_theft_power > 0 else "#2b8a3e"
    st.markdown(f"""
    <div class='power-card' style='border-right-color: {color};'>
        <small>القدرة المفقودة (تجاوز)</small>
        <h2 style='color: {color};'>{round(total_theft_power, 1)} kW</h2>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# قسم التحكم والتمثيل المرئي (الشارع والأعمدة)
st.subheader("🕹️ لوحة التحكم وتحديد المواقع")
st.info("قم بتفعيل الأزرار لمحاكاة التجاوز في مناطق محددة بين المنازل.")

# عرض "الشارع" بتنسيق أفقي
# محولة -> بيت 1 -> عمود 1 -> بيت 2 ... الخ
street = st.columns(9)

# 1. المحولة
with street[0]:
    st.markdown("<div class='node-box'>🏢<br><b>المحولة</b></div>", unsafe_allow_html=True)

# 2. بيت 1
with street[1]:
    st.markdown("<div class='node-box' style='background:#e7f5ff;'>🏠<br>بيت 1</div>", unsafe_allow_html=True)

# 3. عمود 1 (بين بيت 1 و 2)
with street[2]:
    is_act = st.session_state.pole_1_theft
    style = "node-box theft-active" if is_act else "node-box"
    st.markdown(f"<div class='{style}'>🗼<br><b>عـامود 1</b><br><small>بين 1 و 2</small></div>", unsafe_allow_html=True)
    btn_label = "إيقاف" if is_act else "تجاوز"
    if st.button(btn_label, key="b1"):
        st.session_state.pole_1_theft = not st.session_state.pole_1_theft
        st.rerun()

# 4. بيت 2
with street[3]:
    st.markdown("<div class='node-box' style='background:#e7f5ff;'>🏠<br>بيت 2</div>", unsafe_allow_html=True)

# 5. عمود 2 (بين بيت 2 و 3)
with street[4]:
    is_act = st.session_state.pole_2_theft
    style = "node-box theft-active" if is_act else "node-box"
    st.markdown(f"<div class='{style}'>🗼<br><b>عـامود 2</b><br><small>بين 2 و 3</small></div>", unsafe_allow_html=True)
    btn_label = "إيقاف" if is_act else "تجاوز"
    if st.button(btn_label, key="b2"):
        st.session_state.pole_2_theft = not st.session_state.pole_2_theft
        st.rerun()

# 6. بيت 3
with street[5]:
    st.markdown("<div class='node-box' style='background:#e7f5ff;'>🏠<br>بيت 3</div>", unsafe_allow_html=True)

# 7. عمود 3 (بين بيت 3 و 4)
with street[6]:
    is_act = st.session_state.pole_3_theft
    style = "node-box theft-active" if is_act else "node-box"
    st.markdown(f"<div class='{style}'>🗼<br><b>عـامود 3</b><br><small>بين 3 و 4</small></div>", unsafe_allow_html=True)
    btn_label = "إيقاف" if is_act else "تجاوز"
    if st.button(btn_label, key="b3"):
        st.session_state.pole_3_theft = not st.session_state.pole_3_theft
        st.rerun()

# 8. بيت 4
with street[7]:
    st.markdown("<div class='node-box' style='background:#e7f5ff;'>🏠<br>بيت 4</div>", unsafe_allow_html=True)

# 9. عمود 4 (بين بيت 4 و 5)
with street[8]:
    is_act = st.session_state.pole_4_theft
    style = "node-box theft-active" if is_act else "node-box"
    st.markdown(f"<div class='{style}'>🗼<br><b>عـامود 4</b><br><small>بين 4 و 5</small></div>", unsafe_allow_html=True)
    btn_label = "إيقاف" if is_act else "تجاوز"
    if st.button(btn_label, key="b4"):
        st.session_state.pole_4_theft = not st.session_state.pole_4_theft
        st.rerun()

st.divider()

# قسم الخسائر المالية
st.subheader("💰 تقرير الهدر المالي (بالدينار العراقي)")
f_col1, f_col2 = st.columns(2)

with f_col1:
    st.metric("خسارة الساعة الحالية", f"{hourly_loss:,} IQD", delta=f"{total_theft_power} kW", delta_color="inverse")
    st.write("تكلفة الطاقة الضائعة في الساعة الواحدة نتيجة التجاوزات النشطة.")

with f_col2:
    st.metric("الخسارة الشهرية المتوقعة", f"{monthly_loss:,} IQD")
    st.write("المبلغ المهدور خلال 30 يوم في حال عدم معالجة هذه التجاوزات.")

st.divider()
st.markdown("<center>نظام المراقبة الذكي v8.0 | جامعة الأنبار 2026</center>", unsafe_allow_html=True)
