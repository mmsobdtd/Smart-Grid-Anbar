import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime

# إعدادات الصفحة
st.set_page_config(page_title="Al-Anbar Smart Grid - Balanced Mode", layout="wide")

# --- 1. تهيئة الذاكرة (Session State) ---
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["الوقت", "المحطة", "التيار", "الحمل", "الحالة"])
if 'net_load' not in st.session_state: st.session_state.net_load = 0
if 'is_crashed' not in st.session_state: st.session_state.is_crashed = False
if 'transformers' not in st.session_state:
    st.session_state.transformers = {
        f"محولة {i}": {"active": True, "last_i": 70.0, "reason": "طبيعي ✅"} for i in range(1, 6)
    }

# --- 2. واجهة التحكم والعناوين ---
st.title("📟 نظام السيطرة والتحليل الاستقرار - محافظة الأنبار")
st.write(f"**المهندس:** محمد نبيل | **الوضع الحالي:** تشغيل اعتيادي مع مراقبة الأحمال")

# مفتاح البروتوكول في الجانب
protocol_on = st.sidebar.toggle("🔐 تفعيل بروتوكول الحماية (Optimization)", value=True)
if st.sidebar.button("♻️ إعادة ضبط النظام"):
    st.session_state.net_load = 0
    st.session_state.is_crashed = False
    st.rerun()

# --- 3. منطق اختناق الشبكة والانهيار ---
if not protocol_on:
    # البيانات العشوائية تزيد الضغط بسرعة
    st.session_state.net_load += np.random.randint(8, 16)
    delay = st.session_state.net_load / 15
else:
    # البروتوكول يحافظ على استقرار الشبكة
    st.session_state.net_load = max(10, st.session_state.net_load - 5)
    delay = 0.1

if st.session_state.net_load >= 100:
    st.session_state.is_crashed = True

if st.session_state.is_crashed:
    st.markdown("""<div style="background-color: #00008b; padding: 40px; text-align: center; color: white; border: 4px solid yellow;">
    <h1>⚠️ CRITICAL ERROR: NETWORK COLLAPSE</h1>
    <p>توقف تدفق البيانات نتيجة الاختناق المروري في الشبكة (No Protocol Control)</p></div>""", unsafe_allow_html=True)
    st.stop()

# عرض مؤشرات الشبكة
c_net1, c_net2 = st.columns([3, 1])
with c_net1:
    st.write(f"**مستوى إجهاد الشبكة:** {st.session_state.net_load}%")
    st.progress(st.session_state.net_load / 100)
with c_net2:
    st.metric("تأخير البيانات (Latency)", f"{delay:.2f} s")

st.divider()

# --- 4. محاكاة القراءات (أغلبها طبيعي وتنبيه) ---
current_readings = []
max_cap = 150.0

st.subheader("🕹️ وحدة التحكم اليدوي المستقل")
t_cols = st.columns(5)

for idx, (name, state) in enumerate(st.session_state.transformers.items()):
    if state["active"]:
        # جعل النطاق يميل للحالات الطبيعية والتحذيرية
        # تيار بين 60 و 150 أمبير
        new_i = np.random.uniform(60, 150) 
        load_pct = (new_i / max_cap) * 100
        
        # توزيع الحالات بناءً على طلبك
        if load_pct >= 95: 
            status, prio = "🚨 خطر (تجاوز 95%)", 1
        elif load_pct >= 80: 
            status, prio = "⚠️ تحذير (حمل عالي)", 2
        else: 
            status, prio = "✅ طبيعي", 3
            
        state["last_i"], state["reason"] = new_i, status
    else:
        new_i, load_pct, prio, status = 0.0, 0.0, 4, "🛑 مفصول"

    with t_cols[idx]:
        st.metric(name, f"{load_pct:.1f}%")
        if state["active"]:
            if st.button(f"OFF", key=f"off_{idx}", use_container_width=True):
                state["active"] = False
                st.rerun()
        else:
            if st.button(f"ON", key=f"on_{idx}", use_container_width=True):
                state["active"] = True
                st.rerun()

    current_readings.append({
        "المحطة": name,
        "التيار (A)": round(new_i, 1),
        "الحمل (%)": round(load_pct, 1),
        "الحالة": status,
        "p": prio
    })

# --- 5. الجدول الموحد (الفرز والبروتوكول) ---
st.subheader("📋 ميزان الأحمال وجدول البيانات اللحظي")
df = pd.DataFrame(current_readings)

if protocol_on:
    # الفرز الذكي: يجمع التنبيهات والخطر فوق
    df = df.sort_values("p")
    st.success("نظام البروتوكول مفعّل: البيانات مفرزة ومنظمة.")
else:
    # إرسال عشوائي: الجدول يتلخبط باستمرار
    df = df.sample(frac=1)
    st.warning("إرسال عشوائي: البيانات تصل بترتيب غير ثابت (خطر الانهيار قريب).")

# تنسيق ألوان الجدول
def style_status(val):
    if '🚨' in str(val): return 'background-color: #ff4b4b; color: white'
    if '⚠️' in str(val): return 'background-color: #fff3cd; color: #856404'
    if '✅' in str(val): return 'background-color: #d4edda; color: #155724'
    if '🛑' in str(val): return 'background-color: #721c24; color: white'
    return ''

st.table(df.drop(columns=['p']).style.applymap(style_status, subset=['الحالة']))

# --- 6. الأرشيف التاريخي (لم يتمسح) ---
st.divider()
st.subheader("📜 أرشيف قراءات الشبكة (History)")
new_data = df.drop(columns=['p'])
st.session_state.history = pd.concat([new_data, st.session_state.history], ignore_index=True).head(50)
st.dataframe(st.session_state.history, use_container_width=True, hide_index=True)

# تأخير المحاكاة الفعلي
time.sleep(delay if not protocol_on else 1.2)
st.rerun()
