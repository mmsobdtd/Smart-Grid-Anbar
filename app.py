import streamlit as st
import pandas as pd
import random
import time
from datetime import datetime

# --- السطر الأول: إعدادات الصفحة (يجب أن يبقى الأول) ---
st.set_page_config(page_title="نظام طاقة الأنبار الذكي", layout="wide")

# 1. إعدادات المنشآت والمتوسطات
LOCATIONS_CONFIG = {
    "مستشفى الرمادي التعليمي": {"avg": 400, "priority": 10},
    "معمل زجاج الرمادي": {"avg": 500, "priority": 10},
    "جامعة الأنبار (المجمع)": {"avg": 350, "priority": 8},
    "حي التأميم (المغذي الرئيسي)": {"avg": 300, "priority": 7}
}

# 2. تهيئة الذاكرة (Session State)
if 'data_history' not in st.session_state:
    st.session_state.data_history = []

def add_entry(name, current):
    avg = LOCATIONS_CONFIG[name]["avg"]
    if current < avg:
        status, level = "🟢 مستقر", 1
    elif avg <= current < (avg * 1.2):
        status, level = "🟡 تنبيه", 2
    else:
        status, level = "🔴 خطر", 3

    entry = {
        "المنشأة": name,
        "التيار (A)": current,
        "المتوسط": avg,
        "الحالة": status,
        "الوقت": datetime.now().strftime("%H:%M:%S.%f")[:-3],
        "level": level,
        "p": LOCATIONS_CONFIG[name]["priority"]
    }
    # إضافة البيانات في البداية لتظهر بشكل متسلسل
    st.session_state.data_history.append(entry)
    if len(st.session_state.data_history) > 40:
        st.session_state.data_history.pop(0)

# --- 3. تصميم الواجهة الجانبية ---
with st.sidebar:
    st.title("⚙️ التحكم بالنظام")
    mode = st.radio("وضعية التشغيل:", ["بالبروتوكول الذكي (منظم)", "بدون بروتوكول (خطر الانهيار)"])
    input_method = st.radio("طريقة الإدخال:", ["يدوي (Sliders)", "تلقائي (Fast 0.5s)"])
    if st.button("🗑️ مسح السجل"):
        st.session_state.data_history = []
        st.rerun()

# --- 4. تقسيم الشاشة إلى عمودين (صفحتين متجاورتين) ---
col_input, col_display = st.columns([1, 2], gap="large")

# --- القسم الأول (اليمين): وحدة الإدخال ---
with col_input:
    st.header("📥 وحدة الإدخال")
    if input_method == "يدوي (Sliders)":
        st.write("حرك الشريط لإرسال البيانات:")
        for loc in LOCATIONS_CONFIG.keys():
            val = st.slider(f"{loc}:", 0, 800, value=LOCATIONS_CONFIG[loc]["avg"], key=loc)
            # إرسال البيانات إذا تغيرت القيمة
            if st.session_state.get(f"prev_{loc}") != val:
                add_entry(loc, val)
                st.session_state[f"prev_{loc}"] = val
    else:
        st.success("البث التلقائي نشط...")
        # منطق التحديث التلقائي
        name = random.choice(list(LOCATIONS_CONFIG.keys()))
        avg = LOCATIONS_CONFIG[name]["avg"]
        val = random.randint(int(avg*0.7), int(avg*1.6))
        add_entry(name, val)
        time.sleep(0.5)
        st.rerun()

# --- القسم الثاني (اليسار): شاشة المراقبة (الجدول والرسم) ---
with col_display:
    st.header("🖥️ شاشة المراقبة")
    
    if not st.session_state.data_history:
        st.info("بانتظار وصول البيانات...")
    else:
        df = pd.DataFrame(st.session_state.data_history)

        # أ. الرسم البياني (في الأعلى)
        st.subheader("📊 المخطط البياني للأحمال")
        chart_df = df.pivot_table(index='الوقت', columns='المنشأة', values='التيار (A)').ffill()
        st.line_chart(chart_df, height=250)

        # ب. الجدول (في الأسفل)
        st.subheader("📋 سجل البيانات الفني (Data Table)")
        
        # منطق البروتوكول (الفرز)
        if mode == "بالبروتوكول الذكي (منظم)":
            df_display = df.sort_values(by=["level", "p"], ascending=[False, False])
        else:
            df_display = df.iloc[::-1] # ترتيب حسب الوصول فقط (فوضى)

        # تنسيق ألوان الجدول
        def style_rows(row):
            if "🔴" in row['الحالة']: return ['background-color: #7b0000; color: white'] * len(row)
            if "🟡" in row['الحالة']: return ['background-color: #6d5c00; color: white'] * len(row)
            return [''] * len(row)

        st.dataframe(
            df_display.drop(columns=['level', 'p'], errors='ignore').style.apply(style_rows, axis=1),
            use_container_width=True,
            height=400
        )
        
