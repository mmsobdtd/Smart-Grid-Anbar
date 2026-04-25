import streamlit as st
import pandas as pd
import numpy as np
import time

# --- 1. إعدادات الصفحة والتنسيق الاحترافي ---
st.set_page_config(page_title="Al-Anbar Grid - Engineering Edition", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1a1a1a; }
    .street-line {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 20px 0;
    }
    .node-box {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 12px;
        padding: 10px;
        text-align: center;
        min-width: 100px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    .wire {
        flex-grow: 1;
        height: 4px;
        background: #ced4da;
        margin: 0 5px;
        position: relative;
    }
    .wire-theft {
        background: #fa5252 !important;
        box-shadow: 0 0 10px #fa5252;
    }
    .theft-active {
        border: 2px solid #e03131 !important;
        background-color: #fff5f5 !important;
    }
    .engineer-panel {
        background-color: #f1f3f5;
        border-right: 5px solid #228be6;
        padding: 15px;
        border-radius: 10px;
        margin-top: 20px;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة الحالة (Session State) ---
for i in range(1, 5):
    if f'pole_{i}_theft' not in st.session_state:
        st.session_state[f'pole_{i}_theft'] = False
if 'messages_sent' not in st.session_state:
    st.session_state.messages_sent = []

# --- 3. المحرك الهندسي والمالي ---
LEGAL_LOAD = 112.5 # kW
THEFT_UNIT = 28.0  # kW
active_count = sum([st.session_state[f'pole_{i}_theft'] for i in range(1, 5)])
total_theft = active_count * THEFT_UNIT
transformer_power = LEGAL_LOAD + total_theft + 1.5 # + losses

hourly_loss = int(total_theft * 50) # 50 IQD/kWh
monthly_loss = hourly_loss * 24 * 30

# --- 4. الواجهة الرئيسية ---
st.title("⚡ نظام رصد وتتبع التجاوزات الذكي - محافظة الأنبار")
st.markdown(f"**إشراف وتصميم:** المهندس محمد نبيل")

st.divider()

# قسم موازنة القدرة (Dashboard)
col_p1, col_p2, col_p3 = st.columns(3)
with col_p1:
    st.metric("قدرة المحولة الكلية", f"{round(transformer_total_power if 'transformer_total_power' in locals() else transformer_power, 1)} kW")
with col_p2:
    st.metric("مجموع استهلاك البيوت", f"{LEGAL_LOAD} kW")
with col_p3:
    st.metric("القدرة المسروقة", f"{round(total_theft, 1)} kW", delta=f"{total_theft} kW", delta_color="inverse")

st.divider()

# --- 5. تمثيل الشارع (The Street Flow) ---
st.subheader("🏙️ محاكاة المسار الكهربائي للزقاق")
st.info("توضح الخارطة أدناه تسلسل الأعمدة بين البيوت. اللون الأحمر يشير إلى مكان السرقة الدقيق.")

# دالة لرسم المقطع
def draw_street_segment():
    cols = st.columns([1, 0.5, 1, 0.5, 1, 0.5, 1, 0.5, 1])
    
    # محولة
    with cols[0]: st.markdown("<div class='node-box'>🏢<br>المحولة</div>", unsafe_allow_html=True)
    
    # أعمدة وبيوت
    for i in range(1, 5):
        # سلك
        with cols[2*i - 1]:
            is_theft = st.session_state[f'pole_{i}_theft']
            class_name = "wire wire-theft" if is_theft else "wire"
            st.markdown(f"<div class='{class_name}'></div>", unsafe_allow_html=True)
        
        # عمود (بين البيوت)
        with cols[2*i]:
            is_theft = st.session_state[f'pole_{i}_theft']
            style = "node-box theft-active" if is_theft else "node-box"
            st.markdown(f"<div class='{style}'>🗼<br><b>عامود {i}</b><br><small>بين بيت {i} و {i+1}</small></div>", unsafe_allow_html=True)
            if st.button("تغيير" , key=f"btn_{i}"):
                st.session_state[f'pole_{i}_theft'] = not st.session_state[f'pole_{i}_theft']
                st.rerun()

draw_street_segment()

st.divider()

# --- 6. نظام مراسلة المهندس المقيم ---
col_fin, col_msg = st.columns([1.5, 1])

with col_fin:
    st.subheader("💰 التحليل المالي للهدر")
    c1, c2 = st.columns(2)
    c1.markdown(f"**الخسارة بالساعة:** <h2 style='color:#e03131;'>{hourly_loss:,} IQD</h2>", unsafe_allow_html=True)
    c2.markdown(f"**الخسارة بالشهر:** <h3 style='color:#e03131;'>{monthly_loss:,} IQD</h3>", unsafe_allow_html=True)

with col_msg:
    st.subheader("📧 إرسال إشعار للمهندس")
    if active_count > 0:
        st.warning(f"يوجد حالياً {active_count} تجاوزات نشطة.")
        if st.button("📩 إرسال تقرير تجاوز للمهندس المقيم", type="primary"):
            # محاكاة إرسال الرسالة
            locations = [f"بين بيت {i} وبيت {i+1}" for i in range(1,5) if st.session_state[f'pole_{i}_theft']]
            report_msg = f"تنبيه: تم رصد تجاوز في زقاق الأنبار. المواقع: {', '.join(locations)}. القيمة المفقودة: {total_theft}kW."
            st.session_state.messages_sent.append(f"[{time.strftime('%H:%M')}] {report_msg}")
            st.success("✅ تم إرسال الرسالة للمهندس المقيم بنجاح!")
            st.toast("رسالة تليجرام قيد الإرسال...")
    else:
        st.write("الشبكة سليمة، لا حاجة لإرسال تقارير.")

# عرض سجل الرسائل المرسلة
with st.expander("📂 سجل الرسائل الصادرة للمهندس"):
    if st.session_state.messages_sent:
        for m in st.session_state.messages_sent:
            st.write(f"🔹 {m}")
    else:
        st.write("لا توجد رسائل مرسلة بعد.")

st.divider()
st.markdown("<center>نظام المراقبة الذكي v9.0 | جامعة الأنبار - كلية الهندسة 2026</center>", unsafe_allow_html=True)
