import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime

# إعدادات الصفحة
st.set_page_config(page_title="Al-Anbar Smart Grid - Full System", layout="wide")

# --- 1. تهيئة الذاكرة والسجلات (Session State) ---
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["الوقت", "المحطة", "التيار", "الحرارة", "الحمل", "الحالة"])
if 'net_raw' not in st.session_state: st.session_state.net_raw = 0
if 'net_proto' not in st.session_state: st.session_state.net_proto = 0
if 'transformers' not in st.session_state:
    st.session_state.transformers = {
        f"محولة {i}": {"active": True, "last_i": 60.0, "temp": 45.0, "reason": "طبيعي ✅"} for i in range(1, 5)
    }

# --- 2. واجهة العناوين ---
st.title("⚡ منظومة السيطرة والحماية الذكية - محافظة الأنبار")
st.write(f"**المهندس:** محمد نبيل | **مركز السيطرة الرئيسي** | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# --- 3. قسم ضغط الشبكة (البروتوكول) ---
st.subheader("🌐 مراقبة ضغط البيانات (Network Data Stress)")
n_col1, n_col2 = st.columns(2)

# محاكاة حجم البيانات
inc_raw = np.random.randint(100, 150)
inc_proto = np.random.randint(10, 25)
st.session_state.net_raw += inc_raw
st.session_state.net_proto += inc_proto

with n_col1:
    st.write("📡 **بدون بروتوكول (إرسال عشوائي)**")
    st.progress(min(inc_raw/200, 1.0))
    st.metric("الحجم التراكمي", f"{st.session_state.net_raw} KB", f"+{inc_raw} KB/s", delta_color="inverse")

with n_col2:
    st.write("🔐 **ببروتوكول ذكي (بيانات منظمة)**")
    st.progress(min(inc_proto/200, 1.0))
    st.metric("الحجم التراكمي", f"{st.session_state.net_proto} KB", f"+{inc_proto} KB/s")

st.divider()

# --- 4. كروت التحكم اليدوي (القديم المطور) ---
st.subheader("🎮 وحدة التحكم اليدوي وفصل المحطات")
t_cols = st.columns(4)
max_cap = 150.0

current_readings = []

for idx, (name, state) in enumerate(st.session_state.transformers.items()):
    if state["active"]:
        # محاكاة البيانات مع احتمالية "Short Circuit"
        change = np.random.uniform(-5, 10)
        if np.random.rand() < 0.01: change = 70 # شورت مفاجئ
        
        new_i = max(0, min(180, state["last_i"] + change))
        new_t = max(30, min(110, state["temp"] + (change * 0.3)))
        load_pct = (new_i / max_cap) * 100
        
        # --- منطق الحماية التلقائي ---
        reason = "طبيعي ✅"
        if (new_i - state["last_i"]) > 50: 
            state["active"], reason = False, "🚨 Short Circuit"
        elif load_pct > 95: 
            state["active"], reason = False, "🔥 Overload > 95%"
        elif new_t > 90: 
            state["active"], reason = False, "🌡️ Overheat > 90C"
        
        state["last_i"], state["temp"], state["reason"] = new_i, new_t, reason
    else:
        new_i, new_t, load_pct = 0.0, 30.0, state["reason"]

    # عرض كرت التحكم
    with t_cols[idx]:
        st.markdown(f"### {name}")
        st.metric("الحمل الحالي", f"{load_pct:.1f}%")
        if state["active"]:
            if st.button(f"فصل {name}", key=f"trip_{name}"):
                state["active"], state["reason"] = False, "🛑 فصل يدوي"
                st.rerun()
        else:
            if st.button(f"تشغيل {name}", key=f"on_{name}"):
                state["active"], state["reason"] = True, "طبيعي ✅"
                st.rerun()

    # تجهيز القراءات للجدول
    prio = 1 if not state["active"] or load_pct > 90 else (2 if load_pct > 75 else 3)
    reading = {
        "الوقت": datetime.now().strftime('%H:%M:%S'),
        "المحطة": name,
        "التيار (A)": round(new_i, 1),
        "الحرارة (C°)": round(new_t, 1),
        "الحمل (%)": round(load_pct, 1),
        "الحالة": state["reason"],
        "p": prio
    }
    current_readings.append(reading)
    # الأرشفة (إضافة للسجل التاريخي)
    st.session_state.history = pd.concat([pd.DataFrame([reading]), st.session_state.history], ignore_index=True).head(200)

st.divider()

# --- 5. جدول القراءات اللحظية المفرز ---
col_table, col_sort = st.columns([3, 1])
with col_table: st.subheader("📋 القراءات الحالية (فرز الأولوية)")
with col_sort: sort_on = st.toggle("تفعيل الفرز (الأخطر أولاً)", value=True)

df_now = pd.DataFrame(current_readings)
if sort_on: df_now = df_now.sort_values("p")

st.table(df_now.drop(columns=['p']).style.applymap(
    lambda x: 'background-color: #ff4b4b; color: white' if '🚨' in str(x) or '🔥' in str(x) or '🛑' in str(x) else 
    ('background-color: #ffa500' if 'Overload' in str(x) else ''), subset=['الحالة']
))

# --- 6. سجل الأرشفة التاريخي ---
st.divider()
st.subheader("📜 سجل الأرشفة التاريخي (Historical Log)")
st.write("هذا السجل يحفظ كافة البيانات السابقة للرجوع إليها عند حدوث عطل:")
st.dataframe(st.session_state.history.drop(columns=['p']), use_container_width=True, hide_index=True)

# تحديث تلقائي
time.sleep(1.5)
st.rerun()
