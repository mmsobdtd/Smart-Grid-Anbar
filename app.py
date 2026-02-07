import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# إعدادات الصفحة
st.set_page_config(page_title="نظام طاقة الأنبار - بث فائق السرعة", layout="wide")

DB_FILE = "anbar_fast_data.json"

def load_data():
    if not os.path.exists(DB_FILE): return []
    try:
        with open(DB_FILE, "r") as f:
            content = f.read()
            return json.loads(content) if content else []
    except: return []

def save_entry(location, current, category, weight):
    history = load_data()
    entry = {
        "المنشأة": location,
        "النوع": category,
        "التيار (A)": current,
        "التوقيت": datetime.now().strftime("%H:%M:%S.%f")[:-3], # توقيت دقيق بالملي ثانية
        "Priority": weight
    }
    history.append(entry)
    with open(DB_FILE, "w") as f:
        json.dump(history[-100:], f) # حفظ آخر 100 سجل

# --- القائمة الجانبية ---
st.sidebar.title("🛂 التحكم بالنظام")
mode = st.sidebar.toggle("تفعيل بروتوكول الأولويات", value=True)
role = st.sidebar.selectbox("اختر الواجهة:", ["المراقب (Dashboard)", "المحاكي (High Speed Simulator)"])

if st.sidebar.button("مسح السجل التاريخي"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.rerun()

# --- 1. واجهة المحاكي (إرسال كل نصف ثانية) ---
if role == "المحاكي (High Speed Simulator)":
    st.title("🚀 محاكي التدفق السريع - مدينة الرمادي")
    st.warning("تنبيه: الإرسال الآن مبرمج على (0.5 ثانية) لمحاكاة ضغط الشبكة الحقيقي.")
    
    locations = [
        {"n": "مستشفى الرمادي التعليمي", "c": "P1 - حرجة", "w": 10},
        {"n": "مصفى الأنبار النفطي", "c": "P1 - صناعي", "w": 9},
        {"n": "محطة مياه الرمادي", "c": "P2 - خدمي", "w": 8},
        {"n": "جامعة الأنبار", "c": "P2 - تعليمي", "w": 7},
        {"n": "ملعب الأنبار الأولمبي", "c": "P3 - بنية تحتية", "w": 5},
        {"n": "مول الرمادي", "c": "P3 - تجاري", "w": 4},
        {"n": "حي التأميم السكني", "c": "P4 - سكني", "w": 2}
    ]
    
    status = st.checkbox("بدء البث فائق السرعة")
    if status:
        placeholder = st.empty()
        while True:
            loc = random.choice(locations)
            val = random.randint(280, 580)
            save_entry(loc["n"], val, loc["c"], loc["w"])
            with placeholder.container():
                st.success(f"📡 جاري الإرسال: {loc['n']} -> {val}A")
                st.write(f"التوقيت: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
            time.sleep(0.5) # تعديل السرعة إلى نصف ثانية

# --- 2. واجهة المراقب (تحديث تلقائي) ---
else:
    st.title("🖥️ مركز التحكم والسيطرة اللحظي")
    
    @st.fragment(run_every="1s") # تحديث الشاشة كل ثانية لمواكبة البيانات
    def show_dashboard():
        data = load_data()
        if not data:
            st.info("بانتظار وصول البيانات... (يرجى تشغيل المحاكي في الصفحة الأخرى)")
            return

        df = pd.DataFrame(data)

        # منطق البروتوكول
        if mode:
            df['Score'] = df['Priority'] * 100 + df['التيار (A)']
            df_display = df.sort_values(by="Score", ascending=False)
        else:
            df_display = df.iloc[::-1]

        # الرسم البياني
        st.subheader("📈 التحليل البياني المباشر (Live Analysis)")
        # تجهيز البيانات للرسم البياني
        chart_data = df.pivot_table(index='التوقيت', columns='المنشأة', values='التيار (A)').ffill()
        st.line_chart(chart_data, height=350)

        # جدول البيانات
        st.subheader("📋 سجل البيانات الفني المستلم")
        def style_df(row):
            if row['Priority'] >= 9 and row['التيار (A)'] >= 400:
                return ['background-color: #7b0000; color: white; font-weight: bold'] * len(row)
            return [''] * len(row)

        st.dataframe(df_display.style.apply(style_df, axis=1), use_container_width=True, height=450)

    show_dashboard()
    
