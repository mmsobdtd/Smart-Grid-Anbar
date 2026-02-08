import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# إعدادات الصفحة
st.set_page_config(page_title="نظام مراقبة طاقة الأنبار المطور", layout="wide")

DB_FILE = "grid_final_database.json"

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
    # الحفاظ على آخر 60 سجل لضمان سلاسة الرسم البياني
    with open(DB_FILE, "w") as f:
        json.dump(history[-60:], f)

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
        "level": level,
        "p": LOCATIONS_CONFIG[name]["priority"]
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
    
    mode = st.selectbox("نمط العمل:", ["تلقائي (إرسال جماعي كل 1 ثانية)", "يدوي (تحكم فردي)"])
    
    if mode == "تلقائي (إرسال جماعي كل 1 ثانية)":
        run_auto = st.toggle("🚀 بدء البث التلقائي للمواقع الأربعة", value=False)
        
        if run_auto:
            st.success("📡 البث الجماعي نشط: يتم إرسال 4 حزم بيانات كل ثانية.")
            placeholder = st.empty()
            while run_auto:
                batch = []
                for name in LOCATIONS_CONFIG.keys():
                    avg = LOCATIONS_CONFIG[name]["avg"]
                    # محاكاة تذبذب الأحمال
                    val = random.randint(int(avg*0.7), int(avg*1.5))
                    batch.append(create_entry(name, val))
                
                save_entries_batch(batch)
                
                with placeholder.container():
                    st.write(f"✅ تم إرسال تحديث لجميع المواقع عند الساعة: {datetime.now().strftime('%H:%M:%S')}")
                    for entry in batch:
                        st.text(f"📡 {entry['المنشأة']}: {entry['التيار (A)']}A")
                
                time.sleep(1)
                st.rerun()
        else:
            st.info("قم بتفعيل الزر أعلاه لبدء البث التلقائي.")

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
            st.warning("بانتظار استقبال البيانات... (يرجى تفعيل البث من لوحة التحكم)")
            return

        df = pd.DataFrame(data)

        # منطق الفرز المطور (البروتوكول)
        if protocol_active:
            st.success("✅ البروتوكول فعال: الأحمال الزائدة تظهر بالقمة فوراً")
            # الفرز: 1. مستوى الخطر (تنازلي) 2. الوقت (تنازلي)
            df_display = df.sort_values(by=["level", "الوقت"], ascending=[False, False])
        else:
            st.error("🚨 بدون بروتوكول: عرض تسلسلي بسيط (خطر ضياع التنبيهات)")
            df_display = df.iloc[::-1]

        # أ. الرسم البياني
        st.subheader("📊 المخطط البياني لتطور الأحمال")
        chart_df = df.pivot_table(index='الوقت', columns='المنشأة', values='التيار (A)').ffill()
        st.line_chart(chart_df, height=300)

        # ب. الجدول المطور
        st.subheader("📋 سجل البيانات المستلمة")
        
        def color_logic(row):
            if "🔴" in row['الحالة']: return ['background-color: #800000; color: white; font-weight: bold'] * len(row)
            if "🟡" in row['الحالة']: return ['background-color: #705d00; color: white'] * len(row)
            return [''] * len(row)

        st.dataframe(
            df_display.drop(columns=['level', 'p', 'المتوسط'], errors='ignore').style.apply(color_logic, axis=1),
            use_container_width=True,
            height=450
        )

    show_monitoring()
        
