import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime

# إعدادات الصفحة
st.set_page_config(page_title="Anbar Smart Grid - Protection System", layout="wide")

# --- تهيئة الحالة (Session State) ---
if 'system_active' not in st.session_state:
    st.session_state.system_active = True
if 'is_tripped' not in st.session_state:
    st.session_state.is_tripped = False
if 'trip_reason' not in st.session_state:
    st.session_state.trip_reason = ""

# --- العنوان والشعار ---
st.title("⚡ نظام حماية ومراقبة أحمال الأنبار الذكي")
st.markdown(f"**إعداد المهندس:** محمد نبيل | **الحالة الآن:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# --- القائمة الجانبية للإعدادات (Thresholds) ---
st.sidebar.header("⚙️ إعدادات الحماية (Protection Thresholds)")
max_current = st.sidebar.slider("الحد الأقصى للتيار (Amps)", 50, 200, 150)
max_temp = st.sidebar.slider("درجة الحرارة الحرجة (C°)", 40, 100, 85)
wire_resistance = st.sidebar.number_input("مقاومة الأسلاك (Ohm)", value=0.05)

if st.sidebar.button("إعادة تشغيل المنظومة (Reset System)"):
    st.session_state.is_tripped = False
    st.session_state.system_active = True
    st.session_state.trip_reason = ""

# --- محاكاة البيانات (Data Simulation) ---
def get_live_data():
    # محاكاة قراءات الحساسات (PZEM-004T + DS18B20)
    voltage = np.random.uniform(210, 230)
    # رفع التيار والحرارة تدريجياً للمحاكاة
    current = np.random.uniform(80, 160) if st.session_state.system_active else 0
    temp = np.random.uniform(40, 95) if st.session_state.system_active else 30
    pf = 0.85 # Power Factor
    power = voltage * current * pf / 1000 # kW
    losses = (current**2 * wire_resistance) / 1000 # kW
    
    return voltage, current, temp, power, losses

v, i, t, p, loss = get_live_data()

# --- منطق الفصل الآلي (Automatic Tripping Logic) ---
if st.session_state.system_active:
    if i > max_current:
        st.session_state.is_tripped = True
        st.session_state.system_active = False
        st.session_state.trip_reason = f"Overload Detected: {i:.1f} Amps"
    elif t > max_temp:
        st.session_state.is_tripped = True
        st.session_state.system_active = False
        st.session_state.trip_reason = f"Critical Overheating: {t:.1f}°C"

# --- عرض لوحة التحكم (Dashboard Display) ---
if st.session_state.is_tripped:
    st.error(f"🚨 تم فصل المنظومة آلياً (SYSTEM TRIPPED)! السبب: {st.session_state.trip_reason}")
else:
    st.success("✅ المنظومة تعمل بشكل طبيعي")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("الجهد (Voltage)", f"{v:.1f} V")
with col2:
    color = "normal" if i < max_current * 0.8 else "inverse"
    st.metric("التيار (Current)", f"{i:.1f} A", delta=f"{i-max_current:.1f} Limit", delta_color=color)
with col3:
    st.metric("درجة الحرارة (Temp)", f"{t:.1f} °C")
with col4:
    st.metric("الضياعات (Power Losses)", f"{loss:.3f} kW")

# --- الرسوم البيانية ---
st.divider()
st.subheader("📊 تحليل الاستهلاك والضياعات في الوقت الفعلي")

# إنشاء بيانات تاريخية للمحاكاة
chart_data = pd.DataFrame(
    np.random.randn(20, 2) / [10, 5] + [p, loss],
    columns=['القدرة الفعلية (kW)', 'الضياعات الفنية (kW)']
)

st.line_chart(chart_data)

# --- قسم التنبؤ (Predictive Maintenance Section) ---
st.divider()
st.subheader("🔮 التحليل التنبؤي للأعطال")
risk_level = (t / max_temp) * 100
if risk_level < 70:
    st.info(f"مستوى الخطر الحالي: {risk_level:.1f}% - المحول في حالة ممتازة.")
elif risk_level < 90:
    st.warning(f"مستوى الخطر: {risk_level:.1f}% - يُنصح بموازنة الأحمال قريباً.")
else:
    st.error(f"مستوى الخطر: {risk_level:.1f}% - خطر انفجار أو تلف وشيك!")

# زر الطوارئ اليدوي
if not st.session_state.is_tripped:
    if st.button("🔴 فصل اضطراري يدوي (Manual Emergency Stop)", use_container_width=True):
        st.session_state.is_tripped = True
        st.session_state.system_active = False
        st.session_state.trip_reason = "Manual Emergency Shutdown"
        
