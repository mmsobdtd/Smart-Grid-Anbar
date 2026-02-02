import streamlit as st
import pandas as pd
import time

# إعداد الصفحة
st.set_page_config(page_title="Smart Grid Real-time Monitor", layout="wide")

# 1. الذاكرة المشتركة للسيرفر (تبقى البيانات مخزنة طوال فترة تشغيل السيرفر)
@st.cache_resource
def get_shared_data():
    return {"log": [], "count": 0}

data = get_shared_data()

st.title("⚡ نظام مراقبة الشبكة الذكية (التحديث اللحظي: 1 ثانية) 🚀")

# --- لوحة التحكم الجانبية (ثابتة) ---
st.sidebar.header("🕹️ التحكم والإدخال")
protocol_active = st.sidebar.toggle("تفعيل بروتوكول الأولوية", value=True)

st.sidebar.markdown("---")
st.sidebar.subheader("📥 إدخال بيانات الطالب")
user_id = st.sidebar.selectbox("المحطة:", ["طالب 1", "طالب 2", "طالب 3", "طالب 4"])
val = st.sidebar.number_input("الجهد (V):", 0, 400, 220)

if st.sidebar.button("إرسال البيانات"):
    data["count"] += 1
    is_critical = val > 250
    
    if protocol_active and not is_critical:
        st.sidebar.warning("⚠️ البروتوكول حجب البيانات العادية")
    else:
        timestamp = time.strftime("%H:%M:%S")
        priority = "🚨 عالية" if is_critical else "✅ عادية"
        data["log"].append({"الوقت": timestamp, "المحطة": user_id, "القيمة": val, "الأولوية": priority})
        st.sidebar.success("تم التمرير!")

if st.sidebar.button("تصفير السجل"):
    data["log"].clear()
    data["count"] = 0
    st.rerun()

# --- 2. سحر التحديث اللحظي (Fragment) ---
# قمنا بضبط التحديث ليكون كل ثانية واحدة فقط (run_every=1)
@st.fragment(run_every=1)
def display_dashboard():
    # عرض الوقت الحالي للتأكد من سرعة التحديث
    st.markdown(f"**توقيت السيرفر اللحظي:** {time.strftime('%H:%M:%S')}")
    
    if data["log"]:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📡 سجل البيانات المركزي")
            df = pd.DataFrame(data["log"]).sort_index(ascending=False)
            # عرض آخر 10 قراءات فقط لضمان سرعة التحميل
            st.table(df.head(10))
            
        with col2:
            st.subheader("📈 الرسم البياني اللحظي")
            chart_df = pd.DataFrame(data["log"])
            st.line_chart(chart_df.set_index('الوقت')['القيمة'])
    else:
        st.info("بانتظار البيانات... الشاشة تتحدث تلقائياً كل ثانية.")

# استدعاء دالة العرض
display_dashboard()
