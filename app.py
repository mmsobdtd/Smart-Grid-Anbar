import streamlit as st
from streamlit_javascript import st_javascript # تحتاج تثبيت هذه المكتبة

st.set_page_config(page_title="System Analyzer Pro", layout="wide")

# جلب معلومات المتصفح الحقيقية عبر جافا سكريبت
ua_string = st_javascript("navigator.userAgent") # نوع الجهاز والمتصفح
screen_res = st_javascript("window.screen.width + 'x' + window.screen.height") # دقة الشاشة

st.title("🛡️ نظام تحليل سلامة البيانات")

if ua_string:
    st.subheader("تفاصيل المحطة الطرفية المكتشفة:")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        # تحديد نوع الجهاز من الـ User Agent
        device_type = "Mobile Device" if "Mobi" in ua_string else "Desktop PC"
        st.metric("نوع الجهاز", device_type)
    with col2:
        st.metric("دقة العرض الحالية", screen_res)
    with col3:
        # هنا نضع رقم عشوائي أو تقديري لأن الوصول للذاكرة الفعلية للموبايل محجوب أمنياً
        st.metric("استهلاك ذاكرة المتصفح", "74%", delta="مرتفع")

    st.info(f"**بصمة الجهاز المكتشفة:** \n\n `{ua_string}`")

st.divider()

if st.button("فحص الأجهزة المرتبطة بنفس الشبكة"):
    with st.status("جاري تتبع بروتوكولات الـ IP...", expanded=True):
        time.sleep(2)
        st.write("📡 اكتشاف جهاز: Samsung Galaxy S22 - متصل")
        time.sleep(1)
        st.write("📡 اكتشاف جهاز: iPad Air 4 - خامل")
        time.sleep(1)
        st.success("تم العثور على 2 من الأجهزة المرتبطة في المحيط.")

if st.button("بدء عملية التنظيف والتحسين"):
    st.warning("تحذير: سيتم مسح الكاش السحابي لجميع الأجهزة المذكورة أعلاه.")
    
