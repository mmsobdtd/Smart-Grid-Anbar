import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# إعدادات الصفحة الرسمية لجامعة الأنبار
st.set_page_config(page_title="Smart Grid Monitoring - Ramadi", layout="wide")

DB_FILE = "final_grid_db.json"

# المنشآت والأوزان الهندسية
LOCATIONS = {
    "مستشفى الرمادي التعليمي": {"avg": 400, "priority": 10},
    "معمل زجاج الرمادي": {"avg": 500, "priority": 10},
    "جامعة الأنبار (المجمع)": {"avg": 350, "priority": 8},
    "حي التأميم (المغذي الرئيسي)": {"avg": 300, "priority": 7}
}

def load_data():
    if not os.path.exists(DB_FILE): return []
    try:
        with open(DB_FILE, "r") as f:
            content = f.read()
            return json.loads(content) if content else []
    except: return []

def save_batch(entries):
    history = load_data()
    history.extend(entries)
    with open(DB_FILE, "w") as f:
        json.dump(history[-80:], f) # حفظ آخر 80 سجل للسلاسة

def create_packet(name, current):
    avg = LOCATIONS[name]["avg"]
    # منطق تحديد مستوى الخطر
    if current < avg: status, level = "🟢 مستقر", 1
    elif avg <= current < (avg * 1.2): status, level = "🟡 تنبيه", 2
    else: status, level = "🔴 خطر (حمل زائد)", 3
    
    return {
        "المنشأة": name, "التيار (A)": current, "الحالة": status,
        "الوقت": datetime.now().strftime("%H:%M:%S"),
        "ts": time.time(), "level": level, "p": LOCATIONS[name]["priority"]
    }

# --- القائمة الجانبية ---
st.sidebar.title("🛂 مركز السيطرة")
page = st.sidebar.radio("انتقل إلى:", ["🕹️ لوحة التحكم", "🖥️ شاشة المراقبة"])
protocol_active = st.sidebar.toggle("تفعيل بروتوكول الأولويات", value=True)

if st.sidebar.button("🗑️ تصفير السجل"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.rerun()

# --- 1. صفحة التحكم ---
if page == "🕹️ لوحة التحكم":
    st.title("🕹️ وحدة التحكم الميداني")
    mode = st.selectbox("نمط العمل:", ["تلقائي (4 مواقع/ثانية)", "يدوي"])
    
    if mode == "تلقائي (4 مواقع/ثانية)":
        run = st.toggle("🚀 بدء البث الجماعي")
        if run:
            st.success("📡 البث نشط... يتم إرسال بيانات المواقع الأربعة كل ثانية.")
            while run:
                batch = [create_packet(n, random.randint(int(LOCATIONS[n]["avg"]*0.6), int(LOCATIONS[n]["avg"]*1.6))) for n in LOCATIONS.keys()]
                save_batch(batch)
                time.sleep(1)
                st.rerun()
    else:
        st.subheader("🎛️ التحكم اليدوي")
        cols = st.columns(2)
        for i, name in enumerate(LOCATIONS.keys()):
            val = cols[i%2].slider(f"{name}", 0, 800, value=LOCATIONS[name]["avg"])
            if st.session_state.get(f"v_{name}") != val:
                save_batch([create_packet(name, val)])
                st.session_state[f"v_{name}"] = val

# --- 2. صفحة المراقبة ---
else:
    st.title("🖥️ شاشة المراقبة والتحليل")
    
    @st.fragment(run_every="1s")
    def update_ui():
        data = load_data()
        if not data:
            st.warning("⚠️ بانتظار البيانات...")
            return

        df = pd.DataFrame(data)
        
        # ترتيب البيانات (البروتوكول الذكي)
        if protocol_active:
            # هنا التعديل: تظهر كل البيانات لكن الخطر (level 3) يصعد للأعلى أولاً
            df_display = df.sort_values(by=["level", "ts"], ascending=[False, False])
        else:
            # بدون بروتوكول: ترتيب زمني بحت (الأحدث فوق)
            df_display = df.sort_values(by="ts", ascending=False)

        # الرسم البياني
        st.subheader("📊 المخطط الزمني للأحمال")
        chart_df = df.pivot_table(index='الوقت', columns='المنشأة', values='التيار (A)').ffill()
        st.line_chart(chart_df, height=300)
        
        

        # الجدول (التنسيق السلس)
        st.subheader("📋 سجل البيانات المستلمة (كامل)")
        
        def style_rows(row):
            # تلوين السطر فقط إذا كان "خطر" أو "تنبيه" بشكل منفرد
            if row['level'] == 3: return ['background-color: #7b0000; color: white'] * len(row)
            if row['level'] == 2: return ['background-color: #5c4b00; color: white'] * len(row)
            return [''] * len(row)

        st.dataframe(
            df_display.drop(columns=['ts', 'level', 'p'], errors='ignore').style.apply(style_rows, axis=1),
            use_container_width=True, height=450
        )

    update_ui()
