import streamlit as st
import pandas as pd
import numpy as np

# إعدادات الصفحة - Wide mode لراحة العين
st.set_page_config(page_title="Al-Anbar Smart Grid UI", layout="wide")

# --- تحسينات بصرية إضافية ---
st.markdown("""
    <style>
    .main-title { font-size: 32px; font-weight: bold; color: #1E3A8A; text-align: center; margin-bottom: 20px; }
    .status-card { border-radius: 10px; padding: 15px; background-color: #f8f9fa; border-right: 5px solid #1E3A8A; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- البيانات الافتراضية ---
legal_load = 85
theft_loc = st.sidebar.selectbox("🎯 اختر مكان التجاوز (للمحاكاة):", 
                                 ["لا يوجد", "مقطع 1", "مقطع 2", "مقطع 3"])
theft_val = 50 if theft_loc != "لا يوجد" else 0

# --- تقسيم الواجهة إلى تبويبات احترافية ---
st.markdown("<div class='main-title'>⚡ لوحة التحكم الذكية لشبكة الأنبار</div>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📊 المراقبة اللحظية", "💰 التحليل المالي", "📖 دليل المنظومة"])

with tab1:
    # عرض حالة الشارع بشكل مبسط
    st.subheader("📍 خريطة الشارع والأعمدة")
    
    # استخدام الأعمدة لعرض "الشارع"
    col_trans, col_a1, col_a2, col_a3 = st.columns(4)
    
    with col_trans:
        st.markdown("<div class='status-card'>🏢 <b>المحولة المركزية</b><br>الحالة: ✅ تعمل</div>", unsafe_allow_html=True)
        st.metric("الخارج الكلي", f"{legal_load + theft_val} A")
        
    with col_a1:
        st.write("---")
        is_hit = (theft_loc == "مقطع 1")
        color = "🔴" if is_hit else "⚪"
        st.markdown(f"<div class='status-card'>{color} <b>عامود 1</b><br>المنطقة: زقاق 1</div>", unsafe_allow_html=True)
        if is_hit: st.error("⚠️ اكتشاف سرقة!")
        
    with col_a2:
        st.write("---")
        is_hit = (theft_loc == "مقطع 2")
        color = "🔴" if is_hit else "⚪"
        st.markdown(f"<div class='status-card'>{color} <b>عامود 2</b><br>المنطقة: زقاق 2</div>", unsafe_allow_html=True)
        if is_hit: st.error("⚠️ اكتشاف سرقة!")

    with col_a3:
        st.write("---")
        is_hit = (theft_loc == "مقطع 3")
        color = "🔴" if is_hit else "⚪"
        st.markdown(f"<div class='status-card'>{color} <b>عامود 3</b><br>المنطقة: زقاق 3</div>", unsafe_allow_html=True)
        if is_hit: st.error("⚠️ اكتشاف سرقة!")

    st.divider()
    # مقارنة بصرية سريعة للدكتور
    st.subheader("🔍 ملخص مقارنة القدرة")
    c1, c2 = st.columns(2)
    c1.progress(legal_load / (legal_load + theft_val + 0.1), text="الاستهلاك القانوني (%)")
    c2.progress(theft_val / (legal_load + theft_val + 0.1), text="نسبة التجاوز (%)")

with tab2:
    st.subheader("💵 تقرير الخسائر المالية والاقتصادية")
    m1, m2 = st.columns(2)
    loss_iqd = theft_val * 50 # افتراض السعر
    m1.metric("خسارة الساعة الحالية", f"{loss_iqd} دينار")
    m2.metric("التكلفة الشهرية المتوقعة", f"{loss_iqd * 24 * 30:,} دينار")
    
    st.info("💡 تم حساب هذه الأرقام بناءً على الفرق بين تيار المحولة الكلي ومجموع قراءات العدادات الذكية.")

with tab3:
    st.subheader("📚 كيف يعمل النظام؟")
    st.markdown("""
    هذا النظام يعتمد على **قانون كيرشوف للتيار (KCL)**:
    1. يتم قياس التيار عند مخرج المحولة.
    2. يتم جمع التيارات المسجلة في عدادات البيوت (Smart Meters).
    3. إذا كان (تيار المحولة > مجموع تيار البيوت + نسبة الفاقد الفني)، يتم إطلاق الإنذار.
    4. يتم تحديد المكان الدقيق من خلال فحص الحساسات الموزعة على طول الخط (الأعمدة).
    """)
    st.success("إعداد الطالب: محمد نبيل - كلية الهندسة - جامعة الأنبار")
    د
