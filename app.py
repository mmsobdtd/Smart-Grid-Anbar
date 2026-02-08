import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# إعدادات الصفحة
st.set_page_config(page_title="نظام طاقة الأنبار الذكي", layout="wide")

DB_FILE = "anbar_hybrid_grid.json"

# --- إعدادات المنشآت والمتوسطات ---
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
        "الوقت": datetime.now().strftime("%H:%M:%S.%f")[:-3],
        "level": level,
        "p": LOCATIONS_CONFIG[name]["priority"]
    }
    history.append(entry)
    with open(DB_FILE, "w") as f:
        json.dump(history[-80:], f)

# --- القائمة الجانبية ---
st.sidebar.title("🛂 لوحة التحكم المركزي")
st.sidebar.markdown("---")
input_mode = st.sidebar.radio("طريقة إدخال البيانات:", ["يدوي (تحريك الشريط)", "تلقائي (محاكاة)"])
protocol_mode = st.sidebar.toggle("تفعيل بروتوكول الأولوية", value=True)

if st.sidebar.button("مسح السجلات"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.rerun()

# تقسيم الصفحة إلى "إدخال" و "مراقبة"
col_input, col_monitor = st.columns([1, 2])

# --- 1. قسم إدخال البيانات ---
with col_input:
    st.header("📥 وحدة الإدخال")
    
    if input_mode == "يدوي (تحريك الشريط)":
        st.write("حرك المنزلق لإرسال البيانات لحظياً:")
        for loc_name in LOCATIONS_CONFIG.keys():
            # استخدام Session State لتتبع القيمة السابقة ومنع تكرار الإرسال غير الضروري
            current_val = st.slider(
                f"{loc_name} (Amps):", 
                0, 800, 
                value=LOCATIONS_CONFIG[loc_name]["avg"],
                key=f"slider_{loc_name}"
            )
            # الإرسال بمجرد تغيير القيمة (Streamlit يعيد التشغيل تلقائياً عند تغيير السلايدر)
            if st.session_state.get(f"prev_{loc_name}") != current_val:
                save_entry(loc_name, current_val)
                st.session_state[f"prev_{loc_name}"] = current_val

    else:
        st.write("البث التلقائي مفعل...")
        run_auto = st.checkbox("ابدأ المحاكاة (0.5 ثانية)")
        if run_auto:
            placeholder = st.empty()
            while True:
                name = random.choice(list(LOCATIONS_CONFIG.keys()))
                avg = LOCATIONS_CONFIG[name]["avg"]
                val = random.randint(int(avg*0.7), int(avg*1.5))
                save_entry(name, val)
                with placeholder.container():
                    st.success(f"📡 يبث الآن: {name} -> {val}A")
                time.sleep(0.5)
                st.rerun()

# --- 2. قسم المراقبة (Dashboard) ---
with col_monitor:
    st.header("🖥️ شاشة المراقبة والتحليل")
    
    @st.fragment(run_every="1s")
    def update_dashboard():
        data = load_data()
        if not data:
            st.info("بانتظار وصول البيانات...")
            return

        df = pd.DataFrame(data)

        # ترتيب البيانات (البروتوكول)
        if protocol_mode:
            df_display = df.sort_values(by=["level", "p"], ascending=[False, False])
        else:
            df_display = df.iloc[::-1]

        # الرسم البياني
        st.subheader("📊 تحليل الرسم البياني")
        chart_df = df.pivot_table(index='الوقت', columns='المنشأة', values='التيار (A)').ffill()
        st.line_chart(chart_df, height=300)

        # جدول البيانات
        st.subheader("📋 سجل البيانات الفني")
        def style_rows(row):
            if "🔴" in row['الحالة']: return ['background-color: #800000; color: white'] * len(row)
            if "🟡" in row['الحالة']: return ['background-color: #856404; color: white'] * len(row)
            return [''] * len(row)

        st.dataframe(
            df_display.drop(columns=['level', 'p'], errors='ignore').style.apply(style_rows, axis=1),
            use_container_width=True,
            height=400
        )

    update_dashboard()
        
