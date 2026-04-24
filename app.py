import streamlit as st
import pandas as pd
import numpy as np
import time

# إعدادات الصفحة
st.set_page_config(page_title="Al-Anbar Grid - Advanced SCADA", layout="wide")

# --- 1. تهيئة الذاكرة والسجلات ---
# تمت إضافة عمود 'Time' لتتبع القراءات زمنياً
if 'all_data_log' not in st.session_state:
    st.session_state.all_data_log = pd.DataFrame(columns=["Time", "المحطة", "V", "I", "P (kW)", "PF", "Load%", "الحالة", "p"])
if 'net_load' not in st.session_state: 
    st.session_state.net_load = 15 
if 'transformers' not in st.session_state:
    st.session_state.transformers = {f"محولة {i}": {"active": True, "last_i": 75} for i in range(1, 6)}
if 'time_step' not in st.session_state:
    st.session_state.time_step = 0

# زيادة العداد الزمني مع كل تحديث للصفحة
st.session_state.time_step += 1

# --- 2. واجهة العناوين ---
st.title("⚡ نظام الرصد والفرز الديناميكي المتقدم")
st.markdown("### **إعداد الطالب: محمد نبيل**")

# --- 3. القائمة الجانبية (التحكم والتصدير) ---
st.sidebar.header("🕹️ لوحة التحكم الرئيسية")
protocol_on = st.sidebar.toggle("🔐 تفعيل الفرز اللحظي", value=True)

if st.sidebar.button("♻️ تصفير المنظومة"):
    st.session_state.all_data_log = st.session_state.all_data_log.iloc[0:0]
    st.session_state.time_step = 0
    st.session_state.net_load = 15
    st.rerun()

st.sidebar.divider()
st.sidebar.subheader("💾 تصدير البيانات (لغرض التحليل)")
st.sidebar.write("تصدير القراءات بصيغة CSV لإدخالها في MATLAB أو برامج التحليل الأخرى.")

@st.cache_data
def convert_df(df):
    # تحويل البيانات إلى صيغة متوافقة مع Excel و MATLAB
    return df.to_csv(index=False).encode('utf-8-sig')

csv_data = convert_df(st.session_state.all_data_log)
st.sidebar.download_button(
    label="📥 تحميل السجل كملف CSV",
    data=csv_data,
    file_name='anbar_grid_log.csv',
    mime='text/csv',
)

# --- 4. محاكاة استقرار الشبكة والانهيار التدريجي ---
st.subheader("🌐 إجهاد تدفق البيانات للشبكة")
col_net1, col_net2, col_net3 = st.columns(3)

active_count = sum(1 for t in st.session_state.transformers.values() if t["active"])

if not protocol_on:
    st.session_state.net_load += np.random.uniform(1.5, 3.5) * (active_count / 2)
    pps = np.random.randint(450, 600)
    latency = int(st.session_state.net_load * 12)
    net_status = "⚠️ اختناق البيانات" if st.session_state.net_load < 90 else "🚨 انهيار وشيك"
else:
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
    st.error("🆘 !!! CRITICAL NETWORK FAILURE !!!")
    if st.button("إعادة محاولة الاتصال"):
        st.session_state.net_load = 15
        st.rerun()
    st.stop()

st.divider()

# --- 5. توليد ومعالجة البيانات (محاكاة أوقات الذروة) ---
current_batch = []
current_time = pd.Timestamp.now().strftime("%H:%M:%S")

# معادلة رياضية لمحاكاة صعود وهبوط الأحمال بمرور الوقت (Peak Load Simulation)
peak_multiplier = 0.6 + 0.5 * np.abs(np.sin(st.session_state.time_step * np.pi / 15))

for name, state in st.session_state.transformers.items():
    if state["active"]:
        v = int(np.random.uniform(215, 226))
        # التيار يتأثر بمعامل الذروة ليحاكي السلوك الواقعي
        base_i = 90 * peak_multiplier
        i_val = int(base_i + np.random.uniform(-10, 15)) 
        i_val = min(max(i_val, 0), 160) # تحديد أعلى تيار ممكن
        
        pf = round(np.random.uniform(0.86, 0.94), 2)
        p_kw = int((v * i_val * pf) / 1000)
        load_pct = int((i_val / 150) * 100)
        
        if load_pct >= 95: status, prio = "🚨 خطر جداً", 1
        elif load_pct >= 80: status, prio = "⚠️ تنبيه حمل", 2
        else: status, prio = "✅ طبيعي", 3
    else:
        v, i_val, p_kw, pf, load_pct, status, prio = 0, 0, 0, 0, 0, "🛑 مفصول", 4

    current_batch.append({
        "Time": current_time, "المحطة": name, "V": v, "I": i_val, 
        "P (kW)": p_kw, "PF": pf, "Load%": load_pct, "الحالة": status, "p": prio
    })

df_batch = pd.DataFrame(current_batch)

# الفرز الديناميكي
if protocol_on:
    df_batch = df_batch.sort_values(by="p", ascending=True)
else:
    df_batch = df_batch.sample(frac=1).reset_index(drop=True)

# إضافة الدفعة للسجل الكلي
st.session_state.all_data_log = pd.concat([df_batch, st.session_state.all_data_log], ignore_index=True).head(500)

# --- 6. أزرار التحكم اللحظية ---
st.subheader("🕹️ وحدة السيطرة على المحطات")
c_btns = st.columns(5)
for idx, (name, state) in enumerate(st.session_state.transformers.items()):
    with c_btns[idx]:
        if state["active"]:
            if st.button(f"فصل {name}", key=f"off_{idx}"):
                st.session_state.transformers[name]["active"] = False
                st.rerun()
        else:
            if st.button(f"تشغيل {name}", key=f"on_{idx}"):
                st.session_state.transformers[name]["active"] = True
                st.rerun()

st.divider()

# --- 7. الرسوم البيانية اللحظية (Live Visualization) ---
st.subheader("📈 تتبع استهلاك الطاقة اللحظي للأحمال (P_kW)")
if not st.session_state.all_data_log.empty:
    # إعادة ترتيب البيانات لرسم المحطات المختلفة عبر الزمن
    plot_df = st.session_state.all_data_log.copy()
    # استخدام drop_duplicates لتفادي تكرار الأوقات في حال إرسال نفس الدفعة
    chart_data = plot_df.drop_duplicates(subset=['Time', 'المحطة']).pivot(index='Time', columns='المحطة', values='P (kW)')
    
    # رسم آخر 15 قراءة زمنية لتجنب ازدحام الرسم البياني
    st.line_chart(chart_data.tail(15))

st.divider()

# --- 8. الجدول اللحظي المنسق ---
st.subheader("📋 جدول الرصد الديناميكي")
def style_row(val):
    if '🚨' in str(val): return 'background-color: #ff4b4b; color: white'
    if '⚠️' in str(val): return 'background-color: #fff3cd'
    if '✅' in str(val): return 'background-color: #d4edda'
    if '🛑' in str(val): return 'background-color: #721c24; color: white'
    return ''

st.write(df_batch.drop(columns=['p']).style.map(style_row, subset=['الحالة']))

# توقيت التحديث اللحظي (1.5 ثانية)
time.sleep(1.5)
st.rerun()
