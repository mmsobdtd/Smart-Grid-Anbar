import streamlit as st
import pandas as pd
import numpy as np
import time

# --- 1. إعدادات الصفحة والتنسيق ---
st.set_page_config(page_title="Al-Anbar Smart Grid - Autonomous System", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .node-box {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 12px;
        padding: 10px;
        text-align: center;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    .wire { flex-grow: 1; height: 4px; background: #ced4da; margin: 0 5px; }
    .wire-theft { background: #fa5252 !important; box-shadow: 0 0 10px #fa5252; }
    .theft-active { border: 2px solid #e03131 !important; background-color: #fff5f5 !important; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة الحالة والبيانات الواقعية ---
# قيم تجاوز واقعية (بالكيلو واط) لكل منطقة
THEFT_MAP = {
    1: 4.2,  # بين بيت 1 و 2
    2: 8.7,  # بين بيت 2 و 3
    3: 12.4, # بين بيت 3 و 4
    4: 15.8  # بين بيت 4 و 5
}

for i in range(1, 5):
    if f'pole_{i}_theft' not in st.session_state:
        st.session_state[f'pole_{i}_theft'] = False
if 'log' not in st.session_state: st.session_state.log = []

# --- 3. المحرك الهندسي ---
LEGAL_LOAD = 105.0 # kW (الاستهلاك الطبيعي للزقاق)
total_theft_kw = sum([THEFT_MAP[i] for i in range(1, 5) if st.session_state[f'pole_{i}_theft']])
transformer_output = LEGAL_LOAD + total_theft_kw + 2.1 # فواقد فنية

# حسابات مالية (50 دينار للـ kWh)
hourly_loss = int(total_theft_kw * 50)
monthly_loss = hourly_loss * 24 * 30

# --- 4. الواجهة الرئيسية ---
st.title("⚡ نظام المراقبة الذاتي والتبليغ التلقائي - زقاق الأنبار")
st.markdown("**إعداد الطالب:** محمد نبيل | **الحالة:** نظام الفرز والتبليغ المباشر نشط")

st.divider()

# داشبورد القراءات
c1, c2, c3 = st.columns(3)
c1.metric("قدرة المحولة الكلية", f"{round(transformer_output, 1)} kW")
c2.metric("مجموع قراءات العدادات", f"{LEGAL_LOAD} kW")
c3.metric("القدرة المفقودة (سرقة)", f"{round(total_theft_kw, 1)} kW", delta=f"{round(total_theft_kw, 1)} kW", delta_color="inverse")

st.divider()

# --- 5. تمثيل الشارع والتحكم ---
st.subheader("🏙️ خارطة المسار الكهربائي وتحديد نقاط التجاوز")

street = st.columns([1, 0.5, 1, 0.5, 1, 0.5, 1, 0.5, 1])

with street[0]: st.markdown("<div class='node-box'>🏢<br>المحولة</div>", unsafe_allow_html=True)

for i in range(1, 5):
    # تمثيل السلك
    with street[2*i - 1]:
        is_th = st.session_state[f'pole_{i}_theft']
        st.markdown(f"<div class='wire {'wire-theft' if is_th else ''}'></div>", unsafe_allow_html=True)
    
    # تمثيل العمود والتحكم
    with street[2*i]:
        is_th = st.session_state[f'pole_{i}_theft']
        style = "node-box theft-active" if is_th else "node-box"
        st.markdown(f"<div class='{style}'>🗼<br><b>عـامود {i}</b><br><small>{THEFT_MAP[i]} kW</small></div>", unsafe_allow_html=True)
        if st.button("تغيير", key=f"p_{i}"):
            st.session_state[f'pole_{i}_theft'] = not st.session_state[f'pole_{i}_theft']
            st.rerun()

st.divider()

# --- 6. منطق الإرسال التلقائي بعد 3 ثواني ---
st.subheader("💰 التقرير المالي ونظام الإشعارات الآلي")
f1, f2 = st.columns([1.5, 1])

with f1:
    st.markdown(f"**خسارة الساعة:** <span style='color:red; font-size:24px;'>{hourly_loss:,} IQD</span>", unsafe_allow_html=True)
    st.markdown(f"**خسارة الشهر:** <span style='color:red; font-size:20px;'>{monthly_loss:,} IQD</span>", unsafe_allow_html=True)

with f2:
    if total_theft_kw > 0:
        # محاكاة الانتظار والإرسال التلقائي
        with st.status("🔍 جاري تحليل التجاوز المكتشف...", expanded=True) as status:
            st.write("تحليل فرق الجهد والتيار...")
            time.sleep(1.5)
            st.write("تحديد الإحداثيات الجغرافية للمقطع المصاب...")
            time.sleep(1.5) # مجموع الوقت 3 ثواني
            status.update(label="✅ تم إرسال البلاغ للمهندس المقيم!", state="complete", expanded=False)
        
        # إضافة البلاغ للسجل
        locs = [f"بين {i} و {i+1}" for i in range(1, 5) if st.session_state[f'pole_{i}_theft']]
        alert = f"[{time.strftime('%H:%M:%S')}] تم التبليغ عن تجاوز {total_theft_kw}kW في المواقع: {', '.join(locs)}"
        if not st.session_state.log or alert.split(']')[1] != st.session_state.log[0].split(']')[1]:
            st.session_state.log.insert(0, alert)
            st.toast("🚨 رسالة عاجلة أرسلت للمهندس!")
    else:
        st.success("✅ الشبكة مستقرة ولا توجد تجاوزات.")

# السجل التاريخي للرسائل
with st.expander("📂 سجل الرسائل الصادرة للمهندس"):
    for l in st.session_state.log[:5]:
        st.write(f"🔹 {l}")

st.divider()
st.markdown("<center>نظام التحكم الذكي v10.0 | جامعة الأنبار 2026</center>", unsafe_allow_html=True)
د
