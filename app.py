import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# إعدادات الصفحة
st.set_page_config(page_title="نظام مراقبة طاقة الأنبار - الإصدار الاحترافي", layout="wide")

DB_FILE = "grid_final_v3.json"

# --- 1. إعدادات المنشآت ---
LOCATIONS_CONFIG = {
    "مستشفى الرمادي التعليمي": {"avg": 400, "priority": 10},
    "معمل زجاج الرمادي": {"avg": 500, "priority": 10},
    "جامعة الأنبار (المجمع)": {"avg": 350, "priority": 8},
    "حي التأميم (المغذي الرئيسي)": {"avg": 300, "priority": 7}
}

def load_data():
    if not os.path.exists(DB_FILE): return []
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except: return []

def save_entries_batch(entries):
    history = load_data()
    history.extend(entries)
    # الاحتفاظ بآخر 100 سجل لعرض التاريخ الكامل
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
        "timestamp": time.time(), # للترتيب الزمني الدقيق
        "level": level
    }

# --- 2. التنقل الجانبي ---
st.sidebar.title("📑 قائمة النظام")
page = st.sidebar.radio("انتقل إلى:", ["🕹️ لوحة التحكم", "🖥️ شاشة المراقبة"])

st.sidebar.markdown("---")
protocol_active = st.sidebar.toggle("تفعيل البروتوكول الذكي", value=True)

if st.sidebar.button("🗑️ مسح السجلات"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.rerun()

# --- 3. الصفحة الأولى: لوحة التحكم ---
if page == "🕹️ لوحة التحكم":
    st.title("🕹️ وحدة التحكم والإرسال")
    
    input_mode = st.selectbox("نمط العمل:", ["تلقائي (إرسال جماعي 4 مواقع)", "يدوي"])
    
    if input_mode == "تلقائي (إرسال جماعي 4 مواقع)":
        run_auto = st.toggle("🚀 بدء البث الجماعي (1 ثانية)", value=False)
        
        if run_auto:
            st.success("📡 البث الجماعي نشط: يتم إرسال 4 قراءات معاً كل ثانية.")
            placeholder = st.empty()
            while run_auto:
                batch = []
                for name in LOCATIONS_CONFIG.keys():
                    avg = LOCATIONS_CONFIG[name]["avg"]
                    # محاكاة تذبذب (أحياناً طبيعي وأحياناً خطر)
                    val = random.randint(int(avg*0.6), int(avg*1.6))
                    batch.append(create_entry(name, val))
                
                save_entries_batch(batch)
                
                with placeholder.container():
                    st.write(f"✅ تم بث نبضة بيانات شاملة عند: {datetime.now().strftime('%H:%M:%S')}")
                    cols = st.columns(4)
                    for i, entry in enumerate(batch):
                        cols[i].metric(entry['المنشأة'], f"{entry['التيار (A)']}A")
                
                time.sleep(1)
                st.rerun()
    else:
        st.subheader("🎛️ التحكم اليدوي")
        cols = st.columns(2)
        for i, loc in enumerate(LOCATIONS_CONFIG.keys()):
            with cols[i % 2]:
                val = st.slider(f"تيار {loc}:", 0, 800, value=LOCATIONS_CONFIG[loc]["avg"], key=loc)
                if st.session_state.get(f"prev_{loc}") != val:
                    save_entries_batch([create_entry(loc, val)])
                    st.session_state[f"prev_{loc}"] = val

# --- 4. الصفحة الثانية: شاشة المراقبة ---
else:
    st.title("🖥️ مركز المراقبة والتحليل اللحظي")

    @st.fragment(run_every="1s")
    def show_monitoring():
        data = load_data()
        if not data:
            st.warning("بانتظار البيانات... (يرجى تفعيل البث من لوحة التحكم)")
            return

        df = pd.DataFrame(data)

        # منطق الفرز (البروتوكول الذكي)
        if protocol_active:
            st.success("✅ البروتوكول فعال: يتم عرض التاريخ كاملاً مع رفع الأخطار للأعلى")
            # الترتيب: 1. حسب مستوى الخطر (الأحمر أولاً) 2. حسب الوقت (الأحدث أولاً)
            # هذا يضمن ظهور كل البيانات، لكن الخطر يكون دائماً في القمة
            df_display = df.sort_values(by=["level", "timestamp"], ascending=[False, False])
        else:
            st.error("🚨 بدون بروتوكول: عرض تسلسلي زمني فقط")
            df_display = df.sort_values(by="timestamp", ascending=False)

        # أ. الرسم البياني
        st.subheader("📊 المخطط الزمني لتطور الأحمال")
        chart_df = df.pivot_table(index='الوقت', columns='المنشأة', values='التيار (A)').ffill()
        st.line_chart(chart_df, height=300)

        # ب. الجدول المطور
        st.subheader("📋 سجل البيانات الكامل (Full History Log)")
        
        def color_logic(row):
            if row['level'] == 3: return ['background-color: #800000; color: white; font-weight: bold'] * len(row)
            if row['level'] == 2: return ['background-color: #705d00; color: white'] * len(row)
            return [''] * len(row)

        st.dataframe(
            df_display.drop(columns=['level', 'timestamp', 'المتوسط'], errors='ignore').style.apply(color_logic, axis=1),
            use_container_width=True,
            height=500
        )

    show_monitoring()
        
