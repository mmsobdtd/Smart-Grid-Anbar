import streamlit as st
import pandas as pd
import random
import time
from datetime import datetime

# إعدادات الصفحة الرسمية لجامعة الأنبار
st.set_page_config(page_title="نظام طاقة الأنبار - محاكاة البروتوكول", layout="wide")

# --- 1. إعدادات المنشآت والمتوسطات المرجعية ---
LOCATIONS_CONFIG = {
    "مستشفى الرمادي التعليمي": {"avg": 400, "priority": 10},
    "معمل زجاج الرمادي": {"avg": 500, "priority": 10},
    "جامعة الأنبار (المجمع)": {"avg": 350, "priority": 8},
    "حي التأميم (المغذي الرئيسي)": {"avg": 300, "priority": 7}
}

# تهيئة الذاكرة المؤقتة (Session State) لضمان سلاسة التحديث
if 'history' not in st.session_state:
    st.session_state.history = []

def add_entry(name, current):
    avg = LOCATIONS_CONFIG[name]["avg"]
    # منطق تصنيف الحالة بناءً على المتوسط
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
    # الحفاظ على آخر 30 سجل لضمان سرعة المتصفح
    if len(st.session_state.history) > 30:
        st.session_state.history.pop(0)

# --- 2. واجهة التحكم الجانبية ---
with st.sidebar:
    st.title("⚙️ غرفة التحكم والسيطرة")
    simulation_mode = st.radio("اختر وضعية الشبكة:", ["بدون بروتوكول (فوضى/انهيار)", "بالبروتوكول الذكي (أولوية)"])
    input_type = st.radio("نوع البث:", ["تلقائي (فائق السرعة)", "يدوي"])
    st.markdown("---")
    if st.button("🗑️ تصفير سجل البيانات"):
        st.session_state.history = []
        
