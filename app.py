import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# إعدادات الصفحة الرسمية
st.set_page_config(page_title="Smart Grid Protocol Analysis", layout="wide")

DB_FILE = "grid_protocol_data.json"

# دالة إدارة البيانات
def load_history():
    if not os.path.exists(DB_FILE): return []
    try:
        with open(DB_FILE, "r") as f: return json.load(f)
    except: return []

def save_entry(station, current):
    history = load_history()
    entry = {
        "المحطة": station,
        "التيار (A)": current,
        "الوقت": datetime.now().strftime("%H:%M:%S.%f")[:-3], # وقت دقيق بالملي ثانية
        "الحالة": "CRITICAL" if current >= 300 else "NORMAL"
    }
    history.append(entry)
    with open(DB_FILE, "w") as f:
        json.dump(history[-100:], f) # حفظ آخر 100 حركة فقط

# --- القائمة الجانبية للتحكم ---
st.sidebar.title("🛠️ لوحة التحكم بالنظام")
mode = st.sidebar.toggle("تفعيل البروتوكول الذكي (Priority Protocol)", value=True)
role = st.sidebar.selectbox("الدور:", ["المراقب (غرفة التحكم)", "طالب (إرسال يدوي)", "محاكي الإدخال التلقائي"])

if st.sidebar.button("مسح السجل بالكامل"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.rerun()

# --- 1. واجهة الإدخال التلقائي السريع ---
if role == "محاكي الإدخال التلقائي":
    st.title("🚀 محاكي الإدخال التلقائي (4 محطات)")
    st.warning("عند تفعيل هذا الخيار، سيتم إرسال بيانات عشوائية وسريعة من 4 مصادر لمحاكاة الضغط.")
    
    run_sim = st.checkbox("ابدأ المحاكاة الآن")
    if run_sim:
        while True:
            # إرسال بيانات عشوائية من الـ 4 محطات في نفس الوقت
            for i in range(1, 5):
                s_name = f"Station {i}"
                val = random.randint(100, 550) # توليد أحمال عشوائية
                save_entry(s_name, val)
            time.sleep(0.5) # إرسال كل نصف ثانية (سرعة عالية)
            st.toast("جاري إرسال حزم البيانات...")

# --- 2. واجهة الطالب (إرسال يدوي) ---
elif role == "طالب (إرسال يدوي)":
    st.title("📲 وحدة التحكم اليدوية")
    station_id = st.selectbox("اختر المحطة:", [f"Station {i}" for i in range(1, 5)])
    val = st.slider("القيمة:", 0, 600, 200)
    if st.button("إرسال"):
        save_entry(station_id, val)
        st.success("تم الإرسال")

# --- 3. واجهة المراقب (الرسمية والذكية) ---
else:
    st.title("🖥️ مركز مراقبة وتحليل البروتوكول")
    
    if mode:
        st.success("✅ وضع البروتوكول: يتم فرز البيانات حسب الأولوية (الأخطر أولاً)")
    else:
        st.error("⚠️ وضع الفوضى: البيانات تعرض حسب وقت الوصول بدون تنظيم (خطر الانهيار)")

    @st.fragment(run_every="1s")
    def update_dashboard():
        data = load_history()
        if not data:
            st.info("بانتظار وصول البيانات...")
            return

        df = pd.DataFrame(data)

        # تطبيق "البروتوكول" (الفرز)
        if mode:
            # فرز حسب التيار (الأعلى أولاً) ثم الوقت
            df_display = df.sort_values(by=["التيار (A)", "الوقت"], ascending=[False, False])
        else:
            # عرض كما هي (عشوائية أو حسب الوصول)
            df_display = df.iloc[::-1]

        # الرسم البياني المطور
        st.subheader("📊 تحليل تذبذب الأحمال")
        chart_df = df.pivot_table(index='الوقت', columns='المحطة', values='التيار (A)').ffill()
        st.line_chart(chart_df, height=300)

        # جدول البيانات الرسمي
        st.subheader("📋 سجل استلام الحزم (Data Packets Log)")
        
        def color_protocol(row):
            if mode and row['التيار (A)'] >= 300:
                return ['background-color: #9e0000; color: white'] * len(row)
            elif not mode and row['التيار (A)'] >= 300:
                return ['background-color: #444444; color: #ff4b4b'] * len(row)
            return [''] * len(row)

        st.dataframe(
            df_display.style.apply(color_protocol, axis=1),
            use_container_width=True,
            height=500
        )

    update_dashboard()
    
