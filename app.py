import streamlit as st
import pandas as pd
import numpy as np
import time

st.set_page_config(page_title="Al-Anbar Smart Grid - Theft Detection", layout="wide")

# --- 1. تهيئة الذاكرة ---
if 'all_data_log' not in st.session_state:
    st.session_state.all_data_log = pd.DataFrame(columns=["Time", "المحطة", "V", "I", "P (kW)", "PF", "Load%", "الانحراف%", "الحالة", "p"])
if 'net_load' not in st.session_state: st.session_state.net_load = 15 
if 'transformers' not in st.session_state:
    st.session_state.transformers = {f"محولة {i}": {"active": True} for i in range(1, 6)}
if 'time_step' not in st.session_state: st.session_state.time_step = 0
if 'simulated_theft' not in st.session_state: st.session_state.simulated_theft = None

st.session_state.time_step += 1

# --- 2. واجهة العناوين ---
st.title("⚡ نظام الشبكة الذكية وكشف التجاوزات")
st.markdown("### **إعداد الطالب: محمد نبيل**")

# --- 3. القائمة الجانبية (محاكاة التجاوزات) ---
st.sidebar.header("⚠️ وحدة كشف التجاوزات")
protocol_on = st.sidebar.toggle("🔐 تفعيل الفرز اللحظي", value=True)

st.sidebar.markdown("---")
st.sidebar.subheader("محاكاة ربط عشوائي (تجاوز)")
st.sidebar.write("اضغط لمحاكاة ربط حمل غير قانوني على إحدى المحطات لاختبار قدرة النظام على كشفه.")

target_transformer = st.sidebar.selectbox("اختر المحطة المستهدفة:", list(st.session_state.transformers.keys()))
if st.sidebar.button("🪝 إحداث تجاوز مفاجئ"):
    st.session_state.simulated_theft = target_transformer

if st.sidebar.button("🧹 إنهاء حالة التجاوز"):
    st.session_state.simulated_theft = None

st.sidebar.divider()
if st.sidebar.button("♻️ تصفير المنظومة"):
    st.session_state.all_data_log = st.session_state.all_data_log.iloc[0:0]
    st.session_state.time_step = 0
    st.session_state.simulated_theft = None
    st.rerun()

# --- 4. توليد البيانات وخوارزمية كشف التجاوز ---
current_batch = []
current_time = pd.Timestamp.now().strftime("%H:%M:%S")

# الحمل المتوقع بناءً على الوقت (النمط الطبيعي)
peak_multiplier = 0.6 + 0.5 * np.abs(np.sin(st.session_state.time_step * np.pi / 15))
expected_i = 90 * peak_multiplier

for name, state in st.session_state.transformers.items():
    if state["active"]:
        v = int(np.random.uniform(215, 226))
        pf = round(np.random.uniform(0.88, 0.94), 2)
        
        # التيار الطبيعي
        i_val = int(expected_i + np.random.uniform(-5, 10))
        
        # حقن التجاوز إذا تم تفعيله من المستخدم
        if st.session_state.simulated_theft == name:
            i_val += int(np.random.uniform(40, 60)) # سحب تيار عالي مفاجئ
            pf -= np.random.uniform(0.10, 0.18)    # هبوط في معامل القدرة بسبب رداءة الربط
            v -= int(np.random.uniform(5, 12))      # هبوط في الفولتية
            
        i_val = min(max(i_val, 0), 160)
        p_kw = int((v * i_val * pf) / 1000)
        load_pct = int((i_val / 150) * 100)
        
        # حساب نسبة الانحراف عن السلوك الطبيعي
        deviation_pct = int(((i_val - expected_i) / expected_i) * 100) if expected_i > 0 else 0
        
        # خوارزمية الذكاء والتشخيص (Decision Logic)
        if deviation_pct > 35 and pf < 0.82:
            status, prio = "🪝 اشتباه بتجاوز (سرقة)", 0 # أولوية قصوى
        elif load_pct >= 95:
            status, prio = "🚨 خطر جداً (حمل زائد)", 1
        elif load_pct >= 80:
            status, prio = "⚠️ تنبيه (ذروة)", 2
        else:
            status, prio = "✅ مستقر", 3
            
    else:
        v, i_val, p_kw, pf, load_pct, deviation_pct, status, prio = 0, 0, 0, 0, 0, 0, "🛑 مفصول", 4

    current_batch.append({
        "Time": current_time, "المحطة": name, "V": v, "I": i_val, 
        "P (kW)": p_kw, "PF": pf, "Load%": load_pct, "الانحراف%": f"{deviation_pct}%", "الحالة": status, "p": prio
    })

df_batch = pd.DataFrame(current_batch)

if protocol_on:
    df_batch = df_batch.sort_values(by="p", ascending=True)
else:
    df_batch = df_batch.sample(frac=1).reset_index(drop=True)

st.session_state.all_data_log = pd.concat([df_batch, st.session_state.all_data_log], ignore_index=True).head(500)

# --- 5. عرض الجداول والرسوم ---
st.subheader("📈 تتبع الانحراف اللحظي (Anomaly Tracking)")
col1, col2 = st.columns([2, 1])

with col1:
    if not st.session_state.all_data_log.empty:
        plot_df = st.session_state.all_data_log.copy()
        chart_data = plot_df.drop_duplicates(subset=['Time', 'المحطة']).pivot(index='Time', columns='المحطة', values='I')
        st.line_chart(chart_data.tail(15))
        
with col2:
    st.info("**كيف يعمل كشف التجاوز؟**\n\nيقوم النظام بمقارنة التيار المسحوب (I) مع الاستهلاك المتوقع في هذا الوقت. إذا تجاوز الانحراف **35%** مع هبوط معامل القدرة (PF) لأقل من **0.82**، يتم تصنيف الحالة فوراً كـ **اشتباه بتجاوز** ويُرفع التقرير لأعلى القائمة.")

st.divider()

st.subheader("📋 جدول الرصد والتشخيص الذكي")
def style_row(val):
    if '🪝' in str(val): return 'background-color: #800080; color: white; font-weight: bold' # لون بنفسجي للتجاوزات
    if '🚨' in str(val): return 'background-color: #ff4b4b; color: white'
    if '⚠️' in str(val): return 'background-color: #fff3cd'
    if '✅' in str(val): return 'background-color: #d4edda'
    if '🛑' in str(val): return 'background-color: #721c24; color: white'
    return ''

st.write(df_batch.drop(columns=['p']).style.map(style_row, subset=['الحالة']))

time.sleep(1.5)
st.rerun()
