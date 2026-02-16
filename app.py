import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime

# إعدادات الصفحة
st.set_page_config(page_title="Al-Anbar Smart Grid Control", layout="wide")

# --- 1. تهيئة الذاكرة والسجلات ---
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["الوقت", "المحطة", "التيار", "الحرارة", "الحمل", "الحالة"])
if 'net_raw' not in st.session_state: st.session_state.net_raw = 0
if 'net_proto' not in st.session_state: st.session_state.net_proto = 0
if 'transformers' not in st.session_state:
    st.session_state.transformers = {
        f"محولة {i}": {"active": True, "last_i": 60.0, "temp": 45.0, "reason": "طبيعي ✅"} for i in range(1, 6)
    }

# --- 2. واجهة التحكم الرئيسية ---
st.title("🖥️ وحدة السيطرة الموحدة - شبكة الأنبار الذكية")
st.write(f"**المهندس المشرف:** محمد نبيل | **الموقع:** الرمادي | {datetime.now().strftime('%H:%M:%S')}")

# زر تبديل البروتوكول (هو المحرك الأساسي للنظام)
protocol_on = st.toggle("🚀 تفعيل البروتوكول الذكي (فرز الأولوية + ضغط البيانات)", value=True)

st.divider()

# --- 3. محاكاة ضغط البيانات والشبكة ---
col_n1, col_n2 = st.columns(2)
# إذا البروتوكول مفعل، نستهلك بيانات قليلة، إذا طافي نستهلك بيانات هواي
inc_raw = np.random.randint(120, 200) 
inc_proto = np.random.randint(15, 30)

if protocol_on:
    st.session_state.net_proto += inc_proto
    data_vol = inc_proto
    status_msg = "✅ بيانات مضغوطة ومنظمة"
else:
    st.session_state.net_raw += inc_raw
    data_vol = inc_raw
    status_msg = "⚠️ ضغط عالي (بيانات عشوائية)"

with col_n1:
    st.metric("حجم الإرسال الحالي", f"{data_vol} KB/s", status_msg)
with col_n2:
    total_net = st.session_state.net_proto if protocol_on else st.session_state.net_raw
    st.write(f"**إجمالي البيانات المخزنة:** {total_net} KB")
    st.progress(min(data_vol/200, 1.0))

st.divider()

# --- 4. معالجة بيانات المحولات ---
current_readings = []
max_cap = 150.0

# كروت التحكم اليدوي (للفصل والتشغيل)
st.subheader("🕹️ أزرار الفصل اليدوي")
t_cols = st.columns(5)

for idx, (name, state) in enumerate(st.session_state.transformers.items()):
    if state["active"]:
        # محاكاة البيانات
        change = np.random.uniform(-5, 20)
        new_i = max(0, min(180, state["last_i"] + change))
        new_t = max(30, min(110, state["temp"] + (change * 0.3)))
        load_pct = (new_i / max_cap) * 100
        
        # تحديد مستوى الخطورة (prio)
        if load_pct > 95 or new_t > 90:
            status, prio = "🚨 خطر جداً", 1
        elif load_pct > 75:
            status, prio = "⚠️ تحذير حمل", 2
        else:
            status, prio = "✅ طبيعي", 3
            
        state["last_i"], state["temp"], state["reason"] = new_i, new_t, status
    else:
        new_i, new_t, load_pct, prio = 0.0, 30.0, 0.0, 4
        status = "🛑 مفصول يدوياً"

    # أزرار التحكم في الكروت
    with t_cols[idx]:
        if state["active"]:
            if st.button(f"OFF {name}", key=f"off_{name}", use_container_width=True):
                state["active"] = False
                st.rerun()
        else:
            if st.button(f"ON {name}", key=f"on_{name}", use_container_width=True):
                state["active"] = True
                st.rerun()

    # إضافة للجدول
    current_readings.append({
        "المحطة": name,
        "التيار (A)": round(new_i, 1),
        "الحرارة (C°)": round(new_t, 1),
        "الحمل (%)": round(load_pct, 1),
        "الحالة": status,
        "p": prio
    })

# --- 5. الجدول الموحد (الفرز حسب البروتوكول) ---
st.subheader("📋 جدول البيانات والفرز اللحظي")
df = pd.DataFrame(current_readings)

if protocol_on:
    # الفرز الذكي (الخطر فوق)
    df = df.sort_values("p")
    st.info("💡 تم تفعيل البروتوكول: الجدول مفرز حسب الأولوية (الأخطر في الأعلى).")
else:
    # إرسال عشوائي (بدون فرز)
    df = df.sample(frac=1).reset_index(drop=True)
    st.warning("⚠️ إرسال عشوائي: البيانات غير مفرزة وتستهلك حجم إرسال كبير.")

# تنسيق ألوان الجدول
def apply_style(val):
    if '🚨' in str(val): return 'background-color: #ff4b4b; color: white; font-weight: bold'
    if '⚠️' in str(val): return 'background-color: #ffa500; color: black'
    if '✅' in str(val): return 'background-color: #28a745; color: white'
    if '🛑' in str(val): return 'background-color: #721c24; color: white'
    return ''

st.table(df.drop(columns=['p']).style.applymap(apply_style, subset=['الحالة']))

# --- 6. الأرشيف التاريخي ---
st.divider()
st.subheader("📜 سجل الأرشفة (Data Logging)")
# إضافة القراءات للسجل التاريخي
new_history = pd.concat([df.drop(columns=['p']), st.session_state.history], ignore_index=True).head(100)
st.session_state.history = new_history
st.dataframe(st.session_state.history, use_container_width=True, hide_index=True)

# تحديث تلقائي
time.sleep(1.5)
st.rerun()
