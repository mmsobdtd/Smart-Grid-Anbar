import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# إعدادات الصفحة الرسمية
st.set_page_config(page_title="نظام طاقة الأنبار - محاكاة البروتوكول", layout="wide")

DB_FILE = "anbar_grid_sync.json"

# --- إعدادات المنشآت والمتوسطات المرجعية ---
LOCATIONS = {
    "مستشفى الرمادي التعليمي": {"avg": 400, "priority": 10},
    "معمل زجاج الرمادي": {"avg": 500, "priority": 10},
    "جامعة الأنبار (المجمع)": {"avg": 350, "priority": 8},
    "حي التأميم (المغذي الرئيسي)": {"avg": 300, "priority": 7}
}

def load_data():
    if not os.path.exists(DB_FILE): return []
    try:
        with open(DB_FILE, "r") as f: return json.load(f)
    except: return []

def save_entry(name, current):
    history = load_data()
    avg = LOCATIONS[name]["avg"]
    if current < avg: status, level = "🟢 مستقر", 1
    elif avg <= current < (avg * 1.2): status, level = "🟡 تنبيه", 2
    else: status, level = "🔴 خطر", 3

    entry = {
        "المنشأة": name,
        "التيار (A)": current,
        "الحالة": status,
        "الوقت": datetime.now().strftime("%H:%M:%S.%f")[:-3],
        "level": level,
        "p": LOCATIONS[name]["priority"]
    }
    history.append(entry)
    with open(DB_FILE, "w") as f: json.dump(history[-40:], f)

# --- القائمة الجانبية للتنقل بين الوا
