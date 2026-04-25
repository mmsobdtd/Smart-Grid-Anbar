import streamlit as st
import pandas as pd
import numpy as np

# --- 1. إعدادات الصفحة والتنسيق الهندي الداكن ---
st.set_page_config(page_title="Al-Anbar Smart Grid - Expert", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    .node-card {
        background: linear-gradient(145deg, #161b22, #0d1117);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    }
    .theft-node {
        border: 2px solid #ff4b4b;
        box-shadow: 0 0 20px rgba(255, 75, 75, 0.3);
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.02); }
        100% { transform: scale(1); }
    }
    .metric-label { font-size: 14px; color: #8b949e; }
    .metric-value { font-size: 24px; font-weight: bold; color: #58a6ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. لوحة التحكم المتقدمة (Sidebar Controls) ---
with st.sidebar:
    st.header("⚙️ إعدادات الشبكة الدقيقة")
    st.markdown("### **البارامترات الهندسية**")
    
    # تحكمات دقيقة جداً
    v_source = st.slider("جهد المصدر (V_Source)", 210.0, 240.0, 225.0, 0.5)
    pf_target = st.slider("معامل القدرة (Power Factor)", 0.70, 0.99, 0.92, 0.01)
    wire_res = st.slider("مقاومة السلك (Ohm/km)", 0.1, 1.0, 0.4, 0.05)
    ambient_temp = st.slider("درجة حرارة الجو (°C)", 10, 55, 42)
    
    st.divider()
    st.subheader("⚠️ محاكاة التجاوز")
    theft_loc = st.selectbox("موقع التجاوز اللحظي:", 
                             ["سليم ✅", "مقطع 1 (قرب المحولة)", "مقطع 2 (وسط الشارع)", "مقطع 3 (نهاية الخط)"])
    
    theft_i = 0
    if theft_loc != "سليم ✅":
        theft_i = st.slider("تيار التجاوز (Amps):", 5, 120, 55)

    if st.button("♻️ إعادة ضبط المنظومة", use_container_width=True):
        st.rerun()

# --- 3. المحرك الفيزيائي (Power Physics Engine) ---
# حسابات الحمل القانوني (Legal Load)
legal_i_total = 88.5  # أمبير مسجل في العدادات
total_i_actual = legal_i_total + theft_i

# حساب هبوط الجهد بناءً على المقاومة (Ohm's Law)
# هبوط الجهد التراكمي = التيار × المقاومة
total_resistance = (wire_res / 1000) * 300  # لشارع طوله 300 متر
v_drop = total_i_actual * total_resistance
v_final = v_source - v_drop

# حساب القدرات (Active, Reactive, Apparent)
# S = V * I, P = S * cos(phi), Q = S * sin(phi)
s_apparent = (v_final * total_i_actual) / 1000  # kVA
p_active = s_apparent * pf_target  # kW
phi = np.arccos(pf_target)
q_reactive = s_apparent * np.sin(phi)  # kVAR

# الخسائر المالية
iqd_price = 50  # دينار لكل كيلو واط ساعة
theft_power_kw = (v_final * theft_i * pf_target) / 1000 if theft_i > 0 else 0
hourly_loss_iqd = theft_power_kw * iqd_price

# --- 4. واجهة العرض والتبويبات ---
st.markdown(f"<h1 style='text-align: center;'>⚡ مراقب شبكة الأنبار الذكي - v5.0</h1>", unsafe_allow_html=True)

tab_map, tab_comparison, tab_math = st.tabs(["📍 خارطة الشارع", "📊 تحليل الفوارق", "📚 المعادلات الرياضية"])

with tab_map:
    # المقاييس الحيوية العلوية
    st.markdown("### 📡 قراءات السكادا اللحظية")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("الجهد النهائي", f"{v_final:.1f} V", delta=f"{v_final - v_source:.1f}V")
    c2.metric("القدرة الفعالة (P)", f"{p_active:.1f} kW")
    c3.metric("التردد", "50.02 Hz", help="التردد الوطني المستقر")
    c4.metric("الحمل الإجمالي", f"{total_i_actual:.1f} A")

    st.divider()
    
    # تمثيل الشارع مرئياً
    st.subheader("🗺️ تمثيل عقد التوزيع والأعمدة")
    street_cols = st.columns(4)
    
    nodes = [
        {"name": "المحولة", "sub": "محطة التوزيع", "icon": "🏢", "hit": False},
        {"name": "عامود 1", "sub": "زقاق 1", "icon": "🗼", "hit": (theft_loc == "مقطع 1 (قرب المحولة)")},
        {"name": "عامود 2", "sub": "زقاق 2", "icon": "🗼", "hit": (theft_loc == "مقطع 2 (وسط الشارع)")},
        {"name": "عامود 3", "sub": "زقاق 3", "icon": "🗼", "hit": (theft_loc == "مقطع 3 (نهاية الخط)")}
    ]
    
    for i, node in enumerate(nodes):
        with street_cols[i]:
            card_class = "node-card theft-node" if node['hit'] else "node-card"
            st.markdown(f"""
                <div class="{card_class}">
                    <div style="font-size: 40px;">{node['icon']}</div>
                    <div style="font-weight: bold; margin-top:10px;">{node['name']}</div>
                    <div style="font-size: 12px; color: #8b949e;">{node['sub']}</div>
                </div>
            """, unsafe_allow_html=True)
            if node['hit']:
                st.error("🚨 تجاوز مكتشف!")

with tab_comparison:
    st.subheader("⚖️ تحليل الأثر: قبل وبعد التجاوز")
    
    # بيانات المقارنة
    comp_data = {
        "المؤشر الهندسي": ["التيار الكلي (A)", "الفولتية (V)", "الفواقد (kW)", "الخسارة (IQD/h)"],
        "الحالة الطبيعية": [legal_i_total, v_source - (legal_i_total * total_resistance), 0, 0],
        "الحالة الحالية": [total_i_actual, v_final, round(theft_power_kw, 2), int(hourly_loss_iqd)]
    }
    df_comp = pd.DataFrame(comp_data)
    st.table(df_comp)
    
    # تنبيهات ذكية
    if theft_i > 0:
        st.warning(f"⚠️ ملاحظة فنية: زيادة الحمل بمقدار {theft_i}A أدت إلى هبوط إضافي في الجهد قدره {round(v_source - v_final, 1)} فولت.")

with tab_math:
    st.subheader("📐 النموذج الرياضي للشبكة")
    st.markdown("يقوم النظام بحساب هبوط الجهد والقدرة باستخدام المعادلات التالية:")
    
    st.latex(r"V_{drop} = I_{total} \times (R_{wire} \times Length)")
    st.latex(r"P_{kW} = \frac{V \times I \times \cos(\phi)}{1000}")
    st.latex(r"Q_{kVAR} = \sqrt{S^2 - P^2}")
    
    st.info(f"المتغيرات الحالية: معامل القدرة $\cos(\phi)$ = {pf_target} | المقاومة الكلية = {round(total_resistance, 3)} $\Omega$")

# التذييل
st.divider()
st.markdown("<center>إعداد الطالب: محمد نبيل | كلية الهندسة - جامعة الأنبار | نظام مراقبة ذكي 2026</center>", unsafe_allow_html=True)
            
