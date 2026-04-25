import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime

# --- 1. الإعدادات الجمالية (White Professional Theme) ---
st.set_page_config(page_title="Al-Anbar Grid SCADA", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #212529; }
    .main-header { text-align: center; color: #1e3a8a; font-weight: bold; margin-bottom: 5px; }
    .sub-header { text-align: center; color: #495057; font-size: 18px; margin-bottom: 20px; }
    .node-box {
        background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 12px;
        padding: 10px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .theft-active { border: 2px solid #e03131 !important; background-color: #fff5f5 !important; }
    .wire-line { height: 5px; background: #dee2e6; margin-top: 45px; }
    .wire-alert { background: #e03131 !important; box-shadow: 0 0 8px #e03131; }
    .financial-card {
        background: #f1f3f5; padding: 15px; border-radius: 10px;
        border-right: 5px solid #228be6; text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. الثوابت الهندسية وقيم التجاوز الواقعية ---
THEFT_MAP = {1: 4.150, 2: 8.320, 3: 11.450, 4: 15.600}
LEGAL_LOAD_BASE = 108.40  # kW
IQD_RATE = 50             # 50 دينار لكل كيلو واط ساعة

if 'msg_history' not in st.session_state: st.session_state.msg_history = []

# --- 3. تصميم الهيكل الثابت للواجهة ---
st.markdown("<h1 class='main-header'>⚡ نظام الرصد الآلي للشبكة الذكية - محافظة الأنبار</h1>", unsafe_allow_html=True)
st.markdown("<div class='sub-header'>إعداد الطلبة: محمد نبيل بردان | مشتاق طالب جلال</div>", unsafe_allow_html=True)
st.markdown("<center>جامعة الأنبار - كلية الهندسة - قسم الكهرباء</center>", unsafe_allow_html=True)
st.divider()

# القائمة الجانبية (Sidebar) للتحكم
with st.sidebar:
    st.header("🎮 وحدة حقن التجاوز")
    st.write("قم بتفعيل المواقع لمحاكاة السرقة:")
    t1 = st.toggle("تجاوز عامود 1 (بين بيت 1 و 2)", key="t1")
    t2 = st.toggle("تجاوز عامود 2 (بين بيت 2 و 3)", key="t2")
    t3 = st.toggle("تجاوز عامود 3 (بين بيت 3 و 4)", key="t3")
    t4 = st.toggle("تجاوز عامود 4 (بين بيت 4 و 5)", key="t4")
    
    st.divider()
    if st.button("🗑️ مسح سجل البلاغات"):
        st.session_state.msg_history = []

# إنشاء الحاويات الديناميكية للتحديث بدون وميض
metrics_area = st.empty()
map_area = st.empty()
report_area = st.empty()

# --- 4. حلقة التحديث والحسابات اللحظية ---
# ملاحظة: الحلقة تعمل بذكاء لتحديث البيانات فور تغيير أي Switch
while True:
    # جمع التجاوزات النشطة
    active_indices = []
    if t1: active_indices.append(1)
    if t2: active_indices.append(2)
    if t3: active_indices.append(3)
    if t4: active_indices.append(4)
    
    # الحسابات الهندسية الدقيقة
    total_theft_kw = sum([THEFT_MAP[i] for i in active_indices])
    # إضافة تذبذب بسيط (0.1%) لمحاكاة الواقع في الأحمال القانونية
    current_legal = LEGAL_LOAD_BASE + np.random.uniform(-0.1, 0.1)
    transformer_out = current_legal + total_theft_kw + (current_legal * 0.02) # فواقد تقنية 2%
    
    # الحسابات المالية بالدينار
    loss_h = int(total_theft_kw * IQD_RATE)
    loss_d = loss_h * 24
    loss_m = loss_d * 30

    # أ. تحديث المقاييس (Metrics)
    with metrics_area.container():
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("قدرة المحولة الكلية", f"{transformer_out:.2f} kW")
        m2.metric("القدرة المسروقة حالياً", f"{total_theft_kw:.2f} kW", 
                  delta=f"{len(active_indices)} مواقع" if len(active_indices)>0 else None, delta_color="inverse")
        m3.metric("خسارة اليوم (IQD)", f"{loss_d:,}")
        m4.metric("خسارة الشهر (IQD)", f"{loss_m:,}")
        st.divider()

    # ب. تحديث خارطة الشارع (Visual Map)
    with map_area.container():
        st.subheader("📍 خارطة المسار الكهربائي وتحديد المواقع")
        map_cols = st.columns([1.2, 0.5, 1, 0.5, 1, 0.5, 1, 0.5, 1])
        
        # مخرج المحولة
        map_cols[0].markdown("<div class='node-box'>🏢<br><b>المحولة 01</b></div>", unsafe_allow_html=True)
        
        for i in range(1, 5):
            is_active = i in active_indices
            # تمثيل السلك الكهربائي
            map_cols[2*i-1].markdown(f"<div class='wire-line {'wire-alert' if is_active else ''}'></div>", unsafe_allow_html=True)
            # تمثيل العمود
            style = "node-box theft-active" if is_active else "node-box"
            map_cols[2*i].markdown(f"""
                <div class='{style}'>
                    <div style='font-size: 30px;'>🗼</div>
                    <b>عـامود {i}</b><br>
                    <small>بين {i} و {i+1}</small>
                </div>
            """, unsafe_allow_html=True)
        st.divider()

    # ج. تحديث البلاغ والتحليل المالي (Automation)
    with report_area.container():
        c_left, c_right = st.columns([1, 1])
        with c_left:
            st.markdown(f"""
            <div class='financial-card'>
                <b>تكلفة الهدر المالي اللحظي:</b><br>
                <span style='font-size: 26px; color: #e03131; font-weight: bold;'>{loss_h:,} دينار / ساعة</span>
            </div>
            """, unsafe_allow_html=True)
        
        with c_right:
            if len(active_indices) > 0:
                # محاكاة ذكية للتبليغ التلقائي
                with st.status("🔍 جاري تحليل التجاوز المكتشف...", expanded=False) as status:
                    time.sleep(1) # محاكاة معالجة البيانات
                    status.update(label="✅ تم إرسال البلاغ للمهندس المقيم!", state="complete")
                
                # إضافة للسجل التاريخي
                t_str = datetime.now().strftime("%H:%M:%S")
                report_entry = f"[{t_now if 't_now' in locals() else t_str}] تجاوز بقيمة {total_theft_kw:.2f}kW في {[f'عامود {i}' for i in active_indices]}"
                if not st.session_state.msg_history or report_entry.split(']')[1] != st.session_state.msg_history[0].split(']')[1]:
                    st.session_state.msg_history.insert(0, report_entry)
            else:
                st.success("🛡️ نظام المراقبة: الشبكة مستقرة وآمنة.")
        
        with st.expander("📂 سجل الرسائل الصادرة للمهندس"):
            for m in st.session_state.msg_history[:5]: st.write(f"🔹 {m}")

    # التحكم في سرعة التحديث لضمان استقرار الجهاز (Windows 7)
    time.sleep(1)
    
