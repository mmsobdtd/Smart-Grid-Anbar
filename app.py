import streamlit as st
import pandas as pd
import numpy as np
import time

# إعدادات الصفحة
st.set_page_config(page_title="Al-Anbar Grid - Dynamic Sorting", layout="wide")

# --- 1. تهيئة الذاكرة والسجلات ---
if 'all_data_log' not in st.session_state:
    st.session_state.all_data_log = pd.DataFrame(columns=["المحطة", "V", "I", "P (kW)", "PF", "Load%", "الحالة", "p"])
if 'net_load' not in st.session_state: st.session_state.net_load = 15 
if 'transformers' not in st.session_state:
    st.session_state.transformers = {f"محولة {i}": {"active": True, "last_i": 75} for i in range(1, 6)}

# --- 2. واجهة العناوين (Header) ---
st.title("⚡ نظام الرصد والفرز الديناميكي للشبكة الذكية")
st.markdown(f"### **إعداد الطالب: محمد نبيل**")
st.write("**الحالة:** مراقبة حية - يتم تحديث الفرز مع كل إرسال بيانات")

# مفتاح البروتوكول في الجانب
st.sidebar.header("🕹️ التحكم بالبروتوكول")
protocol_on = st.sidebar.toggle("🔐 تفعيل الفرز اللحظي (Priority Sorting)", value=True)

if st.sidebar.button("♻️ إعادة تشغيل المنظومة"):
    st.session_state.all_data_log = st.session_state.all_data_log.iloc[0:0]
    st.session_state.net_load = 15
    st.rerun()

st.divider()

# --- 3. محاكاة استقرار الشبكة والانهيار التدريجي ---
st.subheader("🌐 إجهاد تدفق البيانات (Network Traffic Stress)")
col_net1, col_net2, col_net3 = st.columns(3)

active_count = sum(1 for t in st.session_state.transformers.values() if t["active"])

if not protocol_on:
    # انهيار تدريجي عند إطفاء البروتوكول
    st.session_state.net_load += np.random.uniform(1.5, 3.5) * (active_count / 2)
    pps = np.random.randint(450, 600)
    latency = int(st.session_state.net_load * 12)
    net_status = "⚠️ اختناق البيانات" if st.session_state.net_load < 90 else "🚨 انهيار وشيك"
else:
    # استقرار عند التفعيل
    st.session_state.net_load = max(10, st.session_state.net_load - 5)
    pps = np.random.randint(35, 60)
    latency = np.random.randint(15, 30)
    net_status = "✅ مستقرة"

st.session_state.net_load = min(100, st.session_state.net_load)

with col_net1:
    st.metric("معدل النقل", f"{pps} PPS")
with col_net2:
    st.metric("التأخير", f"{latency} ms")
with col_net3:
    st.write(f"**حالة الاتصال:** {net_status}")
    st.progress(st.session_state.net_load / 100)

if st.session_state.net_load >= 100:
    st.error("🆘 !!! CRITICAL NETWORK FAILURE: BUFFER OVERFLOW !!!")
    st.stop()

st.divider()

# --- 4. توليد ومعالجة البيانات (الفرز يتم في كل دورة) ---
current_batch = [] # مصفوفة لتخزين القراءات الحالية فقط وفرزها

for name, state in st.session_state.transformers.items():
    if state["active"]:
        v = int(np.random.uniform(219, 226))
        # جعل القيم متغيرة باستمرار لإظهار حركة الفرز
        i_val = int(np.random.uniform(60, 155))
        pf = round(np.random.uniform(0.86, 0.94), 2)
        p_kw = int((v * i_val * pf) / 1000)
        load_pct = int((i_val / 150) * 100)
        
        # تحديد الأولوية والحالة
        if load_pct >= 95: status, prio = "🚨 خطر جداً", 1
        elif load_pct >= 80: status, prio = "⚠️ تنبيه حمل", 2
        else: status, prio = "✅ طبيعي", 3
        
        state["last_i"] = i_val
    else:
        v, i_val, p_kw, pf, load_pct, status, prio = 0, 0, 0, 0, 0, "🛑 مفصول", 4

    current_batch.append({
        "المحطة": name, "V": v, "I": i_val, "P (kW)": p_kw, 
        "PF": pf, "Load%": load_pct, "الحالة": status, "p": prio
    })

# تحويل الدفعة الحالية لجدول
df_batch = pd.DataFrame(current_readings if 'current_readings' in locals() else current_batch)

# --- 5. منطق الفرز الديناميكي (مع كل إرسال) ---
if protocol_on:
    # فرز الدفعة الحالية فوراً: الخطر ثم التنبيه ثم الطبيعي
    df_batch = df_batch.sort_values(by="p", ascending=True)
else:
    # إرسال عشوائي: خلط الترتيب (Chaos Mode)
    df_batch = df_batch.sample(frac=1).reset_index(drop=True)

# إضافة هذه الدفعة للسجل التاريخي الكلي (بدون فرز التاريخ)
st.session_state.all_data_log = pd.concat([df_batch, st.session_state.all_data_log], ignore_index=True).head(500)

# --- 6. عرض أزرار التحكم والجدول الديناميكي ---
st.subheader("🕹️ وحدة السيطرة اللحظية")
c_btns = st.columns(5)
for idx, name in enumerate(st.session_state.transformers):
    with c_btns[idx]:
        if st.session_state.transformers[name]["active"]:
            if st.button(f"فصل {name}", key=f"off_{idx}"):
                st.session_state.transformers[name]["active"] = False
                st.rerun()
        else:
            if st.button(f"تشغيل {name}", key=f"on_{idx}"):
                st.session_state.transformers[name]["active"] = True
                st.rerun()

st.divider()

# عرض جدول القراءات الحالية المفرزة
st.subheader("📋 جدول الرصد الديناميكي (تحديث وفرز لحظي)")

def style_row(val):
    if '🚨' in str(val): return 'background-color: #ff4b4b; color: white'
    if '⚠️' in str(val): return 'background-color: #fff3cd'
    if '✅' in str(val): return 'background-color: #d4edda'
    if '🛑' in str(val): return 'background-color: #721c24; color: white'
    return ''

st.table(df_batch.drop(columns=['p']).style.applymap(style_row, subset=['الحالة']))


st.divider()

# --- 7. مراجعة السجل الخاص ---
st.subheader("🔍 مراجعة السجل التاريخي (الأرشفة)")
selected_trans = st.selectbox("اختر المحولة:", list(st.session_state.transformers.keys()))
history_filtered = st.session_state.all_data_log[st.session_state.all_data_log["المحطة"] == selected_trans]
st.dataframe(history_filtered.drop(columns=['p']), use_container_width=True, hide_index=True)

# سرعة التحديث (1.5 ثانية لإظهار حركة الفرز)
time.sleep(1.5)
st.rerun()
