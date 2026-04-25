import streamlit as st
import pandas as pd
import numpy as np

# --- 1. إعدادات الصفحة والتنسيق الاحترافي ---
st.set_page_config(page_title="Al-Anbar Smart Grid - Financial Monitor", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1a1a1a; }
    .node-box {
        background: #f8f9fa;
        border: 2px solid #e9ecef;
        border-radius: 12px;
        padding: 15px;
        text-align: center;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }
    .theft-active {
        border: 2px solid #dc3545;
        background-color: #fff5f5;
        box-shadow: 0 0 15px rgba(220, 53, 69, 0.2);
    }
    .financial-card {
        background-color: #e7f3ff;
        border-right: 5px solid #007bff;
        padding: 20px;
        border-radius: 10px;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. تهيئة حالة الأزرار (Session State لـ 4 أعمدة) ---
for i in range(1, 5):
    if f'pole_{i}_theft' not in st.session_state:
        st.session_state[f'pole_{i}_theft'] = False

# --- 3. المحرك الهندسي والمالي ---
V_SOURCE = 226.50
R_LINE = 0.350       # مقاومة السلك
LEGAL_I = 92.0       # الاستهلاك الشرعي (أمبير)
THEFT_I_PER_POLE = 40.0 # التيار المسحوب عند كل تجاوز (أمبير)
IQD_PER_KWH = 50     # سعر الكيلو واط ساعة

# حساب عدد التجاوزات النشطة حالياً
active_thefts = sum([st.session_state[f'pole_{i}_theft'] for i in range(1, 5)])
total_theft_i = active_thefts * THEFT_I_PER_POLE

# الحسابات الهندسية
total_i = LEGAL_I + total_theft_i
v_drop = total_i * R_LINE
v_actual = V_SOURCE - v_drop

# حساب الخسائر المالية
# P = (V * I * PF) / 1000 -> PF = 0.9
p_theft_kw = (v_actual * total_theft_i * 0.9) / 1000
loss_iqd_hour = int(p_theft_kw * IQD_PER_KWH)
loss_iqd_month = loss_iqd_hour * 24 * 30

# --- 4. واجهة المستخدم ---
st.title("⚡ منظومة رصد التجاوزات والتحليل المالي")
st.markdown(f"**إعداد الطالب:** محمد نبيل | **الجامعة:** جامعة الأنبار - كلية الهندسة")

st.divider()

# قسم التحكم (الأزرار الأربعة)
st.subheader("🕹️ لوحة حقن التجاوزات (تحكم متعدد)")
ctrl_cols = st.columns(4)

for i in range(1, 5):
    with ctrl_cols[i-1]:
        label = "❌ إيقاف التجاوز" if st.session_state[f'pole_{i}_theft'] else "🪝 تفعيل تجاوز"
        if st.button(label, key=f"btn_{i}"):
            st.session_state[f'pole_{i}_theft'] = not st.session_state[f'pole_{i}_theft']
            st.rerun()
        st.markdown(f"<center><b>عامود {i}</b></center>", unsafe_allow_html=True)

st.divider()

# قسم المقاييس والحالة اللحظية
m1, m2, m3 = st.columns(3)
m1.metric("جهد الشبكة", f"{round(v_actual, 1)} V", f"{round(v_actual-220, 1)}V")
m2.metric("الحمل الكلي المجهز", f"{round(total_i, 1)} A")
m3.metric("عدد التجاوزات النشطة", f"{active_thefts} مواقع")

st.divider()

# قسم تمثيل الشارع (Live Map)
st.subheader("🏙️ المراقبة المرئية لخط التوزيع")
map_cols = st.columns(5)

# عرض المحولة أولاً
with map_cols[0]:
    st.markdown("<div class='node-box'>🏢<br><b>المحولة 01</b><br><small>محطة المستودع</small></div>", unsafe_allow_html=True)

# عرض الأعمدة الأربعة مع استجابة لونية للأزرار
for i in range(1, 5):
    with map_cols[i]:
        is_active = st.session_state[f'pole_{i}_theft']
        style = "node-box theft-active" if is_active else "node-box"
        st.markdown(f"""
            <div class='{style}'>
                <div style='font-size: 30px;'>🗼</div>
                <b>عامود {i}</b><br>
                <small>{'⚠️ تجاوز مكتشف' if is_active else '✅ سليم'}</small>
            </div>
            """, unsafe_allow_html=True)

st.divider()

# قسم التقرير المالي (بديل المعادلات)
st.subheader("💰 تقرير الهدر المالي والاقتصادي")
f_col1, f_col2 = st.columns(2)

with f_col1:
    st.markdown(f"""
    <div class='financial-card'>
        <h3>💸 الخسائر المالية الحالية</h3>
        <p>تيار التجاوز التراكمي: <b>{total_theft_i} أمبير</b></p>
        <h2 style='color: #dc3545;'>{loss_iqd_hour:,} دينار / ساعة</h2>
    </div>
    """, unsafe_allow_html=True)

with f_col2:
    st.markdown(f"""
    <div class='financial-card'>
        <h3>📅 التوقعات الشهرية</h3>
        <p>بناءً على معدل التجاوزات الحالي</p>
        <h2 style='color: #dc3545;'>{loss_iqd_month:,} دينار / شهر</h2>
    </div>
    """, unsafe_allow_html=True)

st.info(f"💡 ملاحظة: تم حساب التكلفة بناءً على سعر {IQD_PER_KWH} دينار للكيلو واط ساعة المعتمد في محافظة الأنبار.")

st.divider()
st.markdown("<center>نظام المراقبة الذكي v7.0 | جامعة الأنبار 2026</center>", unsafe_allow_html=True)

