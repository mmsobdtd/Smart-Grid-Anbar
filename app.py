import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# إعدادات الصفحة
st.set_page_config(page_title="نظام طاقة الأنبار - سجل البيانات اللحظي", layout="wide")

# اسم ملف قاعدة البيانات
DB_FILE = "grid_database_v4.json"

# --- 1. إعدادات المنشآت ---
LOCATIONS_CONFIG = {
    "مستشفى الرمادي التعليمي": {"avg": 400, "priority": 10},
    "معمل زجاج الرمادي": {"avg": 500, "priority": 10},
    "جامعة الأنبار (المجمع)": {"avg": 350, "priority": 8},
    "حي التأميم (المغذي الرئيسي)": {"avg": 300, "priority": 7}
}

# دالة تحميل البيانات
def load_data():
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, "r") as f:
            content = f.read()
            if not content: return []
            return json.loads(content)
    except:
        return []

# دالة حفظ البيانات
def save_entries_batch(entries):
    history = load_data()
    history.extend(entries)
    # الحفاظ على آخر 100 سجل لضمان سرعة الواجهة
    with open(DB_FILE, "w") as f:
        json.dump(history[-100:], f)

def create_entry(name, current):
    avg = LOCATIONS_CONFIG[name]["avg"]
    if current < avg:
        status, level = "🟢 مستقر", 1
    elif avg <= current < (avg * 1.2):
        status, level = "🟡 تنبيه", 2
    else:
        status, level = "🔴 خطر (حمل زائد)", 3

    return {
        "المنشأة": name,
        "التيار (A)": current,
        "المتوسط": avg,
        "الحالة": status,
        "الوقت": datetime.now().strftime("%H:%M:%S"),
        "timestamp": time.time(),
        "level": level
    }

# --- 2. القائمة الجانبية ---
st.sidebar.title("📑 قائمة النظام")
page = st.sidebar.radio("انتقل إلى:", ["🕹️ لوحة التحكم", "🖥️ شاشة المراقبة"])

st.sidebar.markdown("---")
protocol_active = st.sidebar.toggle("تفعيل البروتوكول الذكي", value=True)

if st.sidebar.button("🗑️ مسح سجل البيانات"):
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    st.success("تم مسح السجل بنجاح")
    st.rerun()

# --- 3. الصفحة الأولى: لوحة التحكم (إرسال البيانات) ---
if page == "🕹️ لوحة التحكم":
    st.title("🕹️ وحدة التحكم وإرسال البيانات")
    st.info("ملاحظة: البيانات التي ترسلها هنا ستظهر في 'شاشة المراقبة'.")
    
    input_mode = st.selectbox("نمط العمل:", ["تلقائي (4 مواقع معاً)", "يدوي"])
    
    if input_mode == "تلقائي (4 مواقع معاً)":
        run_auto = st.toggle("🚀 بدء البث الجماعي (كل 1 ثانية)", value=False)
        if run_auto:
            st.success("📡 البث نشط الآن... اذهب إلى صفحة المراقبة لرؤية السجل.")
            placeholder = st.empty()
            while run_auto:
                batch = []
                for name in LOCATIONS_CONFIG.keys():
                    avg = LOCATIONS_CONFIG[name]["avg"]
                    val = random.randint(int(avg*0.6), int(avg*1.6))
                    batch.append(create_entry(name, val))
                
                save_entries_batch(batch)
                
                with placeholder.container():
                    st.write(f"✅ نبضة بيانات شاملة مرسلة عند: {datetime.now().strftime('%H:%M:%S')}")
                
                time.sleep(1)
                st.rerun()
    else:
        st.subheader("🎛️ التحكم اليدوي")
        for loc in LOCATIONS_CONFIG.keys():
            val = st.slider(f"تيار {loc}:", 0, 800, value=LOCATIONS_CONFIG[loc]["avg"], key=loc)
            if st.session_state.get(f"prev_{loc}") != val:
                save_entries_batch([create_entry(loc, val)])
                st.session_state[f"prev_{loc}"] = val

# --- 4. الصفحة الثانية: شاشة المراقبة (عرض السجل) ---
else:
    st.title("🖥️ مركز المراقبة والتحليل اللحظي")
    st.markdown("---")

    # تحديث البيانات تلقائياً كل ثانية لمواكبة البث
    @st.fragment(run_every="1s")
    def display_monitoring_data():
        data = load_data()
        
        if not data:
            st.warning("⚠️ لا يوجد سجل بيانات حتى الآن. يرجى الذهاب إلى 'لوحة التحكم' وبدء الإرسال.")
            return

        df = pd.DataFrame(data)

        # منطق الفرز (البروتوكول)
        if protocol_active:
            # ترتيب: الخطر (level 3) أولاً، ثم الوقت الأحدث
            df_display = df.sort_values(by=["level", "timestamp"], ascending=[False, False])
        else:
            # ترتيب زمني بسيط (الأحدث فوق)
            df_display = df.sort_values(by="timestamp", ascending=False)

        # أ. الرسم البياني
        st.subheader("📊 المخطط البياني للأحمال")
        chart_df = df.pivot_table(index='الوقت', columns='المنشأة', values='التيار (A)').ffill()
        st.line_chart(chart_df, height=300)

        [attachment_0](attachment)

        # ب. سجل البيانات (الجدول) - تأكيد ظهوره
        st.subheader("📋 سجل البيانات الكامل (Data Log)")
        
        def apply_styles(row):
            if row['level'] == 3: # خطر
                return ['background-color: #800000; color: white; font-weight: bold'] * len(row)
            if row['level'] == 2: # تنبيه
                return ['background-color: #705d00; color: white'] * len(row)
            return [''] * len(row)

        # عرض الجدول بشكل رسمي وواضح
        st.dataframe(
            df_display.drop(columns=['level', 'timestamp', 'المتوسط'], errors='ignore').style.apply(apply_styles, axis=1),
            use_container_width=True,
            height=500
        )

    display_monitoring_data()
    
