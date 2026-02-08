import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# 1. إعدادات الصفحة الأساسية
st.set_page_config(page_title="Smart Grid - Anbar University", layout="wide")

DB_FILE = "grid_final_data.json"

# تعريف المنشآت بناءً على متطلبات مشروعك
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
    history.extend(entries)
    # الحفاظ على آخر 100 سجل لضمان سرعة المتصفح
    with open(DB_FILE, "w", encoding='utf-8') as f:
        json.dump(history[-100:], f, ensure_ascii=False)

def create_entry(name, current):
    avg = LOCATIONS[name]["avg"]
    if current < avg: status, level = "🟢 مستقر", 1
    elif avg <= current < (avg * 1.2): status, level = "🟡 تنبيه", 2
    else: status, level = "🔴 خطر (حمل زائد)", 3
    
    return {
        "المنشأة": name, "التيار (A)": current, "الحالة": status,
        "الوقت": datetime.now().strftime("%H:%M:%S"),
        "timestamp": time.time(), "level": level
    }

# --- القائمة الجانبية (Navigation) ---
st.sidebar.title("🛂 وحدة التحكم - جامعة الأنبار")
page = st.sidebar.radio("انتقل إلى:", ["🕹️ لوحة التحكم", "🖥️ شاشة المراقبة"])
protocol_active = st.sidebar.toggle("تفعيل البروتوكول الذكي", value=True)

if st.sidebar.button("🗑️ مسح السجلات"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.rerun()

# --- 1. صفحة التحكم (الإرسال) ---
if page == "🕹️ لوحة التحكم":
    st.title("🕹️ وحدة الإرسال الميداني")
    
    input_mode = st.selectbox("نمط العمل:", ["تلقائي (4 مواقع معاً)", "يدوي"])
    
    if input_mode == "تلقائي (4 مواقع معاً)":
        run_auto = st.toggle("🚀 بدء البث الجماعي (كل 1 ثانية)", value=False)
        if run_auto:
            st.success("📡 البث الجماعي نشط الآن... القراءات تُرسل للمواقع الأربعة معاً.")
            placeholder = st.empty()
            while run_auto:
                batch = [create_entry(n, random.randint(int(LOCATIONS[n]["avg"]*0.6), int(LOCATIONS[n]["avg"]*1.6))) for n in LOCATIONS.keys()]
                save_data(batch)
                with placeholder.container():
                    st.write(f"✅ تم بث نبضة بيانات شاملة عند: {datetime.now().strftime('%H:%M:%S')}")
                time.sleep(1)
                st.rerun()
    else:
        st.subheader("🎛️ التحكم اليدوي")
        for loc in LOCATIONS.keys():
            val = st.slider(f"تيار {loc}:", 0, 800, value=LOCATIONS[loc]["avg"], key=loc)
            if st.session_state.get(f"prev_{loc}") != val:
                save_data([create_entry(loc, val)])
                st.session_state[f"prev_{loc}"] = val

# --- 2. صفحة المراقبة (الجدول والرسم) ---
else:
    st.title("🖥️ مركز المراقبة والتحليل اللحظي")

    @st.fragment(run_every="1s")
    def update_monitor():
        data = load_data()
        
        # أ. الرسم البياني
        st.subheader("📊 المخطط الزمني للأحمال")
        if data:
            df_chart = pd.DataFrame(data)
            chart_data = df_chart.pivot_table(index='الوقت', columns='المنشأة', values='التيار (A)').ffill()
            st.line_chart(chart_data, height=250)
        else:
            st.info("بانتظار وصول البيانات لرسم المخطط...")

        # ب. الجدول (Data Table)
        st.subheader("📋 سجل البيانات الفني (Data Log)")
        if not data:
            st.warning("⚠️ السجل فارغ. يرجى تفعيل البث من 'لوحة التحكم'.")
            return
            
        df = pd.DataFrame(data)
        
        # منطق الفرز (البروتوكول)
        if protocol_active:
            # الترتيب: الخطر (level 3) أولاً، ثم الأحدث زمنياً
            df_display = df.sort_values(by=["level", "timestamp"], ascending=[False, False])
        else:
            df_display = df.sort_values(by="timestamp", ascending=False)

        # دالة التنسيق المصلحة لتجنب KeyError
        def style_rows(row):
            if row['level'] == 3: return ['background-color: #800000; color: white; font-weight: bold'] * len(row)
            if row['level'] == 2: return ['background-color: #705d00; color: white'] * len(row)
            return [''] * len(row)

        # عرض الأعمدة المطلوبة فقط مع التنسيق
        display_cols = ["المنشأة", "التيار (A)", "الحالة", "الوقت", "level"]
        st.dataframe(
            df_display[display_cols].style.apply(style_rows, axis=1),
            use_container_width=True, 
            height=450,
            column_config={"level": None} # إخفاء عمود المستوى تقنياً من العرض
        )

    update_monitor()
            
