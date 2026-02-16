import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime

# إعدادات الصفحة
st.set_page_config(page_title="Al-Anbar Grid Stress Test", layout="wide")

# --- 1. تهيئة الذاكرة (Session State) ---
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["الوقت", "المحطة", "التيار", "الحمل", "الحالة"])
if 'net_load' not in st.session_state: st.session_state.net_load = 0
if 'is_crashed' not in st.session_state: st.session_state.is_crashed = False
if 'transformers' not in st.session_state:
    st.session_state.transformers = {
        f"محولة {i}": {"active": True, "last_i": 60.0, "temp": 45.0, "reason": "طبيعي ✅"} for i in range(1, 6)
    }

# --- 2. واجهة التحكم ---
st.title("📟 نظام محاكاة اختناق الشبكة والانهيار الرقمي")
st.write(f"**المهندس المصمم:** محمد نبيل | **الحالة:** اختبار الضغط الحقيقي")

# زر البروتوكول - المنقذ من الانهيار
protocol_on = st.sidebar.toggle("🔐 تفعيل بروتوكول تحسين البيانات (Optimization)", value=True)

if st.sidebar.button("♻️ إعادة تشغيل النظام (System Reset)"):
    st.session_state.net_load = 0
    st.session_state.is_crashed = False
    st.rerun()

# --- 3. منطق اختناق الشبكة (Congestion Logic) ---
if not protocol_on:
    # زيادة الضغط بسرعة (إرسال عشوائي كثيف)
    st.session_state.net_load += np.random.randint(5, 15)
    # حساب التأخير (Latency) - كلما زاد الضغط زاد التأخير الفعلي للبرنامج
    delay = st.session_state.net_load / 20 
else:
    # البروتوكول يقلل الضغط ويحافظ على ثباته
    st.session_state.net_load = max(10, st.session_state.net_load - 5)
    delay = 0.1

# التحقق من الانهيار
if st.session_state.net_load >= 100:
    st.session_state.is_crashed = True

# --- 4. عرض الانهيار أو العمل الطبيعي ---
if st.session_state.is_crashed:
    st.markdown("""
        <div style="background-color: #0000aa; padding: 50px; border: 5px solid red; text-align: center; color: white; font-family: monospace;">
            <h1 style="font-size: 50px;">FATAL NETWORK ERROR</h1>
            <p style="font-size: 24px;">SYSTEM COLLAPSE: BUFFER OVERFLOW</p>
            <p>البيانات المرسلة تجاوزت سعة الشبكة (Bandwidth Exceeded)</p>
            <p>لم يتم استلام القراءات من المحولات... توقف الاتصال</p>
            <h2 style="color: yellow;">تم فقدان السيطرة على الشبكة!</h2>
        </div>
    """, unsafe_allow_html=True)
    st.stop()

# عرض شريط ضغط الشبكة
st.subheader("📡 مراقبة تدفق البيانات واختناق الشبكة (Network Congestion)")
cols_net = st.columns([3, 1])
with cols_net[0]:
    bar_color = "red" if st.session_state.net_load > 80 else "orange" if st.session_state.net_load > 50 else "green"
    st.write(f"**مستوى اختناق الشبكة:** {st.session_state.net_load}%")
    st.progress(st.session_state.net_load / 100)
with cols_net[1]:
    st.metric("التأخير (Latency)", f"{delay:.2f} s", delta="تأخير حرج" if delay > 2 else None, delta_color="inverse")

st.divider()

# --- 5. معالجة بيانات المحولات ---
current_readings = []
max_cap = 150.0

st.subheader("🕹️ لوحة السيطرة (تتأثر بالتأخير)")
t_cols = st.columns(5)

for idx, (name, state) in enumerate(st.session_state.transformers.items()):
    if state["active"]:
        # قراءات عشوائية
        change = np.random.uniform(-5, 15)
        new_i = max(0, min(180, state["last_i"] + change))
        load_pct = (new_i / max_cap) * 100
        
        if load_pct > 95: status, prio = "🚨 خطر", 1
        elif load_pct > 75: status, prio = "⚠️ تحذير", 2
        else: status, prio = "✅ طبيعي", 3
        
        state["last_i"], state["reason"] = new_i, status
    else:
        new_i, load_pct, prio, status = 0.0, 0.0, 4, "🛑 مفصول"

    # أزرار الفصل
    with t_cols[idx]:
        if state["active"]:
            if st.button(f"OFF {name}", key=f"off_{name}"):
                state["active"] = False
                st.rerun()
        else:
            if st.button(f"ON {name}", key=f"on_{name}"):
                state["active"] = True
                st.rerun()

    current_readings.append({
        "المحطة": name,
        "التيار (A)": round(new_i, 1),
        "الحمل (%)": round(load_pct, 1),
        "الحالة": status,
        "p": prio
    })

# --- 6. الجدول الموحد (المفرز أو المخربط) ---
st.subheader("📋 جدول البيانات المستلمة")
df = pd.DataFrame(current_readings)

if protocol_on:
    df = df.sort_values("p")
    st.success("البروتوكول فعال: يتم استلام البيانات مفرزة ومنظمة.")
else:
    # محاكاة وصول البيانات بشكل عشوائي ومخربط بسبب الاختناق
    df = df.sample(frac=1)
    st.warning("تحذير: البيانات تصل بشكل عشوائي وغير مرتب نتيجة اختناق الشبكة.")

st.table(df.drop(columns=['p']).style.applymap(
    lambda x: 'background-color: #ff4b4b; color: white' if '🚨' in str(x) or '🛑' in str(x) else 
    ('background-color: #ffa500' if '⚠️' in str(x) else ''), subset=['الحالة']
))

# إضافة للأرشفة
st.session_state.history = pd.concat([df.drop(columns=['p']), st.session_state.history], ignore_index=True).head(50)

# محاكاة التأخير الفعلي (Latency)
time.sleep(delay if not protocol_on else 1)
st.rerun()
