import streamlit as st
import pandas as pd
import numpy as np

# --- 1. إعدادات الهوية البصرية (Professional Design) ---
st.set_page_config(page_title="Al-Anbar Smart Grid Elite", layout="wide")

st.markdown("""
    <style>
    /* تنسيق الخلفية والخطوط */
    .stApp { background-color: #050b14; color: #d1d5db; }
    
    /* بطاقات الأجهزة (Nodes) */
    .node-box {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        transition: 0.3s;
    }
    .node-box:hover { border-color: #3b82f6; }
    
    /* تنبيه التجاوز */
    .theft-active {
        border: 2px solid #ef4444;
        background: #1a1010;
        box-shadow: 0 0 15px rgba(239, 68, 68, 0.2);
    }

    /* تنسيق الأزرار الاحترافي */
    .stButton>button {
        background-color: #1f2937;
        color: #3b82f6;
        border: 1px solid #3b82f6;
        border-radius: 5px;
        font-weight: bold;
        height: 45px;
    }
    .stButton>button:hover {
        background-color: #3b82f6;
        color: white;
    }

    /* العناوين والمقاييس */
    h1, h2, h3 { color: #f3f4f6 !important; }
    [data-testid="stMetricValue"] { color: #60a5fa !important; font-family: 'Courier New', monospace; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. المحرك الهندسي (Engineering Engine) ---
# ثوابت لا تتغير لضمان الدقة
V_SOURCE = 226.550 # جهد مخرج المحولة بدقة عالية
R_LINE = 0.325     # مقاومة الخط الكلية (أوم)
LEGAL_I = 92.440   # تيار الاستهلاك الشرعي (أمبير)

def calculate_grid(theft_i):
    total_i = LEGAL_I + theft_i
    v_drop = total_i * R_LINE
    v_final = V_SOURCE - v_drop
    
    # حساب القدرة (P = V * I * PF) - معامل القدرة الافتراضي 0.91
    p_legal_kw = (v_final * LEGAL_I * 0.91) / 1000
    p_theft_kw = (v_final * theft_i * 0.91) / 1000 if theft_i > 0 else 0
    
    return round(v_final, 3), round(total_i, 3), round(p_theft_kw, 3)

# --- 3. واجهة التحكم والعرض ---

st.markdown("<h1 style='text-align: center;'>⚡ منظومة رصد وتتبع أحمال الأنبار الذكية</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#9ca3af;'>نظام السيطرة والتشخيص الهندسي - الإصدار الاحترافي 2026</p>", unsafe_allow_html=True)

# القائمة الجانبية: التحكم بالأهم فقط
with st.sidebar:
    st.header("🎮 وحدة التحكم")
    if st.button("🔄 سحب قراءات IoT", use_container_width=True):
        st.toast("تم تحديث البيانات من العقد بنجاح")
    
    st.divider()
    st.subheader("⚠️ سيناريو التجاوز")
    theft_loc = st.selectbox("موقع التجاوز (للفحص):", 
                             ["سليم ✅", "زقاق 1 (عقدة A)", "زقاق 2 (عقدة B)", "زقاق 3 (عقدة C)"])
    
    theft_val = 0
    if theft_loc != "سليم ✅":
        theft_val = st.slider("تيار التجاوز (A):", 0.0, 120.0, 65.5, 0.5)
        
    st.divider()
    if st.button("🚨 تصفير (Emergency Reset)", use_container_width=True):
        st.rerun()

# حسابات الحالة
v_actual, i_actual, p_loss = calculate_grid(theft_val)

# --- الصف الأول: لوحة القياس (Dashboard) ---
st.divider()
col1, col2, col3, col4 = st.columns(4)
col1.metric("الجهد النهائي", f"{v_actual} V", f"{round(v_actual - 220, 2)}V")
col2.metric("الحمل الإجمالي", f"{i_actual} A")
col3.metric("القدرة المسروقة", f"{p_loss} kW")
col4.metric("خسارة الساعة", f"{int(p_loss * 50)} IQD")

# --- الصف الثاني: التمثيل المرئي للشارع ---
st.divider()
st.subheader("🏙️ المراقبة المكانية لخط التوزيع")

street_cols = st.columns(4)

nodes = [
    {"name": "المحولة 01", "sub": "محطة المستودع", "icon": "🏢", "is_hit": False},
    {"name": "عقدة A", "sub": "زقاق 1", "icon": "🗼", "is_hit": (theft_loc == "زقاق 1 (عقدة A)")},
    {"name": "عقدة B", "sub": "زقاق 2", "icon": "🗼", "is_hit": (theft_loc == "زقاق 2 (عقدة B)")},
    {"name": "عقدة C", "sub": "زقاق 3", "icon": "🗼", "is_hit": (theft_loc == "زقاق 3 (عقدة C)")}
]

for i, node in enumerate(nodes):
    with street_cols[i]:
        style = "node-box theft-active" if node["is_hit"] else "node-box"
        st.markdown(f"""
            <div class='{style}'>
                <div style='font-size: 35px;'>{node['icon']}</div>
                <div style='font-weight: bold; margin-top:10px; color:#f3f4f6;'>{node['name']}</div>
                <div style='font-size: 12px; color: #9ca3af;'>{node['sub']}</div>
            </div>
            """, unsafe_allow_html=True)
        if node["is_hit"]:
            st.error("🚨 سرقة مكتشفة!")

# --- الصف الثالث: التقارير الهندسية (للدكتور) ---
st.divider()
tab_report, tab_math = st.tabs(["📋 التقرير الفني", "📐 التحليل الرياضي"])

with tab_report:
    st.subheader("تحليل جودة الطاقة (Power Quality)")
    eff = (LEGAL_I / i_actual) * 100
    st.progress(eff/100, text=f"كفاءة الشبكة الحالية: {round(eff, 1)}%")
    
    c_a, c_b = st.columns(2)
    with c_a:
        st.info(f"**الحالة:** {'تجاوز مكتشف' if theft_val > 0 else 'مستقرة'}")
        st.write(f"المحولة مجهزة بـ: {i_actual} أمبير.")
    with c_b:
        st.write(f"مجموع العدادات المسجل: {LEGAL_I} أمبير.")
        st.write(f"الفارق (الضياعات): {round(i_actual - LEGAL_I, 3)} أمبير.")

with tab_math:
    st.markdown("### المعادلات الحاكمة للنظام")
    st.latex(r"V_{load} = V_{source} - (I_{legal} + I_{theft}) \cdot R_{line}")
    st.latex(r"P_{loss} = \frac{V_{load} \cdot I_{theft} \cdot \cos(\phi)}{1000}")
    st.info("تم استخدام معامل قدرة ثابت $\cos(\phi) = 0.91$ ومقاومة خط ثابتة $R = 0.325 \Omega$ للحصول على نتائج دقيقة.")

# تذييل الصفحة
st.markdown("<br><hr><center>محمد نبيل - جامعة الأنبار - قسم الهندسة الكهربائية - 2026</center>", unsafe_allow_html=True)
