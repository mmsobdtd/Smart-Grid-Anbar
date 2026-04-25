import streamlit as st

# إعدادات الصفحة لضمان استجابة الموبايل والوضع العريض
st.set_page_config(
    page_title="Anbar Smart Grid",
    layout="wide",
    initial_sidebar_state="expanded"
)

# العنوان الرئيسي كما في تطبيقك الأصلي
st.title("⚡ Anbar Smart Grid")

# القسم الأول: اختيار الدور
st.subheader("🛂 اختيار الدور")
role = st.selectbox("من أنت؟", ["طالب (إدخال بيانات)", "مهندس (غرفة التحكم)"])

if role == "طالب (إدخال بيانات)":
    st.divider()
    st.header("📲 واجهة المحطة الفرعية")
    st.write("قم بتعديل حمل محطتك وسيتم تحديثه في غرفة التحكم فوراً.")
    
    # اختيار المحطة
    station = st.selectbox("اختر رقم محطتك:", ["Station 1", "Station 2", "Station 3"])
    
    # السلايدر بالقيمة 17.5 التي طلبتها
    # ملاحظة: تم استخدام use_container_width لضمان التنسيق على الموبايل
    current_amps = st.slider(
        f"تعديل تيار {station} (Amps):",
        min_value=0.0,
        max_value=600.0,
        value=17.5, # القيمة المطلوبة
        step=0.1
    )
    
    # زر الإرسال بنفس التصميم الأصلي مع جعله عريضاً للموبايل
    if st.button("إرسال البيانات إلى السيرفر", use_container_width=True):
        st.success(f"تم تحديث بيانات {station} إلى {current_amps} أمبير")

elif role == "مهندس (غرفة التحكم)":
    st.divider()
    st.header("📊 غرفة التحكم المركزية")
    st.info("هذه الواجهة مخصصة لمراقبة الشبكة وكشف السرقات.")
    
    # عرض النتائج في بطاقات (Metrics) لتكون واضحة على الموبايل
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="الحمل الحالي", value="17.5 A")
    with col2:
        st.metric(label="حالة التجاوز", value="لا يوجد", delta="✅")

    # إضافة الخريطة (اختياري حسب مشروعك)
    st.subheader("📍 موقع المحطة")
    # [span_0](start_span)إحداثيات تقريبية في الرمادي - جامعة الأنبار[span_0](end_span)
    map_data = {"lat": [33.4273], "lon": [43.3013]}
    st.map(map_data, use_container_width=True)
