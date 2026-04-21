import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# إعداد الصفحة
st.set_page_config(page_title="Anbar Smart Grid - 50 Houses Simulation", layout="wide")

st.title("⚡ نظام مراقبة شبكة الرمادي الذكية (ADMS)")
st.info("محاكاة حية لـ 50 عداد منزلي مرتبط بمحولة حي الأندلس")

# --- إدارة حالة التجاوز (Session State) ---
if 'theft_active' not in st.session_state:
    st.session_state.theft_active = False

# القائمة الجانبية للتحكم
with st.sidebar:
    st.header("🛠️ غرفة التحكم بالشبكة")
    if st.button("🔴 تفعيل تجاوز (Simulation)", type="primary"):
        st.session_state.theft_active = True
    if st.button("🟢 إيقاف التجاوز / إصلاح الشبكة"):
        st.session_state.theft_active = False
    
    st.write("---")
    base_voltage = st.number_input("جهد الشبكة (Voltage)", value=220)

# --- توليد قراءات 50 منزل (Data Generation) ---
np.random.seed(42) # للحفاظ على استقرار القراءات العشوائية
house_ids = [f"House_{i+1:02d}" for i in range(50)]
# توزيع المنازل على الفازات (17 بيت على R، 17 على S، 16 على T)
phases = ['R']*17 + ['S']*17 + ['T']*16
# استهلاك عشوائي بين 2 إلى 15 أمبير لكل بيت
house_currents = np.random.uniform(2, 15, 50)

df_houses = pd.DataFrame({
    'ID': house_ids,
    'Phase': phases,
    'Current (A)': house_currents
})

# --- منطق التجاوز (Theft Logic) ---
theft_location = "House_22" # تحديد الموقع المفترض للتجاوز
theft_value = 0
if st.session_state.theft_active:
    theft_value = 45.0  # قيمة سحب التجاوز (45 أمبير إضافية غير مسجلة)
    # التجاوز يحدث غالباً في فاز معين، لنفترض الفاز R
    theft_phase = "R"
else:
    theft_phase = None

# --- حسابات المحولة (Transformer Analytics) ---
# مجموع قراءات العدادات حسب الفازات
sum_r = df_houses[df_houses['Phase'] == 'R']['Current (A)'].sum()
sum_s = df_houses[df_houses['Phase'] == 'S']['Current (A)'].sum()
sum_t = df_houses[df_houses['Phase'] == 'T']['Current (A)'].sum()

# القراءات الحقيقية في المحولة (تشمل التجاوز + الضياع الفني 3%)
trans_r = sum_r + (theft_value if theft_phase == "R" else 0) + (sum_r * 0.03)
trans_s = sum_s + (theft_value if theft_phase == "S" else 0) + (sum_s * 0.03)
trans_t = sum_t + (theft_value if theft_phase == "T" else 0) + (sum_t * 0.03)

total_trans_power = (trans_r + trans_s + trans_t) * base_voltage / 1000 # kW
total_meters_power = (sum_r + sum_s + sum_t) * base_voltage / 1000 # kW

# --- واجهة العرض (Dashboard) ---
# 1. المربعات العلوية
c1, c2, c3, c4 = st.columns(4)
c1.metric("قدرة المحولة الكلية", f"{total_trans_power:.1f} kW")
c2.metric("مجموع قراءات 50 بيت", f"{total_meters_power:.1f} kW")
c3.metric("الضياع الكلي (Losses)", f"{total_trans_power - total_meters_power:.2f} kW")

if st.session_state.theft_active:
    c4.error(f"🚨 تم كشف تجاوز في الفاز {theft_phase}")
else:
    c4.success("✅ الشبكة مستقرة")

st.write("---")

# 2. الرسوم البيانية
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("🏠 حالة استهلاك الـ 50 منزلاً (Real-time)")
    # تلوين البيت المتجاوز باللون الأحمر إذا تم تفعيل التجاوز
    df_houses['Status'] = 'قانوني'
    if st.session_state.theft_active:
        df_houses.loc[df_houses['ID'] == theft_location, 'Status'] = 'تجاوز مشبوه'
    
    fig_houses = px.bar(df_houses, x='ID', y='Current (A)', color='Status', 
                        color_discrete_map={'قانوني':'#00CC96', 'تجاوز مشبوه':'#EF553B'})
    st.plotly_chart(fig_houses, use_container_width=True)

with col_right:
    st.subheader("📊 أحمال الفازات في المحولة")
    fig_phase = px.bar(x=['Phase R', 'Phase S', 'Phase T'], y=[trans_r, trans_s, trans_t],
                      color=['R', 'S', 'T'], labels={'x':'الفاز', 'y':'التيار (A)'})
    st.plotly_chart(fig_phase, use_container_width=True)

# 3. جدول البيانات التفصيلي
with st.expander("👁️ عرض قراءات العدادات التفصيلية"):
    st.dataframe(df_houses, use_container_width=True)

# 4. الذكاء الاصطناعي وكشف الموقع
if st.session_state.theft_active:
    st.warning(f"""
    🔍 **تحليل النظام:** تم ملاحظة عدم اتزان حاد في **الفاز {theft_phase}**.
    - الفرق بين خرج المحولة ومجموع العدادات في هذا الفاز هو **{theft_value:.1f} أمبير**.
    - الموقع التقريبي للتجاوز: **القطاع القريب من {theft_location}** في حي الأندلس.
    """)
    
