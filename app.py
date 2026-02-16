import streamlit as st
import pandas as pd
import numpy as np
import time

# إعدادات الصفحة
st.set_page_config(page_title="مركز سيطرة الأنبار - إعداد محمد نبيل", layout="wide")

# --- 1. تهيئة الذاكرة (Session State) ---
if 'all_data_log' not in st.session_state:
    # إزالة "الوقت" من الأعمدة
    st.session_state.all_data_log = pd.DataFrame(columns=["المحطة", "V", "I", "P (kW)", "PF", "Load%", "الحالة", "p"])
if 'net_load' not in st.session_state: st.session_state.net_load = 10 
if 'transformers' not in st.session_state:
    st.session_state.transformers = {f"محولة {i}": {"active": True, "last_i": 70} for i in range(1, 6)}

# --- 2. واجهة التحكم والعناوين ---
st.title("🖥️ مركز سيطرة الأنبار - محاكاة تدفق البيانات المتزن")
# تم تغيير الاسم وإزالة الوقت كما طلبت
st.subheader("إعداد الطالب: محمد نبيل")
st.write("**الحالة التشغيلية:** رصد حي للأحمال")

# مفتاح البروتوكول في الجانب
protocol_on = st.sidebar.toggle("🔐 تفعيل بروتوكول تحسين البيانات (Optimization)", value=True)

if st.sidebar.button("♻️ إعادة تشغيل النظام"):
    st.session_state.all_data_log = st.session_state.all_data_log.iloc[0:0]
    st.session_state.net_load = 10
    st.rerun()

st.divider()

# --- 3. محاكاة استقرار الشبكة والانهيار التدريجي ---
st.subheader("🌐 مراقبة استقرار الشبكة (Network Stability)")
col_net1, col_net2, col_net3 = st.columns(3)

active_count = sum(1 for t in st.session_state.transformers.values() if t["active"])

if not protocol_on:
    # الانهيار التدريجي (بدون بروتوكول)
    st.session_state.net_load += np.random.uniform(1.5, 3.5) * (active_count / 2)
    pps = np.random.randint(400, 550)
    latency = int(st.session_state.net_load * 15)
    net_status = "⚠️ اختناق تدريجي" if st.session_state.net_load < 90 else "🚨 خطر الانهيار"
else:
    # الاستقرار (مع بروتوكول)
    st.session_state.net_load = max(12, st.session_state.net_load - 4)
    pps = np.random.randint(30, 55)
    latency = np.random.randint(15, 35)
    net_status = "✅ مستقرة"

st.session_state.net_load = min(100, st.session_state.net_load)

with col_net1:
    st.metric("معدل النقل (Traffic)", f"{pps} PPS")
with col_net2:
    st.metric("التأخير (Latency)", f"{latency} ms")
with col_net3:
    st.write(f"**حالة الشبكة:** {net_status}")
    st.progress(st.session_state.net_load / 100)

if st.session_state.net_load >= 100:
    st.error("🆘 !!! CRITICAL NETWORK FAILURE: BUFFER OVERFLOW !!!")
    st.markdown("<h2 style='text-align: center; color: yellow;'>فشل الاتصال - يرجى تفعيل البروتوكول لإعادة التشغيل</h2>", unsafe_allow_html=True)
    st.stop()

st.divider()

# --- 4. توليد القراءات (أرقام نظيفة وبدون وقت) ---
new_readings = []
for name, state in st.session_state.transformers.items():
    if state["active"]:
        v = int(np.random.uniform(219, 226))
        i_val = int(np.random.uniform(65, 145))
        pf = round(np.random.uniform(0.86, 0.94), 2)
        p_kw = int((v * i_val * pf) / 1000)
        load_pct = int((i_val / 150) * 100)
        
        if load_pct >= 95: status, prio = "🚨 خطر", 1
        elif load_pct >= 80: status, prio = "⚠️ تنبيه", 2
        else: status, prio = "✅ طبيعي", 3
    else:
        v, i_val, p_kw, pf, load_pct, status, prio = 0, 0, 0, 0, 0, "🛑 مفصول", 4

    new_readings.append({
        "المحطة": name, "V": v, "I": i_val, "P (kW)": p_kw, 
        "PF": pf, "Load%": load_pct, "الحالة": status, "p": prio
    })

# تحديث سجل البيانات الموحد
new_df = pd.DataFrame(new_readings)
st.session_state.all_data_log = pd.concat([new_df, st.session_state.all_data_log], ignore_index=True).head(500)

# --- 5. التحكم اليدوي ---
st.subheader("🕹️ وحدة التحكم اليدوي (Manual Control)")
c_btns = st.columns(5)
for idx, name in enumerate(st.session_state.transformers):
    with c_btns[idx]:
        if st.session_state.transformers[name]["active"]:
            if st.button(f"OFF {name}", key=f"off_{idx}", use_container_width=True):
                st.session_state.transformers[name]["active"] = False
                st.rerun()
        else:
            if st.button(f"ON {name}", key=f"on_{idx}", use_container_width=True):
                st.session_state.transformers[name]["active"] = True
                st.rerun()

# --- 6. الجدول الموحد (Live Feed) ---
st.subheader("📋 سجل القراءات الموحد (المباشر والأرشيف)")
display_df = st.session_state.all_data_log.copy()

if protocol_on:
    # الفرز حسب الخطورة (p) أولاً
    display_df = display_df.sort_values(["p"], ascending=[True])

def style_row(val):
    if '🚨' in str(val): return 'background-color: #ff4b4b; color: white'
    if '⚠️' in str(val): return 'background-color: #fff3cd'
    if '✅' in str(val): return 'background-color: #d4edda'
    return ''

# عرض أول 15 قراءة في السجل
st.table(display_df.drop(columns=['p']).head(15).style.applymap(style_row, subset=['الحالة']))

st.divider()

# --- 7. استعلام تاريخي منفصل لكل محولة ---
st.subheader("🔍 مراجعة السجل الخاص لكل محولة")
selected_trans = st.selectbox("اختر المحولة:", list(st.session_state.transformers.keys()))
history_filtered = st.session_state.all_data_log[st.session_state.all_data_log["المحطة"] == selected_trans]
# إظهار الجدول الخاص بدون عمود الوقت أيضاً
st.dataframe(history_filtered.drop(columns=['p']), use_container_width=True, hide_index=True)

# تأخير المحاكاة للوضوح
time.sleep(1.8 if protocol_on else 1.0)
st.rerun()
