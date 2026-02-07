import streamlit as st
import pandas as pd
import time

# إعدادات الصفحة
st.set_page_config(page_title="Smart Grid Monitoring - Anbar University", layout="wide")

st.title("⚡ نظام مراقبة الشبكة الذكية (محاكاة البروتوكول)")
st.write("قسم الهندسة الكهربائية - جامعة الأنبار")

# تعريف الثوابت (المعايير الهندسية)
HIGH_THRESHOLD = 300 # $I > 300\text{ A}$ أولوية قصوى
NORMAL_THRESHOLD = 250 # $I < 250\text{ A}$ حالة طبيعية

# تفعيل أو تعطيل البروتوكول
protocol_active = st.sidebar.toggle("تفعيل بروتوكول الأولوية (Protocol Mode)", value=False)

st.sidebar.markdown("---")
st.sidebar.info("بدون بروتوكول: تظهر البيانات بترتيب وصولها العشوائي فقط.\n\nمع البروتوكول: يتم فرز المحطات حسب خطورة الحمل.")

# واجهة إدخال البيانات للطلاب الأربعة
st.subheader("📥 إدخال بيانات المحطات (طلاب)")
col1, col2, col3, col4 = st.columns(4)

with col1:
    s1 = st.number_input("محطة 1 (Amps)", min_value=0, value=200, key="st1")
with col2:
    s2 = st.number_input("محطة 2 (Amps)", min_value=0, value=200, key="st2")
with col3:
    s3 = st.number_input("محطة 3 (Amps)", min_value=0, value=200, key="st3")
with col4:
    s4 = st.number_input("محطة 4 (Amps)", min_value=0, value=200, key="st4")

data = [
    {"Station": "Station 1", "Current": s1},
    {"Station": "Station 2", "Current": s2},
    {"Station": "Station 3", "Current": s3},
    {"Station": "Station 4", "Current": s4},
]

df = pd.DataFrame(data)

# منطق المعالجة (البروتوكول)
st.divider()

if not protocol_active:
    st.warning("⚠️ الوضع الحالي: بدون بروتوكول (البيانات خام وغير منظمة)")
    st.table(df) # عرض البيانات كما هي بدون معالجة
else:
    st.success("✅ الوضع الحالي: بروتوكول الأولوية نشط")
    
    # تصنيف البيانات وإعطاء الأولوية
    def assign_priority(current):
        if current >= HIGH_THRESHOLD:
            return "🔴 HIGH PRIORITY (Overload)"
        elif current <= NORMAL_THRESHOLD:
            return "🟢 Normal (Low Load)"
        else:
            return "🟡 Stable"

    df['Status'] = df['Current'].apply(assign_priority)
    
    # فرز الجدول بحيث تظهر "الأولوية القصوى" في الأعلى دائماً
    df = df.sort_values(by="Current", ascending=False)
    
    # عرض النتائج بشكل احترافي
    st.dataframe(df.style.apply(lambda x: ['background-color: #ff4b4b' if 'HIGH' in str(v) else '' for v in x], axis=1), use_container_width=True)

    # إشارات البروتوكول (Alerts)
    for index, row in df.iterrows():
        if row['Current'] >= HIGH_THRESHOLD:
            st.error(f"🚨 إنذار من {row['Station']}: تم اكتشاف حمل زائد ({row['Current']}A) - جاري تحويل الطاقة!")
            
