import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# إعدادات الصفحة الرسمية (تصحيح السطر 9 الشهير)
st.set_page_config(page_title="Ramadi Industrial Grid Control", layout="wide")

DB_FILE = "anbar_grid_system.json"

# دالة إدارة البيانات
def load_data():
    if not os.path.exists(DB_FILE): return []
    try:
        with open(DB_FILE, "r") as f: return json.load(f)
    except: return []

def save_entry(location, current, category, weight):
    history = load_data()
    entry = {
        "المنشأة": location,
        "نوع الحمل": category,
        "التيار (A)": current,
        "التوقيت": datetime.now().strftime("%H:%M:%S"),
        "الوزن": weight # لترتيب الأولويات الهندسية
    }
    history.append(entry)
    with open(DB_FILE, "w") as f:
        json.dump(history[-80:], f) # حفظ آخر 80 إدخال للسجلات الزمنية

# --- القائمة الجانبية (Sidebar) ---
st.sidebar.title("🛡️ مركز التحكم القومي")
st.sidebar.markdown("---")
mode = st.sidebar.toggle("تفعيل بروتوكول الأولويات (Smart Mode)", value=True)
role = st.sidebar.selectbox("الدور التشغيلي:", ["المراقب العام (Dashboard)", "محاكي الأحمال (7 مواقع)"])

if st.sidebar.button("مسح سجل البيانات"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.rerun()

# --- 1. محاكي المنشآت (7 مواقع مشهورة في الأنبار) ---
if role == "محاكي المنشآت (7 مواقع)":
    st.title("🚀 محاكي التدفق الميداني - الأنبار")
    st.info("النظام يحاكي الآن 7 منشآت بأحمال ثقيلة ومتقاربة (300A - 550A).")
    
    locations = [
        {"name": "مستشفى الرمادي التعليمي", "cat": "حرجة (P1)", "w": 10},
        {"name": "معمل سمنت كبيسة", "cat": "صناعي ثقيل (P1)", "w": 9},
        {"name": "جامعة الأنبار - المجمع الرئيسي", "cat": "تعليمي (P2)", "w": 7},
        {"name": "مول الرمادي الكبير", "cat": "تجاري (P2)", "w": 6},
        {"name": "محطة مياه الرمادي الكبرى", "cat": "خدمي (P1)", "w": 9},
        {"name": "ملعب الأنبار الأولمبي", "cat": "بنية تحتية (P3)", "w": 5},
        {"name": "مصفى الأنبار النفطي", "cat": "صناعي ثقيل (P1)", "w": 9}
    ]
    
    if st.checkbox("بدء المحاكاة التلقائية (إرسال كل 4 ثوانٍ)"):
        while True:
            loc = random.choice(locations)
            # أحمال عالية متقاربة لمحاكاة الضغط
            val = random.randint(280, 580)
            save_entry(loc["name"], val, loc["cat"], loc["w"])
            st.toast(f"إرسال: {loc['name']} بقيمة {val}A")
            time.sleep(4)

# --- 2. واجهة المراقب (الرسمية والرسومية) ---
else:
    st.title("🖥️ نظام مراقبة استقرار الشبكة الذكية")
    st.caption("جامعة الأنبار - كلية الهندسة | قسم الكهرباء")
    
    @st.fragment(run_every="2s")
    def render_dashboard():
        data = load_data()
        if not data:
            st.warning("بانتظار استقبال البيانات من الحقل...")
            return

        df = pd.DataFrame(data)

        # منطق البروتوكول (Sorting Logic)
        if mode:
            # ترتيب حسب (الأولوية الهندسية * القيمة) لإبراز الأخطر
            df['Score'] = df['الوزن'] * 100 + df['التيار (A)']
            df_display = df.sort_values(by="Score", ascending=False)
        else:
            # ترتيب عشوائي حسب وقت الوصول (Chaos)
            df_display = df.iloc[::-1]

        # --- القسم الأول: المؤشرات (Metrics) ---
        cols = st.columns(4)
        unique_locs = df.drop_duplicates(subset=['المنشأة'], keep='last').tail(4)
        for i, (idx, row) in enumerate(unique_locs.iterrows()):
            cols[i].metric(row['المنشأة'], f"{row['التيار (A)']} A", f"P{row['الوزن']}")

        st.markdown("---")

        # --- القسم الثاني: الرسم البياني (Focus on Visuals) ---
        st.subheader("📈 تحليل استقرارية الأحمال (Real-time Load Analysis)")
        # تحضير البيانات للرسم البياني الزمني
        chart
        
