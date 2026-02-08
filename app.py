import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# 1. إعدادات الصفحة الأساسية
st.set_page_config(page_title="نظام طاقة الأنبار - المراقبة الذكية", layout="wide")

DB_FILE = "grid_final_log.json"

# تعريف المنشآت والمتوسطات المرجعية
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

def save_data(entries):
    history = load_data()
    history.extend(entries)
    with open(DB_FILE, "w") as f:
        json.dump(history[-100:], f)

def create_entry(name, current):
    avg = LOCATIONS[name]["avg"]
    # منطق التنبيه بناءً على المتوسط المرجعي
    if current < avg: status, level = "🟢 مستقر", 1
    elif avg <= current < (avg * 1.2): status, level = "🟡 تنبيه", 2
    else: status, level = "🔴 خطر (حمل زائد)", 3
    
    return {
        "المنشأة": name, "التيار (A)": current, "الحالة": status,
        "الوقت": datetime.now().strftime("%H:%M:%S"),
        "timestamp": time.time(), "level": level, "p": LOCATIONS[name]["priority"]
    }

# --- القائمة الجانبية (Navigation) ---
st.sidebar.title("🛂 وحدة التحكم")
page = st.sidebar.radio("انتقل إلى:", ["🕹️ لوحة التحكم", "🖥️ شاشة المراقبة"])
protocol_active = st.sidebar.toggle("تفعيل بروتوكول الأولويات", value=True)

if st.sidebar.button("🗑️ مسح السجلات"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.rerun()

# --- 1. صفحة التحكم (الإرسال) ---
if page == "🕹️ لوحة التحكم":
    st.title("🕹️ وحدة الإرسال الميداني")
    st.info("قم بإرسال البيانات من هنا لتظهر في شاشة المراقبة.")
    
    mode = st.selectbox("نمط العمل:", ["تلقائي (4 مواقع/ثانية)", "يدوي"])
    
    if mode == "تلقائي (4 مواقع/ثانية)":
        run = st.toggle("🚀 بدء البث الجماعي الموحد")
        if run:
            st.success("📡 البث نشط الآن... يتم تحديث المواقع الأربعة كل ثانية.")
            placeholder = st.empty()
            while run:
                batch = [create_entry(n, random.randint(int(LOCATIONS[n]["avg"]*0.7), int(LOCATIONS[n]["avg"]*1.6))) for n in LOCATIONS.keys()]
                save_data(batch)
                with placeholder.container():
                    st.write(f"✅ تم بث نبضة شاملة عند: {datetime.now().strftime('%H:%M:%S')}")
                time.sleep(1)
                st.rerun()
    else:
        st.subheader("🎛️ التحكم اليدوي")
        cols = st.columns(2)
        for i, name in enumerate(LOCATIONS.keys()):
            val = cols[i%2].slider(f"{name}:", 0, 800, value=LOCATIONS[name]["avg"], key=name)
            if st.session_state.get(f"v_{name}") != val:
                save_data([create_entry(name, val)])
                st.session_state[f"v_{name}"] = val

# --- 2. صفحة المراقبة (الجدول والرسم) ---
else:
    st.title("🖥️ شاشة المراقبة والتحليل")

    # تحديث تلقائي كل ثانية للجزء المخصص للبيانات
    @st.fragment(run_every="1s")
    def update_monitor():
        data = load_data()
        
        # الرسم البياني
        st.subheader("📊 المخطط الزمني للأحمال")
        if data:
            df_chart = pd.DataFrame(data)
            chart_data = df_chart.pivot_table(index='الوقت', columns='المنشأة', values='التيار (A)').ffill()
            st.line_chart(chart_data, height=250)
        else:
            st.info("بانتظار وصول البيانات لرسم المخطط...")

        # الجدول (Data Table)
        st.subheader("📋 سجل البيانات الفني (Data Log)")
        if not data:
            st.warning("⚠️ السجل فارغ. يرجى تفعيل البث من 'لوحة التحكم'.")
            # إظهار جدول فارغ كإطار فقط
            empty_df = pd.DataFrame(columns=["المنشأة", "التيار (A)", "الحالة", "الوقت"])
            st.table(empty_df)
        else:
            df = pd.DataFrame(data)
            
            # تطبيق منطق البروتوكول (الفرز)
            if protocol_active:
                # يظهر كل شيء، لكن الخطر (level 3) يصعد للأعلى فوراً
                df_display = df.sort_values(by=["level", "timestamp"], ascending=[False, False])
            else:
                # عرض زمني بحت (الأحدث فوق)
                df_display = df.sort_values(by="timestamp", ascending=False)

            # تنسيق ألوان الأسطر
            def style_rows(row):
                if row['level'] == 3: return ['background-color: #800000; color: white; font-weight: bold'] * len(row)
                if row['level'] == 2: return ['background-color: #705d00; color: white'] * len(row)
                return [''] * len(row)

            st.dataframe(
                df_display.drop(columns=['timestamp', 'level', 'p', 'المتوسط'], errors='ignore').style.apply(style_rows, axis=1),
                use_container_width=True, height=450
            )

    update_monitor()
                
