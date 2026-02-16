import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime

# إعدادات الصفحة
st.set_page_config(page_title="مركز سيطرة الأنبار المتكامل", layout="wide")

# --- 1. تهيئة الذاكرة (Session State) ---
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["الوقت", "المحطة", "V (فولت)", "I (أمبير)", "P (كيلوواط)", "PF", "الحمل %", "الحالة"])
if 'net_load' not in st.session_state: st.session_state.net_load = 0
if 'is_crashed' not in st.session_state: st.session_state.is_crashed = False
if 'transformers' not in st.session_state:
    st.session_state.transformers = {
        f"محولة {i}": {"active": True, "last_i": 75.0, "reason": "طبيعي ✅"} for i in range(1, 6)
    }

# --- 2. واجهة التحكم والعناوين ---
st.title("⚡ مركز السيطرة والرصد الكهربائي الموحد - الأنبار")
st.write(f"**المهندس المشرف:** محمد نبيل | **الحالة التشغيلية:** مستقرة | {datetime.now().strftime('%H:%M:%S')}")

# مفتاح البروتوكول (قلب المحاكاة)
protocol_on = st.sidebar.toggle("🔐 تفعيل بروتوكول تحسين البيانات والفرز", value=True)
if st.sidebar.button("♻️ إعادة تشغيل النظام"):
    st.session_state.net_load = 0
    st.session_state.is_crashed = False
    st.rerun()

# --- 3. محاكاة اختناق الشبكة والانهيار ---
if not protocol_on:
    st.session_state.net_load += np.random.randint(10, 18) # ضغط عالي بدون بروتوكول
    delay = st.session_state.net_load / 12
else:
    st.session_state.net_load = max(8, st.session_state.net_load - 6)
    delay = 0.1

if st.session_state.net_load >= 100:
    st.session_state.is_crashed = True

if st.session_state.is_crashed:
    st.markdown("""<div style="background-color: darkblue; padding: 40px; text-align: center; color: white; border: 5px solid red;">
    <h1>🆘 CRITICAL SYSTEM COLLAPSE</h1>
    <p>فشل الاتصال: الشبكة مختنقة بالبيانات العشوائية</p></div>""", unsafe_allow_html=True)
    st.stop()

# عرض مؤشرات الشبكة
st.subheader("🌐 حالة تدفق البيانات والشبكة")
c_net1, c_net2 = st.columns([3, 1])
with c_net1:
    st.write(f"**مستوى إجهاد الباندويث (Bandwidth Stress):** {st.session_state.net_load}%")
    st.progress(st.session_state.net_load / 100)
with c_net2:
    st.metric("تأخير الاستجابة (Latency)", f"{delay:.2f} s")

st.divider()

# --- 4. محاكاة القراءات الكهربائية الكاملة ---
current_readings = []
max_cap = 150.0

st.subheader("🕹️ وحدة السيطرة اليدوية (Manual Override)")
t_cols = st.columns(5)

for idx, (name, state) in enumerate(st.session_state.transformers.items()):
    if state["active"]:
        # توليد قراءات هندسية واقعية (أغلبها طبيعي)
        v = np.random.uniform(215, 228) # جهد مستقر حول الـ 220 فولت
        i_val = np.random.uniform(65, 148) # تيار يتراوح بين الطبيعي والتنبيه
        pf = np.random.uniform(0.82, 0.96) # معامل قدرة واقعي
        
        # حساب القدرة الحقيقية (P = V * I * PF / 1000) لتكون بالـ kW
        p_kw = (v * i_val * pf) / 1000
        
        load_pct = (i_val / max_cap) * 100
        temp = np.random.uniform(40, 92)
        
        # تحديد الحالة والفرز
        if load_pct >= 95 or temp >= 90: 
            status, prio = "🚨 خطر جداً", 1
        elif load_pct >= 80: 
            status, prio = "⚠️ تحذير حمل", 2
        else: 
            status, prio = "✅ طبيعي", 3
            
        state["last_i"], state["reason"] = i_val, status
    else:
        v, i_val, p_kw, pf, load_pct, temp, prio, status = 0, 0, 0, 0, 0, 30, 4, "🛑 مفصول"

    # أزرار التحكم اليدوي
    with t_cols[idx]:
        st.metric(name, f"{load_pct:.1f}%")
        if state["active"]:
            if st.button(f"OFF {name}", key=f"off_{idx}"):
                state["active"] = False
                st.rerun()
        else:
            if st.button(f"ON {name}", key=f"on_{idx}"):
                state["active"] = True
                st.rerun()

    current_readings.append({
        "المحطة": name,
        "V (فولت)": round(v, 1),
        "I (أمبير)": round(i_val, 1),
        "P (كيلوواط)": round(p_kw, 2),
        "PF": round(pf, 2),
        "T (C°)": round(temp, 1) if state["active"] else 30,
        "الحمل %": round(load_pct, 1),
        "الحالة": status,
        "p": prio
    })

# --- 5. الجدول الموحد المفرز ---
st.subheader("📋 ميزان الطاقة والقراءات التفصيلية")
df = pd.DataFrame(current_readings)

if protocol_on:
    df = df.sort_values("p") # فرز بالبروتوكول (الخطر فوق)
    st.success("🛡️ البروتوكول مفعّل: يتم فرز المحولات حسب الأولوية لتقليل زمن الاستجابة.")
else:
    df = df.sample(frac=1) # إرسال عشوائي مخربط
    st.warning("⚠️ إرسال عشوائي: البيانات غير منظمة ومرتبة بشكل عشوائي (خطر الانهيار).")

# تنسيق الألوان للجدول
def style_table(val):
    if '🚨' in str(val): return 'background-color: #ff4b4b; color: white'
    if '⚠️' in str(val): return 'background-color: #fff3cd; color: black'
    if '✅' in str(val): return 'background-color: #d4edda; color: black'
    if '🛑' in str(val): return 'background-color: #721c24; color: white'
    return ''

st.table(df.drop(columns=['p']).style.applymap(style_status if 'style_status' in globals() else style_table, subset=['الحالة']))

# --- 6. الأرشفة التاريخية (Data Logging) ---
st.divider()
st.subheader("📜 أرشيف البيانات التاريخي (Historical Log)")
# تسجيل القراءات الحالية في الأرشيف
new_log = df.drop(columns=['p'])
st.session_state.history = pd.concat([new_log, st.session_state.history], ignore_index=True).head(100)
st.dataframe(st.session_state.history, use_container_width=True, hide_index=True)

# محاكاة زمن التأخير
time.sleep(delay if not protocol_on else 1.3)
st.rerun()
