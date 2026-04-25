import streamlit as st
import pandas as pd
import numpy as np
import time

# --- 1. إعدادات الصفحة والتنسيق الجمالي ---
st.set_page_config(page_title="Al-Anbar Smart Grid UI", layout="wide")

st.markdown("""
    <style>
    .main-title { font-size: 30px; font-weight: bold; color: #1E3A8A; text-align: center; margin-bottom: 20px; }
    .status-card { 
        border-radius: 12px; 
        padding: 15px; 
        background-color: #f8f9fa; 
        border-right: 5px solid #1E3A8A; 
        margin-bottom: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    .theft-card { 
        border-right: 5px solid #ff4b4b; 
        background-color: #fff5f5;
        animation: blinker 1.5s linear infinite;
    }
    @keyframes blinker { 50% { opacity: 0.7; } }
    .alert-box { 
        background-color: #212529; 
        color: #00ff00; 
        padding: 10px; 
        border-radius: 5px; 
        font-family: 'Courier New', monospace; 
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. تهيئة الذاكرة (Session State) ---
if 'alert_history' not in st.session_state: st.session_state.alert_history = []
if 'total_loss' not in st.session_state: st.session_state.total_loss = 0

# --- 3. لوحة التحكم الجانبية (Sidebar) ---
with st.sidebar:
    st.header("🕹️ لوحة التحكم")
    if st.button("🔄 تحديث البيانات (IoT)", use_container_width=True):
        st.toast("جاري سحب البيانات من الحساسات...")
    
    st.divider()
    st.subheader("⚠️ محاكاة التجاوز")
    theft_loc = st.selectbox("اختر مكان التجاوز للفحص:", 
                             ["لا يوجد", "مقطع 1 (زقاق 1)", "مقطع 2 (زقاق 2)", "مقطع 3 (زقاق 3)"])
    
    temp_val = st.slider("حرارة المحولة (°C)", 30, 110, 50)
    
    st.divider()
    if st.button("🗑️ تصفير السجلات"):
        st.session_state.alert_history = []
        st.session_state.total_loss = 0
        st.rerun()

# --- 4. الحسابات الهندسية ---
legal_load = 85 # أمبير
theft_val = 55 if theft_loc != "لا يوجد" else 0
total_current = legal_load + theft_val
v_base = 220 - (12 if theft_val > 0 else 0)

# حساب الخسائر (50 دينار للأمبير/ساعة)
hourly_loss = theft_val * 50
st.session_state.total_loss += hourly_loss

# --- 5. واجهة العرض الرئيسية ---
st.markdown("<div class='main-title'>⚡ منظومة مراقبة شبكة الأنبار الذكية</div>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📊 المراقبة والشارع", "💰 التحليل المالي", "📜 سجل الإنذارات"])

with tab1:
    # المقاييس العلوية
    m1, m2, m3 = st.columns(3)
    m1.metric("التيار الكلي (المحولة)", f"{total_current} A")
    m2.metric("درجة الحرارة", f"{temp_val} °C", delta="مرتفع!" if temp_val > 80 else None, delta_color="inverse")
    m3.metric("الجهد الحالي", f"{v_base} V")

    st.divider()
    st.subheader("📍 خارطة توزيع الشارع (Live View)")
    
    # تمثيل الشارع
    c_trans, c_a1, c_a2, c_a3 = st.columns(4)
    
    with c_trans:
        st.markdown(f"<div class='status-card'>🏢 <b>المحولة الرئيسية</b><br>المكان: شارع المستودع</div>", unsafe_allow_html=True)
        if temp_val > 85: st.error("🔥 حرارة عالية!")

    with c_a1:
        is_h = (theft_loc == "مقطع 1 (زقاق 1)")
        style = "status-card theft-card" if is_h else "status-card"
        st.markdown(f"<div class='{style}'>🗼 <b>عامود 1</b><br>يغذي بيت 1-4</div>", unsafe_allow_html=True)
        if is_h: st.warning("🪝 تجاوز مكتشف!")

    with c_a2:
        is_h = (theft_loc == "مقطع 2 (زقاق 2)")
        style = "status-card theft-card" if is_h else "status-card"
        st.markdown(f"<div class='{style}'>🗼 <b>عامود 2</b><br>يغذي بيت 5-8</div>", unsafe_allow_html=True)
        if is_h: st.warning("🪝 تجاوز مكتشف!")

    with c_a3:
        is_h = (theft_loc == "مقطع 3 (زقاق 3)")
        style = "status-card theft-card" if is_h else "status-card"
        st.markdown(f"<div class='{style}'>🗼 <b>عامود 3</b><br>يغذي بيت 9-12</div>", unsafe_allow_html=True)
        if is_h: st.warning("🪝 تجاوز مكتشف!")

    st.divider()
    # تحليل النسب
    st.subheader("🔍 تحليل كفاءة الطاقة")
    st.progress(legal_load/total_current if total_current > 0 else 1.0, text=f"نسبة الاستهلاك القانوني: {int((legal_load/total_current)*100)}%")

with tab2:
    st.subheader("💵 التقرير الاقتصادي للخسائر")
    col_f1, col_f2 = st.columns(2)
    col_f1.metric("خسارة الساعة الحالية", f"{hourly_loss} IQD")
    col_f2.metric("إجمالي الخسائر المتراكمة", f"{st.session_state.total_loss:,} IQD")
    
    st.info("💡 يتم احتساب الخسائر بناءً على الفرق بين تيار مخرج المحولة ومجموع العدادات الذكية المسجلة قانونياً.")

with tab3:
    st.subheader("📂 سجل أحداث المنظومة")
    if theft_val > 0:
        msg = f"[{time.strftime('%H:%M:%S')}] اكتشاف تجاوز في {theft_loc} بقيمة {theft_val}A"
        if not st.session_state.alert_history or msg != st.session_state.alert_history[0]:
            st.session_state.alert_history.insert(0, msg)
            st.toast("تم إرسال إشعار تليجرام للمراقب!")

    if st.session_state.alert_history:
        for log in st.session_state.alert_history[:10]:
            st.markdown(f"<div class='alert-box'>{log}</div>", unsafe_allow_html=True)
            st.write("")
    else:
        st.write("لا توجد إنذارات حالياً.")

# تذييل الصفحة
st.markdown("---")
st.caption("إعداد الطالب: محمد نبيل | كلية الهندسة - جامعة الأنبار | 2026")
