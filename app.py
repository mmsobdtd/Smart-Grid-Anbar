import streamlit as st
import pandas as pd
import json
import os
import time
from datetime import datetime

# إعدادات الصفحة الرسمية (تم تصحيح السطر 9 هنا)
st.set_page_config(page_title="Smart Grid Monitoring System", layout="wide")

DB_FILE = "grid_history.json"

# دالة إدارة سجل البيانات
def load_history():
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_to_history(station, current):
    history = load_history()
    new_entry = {
        "المحطة": station,
        "التيار (A)": current,
        "الوقت": datetime.now().strftime("%H:%M:%S"),
        "الحالة": "Critical" if current >= 300 else ("Stable" if current <= 250 else "Warning")
    }
    history.append(new_entry)
    # الاحتفاظ بآخر 100 سجل فقط لضمان كفاءة النظام
    with open(DB_FILE, "w") as f:
        json.dump(history[-100:], f)

# --- القائمة الجانبية ---
st.sidebar.markdown("### ⚙️ إدارة النظام")
role = st.sidebar.radio("تحديد الصلاحية:", ["طالب (إرسال بيانات)", "المراقب (غرفة التحكم)"])
if st.sidebar.button("تهيئة السجل (Clear Log)"):
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    st.rerun()

# --- واجهة الطالب (إرسال البيانات) ---
if role == "طالب (إرسال بيانات)":
    st.title("📲 وحدة إدخال البيانات الميدانية")
    station_id = st.selectbox("اختر المحطة:", [f"Station {i}" for i in range(1, 5)])
    
    val = st.slider("قيمة التيار المقاسة (Amperes):", 0, 600, 200, step=5)
    
    if st.button("تأكيد وإرسال"):
        save_to_history(station_id, val)
        st.success(f"تم تسجيل {val}A للمحطة {station_id}")

# --- واجهة المراقب الرسمية (تحديث تلقائي) ---
else:
    st.title("🖥️ مركز مراقبة الشبكة الذكية - جامعة الأنبار")
    st.markdown("---")

    @st.fragment(run_every="1s")
    def monitor_dashboard():
        history = load_history()
        if not history:
            st.info("بانتظار استقبال أول حزمة بيانات من المحطات...")
            return

        df = pd.DataFrame(history)
        
        # 1. حالة المحطات اللحظية (أعلى الشاشة)
        st.subheader("📍 آخر القراءات المستلمة")
        cols = st.columns(4)
        for i in range(1, 5):
            s_name = f"Station {i}"
            s_data = df[df["المحطة"] == s_name]
            if not s_data.empty:
                latest = s_data.iloc[-1]
                cols[i-1].metric(label=s_name, value=f"{latest['التيار (A)']} A", delta=latest['الحالة'])

        st.markdown("---")

        # 2. الرسم البياني (تطور الأحمال)
        st.subheader("📊 الرسم البياني الزمني للأحمال (Live Load Graph)")
        chart_data = df.pivot_table(index='الوقت', columns='المحطة', values='التيار (A)').ffill()
        st.line_chart(chart_data, height=350)

        # 3. سجل البيانات الكامل (Sequential Log)
        st.subheader("📋 سجل البيانات التراكمي (History Log)")
        
        # تنسيق الألوان للأحمال العالية
        def highlight_overload(row):
            return ['background-color: #ff4b4b; color: white' if row['التيار (A)'] >= 300 else ''] * len(row)

        # عرض الجدول (الأحدث يظهر في الأعلى)
        st.dataframe(
            df.iloc[::-1].style.apply(highlight_overload, axis=1),
            use_container_width=True,
            height=400
        )

    monitor_dashboard()
    
