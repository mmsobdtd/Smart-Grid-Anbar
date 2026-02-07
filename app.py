import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# إعدادات الصفحة الرسمية
st.set_page_config(page_title="Ramadi Smart City Grid Management", layout="wide")

DB_FILE = "ramadi_grid_data.json"

# دالة إدارة البيانات
def load_history():
    if not os.path.exists(DB_FILE): return []
    try:
        with open(DB_FILE, "r") as f: return json.load(f)
    except: return []

def save_entry(location, current, category, base_priority):
    history = load_history()
    entry = {
        "المنشأة": location,
        "التصنيف": category,
        "التيار (A)": current,
        "الوقت": datetime.now().strftime("%H:%M:%S"),
        "الأولوية": base_priority  # رقم يعبر عن أهمية المكان هندسياً
    }
    history.append(entry)
    # الاحتفاظ بآخر 60 سجل لمراقبة التطور الزمني
    with open(DB_FILE, "w") as f:
        json.dump(history[-60:], f)

# --- القائمة الجانبية ---
st.sidebar.title("🏢 إدارة طاقة مدينة الرمادي")
mode = st.sidebar.selectbox("نظام إدارة البروتوكول:", ["بروتوكول الأولويات الذكي (Active)", "التوزيع المتساوي (No Protocol)"])
role = st.sidebar.radio("الدور التشغيلي:", ["المراقب (غرفة التحكم)", "محاكي المنشآت (7 أماكن)"])

if st.sidebar.button("تصفير السجل التاريخي"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.rerun()

# --- 1. محاكي المنشآت السبعة (إرسال هادئ ومنظم) ---
if role == "محاكي المنشآت (7 أماكن)":
    st.title("🚀 محاكي التدفق الميداني")
    st.info("سيقوم المحاكي بإرسال بيانات استهلاك التيار من 7 مواقع حيوية كل 4 ثوانٍ.")
    
    # تعريف المنشآت مع وزن الأولوية (Base Priority)
    locations = [
        {"name": "مستشفى الرمادي التعليمي", "cat": "حرجة (P1)", "p": 10},
        {"name": "مصنع الأكسجين المركزي", "cat": "حرجة (P1)", "p": 10},
        {"name": "محطة مياه الرمادي الكبرى", "cat": "خدمية (P2)", "p": 8},
        {"name": "مبنى محافظة الأنبار", "cat": "حكومية (P2)", "p": 7},
        {"name": "جامعة الأنبار - كلية الهندسة", "cat": "تعليمية (P3)", "p": 5},
        {"name": "مول الرمادي التجاري", "cat": "تجارية (P3)", "p": 4},
        {"name": "حي الأندلس السكني", "cat": "سكنية (P4)", "p": 2}
    ]
    
    active_sim = st.checkbox("تفعيل البث التلقائي")
    if active_sim:
        while True:
            loc = random.choice(locations)
            val = random.randint(100, 500)
            save_entry(loc["name"], val, loc["cat"], loc["p"])
            st.toast(f"بث بيانات: {loc['name']} -> {val}A")
            time.sleep(4) # إرسال كل 4 ثوانٍ (هدوء العرض)

# --- 2. واجهة المراقب (الرسمية والتحليلية) ---
else:
    st.title("🖥️ مركز التحكم والسيطرة الوطني - الأنبار")
    st.write(f"الحالة الأمنية للشبكة: **{mode}**")

    @st.fragment(run_every="2s")
    def dashboard_update():
        history = load_history()
        if not history:
            st.info("بانتظار استلام إشارات من المحطات...")
            return

        df = pd.DataFrame(history)

        # منطق البروتوكول (Priority Sorting)
        if mode == "بروتوكول الأولويات الذكي (Active)":
            # الترتيب حسب الأولوية الأساسية للمكان + شدة التيار
            df['Final_Score'] = df['الأولوية'] * 100 + df['التيار (A)']
            df_display = df.sort_values(by="Final_Score", ascending=False)
        else:
            # ترتيب عشوائي حسب وقت الوصول فقط
            df_display = df.iloc[::-1]

        # 1. عدادات الحالة (Metrics) لأهم 4 منشآت
        st.subheader("📍 مراقبة الأحمال الحالية")
        m_cols = st.columns(4)
        top_4 = df.drop_duplicates(subset=['المنشأة'], keep='last').tail(4)
        for i, (idx, row) in enumerate(top_4.iterrows()):
            m_cols[i].metric(row['المنشأة'], f"{row['التيار (A)']} A", row['التصنيف'])

        st.markdown("---")

        # 2. الرسم البياني الزمني (احترافي)
        st.subheader("📊 المخطط البياني لتذبذب الطاقة")
        chart_df = df.pivot_table(index='الوقت', columns='المنشأة', values='التيار (A)').ffill()
        st.line_chart(chart_df, height=300)

        # 3. سجل البيانات التسلسلي
        st.subheader("📋 السجل التاريخي لاستلام الحزم (Data Logging)")
        
        def style_logic(row):
            if row['الأولوية'] >= 9 and row['التيار (A)'] >= 300: # مستشفى أو أكسجين
                return ['background-color: #580000; color: white; font-weight: bold'] * len(row)
            elif row['التيار (A)'] >= 300:
                return ['background-color: #664d03; color: white'] * len(row)
            return [''] * len(row)

        st.dataframe(
            df_display.drop(columns=['الأولوية', 'Final_Score'], errors='ignore').style.apply(style_logic, axis=1),
            use_container_width=True,
            height=400
        )

    dashboard_update()
        
