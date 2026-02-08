import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# إعداد الصفحة
st.set_page_config(page_title="نظام طاقة الأنبار الذكي", layout="wide")

DB_FILE = "grid_batch_sort.json"

# تعريف المنشآت
LOCATIONS = {
    "مستشفى الرمادي التعليمي": {"avg": 400, "priority": 10},
    "معمل زجاج الرمادي": {"avg": 500, "priority": 10},
    "جامعة الأنبار (المجمع)": {"avg": 350, "priority": 8},
    "حي التأميم (المغذي الرئيسي)": {"avg": 300, "priority": 7}
}

def load_data():
    if not os.path.exists(DB_FILE): return []
    try:
        with open(DB_FILE, "r", encoding='utf-8') as f:
            content = f.read()
            return json.loads(content) if content else []
    except: return []

def save_data(entries):
    history = load_data()
    # نضيف البيانات الجديدة في البداية (لتكون هي الأحدث)
    # نستخدم extend ثم نعكس الترتيب أو نستخدم طريقة أخرى، 
    # الأفضل: نضيف الجديد للقائمة الموجودة ثم نحفظ الكل.
    history.extend(entries)
    # نحتفظ بآخر 80 سجل
    with open(DB_FILE, "w", encoding='utf-8') as f:
        json.dump(history[-80:], f, ensure_ascii=False)

def create_entry(name, current, batch_id):
    avg = LOCATIONS[name]["avg"]
    if current < avg: status, level = "🟢 مستقر", 1
    elif avg <= current < (avg * 1.2): status, level = "🟡 تنبيه", 2
    else: status, level = "🔴 خطر", 3
    
    return {
        "المنشأة": name, 
        "التيار (A)": current, 
        "الحالة": status,
        "الوقت": datetime.now().strftime("%H:%M:%S"),
        "timestamp": time.time(), 
        "level": level,
        "batch_id": batch_id # معرف فريد للنبضة لتمييز المجموعات
    }

# --- القائمة الجانبية ---
st.sidebar.title("🛂 وحدة التحكم")
page = st.sidebar.radio("انتقل إلى:", ["🕹️ لوحة التحكم", "🖥️ شاشة المراقبة"])
protocol_active = st.sidebar.toggle("تفعيل بروتوكول الأولويات", value=True)

if st.sidebar.button("🗑️ مسح السجلات"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.rerun()

# --- 1. صفحة التحكم ---
if page == "🕹️ لوحة التحكم":
    st.title("🕹️ وحدة الإرسال والتحكم")
    
    input_mode = st.selectbox("نمط العمل:", ["تلقائي (بث 4 مواقع)", "يدوي"])
    
    if input_mode == "تلقائي (بث 4 مواقع)":
        run_auto = st.toggle("🚀 بدء البث الجماعي", value=False)
        if run_auto:
            st.success("📡 البث نشط... يتم إرسال نبضة بيانات كل ثانية.")
            placeholder = st.empty()
            while run_auto:
                # إنشاء معرف فريد للنبضة (باستخدام الوقت الحالي)
                current_batch_id = time.time()
                batch = []
                for n in LOCATIONS.keys():
                    val = random.randint(int(LOCATIONS[n]["avg"]*0.7), int(LOCATIONS[n]["avg"]*1.6))
                    batch.append(create_entry(n, val, current_batch_id))
                
                save_data(batch)
                with placeholder.container():
                    st.write(f"✅ تم إرسال نبضة جديدة (4 مواقع) عند: {datetime.now().strftime('%H:%M:%S')}")
                time.sleep(1)
                st.rerun()
    else:
        st.subheader("🎛️ التحكم اليدوي")
        current_batch_id = time.time()
        for loc in LOCATIONS.keys():
            val = st.slider(f"تيار {loc}:", 0, 800, value=LOCATIONS[loc]["avg"], key=loc)
            if st.session_state.get(f"prev_{loc}") != val:
                save_data([create_entry(loc, val, current_batch_id)])
                st.session_state[f"prev_{loc}"] = val

# --- 2. صفحة المراقبة ---
else:
    st.title("🖥️ مركز المراقبة والتحليل اللحظي")

    @st.fragment(run_every="1s")
    def update_monitor():
        data = load_data()
        
        # المخطط البياني
        st.subheader("📊 المخطط الزمني للأحمال")
        if data:
            df_chart = pd.DataFrame(data)
            chart_data = df_chart.pivot_table(index='الوقت', columns='المنشأة', values='التيار (A)').ffill()
            st.line_chart(chart_data, height=250)
        
        # الجدول
        st.subheader("📋 سجل البيانات (أحدث نبضة في الأعلى)")
        if not data:
            st.warning("⚠️ لا توجد بيانات.")
            return
            
        df = pd.DataFrame(data)
        
        # --- منطق الفرز الذكي الجديد ---
        if protocol_active:
            # الترتيب يكون بناءً على مستويين:
            # 1. رقم النبضة (batch_id): الأحدث (الأكبر رقماً) يكون في الأعلى دائماً.
            # 2. داخل نفس النبضة: مستوى الخطر (level) يكون في الأعلى.
            df_display = df.sort_values(by=["batch_id", "level"], ascending=[False, False])
        else:
            # بدون بروتوكول: ترتيب زمني بحت (الأحدث فوق)
            df_display = df.sort_values(by="timestamp", ascending=False)

        # تنسيق الألوان
        def style_rows(row):
            if row['level'] == 3: return ['background-color: #800000; color: white; font-weight: bold'] * len(row)
            if row['level'] == 2: return ['background-color: #705d00; color: white'] * len(row)
            return [''] * len(row)

        # عرض الجدول
        # نحذف الأعمدة التقنية من العرض (batch_id, timestamp, level)
        cols_to_show = ["المنشأة", "التيار (A)", "الحالة", "الوقت"]
        
        st.dataframe(
            df_display[cols_to_show + ['level']].style.apply(style_rows, axis=1),
            use_container_width=True, 
            height=600,
            column_config={"level": None} # إخفاء عمود المستوى
        )

    update_monitor()
                                                                                             
