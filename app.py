import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام طاقة الأنبار الموحد", layout="wide")

DB_FILE = "anbar_final_db.json"

# 2. إعدادات محطات الرمادي
STATIONS = {
    "مستشفى الرمادي التعليمي": {"max": 1000, "priority": 1},   # أهم منشأة
    "معمل زجاج الرمادي": {"max": 1200, "priority": 2},         # صناعي
    "محطة مياه الورار": {"max": 900, "priority": 3},           # بنية تحتية
    "جامعة الأنبار": {"max": 700, "priority": 4},              # تعليمي
    "حي التأميم (سكني)": {"max": 500, "priority": 5}           # سكني
}

# --- دوال التعامل مع الملفات (قراءة/كتابة آمنة) ---
def load_data():
    if not os.path.exists(DB_FILE): return []
    try:
        with open(DB_FILE, "r", encoding='utf-8') as f:
            data = json.load(f)
            return data
    except:
        return []

def save_data(new_entries):
    try:
        history = load_data()
        history.extend(new_entries)
        # نحتفظ بآخر 200 سجل ليكون الأرشيف كافياً
        with open(DB_FILE, "w", encoding='utf-8') as f:
            json.dump(history[-200:], f, ensure_ascii=False, indent=4)
    except:
        pass

def create_reading(name, current, batch_id):
    limit = STATIONS[name]["max"]
    
    # تحديد الحالة
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
# الصفحة الأولى: غرفة التحكم
# ==========================================
if page == "🕹️ غرفة التحكم (إرسال)":
    st.title("🕹️ وحدة إرسال الإشارات الميدانية")
    
    mode = st.selectbox("نمط العمل:", ["بث تلقائي (محاكاة)", "تحكم يدوي"])
    
    # 1. الوضع التلقائي
    if mode == "بث تلقائي (محاكاة)":
        st.info("سيقوم النظام بإرسال بيانات للمحطات الـ 5 بشكل مستمر.")
        run_auto = st.checkbox("تشغيل البث التلقائي")
        
        if run_auto:
            st.success("📡 البث نشط... البيانات تتدفق.")
            placeholder = st.empty()
            
            while run_auto:
                batch_id = time.time()
                batch = []
                for name in STATIONS:
                    # توليد قيم عشوائية
                    val = random.randint(int(STATIONS[name]["max"]*0.6), int(STATIONS[name]["max"]*1.1))
                    batch.append(create_reading(name, val, batch_id))
                
                save_data(batch)
                with placeholder.container():
                    st.write(f"✅ تم الإرسال: {datetime.now().strftime('%H:%M:%S')}")
                
                time.sleep(1) # إرسال كل ثانية
    
    # 2. الوضع اليدوي
    else:
        st.write("التحكم بقيم التيار لكل محطة:")
        batch_id = time.time()
        
        for name in STATIONS:
            col1, col2 = st.columns([3, 1])
            with col1:
                val = st.slider(f"{name}", 0, int(STATIONS[name]["max"]*1.3), value=int(STATIONS[name]["max"]*0.7), key=name)
            with col2:
                if st.button(f"إرسال {name}"):
                    reading = create_reading(name, val, batch_id)
                    save_data([reading])
                    st.toast(f"تم إرسال قراءة {name}")

# ==========================================
# الصفحة الثانية: شاشة المراقبة
# ==========================================
else:
    st.title("🖥️ مركز مراقبة الشبكة")
    
    placeholder = st.empty()
    
    # حلقة التحديث المستمر
    while True:
        data = load_data()
        
        with placeholder.container():
            if not data:
                st.warning("⚠️ بانتظار البيانات... شغل البث من غرفة التحكم.")
            else:
                df = pd.DataFrame(data)
                
                # التأكد من صحة الأعمدة
                required_cols = ["batch_id", "level", "priority", "timestamp"]
                if all(col in df.columns for col in required_cols):
                    
                    # === الفروقات في العرض ===
                    if protocol_active:
                        # مع البروتوكول: ترتيب ذكي (الأحدث + الخطر + الأهمية)
                        df_display = df.sort_values(by=["batch_id", "level", "priority"], ascending=[False, False, True])
                        st.success("✅ البروتوكول فعال: يتم تقديم الحالات الحرجة والمواقع السيادية.")
                    else:
                        # بدون بروتوكول: ترتيب زمني طبيعي (Raw Data)
                        # لا يوجد انهيار، لا يوجد حذف، فقط عرض كما وصلت البيانات
                        df_display = df.sort_values(by="timestamp", ascending=False)
                        st.info("ℹ️ عرض البيانات الخام (Raw Log): الترتيب حسب وقت الوصول.")

                    # 1. الرسم البياني
                    st.subheader("📊 مخطط الأحمال")
                    chart_data = df.tail(50).pivot_table(index='الوقت', columns='المنشأة', values='التيار (A)').ffill()
                    st.line_chart(chart_data, height=250)

                    # 2. الجدول
                    st.subheader("📋 سجل البيانات")
                    
                    def highlight_danger(row):
                        if row['level'] == 3: return ['background-color: #8b0000; color: white; font-weight: bold'] * len(row)
                        if row['level'] == 2: return ['background-color: #705d00; color: white'] * len(row)
                        return [''] * len(row)

                    cols = ["المنشأة", "التيار (A)", "الحالة", "الوقت"]
                    st.dataframe(
                        df_display[cols + ['level']].style.apply(highlight_danger, axis=1),
                        use_container_width=True,
                        height=600,
                        column_config={"level": None}
                    )
                else:
                    st.error("⚠️ البيانات قديمة. اضغط زر 'تصفير قاعدة البيانات' من القائمة.")
        
        time.sleep(1)
                                                                                        
