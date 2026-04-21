import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import time

# إعدادات الصفحة لتشبه أنظمة SCADA العالمية
st.set_page_config(page_title="Anbar ADMS Pro", layout="wide")

st.title("⚡ نظام إدارة الأحمال وكشف التجاوزات - مركز سيطرة الرمادي")
st.markdown("---")

# --- 1. بناء هيكلية الشبكة (5 خطوط/قطاعات) ---
# كل خط يحتوي على 10 منازل موزعة على 3 فازات
sectors = ['قطاع التأميم', 'قطاع الأندلس', 'قطاع الملعب', 'قطاع الورار', 'قطاع الجزيرة']
if 'base_loads' not in st.session_state:
    # توليد أحمال أساسية ثابتة لكل بيت لضمان الاستقرارية
    st.session_state.base_loads = np.random.uniform(5, 20, 50) 

# --- 2. التحكم في المحاكاة عبر القائمة الجانبية ---
with st.sidebar:
    st.header("🎮 لوحة التحكم بالحقن")
    inject_theft = st.toggle("تفعيل حالة تجاوز (Injection)")
    if inject_theft:
        theft_sector = st.selectbox("اختر القطاع المستهدف", sectors)
        theft_phase = st.selectbox("اختر الفاز المستهدف", ['R', 'S', 'T'])
        theft_val = st.slider("قيمة التجاوز (Amps)", 20, 100, 50)
    else:
        theft_sector, theft_phase, theft_val = None, None, 0
    
    st.divider()
    update_speed = st.slider("سرعة التحديث (ثواني)", 1, 5, 2)

# --- 3. محرك المحاكاة اللحظي ---
placeholder = st.empty()

while True:
    # توليد تذبذب طفيف جداً (0.5%) لضمان واقعية القراءات (أحمال مستقرة)
    fluctuation = np.random.uniform(0.99, 1.01, 50)
    current_loads = st.session_state.base_loads * fluctuation
    
    # توزيع المنازل على القطاعات والفازات
    data = []
    for i in range(50):
        sector = sectors[i // 10]
        phase = ['R', 'S', 'T'][i % 3]
        data.append({
            'ID': f"M-{i+1:02d}",
            'Sector': sector,
            'Phase': phase,
            'Meter_Current': current_loads[i]
        })
    
    df = pd.DataFrame(data)
    
    # حساب ميزان القوى لكل فاز ولكل قطاع
    # 1. مجموع العدادات (القانوني)
    meter_totals = df.groupby(['Sector', 'Phase'])['Meter_Current'].sum().reset_index()
    
    # 2. قراءة المحولة (تشمل التجاوز إذا وجد + ضياع فني 2%)
    transformer_readings = []
    for _, row in meter_totals.iterrows():
        real_val = row['Meter_Current'] * 1.02 # ضياع فني ثابت
        is_theft = (row['Sector'] == theft_sector and row['Phase'] == theft_phase)
        if is_theft:
            real_val += theft_val
        
        transformer_readings.append({
            'Sector': row['Sector'],
            'Phase': row['Phase'],
            'Trans_Current': real_val,
            'Is_Theft': is_theft
        })
    
    df_trans = pd.DataFrame(transformer_readings)

    # --- 4. واجهة العرض Dashboard ---
    with placeholder.container():
        # الصف الأول: مؤشرات الحالة العامة
        m1, m2, m3, m4 = st.columns(4)
        total_p_meters = df['Meter_Current'].sum() * 220 / 1000
        total_p_trans = df_trans['Trans_Current'].sum() * 220 / 1000
        
        m1.metric("حمل المحولة الكلي", f"{total_p_trans:.1f} kW")
        m2.metric("الحمل المستلم (عدادات)", f"{total_p_meters:.1f} kW")
        m3.metric("استقرارية التردد", "50.01 Hz")
        m4.metric("حالة الشبكة", "مستقرة" if not inject_theft else "حرجة", 
                  delta="-تجاوز مكتشف" if inject_theft else None, delta_color="inverse")

        # الصف الثاني: الرسوم البيانية
        c1, c2 = st.columns([2, 1])
        
        with c1:
            st.subheader("📍 مراقبة الأحمال حسب القطاعات (Feeders)")
            fig_sec = px.bar(df, x='Sector', y='Meter_Current', color='Phase', 
                             barmode='group', title="توزيع الأحمال القانونية على الفازات لكل قطاع")
            st.plotly_chart(fig_sec, use_container_width=True)
            
        with c2:
            st.subheader("⚖️ اتزان فازات المحولة المركزية")
            phase_sums = df_trans.groupby('Phase')['Trans_Current'].sum()
            fig_phase = px.pie(values=phase_sums, names=phase_sums.index, 
                               color=phase_sums.index, color_discrete_map={'R':'red', 'S':'orange', 'T':'blue'})
            st.plotly_chart(fig_phase, use_container_width=True)

        # الصف الثالث: تقرير كشف التجاوزات (الجزء الأهم للدكتور)
        st.markdown("### 📋 سجل الحوادث وتحليل الأعطال (Incident Report)")
        
        # خوارزمية كشف الفرق
        for index, row in df_trans.iterrows():
            meter_val = meter_totals[(meter_totals['Sector'] == row['Sector']) & 
                                     (meter_totals['Phase'] == row['Phase'])]['Meter_Current'].values[0]
            diff = row['Trans_Current'] - (meter_val * 1.02)
            
            if diff > 10: # إذا كان الفرق أكبر من 10 أمبير (تجاوز)
                st.error(f"""
                **🚨 تنبيه أمني:** تم كشف تجاوز في **{row['Sector']}** | **الفاز {row['Phase']}** - القيمة المسربة: **{diff:.2f} أمبير** - الإجراء: جاري تحديد النقطة بدقة وإرسال إشعار لمركز صيانة الرمادي.
                """)
        
        if not inject_theft:
            st.success("✅ جميع الخطوط تعمل ضمن المعايير الفنية المسموحة.")

    time.sleep(update_speed)
    
