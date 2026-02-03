import streamlit as st
import pandas as pd
import time
import random

st.set_page_config(page_title="Smart Grid Automatic Simulation", layout="wide")

# ======================
# Session State
# ======================
if "data" not in st.session_state:
    st.session_state.data = []

if "protocol" not in st.session_state:
    st.session_state.protocol = True

if "running" not in st.session_state:
    st.session_state.running = False

# ======================
# Stations & Priorities
# ======================
stations = {
    "طالب 1 (Hospital)": 1,
    "طالب 2 (Water)": 2,
    "طالب 3 (Residential)": 3,
    "طالب 4 (Lighting)": 3
}

# ======================
# Title
# ======================
st.title("⚡ Smart Grid Automatic Load Simulation")
st.markdown("### 4 Stations – Automatic Data Generation")

# ======================
# Control Panel
# ======================
st.sidebar.header("🎛️ Control Panel")

st.session_state.protocol = st.sidebar.toggle("تفعيل بروتوكول الأولوية", value=True)

start = st.sidebar.button("▶ تشغيل المحاكاة")
stop = st.sidebar.button("⏹ إيقاف المحاكاة")
reset = st.sidebar.button("🔄 تصفير النظام")

if start:
    st.session_state.running = True

if stop:
    st.session_state.running = False

if reset:
    st.session_state.running = False
    st.session_state.data = []
    st.experimental_rerun()

# ======================
# Network Status
# ======================
st.subheader("📡 حالة الشبكة")

if st.session_state.protocol:
    st.success("✅ بروتوكول الأولوية نشط")
else:
    st.error("❌ بدون بروتوكول – الشبكة معرضة للانهيار")

# ======================
# Automatic Data Generator
# ======================
if st.session_state.running:
    for station, priority in stations.items():
        voltage = random.randint(180, 420)

        st.session_state.data.append({
            "الوقت": time.strftime("%H:%M:%S"),
            "المحطة": station,
            "القيمة (V)": voltage,
            "الأولوية": priority
        })

    time.sleep(1)
    st.experimental_rerun()

# ======================
# Display Data
# ======================
if st.session_state.data:
    df = pd.DataFrame(st.session_state.data)

    if st.session_state.protocol:
        df = df.sort_values("الأولوية")

    # Network Congestion Simulation
    st.subheader("📊 سجل البيانات")

    if not st.session_state.protocol and len(df) > 8:
        st.error("🚨 Network Congestion Detected!")
        st.warning("تضارب بيانات بسبب الإرسال المتزامن")
    else:
        st.dataframe(df.tail(12), use_container_width=True)

    # ======================
    # Graph
    # ======================
    st.subheader("📈 الرسم البياني اللحظي للجهد")
    st.line_chart(df.set_index("الوقت")["القيمة (V)"])

else:
    st.info("لا توجد بيانات بعد")
