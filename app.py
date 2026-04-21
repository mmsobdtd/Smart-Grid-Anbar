import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import time

# --- إعدادات رصانة المشروع ---
st.set_page_config(page_title="Anbar Pro-Grid ADMS", layout="wide")

# دالة لتوليد أحمال واقعية متذبذبة
def generate_real_data(n_houses, theft_active, theft_val, theft_house_idx):
    # تصنيف البيوت (30% حمل خفيف، 50% متوسط، 20% عالٍ)
    categories = np.random.choice(['Light', 'Medium', 'Heavy'], size=n_houses, p=[0.3, 0.5, 0.2])
    currents = []
    for cat in categories:
        if cat == 'Light': currents.append(np.random.uniform(1, 5))
        elif cat == 'Medium': currents.append(np.random.uniform(5, 15))
        else: currents.append(np.random.uniform(15, 35))
    
    # إضافة التذبذب اللحظي
    currents = np.array(currents) + np.random.uniform(-0.5, 0.5, n_houses)
    currents = np.maximum(currents, 0.5) # لضمان عدم وجود تيار سالب
    
    # توزيع متزن على الفازات (R, S, T)
    phases = ['R', 'S', 'T'] * (n_houses // 3) + ['R', 'S'][:n_houses % 3]
    np.random.shuffle(phases)
    
    df = pd.DataFrame({'House_ID': [f"H-{i+1:02d}" for i in range(n_houses)], 
                       'Phase': phases, 'Meter_Current': currents})
    
    # حساب قيم المحولة (Transformer)
    trans_data = df.groupby('Phase')['Meter_Current'].sum().to_dict()
    
    # إضافة التجاوز في المحولة فقط (لا يظهر في العدادات)
    theft_info = {"Value": 0, "Phase": None, "House": None}
    if theft_active:
        theft_p = df.iloc[theft_house_idx]['Phase']
        trans_data[theft_p] += theft_val
        theft_info = {"Value": theft_val, "Phase": theft_p, "House": df.iloc[theft_house_idx]['House_ID']}
        
    return df, trans_data, theft_info

# --- واجهة المستخدم ---
st.title("🏛️ منصة إدارة الشبكة المتقدمة - جامعة الأنبار")
st.markdown("#### نظام ADMS لمراقبة ميزان القوى وكشف الضياعات غير الفنية")

# السيّدبار للتحكم العميق
with st.sidebar:
    st.header("🎮 لوحة التحكم بالبث الحي")
    live_mode = st.toggle("تفعيل البث اللحظي (Live Simulation)", value=True)
    st.divider()
    st.subheader("⚠️ سيناريو التجاوز")
    theft_toggle = st.checkbox("حقن تجاوز في الشبكة (Inject Theft)")
    theft_amount = st.slider("قيمة التجاوز (Amps)", 10, 100, 40)
    theft_h_idx = st.number_input("موقع التجاوز (Index)", 0, 49, 21)
    st.divider()
    st.write("**الحالة الفنية:** متصل ببروكر MQTT (افتراضي)")

# حاويات العرض المتغيرة
placeholder = st.empty()

# حلقة المحاكاة اللحظية
while True:
    df_houses, trans_dict, theft_details = generate_real_data(50, theft_toggle, theft_amount, theft_h_idx)
    
    # حسابات هندسية رصينة
    v_line = 220
    p_meters = (df_houses['Meter_Current'].sum() * v_line) / 1000 # kW
    p_trans = (sum(trans_dict.values()) * v_line * 1.02) / 1000 # kW (2% ضياع فني ثابت)
    
    # حساب معامل عدم الاتزان (VUF)
    i_vals = list(trans_dict.values())
    i_avg = np.mean(i_vals)
    unbalance = (max([abs(x - i_avg) for x in i_vals]) / i_avg) * 100

    with placeholder.container():
        # 1. المربعات القياسية (KPIs)
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("إجمالي حمل المحولة", f"{p_trans:.2f} kW")
        kpi2.metric("مجموع العدادات الذكية", f"{p_meters:.2f} kW")
        kpi3.metric("تيار المتعادل (In)", f"{np.std(i_vals):.2f} A")
        kpi4.metric("معامل عدم الاتزان", f"{unbalance:.1f}%", delta="-2.1%" if unbalance < 10 else "+5.4%", delta_color="inverse")

        # 2. الرسم البياني للمتجهات (Phasor Diagram) - قمة الرصانة الهندسية
        st.write("---")
        c_left, c_right = st.columns([2, 1])
        
        with c_left:
            st.subheader("🏠 التوزيع الحي لأحمال 50 منزلاً")
            fig_h = px.bar(df_houses, x='House_ID', y='Meter_Current', color='Phase',
                           color_discrete_map={'R':'#FF4136', 'S':'#FF851B', 'T':'#0074D9'},
                           title="قراءات العدادات اللحظية (Amps)")
            fig_h.update_layout(height=400)
            st.plotly_chart(fig_h, use_container_width=True)

        with c_right:
            st.subheader("📈 توازن فازات المحولة")
            fig_p = go.Figure(go.Bar(x=['Phase R', 'Phase S', 'Phase T'], 
                                   y=[trans_dict['R'], trans_dict['S'], trans_dict['T']],
                                   marker_color=['#FF4136', '#FF851B', '#0074D9']))
            fig_p.update_layout(height=400)
            st.plotly_chart(fig_p, use_container_width=True)

        # 3. محرك كشف التجاوز الذكي
        if theft_toggle:
            diff = p_trans - (p_meters + (p_trans * 0.02)) # الفرق بعد طرح الضياع الفني
            if diff > 5:
                st.error(f"""
                ### 🚨 إنذار: تم كشف تجاوز (Non-Technical Loss)
                - **الفاز المصاب:** {theft_details['Phase']}
                - **القيمة التقديرية:** {theft_amount} Amps
                - **موقع الاحتباه:** المنطقة القريبة من العداد {theft_details['House']}
                - **التوصية:** إرسال فريق تفتيش فوراً إلى قطاع 'حي الأندلس - زقاق 12'.
                """)
        else:
            st.success("🔒 أمن الشبكة: لا توجد فروقات غير مفسرة بين الخارج والمستلم.")

    if not live_mode:
        break
    time.sleep(2) # تحديث كل ثانيتين ليعطي شعور البث الحي
