import streamlit as st
import pandas as pd
import time
import random

st.set_page_config(page_title="Smart Grid - Stochastic Simulation", layout="wide")

# 1. الذاكرة المشتركة للنظام
if 'system' not in st.session_state:
    st.session_state.system = {
        "log": [], 
        "stations": {"طالب 1": "ON", "طالب 2": "ON", "طالب 3": "ON", "طالب 4": "ON"}
    }

st.title("⚡ محاكاة تذبذب الشبكة الذكية (Unstable Data Simulation)")

# --- لوحة التحكم الجانبية ---
st.sidebar.header("🕹️ إعدادات المحاكاة")
mode = st.sidebar.radio("اختر وضع البيانات:", ["إدخال يدوي", "تذبذب طبيعي (Stable)", "تذبذب غير مستقر (Unstable/Noisy)"])
refresh_speed = st.sidebar.slider("سرعة التحديث (ثانية):", 0.5, 5.0, 1.0)

if st.sidebar.button("تصفير المنظومة ♻️"):
    st.session_state.system["log"] = []
    for s in st.session_state.system["stations"]: st.session_state.system["stations"][s] = "ON"
    st.rerun()

# --- محرك توليد البيانات (Simulator Engine) ---
def generate_voltage(mode):
    if mode == "تذبذب طبيعي (Stable)":
        return random.uniform(215, 225) # تذبذب بسيط حول الـ 220V
    elif mode == "تذبذب غير مستقر (Unstable/Noisy)":
        # محاكاة قفزات جهد (Spikes) غير متوقعة
        chance = random.random()
        if chance > 0.8: return random.uniform(300, 380) # قفزة مفاجئة (Spike)
        if chance < 0.2: return random.uniform(150, 200) # هبوط مفاجئ (Sag)
        return random.uniform(200, 260)
    return None

# --- معالجة البيانات وتحديث الواجهة ---
@st.fragment(run_every=refresh_speed)
def run_simulation():
    if mode != "إدخال يدوي":
        active_ones = [s for s, status in st.session_state.system["stations"].items() if status == "ON"]
        if active_ones:
            target = random.choice(active_ones)
            v_val = round(generate_voltage(mode), 2)
            t_stamp = time.strftime("%H:%M:%S")
            
            # منطق الحماية (Safety Logic)
            status_text = "✅ مستقر"
            if v_val > 350:
                st.session_state.system["stations"][target] = "OFF"
                status_text = "💥 إطفاء (Overload)"
            elif v_val < 180:
                status_text = "⚠️ هبوط جهد"
            
            st.session_state.system["log"].append({
                "الوقت": t_stamp, "المحطة": target, "القيمة": v_val, "الحالة": status_text
            })

    # عرض حالة المحطات
    cols = st.columns(4)
    for i, (name, status) in enumerate(st.session_state.system["stations"].items()):
        color = "green" if status == "ON" else "red"
        cols[i].markdown(f"**{name}**")
        cols[i].markdown(f"<h3 style='color:{color};'>{status}</h3>", unsafe_allow_html=True)

    st.markdown("---")
    
    if st.session_state.system["log"]:
        c1, c2 = st.columns([1, 1])
        with c1:
            st.subheader("📡 تدفق البيانات اللحظي")
            df = pd.DataFrame(st.session_state.system["log"]).sort_index(ascending=False)
            st.table(df.head(10))
        with c2:
            st.subheader("📈 مخطط الاستقرار الكهربائي")
            st.line_chart(pd.DataFrame(st.session_state.system["log"]).set_index('الوقت')['القيمة'])

run_simulation()
