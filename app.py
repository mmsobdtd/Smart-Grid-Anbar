import streamlit as st
import pandas as pd
import time
import random

st.set_page_config(page_title="Smart Grid Priority Simulation", layout="wide")

# ======================
# Shared Memory
# ======================
if "data" not in st.session_state:
    st.session_state.data = []

if "network_state" not in st.session_state:
    st.session_state.network_state = "STABLE"

# ======================
# Title
# ======================
st.title("⚡ Smart Grid Load Reporting Simulation")
st.markdown("### Simulation of Network Congestion With and Without Priority Protocol")

# ======================
# User Input (Student Side)
# ======================
st.sidebar.header("📡 Student Station")

student = st.sidebar.selectbox(
    "Select Station",
    ["Station 1", "Station 2", "Station 3", "Station 4"]
)

load_type = st.sidebar.selectbox(
    "Load Type",
    [
        "Hospital (High)",
        "Water Station (Medium)",
        "Residential (Low)",
        "Lighting (Low)"
    ]
)

load_value = st.sidebar.slider("Load Value (kW)", 10, 300)

send = st.sidebar.button("📤 Send Data")

# ======================
# Priority Map
# ======================
priority_map = {
    "Hospital (High)": 1,
    "Water Station (Medium)": 2,
    "Residential (Low)": 3,
    "Lighting (Low)": 3
}

# ======================
# Send Data
# ======================
if send:
    st.session_state.data.append({
        "Station": student,
        "Load Type": load_type,
        "Priority": priority_map[load_type],
        "Load (kW)": load_value,
        "Time": time.strftime("%H:%M:%S")
    })
    st.success("Data Sent Successfully")

# ======================
# Control Panel (Professor / Control Center)
# ======================
st.subheader("🎛️ Control Center")

col1, col2 = st.columns(2)

with col1:
    if st.button("❌ Run WITHOUT Protocol (Congestion)"):
        st.session_state.network_state = "CONGESTED"

with col2:
    if st.button("✅ Run WITH Priority Protocol"):
        st.session_state.network_state = "PRIORITY"

# ======================
# Display Logic
# ======================
st.subheader("📊 Network Status")

if st.session_state.network_state == "CONGESTED":
    st.error("❌ Network Congestion Detected!")
    st.warning("All stations are sending data simultaneously.")
    time.sleep(1)
    st.error("Data Collision – Network Collapse")

elif st.session_state.network_state == "PRIORITY":
    st.success("✅ Priority Protocol Active")
    st.info("Critical loads are processed first.")

# ======================
# Data Table
# ======================
if st.session_state.data:
    df = pd.DataFrame(st.session_state.data)

    if st.session_state.network_state == "PRIORITY":
        df = df.sort_values("Priority")

    st.subheader("📑 Received Data")
    st.dataframe(df, use_container_width=True)

    # ======================
    # Graph
    # ======================
    st.subheader("📈 Load Visualization")
    st.bar_chart(df.set_index("Station")["Load (kW)"])

else:
    st.info("No data received yet.")

# ======================
# Reset
# ======================
if st.button("🔄 Reset System"):
    st.session_state.data = []
    st.session_state.network_state = "STABLE"
    st.experimental_rerun()
