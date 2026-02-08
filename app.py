import streamlit as st
import pandas as pd
import time
import random
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(page_title="منظومة طاقة الأنبار الموحدة", layout="wide")

# 2. إعدادات محطات الأنبار (الرمادي)
# Priority: 1 (أعلى أهمية) -> 5 (أقل أهمية)
STATIONS = {
    "مستشفى الرمادي التعليمي": {"max": 1000, "priority": 1},
    "معمل زجاج الرمادي": {"max": 1200, "priority": 2},
    "محطة مياه الورار": {"max": 900, "priority": 3},
    "جامعة الأنبار": {"max": 700, "priority": 4},
    "حي التأميم (سكني)": {"max": 500, "priority": 5}
}

# 3. تهيئة الذاكرة (بديلة للملفات لمنع التعليق)
if 'grid_history' not in st.session_state:
    st.session_state.grid_history = []
if 'auto_running' not in st.session_state:
    st.session_state.auto_running = False

# دالة إنشاء قراءة جديدة
def generate_reading(name, current, batch_id):
    limit = STATIONS[name]["max"]
    
    # تحديد الحالة (مستقر - تنبيه - خطر)
    if current < (limit * 0.8):
        status, level = "🟢 مستقر", 1
    elif (limit * 0.8) <= current < (limit * 0.95):
        status, level = "🟡 تنبيه", 2
    else:
        status, level = "🔴 خطر", 3

    return {
        "المنشأة": name,
        "التيار (A)": current,
        "الحالة": status,
        "الوقت": datetime.now().strftime("%H:%M:%S"),
        "timestamp": time.time(),
        "level": level,
        "priority": STATIONS[name]["priority"],
        "batch_id": batch_id  # لتمييز الدفعة
    }

# --- القائمة الجانبية (Navigation) ---
st.sidebar.title("🛂 مركز سيطرة الأنبار")
page = st.sidebar.radio("تنقل بين الأقسام:", ["🕹️ غرفة التحكم (الإرسال)", "🖥️ شاشة المراقبة (التحليل)"])
st.sidebar.markdown("---")
protocol_active = st.sidebar.toggle("تفعيل بروتوكول الأولويات", value=True)

if st.sidebar.button("🗑️ تصفير النظام"):
    st.session_state.grid_history = []
    st.rerun()

# ==========================================
# الصفحة الأولى: غرفة التحكم (الإرسال)
# ==========================================
if page == "🕹️ غرفة التحكم (الإرسال)":
    st.title("🕹️ وحدة التحكم وإرسال البيانات")
    
    mode = st.selectbox("نوع البث:", ["تلقائي (بث مستمر)", "يدوي (تحكم دقيق)"])
    
    # --- الوضع التلقائي ---
    if mode == "تلقائي (بث مستمر)":
        st.info("سيقوم النظام بإرسال قراءات لجميع محطات الرمادي الـ 5 كل ثانية.")
        
        # زر التشغيل/الإيقاف
        if st.button("🚀 تشغيل/إيقاف البث التلقائي"):
            st.session_state.auto_running = not st.session_state.auto_running
            st.rerun()
        
        if st.session_state.auto_running:
            st.success("📡 البث نشط... يتم إرسال البيانات الآن.")
            
            # حلقة التوليد (تشتغل مرة واحدة ثم تعيد تحميل الصفحة)
            batch_id = time.time()
            new_batch = []
            
            for name in STATIONS:
                # توليد قيم عشوائية تحاكي الواقع
                val = random.randint(int(STATIONS[name]["max"]*0.6), int(STATIONS[name]["max"]*1.1))
                new_batch.append(generate_reading(name, val, batch_id))
            
            # الحفظ في الذاكرة (في الأعلى)
            st.session_state.grid_history = new_batch + st.session_state.grid_history[:90] # نحتفظ بآخر 90 قراءة
            
            # انتظار ثانية ثم تحديث
            time.sleep(1) 
            st.rerun()
            
    # --- الوضع اليدوي ---
    else:
        st.session_state.auto_running = False
        st.write("تحكم بكل محطة على حدة:")
        
        batch_id = time.time()
        for name in STATIONS:
            col1, col2 = st.columns([3, 1])
            with col1:
                val = st.slider(f"{name}", 0, int(STATIONS[name]["max"]*1.2), value=int(STATIONS[name]["max"]*0.5))
            with col2:
                if st.button(f"إرسال {name}"):
                    reading = generate_reading(name, val, batch_id)
                    st.session_state.grid_history.insert(0, reading)
                    st.toast(f"تم إرسال بيانات {name}")

# ==========================================
# الصفحة الثانية: شاشة المراقبة
# ==========================================
else:
    st.title("🖥️ مركز مراقبة الشبكة الوطنية")
    
    # تحديث تلقائي للشاشة كل ثانية لرؤية البيانات القادمة من الصفحة الأخرى
    if st.session_state.auto_running:
        time.sleep(1)
        st.rerun()

    if not st.session_state.grid_history:
        st.warning("⚠️ لا توجد بيانات. يرجى الذهاب لغرفة التحكم وتشغيل البث.")
    else:
        df = pd.DataFrame(st.session_state.grid_history)
        
        # --- منطق البروتوكول ---
        if protocol_active:
            # 1. ترتيب حسب الدفعة (الأحدث فوق)
            # 2. داخل الدفعة: الخطر (3) فوق
            # 3. ثم الأهمية (المستشفى 1 فوق الجامعة 4)
            df_display = df.sort_values(by=["batch_id", "level", "priority"], ascending=[False, False, True])
            st.success("✅ البروتوكول فعال: أولوية قصوى للمستشفى والحالات الخطرة.")
        else:
            # ترتيب زمني فقط
            df_display = df.sort_values(by="timestamp", ascending=False)
            st.error("⚠️ تحذير: النظام يعمل بدون حماية (وضع الترتيب الزمني).")

        # الرسم البياني
        st.subheader("📊 مخطط الأحمال اللحظي")
        # نأخذ بيانات آخر دقيقة فقط للرسم
        chart_data = df.head(50).pivot_table(index='الوقت', columns='المنشأة', values='التيار (A)')
        st.line_chart(chart_data, height=250)

        # الجدول
        st.subheader("📋 سجل البيانات الفني")
        
        def style_rows(row):
            if row['level'] == 3: return ['background-color: #8b0000; color: white; font-weight: bold'] * len(row)
            if row['level'] == 2: return ['background-color: #705d00; color: white'] * len(row)
            return [''] * len(row)

        # عرض الأعمدة المهمة فقط
        cols = ["المنشأة", "التيار (A)", "الحالة", "الوقت"]
        st.dataframe(
            df_display[cols + ['level']].style.apply(style_rows, axis=1),
            use_container_width=True,
            height=600,
            column_config={"level": None}
        )
        
