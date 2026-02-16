import streamlit as st
import pandas as pd
import numpy as np
import time

# إعدادات الصفحة
st.set_page_config(page_title="Network & Grid Control - Anbar", layout="wide")

# --- محاكاة استهلاك البيانات (Network Traffic) ---
if 'total_data_no_proto' not in st.session_state:
    st.session_state.total_data_no_proto = 0
    st.session_state.total_data_with_proto = 0

# --- العنوان ---
st.title("🌐 مركز مراقبة الشبكة والبيانات - الأنبار")
st.write("**المهندس المنفذ:** محمد نبيل | **جامعة الأنبار - كلية الهندسة**")

# --- قسم مقارنة ضغط الشبكة (Network Stress Section) ---
st.subheader("📊 تحليل ضغط البيانات المرسلة (Network Throughput)")

col_n1, col_n2 = st.columns(2)

# حساب الزيادة في البيانات لكل ثانية (محاكاة)
# بدون بروتوكول: بيانات كثيرة وعشوائية
inc_no_proto = np.random.randint(80, 120) 
# مع بروتوكول: بيانات منظمة وأقل حجماً
inc_with_proto = np.random.randint(15, 30) 

st.session_state.total_data_no_proto += inc_no_proto
st.session_state.total_data_with_proto += inc_with_proto

with col_n1:
    st.write("📡 **بدون بروتوكول (Raw Data Stream)**")
    # شريط ضغط الشبكة (أحمر لأنه يستهلك باندويث عالي)
    st.progress(min(inc_no_proto / 150, 1.0))
    st.metric("حجم البيانات الكلي", f"{st.session_state.total_data_no_proto} KB", f"+{inc_no_proto} KB/s", delta_color="inverse")

with col_n2:
    st.write("🔐 **ببروتوكول ذكي (MQTT/Optimization)**")
    # شريط ضغط الشبكة (أخضر لأنه كفوء)
    st.progress(min(inc_with_proto / 150, 1.0))
    st.metric("حجم البيانات الكلي", f"{st.session_state.total_data_with_proto} KB", f"+{inc_with_proto} KB/s")

# عرض الفرق (الاستثمار في كفاءة البيانات)
efficiency = 100 - (inc_with_proto / inc_no_proto * 100)
st.success(f"💡 **النتيجة:** استخدام البروتوكول قلل ضغط الشبكة بنسبة **{efficiency:.1f}%** مقارنة بالإرسال العشوائي.")

st.divider()

# --- جدول قراءات المحولات ---
st.subheader("📋 جدول مراقبة المحولات اللحظي")

transformers = []
for i in range(1, 5):
    v = np.random.uniform(218, 222)
    i_val = np.random.uniform(40, 145)
    t = np.random.uniform(45, 88)
    load = (i_val / 150) * 100
    loss = (i_val**2 * 0.05) / 1000
    
    status = "طبيعي ✅"
    if load > 90 or t > 80: status = "خطر 🚩"
    elif load > 75: status = "تحذير ⚠️"

    transformers.append({
        "المحطة": f"محولة {i}",
        "الجهد (V)": f"{v:.1f}",
        "التيار (A)": f"{i_val:.1f}",
        "الحرارة (C°)": f"{t:.1f}",
        "الخسائر (kW)": f"{loss:.3f}",
        "نسبة الحمل": f"{load:.1f}%",
        "الحالة": status
    })

df = pd.DataFrame(transformers)

# تنسيق الجدول بشكل احترافي
def style_status(val):
    if 'خطر' in val: return 'background-color: #ff4b4b; color: white'
    if 'تحذير' in val: return 'background-color: #ffa500'
    if 'طبيعي' in val: return 'background-color: #28a745; color: white'
    return ''

st.table(df.style.applymap(style_status, subset=['الحالة']))

# زر لإعادة تصوير البيانات
if st.sidebar.button("تصفير سجل البيانات"):
    st.session_state.total_data_no_proto = 0
    st.session_state.total_data_with_proto = 0
    st.rerun()

time.sleep(1)
st.rerun()
