import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# إعداد الصفحة - يجب أن يكون أول أمر
st.set_page_config(page_title="نظام طاقة الأنبار الذكي", layout="wide")

DB_FILE = "smart_grid_data.json"

# إعدادات المنشآت
LOCATIONS = {
    "مستشفى الرمادي التعليمي": {"avg": 400, "priority": 10},
    "معمل زجاج الرمادي": {"avg": 500, "priority": 10},
    "جامعة الأنبار (المجمع)": {"avg": 350, "priority": 8},
    "حي التأميم (المغذي الرئيسي)": {"avg": 300, "priority": 7}
}

# دالة لقراءة البيانات بأمان لمنع الانهيار
def get_data():
    if not os.path.exists(DB_FILE): return []
    try:
        with open(DB_FILE, "r") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except:
        return []

# دالة لحفظ البيانات
def save_data(entries):
    try:
        current_history = get_data()
        current_history.extend(entries)
        # نكتفي بآخر 40 سجل ليكون البرنامج خفيفاً وسريعاً
        with open(DB_FILE, "w") as f:
            json.dump(current_history[-40:], f)
    except:
        pass

def create_log_entry(name, current):
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
st.sidebar.title("🛂 وحدة التحكم")
page = st.sidebar.radio("القائمة:", ["🕹️ لوحة التحكم", "🖥️ شاشة المراقبة"])
protocol_on = st.sidebar.toggle("تفعيل البروتوكول الذكي", value=True)

if st.sidebar.button("🗑️ مسح السجلات"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.rerun()

# --- الصفحة 1: لوحة التحكم ---
if page == "🕹️ لوحة التحكم":
    st.title("🕹️ وحدة الإرسال الميداني")
    input_mode = st.radio("نمط الإرسال:", ["تلقائي (كل 1 ثانية)", "يدوي"])

    if input_mode == "تلقائي (كل 1 ثانية)":
        auto_run = st.toggle("🚀 تشغيل البث الجماعي")
        if auto_run:
            placeholder = st.empty()
            while auto_run:
                batch = [create_log_entry(n, random.randint(int(LOCATIONS[n]["avg"]*0.7), int(LOCATIONS[n]["avg"]*1.5))) for n in LOCATIONS.keys()]
                save_data(batch)
                with placeholder.container():
                    st.success(f"📡 جاري البث... آخر تحديث: {datetime.now().strftime('%H:%M:%S')}")
                time.sleep(1) # تأخير ثانية لمنع الضغط
                # لا نستخدم rerun هنا لضمان استقرار السيرفر
    else:
        st.subheader("🎛️ التحكم اليدوي")
        cols = st.columns(2)
        for i, name in enumerate(LOCATIONS.keys()):
            val = cols[i%2].slider(f"{name}", 0, 800, value=LOCATIONS[name]["avg"], key=name)
            if st.session_state.get(f"v_{name}") != val:
                save_data([create_log_entry(name, val)])
                st.session_state[f"v_{name}"] = val

# --- الصفحة 2: شاشة المراقبة ---
else:
    st.title("🖥️ شاشة المراقبة والتحليل")

    # استخدام st.fragment لتحديث الجدول والرسم البياني فقط بدون الصفحة كاملة
    @st.fragment(run_every=1.5)
    def update_dashboard():
        data = get_data()
        if not data:
            st.warning("⚠️ بانتظار البيانات... شغل البث من لوحة التحكم.")
            return

        df = pd.DataFrame(data)
        
        # الرسم البياني
        st.subheader("📊 مخطط توزيع الأحمال")
        chart_df = df.pivot_table(index='الوقت', columns='المنشأة', values='التيار (A)').ffill()
        st.line_chart(chart_df, height=300)

        # منطق البروتوكول
        if protocol_active := protocol_on:
            # الخطر (level 3) يصعد للأعلى فوراً
            df_display = df.sort_values(by=["level", "ts"], ascending=[False, False])
        else:
            df_display = df.sort_values(by="ts", ascending=False)

        # الجدول
        st.subheader("📋 السجل الفني للأحمال")
        def style_rows(row):
            if "🔴" in row['الحالة']: return ['background-color: #7b0000; color: white'] * len(row)
            if "🟡" in row['الحالة']: return ['background-color: #6d5c00; color: white'] * len(row)
            return [''] * len(row)

        st.dataframe(
            df_display.drop(columns=['ts', 'level', 'p'], errors='ignore').style.apply(style_rows, axis=1),
            use_container_width=True, height=400
        )

    update_dashboard()
    
