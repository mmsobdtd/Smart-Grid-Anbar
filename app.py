import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# ==========================================
# 1. الإعدادات الجمالية المتقدمة (Professional Dark Theme)
# ==========================================
st.set_page_config(page_title="Grid Guardian - Al-Anbar", layout="wide")

st.markdown("""
    <style>
    /* تنسيق الخلفية العامة */
    .stApp { background-color: #0b0e14; color: #e0e0e0; }
    
    /* بطاقات الأعمدة والبيوت */
    .grid-node {
        background: linear-gradient(145deg, #161b22, #0d1117);
        border: 1px solid #30363d;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        box-shadow: 5px 5px 15px rgba(0,0,0,0.3);
        margin-bottom: 20px;
    }
    
    /* حالة التجاوز (النبض الأحمر) */
    .theft-alert {
        border: 2px solid #ff4b4b;
        box-shadow: 0 0 20px rgba(255, 75, 75, 0.4);
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0px rgba(255, 75, 75, 0.7); }
        70% { box-shadow: 0 0 0 15px rgba(255, 75, 75, 0); }
        100% { box-shadow: 0 0 0 0px rgba(255, 75, 75, 0); }
    }

    /* العناوين */
    h1, h2, h3 { color: #58a6ff !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    
    /* المقاييس (Metrics) */
    [data-testid="stMetricValue"] { color: #39d353 !important; font-size: 28px !important; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. المنطق الهندسي (Engineering Engine)
# ==========================================

# ثوابت هندسية
V_SOURCE = 225.0  # جهد مخرج المحولة
R_PER_METER = 0.0005  # مقاومة السلك (Ohm/m)
PRICE_PER_KWH = 50  # السعر الافتراضي للكهرباء في العراق

def calculate_grid_physics(distance, total_current, theft_current=0):
    # حساب هبوط الجهد: V_drop = I * R
    total_i = total_current + theft_current
    v_drop = total_i * (R_PER_METER * distance)
    v_actual = V_SOURCE - v_drop
    
    # حساب القدرة الضائعة (Losses)
    p_loss_kw = (v_actual * theft_current * 0.9) / 1000 if theft_current > 0 else 0
    return round(v_actual, 2), round(p_loss_kw, 3)

# ==========================================
# 3. إدارة واجهة المستخدم
# ==========================================

st.markdown("<h1 style='text-align: center;'>⚡ منظومة الأنبار الذكية لإدارة الأحمال</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #8b949e;'>نظام المراقبة والتشخيص اللحظي - جامعة الأنبار</p>", unsafe_allow_html=True)

# القائمة الجانبية (لوحة التحكم السريعة)
with st.sidebar:
    st.image("https://img.icons8.com/nolan/128/electricity.png", width=100)
    st.header("🎮 تحكم المحاكاة")
    
    st.subheader("⚠️ حقن تجاوز")
    theft_mode = st.selectbox("موقع التجاوز المراد فحصه:", 
                              ["سليم ✅", "مقطع A (قرب المحولة)", "مقطع B (منتصف الشارع)", "مقطع C (نهاية الشارع)"])
    
    theft_val = 0
    if theft_mode != "سليم ✅":
        theft_val = st.slider("قوة التجاوز (أمبير):", 10, 150, 60)
        
    st.divider()
    if st.button("♻️ إعادة ضبط الشبكة"):
        st.rerun()

# --- الحسابات المالية والهندسية ---
legal_load = 95.0
v_final, p_loss = calculate_grid_physics(250, legal_load, theft_val)
hourly_cost = p_loss * PRICE_PER_KWH

# الصف الأول: المقاييس الحيوية
st.divider()
m1, m2, m3, m4 = st.columns(4)
m1.metric("جهد الشبكة النهائي", f"{v_final} V", delta=f"{v_final-220:.1f}V")
m2.metric("الحمل الكلي المجهز", f"{legal_load + theft_val} A")
m3.metric("القدرة المسروقة", f"{p_loss} kW")
m4.metric("خسارة الساعة", f"{int(hourly_cost)} IQD")

# الصف الثاني: التمثيل المرئي (الشارع الذكي)
st.divider()
st.subheader("📍 خارطة التدفق اللحظية (The Smart Street)")

c1, c2, c3, c4 = st.columns(4)

def draw_node(col, title, subtitle, icon, is_theft=False):
    css_class = "grid-node theft-alert" if is_theft else "grid-node"
    col.markdown(f"""
        <div class='{css_class}'>
            <div style='font-size: 40px;'>{icon}</div>
            <div style='font-size: 20px; font-weight: bold; margin-top:10px;'>{title}</div>
            <div style='font-size: 14px; color: #8b949e;'>{subtitle}</div>
        </div>
        """, unsafe_allow_html=True)

with c1:
    draw_node(c1, "المحولة", "محطة الرمادي (01)", "🏢")
    st.write("---")

with c2:
    is_hit = (theft_mode == "مقطع A (قرب المحولة)")
    draw_node(c2, "نقطة توزيع 1", "زقاق المستودع", "🗼", is_hit)
    if is_hit: st.error("🚨 تجاوز مكتشف هنا!")
    st.write("---")

with c3:
    is_hit = (theft_mode == "مقطع B (منتصف الشارع)")
    draw_node(c3, "نقطة توزيع 2", "قرب المسجد", "🗼", is_hit)
    if is_hit: st.error("🚨 تجاوز مكتشف هنا!")
    st.write("---")

with c4:
    is_hit = (theft_mode == "مقطع C (نهاية الشارع)")
    draw_node(c4, "نقطة توزيع 3", "نهاية الخط", "🗼", is_hit)
    if is_hit: st.error("🚨 تجاوز مكتشف هنا!")

# الصف الثالث: التحليل الهندسي (للتقديم للدكتور)
st.divider()
tab_math, tab_analysis = st.tabs(["📐 الصيغ الرياضية", "📊 تحليل كفاءة المقطع"])

with tab_math:
    st.markdown("### المعادلات المستخدمة في حسابات المنظومة")
    st.latex(r"V_{actual} = V_{source} - (I_{total} \times R_{line} \times L)")
    st.info("حيث أن $L$ هي المسافة بالمتر، و $R_{line}$ هي المقاومة النوعية للسلك.")
    st.latex(r"Losses_{IQD} = \frac{V \times I_{theft} \times PF \times \Delta t}{1000} \times Price")

with tab_analysis:
    st.subheader("تقرير جودة الطاقة")
    efficiency = (legal_load / (legal_load + theft_val)) * 100
    st.progress(efficiency/100, text=f"كفاءة الشبكة الحالية: {int(efficiency)}%")
    if efficiency < 70:
        st.warning("⚠️ كفاءة الشبكة متدنية جداً بسبب التجاوزات، خطر احتراق الأسلاك مرتفع.")
    else:
        st.success("✅ جودة النقل ضمن المعايير الهندسية المقبولة.")

# تذييل الصفحة
st.markdown("<br><hr><center>إعداد الطالب: محمد نبيل | جامعة الأنبار - كلية الهندسة - قسم الكهرباء | 2026</center>", unsafe_allow_html=True)
