import streamlit as st
import pandas as pd
import time
import random

st.set_page_config(page_title="Smart Grid Wireless Simulation", layout="wide")

# الذاكرة المشتركة
if 'log' not in st.session_state:
    st.session_state.log = []
if 'stations' not in st.session_state:
    st.session_state.stations = {"طالب 1": "ON", "طالب 2": "ON", "طالب 3": "ON", "طالب 4": "ON"}

st.title("⚡ نظام مراقبة الشبكة الذكية (محاكاة الحساس اللاسلكي)")

# --- لوحة التحكم الجانبية ---
st.sidebar.header("🕹️ التحكم بالنظام")
auto_mode = st.sidebar.toggle("تشغيل الحساس اللاسلكي (Auto-Sense)", value=False)
protocol_active = st.sidebar.toggle("تفعيل بروتوكول الأمان", value=True)

if st.sidebar.button("إعادة تشغيل النظام ♻️"):
    st.session_state.log = []
    for s in st.session_state.stations: st.session_state.stations[s] = "ON"
    st.rerun()

# --- منطق "الحساس اللاسلكي" الافتراضي ---
if auto_mode:
    # يختار محطة عشوائية ويولد لها قيمة كل ثانية
    target_station = random.choice(["طالب 1", "طالب 2", "طالب 3", "طالب 4"])
    if st.session_state.stations[target_station] == "ON":
        val = random.randint(210, 380) # توليد قيمة جهد عشوائية
        timestamp = time.strftime("%H:%M:%S")
        
        # منطق الإطفاء والبروتوكول
        if val > 350:
            st.session_state.stations[target_station] = "OFF"
            st.session_state.log.append({"الوقت": timestamp, "المحطة": target_station, "القيمة": val, "الحالة": "💥 إطفاء فوري"})
        else:
            is_critical = val > 250
            if not (protocol_active and not is_critical):
                st.session_state.log.append({"الوقت": timestamp, "المحطة": target_station, "القيمة": val, "الحالة": "✅ مستقر"})

# --- الشاشة الرئيسية ---
@st.fragment(run_every=1)
def dashboard():
    # عرض حالة المحطات
    cols = st.columns(4)
    for i, (name, status) in enumerate(st.session_state.stations.items()):
        color = "green" if status == "ON" else "red"
        cols[i].markdown(f"**{name}**\n<h2 style='color:{color};'>{status}</h2>", unsafe_allow_html=True)

    st.markdown("---")
    if st.session_state.log:
        c1, c2 = st.columns([1, 1])
        with c1:
            st.subheader("📊 قراءات الحساس (Wireless Feed)")
            df = pd.DataFrame(st.session_state.log).sort_index(ascending=False)
            st.table(df.head(10))
        with c2:
            st.subheader("📈 تذبذب الشبكة اللحظي")
            st.line_chart(pd.DataFrame(st.session_state.log).set_index('الوقت')['القيمة'])
    
    # تحديث الصفحة تلقائياً إذا كان وضع الحساس يعمل
    if auto_mode:
        time.sleep(1)
        st.rerun()

dashboard()
