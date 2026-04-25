import streamlit as st
import requests

# 1. إعدادات الصفحة لتناسب الموبايل والشاشات العريضة
st.set_page_config(
    page_title="Anbar Smart Grid",
    layout="wide",  # استغلال كامل عرض الشاشة
    initial_sidebar_state="collapsed"  # إخفاء القائمة الجانبية تلقائياً في الموبايل
)

# تحسين المظهر باستخدام CSS مخصص للموبايل
st.markdown("""
    <style>
    .main {
        padding: 10px;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #ddd;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. إعدادات الحالة (Session State) لمنع فقدان البيانات عند التحديث
if 'current_value' not in st.session_state:
    st.session_state.current_value = 17.5  # القيمة التي طلبتها كبداية

# 3. تقسيم الواجهة باستخدام "الألسنة" (Tabs) - الأفضل للموبايل
tab1, tab2 = st.tabs(["📲 واجهة المحطة", "📊 غرفة التحكم"])

with tab1:
    st.header("📲 واجهة المحطة الفرعية")
    st.info("قم بتعديل حمل محطتك وسيتم تحديثه في غرفة التحكم فوراً.")
    
    # استخدام حاوية منظمة
    with st.container():
        station_num = st.selectbox("اختر رقم محطتك:", ["Station 1", "Station 2", "Station 3"])
        
        # السلايدر مع القيمة 17.5 التي طلبتها
        amps = st.slider(
            f"تعديل تيار {station_num} (Amps):", 
            min_value=0.0, 
            max_value=600.0, 
            value=float(st.session_state.current_value),
            step=0.5
        )
        
        if st.button("إرسال البيانات إلى السيرفر", use_container_width=True):
            st.session_state.current_value = amps
            st.success(f"تم إرسال القيمة {amps} أمبير بنجاح!")

with tab2:
    st.header("📊 غرفة التحكم (SCADA)")
    
    # عرض الأرقام بشكل بارز (Metric) - واضحة جداً على الموبايل
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="التيار الحالي", value=f"{st.session_state.current_value} A")
    with col2:
        # نظام كشف السرقة بناءً على القيمة 17.5
        status = "⚠️ تجاوز/سرقة" if st.session_state.current_value > 500 else "✅ مستقر"
        st.metric(label="حالة الشبكة", value=status)

    st.divider()
    
    # عرض الخريطة مع تفعيل خاصية التمدد لتناسب الموبايل
    st.subheader("📍 الموقع الجغرافي للخلل")
    # إحداثيات افتراضية في الرمادي (الأنبار)
    map_data = {"lat": [33.4273], "lon": [43.3013]} 
    st.map(map_data, use_container_width=True)

    # زر الملاحة المباشر لخرائط جوجل
    google_maps_link = f"https://www.google.com/maps?q=33.4273,43.3013"
    st.link_button("فتح الموقع في خرائط جوجل 🌍", google_maps_link, use_container_width=True)

# 4. وظيفة إرسال التنبيه (مثال مبسط لتيليجرام)
def send_alert(value):
    # هنا تضع توكن البوت الخاص بك كما في تقريرك
    # requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={...})
    pass
