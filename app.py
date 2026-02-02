import streamlit as st
import pandas as pd
import time

# إعداد واجهة البرنامج
st.set_page_config(page_title="نظام الشبكة الذكية المشترك", layout="wide")

# --- وظيفة التخزين المشترك (هذه هي اللي تجعل البيانات تظهر عند الجميع) ---
@st.cache_resource
def get_shared_log():
    return []  # مصفوفة فارغة تعيش في ذاكرة السيرفر

shared_log = get_shared_log()

st.title("🔌 نظام مراقبة الشبكة الذكية (المراقبة المركزية)")

# --- بوابة إدخال الطلاب (في الجانب) ---
st.sidebar.header("بوابة إدخال البيانات")
user_id = st.sidebar.selectbox("اختر المحطة (الطالب):", ["طالب 1", "طالب 2", "طالب 3", "طالب 4"])
value = st.sidebar.number_input("أدخل قيمة الجهد (Voltage):", min_value=0, max_value=400, value=220)

if st.sidebar.button("إرسال البيانات"):
    priority = "عالية (🚨)" if value > 250 else "عادية (✅)"
    timestamp = time.strftime("%H:%M:%S")
    # إضافة البيانات للذاكرة المشتركة
    shared_log.append({
        "الوقت": timestamp,
        "المحطة": user_id,
        "القيمة": value,
        "الأولوية": priority
    })
    st.sidebar.success(f"تم الإرسال بنجاح من {user_id}")
    time.sleep(1)
    st.rerun() # تحديث الصفحة تلقائياً لرؤية البيانات الجديدة

# --- واجهة المراقبة الأساسية (شاشتك أنت) ---
if shared_log:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📊 سجل البيانات الموحد (Real-time Log)")
        # تحويل القائمة المشتركة إلى DataFrame للعرض
        df = pd.DataFrame(shared_log).sort_index(ascending=False)
        st.dataframe(df.style.highlight_max(axis=0, color='red', subset=['القيمة']), use_container_width=True)

    with col2:
        st.subheader("📈 الرسم البياني التفاعلي")
        chart_data = pd.DataFrame(shared_log)
        # رسم خط بياني لكل محطة بشكل منفصل (اختياري) أو للكل
        st.line_chart(chart_data.set_index('الوقت')['القيمة'])

    if st.button("تصفير النظام (Reset)"):
        shared_log.clear()
        st.rerun()
else:
    st.info("بانتظار دخول الطلاب وإرسال البيانات... (افتح القائمة الجانبية للإرسال)")

# إضافة زر للتحديث اليدوي
if st.button("تحديث الشاشة الآن 🔄"):
    st.rerun()
    
