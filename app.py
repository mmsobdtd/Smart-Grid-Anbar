import streamlit as st
import pandas as pd
import time
import random

# إعداد الصفحة لتكون عريضة واحترافية
st.set_page_config(page_title="Ultra-Smooth Smart Grid Monitor", layout="wide")

# 1. تهيئة الذاكرة المشتركة
if 'shared_log' not in st.session_state:
    st.session_state.shared_log = []
if 'traffic_load' not in st.session_state:
    st.session_state.traffic_load = 0

st.title("🔌 نظام مراقبة الشبكة الذكية (التحديث السلس)")

# --- الجانب: لوحة التحكم والإدخال ---
st.sidebar.header("🕹️ التحكم")
protocol_active = st.sidebar.toggle("تفعيل البروتوكول الذكي", value=False)

st.sidebar.markdown("---")
user_id = st.sidebar.selectbox("المحطة:", ["طالب 1", "طالب 2", "طالب 3", "طالب 4"])
val = st.sidebar.number_input("الجهد (V):", 0, 400, 220)

if st.sidebar.button("إرسال البيانات"):
    st.session_state.traffic_load += 1
    is_critical = val > 250
    
    # محاكاة الانهيار (ثقل في الاستجابة)
    if not protocol_active and st.session_state.traffic_load > 4:
        with st.sidebar:
            with st.spinner('⚠️ الشبكة مزدحمة...'):
                time.sleep(1.5) # Lag متعمد
        st.sidebar.error("🚨 تأخير في الاستجابة (Network Congestion)")

    if protocol_active and not is_critical:
        st.sidebar.warning("🚫 تم حجب البيانات العادية")
    else:
        new_data = {"الوقت": time.strftime("%H:%M:%S"), "المحطة": user_id, "القيمة": val, "الأولوية": "🚨" if is_critical else "✅"}
        st.session_state.shared_log.append(new_data)
        st.sidebar.success("تم التمرير بنجاح")

# --- المنطقة الرئيسية: التحديث السلس جداً ---
# استخدام Containers فارغة لتحديث محتواها بدون إعادة تحميل الصفحة
placeholder_metrics = st.empty()
placeholder_chart = st.empty()
placeholder_table = st.empty()

# حلقة التحديث السلس (تعمل باستمرار لتحديث الواجهة)
while True:
    # تقليل ضغط الشبكة الوهمي تدريجياً
    if st.session_state.traffic_load > 0:
        st.session_state.traffic_load -= 0.1

    with placeholder_metrics.container():
        col1, col2 = st.columns(2)
        # إظهار مؤشر الضغط بشكل احترافي
        load = min(st.session_state.traffic_load / 10, 1.0)
        status_color = "inverse" if load > 0.6 and not protocol_active else "normal"
        col1.metric("ضغط البيانات الحالي", f"{int(load*100)}%", delta="- سلس" if protocol_active else "+ زحام")
        col2.metric("حالة البروتوكول", "نشط ✅" if protocol_active else "متوقف ❌")

    with placeholder_chart.container():
        if st.session_state.shared_log:
            df = pd.DataFrame(st.session_state.shared_log)
            # الرسم البياني السلس
            st.line_chart(df.set_index('الوقت')['القيمة'], height=250)
        else:
            st.info("بانتظار البيانات... الشاشة تتحدث بتردد عالٍ الآن.")

    with placeholder_table.container():
        if st.session_state.shared_log:
            st.subheader("📊 سجل البيانات الأخير")
            df_table = pd.DataFrame(st.session_state.shared_log).sort_index(ascending=False)
            st.table(df_table.head(5))

    # التوقف لجزء بسيط جداً من الثانية لجعل الحركة "سلسة"
    time.sleep(0.5) 
