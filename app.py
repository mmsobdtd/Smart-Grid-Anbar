import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime

# إعدادات الصفحة
st.set_page_config(page_title="Al-Anbar Grid - Integrated Log", layout="wide")

# --- 1. تهيئة الذاكرة (Session State) ---
if 'all_data_log' not in st.session_state:
    st.session_state.all_data_log = pd.DataFrame(columns=["الوقت", "المحطة", "V", "I", "P (kW)", "PF", "Load%", "الحالة", "p"])

if 'net_load' not in st.session_state: st.session_state.net_load = 0
if 'transformers' not in st.session_state:
    st.session_state.transformers = {f"محولة {i}": {"active": True, "last_i": 70} for i in range(1, 6)}

# --- 2. واجهة التحكم والعناوين ---
st.title("🏛️ وحدة الرصد المتكاملة وأرشفة البيانات - محافظة الأنبار")
st.write(f"**إعداد المهندس:** محمد نبيل | **مركز السيطرة الذكي** | {datetime.now().strftime('%H:%M:%S')}")

# مفتاح البروتوكول
protocol_on = st.sidebar.toggle("🔐 تفعيل بروتوكول الحماية والفرز", value=True)
if st.sidebar.button("♻️ تصفير السجل"):
    st.session_state.all_data_log = st.session_state.all_data_log.iloc[0:0]
    st.session_state.net_load = 0
    st.rerun()

# --- 3. محاكاة اختناق الشبكة ---
if not protocol_on:
    st.session_state.net_load += 15
    if st.session_state.net_load >= 100:
        st.error("🆘 انهيار النظام: الشبكة غير قادرة على معالجة البيانات العشوائية!")
        st.progress(1.0)
        st.stop()
else:
    st.session_state.net_load = max(5, st.session_state.net_load - 5)

st.subheader("🌐 حالة تدفق البيانات")
st.progress(st.session_state.net_load / 100)
st.caption(f"مستوى إجهاد الشبكة: {st.session_state.net_load}%")

st.divider()

# --- 4. توليد البيانات اللحظية (5 محولات) ---
new_readings = []
for name, state in st.session_state.transformers.items():
    if state["active"]:
        v = int(np.random.uniform(218, 225))
        i_val = int(np.random.uniform(60, 155))
        pf = round(np.random.uniform(0.85, 0.95), 2)
        p_kw = int((v * i_val * pf) / 1000)
        load_pct = int((i_val / 150) * 100)
        
        if load_pct >= 95: status, prio = "🚨 خطر", 1
        elif load_pct >= 80: status, prio = "⚠️ تنبيه", 2
        else: status, prio = "✅ طبيعي", 3
    else:
        v, i_val, p_kw, pf, load_pct, status, prio = 0, 0, 0, 0, 0, "🛑 مفصول", 4

    new_readings.append({
        "الوقت": datetime.now().strftime('%H:%M:%S'),
        "المحطة": name,
        "V": v, "I": i_val, "P (kW)": p_kw, "PF": pf,
        "Load%": load_pct, "الحالة": status, "p": prio
    })

# إضافة القراءات الجديدة للسجل العام (لحفظ القديم)
new_df = pd.DataFrame(new_readings)
st.session_state.all_data_log = pd.concat([new_df, st.session_state.all_data_log], ignore_index=True).head(500)

# --- 5. عرض أزرار التحكم اليدوي ---
st.subheader("🕹️ أزرار التحكم اليدوي")
c_btns = st.columns(5)
for idx, name in enumerate(st.session_state.transformers):
    with c_btns[idx]:
        if st.session_state.transformers[name]["active"]:
            if st.button(f"OFF {name}", key=f"off_{idx}"):
                st.session_state.transformers[name]["active"] = False
                st.rerun()
        else:
            if st.button(f"ON {name}", key=f"on_{idx}"):
                st.session_state.transformers[name]["active"] = True
                st.rerun()

st.divider()

# --- 6. الجدول الموحد (Live Log) ---
st.subheader("📋 سجل البيانات الموحد (Live & History)")

display_df = st.session_state.all_data_log.copy()

if protocol_on:
    # الفرز الذكي (الخطر يظهر في أعلى القائمة اللحظية)
    display_df = display_df.sort_values(["الوقت", "p"], ascending=[False, True])
    st.success("البروتوكول فعال: الفرز التلقائي للأولويات نشط.")
else:
    st.warning("البروتوكول معطل: البيانات تظهر بترتيب وصولها العشوائي.")

def style_row(val):
    if '🚨' in str(val): return 'background-color: #ff4b4b; color: white'
    if '⚠️' in str(val): return 'background-color: #fff3cd'
    if '✅' in str(val): return 'background-color: #d4edda'
    return ''

st.table(display_df.drop(columns=['p']).head(15).style.applymap(style_row, subset=['الحالة']))

st.divider()

# --- 7. خانة الاستعلام الخاص لكل محولة (Individual Analysis) ---
st.subheader("🔍 استعلام تاريخي مخصص")
selected_trans = st.selectbox("اختر المحولة لعرض سجلها التاريخي الخاص:", list(st.session_state.transformers.keys()))

history_filtered = st.session_state.all_data_log[st.session_state.all_data_log["المحطة"] == selected_trans]

st.write(f"عرض كافة القراءات السابقة لـ **{selected_trans}**:")
st.dataframe(history_filtered.drop(columns=['p']), use_container_width=True, hide_index=True)

# تحديث تلقائي
time.sleep(1.5)
st.rerun()
