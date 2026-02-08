import streamlit as st
import pandas as pd
import random
import time
from datetime import datetime

# السطر ده لازم يكون أول سطر برمجيا
st.set_page_config(page_title="نظام طاقة الأنبار", layout="wide")

# --- 1. إعدادات المنشآت ---
LOCATIONS_CONFIG = {
    "مستشفى الرمادي التعليمي": {"avg": 400, "priority": 10},
    "معمل زجاج الرمادي": {"avg": 500, "priority": 10},
    "جامعة الأنبار (المجمع)": {"avg": 350, "priority": 8},
    "حي التأميم (المغذي الرئيسي)": {"avg": 300, "priority": 7}
}

# تهيئة الذاكرة في المتصفح
if 'data_history' not in st.session_state:
    st.session_state.data_history = []
if 'simulation_active' not in st.session_state:
    st.session_state.simulation_active = False

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
    st.session_state.data_history.append(entry)
    if len(st.session_state.data_history) > 30:
        st.session_state.data_history.pop(0)

# --- 2. الواجهة الجانبية ---
with st.sidebar:
    st.title("⚙️ الإعدادات")
    mode = st.radio("الوضعية:", ["بدون بروتوكول (خطر الانهيار)", "بالبروتوكول الذكي"])
    st.markdown("---")
    sim_toggle = st.toggle("تشغيل البث التلقائي (0.5 ثانية)")
    st.session_state.simulation_active = sim_toggle
    
    if st.button("🗑️ مسح السجل"):
        st.session_state.data_history = []
        st.rerun()

# --- 3. الواجهة الرئيسية ---
st.title("🖥️ مركز السيطرة والتحكم - الأنبار")

# ميزة الـ Fragment لتحديث الجدول والرسم البياني فقط
@st.fragment(run_every=0.5 if st.session_state.simulation_active else None)
def dashboard_fragment():
    # توليد بيانات جديدة لو المحاكاة شغالة
    if st.session_state.simulation_active:
        name = random.choice(list(LOCATIONS_CONFIG.keys()))
        avg = LOCATIONS_CONFIG[name]["avg"]
        val = random.randint(int(avg*0.7), int(avg*1.5))
        add_entry(name, val)

    if not st.session_state.data_history:
        st.info("بانتظار البيانات... شغل البث التلقائي من الجانب.")
        return

    df = pd.DataFrame(st.session_state.data_history)

    # منطق العرض
    if mode == "بالبروتوكول الذكي":
        st.success("✅ نظام الأولويات فعال")
        df_display = df.sort_values(by=["level", "p"], ascending=[False, False])
    else:
        st.error("🚨 وضع الانهيار: البيانات تتدفق عشوائياً")
        df_display = df.iloc[::-1]

    # الرسم البياني
    st.subheader("📊 تحليل الأحمال")
    chart_df = df.pivot_table(index='الوقت', columns='المنشأة', values='التيار (A)').ffill()
    st.line_chart(chart_df, height=250)
    
    

    # الجدول
    def style_rows(row):
        if row['level'] == 3: return ['background-color: #800000; color: white'] * len(row)
        if row['level'] == 2: return ['background-color: #705d00; color: white'] * len(row)
        return [''] * len(row)

    st.dataframe(
        df_display.drop(columns=['level', 'p'], errors='ignore').style.apply(style_rows, axis=1),
        use_container_width=True,
        height=350
    )

# تشغيل الجزء المحدث
dashboard_fragment()
