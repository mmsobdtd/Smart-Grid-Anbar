import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime

# إعدادات الصفحة
st.set_page_config(page_title="Al-Anbar Smart Grid - Real-time Network", layout="wide")

# --- 1. تهيئة الذاكرة (Session State) ---
if 'all_data_log' not in st.session_state:
    st.session_state.all_data_log = pd.DataFrame(columns=["الوقت", "المحطة", "V", "I", "P (kW)", "PF", "Load%", "الحالة", "p"])
if 'net_load' not in st.session_state: st.session_state.net_load = 20 # تبدأ بنسبة بسيطة
if 'transformers' not in st.session_state:
    st.session_state.transformers = {f"محولة {i}": {"active": True, "last_i": 70} for i in range(1, 6)}

# --- 2. واجهة التحكم والعناوين ---
st.title("🖥️ مركز سيطرة الأنبار - محاكاة تدفق البيانات الواقعي")
st.write(f"**المهندس:** محمد نبيل | **الحالة:** رصد حي | {datetime.now().strftime('%H:%M:%S')}")

# مفتاح البروتوكول
protocol_on = st.sidebar.toggle("🔐 تفعيل بروتوكول تحسين البيانات (Optimization)", value=True)

if st.sidebar.button("♻️ تصفير السجل وإعادة الضبط"):
    st.session_state.all_data_log = st.session_state.all_data_log.iloc[0:0]
    st.session_state.net_load = 20
    st.rerun()

st.divider()

# --- 3. محاكاة واقعية لتدفق البيانات (Network Realism) ---
st.subheader("🌐 حالة الشبكة (Network Health & Traffic)")
col_net1, col_net2, col_net3 = st.columns(3)

if not protocol_on:
    # إرسال عشوائي: كل حساس يرسل بياناته باستمرار (أكثر من 500 حزمة/ثانية)
    pps = np.random.randint(450, 600) # Packets Per Second
    st.session_state.net_load = min(100, st.session_state.net_load + np.random.randint(5, 12))
    latency = st.session_state.net_load * 25 # بالملي ثانية
    net_status = "⚠️ اختناق (Congested)" if st.session_state.net_load < 100 else "🆘 انهيار (Collapsed)"
else:
    # البروتوكول: يرسل فقط عند التغير أو بشكل دوري منظم (50 حزمة/ثانية)
    pps = np.random.randint(40, 60)
    st.session_state.net_load = max(15, st.session_state.net_load - 10)
    latency = np.random.randint(20, 45)
    net_status = "✅ مستقرة (Healthy)"

with col_net1:
    st.metric("معدل نقل البيانات (Traffic)", f"{pps} PPS", "إرسال كثيف" if not protocol_on else "إرسال محسن")
with col_net2:
    st.metric("تأخير الشبكة (Latency)", f"{latency} ms")
with col_net3:
    st.write(f"**حالة الشبكة:** {net_status}")
    st.progress(st.session_state.net_load / 100)

if st.session_state.net_load >= 100:
    st.error("!!! NETWORK FAILURE: BUFFER OVERFLOW !!!")
    st.stop()

st.divider()

# --- 4. توليد القراءات (أرقام صحيحة بدون أصفار) ---
new_readings = []
for name, state in st.session_state.transformers.items():
    if state["active"]:
        v = int(np.random.uniform(218, 226))
        # جعل الأحمال تميل للطبيعي والتحذير كما طلبت
        i_val = int(np.random.uniform(65, 145))
        pf = round(np.random.uniform(0.85, 0.94), 2)
        p_kw = int((v * i_val * pf) / 1000)
        load_pct = int((i_val / 150) * 100)
        
        if load_pct >= 95: status, prio = "🚨 خطر", 1
        elif load_pct >= 80: status, prio = "⚠️ تنبيه", 2
        else: status, prio = "✅ طبيعي", 3
    else:
        v, i_val, p_kw, pf, load_pct, status, prio = 0, 0, 0, 0, 0, "🛑 مفصول", 4

    new_readings.append({
        "الوقت": datetime.now().strftime('%H:%M:%S'),
        "المحطة": name, "V": v, "I": i_val, "P (kW)": p_kw, 
        "PF": pf, "Load%": load_pct, "الحالة": status, "p": prio
    })

# تحديث السجل التاريخي (الموحد)
new_df = pd.DataFrame(new_readings)
st.session_state.all_data_log = pd.concat([new_df, st.session_state.all_data_log], ignore_index=True).head(500)

# --- 5. التحكم اليدوي ---
st.subheader("🕹️ وحدة التحكم اليدوي بالمحطات")
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

# --- 6. الجدول الموحد (Live Feed) ---
st.subheader("📋 سجل البيانات الموحد (القراءات اللحظية والتاريخية)")

display_df = st.session_state.all_data_log.copy()

if protocol_on:
    # الفرز الذكي (الخطر فوق)
    display_df = display_df.sort_values(["الوقت", "p"], ascending=[False, True])
    st.success("🛡️ البروتوكول ينظم تدفق البيانات ويفرز الأولويات")
else:
    st.warning("📡 إرسال عشوائي: البيانات تصل بترتيب غير مستقر")

def style_row(val):
    if '🚨' in str(val): return 'background-color: #ff4b4b; color: white'
    if '⚠️' in str(val): return 'background-color: #fff3cd'
    if '✅' in str(val): return 'background-color: #d4edda'
    return ''

# عرض أول 15 قراءة في الجدول الموحد
st.table(display_df.drop(columns=['p']).head(15).style.applymap(style_row, subset=['الحالة']))

st.divider()

# --- 7. استعلام تاريخي منفصل لكل محولة ---
st.subheader("🔍 مراجعة السجل الخاص لكل محولة")
selected_trans = st.selectbox("اختر المحولة لعرض تاريخ قراءاتها:", list(st.session_state.transformers.keys()))
history_filtered = st.session_state.all_data_log[st.session_state.all_data_log["المحطة"] == selected_trans]

st.dataframe(history_filtered.drop(columns=['p']), use_container_width=True, hide_index=True)

# محاكاة واقعية للتأخير
time.sleep(1.5 if protocol_on else 0.5)
st.rerun()
