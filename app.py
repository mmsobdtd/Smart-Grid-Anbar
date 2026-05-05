import streamlit as st
import time
import random

# إعدادات الصفحة لتبدو كنظام تشغيل احترافي
st.set_page_config(page_title="X-TERMINAL | OVERRIDE", page_icon="📡", layout="centered")

# تطبيق نمط Terminal (اختياري لجعل الشكل أجمل)
st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #00FF00; font-family: 'Courier New', Courier, monospace; }
    .stButton>button { width: 100%; border: 1px solid #00FF00; background-color: black; color: #00FF00; }
    </style>
    """, unsafe_allow_html=True)

# إدارة مراحل النظام
if 'stage' not in st.session_state:
    st.session_state.stage = "auth"

def change_stage(new_stage):
    st.session_state.stage = new_stage
    st.rerun()

# --- المرحلة 1: شاشة الوصول المحظور ---
if st.session_state.stage == "auth":
    st.title("📡 GLOBAL-SYNC TERMINAL v8.4")
    st.error("ACCESS RESTRICTED: SECURITY LEVEL 4 REQUIRED")
    st.write("محاولة ربط الجهاز ببروتوكول السحابة الموزعة...")
    
    if st.button("EXECUTE: CLOUD_MIRROR_PULL"):
        with st.status("جاري اختراق الثغرة وتجاوز التشفير...", expanded=True) as status:
            time.sleep(2)
            st.write("🔗 جاري حقن كود الـ Proxy...")
            time.sleep(2)
            st.write("🔓 تم كسر الجدار الناري بنجاح.")
            time.sleep(1)
            status.update(label="تم الوصول للقاعدة بنجاح!", state="complete")
        change_stage("fetching")

# --- المرحلة 2: سحب الصور (انتظار وتحميل) ---
elif st.session_state.stage == "fetching":
    st.subheader("🕵️ جاري سحب كائنات البيانات (Data Objects)...")
    
    # فواصل زمنية توحي بالعمل الحقيقي
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    logs = ["Requesting Access to DCIM...", "Decrypting Metadata...", "Fetching Thumbnails...", "Mirroring Cloud Nodes..."]
    
    for i in range(101):
        # جعل السرعة متغيرة لتبدو حقيقية
        delay = random.uniform(0.05, 0.2) 
        time.sleep(delay)
        progress_bar.progress(i)
        
        if i % 25 == 0:
            status_text.text(f"Status: {logs[int(i/25)-1]}")
            
    st.success("تم سحب قائمة الملفات بنجاح.")
    change_stage("display")

# --- المرحلة 3: عرض الملفات المسحوبة ---
elif st.session_state.stage == "display":
    st.markdown("### 📁 الملفات المكتشفة في الأجهزة المرتبطة:")
    
    fake_files = [
        "IMG_2026_HIDDEN_01.jpg", "CLOUD_BACKUP_SAMSUNG_V2.zip",
        "DCIM_CAMERA_CACHE.bin", "PRIVATE_VAULT_SNAPSHOT.png",
        "SYNC_LOG_882.txt", "METADATA_TEMP_FOLDER.tmp"
    ]
    
    # عرض الملفات داخل كود لتبدو تقنية
    st.code("\n".join(fake_files), language="bash")
    
    st.warning("تم اكتشاف وجود هذه الملفات في 4 أجهزة أخرى مرتبطة بنفس الحساب.")
    st.divider()

    if st.button("🔥 EXECUTE: TOTAL_WIPE (تدمير شامل)"):
        change_stage("wiping")

# --- المرحلة 4: عملية الحذف الطويلة (دقيقتين إلى 3 دقائق) ---
elif st.session_state.stage == "wiping":
    st.header("⚡ جاري تنفيذ بروتوكول المسح النهائي")
    st.info("⚠️ تحذير: هذه العملية لا يمكن التراجع عنها. يتم الآن مسح كافة السجلات من الخوادم العالمية.")
    
    # هنا الفاصل الزمني الطويل (3 دقائق = 180 ثانية)
    total_seconds = 180 
    progress_bar = st.progress(0)
    countdown_text = st.empty()
    detail_text = st.empty()
    
    nodes = ["US-East", "EU-West", "Asia-South", "Middle-East-Main", "Backup-Vault-01"]
    
    start_time = time.time()
    while time.time() - start_time < total_seconds:
        elapsed = time.time() - start_time
        percent = min(int((elapsed / total_seconds) * 100), 99)
        
        progress_bar.progress(percent)
        countdown_text.markdown(f"**نسبة الإنجاز:** `{percent}%` | **الزمن المنقضي:** `{int(elapsed)} ثانية`")
        
        # عرض "تحديثات" وهمية أثناء الحذف
        if int(elapsed) % 15 == 0:
            current_node = random.choice(nodes)
            detail_text.write(f"♻️ جاري تطهير العقدة: `{current_node}`...")
            
        time.sleep(1) # تحديث كل ثانية
        
    progress_bar.progress(100)
    change_stage("final")

# --- المرحلة 5: النهاية ---
elif st.session_state.stage == "final":
    st.balloons()
    st.success("✅ MISSION ACCOMPLISHED: DATA ERASED")
    st.markdown("""
    ---
    ### تقرير الحالة النهائي:
    - **الجهاز المحلي:** تم مسح الذاكرة بنجاح.
    - **الأجهزة السحابية:** تم تدمير كافة النسخ في الأجهزة الـ 4 المرتبطة.
    - **سجلات الـ IP:** تم تشفير العملية لمنع التتبع.
    ---
    """)
    if st.button("إعادة تهيئة النظام"):
        change_stage("auth")
        
