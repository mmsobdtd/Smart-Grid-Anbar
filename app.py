import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# --- السطر 9 المصحح (تأكد أنه أول أمر بعد الاستيراد) ---
st.set_page_config(page_title="مركز تحكم شبكة الأنبار", layout="wide")

DB_FILE = "anbar_data.json"

# دالة ذكية لإدارة البيانات مع معالجة الأخطاء
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
        "الوقت": datetime.now().strftime("%H:%M:%S"),
        "Priority": weight
    }
    history.append(entry)
    with open(DB_FILE, "w") as f:
        json.dump(history[-60:], f) # حفظ آخر 60 حركة

# --- القائمة الجانبية ---
st.sidebar.title("🛂 التحكم بالنظام")
mode = st.sidebar.toggle("تفعيل بروتوكول الأولويات", value=True)
role = st.sidebar.selectbox("اختر الواجهة:", ["المراقب (Dashboard)", "المحاكي (Simulator)"])

if st.sidebar.button("تفريغ البيانات"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.rerun()

# --- 2. واجهة المحاكي ---
if role == "المحاكي (Simulator)":
    st.title("🚀 محاكي الأحمال - مدينة الرمادي")
    locations = [
        {"n": "مستشفى الرمادي التعليمي", "c": "P1 - حرجة", "w": 10},
        {"n": "مصفى الأنبار النفطي", "c": "P1 - صناعي", "w": 9},
        {"n": "محطة مياه الرمادي", "c": "P2 - خدمي", "w": 8},
        {"n": "جامعة الأنبار", "c": "P2 - تعليمي", "w": 7},
        {"n": "ملعب الأنبار الأولمبي", "c": "P3 - بنية تحتية", "w": 5},
        {"n": "مول الرمادي", "c": "P3 - تجاري", "w": 4},
        {"n": "حي التأميم السكني", "c": "P4 - سكني", "w": 2}
    ]
    
    status = st.checkbox("بدء البث التلقائي (كل 3 ثوانٍ)")
    if status:
        st.write("🔄 جاري إرسال البيانات إلى السيرفر...")
        while True:
            loc = random.choice(locations)
            val = random.randint(250, 550)
            save_entry(loc["n"], val, loc["c"], loc["w"])
            time.sleep(3)
            st.rerun()

# --- 3. واجهة المراقب ---
else:
    st.title("🖥️ شاشة المراقبة والتحليل الذكي")
    
    @st.fragment(run_every="2s")
    def show_dashboard():
        data = load_data()
        if not data:
            st.info("بانتظار وصول البيانات من المحاكي... (افتح المحاكي وشغل البث)")
            return

        df = pd.DataFrame(data)

        # منطق البروتوكول
        if mode:
            df['Score'] = df['Priority'] * 100 + df['التيار (A)']
            df_display = df.sort_values(by="Score", ascending=False)
        else:
            df_display = df.iloc[::-1]

        # الرسم البياني
        st.subheader("📈 المخطط الزمني للأحمال")
        chart_data = df.pivot_table(index='الوقت', columns='المنشأة', values='التيار (A)').ffill()
        st.line_chart(chart_data)

        # الجدول
        st.subheader("📋 سجل البيانات الفني")
        def style_df(row):
            if row['Priority'] >= 9 and row['التيار (A)'] >= 400:
                return ['background-color: #800000; color: white'] * len(row)
            return [''] * len(row)

        st.dataframe(df_display.style.apply(style_df, axis=1), use_container_width=True)

    show_dashboard()
    
