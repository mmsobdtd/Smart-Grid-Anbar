import streamlit as st
import pandas as pd
import random
import time
from datetime import datetime

# إعدادات الصفحة
st.set_page_config(page_title="نظام طاقة الأنبار - محاكاة البروتوكول", layout="wide")

# --- 1. إعدادات المنشآت والمتوسطات المرجعية ---
LOCATIONS_CONFIG = {
    "مستشفى الرمادي التعليمي": {"avg": 400, "priority": 10},
    "معمل زجاج الرمادي": {"avg": 500, "priority": 10},
    "جامعة الأنبار (المجمع)": {"avg": 350, "priority": 8},
    "حي التأميم (المغذي الرئيسي)": {"avg": 300, "priority": 7}
}

# تهيئة الذاكرة المؤقتة (Session State)
if 'history' not in st.session_state:
    st.session_state.history = []

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
        "الحالة": status,
        "الوقت": datetime.now().strftime("%H:%M:%S.%f")[:-3],
        "level": level,
        "p": LOCATIONS_CONFIG[name]["priority"]
    }
    st.session_state.history.append(entry)
    # الحفاظ على آخر 30 سجل لضمان السلاسة
    if len(st.session_state.history) > 30:
        st.session_state.history.pop(0)

# --- 2. واجهة التحكم الجانبية ---
with st.sidebar:
    st.title("⚙️ غرفة التحكم")
    simulation_mode = st.radio("اختر وضعية الشبكة:", ["بدون بروتوكول (Chaos/Congestion)", "بالبروتوكول الذكي (Priority)"])
    input_type = st.radio("نوع البث:", ["تلقائي (0.5 ثانية)", "يدوي"])
    st.markdown("---")
    if st.button("🗑️ تصفير السجل"):
        st.session_state.history = []
        st.rerun()

# --- 3. الواجهة الرئيسية ---
st.title("🖥️ نظام إدارة أحمال مدينة الرمادي")
st.markdown(f"الحالة الحالية: **{simulation_mode}**")

# حاويات العرض (لضمان التحديث السلس)
metrics_area = st.empty()
dashboard_area = st.empty()

# --- 4. منطق توليد البيانات ---
if input_type == "تلقائي (0.5 ثانية)":
    name = random.choice(list(LOCATIONS_CONFIG.keys()))
    avg = LOCATIONS_CONFIG[name]["avg"]
    # توليد قيم عالية لمحاكاة ضغط الشبكة
    val = random.randint(int(avg*0.7), int(avg*1.6))
    add_entry(name, val)
else:
    # الوضع اليدوي باستخدام أعمدة
    cols = st.columns(4)
    for i, loc in enumerate(LOCATIONS_CONFIG.keys()):
        val = cols[i].slider(f"{loc.split()[0]}", 0, 800, value=LOCATIONS_CONFIG[loc]["avg"], key=loc)
        if st.session_state.get(f"prev_{loc}") != val:
            add_entry(loc, val)
            st.session_state[f"prev_{loc}"] = val

# --- 5. منطق العرض والفرز (البروتوكول vs الانهيار) ---
with dashboard_area.container():
    if st.session_state.history:
        df = pd.DataFrame(st.session_state.history)

        # السيناريو 1: بدون بروتوكول (الانهيار)
        if simulation_mode == "بدون بروتوكول (Chaos/Congestion)":
        
