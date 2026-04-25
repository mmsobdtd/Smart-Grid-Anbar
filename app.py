import streamlit as st
import pandas as pd
import numpy as np
import time

# إعدادات الصفحة
st.set_page_config(page_title="Al-Anbar Smart Grid - Enterprise Edition", layout="wide")

# --- 1. تحسين الواجهة باستخدام CSS ---
st.markdown("""
    <style>
    .metric-box {
        background-color: #ffffff;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        border-bottom: 5px solid #2e7d32;
    }
    .node-card {
        background-color: #f8f9fa;
        border-radius: 12px;
        padding: 15px;
        text-align: center;
        border: 1px solid #dee2e6;
        transition: 0.3s;
    }
    .theft-active {
        background-color: #fff5f5;
        border: 2px solid #e03131;
        box-shadow: 0 0 15px rgba(224, 49, 49, 0.4);
    }
    .alert-log {
        background-color: #212529;
        color: #00ff00;
        padding: 15px;
        border-radius: 5px;
        font-family: 'Courier New', Courier, monospace;
        font-size: 0.9em;
        height: 200px;
        overflow-y: auto;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. تهيئة الذاكرة والسجلات ---
if 'alert_history' not in st.session_state: st.session_state.alert_history = []
if 'total_loss_iqd' not in st.session_state: st.session_state.total_loss_iqd = 0

# --- 3. لوحة التحكم الجانبية (Sidebar) ---
with st.sidebar:
    st.header("🏢 مركز السيطرة والتحكم")
    st.info("نظام مراقبة شبكة توزيع الأنبار - الإصدار 3.0")
    
    if st.button("🔄 سحب بيانات (IoT Live Stream)", type="primary", use_container_width=True):
        st.toast("جاري سحب القراءات من الحساسات...")
        time.sleep(0.5)
    
    st.divider()
    st.subheader("🌡️ الإدارة الحرارية")
    t_temp = st.slider("درجة حرارة المحولة (°C)", 30, 110, 55)
    
    st.subheader("🪝 حقن تجاوز (فحص النظام)")
    theft_loc = st.selectbox("اختر مكان التجاوز:", 
                             ["لا يوجد", "مقطع 1 (بداية الشارع)", "مقطع 2 (وسط الشارع)", "مقطع 3 (نهاية الشارع)"])
    
    st.divider()
    if st.button("🗑️ تصفير السجلات المالية"):
        st.session_state.total_loss_iqd = 0
        st.session_state.alert_history = []
        st.rerun()

# --- 4. المحرك البرمجي (Engineering Engine) ---
# بيانات افتراضية للبيوت
legal_load = 85 # أمبير كلي
theft_val = 55 if theft_loc != "لا يوجد" else 0
v_base = 220 - (15 if theft_val > 0 else 0) # هبوط الجهد عند السرقة

# حساب الخسائر المالية
# فرضية: سعر الأمبير/ساعة = 50 دينار عراقي (لغرض المحاكاة)
hourly_loss = theft_val * 50 
st.session_state.total_loss_iqd += hourly_loss

# --- 5. واجهة العرض الرئيسية ---
st.title("⚡ نظام الأنبار الذكي لإدارة الطاقة")
st.markdown("---")

# الصف الأول: المقاييس الحيوية (Key Metrics)
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("توليد المحولة الفعلي", f"{legal_load + theft_val} A")
with m2:
    st.metric("الحرارة الحالية", f"{t_temp} °C", delta="-5°C" if t_temp < 70 else "+15°C", delta_color="inverse")
with m3:
    st.metric("التيار المفقود (تجاوز)", f"{theft_val} A")
with m4:
    st.metric("إجمالي الخسائر المالية", f"{format(st.session_state.total_loss_iqd, ',')} IQD", delta=f"{hourly_loss} IQD/h")

st.divider()

# الصف الثاني: التمثيل المرئي للشارع (Street Map)
st.subheader("📍 خارطة التوزيع اللحظية (Live Distribution Map)")
c1, c2, c3, c4, c5 = st.columns(5)

def draw_element(col, title, icon, info, is_alert=False):
    style = "node-card theft-active" if is_alert else "node-card"
    col.markdown(f"<div class='{style}'><h2>{icon}</h2><b>{title}</b><br><small>{info}</small></div>", unsafe_allow_html=True)

with c1:
    draw_element(c1, "المحولة", "🏬", f"{t_temp}°C | {v_base}V", t_temp > 85)
with c2:
    is_th = (theft_loc == "مقطع 1 (بداية الشارع)")
    draw_element(c2, "عامود 1", "🗼", "تغذية زقاق 1", is_th)
    if is_th: st.error("🪝 سرقة مكتشفة!")
with c3:
    is_th = (theft_loc == "مقطع 2 (وسط الشارع)")
    draw_element(c3, "عامود 2", "🗼", "تغذية زقاق 2", is_th)
    if is_th: st.error("🪝 سرقة مكتشفة!")
with c4:
    is_th = (theft_loc == "مقطع 3 (نهاية الشارع)")
    draw_element(c4, "عامود 3", "🗼", "تغذية زقاق 3", is_th)
    if is_th: st.error("🪝 سرقة مكتشفة!")
with c5:
    draw_element(c5, "نهاية الخط", "🏁", "نقطة التعادل", False)

st.divider()

# الصف الثالث: التقارير والإنذارات (Reports & Alert System)
col_rep, col_log = st.columns([1, 1])

with col_rep:
    st.subheader("📝 تقرير الحالة الفني")
    if t_temp > 80:
        st.warning("⚠️ تحذير: درجة حرارة المحولة مرتفعة جداً، يرجى تقليل الأحمال.")
    if theft_val > 0:
        st.error(f"🚨 تم اكتشاف تجاوز في [{theft_loc}].")
        # محاكاة إرسال رسالة تليجرام
        msg = f"تنبيه: سرقة طاقة في {theft_loc} بقيمة {theft_val}A"
        if msg not in st.session_state.alert_history:
            st.session_state.alert_history.insert(0, f"{time.strftime('%H:%M:%S')} - {msg}")
            st.toast("تم إرسال تنبيه إلى هاتف المهندس المناوب (Telegram)")
    else:
        st.success("✅ المنظومة مستقرة، لا توجد تجاوزات حالياً.")

with col_log:
    st.subheader("📜 سجل أحداث النظام (System Log)")
    log_content = "<br>".join(st.session_state.alert_history) if st.session_state.alert_history else "No alerts recorded."
    st.markdown(f"<div class='alert-log'>{log_content}</div>", unsafe_allow_html=True)

# إضافة تحليل الخسائر الاقتصادية
st.info(f"**ملاحظة اقتصادية:** بناءً على القراءات الحالية، فإن نسبة الهدر المالي تشكل {round((theft_val/(legal_load+theft_val+0.1))*100, 1)}% من إجمالي الطاقة المجهزة لهذا الشارع.")
