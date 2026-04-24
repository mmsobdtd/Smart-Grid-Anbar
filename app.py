import streamlit as st
import pandas as pd
import numpy as np
import time

st.set_page_config(page_title="Al-Anbar Grid - Segment Theft Detection", layout="wide")

# --- 1. تهيئة الذاكرة ---
if 'time_step' not in st.session_state: st.session_state.time_step = 0
if 'alert_history' not in st.session_state: st.session_state.alert_history = []
st.session_state.time_step += 1

st.title("⚡ نظام المراقبة الذكي: كشف التجاوزات على خطوط النقل")
st.markdown("### **تحليل المقاطع (Segment Analysis) بين المحولة والمنازل**")

# --- 2. محاكاة التجاوز (القائمة الجانبية) ---
st.sidebar.header("⚠️ وحدة حقن التجاوزات")
st.sidebar.write("اختر المقطع (السلك) الذي سيتم رمي التجاوز عليه:")

# المقاطع تمثل المسافة بين الأعمدة والمنازل
segments = ["لا يوجد تجاوز", 
            "مقطع A (محولة -> عمود 1)", 
            "مقطع B (عمود 1 -> عمود 2)", 
            "مقطع C (عمود 2 -> عمود 3)"]

target_segment = st.sidebar.selectbox("موقع التجاوز (الربط غير القانوني):", segments)

if st.sidebar.button("♻️ تصفير النظام"):
    st.session_state.alert_history = []
    st.rerun()

# --- 3. محاكاة الشبكة والقياس التفاضلي ---
# استهلاك المنازل الشرعية المربوطة بكل مقطع (بالأمبير)
houses_load = {
    "مقطع A": 30, # منازل مربوطة بين المحولة والعمود 1
    "مقطع B": 45, # منازل مربوطة بين العمود 1 و 2
    "مقطع C": 25  # منازل مربوطة في نهاية الخط
}

line_loss_margin = 2.0 # الفاقد الفني الطبيعي المسموح به في الأسلاك (حرارة، مقاومة)

# التيار الكلي الذي يجب أن يخرج من المحولة (الوضع الطبيعي)
total_expected_i = sum(houses_load.values())

# إذا كان هناك تجاوز، نضيف تياراً مخفياً في المقطع المحدد
theft_current = 0
if target_segment != "لا يوجد تجاوز":
    theft_current = np.random.uniform(40, 60) # سحب تيار عالي

# حساب التيارات الفعلية المتدفقة في الخطوط
actual_i_in_A = total_expected_i + (theft_current if target_segment in ["مقطع A", "مقطع B", "مقطع C"] else 0)
actual_i_in_B = actual_i_in_A - houses_load["مقطع A"] - (theft_current if target_segment == "مقطع A" else 0)
actual_i_in_C = actual_i_in_B - houses_load["مقطع B"] - (theft_current if target_segment == "مقطع B" else 0)

network_data = []
alerts_triggered = []

# دالة لتحليل المقطع وكشف التجاوز
def analyze_segment(seg_name, i_in, next_i_in, legal_load):
    # حساب التيار المفقود في هذا المقطع بالتحديد
    # التيار الداخل - (التيار الذاهب للمقطع التالي + استهلاك منازل المقطع الحالي)
    current_loss = i_in - (next_i_in + legal_load)
    
    if current_loss > line_loss_margin:
        status = "🚨 تم كشف تجاوز!"
        color = "#ff4b4b"
        alerts_triggered.append(f"⚠️ إنذار أمني: اكتشاف ربط غير قانوني في {seg_name} بتيار مسروق يقدر بـ {round(current_loss,1)}A.")
    else:
        status = "✅ المقطع سليم"
        color = "#d4edda"
        
    network_data.append({
        "المقطع (Segment)": seg_name,
        "قراءة حساس الدخول (A)": round(i_in, 1),
        "قراءة حساس الخروج (A)": round(next_i_in, 1),
        "استهلاك العدادات الشرعية (A)": round(legal_load, 1),
        "التيار المفقود (A)": round(current_loss, 1),
        "حالة الخط": status
    })

# تشغيل التحليل لكل مقطع
analyze_segment("مقطع A", actual_i_in_A, actual_i_in_B, houses_load["مقطع A"])
analyze_segment("مقطع B", actual_i_in_B, actual_i_in_C, houses_load["مقطع B"])
analyze_segment("مقطع C", actual_i_in_C, 0, houses_load["مقطع C"]) # المقطع الأخير خروجه صفر

df_network = pd.DataFrame(network_data)

# --- 4. نظام إرسال الإشارات والإنذارات (Alert System) ---
st.subheader("🔔 مركز الإشعارات والإنذار المبكر")

if alerts_triggered:
    # إرسال إشعار لحظي للمراقب (تظهر نافذة منبثقة في الشاشة)
    st.toast("🚨 تم رصد تجاوز جديد على الشبكة!", icon="🚨")
    
    # عرض الإشارة باللون الأحمر البارز
    for alert in alerts_triggered:
        st.error(alert, icon="📍")
        # حفظ الإنذار في السجل
        time_now = pd.Timestamp.now().strftime("%H:%M:%S")
        st.session_state.alert_history.insert(0, f"[{time_now}] {alert}")
else:
    st.success("✅ جميع خطوط النقل آمنة ولا يوجد تسريب للطاقة.", icon="🛡️")

st.divider()

# --- 5. جدول تحليل المقاطع التفصيلي ---
st.subheader("📊 لوحة تدقيق المقاطع (Energy Audit)")
st.write("يقوم النظام بطرح قراءة العدادات الشرعية للبيوت والتيار العابر للمقطع التالي من التيار الكلي الداخل للمقطع لمعرفة مكان التسريب بدقة.")

def style_segments(val):
    if '🚨' in str(val): return 'background-color: #ff4b4b; color: white; font-weight: bold'
    if '✅' in str(val): return 'background-color: #d4edda'
    return ''

st.table(df_network.style.map(style_segments, subset=['حالة الخط']))

# --- 6. سجل المراقبة (Log) ---
with st.expander("📂 سجل إنذارات التجاوزات السابقة"):
    if st.session_state.alert_history:
        for log in st.session_state.alert_history[:10]: # عرض آخر 10 إنذارات
            st.write(log)
    else:
        st.write("لا توجد إنذارات مسجلة.")

time.sleep(2.0)
st.rerun()
