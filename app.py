import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time

# --- إعدادات الواجهة الاحترافية ---
st.set_page_config(page_title="Visionary Store OS", layout="wide", initial_sidebar_state="expanded")

# CSS لإضفاء طابع تقني فخم
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 10px; border: 1px solid #3b82f6; }
    </style>
    """, unsafe_allow_html=True)

# --- محاكاة قاعدة البيانات الحية ---
if 'db' not in st.session_state:
    st.session_state.db = {
        'cart': [],
        'energy_usage': [15.2],
        'active_users': 0,
        'lidar_points': np.random.rand(10, 2) * 10
    }

# --- Sidebar: لوحة التحكم بالنظام ---
with st.sidebar:
    st.title("🛡️ System Kernel")
    st.status("NVIDIA Orin: ONLINE", state="complete")
    st.status("LiDAR Scanner: ACTIVE", state="complete")
    st.divider()
    
    option = st.selectbox("اختر وضع المحاكاة", ["تسوق فردي", "تسوق مجموعة (بطاقة واحدة)", "حالة اشتباه سرقة"])
    st.slider("دقة معالجة الـ LiDAR (%)", 90, 100, 99)
    
    if st.button("🔄 إعادة ضبط النظام"):
        st.session_state.db['cart'] = []
        st.rerun()

# --- الجزء العلوي: المقاييس الحيوية (Smart Grid & Revenue) ---
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    st.metric("المستهلكون حالياً", f"{st.session_state.db['active_users']} شخص")
with col_m2:
    energy = st.session_state.db['energy_usage'][-1]
    st.metric("استهلاك الطاقة (Smart Grid)", f"{energy} kWh", "+0.2%")
with col_m3:
    st.metric("دقة التعرف (AI Precision)", "99.8%")
with col_m4:
    total_sales = sum(item['price'] for item in st.session_state.db['cart'])
    st.metric("مبيعات الجلسة الحالية", f"{total_sales} د.ع")

st.divider()

# --- الجسم الرئيسي: LiDAR و الرؤية الحاسوبية ---
c1, c2 = st.columns([1.5, 1])

with c1:
    st.subheader("🌐 خريطة التتبع الرقمية (4D LiDAR Scan)")
    
    # محاكاة حركة الأشخاص باستخدام Plotly
    fig = go.Figure()
    # نقاط تمثل الرفوف
    fig.add_trace(go.Scatter(x=[2, 8, 2, 8], y=[2, 2, 8, 8], mode='markers', 
                             marker=dict(size=40, color='gray', symbol='square'), name='Shelves'))
    # نقاط تمثل الأشخاص (LiDAR)
    if st.session_state.db['active_users'] > 0:
        pos = st.session_state.db['lidar_points']
        fig.add_trace(go.Scatter(x=pos[:,0], y=pos[:,1], mode='markers+text', 
                                 text=["User"]*len(pos), marker=dict(size=15, color='red'), name='Live Person'))
    
    fig.update_layout(template="plotly_dark", height=400, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("📸 تحليل الكاميرا (Computer Vision)")
    event_log = st.empty()
    
    if st.button("🏃 محاكاة دخول زبائن"):
        st.session_state.db['active_users'] = 2 if "مجموعة" in option else 1
        st.session_state.db['lidar_points'] = np.random.rand(st.session_state.db['active_users'], 2) * 10
        event_log.info("🔔 تنبيه: تم رصد دخول جديد - ربط مع الماستر كارد...")
        time.sleep(1)
        st.rerun()

    if st.session_state.db['active_users'] > 0:
        if st.button("🤏 محاكاة سحب منتج"):
            with st.spinner("Sensor Fusion Process..."):
                time.sleep(1)
                new_item = {"Product": "بيبسي", "Price": 500, "Time": time.strftime("%H:%M:%S")}
                st.session_state.db['cart'].append({"name": "بيبسي", "price": 500})
                st.toast("✅ تم التأكد: الكاميرا + حساس الوزن متطابقان", icon='⚖️')
            st.rerun()

# --- أسفل الشاشة: جدول البيانات الضخمة ---
st.subheader("📊 سجل العمليات الفوري (Transaction Logs)")
if st.session_state.db['cart']:
    df = pd.DataFrame(st.session_state.db['cart'])
    st.dataframe(df, use_container_width=True)
else:
    st.info("في انتظار رصد أول عملية تسوق...")

# --- تذييل الصفحة للمناقشة مع الدكتور ---
st.divider()
st.caption(f"تم تطوير هذا النظام لمحاكاة بيئة {option} في جامعة الأنبار - قسم الكهرباء. جميع الحقوق محفوظة للمهندس محمد نبيل.")
    
