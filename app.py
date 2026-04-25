import streamlit as st
import pandas as pd
import numpy as np

# إعدادات الصفحة
st.set_page_config(page_title="Al-Anbar Smart Grid - Visual Theft Location", layout="wide")

# --- 1. تهيئة الذاكرة (بدون تحديث تلقائي) ---
if 'time_step' not in st.session_state: st.session_state.time_step = 0
if 'transformers' not in st.session_state:
    st.session_state.transformers = {f"محطة {i}": {"active": True} for i in range(1, 6)}

# --- 2. واجهة العناوين ---
st.title("⚡ محاكي الشبكة الذكية: تتبع التجاوزات الدقيق (Al-Anbar SCADA)")
st.markdown("### **تحليل هبوط القدرة وتحديد الموقع بين الأعمدة**")

# --- 3. القائمة الجانبية (محاكاة التجاوز الموضعي) ---
st.sidebar.header("🕹️ لوحة المحاكاة والتحكم")
if st.sidebar.button("🔄 سحب بيانات جديدة (Step)", use_container_width=True):
    st.session_state.time_step += 1

st.sidebar.divider()
st.sidebar.header("⚠️ محاكاة تجاوز موضعي")
st.sidebar.write("اختر المقطع (السلك) الذي سيتم رمي التجاوز عليه:")

# المقاطع تمثل المسافة بين الأعمدة والمنازل
segments = ["لا يوجد تجاوز", 
            "بين محولة وعامود 1", 
            "بين عامود 1 و 2", 
            "بين عامود 2 و 3",
            "بين عامود 3 و 4"]

target_segment = st.sidebar.selectbox("موقع الربط غير القانوني:", segments)

st.sidebar.divider()
if st.sidebar.button("♻️ تصفير النظام"):
    st.session_state.time_step = 0
    st.session_state.alert_history = []
    st.rerun()

# --- 4. محاكاة الشبكة والقياس التفاضلي ---
# استهلاك المنازل الشرعية المربوطة بكل مقطع (بالأمبير)
houses_load = {
    "مقطع 1": 20, 
    "مقطع 2": 18, 
    "مقطع 3": 22,
    "مقطع 4": 15
}

line_loss_margin = 2.0 
total_expected_i = sum(houses_load.values())

# إذا كان هناك تجاوز، نضيف تياراً مخفياً في المقطع المحدد
theft_current = 0
if target_segment != "لا يوجد تجاوز":
    theft_current = np.random.uniform(40, 60) 

# حساب التيارات الفعلية المتدفقة في الخطوط
actual_i_in_1 = total_expected_i + (theft_current if target_segment != "لا يوجد تجاوز" else 0)
actual_i_in_2 = actual_i_in_1 - houses_load["مقطع 1"] - (theft_current if target_segment == "بين محولة وعامود 1" else 0)
actual_i_in_3 = actual_i_in_2 - houses_load["مقطع 2"] - (theft_current if target_segment == "بين عامود 1 و 2" else 0)
actual_i_in_4 = actual_i_in_3 - houses_load["مقطع 3"] - (theft_current if target_segment == "بين عامود 2 و 3" else 0)

network_data = []
location_alert = None

# دالة لتحليل المقطع وكشف التجاوز
def analyze_segment(seg_name, i_in, next_i_in, legal_load):
    current_loss = i_in - (next_i_in + legal_load)
    
    if current_loss > line_loss_margin:
        status = "🚨 تجاوز مكتشف!"
        color = "#800080" # بنفسجي
    else:
        status = "✅ سليم"
        color = "#d4edda" # أخضر
        
    network_data.append({
        "المقطع": seg_name,
        "التيار الداخل (A)": round(i_in, 1),
        "التيار الخارج (A)": round(next_i_in, 1),
        "استهلاك العدادات الشرعية (A)": round(legal_load, 1),
        "التيار المفقود (A)": round(current_loss, 1),
        "التشخيص": status,
        "color": color
    })

analyze_segment("مقطـع 1 (محولة -> عامود 1)", actual_i_in_1, actual_i_in_2, houses_load["مقطع 1"])
analyze_segment("مقطـع 2 (عامود 1 -> عامود 2)", actual_i_in_2, actual_i_in_3, houses_load["مقطع 2"])
analyze_segment("مقطـع 3 (عامود 2 -> عامود 3)", actual_i_in_3, actual_i_in_4, houses_load["مقطع 3"])
analyze_segment("مقطـع 4 (عامود 3 -> نهاية الخط)", actual_i_in_4, 0, houses_load["مقطع 4"]) 

df_network = pd.DataFrame(network_data)

# --- 5. مقارنة القدرة الشاملة (Overall Audit) ---
st.subheader("📊 تحليل الطاقة ومقارنة القدرة الشاملة")
col_p1, col_p2, col_p3 = st.columns(3)

total_legal_consumption = sum(houses_load.values())
actual_supplied_power = actual_i_in_1 
power_difference = actual_supplied_power - total_legal_consumption

with col_p1:
    st.metric("القدرة الخارجة من المحولة", f"{round(actual_supplied_power, 1)}A", help="التيار الفعلي المقاس عند مخرج المحطة.")
with col_p2:
    st.metric("مجموع استهلاك البيوت (المفروض)", f"{round(total_legal_consumption, 1)}A", help="مجموع ما تسجله عدادات المنازل الشرعية.")
with col_p3:
    if power_difference > 5.0:
        st.metric("القدرة المفقودة (التجاوز)", f"{round(power_difference, 1)}A", delta=f"{round(power_difference, 1)}A", delta_color="inverse")
    else:
        st.metric("الفاقد الفني (طبيعي)", f"{round(power_difference, 1)}A", delta=None)

# --- 6. التحديد الدقيق لمكان التجاوز (Final Diagnose) ---
st.divider()
st.subheader("📍 التحديد الدقيق لموقع التجاوز وتتبع الأثر")

# العثور على المقطع المصاب
theft_segment_row = df_network[df_network["التشخيص"].str.contains("🚨")].first_valid_index()

if theft_segment_row is not None:
    infected_segment = df_network.loc[theft_segment_row, "المقطع"]
    current_stolen = df_network.loc[theft_segment_row, "التيار المفقود (A)"]
    
    # إرسال التنبيه التشخيصي
    st.error(f"🪝 إنذار أمني: تم رصد تجاوز مؤكد في [{infected_segment}]. يرجى إرسال فرق الصيانة للتتبع الدقيق بين هاتين النقطتين. التيار المفقود يقدر بـ {current_stolen}A.")
else:
    st.success("✅ جميع خطوط النقل آمنة ولا يوجد تسريب للطاقة.")

# عرض الجدول التحليلي التفصيلي
st.write("يوضح الجدول التالي حسابات تدقيق الطاقة (Energy Audit) لكل مقطع بين المحولة والمنازل:")

def style_feeder(val):
    if '🚨' in str(val): return 'background-color: #800080; color: white; font-weight: bold' # بنفسجي
    if '✅' in str(val): return 'background-color: #d4edda' # أخضر
    return ''

st.table(df_network.drop(columns=['color']).style.map(style_feeder, subset=['التشخيص']))
