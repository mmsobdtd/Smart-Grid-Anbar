import streamlit as st
import pandas as pd
import numpy as np

# --- 1. الإعدادات الجمالية الهندسية ---
st.set_page_config(page_title="Impact Analysis - Al-Anbar Grid", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    .compare-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .diff-text { color: #ff7b72; font-weight: bold; }
    .normal-text { color: #3fb950; font-weight: bold; }
    h1, h2 { color: #58a6ff !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. الثوابت والمحرك الهندسي ---
V_SOURCE = 225.0
R_LINE = 0.08  # المقاومة الكلية للخط (أوم)
LEGAL_I = 80.0 # الحمل القانوني الثابت (أمبير)

def get_grid_metrics(theft_i):
    total_i = LEGAL_I + theft_i
    v_drop = total_i * R_LINE
    v_actual = V_SOURCE - v_drop
    p_loss_kw = (v_actual * theft_i * 0.9) / 1000 if theft_i > 0 else 0
    efficiency = (LEGAL_I / total_i) * 100 if total_i > 0 else 100
    return round(v_actual, 1), round(total_i, 1), round(p_loss_kw, 2), round(efficiency, 1)

# --- 3. واجهة المستخدم ---
st.markdown("<h1 style='text-align: center;'>⚡ لوحة تحليل أثر التجاوزات اللحظي</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>مقارنة البيانات الهندسية قبل وبعد حقن التجاوز</p>", unsafe_allow_html=True)

# القائمة الجانبية للتحكم
with st.sidebar:
    st.header("⚙️ محاكاة الأعطال")
    theft_val = st.slider("قيمة التجاوز المحقون (أمبير):", 0, 100, 50)
    st.divider()
    st.info("💡 يتم الآن مقارنة حالة الشبكة مع وبدون هذا الحمل غير القانوني.")

# حساب البيانات للحالتين
v_norm, i_norm, p_norm, eff_norm = get_grid_metrics(0)      # قبل (طبيعي)
v_curr, i_curr, p_curr, eff_curr = get_grid_metrics(theft_val) # بعد (تجاوز)

# --- 4. عرض المقارنة (الجدول والتحليل) ---

st.subheader("📊 جدول المقارنة الفنية")

# بناء جدول البيانات للمقارنة
comparison_data = {
    "المقياس الهندسي": ["الجهد النهائي (V)", "التيار الكلي (A)", "القدرة الضائعة (kW)", "كفاءة النقل (%)", "التكلفة المالية (IQD/h)"],
    "الحالة الطبيعية ✅": [v_norm, i_norm, p_norm, f"{eff_norm}%", "0"],
    "الحالة الحالية ⚠️": [v_curr, i_curr, p_curr, f"{eff_curr}%", f"{int(p_curr * 50)}"],
    "الفارق / الأثر": [
        f"{round(v_curr - v_norm, 1)} V",
        f"+{round(i_curr - i_norm, 1)} A",
        f"+{round(p_curr - p_norm, 2)} kW",
        f"{round(eff_curr - eff_norm, 1)}%",
        f"+{int(p_curr * 50)} دينار"
    ]
}

df_comp = pd.DataFrame(comparison_data)
st.table(df_comp)

st.divider()

# --- 5. التحليل البصري (قبل وبعد) ---
st.subheader("📉 التمثيل المرئي للأثر الهندي")
col1, col2 = st.columns(2)

with col1:
    st.markdown("<div class='compare-card'>", unsafe_allow_html=True)
    st.markdown("### الحالة المستقرة (قبل)")
    st.write("الشبكة تعمل ضمن الحدود المسموحة.")
    st.metric("V-Stable", f"{v_norm} V")
    st.metric("Efficiency", f"{eff_norm}%")
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='compare-card'>", unsafe_allow_html=True)
    st.markdown("### الحالة المتأثرة (بعد)")
    st.write("انهيار في الجهد وزيادة في الفواقد.")
    st.metric("V-Current", f"{v_curr} V", delta=f"{round(v_curr - v_norm, 1)}V", delta_color="inverse")
    st.metric("Losses", f"{p_curr} kW", delta=f"+{p_curr}kW", delta_color="inverse")
    st.markdown("</div>", unsafe_allow_html=True)

# --- 6. التفسير الهندسي للدكتور ---
st.divider()
with st.expander("📝 التقرير التحليلي للمناقشة"):
    st.markdown(f"""
    عند حقن تجاوز بقيمة **{theft_val} أمبير**، تم ملاحظة الآتي:
    1. **هبوط الجهد:** انخفض الجهد من {v_norm}V إلى {v_curr}V نتيجة زيادة التيار المار في مقاومة الخط.
    2. **الخسائر النحاسية:** زادت القدرة المبددة بشكل غير قانوني بمقدار **{p_curr} kW**.
    3. **الكفاءة:** تراجعت كفاءة النقل بنسبة **{abs(round(eff_curr - eff_norm, 1))}%**.
    
    **المعادلة الحاكمة:**
    """)
    st.latex(r"V_{drop} = (I_{legal} + I_{theft}) \times R_{line}")
    
