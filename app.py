import streamlit as st
import pandas as pd
import time

# إعداد واجهة البرنامج
st.set_page_config(page_title="Smart Grid Monitor", layout="wide")
st.title("🔌 نظام مراقبة الشبكة الذكية (4 محطات)")

# مصفوفة لتخزين البيانات
if 'data_log' not in st.session_state:
    st.session_state.data_log = []

# --- بوابة إدخال الطلاب ---
st.sidebar.header("بوابة إدخال البيانات")
user_id = st.sidebar.selectbox("اختر المحطة (الطالب):", ["طالب 1", "طالب 2", "طالب 3", "طالب 4"])
value = st.sidebar.number_input("أدخل قيمة الجهد (Voltage):", min_value=0, max_value=400, value=220)

if st.sidebar.button("إرسال البيانات"):
    priority = "عالية (🚨)" if value > 250 else "عادية (✅)"
    timestamp = time.strftime("%H:%M:%S")
    st.session_state.data_log.append({"الوقت": timestamp, "المحطة": user_id, "القيمة": value, "الأولوية": priority})
    st.sidebar.success(f"تم الإرسال بنجاح من {user_id}")

# --- عرض النتائج ---
col1, col2 = st.columns([1, 1])
with col1:
    st.subheader("📊 سجل البيانات")
    if st.session_state.data_log:
        df = pd.DataFrame(st.session_state.data_log).sort_index(ascending=False)
        st.dataframe(df.style.highlight_max(axis=0, color='red', subset=['القيمة']))
with col2:
    st.subheader("📈 الرسم البياني اللحظي")
    if st.session_state.data_log:
        chart_data = pd.DataFrame(st.session_state.data_log)
        st.line_chart(chart_data.set_index('الوقت')['القيمة'])
      
