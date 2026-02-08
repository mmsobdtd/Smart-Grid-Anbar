import streamlit as st
import pandas as pd
import json
import os
import time
from datetime import datetime

# إعدادات الصفحة الرسمية
st.set_page_config(page_title="نظام إدارة أحمال الأنبار - إدخال يدوياً", layout="wide")

DB_FILE = "anbar_manual_grid.json"

# --- تعريف المنشآت والمتوسطات المرجعية ---
LOCATIONS_CONFIG = {
    "مستشفى الرمادي التعليمي": {"avg": 400, "priority": 10},
    "معمل زجاج الرمادي": {"avg": 500, "priority": 10},
    "جامعة الأنبار (المجمع)": {"avg": 350, "priority": 8},
    "حي التأميم (المغذي الرئيسي)": {"avg": 300, "priority": 7}
}

def load_data():
    if not os.path.exists(DB_FILE): return []
    try:
        with open(DB_FILE, "r") as f:
            content = f.read()
            return json.loads(content) if content else []
    except: return []

def save_entry(name, current):
    history = load_data()
    avg = LOCATIONS_CONFIG[name]["avg"]
    
    # منطق تصنيف الحالة بناءً على المتوسط
    if current < avg:
        status, level = "🟢 مستقر (Normal)", 1
    elif avg <= current < (avg * 1.2):
        status, level = "🟡 تنبيه (Warning)", 2
    else:
        status, level = "🔴 خطر (Critical)", 3

    entry = {
        "المنشأة": name,
        "التيار (A)": current,
        "المتوسط": avg,
        "الحالة": status,
        "الوقت": datetime.now().strftime("%H:%M:%S"),
        "level": level,
        "p": LOCATIONS_CONFIG[name]["priority"]
    }
    history.append(entry)
    with open(DB_FILE, "w") as f:
        json.dump(history[-100:], f)

# --- القائمة الجانبية ---
st.sidebar.title("🛂 وحدة التحكم")
mode = st.sidebar.toggle("تفعيل بروتوكول الأولوية", value=True)
role = st.sidebar.radio("اختر المهمة:", ["إدخال بيانات (الطالب)", "شاشة المراقبة (المراقب)"])

if st.sidebar.button("مسح السجلات"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.rerun()

# --- 1. واجهة إدخال البيانات (يدوياً) ---
if role == "إدخال بيانات (الطالب)":
    st.title("📥 وحدة إدخال البيانات الميدانية")
    st.info("قم باختيار المنشأة وإدخال قيمة التيار المقاسة حالياً.")
    
    col1, col2 = st.columns(2)
    with col1:
        name = st.selectbox("المنشأة المستهدفة:", list(LOCATIONS_CONFIG.keys()))
    with col2:
        current_val = st.number_input("قيمة التيار (Amps):", min_value=0, max_value=1000, value=LOCATIONS_CONFIG[name]["avg"])
    
    if st.button("إرسال البيانات إلى السيرفر"):
        save_entry(name, current_val)
        st.success(f"تم إرسال {current_val}A لـ {name} بنجاح!")
        st.balloons() # تأثير بصري عند الإرسال

# --- 2. واجهة المراقب (تحديث تلقائي) ---
else:
    st.title("🖥️ مركز المراقبة والتحليل اللحظي")
    st.caption("جامعة الأنبار - كلية الهندسة | مشروع إدارة الأحمال الذكية")

    @st.fragment(run_every="2s")
    def dashboard():
        data = load_data()
        if not data:
            st.warning("بانتظار استقبال أول حزمة بيانات... (اذهب لصفحة الإدخال أولاً)")
            return

        df = pd.DataFrame(data)

        # تطبيق البروتوكول (الفرز)
        if mode:
            df_display = df.sort_values(by=["level", "p"], ascending=[False, False])
        else:
            df_display = df.iloc[::-1]

        # --- الرسم البياني ---
        st.subheader("📊 تحليل الرسم البياني للأحمال")
        chart_df = df.pivot_table(index='الوقت', columns='المنشأة', values='التيار (A)').ffill()
        st.line_chart(chart_df, height=350)
        
        

        # --- جدول البيانات ---
        st.subheader("📋 سجل استلام الحزم (Data Logging)")
        
        def color_rows(row):
            if "🔴" in row['الحالة']:
                return ['background-color: #7b0000; color: white; font-weight: bold'] * len(row)
            elif "🟡" in row['الحالة']:
                return ['background-color: #6d5c00; color: white'] * len(row)
            return [''] * len(row)

        st.dataframe(
            df_display.drop(columns=['level', 'p'], errors='ignore').style.apply(color_rows, axis=1),
            use_container_width=True,
            height=400
        )

    dashboard()
    
