import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime

# إعدادات الصفحة
st.set_page_config(page_title="مركز سيطرة الأنبار المتكامل", layout="wide")

# --- تنسيق CSS مخصص ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; font-weight: bold; }
    .trip-btn { background-color: #ff4b4b; color: white; }
    th { background-color: #004a99 !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- تهيئة الذاكرة (Session State) ---
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["الوقت", "المحطة", "التيار", "الحرارة", "الحمل", "الحالة"])

if 'trans_state' not in st.session_state:
    st.session_state.trans_state = {
        f"محولة {i}": {
            "active": True, 
            "last_i": 60.0, 
            "temp": 45.0, 
            "reason": "عمل طبيعي",
            "is_manual": False
        } for i in range(1, 5)
    }

# --- وظائف الحماية ---
def trip_transformer(name, reason):
    st.session_state.trans_state[name]["active"] = False
    st.session_state.trans_state[name]["reason"] = reason
    st.toast(f"🚨 عطل في {name}: {reason}", icon="🔥")

# --- العنوان الرئيسي ---
st.title("🛡️ نظام الأنبار للسيطرة والحماية والأرشفة الذكي")
st.write(f"**المهندس المسؤول:** محمد نبيل | **توقيت النظام:** {datetime.now().strftime('%H:%M:%S')}")

# --- القائمة الجانبية لإعادة التشغيل ---
if st.sidebar.button("♻️ إعادة ضبط المنظومة وتشغيل الكل"):
    for name in st.session_state.trans_state:
        st.session_state.trans_state[name] = {"active": True, "last_i": 60.0, "temp": 45.0, "reason": "عمل طبيعي", "is_manual": False}
    st.rerun()

# --- قسم المعالجة والمحاكاة ---
current_readings = []
max_cap = 150.0 # السعة القصوى 150 أمبير

for name, state in st.session_state.trans_state.items():
    if state["active"]:
        # محاكاة تغير التيار
        change = np.random.uniform(-5, 8)
        # محاكاة "Short Circuit" عشوائي (احتمال 2%)
        if np.random.rand() < 0.02: change = 60 
        
        new_i = max(0, min(170, state["last_i"] + change))
        new_t = max(30, min(110, state["temp"] + (change * 0.3)))
        
        load_pct = (new_i / max_cap) * 100
        
        # --- منطق الحماية التلقائي ---
        if new_i - state["last_i"] > 50: # حماية من الارتفاع المفاجئ (Short Circuit)
            trip_transformer(name, "ارتفاع مفاجئ (Short Circuit)")
        elif load_pct > 95:
            trip_transformer(name, "تجاوز الحمل 95%")
        elif new_t > 90:
            trip_transformer(name, "ارتفاع حرارة حررجي")
        
        state["last_i"] = new_i
        state["temp"] = new_t
    else:
        new_i, new_t, load_pct = 0.0, 30.0, 0.0

    # تسجيل القراءة الحالية
    reading = {
        "الوقت": datetime.now().strftime('%H:%M:%S'),
        "المحطة": name,
        "التيار": round(new_i, 1),
        "الحرارة": round(new_t, 1),
        "الحمل": round(load_pct, 1),
        "الحالة": state["reason"] if not state["active"] else "طبيعي ✅"
    }
    current_readings.append(reading)
    
    # إضافة للسجل التاريخي (الأرشفة)
    new_row = pd.DataFrame([reading])
    st.session_state.history = pd.concat([new_row, st.session_state.history], ignore_index=True).head(100)

# --- عرض الجدول الرئيسي (Real-time Dashboard) ---
st.subheader("📊 لوحة القراءات اللحظية وأزرار التحكم")
df_now = pd.DataFrame(current_readings)

# إنشاء أعمدة لعرض أزرار الفصل اليدوي
cols = st.columns(len(st.session_state.trans_state))
for idx, name in enumerate(st.session_state.trans_state):
    with cols[idx]:
        st.markdown(f"### {name}")
        st.metric("الحمل", f"{df_now.iloc[idx]['الحمل']}%")
        if st.session_state.trans_state[name]["active"]:
            if st.button(f"🔴 فصل يدوياً", key=f"btn_{name}"):
                st.session_state.trans_state[name]["active"] = False
                st.session_state.trans_state[name]["reason"] = "فصل يدوي من الإدارة"
                st.rerun()
        else:
            st.error("مفصول")

st.divider()

# عرض الجدول الرئيسي بتنسيق واضح
st.dataframe(
    df_now,
    column_config={
        "الحمل": st.column_config.ProgressColumn("مستوى الحمل %", min_value=0, max_value=100, format="%d%%"),
        "التيار": st.column_config.NumberColumn("التيار (A)"),
        "الحرارة": st.column_config.NumberColumn("الحرارة (C°)")
    },
    use_container_width=True,
    hide_index=True
)

# --- قسم الأرشيف (Historical Data) ---
st.divider()
st.subheader("📜 سجل البيانات التاريخي (الأرشفة)")
st.write("هذا الجدول يحفظ القراءات السابقة ولا يحذفها لمراجعة سجل المحولات:")
st.dataframe(st.session_state.history, use_container_width=True, hide_index=True)

# تحديث آلي
time.sleep(1.5)
st.rerun()
