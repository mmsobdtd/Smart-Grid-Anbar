import streamlit as st
import pandas as pd
import time

st.set_page_config(page_title="Smart Grid Stress Test", layout="wide")

# الذاكرة المشتركة
@st.cache_resource
def get_shared_data():
    return {"log": [], "count": 0}

data = get_shared_data()

st.title("⚡ نظام إدارة الأحمال والبروتوكولات الذكية")

# --- لوحة التحكم الخاصة بك (المدير) ---
st.sidebar.header("🕹️ لوحة تحكم المهندس")
protocol_active = st.sidebar.toggle("تفعيل بروتوكول الأولوية (Priority Protocol)", value=False)
clear_btn = st.sidebar.button("تصفير النظام")

if clear_btn:
    data["log"].clear()
    data["count"] = 0
    st.rerun()

# --- واجهة إدخال الطلاب ---
st.sidebar.markdown("---")
st.sidebar.subheader("📥 بوابة إدخال الطالب")
user_id = st.sidebar.selectbox("المحطة:", ["طالب 1", "طالب 2", "طالب 3", "طالب 4"])
val = st.sidebar.number_input("الجهد (V):", 0, 400, 220)

if st.sidebar.button("إرسال الآن"):
    data["count"] += 1  # زيادة عداد المحاولات (الضغط)
    
    # منطق البروتوكول
    is_critical = val > 250
    
    if protocol_active and not is_critical:
        st.sidebar.warning("⚠️ البروتوكول رفض البيانات العادية لتقليل ضغط الشبكة")
    else:
        timestamp = time.strftime("%H:%M:%S")
        priority = "🚨 عالية" if is_critical else "✅ عادية"
        data["log"].append({"الوقت": timestamp, "المحطة": user_id, "القيمة": val, "الأولوية": priority})
        st.sidebar.success("تم تمرير البيانات بنجاح")
        st.rerun()

# --- شاشة العرض الأساسية (المقارنة) ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📡 حالة الشبكة (Network Status)")
    traffic_load = data["count"]
    
    # إظهار مؤشر الضغط
    if traffic_load > 10 and not protocol_active:
        st.error(f"⚠️ حالة انهيار: ضغط بيانات عالٍ ({traffic_load} طلبات) بدون بروتوكول!")
    elif protocol_active:
        st.success(f"💎 الشبكة مستقرة: البروتوكول ينظم المرور ({len(data['log'])} بيانات مقبولة)")
    else:
        st.info(f"الضغط الحالي: {traffic_load} طلبات")

    if data["log"]:
        df = pd.DataFrame(data["log"]).sort_index(ascending=False)
        st.table(df) # استخدام Table بدل DataFrame ليظهر بشكل أوضح في العرض

with col2:
    st.subheader("📈 مراقبة الاستقرار")
    if data["log"]:
        chart_df = pd.DataFrame(data["log"])
        st.line_chart(chart_df.set_index('الوقت')['القيمة'])

if st.button("تحديث يدوي 🔄"):
    st.rerun()
    
