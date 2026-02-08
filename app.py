import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# إعداد الصفحة - يجب أن يكون أول أمر
st.set_page_config(page_title="نظام طاقة الأنبار", layout="wide")

DB_FILE = "data_storage.json"

# إعدادات المنشآت
LOCATIONS = {
    "مستشفى الرمادي التعليمي": {"avg": 400, "priority": 10},
    "معمل زجاج الرمادي": {"avg": 500, "priority": 10},
    "جامعة الأنبار (المجمع)": {"avg": 350, "priority": 8},
    "حي التأميم (المغذي الرئيسي)": {"avg": 300, "priority": 7}
}

# دالات البيانات
def load_grid_data():
    if not os.path.exists(DB_FILE): return []
    try:
        with open(DB_FILE, "r") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except: return []

def save_grid_data(new_entries):
    history = load_grid_data()
    history.extend(new_entries)
    with open(DB_FILE, "w") as f:
        json.dump(history[-60:], f) # حفظ آخر 60 سجل فقط للسلاسة

def create_log(name, current):
    avg = LOCATIONS[name]["avg"]
    if current < avg: status, level = "🟢 مستقر", 1
    elif avg <= current < (avg * 1.2): status, level = "🟡 تنبيه", 2
    else: status, level = "🔴 خطر", 3
    return {
        "المنشأة": name, "التيار (A)": current, "الحالة": status,
        "الوقت": datetime.now().strftime("%H:%M:%S"),
        "ts": time.time(), "level": level, "p": LOCATIONS[name]["priority"]
    }

# --- القائمة الجانبية ---
st.sidebar.title("🛂 تحكم النظام")
page = st.sidebar.selectbox("القائمة:", ["🕹️ لوحة التحكم", "🖥️ شاشة المراقبة"])
protocol = st.sidebar.toggle("تفعيل البروتوكول الذكي", value=True)

if st.sidebar.button("🗑️ مسح السجل"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.rerun()

# --- الصفحة 1: لوحة التحكم ---
if page == "🕹️ لوحة التحكم":
    st.title("🕹️ وحدة الإرسال والتحكم")
    
    mode = st.radio("نمط الإرسال:", ["تلقائي (كل 1 ثانية)", "يدوي"])
    
    if mode == "تلقائي (كل 1 ثانية)":
        active = st.toggle("🚀 تشغيل البث الجماعي")
        if active:
            st.success("📡 البث نشط... يتم إرسال قراءات المواقع الأربعة معاً.")
            # إرسال البيانات
            batch = []
            for name in LOCATIONS.keys():
                val = random.randint(int(LOCATIONS[name]["avg"]*0.7), int(LOCATIONS[name]["avg"]*1.5))
                batch.append(create_log(name, val))
            save_grid_data(batch)
            # انتظار ثانية واحدة ثم إعادة التشغيل لعمل نبضة جديدة
            time.sleep(1)
            st.rerun()
    else:
        st.subheader("🎛️ إدخال يدوي")
        cols = st.columns(2)
        for i, name in enumerate(LOCATIONS.keys()):
            val = cols[i%2].slider(f"{name}", 0, 800, value=LOCATIONS[name]["avg"])
            if st.session_state.get(f"v_{name}") != val:
                save_grid_data([create_log(name, val)])
                st.session_state[f"v_{name}"] = val

# --- الصفحة 2: شاشة المراقبة ---
else:
    st.title("🖥️ شاشة المراقبة والتحليل")
    
    # تحديث تلقائي للجزء السفلي فقط كل ثانية
    container = st.container()
    
    data = load_grid_data()
    if not data:
        st.warning("⚠️ لا توجد بيانات. ابدأ البث من لوحة التحكم.")
    else:
        df = pd.DataFrame(data)
        
        # الرسم البياني
        st.subheader("📊 مخطط الأحمال اللحظي")
        chart_df = df.pivot_table(index='الوقت', columns='المنشأة', values='التيار (A)').ffill()
        st.line_chart(chart_df)

        # البروتوكول (الترتيب)
        if protocol:
            # يظهر كل شيء، لكن الخطر (level 3) يصعد للأعلى
            df_display = df.sort_values(by=["level", "ts"], ascending=[False, False])
        else:
            df_display = df.sort_values(by="ts", ascending=False)

        # الجدول
        st.subheader("📋 سجل البيانات المستلمة")
        def style_df(row):
            if "🔴" in row['الحالة']: return ['background-color: #800000; color: white'] * len(row)
            if "🟡" in row['الحالة']: return ['background-color: #705d00; color: white'] * len(row)
            return [''] * len(row)

        st.dataframe(
            df_display.drop(columns=['ts', 'level', 'p'], errors='ignore').style.apply(style_df, axis=1),
            use_container_width=True
        )
        
        # زر تحديث يدوي أو تركه يحدث مع البث
        time.sleep(1)
        st.rerun()
            
