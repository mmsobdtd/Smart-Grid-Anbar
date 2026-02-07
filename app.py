import streamlit as st
import pandas as pd
import json
import os
import time
from datetime import datetime

# إعدادات الصفحة الرسمية
st.set_config(page_title="Smart Grid Monitoring System", layout="wide")

DB_FILE = "grid_history.json"

# دالة إدارة سجل البيانات (تخزين بصيغة القائمة لرؤية كل التحديثات)
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
        "الحالة": "🔴 حمل زائد" if current >= 300 else ("🟢 مستقر" if current <= 250 else "🟡 تحذير")
    }
    history.append(new_entry)
    # الاحتفاظ بآخر 100 إدخال فقط لضمان سرعة النظام
    with open(DB_FILE, "w") as f:
        json.dump(history[-100:], f)

# --- القائمة الجانبية ---
st.sidebar.markdown("### 🛠️ لوحة التحكم")
role = st.sidebar.radio("تحديد الدور:", ["طالب (إرسال بيانات)", "المراقب (غرفة التحكم)"])
if st.sidebar.button("مسح السجل بالكامل"):
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    st.rerun()

# --- واجهة الطالب ---
if role == "طالب (إرسال بيانات)":
    st.title("📲 وحدة إدخال البيانات")
    station_id = st.selectbox("اختر المحطة الخاصة بك:", [f"Station {i}" for i in range(1, 5)])
    
    val = st.slider("تعديل قيمة التيار (Amps):", 0, 600, 200, step=5)
    
    if st.button("إرسال التحديث"):
        save_to_history(station_id, val)
        st.success(f"تم تسجيل القيمة {val}A للمحطة {station_id}")

# --- واجهة المراقب الرسمية ---
else:
    st.title("🖥️ نظام مراقبة الشبكة الذكية - جامعة الأنبار")
    st.markdown("---")

    @st.fragment(run_every="1s")
    def monitor_dashboard():
        history = load_history()
        if not history:
            st.info("بانتظار استلام بيانات من الطلاب...")
            return

        df = pd.DataFrame(history)
        
        # 1. قسم المؤشرات العلوية (آخر قراءة لكل محطة)
        st.subheader("📍 الحالة اللحظية للمحطات")
        cols = st.columns(4)
        for i in range(1, 5):
            station_name = f"Station {i}"
            station_data = df[df["المحطة"] == station_name]
            if not station_data.empty:
                latest = station_data.iloc[-1]
                cols[i-1].metric(label=station_name, value=f"{latest['التيار (A)']} A", delta=latest['الحالة'])

        st.markdown("---")

        # 2. الرسم البياني المطور (تطور الأحمال مع الوقت)
        st.subheader("📊 تحليل الرسم البياني للأحمال")
        # ترتيب البيانات للرسم البياني
        chart_df = df.pivot(index='الوقت', columns='المحطة', values='التيار (A)').ffill()
        st.line_chart(chart_df, height=300)

        # 3. جدول البيانات الرسمي (سجل تاريخي كامل)
        st.subheader("📋 سجل استلام البيانات الكامل (History Log)")
        
        # تنسيق الجدول ليكون رسمياً
        def style_rows(row):
            if row['التيار (A)'] >= 300:
                return ['background-color: #ffcccc'] * len(row)
            return [''] * len(row)

        # عرض الجدول معكوساً (الأحدث في الأعلى)
        st.dataframe(
            df.iloc[::-1].style.apply(style_rows, axis=1),
            use_container_width=True,
            height=400
        )

    monitor_dashboard()
    
