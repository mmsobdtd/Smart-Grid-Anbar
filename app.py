import streamlit as st
import time

# إعدادات الصفحة
st.set_page_config(page_title="مدير ملفات النظام", page_icon="🛡️")

# --- التصحيح هنا: أضفنا st. قبل session_state ---
if 'view_files' not in st.session_state:
    st.session_state.view_files = False
if 'deleted' not in st.session_state:
    st.session_state.deleted = False
# ---------------------------------------------

st.title("🛡️ نظام الحماية السحابي")
st.write("مرحباً بك. يرجى فحص ملفات الجهاز لضمان الأمان.")

if not st.session_state.view_files:
    if st.button("فحص ملفات الصور بالجهاز"):
        st.session_state.view_files = True
        st.rerun()

if st.session_state.view_files and not st.session_state.deleted:
    st.divider()
    st.subheader("📁 الصور المكتشفة في الذاكرة المؤقتة:")
    
    fake_files = [
        "IMG_2024_001.jpg", "DCIM_Camera_Capture.png", 
        "Personal_Photo_01.jpeg", "WhatsApp_Images_Backup.zip",
        "ScreenShot_2026_05_04.png", "Family_Trip_2023.jpg"
    ]
    
    for file in fake_files:
        st.text(f"📄 {file} (حجم: 2.4 MB)")

    st.warning("تحذير: تم اكتشاف مزامنة نشطة مع أجهزة أخرى.")
    
    if st.button("حذف كافة الصور من جميع الأجهزة"):
        with st.spinner('جاري الحذف وتطهير السحابة...'):
            progress_bar = st.progress(0)
            for percent_complete in range(100):
                time.sleep(0.03)
                progress_bar.progress(percent_complete + 1)
        
        st.session_state.deleted = True
        st.rerun()

if st.session_state.deleted:
    st.divider()
    st.success("✅ تم حذف الصور بنجاح من هذا الجهاز ومن جميع الأجهزة الأخرى المرتبطة.")
    st.balloons()
    
    if st.button("العودة للرئيسية"):
        st.session_state.view_files = False
        st.session_state.deleted = False
        st.rerun()
        
