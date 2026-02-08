import streamlit as st
import pandas as pd
import random
import time
from datetime import datetime

# إعدادات الصفحة الرسمية
st.set_page_config(page_title="نظام طاقة الأنبار - محاكاة البروتوكول", layout="wide")

# --- 1. إعدادات المنشآت والبيانات المرجعية ---
LOCATIONS_CONFIG = {
    "مستشفى الرمادي التعليمي": {"avg": 400, "priority": 10},
    "معمل زجاج الرمادي": {"avg": 500, "priority": 10},
    "جامعة الأنبار (المجمع)": {"avg": 350, "priority": 8},
    "حي التأميم (المغذي الرئيسي)": {"avg": 300, "priority": 7}
}

# تهيئة ذاكرة البيانات (Session State) لضمان سلاسة التحديث
if 'data_history' not in st.session_state:
    st.session_state.data_history = []

def add_entry(name, current):
    avg = LOCATIONS_CONFIG[name]["avg"]
    if current < avg:
        status, level = "🟢 مستقر", 1
    elif avg <= current < (avg * 1.2):
        status, level = "🟡 تنبيه (تجاوز المتوسط)", 2
    else:
        status, level = "🔴 خطر (حمل زائد)", 3

    entry = {
        "المنشأة": name,
        "التيار (A)": current,
        "الحالة": status,
        "الوقت": datetime.now().strftime("%H:%M:%S.%f")[:-3],
        "level": level,
        "p": LOCATIONS_CONFIG[name]["priority"]
    }
    st.session_state.data_history.append(entry)
    # الحفاظ على آخر 30 سجل لضمان سرعة المتصفح
    if len(st.session_state.data_history) > 30:
        st.session_state.data_history.pop(0)

# --- 2. واجهة التحكم (Sidebar) ---
with st.sidebar:
    st.title("⚙️ إعدادات النظام")
    mode = st.radio("اختر وضعية الشبكة:", ["بدون بروتوكول (خطر الانهيار)", "بالبروتوكول الذكي (الأولويات)"])
    input_type = st.radio("طريقة البث:", ["تلقائي (فائق السرعة)", "يدوي"])
    st.markdown("---")
    if st.button("🗑️ مسح سجل البيانات"):
        st.session_state.data_history = []
        st.rerun()

# --- 3. تصميم الواجهة الرئيسية ---
st.title("🖥️ مركز التحكم في أحمال مدينة الرمادي")
st.markdown(f"الحالة التشغيلية الآن: **{mode}**")

# حاوية ثابتة للرسم البياني والجدول لمنع الارتجاج في الشاشة
dashboard_placeholder = st.empty()

# --- 4. منطق التشغيل (تلقائي / يدوي) ---
if input_type == "تلقائي (فائق السرعة)":
    # اختيار عشوائي سريع
    loc_names = list(LOCATIONS_CONFIG.keys())
    name = random.choice(loc_names)
    avg = LOCATIONS_CONFIG[name]["avg"]
    # توليد قيم عالية لمحاكاة الضغط
    val = random.randint(int(avg*0.7), int(avg*1.5))
    add_entry(name, val)
else:
    # الوضع اليدوي (sliders)
    st.info("حرك المنزلقات أدناه لتوليد البيانات:")
    cols = st.columns(4)
    for i, loc_name in enumerate(LOCATIONS_CONFIG.keys()):
        val = cols[i].slider(f"{loc_name.split()[0]}", 0, 800, value=LOCATIONS_CONFIG[loc_name]["avg"], key=loc_name)
        if st.session_state.get(f"prev_{loc_name}") != val:
            add_entry(loc_name, val)
            st.session_state[f"prev_{loc_name}"] = val

# --- 5. منطق العرض (البروتوكول vs الانهيار) ---
with dashboard_placeholder.container():
    if not st.session_state.data_history:
        st.info("بانتظار وصول البيانات...")
    else:
        df = pd.DataFrame(st.session_state.data_history)

        # سيناريو 1: بدون بروتوكول (Chaos)
        if mode == "بدون بروتوكول (خطر الانهيار)":
            st.error("🚨 تحذير: البيانات تتدفق بدون تنظيم (High Congestion)")
            # البيانات تظهر كما وصلت تماماً (فوضى)
            df_display = df.iloc[::-1] # الأحدث فوق لكن بدون ترتيب أهمية
            
            # محاكاة "الانهيار" إذا كانت هناك أكثر من 3 حالات خطر
            danger_count = len(df[df['level'] == 3])
            if danger_count > 4:
                st.markdown("<h2 style='color:red; text-align:center;'>⛔ NETWORK COLLAPSE ⛔</h2>", unsafe_allow_html=True)
                st.warning("النظام غير قادر على فرز الأحمال الحرجة - خطر انقطاع عام!")

        # سيناريو 2: بالبروتوكول الذكي (Priority)
        else:
            st.success("✅ البروتوكول فعال: يتم فرز الأحمال الحرجة وتأمينها")
            # الفرز حسب (الحالة الخطرة أولاً) ثم (أولوية المنشأة)
            df_display = df.sort_values(by=["level", "p"], ascending=[False, False])

        # عرض الرسم البياني (سلس ومتسلسل)
        chart_df = df.pivot_table(index='الوقت', columns='المنشأة', values='التيار (A)').ffill()
        st.line_chart(chart_df, height=300)

        # عرض الجدول بتنسيق احترافي
        def style_rows(row):
            if row['level'] == 3: return ['background-color: #800000; color: white'] * len(row)
            if row['level'] == 2: return ['background-color: #705d00; color: white'] * len(row)
            return [''] * len(row)

        st.dataframe(
            df_display.drop(columns=['level', 'p'], errors='ignore').style.apply(style_rows, axis=1),
            use_container_width=True,
            height=400
        )

# تحديث تلقائي كل 0.5 ثانية في الوضع التلقائي فقط
if input_type == "تلقائي (فائق السرعة)":
    time.sleep(0.5)
    st.rerun()
    
