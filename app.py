import streamlit as st
import pandas as pd
import time
import random

# إعدادات الصفحة الفخمة
st.set_page_config(page_title="Ultra Smart Store Simulator", layout="wide")

st.title("🛒 نظام المتجر الذكي - محاكاة الاندماج الحسي (Sensor Fusion)")
st.write("هذا النظام يحاكي تتبع LiDAR، الكاميرات، وحساسات الوزن في آن واحد.")

# --- قاعدة بيانات تجريبية ---
products = {
    "101": {"name": "Pepsi 250ml", "weight": 258, "price": 500},
    "102": {"name": "Lays Chips", "weight": 50, "price": 1000},
    "103": {"name": "Water Bottle", "weight": 500, "price": 250}
}

# --- Sidebar: بيانات المستخدم ---
with st.sidebar:
    st.header("👤 بيانات المشترك")
    st.info("الاسم: محمد نبيل")
    st.success("البطاقة المرتبطة: **** 4422")
    st.metric("الرصيد المتاح", "25,000 د.ع")
    st.divider()
    sim_speed = st.slider("سرعة المعالجة (ms)", 100, 1000, 500)

# --- واجهة العرض الرئيسية ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📡 مراقبة المستشعرات الحية")
    
    # محاكاة خريطة LiDAR و الكاميرا
    status_placeholder = st.empty()
    
    # محاكاة "حدث" شراء
    if st.button("🚀 محاكاة دخول زبون وتسوق"):
        with st.status("جاري تتبع الحركة وتحليل البيانات...", expanded=True) as status:
            st.write("✅ LiDAR: تم رصد كائن في الإحداثيات (X:45.2, Y:12.8)")
            time.sleep(1)
            st.write("📸 Vision AI: الكاميرا رصدت يد تمتد لرف المشروبات")
            time.sleep(1)
            st.write("⚖️ Weight Sensor: نقص في الوزن بمقدار 258g")
            time.sleep(1)
            status.update(label="تم تأكيد العملية بنجاح!", state="complete")
        
        st.balloons()
        # إضافة المنتج للسلة (محاكاة)
        item = products["101"]
        st.session_state.cart.append(item)

# --- عمود الفاتورة والذكاء الاصطناعي ---
with col2:
    st.subheader("🧾 الفاتورة الذكية")
    if 'cart' not in st.session_state:
        st.session_state.cart = []
    
    if st.session_state.cart:
        df = pd.DataFrame(st.session_state.cart)
        st.table(df[['name', 'price']])
        total = df['price'].sum()
        st.metric("الإجمالي للخصم", f"{total} د.ع")
        
        if st.button("💳 تأكيد الدفع الإلكتروني"):
            st.warning("جاري التواصل مع بوابة البنك المركزي...")
            time.sleep(2)
            st.success("تم الاستقطاع بنجاح. شكراً لتسوقك!")
            st.session_state.cart = []
    else:
        st.write("السلة فارغة حالياً.")

# --- قسم الـ Sensor Fusion Logic (لإبهار الدكتور) ---
st.divider()
st.subheader("🧠 منطق اتخاذ القرار (Decision Logic)")
st.code(f"""
def confirm_purchase(vision_id, weight_delta, lidar_pos):
    # إذا تساوت قراءة الكاميرا مع الوزن وموقع الشخص
    if vision_id == "Pepsi" and 250 < weight_delta < 265:
        return "MATCH_CONFIRMED"
    else:
        return "ERROR_RETRY"
""", language='python')
            
