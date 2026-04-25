import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

# ==========================================
# 1. الإعدادات العامة والتنسيق الصناعي (CSS)
# ==========================================
st.set_page_config(page_title="Al-Anbar Advanced Grid SCADA v4.0", layout="wide")

st.markdown("""
    <style>
    .reportview-container { background: #0e1117; }
    .stMetric { background-color: #1a1c24; padding: 15px; border-radius: 10px; border: 1px solid #3e4451; }
    .main-header { font-size: 38px; color: #00d4ff; font-weight: bold; text-align: center; text-shadow: 2px 2px #000; }
    .sidebar-title { color: #00d4ff; font-size: 20px; font-weight: bold; }
    .log-container { background-color: #000; color: #0f0; padding: 10px; font-family: 'Courier New', monospace; height: 250px; overflow-y: scroll; border: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. المحرك الهندسي (Engineering Logic Classes)
# ==========================================

class GridComponent:
    """الفئة الأساسية لمكونات الشبكة"""
    def __init__(self, name, id):
        self.name = name
        self.id = id
        self.status = "ONLINE"

class Transformer(GridComponent):
    """تمثيل المحولة الكهربائية مع حسابات الكفاءة والحرارة"""
    def __init__(self, name, id, capacity_kva=250):
        super().__init__(name, id)
        self.capacity = capacity_kva
        self.temperature = 45.0
        self.cooling_status = "AUTO"
        self.frequency = 50.0 # 50Hz Standard for Iraq

    def calculate_thermal_stress(self, current_load_a):
        # محاكاة ارتفاع الحرارة بناءً على الحمل (الخسائر النحاسية)
        stress_factor = (current_load_a / 150)**2
        self.temperature += (stress_factor * 0.5) - 0.1 # تبريد بسيط مستمر
        self.temperature = max(30, min(self.temperature, 120))
        return self.temperature

class Consumer:
    """تمثيل المستهلك (البيت) مع العداد الذكي"""
    def __init__(self, house_id, base_load):
        self.id = house_id
        self.base_load = base_load
        self.is_connected = True
        self.smart_meter_reading = 0.0

    def get_real_consumption(self):
        return self.base_load + np.random.uniform(-2, 2) if self.is_connected else 0

class PowerGridManager:
    """العقل المدبر للمنظومة - SCADA Master Node"""
    def __init__(self):
        self.transformer = Transformer("محطة الرمادي الرئيسية", "TX-01")
        self.consumers = [Consumer(f"بيت {i}", np.random.randint(10, 25)) for i in range(1, 11)]
        self.line_resistance = 0.02 # Ohm per segment
        self.theft_active = False
        self.theft_location = None
        self.theft_current = 0.0

    def run_load_flow(self):
        """محاكاة تدفق الأحمال وحساب الفواقد وهبوط الجهد"""
        total_legal_i = sum([c.get_real_consumption() for c in self.consumers])
        actual_i_out = total_legal_i + (self.theft_current if self.theft_active else 0)
        
        # قانون أوم: V_drop = I * R
        v_drop = actual_i_out * self.line_resistance * len(self.consumers)
        v_final = 225 - v_drop
        
        # كفاءة الشبكة
        efficiency = (total_legal_i / actual_i_out) * 100 if actual_i_out > 0 else 100
        
        return {
            "total_i": actual_i_out,
            "legal_i": total_legal_i,
            "v_out": v_final,
            "efficiency": efficiency,
            "loss_i": actual_i_out - total_legal_i
        }

# ==========================================
# 3. إدارة الجلسة والبيانات (Session Management)
# ==========================================
if 'grid' not in st.session_state:
    st.session_state.grid = PowerGridManager()
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["Time", "Voltage", "Total_I", "Theft_I", "Temp"])
if 'logs' not in st.session_state:
    st.session_state.logs = []

def add_log(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.insert(0, f"[{timestamp}] >> {msg}")

# ==========================================
# 4. واجهة المستخدم الرسومية (Advanced UI)
# ==========================================

st.markdown("<div class='main-header'>Al-Anbar Smart Grid | SCADA System v4.0</div>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#888;'>نظام التحكم والإشراف الذكي - جامعة الأنبار - قسم الهندسة الكهربائية</p>", unsafe_allow_html=True)

# القائمة الجانبية المتقدمة
with st.sidebar:
    st.markdown("<div class='sidebar-title'>⚙️ Control Panel</div>", unsafe_allow_html=True)
    
    # محاكاة التحكم في الشبكة
    mode = st.selectbox("Operation Mode", ["Normal", "Peak Load", "Emergency", "Maintenance"])
    
    st.divider()
    st.markdown("⚠️ **Simulation Injector**")
    inject_theft = st.toggle("Inject Power Theft (🪝 تجاوز عشوائي)")
    if inject_theft:
        st.session_state.grid.theft_active = True
        st.session_state.grid.theft_current = st.slider("Theft Current (A)", 10, 100, 45)
        st.session_state.grid.theft_location = st.selectbox("Target Node", [f"Node {i}" for i in range(1, 6)])
    else:
        st.session_state.grid.theft_active = False
        st.session_state.grid.theft_current = 0

    st.divider()
    if st.button("🚀 Execute Data Refresh", use_container_width=True):
        st.rerun()

# --- الحسابات والنتائج اللحظية ---
res = st.session_state.grid.run_load_flow()
temp = st.session_state.grid.transformer.calculate_thermal_stress(res['total_i'])

# عرض المقاييس الرئيسية بتصميم Card
m1, m2, m3, m4 = st.columns(4)
m1.metric("Output Voltage", f"{res['v_out']:.1f} V", delta=f"{res['v_out']-220:.1f}V", delta_color="normal")
m2.metric("Total Line Current", f"{res['total_i']:.1f} A")
m3.metric("Grid Efficiency", f"{res['efficiency']:.1f} %", delta=f"{res['efficiency']-95:.1f}%")
m4.metric("Core Temp", f"{temp:.1f} °C", delta=f"{temp-60:.1f}°C", delta_color="inverse")

st.divider()

# --- تبويبات المنظومة (The Multi-Tab System) ---
tab_viz, tab_analysis, tab_financial, tab_security = st.tabs([
    "🌐 Network Visualization", "📈 Engineering Analysis", "💰 Economic Impact", "🛡️ Cyber & Protection"
])

with tab_viz:
    st.subheader("📍 Live Power Flow Map")
    # تمثيل مرئي للشبكة باستخدام الرسم البياني
    cols = st.columns(6)
    with cols[0]:
        st.info("🏢 TX-01\n(Transformer)")
    for i in range(1, 5):
        with cols[i]:
            is_node_stolen = (inject_theft and f"Node {i}" == st.session_state.grid.theft_location)
            if is_node_stolen:
                st.error(f"🗼 Node {i}\nALERT: THEFT")
                add_log(f"CRITICAL: Deviation detected at Node {i} - Loss: {res['loss_i']:.1f}A")
            else:
                st.success(f"🗼 Node {i}\nNormal Flow")
    with cols[5]:
        st.write("🏁 End of Line")
    
    st.progress(res['total_i']/200, text=f"Total Feeder Capacity Usage: {int((res['total_i']/200)*100)}%")

with tab_analysis:
    st.subheader("📊 Advanced Signal Analysis")
    
    # محاكاة سجل البيانات للرسم
    new_data = pd.DataFrame({
        "Time": [datetime.now()],
        "Voltage": [res['v_out']],
        "Total_I": [res['total_i']],
        "Theft_I": [res['loss_i']],
        "Temp": [temp]
    })
    st.session_state.history = pd.concat([st.session_state.history, new_data]).tail(30)
    
    # رسم بياني متقدم باستخدام Plotly
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=st.session_state.history['Time'], y=st.session_state.history['Voltage'], name='Line Voltage (V)', line=dict(color='#00d4ff')))
    fig.add_trace(go.Scatter(x=st.session_state.history['Time'], y=st.session_state.history['Total_I'], name='Total Amps (A)', line=dict(color='#ff4b4b')))
    fig.update_layout(template="plotly_dark", height=400, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

with tab_financial:
    st.subheader("💰 Loss & Revenue Analysis")
    col_f1, col_f2 = st.columns(2)
    
    # حساب الخسائر بالدينار العراقي (IQD)
    # بافتراض سعر الكيلو واط ساعة 50 دينار
    power_loss_kw = (res['v_out'] * res['loss_i'] * 0.9) / 1000
    hourly_money_loss = power_loss_kw * 50
    
    with col_f1:
        st.metric("Power Loss (kW)", f"{power_loss_kw:.2f} kW")
        st.write(f"تكلفة الطاقة الضائعة حالياً: **{hourly_money_loss:,.0f} دينار/ساعة**")
    
    with col_f2:
        annual_projection = hourly_money_loss * 24 * 365
        st.metric("Annual Financial Leakage", f"{annual_projection:,.0f} IQD")
        st.warning("⚠️ هذه الخسائر تؤثر مباشرة على ميزانية الصيانة في محافظة الأنبار.")

with tab_security:
    st.subheader("🛡️ IoT Security & Protection Relay")
    col_s1, col_s2 = st.columns(2)
    
    with col_s1:
        st.write("🔒 **Data Integrity Check**")
        st.code("""
        def validate_packet(packet):
            checksum = calculate_crc32(packet)
            if checksum == packet.received_crc:
                return "VALID_DATA"
            else:
                return "INJECTION_ATTACK_DETECTED"
        """)
        st.write("الحالة: **Packet Integrity Verified ✅**")
        
    with col_s2:
        st.write("🚨 **Automatic Protection (Relay)**")
        if res['total_i'] > 180:
            st.error("PROTECTION TRIP: Overcurrent Detected!")
            add_log("RELAY TRIP: Circuit breaker opened due to overcurrent.")
        else:
            st.success("RELAY STATUS: Armed & Healthy")

# --- السجل التقني السفلي (The Matrix Style Log) ---
st.divider()
st.subheader("📡 SCADA System Logs (Real-time)")
log_html = "".join([f"<div>{l}</div>" for l in st.session_state.logs[:10]])
st.markdown(f"<div class='log-container'>{log_html}</div>", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown(f"**System Status:** Running | **Master Node:** University of Anbar Lab | **Engineer:** Mohammed Nabeel | **Current Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
