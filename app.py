import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time
from datetime import datetime

# ==========================================
# 1. إعدادات الصفحة والتصميم الصناعي (Cyberpunk Theme)
# ==========================================
st.set_page_config(page_title="NVIDIA Retail OS | Digital Twin", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* تعديل الخلفية والألوان لتصميم صناعي داكن */
    .stApp { background-color: #050505; color: #e0e0e0; }
    [data-testid="stSidebar"] { background-color: #111111; border-right: 1px solid #333; }
    .stMetric { background-color: #1a1a1a; border: 1px solid #333; border-radius: 5px; padding: 10px; }
    /* تلوين العناوين */
    h1, h2, h3 { color: #00d4ff !important; font-family: 'Courier New', monospace; }
    /* تعديل الأزرار */
    .stButton>button { color: #00d4ff; border: 1px solid #00d4ff; background-color: transparent; transition: 0.3s; }
    .stButton>button:hover { background-color: #00d4ff; color: black; }
    /* تبويبات احترافية */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #1a1a1a; border-radius: 5px; color: #888; }
    .stTabs [aria-selected="true"] { background-color: #00d4ff !important; color: black !important; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. إدارة حالة النظام (Session State)
# ==========================================
if 'system_state' not in st.session_state:
    st.session_state.system_state = {
        'cart': [],
        'logs': [],
        'user_pos': np.array([[0,0,0]]), # موقع افتراضي 3D
        'active_users': 0,
        'energy_history': [10, 12, 11, 15, 14, 18], # بيانات وهمية للطاقة
        'fusion_debug': {"vision_conf": 0, "weight_stable": False, "lidar_lock": False}
    }

def add_log(message, type="info"):
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    icon = "🟢" if type == "info" else ("🔴" if type == "error" else "🟡")
    st.session_state.system_state['logs'].insert(0, f"{timestamp} | {icon} {message}")

# ==========================================
# 3. الهيدر والمؤشرات الحيوية (KPIs)
# ==========================================
st.title("🛰️ NVIDIA RETAIL OS // DIGITAL TWIN")
st.caption("نظام المحاكاة المتقدم للجيل القادم من المتاجر الذكية - جامعة الأنبار")

col_k1, col_k2, col_k3, col_k4 = st.columns(4)
col_k1.metric("SYSTEM STATUS", "ONLINE", "Latency: 12ms")
num_users = st.session_state.system_state['active_users']
col_k2.metric("ACTIVE LiDAR TARGETS", f"{num_users} Objects", f"{num_users*100/50}% Load")
current_energy = st.session_state.system_state['energy_history'][-1]
col_k3.metric("GRID POWER DRAW", f"{current_energy:.1f} kW", delta=f"{(current_energy-15):.1f} kW")
sales = sum([p['price'] for p in st.session_state.system_state['cart']])
col_k4.metric("SESSION REVENUE", f"{sales:,} IQD")

st.divider()

# ==========================================
# 4. التبويبات الرئيسية للنظام
# ==========================================
tab1, tab2, tab3 = st.tabs(["🧠 مركز القيادة (Command Center)", "🛠️ مصحح الاندماج (Sensor Fusion Debug)", "⚡ الشبكة الذكية (Smart Grid)"])

# --- TAB 1: مركز القيادة (3D Map & Logs) ---
with tab1:
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("🌐 3D Spatial Awareness (LiDAR + Depth)")
        
        # إنشاء مشهد 3D وهمي للمحل
        fig = go.Figure()
        
        # رسم الرفوف ككتل رمادية
        fig.add_trace(go.Mesh3d(x=[1, 3, 3, 1, 1, 3, 3, 1], y=[1, 1, 5, 5, 1, 1, 5, 5], z=[0, 0, 0, 0, 2, 2, 2, 2], color='gray', opacity=0.3, name='Shelf A'))
        fig.add_trace(go.Mesh3d(x=[6, 8, 8, 6, 6, 8, 8, 6], y=[1, 1, 5, 5, 1, 1, 5, 5], z=[0, 0, 0, 0, 2, 2, 2, 2], color='gray', opacity=0.3, name='Shelf B'))

        # رسم موقع الزبائن بناء على المحاكاة
        if st.session_state.system_state['active_users'] > 0:
            pos = st.session_state.system_state['user_pos']
            fig.add_trace(go.Scatter3d(x=pos[:,0], y=pos[:,1], z=pos[:,2], mode='markers', marker=dict(size=15, color='#00d4ff'), name='Tracked Person (LiDAR)'))

        fig.update_layout(
            scene=dict(
                xaxis=dict(backgroundcolor="#000000", gridcolor="#333", title="X (meters)", range=[0, 10]),
                yaxis=dict(backgroundcolor="#000000", gridcolor="#333", title="Y (meters)", range=[0, 10]),
                zaxis=dict(backgroundcolor="#000000", gridcolor="#333", title="Z (Height)", range=[0, 4]),
                aspectmode='manual', aspectratio=dict(x=1, y=1, z=0.4)
            ),
            margin=dict(l=0, r=0, b=0, t=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=450,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("📟 Live Transaction Terminal")
        
        # أزرار التحكم بالمحاكاة
        col_ctrl1, col_ctrl2 = st.columns(2)
        if col_ctrl1.button("▶️ محاكاة دخول زبون"):
            st.session_state.system_state['active_users'] = np.random.randint(1, 4)
            # إنشاء مواقع عشوائية للزبائن قرب الرفوف
            st.session_state.system_state['user_pos'] = np.random.rand(st.session_state.system_state['active_users'], 3) * [8, 4, 1.8] + [1, 1, 0]
            add_log(f"تم رصد دخول {st.session_state.system_state['active_users']} أشخاص. بدء التتبع.", "info")
            st.rerun()

        if st.session_state.system_state['active_users'] > 0:
             if col_ctrl2.button("🛒 محاكاة سحب منتج (سريع)"):
                 item_price = np.random.choice([500, 1000, 2500])
                 item_name = "منتج_" + str(np.random.randint(100,999))
                 st.session_state.system_state['cart'].append({'name': item_name, 'price': item_price})
                 # تحديث الطاقة
                 new_energy = st.session_state.system_state['energy_history'][-1] + np.random.uniform(0.5, 2.0)
                 st.session_state.system_state['energy_history'].append(new_energy)
                 add_log(f"تمت إضافة {item_name} للسلة. السعر: {item_price}", "success")
                 st.rerun()

        # عرض الفاتورة الحية
        if st.session_state.system_state['cart']:
            st.dataframe(pd.DataFrame(st.session_state.system_state['cart']), use_container_width=True, height=200)
        else:
            st.info("بانتظار عمليات شراء...")

    # سجل الأحداث أسفل التبويب
    st.subheader("📜 System Event Logs")
    log_box = st.empty()
    log_text = "\n".join(st.session_state.system_state['logs'][:5])
    log_box.code(log_text if log_text else "No events yet...", language="log")


# --- TAB 2: مصحح الاندماج الحسي (لإبهار الدكتور) ---
with tab2:
    st.subheader("🧠 Sensor Fusion Logic Analyzer")
    st.write("هذا القسم يوضح كيف يتخذ الذكاء الاصطناعي القرار بناءً على تقاطع البيانات.")
    
    col_f1, col_f2 = st.columns([1, 2])
    
    with col_f1:
        # أدوات تحكم لمحاكاة حالة الحساسات يدوياً
        st.markdown("##### 🎛️ محاكاة مدخلات الحساسات")
        vision_conf = st.slider("ثقة الكاميرا (Vision Confidence %)", 0, 100, 85)
        weight_diff = st.number_input("فرق الوزن المقاس (جرام)", -500, 500, -258)
        lidar_status = st.selectbox("حالة تتبع الـ LiDAR", ["Target Locked (داخل المنطقة)", "Target Lost (خارج المنطقة)", "Occluded (محجوب)"])
        
        expected_weight = -258 # وزن علبة بيبسي مثلاً
        weight_tolerance = 5 # السماحية بالجرام
        
        # منطق المحاكاة
        vision_pass = vision_conf > 90
        weight_pass = abs(weight_diff - expected_weight) <= weight_tolerance
        lidar_pass = lidar_status == "Target Locked (داخل المنطقة)"
        
        decision = "🔴 مرفوض (بيانات غير كافية)"
        if vision_pass and weight_pass and lidar_pass:
            decision = "🟢 مقبول (تم تأكيد الشراء)"
        elif vision_pass and lidar_pass and not weight_pass:
             decision = "🟡 تحذير (خطأ في الوزن - احتمال إرجاع خاطئ)"
        elif weight_pass and lidar_pass and not vision_pass:
             decision = "🟡 تحذير (الكاميرا غير متأكدة - يرجى المراجعة)"

    with col_f2:
        st.markdown("##### 📊 مصفوفة اتخاذ القرار (Decision Matrix)")
        
        # عرض النتائج بشكل مرئي جذاب
        col_res1, col_res2, col_res3 = st.columns(3)
        col_res1.metric("👁️ Vision AI Status", f"{vision_conf}%", delta="PASS" if vision_pass else "FAIL", delta_color="normal" if vision_pass else "inverse")
        col_res2.metric("⚖️ Weight Sensor Status", f"{weight_diff}g", delta="MATCH" if weight_pass else "MISMATCH", delta_color="normal" if weight_pass else "inverse")
        col_res3.metric("🎯 LiDAR Tracking Status", lidar_status.split(" ")[0], delta="LOCKED" if lidar_pass else "LOST", delta_color="normal" if lidar_pass else "inverse")
        
        st.divider()
        st.subheader(f"القرار النهائي للنظام: {decision}")
        
        if decision.startswith("🟢"):
             st.balloons()
        elif decision.startswith("🟡"):
             st.warning("النظام يطلب تدخلاً بشرياً أو إعادة المحاولة.")

# --- TAB 3: الشبكة الذكية (Smart Grid) ---
with tab3:
    st.subheader("⚡ Intelligent Power Management (IPM)")
    st.write("مراقبة حية لاستهلاك الطاقة بناءً على الحمل الحسابي وعدد الزبائن.")
    
    # محاكاة بيانات الطاقة
    energy_data = st.session_state.system_state['energy_history']
    # إضافة نقطة جديدة تعتمد على عدد المستخدمين لإعطاء واقعية
    base_load = 10.0
    user_load = st.session_state.system_state['active_users'] * 2.5
    current_load = base_load + user_load + np.random.uniform(-1, 1)
    
    # تحديث القائمة (نحتفظ بآخر 50 قراءة فقط)
    if len(energy_data) > 50:
        energy_data.pop(0)
    energy_data.append(current_load)
    
    # رسم بياني خطي حي
    chart_data = pd.DataFrame({"Time": range(len(energy_data)), "Power Draw (kW)": energy_data})
    st.line_chart(chart_data, x="Time", y="Power Draw (kW)", height=350)
    
    col_p1, col_p2 = st.columns(2)
    col_p1.info("ℹ️ ملاحظة هندسية: النظام مبرمج لتقليل قدرة الـ GPU بنسبة 40% عند عدم وجود زبائن لتوفير الطاقة (Eco-Mode).")
    col_p2.success(f"حالة البطاريات الاحتياطية (UPS): مشحونة 98% - تكفي لمدة 4 ساعات.")

# ==========================================
# تذييل الصفحة
# ==========================================
st.divider()
st.markdown("<div style='text-align: center; color: #666;'>© 2026 Advanced Engineering Systems - University of Anbar Project Prototype. Powered by NVIDIA & Streamlit.</div>", unsafe_allow_html=True)

# زر مخفي للتحديث التلقائي (اختياري لجعله "حي" أكثر)
# if st.checkbox("تفعيل التحديث التلقائي (كل ثانية)"):
#     time.sleep(1)
#     st.rerun()
