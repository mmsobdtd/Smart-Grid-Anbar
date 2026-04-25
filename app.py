import streamlit as st
import pandas as pd
import numpy as np

# --- 1. إعدادات الصفحة والتنسيق الأبيض النظيف ---
st.set_page_config(page_title="Al-Anbar Smart Grid - Full View", layout="wide")

st.markdown("""
    <style>
    /* خلفية بيضاء ونصوص واضحة */
    .stApp { background-color: #ffffff; color: #1a1a1a; }
    
    /* بطاقات العقد والأعمدة */
    .node-box {
        background: #f8f9fa;
        border: 2px solid #e9ecef;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.05);
    }
    
    /* تنبيه التجاوز الأحمر */
    .theft-warning {
        border: 2px solid #dc3545;
        background-color: #fff5f5;
        animation: blink 1.5s infinite;
    }
    @keyframes blink { 50% { border-color: transparent; } }

    /* الأزرار الاحترافية */
    .stButton>button {
        background-color: #ffffff;
        color: #007bff;
        border: 1px solid #007bff;
        border-radius: 5px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #007bff;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. المحرك الهندسي (Engineering Logic) ---
V_SOURCE = 226.550 # فولتية المصدر بدقة
R_LINE = 0.325     # مقاومة السلك الكلية (أوم)
LEGAL_I = 92.440   # الاستهلاك الشرعي الثابت (أمبير)

def calculate_grid_metrics(theft_i):
    total_i = LEGAL_I + theft_i
    v_drop = total_i * R_LINE
    v_actual = V_SOURCE - v_drop
    # القدرة المفقودة كلياً (P = V * I * PF)
    p_loss_kw = (v_actual * theft_i * 0.91) / 1000 if theft_i > 0 else 0
    efficiency = (LEGAL_I / total_i) * 100 if total_i > 0 else 100
    return round(v_actual, 3), round(total_i, 3), round(p_loss_kw, 3), round(efficiency, 1)

# --- 3. واجهة المستخدم (السيطرة والبيانات) ---

st.title("⚡ منظومة رصد وتتبع أحمال الأنبار الذكية")
st.markdown(f"**إعداد الطالب:** محمد نبيل | **الجامعة:** جامعة الأنبار - كلية الهندسة")

# القائمة الجانبية الموحدة
with st.sidebar:
    st.header("⚙️ السيطرة على المحاكاة")
    if st.button("🔄 تحديث قراءات IoT", use_container_width=True):
        st.toast("جاري سحب البيانات...")
    
    st.divider()
    theft_loc = st.selectbox("موقع التجاوز (للفحص):", 
                             ["سليم ✅", "عقدة A (زقاق 1)", "عقدة B (زقاق 2)", "عقدة C (زقاق 3)"])
    
    theft_val = 0
    if theft_loc != "سليم ✅":
        theft_val = st.slider("تيار التجاوز (A):", 0.0, 150.0, 65.5, 0.5)
        
    st.divider()
    if st.button("🚨 تصفير (Reset)", use_container_width=True):
        st.rerun()

# حسابات الحالة الحالية
v_act, i_act, p_loss, eff = calculate_grid_metrics(theft_val)
v_norm, i_norm, _, _ = calculate_grid_metrics(0) # القيمة الطبيعية للمقارنة

# --- 4. عرض المقاييس (Dashboard) ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("الجهد النهائي", f"{v_act} V", f"{round(v_act - v_norm, 2)} V")
col2.metric("الحمل الإجمالي", f"{i_act} A", f"+{round(i_act - i_norm, 2)} A")
col3.metric("القدرة المسروقة", f"{p_loss} kW")
col4.metric("كفاءة النقل", f"{eff}%")

st.divider()

# --- 5. تمثيل الشارع (Street Simulation) ---
st.subheader("📍 الخارطة المرئية لخط التوزيع (Live Stream)")
street_cols = st.columns(4)

nodes = [
    {"name": "المحولة 01", "sub": "محطة المستودع", "icon": "🏢", "hit": False},
    {"name": "عقدة A", "sub": "زقاق 1", "icon": "🗼", "hit": (theft_loc == "عقدة A (زقاق 1)")},
    {"name": "عقدة B", "sub": "زقاق 2", "icon": "🗼", "hit": (theft_loc == "عقدة B (زقاق 2)")},
    {"name": "عقدة C", "sub": "زقاق 3", "icon": "🗼", "hit": (theft_loc == "عقدة C (زقاق 3)")}
]

for i, node in enumerate(nodes):
    with street_cols[i]:
        style = "node-box theft-warning" if node["hit"] else "node-box"
        st.markdown(f"""
            <div class='{style}'>
                <div style='font-size: 35px;'>{node['icon']}</div>
                <div style='font-weight: bold; margin-top:10px;'>{node['name']}</div>
                <div style='font-size: 12px; color: #6c757d;'>{node['sub']}</div>
            </div>
            """, unsafe_allow_html=True)
        if node["hit"]:
            st.error("🚨 اكتشاف تجاوز!")

st.divider()

# --- 6. التقارير والتحليل الرياضي (كل شيء في صفحة واحدة) ---
rep_col, math_col = st.columns([1.2, 1])

with rep_col:
    st.subheader("📋 التقرير الفني المباشر")
    st.write(f"المحولة مجهزة بـ: **{i_act} أمبير**.")
    st.write(f"مجموع عدادات البيوت (الشرعية): **{LEGAL_I} أمبير**.")
    diff = round(i_act - LEGAL_I, 3)
    if diff > 1.0:
        st.error(f"⚠️ يوجد فاقد غير مفسر بقيمة **{diff} أمبير** في {theft_loc}.")
        st.write(f"الخسارة المالية التقديرية: **{int(p_loss * 50)} دينار/ساعة**.")
    else:
        st.success("✅ حالة الشبكة مستقرة وضمن حدود الفاقد الفني المسموح.")

with math_col:
    st.subheader("📐 النموذج الرياضي")
    st.latex(r"V_{drop} = (I_{legal} + I_{theft}) \cdot R_{wire}")
    st.latex(r"P_{loss} = \frac{V_{actual} \cdot I_{theft} \cdot \cos(\phi)}{1000}")
    st.caption("ملاحظة: تم حساب النتائج بدقة 3 فواصل عشرية لمحاكاة الحساسات الصناعية.")

st.divider()
st.markdown("<center>إعداد الطالب: محمد نبيل | جامعة الأنبار - قسم الكهرباء | 2026</center>", unsafe_allow_html=True)
