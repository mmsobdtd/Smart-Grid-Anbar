import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime

# إعدادات الصفحة
st.set_page_config(page_title="مركز سيطرة الأنبار - فرز الأولوية", layout="wide")

# --- محاكاة استهلاك البيانات ---
if 'total_data_no_proto' not in st.session_state:
    st.session_state.total_data_no_proto = 0
    st.session_state.total_data_with_proto = 0

# --- العنوان ---
st.title("🛡️ نظام السيطرة والفرز الذكي - محافظة الأنبار")
st.write(f"**إشراف المهندس:** محمد نبيل | **الحالة:** مراقبة مباشرة | **الوقت:** {datetime.now().strftime('%H:%M:%S')}")

# --- قسم مقارنة ضغط الشبكة ---
col_n1, col_n2 = st.columns(2)
inc_no_proto = np.random.randint(80, 120) 
inc_with_proto = np.random.randint(15, 30) 
st.session_state.total_data_no_proto += inc_no_proto
st.session_state.total_data_with_proto += inc_with_proto

with col_n1:
    st.write("📡 **بدون بروتوكول (إرسال عشوائي)**")
    st.progress(min(inc_no_proto / 150, 1.0))
    st.caption(f"تراكم البيانات: {st.session_state.total_data_no_proto} KB")

with col_n2:
    st.write("🔐 **ببروتوكول ذكي (إرسال منظم)**")
    st.progress(min(inc_with_proto / 150, 1.0))
    st.caption(f"تراكم البيانات: {st.session_state.total_data_with_proto} KB")

st.divider()

# --- قسم الجدول والتحكم بالفرز ---
col_header, col_toggle = st.columns([3, 1])

with col_header:
    st.subheader("📋 جدول مراقبة المحولات اللحظي")

with col_toggle:
    # الزر الذي طلبته: تفعيل بروتوكول الفرز حسب الخطورة
    sort_active = st.toggle("تفعيل فرز الأولوية (الخطر أولاً)", value=True)

# توليد بيانات المحولات
transformers = []
for i in range(1, 6): # زدت عدد المحولات لتوضيح الفرز بشكل أفضل
    v = np.random.uniform(215, 225)
    # محاكاة أحمال مختلفة للمحولات
    if i == 1: i_val = np.random.uniform(135, 155) # نجعل محولة 1 غالباً في خطر
    elif i == 3: i_val = np.random.uniform(115, 130) # نجعل محولة 3 في تحذير
    else: i_val = np.random.uniform(40, 100)
    
    t = np.random.uniform(40, 90)
    load = (i_val / 150) * 100
    loss = (i_val**2 * 0.05) / 1000
    
    # تحديد الحالة والرقم التعريفي للفرز
    if load >= 90 or t >= 85:
        status = "خطر 🚩"
        priority = 1 # أعلى أولوية
    elif load >= 75:
        status = "تحذير ⚠️"
        priority = 2
    else:
        status = "طبيعي ✅"
        priority = 3

    transformers.append({
        "المحطة": f"محولة {i}",
        "الجهد (V)": f"{v:.1f}",
        "التيار (A)": f"{i_val:.1f}",
        "الحرارة (C°)": f"{t:.1f}",
        "الخسائر (kW)": f"{loss:.3f}",
        "نسبة الحمل": f"{load:.1f}%",
        "الحالة": status,
        "priority": priority # حقل مخفي للفرز
    })

df = pd.DataFrame(transformers)

# --- منطق الفرز حسب طلبك ---
if sort_active:
    # فرز الجدول بناءً على حقل الـ priority
    df = df.sort_values(by="priority")

# حذف عمود الـ priority قبل العرض ليبقى الجدول نظيفاً
df_display = df.drop(columns=['priority'])

# تنسيق الألوان
def style_status(val):
    if 'خطر' in val: return 'background-color: #ff4b4b; color: white; font-weight: bold'
    if 'تحذير' in val: return 'background-color: #ffa500; color: black'
    if 'طبيعي' in val: return 'background-color: #28a745; color: white'
    return ''

# عرض الجدول
st.table(df_display.style.applymap(style_status, subset=['الحالة']))

# --- تذييل الصفحة ---
st.divider()
st.info(f"💡 **ملاحظة:** {'نظام الفرز الذكي قيد التشغيل. يتم دفع المحولات الأكثر خطورة إلى أعلى القائمة لضمان سرعة الاستجابة.' if sort_active else 'نظام الفرز معطل. يتم عرض المحولات بترتيبها التسلسلي.'}")

# تحديث تلقائي كل ثانية
time.sleep(1)
st.rerun()
