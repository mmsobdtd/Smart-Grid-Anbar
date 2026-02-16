import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime

# إعدادات الصفحة
st.set_page_config(page_title="Al-Anbar Grid - System Stability", layout="wide")

# --- 1. تهيئة الذاكرة والسجلات ---
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["الوقت", "المحطة", "التيار", "الحرارة", "الحمل", "الحالة"])
if 'net_stress' not in st.session_state: st.session_state.net_stress = 0
if 'transformers' not in st.session_state:
    st.session_state.transformers = {
        f"محولة {i}": {"active": True, "last_i": 60.0, "temp": 45.0, "reason": "طبيعي ✅"} for i in range(1, 6)
    }

# --- 2. واجهة التحكم الرئيسية ---
st.title("📟 مركز السيطرة والتحقق من استقرارية الشبكة - الأنبار")
st.write(f"**المهندس:** محمد نبيل | **الحالة:** اختبار الضغط التشغيلي")

# المفتاح السحري للنظام
protocol_on = st.toggle("🌐 تفعيل بروتوكول الحماية والفرز الذكي", value=True)

st.divider()

# --- 3. محاكاة الانهيار (The Collapse Logic) ---
if not protocol_on:
    # محاكاة انهيار النظام
    st.session_state.net_stress += np.random.randint(20, 50)
    
    st.error("!!! CRITICAL SYSTEM FAILURE !!!")
    st.markdown("""
        <div style="background-color: #ff4b4b; padding: 20px; border-radius: 10px; text-align: center; color: white;">
            <h1>⚠️ انهيار النظام (System Collapse)</h1>
            <p>فشل في معالجة البيانات بسبب الإرسال العشوائي وضغط الشبكة العالي</p>
            <p>البيانات غير مفرزة - وقت الاستجابة (Latency): INFINITE</p>
        </div>
    """, unsafe_allow_html=True)
    
    # إظهار شريط ضغط الشبكة وهو ينفجر
    st.write("**مستوى اختناق الشبكة (Network Congestion):**")
    st.progress(1.0) # شريط كامل أحمر
    
    if st.button("محاولة إعادة الاتصال الاضطراري"):
        st.rerun()
    
    st.stop() # إيقاف بقية الكود عن العمل (هذا هو الانهيار الحقيقي)

else:
    # إذا البروتوكول يعمل، نصفر الإجهاد تدريجياً
    st.session_state.net_stress = max(0, st.session_state.net_stress - 10)
    st.success("✅ النظام مستقر: البروتوكول يقوم بفرز البيانات وتقليل الضغط")
    
    col_n1, col_n2 = st.columns(2)
    with col_n1:
        st.metric("حجم البيانات", "18 KB/s", "كفاءة عالية")
    with col_n2:
        st.write("**ضغط الشبكة الحالي:**")
        st.progress(0.15) # شريط منخفض يوضح الراحة في الشبكة

# --- 4. معالجة بيانات المحولات (تعمل فقط إذا البروتوكول ON) ---
current_readings = []
max_cap = 150.0

st.subheader("🕹️ وحدة التحكم اليدوي")
t_cols = st.columns(5)

for idx, (name, state) in enumerate(st.session_state.transformers.items()):
    if state["active"]:
        change = np.random.uniform(-2, 15)
        new_i = max(0, min(180, state["last_i"] + change))
        new_t = max(30, min(105, state["temp"] + (change * 0.2)))
        load_pct = (new_i / max_cap) * 100
        
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
        "الحرارة (C°)": round(new_t, 1),
        "الحمل (%)": round(load_pct, 1),
        "الحالة": status,
        "p": prio
    })

# --- 5. الجدول الموحد والمفرز ---
st.divider()
st.subheader("📊 جدول البيانات اللحظي (مفرز حسب الأولوية)")
df = pd.DataFrame(current_readings).sort_values("p")

def apply_style(val):
    if '🚨' in str(val): return 'background-color: #ff4b4b; color: white'
    if '⚠️' in str(val): return 'background-color: #ffa500; color: black'
    if '✅' in str(val): return 'background-color: #28a745; color: white'
    return ''

st.table(df.drop(columns=['p']).style.applymap(apply_style, subset=['الحالة']))

# --- 6. الأرشيف التاريخي ---
st.divider()
st.subheader("📜 سجل الأرشفة الدائم")
new_row = df.drop(columns=['p'])
st.session_state.history = pd.concat([new_row, st.session_state.history], ignore_index=True).head(50)
st.dataframe(st.session_state.history, use_container_width=True, hide_index=True)

time.sleep(1.5)
st.rerun()
