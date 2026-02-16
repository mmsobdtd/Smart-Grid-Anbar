import streamlit as st
import pandas as pd
import numpy as np
import time

# إعدادات الصفحة - وضع الـ Wide ضروري لتكبير الجدول
st.set_page_config(page_title="Al-Anbar Smart Grid Control", layout="wide")

# --- تنسيق مخصص CSS لتكبير الخط والعناوين ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    th { font-size: 1.2rem !important; background-color: #1f77b4 !important; color: white !important; }
    td { font-size: 1.1rem !important; font-weight: 500 !important; }
    .stDataFrame { width: 100% !important; }
    </style>
    """, unsafe_allow_html=True)

# --- محاكاة البيانات ---
if 'net_raw' not in st.session_state: st.session_state.net_raw = 0
if 'net_proto' not in st.session_state: st.session_state.net_proto = 0

# --- العنوان الرئيسي ---
st.title("🏛️ غرفة السيطرة المركزية - كهرباء محافظة الأنبار")
st.markdown("---")

# --- أولاً: شريط ضغط البيانات (بشكل أوضح وعريض) ---
st.subheader("📡 مراقبة تدفق البيانات (Network Traffic)")
n_col1, n_col2 = st.columns(2)

inc_raw = np.random.randint(100, 150)
inc_proto = np.random.randint(10, 25)
st.session_state.net_raw += inc_raw
st.session_state.net_proto += inc_proto

with n_col1:
    st.write("**⚠️ إرسال عشوائي (بدون بروتوكول)**")
    st.progress(min(inc_raw/200, 1.0))
    st.metric("الحجم التراكمي", f"{st.session_state.net_raw} KB", f"+{inc_raw} KB/s", delta_color="inverse")

with n_col2:
    st.write("**✅ إرسال ذكي (ببروتوكول)**")
    st.progress(min(inc_proto/200, 1.0))
    st.metric("الحجم التراكمي", f"{st.session_state.net_proto} KB", f"+{inc_proto} KB/s")

st.markdown("---")

# --- ثانياً: إعدادات الجدول والفرز ---
t_col1, t_col2 = st.columns([2, 1])
with t_col1:
    st.subheader("📋 القراءات اللحظية للمحولات")
with t_col2:
    sort_on = st.toggle("🚀 تفعيل الفرز التلقائي (الأخطر أولاً)", value=True)

# توليد بيانات المحولات
data_list = []
for i in range(1, 7): # عرض 6 محولات لملء الشاشة
    v = np.random.uniform(210, 230)
    # محاكاة حالة خطر عشوائية لمحولة واحدة على الأقل لبيان الفرز
    if i == 2: i_val = np.random.uniform(135, 155)
    else: i_val = np.random.uniform(40, 120)
    
    t = np.random.uniform(40, 95)
    load_pct = (i_val / 150) # كنسبة مئوية من 1
    loss = (i_val**2 * 0.05) / 1000
    
    # تحديد الحالة والأولوية
    if load_pct >= 0.9 or t >= 85:
        status, priority, icon = "🚨 خطر جداً", 1, "🔴"
    elif load_pct >= 0.75:
        status, priority, icon = "⚠️ تحذير حمل", 2, "🟡"
    else:
        status, priority, icon = "✅ عمل طبيعي", 3, "🟢"

    data_list.append({
        "المحطة": f"محولة {i} {icon}",
        "الجهد (V)": round(v, 1),
        "التيار (A)": round(i_val, 1),
        "الحرارة (C°)": round(t, 1),
        "الخسائر (kW)": round(loss, 3),
        "مستوى الحمل": load_pct, # سيتم عرضه كـ Progress Bar
        "الحالة": status,
        "p": priority
    })

df = pd.DataFrame(data_list)
if sort_on:
    df = df.sort_values("p")

# --- عرض الجدول بأقصى حجم وأوضح تنسيق ---
st.dataframe(
    df.drop(columns=['p']),
    column_config={
        "مستوى الحمل": st.column_config.ProgressColumn(
            "مستوى الحمل (%)",
            help="نسبة الاستهلاك من السعة الكلية للمحولة",
            format="%.0f%%",
            min_value=0,
            max_value=1,
        ),
        "المحطة": st.column_config.TextColumn("اسم المحطة", width="medium"),
        "الحالة": st.column_config.TextColumn("التشخيص الآلي", width="medium"),
    },
    use_container_width=True,
    hide_index=True,
    height=400 # تحديد ارتفاع مناسب للجدول
)

# --- تذييل الصفحة ---
if sort_on and df.iloc[0]['p'] == 1:
    st.toast(f"تحذير: {df.iloc[0]['المحطة']} في حالة حرجة!", icon="🚨")

st.info(f"💡 ملاحظة: الجدول يتم فرزه لحظياً. المحولات ذات اللون الأحمر تظهر في الأعلى تلقائياً لاتخاذ إجراء الفصل.")

time.sleep(1)
st.rerun()
    
