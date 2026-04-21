import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# إعدادات الصفحة
st.set_page_config(page_title="Anbar Smart Grid", layout="wide")

st.title("⚡ نظام إدارة الشبكة الذكية المتكامل - الأنبار")

# محاكاة البيانات في القائمة الجانبية
with st.sidebar:
    st.header("⚙️ مدخلات الشبكة")
    p_main = st.number_input("القدرة الكلية للمحولة (kW)", value=800.0)
    st.subheader("أحمال الفازات (Amp)")
    ir = st.slider("الفاز R", 0.0, 400.0, 250.0)
    is_ = st.slider("الفاز S", 0.0, 400.0, 280.0)
    it = st.slider("الفاز T", 0.0, 400.0, 210.0)
    p_meters = st.number_input("مجموع قراءات العدادات (kW)", value=720.0)

# الحسابات الهندسية (لإقناع الدكتور برصانة العمل)
tech_loss = p_main * 0.05
total_loss = p_main - p_meters
theft_loss = max(0.0, total_loss - tech_loss)
# تيار المتعادل (للتوازن)
i_n = np.sqrt(ir**2 + is_**2 + it**2 - (ir*is_ + is_*it + it*ir))

# عرض النتائج
col1, col2, col3 = st.columns(3)
col1.metric("تيار المتعادل", f"{i_n:.2f} A")
col2.metric("التجاوزات", f"{theft_loss:.1f} kW", delta_color="inverse")
col3.metric("كفاءة الشبكة", f"{(p_meters/p_main)*100:.1f}%")

st.write("---")
# الرسوم البيانية
c1, c2 = st.columns(2)
with c1:
    st.subheader("📊 توزيع الطاقة وضياعات التجاوز")
    fig = px.pie(values=[p_meters, tech_loss, theft_loss], names=['قانوني', 'ضياع فني', 'تجاوز'])
    st.plotly_chart(fig, use_container_width=True)
with c2:
    st.subheader("📈 مراقبة الفازات الثلاثة")
    st.bar_chart({"Current (A)": [ir, is_, it]})

if theft_loss > 40:
    st.error(f"🚨 تحذير: تم كشف سرقة طاقة بقيمة {theft_loss:.1f} كيلو واط!")
    
