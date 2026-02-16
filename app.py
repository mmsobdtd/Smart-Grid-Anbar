import streamlit as st
import pandas as pd
import numpy as np
import time

# إعدادات الصفحة - وضع الـ Wide للعرض الاحترافي
st.set_page_config(page_title="مركز سيطرة الأنبار - محمد نبيل", layout="wide")

# --- 1. تهيئة الذاكرة والسجلات (Session State) ---
if 'all_data_log' not in st.session_state:
    # تم إزالة عمود "الوقت" نهائياً
    st.session_state.all_data_log = pd.DataFrame(columns=["المحطة", "V", "I", "P (kW)", "PF", "Load%", "الحالة", "p"])
if 'net_load' not in st.session_state: st.session_state.net_load = 15 
if 'transformers' not in st.session_state:
    st.session_state.transformers = {f"محولة {i}": {"active": True, "last_i": 75} for i in range(1, 6)}

# --- 2. واجهة العناوين (Header) ---
st.title("⚡ نظام السيطرة والتحليل الاستقرائي للشبكة الذكية")
st.markdown(f"### **إعداد الطالب: محمد نبيل**")
st.write("**الموقع:** محافظة الأنبار - غرفة السيطرة المركزية")

# مفتاح البروتوكول في الجانب (Side Bar)
st.sidebar.header("🕹️ لوحة التحكم بالنظام")
protocol_on = st.sidebar.toggle("🔐 تفعيل البروتوكول الذكي (Optimization)", value=True)

if st.sidebar.button("♻️ إعادة ضبط المنظومة"):
    st.session_state.all_data_log = st.session_state.all_data_log.iloc[0:0]
    st.session_state.net_load = 15
    st.rerun()

st.divider()

# --- 3. محاكاة استقرار واختناق الشبكة (Network Realism) ---
st.subheader("🌐 مراقبة كفاءة تدفق البيانات (Network Data Traffic)")
col_net1, col_net2, col_net3 = st.columns(3)

# حساب عدد المحولات الشغالة لتأثير الضغط
active_count = sum(1 for t in st.session_state.transformers.values() if t["active"])

if not protocol_on:
    # إرسال عشوائي: انهيار تدريجي وواقعي
    st.session_state.net_load += np.random.uniform(1.2, 3.2) * (active_count / 2)
    pps = np.random.randint(450, 600)
    latency = int(st.session_state.net_load * 12)
    net_status = "⚠️ اختناق البيانات" if st.session_state.net_load < 90 else "🚨 انهيار وشيك"
else:
    # البروتوكول: استقرار وتحسين
    st.session_state.net_load = max(10, st.session_state.net_load - 5)
    pps = np.random.randint(35, 60)
    latency = np.random.randint(15, 30)
    net_status = "✅ مستقرة"

# تثبيت الحد الأقصى للضغط
st.session_state.net_load = min(100, st.session_state.net_load)

with col_net1:
    st.metric("معدل النقل (Traffic)", f"{pps} PPS")
with col_net2:
    st.metric("التأخير (Latency)", f"{latency} ms")
with col_net3:
    st.write(f"**حالة الاتصال:** {net_status}")
    st.progress(st.session_state.net_load / 100)

# حالة الانهيار
if st.session_state.net_load >= 100:
    st.error("🆘 !!! CRITICAL NETWORK FAILURE: BUFFER OVERFLOW !!!")
    st.markdown("<h2 style='text-align: center; color: yellow;'>توقف النظام نتيجة اختناق الشبكة - فعّل البروتوكول للاستعادة</h2>", unsafe_allow_html=True)
    st.stop()

st.divider()

# --- 4. توليد القراءات الهندسية (أرقام نظيفة وبدون وقت) ---
new_readings = []
for name, state in st.session_state.transformers.items():
    if state["active"]:
        # توليد قراءات تميل للطبيعي والتنبيه
        v = int(np.random.uniform(219, 226))
        i_val = int(np.random.uniform(65, 146))
        pf = round(np.random.uniform(0.86, 0.94), 2)
        p_kw = int((v * i_val * pf) / 1000)
        load_pct = int((i_val / 150) * 100)
        
        # منطق الفرز
        if load_pct >= 95: status, prio = "🚨 خطر جداً", 1
        elif load_pct >= 80: status, prio = "⚠️ تنبيه حمل", 2
        else: status, prio = "✅ طبيعي", 3
        
        state["last_i"], state["reason"] = i_val, status
    else:
        v, i_val, p_kw, pf, load_pct, status, prio = 0, 0, 0, 0, 0, "🛑 مفصول", 4

    new_readings.append({
        "المحطة": name, "V": v, "I": i_val, "P (kW)": p_kw, 
        "PF": pf, "Load%": load_pct, "الحالة": status, "p": prio
    })

# تحديث السجل التاريخي المتراكم
new_df = pd.DataFrame(new_readings)
st.session_state.all_data_log = pd.concat([new_df, st.session_state.all_data_log], ignore_index=True).head(500)

# --- 5. وحدة التحكم اليدوي (أزرار الفصل) ---
st.subheader("🕹️ وحدة السيطرة اليدوية المستقلة")
c_btns = st.columns(5)
for idx, name in enumerate(st.session_state.transformers):
    with c_btns[idx]:
        if st.session_state.transformers[name]["active"]:
            if st.button(f"فصل {name}", key=f"off_{idx}", use_container_width=True):
                st.session_state.transformers[name]["active"] = False
                st.rerun()
        else:
            if st.button(f"تشغيل {name}", key=f"on_{idx}", use_container_width=True):
                st.session_state.transformers[name]["active"] = True
                st.rerun()

# --- 6. الجدول الموحد (Live Feed & History) ---
st.subheader("📋 سجل البيانات الموحد (القراءات اللحظية والأرشيف)")

display_df = st.session_state.all_data_log.copy()

if protocol_on:
    # الفرز الذكي (الخطر يظهر فوق فوراً)
    display_df = display_df.sort_values(["p"], ascending=[True])
    st.success("البروتوكول فعال: يتم فرز المحولات الخطرة في الصدارة.")
else:
    st.warning("إرسال عشوائي: البيانات تظهر بترتيب وصولها العشوائي.")

def style_row(val):
    if '🚨' in str(val): return 'background-color: #ff4b4b; color: white'
    if '⚠️' in str(val): return 'background-color: #fff3cd'
    if '✅' in str(val): return 'background-color: #d4edda'
    if '🛑' in str(val): return 'background-color: #721c24; color: white'
    return ''

# عرض الجدول الموحد
st.table(display_df.drop(columns=['p']).head(15).style.applymap(style_row, subset=['الحالة']))

st.divider()

# --- 7. استعلام مخصص لكل محولة (Individual Analysis) ---
st.subheader("🔍 مراجعة السجل الخاص لكل محولة على حدة")
selected_trans = st.selectbox("اختر المحولة لعرض تاريخ قراءاتها:", list(st.session_state.transformers.keys()))

history_filtered = st.session_state.all_data_log[st.session_state.all_data_log["المحطة"] == selected_trans]

st.write(f"كافة القراءات المخزنة لـ **{selected_trans}**:")
st.dataframe(history_filtered.drop(columns=['p']), use_container_width=True, hide_index=True)

# سرعة التحديث
time.sleep(1.8 if protocol_on else 1.2)
st.rerun()
