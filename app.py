import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# إعدادات الصفحة الرسمية
st.set_page_config(page_title="نظام مراقبة الطاقة الذكي - الأنبار", layout="wide")

DB_FILE = "anbar_auto_grid.json"

# --- إعدادات المنشآت والمتوسطات المرجعية ---
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
        "الوقت": datetime.now().strftime("%H:%M:%S.%f")[:-1],
        "level": level,
        "p": LOCATIONS_CONFIG[name]["priority"]
    }
    history.append(entry)
    with open(DB_FILE, "w") as f:
        json.dump(history[-50:], f)

# --- واجهة المستخدم ---
st.title("🖥️ مركز التحكم والسيطرة الوطني - الأنبار")
st.markdown("---")

with st.sidebar:
    st.header("🛂 إعدادات النظام")
    input_mode = st.radio("وضع الإدخال:", ["تلقائي (بث فائق السرعة)", "يدوي (تحكم لحظي)"])
    protocol_mode = st.sidebar.toggle("تفعيل الفرز الذكي (Priority)", value=True)
    st.markdown("---")
    if st.button("🗑️ مسح السجلات"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.rerun()

col_input, col_monitor = st.columns([1, 2], gap="large")

# --- 1. قسم الإدخال (التشغيل التلقائي) ---
with col_input:
    st.subheader("📥 بوابة البيانات")
    
    if input_mode == "تلقائي (بث فائق السرعة)":
        st.success("✅ البث التلقائي نشط الآن (0.5 ثانية)")
        
        # مصفوفة للمواقع للتحديث الدوري
        locations = list(LOCATIONS_CONFIG.keys())
        # استخدام session_state للحفاظ على العداد عند إعادة التشغيل
        if 'idx' not in st.session_state:
            st.session_state.idx = 0
            
        name = locations[st.session_state.idx % len(locations)]
        avg = LOCATIONS_CONFIG[name]["avg"]
        val = random.randint(int(avg*0.8), int(avg*1.4))
        
        save_entry(name, val)
        st.session_state.idx += 1
        
        # عرض المقياس الحالي
        st.metric(label=f"بث حي: {name}", value=f"{val} A", delta=f"{val-avg} vs Avg")
        
        # التحديث التلقائي الفوري
        time.sleep(0.5)
        st.rerun()

    else:
        st.write("حرك المنزلق للإرسال الفوري:")
        for loc_name in LOCATIONS_CONFIG.keys():
            val = st.slider(f"{loc_name}:", 0, 800, value=LOCATIONS_CONFIG[loc_name]["avg"], key=loc_name)
            if st.session_state.get(f"v_{loc_name}") != val:
                save_entry(loc_name, val)
                st.session_state[f"v_{loc_name}"] = val

# --- 2. قسم المراقبة والتحليل ---
with col_monitor:
    st.subheader("📊 لوحة التحليل اللحظي")
    
    @st.fragment(run_every="1s")
    def update_dashboard():
        data = load_data()
        if not data:
            st.info("بانتظار البيانات...")
            return

        df = pd.DataFrame(data)

        if protocol_mode:
            df_display = df.sort_values(by=["level", "p"], ascending=[False, False])
        else:
            df_display = df.iloc[::-1]

        chart_df = df.pivot_table(index='الوقت', columns='المنشأة', values='التيار (A)').ffill()
        st.line_chart(chart_df, height=300)

        st.markdown("##### 📋 سجل تدفق البيانات")
        
        def highlight_status(row):
            if "🔴" in row['الحالة']: return ['background-color: #7b0000; color: white'] * len(row)
            if "🟡" in row['الحالة']: return ['background-color: #6d5c00; color: white'] * len(row)
            return [''] * len(row)

        st.dataframe(
            df_display.drop(columns=['level', 'p'], errors='ignore').style.apply(highlight_status, axis=1),
            use_container_width=True,
            height=350
        )

    update_dashboard()
    
