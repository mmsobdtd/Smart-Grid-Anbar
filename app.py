import streamlit as st
import pandas as pd
import numpy as np

# إعدادات الصفحة
st.set_page_config(page_title="Al-Anbar Grid - Segment Theft Detection", layout="wide")

# --- 1. تهيئة الذاكرة (بدون التحديث التلقائي المزعج) ---
if 'time_step' not in st.session_state: 
    st.session_state.time_step = 0
if 'alert_history' not in st.session_state: 
    st.session_state.alert_history = []

# --- 2. واجهة العناوين ---
st.title("⚡ نظام المراقبة الذكي: كشف التجاوزات على خطوط النقل")
st.markdown("### **تحليل المقاطع (Segment Analysis) بين المحولة والمنازل**")

# --- 3. القائمة الجانبية للتحكم ---
st.sidebar.header("🕹️ لوحة التحكم والمحاكاة")

# زر تحديث البيانات اليدوي (بديل التحديث التلقائي)
if st.sidebar.button("🔄 سحب قراءة جديدة (التالي)", use_container_width=True):
    st.session_state.time_step += 1

st.sidebar.divider()
st.sidebar.header("⚠️ وحدة حقن التجاوزات")
st.sidebar.write("اختر المقطع (السلك) الذي سيتم رمي التجاوز عليه:")

# المقاطع
segments = ["لا يوجد تجاوز", 
            "مقطع A (محولة -> عمود 1)", 
            "مقطع B (عمود 1 -> عمود 2)", 
            "مقطع C (عمود 2 -> عمود 3)"]

target_segment = st.sidebar.selectbox("موقع التجاوز (الربط غير القانوني):", segments)

st.sidebar.divider()
if st.sidebar.button("🗑️ تصفير النظام"):
    st.session_state.time_step = 0
    st.session_state.alert_history = []
    st.rerun()

# --- 4. محاكاة الشبكة والقياس التفاضلي ---
houses_load = {
    "مقطع A": 30, 
    "مقطع B": 45, 
    "مقطع C": 25  
}

line_loss_margin = 2.0 
total_expected_i = sum(houses_load.values())

theft_current = 0
if target_segment != "لا يوجد تجاوز":
    theft_current = np.random.uniform(40, 60) 

# حساب التيارات الفعلية
actual_i_in_A = total_expected_i + (theft_current if target_segment in ["مقطع A", "مقطع B", "مقطع C"] else 0)
actual_i_in_B = actual_i_in_A - houses_load["مقطع A"] - (theft_current if target_segment == "مقطع A" else 0)
actual_i_in_C = actual_i_in_B - houses_load["مقطع B"] - (theft_current if target_segment == "مقطع B" else 0)

network_data = []
alerts_triggered = []

def analyze_segment(seg_name, i_in, next_i_in, legal_load):
    current_loss = i_in - (next_i_in + legal_load)
    
    if current_loss > line_loss_margin:
        status = "🚨 تم كشف تجاوز!"
        alerts_triggered.append(f"⚠️ إنذار أمني (الخطوة الزمنية {st.session_state.time_step}): اكتشاف ربط غير قانوني في {seg_name} بتيار مسروق يقدر بـ {round(current_loss,1)}A.")
    else:
        status = "✅ المقطع سليم"
        
    network_data.append({
        "المقطع (Segment)": seg_name,
        "التيار الداخل (A)": round(i_in, 1),
        "التيار الخارج (A)": round(next_i_in, 1),
        "استهلاك العدادات (A)": round(legal_load, 1),
        "التيار المفقود (A)": round(current_loss, 1),
        "حالة الخط": status
    })

analyze_segment("مقطع A", actual_i_in_A, actual_i_in_B, houses_load["مقطع A"])
analyze_segment("مقطع B", actual_i_in_B, actual_i_in_C, houses_load["مقطع B"])
analyze_segment("مقطع C", actual_i_in_C, 0, houses_load["مقطع C"]) 

df_network = pd.DataFrame(network_data)

# --- 5. نظام الإنذار ---
st.subheader("🔔 مركز الإشعارات والإنذار المبكر")

if alerts_triggered:
    for alert in alerts_triggered:
        st.error(alert, icon="📍")
        if alert not in st.session_state.alert_history:
            st.session_state.alert_history.insert(0, alert)
else:
    st.success("✅ جميع خطوط النقل آمنة ولا يوجد تسريب للطاقة.", icon="🛡️")

st.divider()

# --- 6. جدول التحليل ---
st.subheader("📊 لوحة تدقيق المقاطع (Energy Audit)")
st.write(f"**القراءة الحالية:** الخطوة الزمنية {st.session_state.time_step}")

def style_segments(val):
    if '🚨' in str(val): return 'background-color: #ff4b4b; color: white; font-weight: bold'
    if '✅' in str(val): return 'background-color: #d4edda'
    return ''

st.table(df_network.style.map(style_segments, subset=['حالة الخط']))

# --- 7. سجل المراقبة ---
with st.expander("📂 سجل إنذارات التجاوزات السابقة"):
    if st.session_state.alert_history:
        for log in st.session_state.alert_history[:10]: 
            st.write(log)
    else:
        st.write("لا توجد إنذارات مسجلة.")
                
