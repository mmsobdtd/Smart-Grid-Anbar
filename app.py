import streamlit as st
import pandas as pd
import time

st.set_page_config(page_title="Smart Grid Stress Test", layout="wide")

@st.cache_resource
def get_shared_data():
    # سجل البيانات، عداد الضغط اللحظي، ووقت آخر إرسال
    return {"log": [], "traffic_counter": 0, "last_update": time.time()}

data = get_shared_data()

st.title("⚡ محاكاة انهيار الشبكة vs البروتوكول الذكي")

# --- لوحة التحكم الجانبية ---
st.sidebar.header("🕹️ لوحة المهندس")
protocol_on = st.sidebar.toggle("تفعيل البروتوكول (Priority Mode)", value=False)

st.sidebar.markdown("---")
user_id = st.sidebar.selectbox("المحطة:", ["طالب 1", "طالب 2", "طالب 3", "طالب 4"])
val = st.sidebar.number_input("الجهد (V):", 0, 400, 220)

if st.sidebar.button("إرسال البيانات"):
    # حساب الضغط اللحظي (Traffic Intensity)
    current_time = time.time()
    data["traffic_counter"] += 1
    
    # محاكاة الانهيار: إذا كان البروتوكول مطفأ والضغط عالي
    if not protocol_on and data["traffic_counter"] > 5:
        with st.sidebar:
            with st.spinner('⚠️ جاري معالجة الزحام... الشبكة بطيئة'):
                time.sleep(2) # تأخير متعمد لإظهار "الانهيار"
        st.sidebar.error("🚨 فشل في الاستجابة اللحظية (Network Lag)")
    
    # منطق البروتوكول
    is_critical = val > 250
    if protocol_on and not is_critical:
        st.sidebar.warning("🚫 البروتوكول رفض البيانات غير الضرورية")
    else:
        timestamp = time.strftime("%H:%M:%S")
        data["log"].append({"الوقت": timestamp, "المحطة": user_id, "القيمة": val, "الأولوية": "🚨" if is_critical else "✅"})
        st.sidebar.success("تم التمرير")

if st.sidebar.button("تصفير السجل"):
    data["log"].clear()
    data["count"] = 0
    st.rerun()

# --- التحديث التلقائي (كل 1 ثانية) ---
@st.fragment(run_every=1)
def show_dashboard():
    # تصفير عداد الضغط تدريجياً لمحاكاة هدوء الشبكة
    if data["traffic_counter"] > 0:
        data["traffic_counter"] -= 0.5 

    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📡 حالة استقرار السيرفر")
        # إظهار شريط يوضح "ضغط البيانات"
        load_level = min(data["traffic_counter"] / 10, 1.0)
        if not protocol_on:
            st.progress(load_level, text=f"ضغط الشبكة بدون بروتوكول: {int(load_level*100)}%")
            if load_level > 0.6:
                st.error("🔥 تحذير: الشبكة تقترب من الانهيار بسبب كثرة البيانات العادية!")
        else:
            st.success("💎 البروتوكول يعمل: يتم تصفية البيانات (الضغط 0%)")

        df = pd.DataFrame(data["log"]).sort_index(ascending=False)
        st.table(df.head(10))

    with col2:
        st.subheader("📈 تذبذب الجهد اللحظي")
        if data["log"]:
            chart_df = pd.DataFrame(data["log"])
            st.line_chart(chart_df.set_index('الوقت')['القيمة'])

show_dashboard()
