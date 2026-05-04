import streamlit as st
import time
import random

# إعداد الصفحة لتبدو احترافية
st.set_page_config(page_title="TERMINAL: ACCESS RESTRICTED", page_icon="☣️", layout="centered")

# القوالب الجمالية (CSS بسيط لجعل الخط يبدو كأنه Terminal)
st.markdown("""
    <style>
    .reportview-container {
        background: #0e1117;
    }
    .stCodeBlock {
        background-color: #002b36 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# إدارة مراحل التطبيق
if 'stage' not in st.session_state:
    st.session_state.stage = 0

def next_stage():
    st.session_state.stage += 1

# --- المرحلة 0: شاشة الدخول المحظور ---
if st.session_state.stage == 0:
    st.error("⚠️ WARNING: SYSTEM ENCRYPTED")
    st.title("☣️ مشروع الاختراق العالمي - البروتوكول صفر")
    st.write("محاولة الوصول إلى قاعدة بيانات الصور السحابية...")
    
    if st.button("🔓 كسر الجدار الناري (Bypass Firewall)"):
        with st.status("جاري اختراق الحماية...", expanded=True) as status:
            st.write("جاري حقن الكود في الثغرة 0x882...")
            time.sleep(1)
            st.write("تم تجاوز بروتوكول SSL...")
            time.sleep(1)
            status.update(label="تم الاختراق بنجاح!", state="complete", expanded=False)
        next_stage()
        st.rerun()

# --- المرحلة 1: فك تشفير الملفات ---
elif st.session_state.stage == 1:
    st.subheader("🕵️ جاري سحب البيانات من الأجهزة القريبة...")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 فحص ذاكرة الجهاز"):
            st.info("جاري البحث عن ملفات .jpg, .png, .mp4")
            next_stage()
            st.rerun()
    with col2:
        if st.button("📡 تعقب المزامنة السحابية"):
            st.toast("تم العثور على 4 أجهزة مرتبطة بنفس الحساب!")

# --- المرحلة 2: عرض الملفات "المسربة" ---
elif st.session_state.stage == 2:
    st.markdown("### 📁 الملفات التي تم العثور عليها في 'الخادم المظلم':")
    
    fake_logs = [
        "Partition_A: IMG_DCIM_8821.jpg (Encrypted)",
        "Partition_B: PRIVATE_VAULT_01.png (Decrypted)",
        "System: Cloud_Backup_2026.zip",
        "Hidden: Hidden_Folder_Donot_Open.bin"
    ]
    
    for log in fake_logs:
        st.code(log, language="bash")

    st.divider()
    st.markdown("#### 🚨 خيارات التدمير النهائي")
    
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        if st.button("🛑 إلغاء العملية"):
            st.session_state.stage = 0
            st.rerun()
    
    with col_b:
        if st.button("👁️ عرض الصور (وهمي)"):
            st.warning("فشل: الملفات محمية بكلمة مرور 'الروت'")
            
    with col_c:
        # الزر الذي طلبه المستخدم
        if st.button("🔥 حذف الكل (WIPE ALL)"):
            next_stage()
            st.rerun()

# --- المرحلة 3: عملية الحذف الوهمية ---
elif st.session_state.stage == 3:
    st.header("⚡ جاري تنفيذ بروتوكول الحذف الذاتي...")
    
    progress_text = "تدمير البيانات من الخوادم العالمية..."
    my_bar = st.progress(0, text=progress_text)

    for percent_complete in range(100):
        time.sleep(0.05)
        my_bar.progress(percent_complete + 1, text=f"جاري الحذف من الجهاز الموصل {random.randint(10, 99)}: {percent_complete}%")
    
    next_stage()
    st.rerun()

# --- المرحلة النهائية ---
elif st.session_state.stage == 4:
    st.balloons()
    st.success("✅ MISSION ACCOMPLISHED")
    st.markdown("""
    ### تم حذف الصور من جميع الأجهزة المرتبطة نهائياً!
    * تم مسح الذاكرة المؤقتة (Cache).
    * تم تعطيل النسخ الاحتياطي السحابي.
    * تم إرسال أمر التدمير الذاتي للملفات المشفرة.
    """)
    
    if st.button("إعادة تشغيل النظام 🔄"):
        st.session_state.stage = 0
        st.rerun()
        
