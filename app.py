import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام طاقة الأنبار الموحد", layout="wide")

DB_FILE = "anbar_grid_db.json"

# 2. إعدادات محطات الرمادي (5 محطات رئيسية)
STATIONS = {
    "مستشفى الرمادي التعليمي": {"max": 1000, "priority": 1},   # أولوية قصوى
    "معمل زجاج الرمادي": {"max": 1200, "priority": 2},         # صناعي
    "محطة مياه الورار": {"max": 900, "priority": 3},           # خدمات
    "جامعة الأنبار": {"max": 700, "priority": 4},              # تعليمي
    "حي التأميم (سكني)": {"max": 500, "priority": 5}           # سكني
}

# --- دوال التعامل مع الملفات (محمية من الأخطاء) ---
def load_data():
    if not os.path.exists(DB_FILE): return []
    try:
        with open(DB_FILE, "r", encoding='utf-8') as f:
            data = json.load(f)
            return data
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_data(new_entries):
    try:
        # قراءة البيانات القديمة أولاً
        history = load_data()
        # إضافة البيانات الجديدة
        history.extend(new_entries)
        # الاحتفاظ بآخر 100 سجل فقط لضمان السرعة
        with open(DB_FILE, "w", encoding='utf-8') as f:
            json.dump(history[-100:], f, ensure_ascii=False, indent=4)
    except:
        pass # تجاهل الخطأ لحظياً لمنع توقف النظام

def create_reading(name, current, batch_id):
    limit = STATIONS[name]["max"]
    
    # تحديد الحالة ومستوى الخطر
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
        "batch_id": batch_id
    }

# --- القائمة الجانبية ---
st.sidebar.title("⚡ مركز سيطرة الرمادي")
page = st.sidebar.radio("القوائم:", ["🕹️ غرفة التحكم (إرسال)", "🖥️ شاشة المراقبة (استقبال)"])
st.sidebar.markdown("---")
protocol_active = st.sidebar.toggle("تفعيل بروتوكول الأولويات", value=True)

if st.sidebar.button("🗑️ تصفير قاعدة البيانات"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.rerun()

# ==========================================
# الصفحة الأولى: غرفة التحكم (إرسال البيانات)
# ==========================================
if page == "🕹️ غرفة التحكم (إرسال)":
    st.title("🕹️ وحدة إرسال الإشارات")
    
    mode = st.selectbox("طريقة الإرسال:", ["بث تلقائي (مستمر)", "إرسال يدوي"])
    
    # الوضع التلقائي
    if mode == "بث تلقائي (مستمر)":
        st.info("سيتم إرسال قراءات لجميع المحطات الـ 5 كل ثانية.")
        
        # نستخدم checkbox بدلاً من button ليبقى فعالاً
        run_auto = st.checkbox("تشغيل البث التلقائي")
        
        if run_auto:
            st.success("📡 البث نشط... البيانات تُرسل الآن إلى شاشة المراقبة.")
            placeholder = st.empty()
            
            # حلقة التوليد والإرسال
            while run_auto:
                batch_id = time.time()
                batch = []
                for name in STATIONS:
                    # قيم عشوائية تحاكي الواقع
                    val = random.randint(int(STATIONS[name]["max"]*0.6), int(STATIONS[name]["max"]*1.1))
                    batch.append(create_reading(name, val, batch_id))
                
                save_data(batch)
                
                with placeholder.container():
                    st.write(f"✅ تم إرسال دفعة بيانات عند: {datetime.now().strftime('%H:%M:%S')}")
                
                time.sleep(1) # انتظار ثانية
                # ملاحظة: لا نستخدم st.rerun هنا لكي لا يعيد تحميل الصفحة ويوقف الـ checkbox
    
    # الوضع اليدوي
    else:
        st.write("التحكم الدقيق بالمحطات:")
        batch_id = time.time()
        
        for name in STATIONS:
            col1, col2 = st.columns([3, 1])
            with col1:
                val = st.slider(f"{name}", 0, int(STATIONS[name]["max"]*1.25), value=int(STATIONS[name]["max"]*0.5), key=name)
            with col2:
                if st.button(f"إرسال {name}"):
                    reading = create_reading(name, val, batch_id)
                    save_data([reading])
                    st.toast(f"تم إرسال {name} بنجاح")

# ==========================================
# الصفحة الثانية: شاشة المراقبة (استقبال وعرض)
# ==========================================
else:
    st.title("🖥️ مركز مراقبة الشبكة")
    
    # حاوية لتحديث البيانات تلقائياً دون إعادة تحميل الصفحة كاملة
    placeholder = st.empty()
    
    # حلقة لانهائية للتحديث المستمر (مثل شاشات المراقبة الحقيقية)
    # ملاحظة: هذا الكود سيعمل طالما الصفحة مفتوحة
    while True:
        data = load_data()
        
        with placeholder.container():
            if not data:
                st.warning("⚠️ لا توجد بيانات في النظام. يرجى تشغيل البث من غرفة التحكم.")
            else:
                df = pd.DataFrame(data)
                
                # --- خوارزمية البروتوكول (القلب النابض للنظام) ---
                if protocol_active:
                    # الترتيب الذكي:
                    # 1. رقم الدفعة (batch_id): الأحدث يظهر في الأعلى.
                    # 2. مستوى الخطر (level): داخل الدفعة، الخطر (3) يصعد فوق.
                    # 3. الأولوية (priority): المستشفى (1) يصعد فوق الجامعة (4).
                    df_display = df.sort_values(by=["batch_id", "level", "priority"], ascending=[False, False, True])
                    st.success("✅ البروتوكول فعال: يتم فرز المخاطر والمواقع الحيوية للأعلى.")
                else:
                    # الترتيب الزمني البسيط (من الأحدث للأقدم)
                    df_display = df.sort_values(by="timestamp", ascending=False)
                    st.error("⚠️ تحذير: النظام يعمل بدون حماية (Raw Data Mode).")

                # 1. الرسم البياني (لآخر 50 قراءة فقط)
                st.subheader("📊 مخطط الأحمال")
                chart_data = df.tail(50).pivot_table(index='الوقت', columns='المنشأة', values='التيار (A)').ffill()
                st.line_chart(chart_data, height=250)

                # 2. الجدول الملون
                st.subheader("📋 سجل البيانات المباشر")
                
                def highlight_danger(row):
                    if
                    
