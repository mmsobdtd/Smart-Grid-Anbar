import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import time

# --- إعدادات الواجهة الاحترافية ---
st.set_page_config(page_title="Anbar Smart Grid - Enterprise Edition", layout="wide")

st.title("⚡ مركز السيطرة الذكي لشبكات التوزيع - الإصدار المتقدم")
st.markdown("نظام (ADMS) متكامل يتضمن: موازنة الأحمال، كشف التجاوزات، التحليل الاقتصادي، والحماية الآلية.")
st.write("---")

# --- 1. إعداد البيانات الأساسية ---
if 'base_data' not in st.session_state:
    st.session_state.base_data = np.random.uniform(10, 25, 50) # أحمال البيوت بالأساس

sectors = ['قطاع A (تجاري)', 'قطاع B (سكني)', 'قطاع C (مستشفى/حيوي)', 'قطاع D (سكني)', 'قطاع E (صناعي)']

# --- 2. لوحة التحكم والمدخلات الاقتصادية ---
with st.sidebar:
    st.header("🎮 محاكي الشبكة المركزية")
    
    st.subheader("⚠️ سيناريوهات الأعطال")
    inject = st.toggle("حقن تجاوز (Non-Technical Loss)", value=False)
    if inject:
        sel_sector = st.selectbox("موقع التجاوز", sectors)
        sel_phase = st.radio("الفاز", ['R', 'S', 'T'])
        theft_val = st.slider("تيار التجاوز (Amps)", 20, 150, 60)
    else:
        sel_sector, sel_phase, theft_val = None, None, 0
        
    st.divider()
    st.subheader("💰 المعايير الاقتصادية والفنية")
    tariff = st.number_input("تسعيرة الكهرباء (دينار/kWh)", value=15)
    max_capacity = st.number_input("سعة المحولة القصوى (kW)", value=300)
    
    st.info("💡 النظام مزود بخوارزمية الفصل الذكي لحماية المحولات.")

# --- 3. الأبواب (Tabs) لتنظيم العرض ---
tab1, tab2, tab3 = st.tabs(["🖥️ غرفة العمليات (SCADA)", "💸 التحليل الاقتصادي والخسائر", "🧮 المعايير الرياضية"])

with tab1:
    placeholder = st.empty()
    while True:
        # 1. توليد القراءات اللحظية
        fluct = np.random.uniform(0.99, 1.01, 50)
        currents = st.session_state.base_data * fluct
        
        df = pd.DataFrame({
            'ID': [f"M-{i+1:02d}" for i in range(50)],
            'Sector': [sectors[i // 10] for i in range(50)],
            'Phase': [['R', 'S', 'T'][i % 3] for i in range(50)],
            'Load_A': currents
        })

        # 2. حسابات المحولة والتجاوز
        summary = df.groupby(['Sector', 'Phase'])['Load_A'].sum().reset_index()
        trans_rows = []
        for _, r in summary.iterrows():
            val = r['Load_A'] * 1.02 # 2% ضياع فني
            if inject and r['Sector'] == sel_sector and r['Phase'] == sel_phase:
                val += theft_val
            trans_rows.append({'Sector': r['Sector'], 'Phase': r['Phase'], 'Trans_Load': val})
        
        df_trans = pd.DataFrame(trans_rows)
        
        # تحويل التيار إلى قدرة (kW) - بافتراض 220 فولت
        p_meters_total = (df['Load_A'].sum() * 220) / 1000
        p_trans_total = (df_trans['Trans_Load'].sum() * 220) / 1000
        load_percentage = (p_trans_total / max_capacity) * 100

        # 3. خوارزمية الحماية (Smart Load Shedding)
        system_warning = ""
        if load_percentage > 95:
            system_warning = "⚠️ المحولة في خطر الإنهيار! تم تفعيل الفصل الآلي لـ (القطاع B - السكني) للحفاظ على (القطاع C - المستشفى)."
            # محاكاة فصل القطاع B
            p_trans_total -= 40 # فصل افتراضي لـ 40 كيلوواط
            load_percentage = (p_trans_total / max_capacity) * 100

        with placeholder.container():
            # تنبيهات النظام
            if system_warning:
                st.error(system_warning)
                
            col_g1, col_g2, col_g3 = st.columns(3)
            
            # Gauge 1: حمل المحولة
            fig_gauge1 = go.Figure(go.Indicator(
                mode = "gauge+number", value = load_percentage,
                title = {'text': "تحميل المحولة (%)"},
                gauge = {'axis': {'range': [None, 120]},
                         'bar': {'color': "darkblue"},
                         'steps': [{'range': [0, 80], 'color': "lightgreen"},
                                   {'range': [80, 95], 'color': "orange"},
                                   {'range': [95, 120], 'color': "red"}]}
            ))
            fig_gauge1.update_layout(height=250, margin=dict(l=10, r=10, t=30, b=10))
            col_g1.plotly_chart(fig_gauge1, use_container_width=True)

            col_g2.metric("القدرة المجهزة الكلية", f"{p_trans_total:.1f} kW")
            col_g2.metric("الاستهلاك المفوتر (القانوني)", f"{p_meters_total:.1f} kW")
            
            # حساب عدم الاتزان
            ir = df_trans[df_trans['Phase'] == 'R']['Trans_Load'].sum()
            is_ = df_trans[df_trans['Phase'] == 'S']['Trans_Load'].sum()
            it = df_trans[df_trans['Phase'] == 'T']['Trans_Load'].sum()
            unbalance = (max(abs(ir - is_), abs(is_ - it), abs(it - ir)) / ((ir+is_+it)/3)) * 100
            
            col_g3.metric("معامل عدم الاتزان", f"{unbalance:.1f}%", delta="مستقر" if unbalance < 15 else "خطر", delta_color="inverse")

            st.write("---")
            # رسم بياني للأحمال
            fig_bar = px.bar(df_trans, x='Sector', y='Trans_Load', color='Phase',
                             title="الأحمال الحية للقطاعات المغذاة", barmode='group')
            st.plotly_chart(fig_bar, use_container_width=True)
            
        time.sleep(2) # تحديث مستمر

with tab2:
    st.header("💸 تقييم الأثر المالي للتجاوزات (Financial Audit)")
    
    if inject:
        # الحسابات المالية
        theft_kw = (theft_val * 220) / 1000
        cost_per_hour = theft_kw * tariff
        cost_per_month = cost_per_hour * 24 * 30
        cost_per_year = cost_per_month * 12
        
        st.error(f"🚨 تم اكتشاف هدر مالي بسبب التجاوز في **{sel_sector} - الفاز {sel_phase}**")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("الطاقة المسروقة اللحظية", f"{theft_kw:.2f} kW")
        c2.metric("الخسارة الشهرية المقدرة", f"{cost_per_month:,.0f} IQD")
        c3.metric("الخسارة السنوية المقدرة", f"{cost_per_year:,.0f} IQD")
        
        st.write("---")
        st.subheader("📉 الإسقاط المالي التراكمي")
        # رسم بياني للخسائر التراكمية
        months = [f"شهر {i+1}" for i in range(12)]
        cumulative_loss = [cost_per_month * (i+1) for i in range(12)]
        fig_finance = px.area(x=months, y=cumulative_loss, 
                              labels={'x': 'الفترة الزمنية', 'y': 'الخسائر التراكمية (دينار)'},
                              title="النزيف المالي المتوقع في حال عدم معالجة التجاوز")
        st.plotly_chart(fig_finance, use_container_width=True)
        
    else:
        st.success("✅ الشبكة محكمة. لا توجد خسائر مالية خارج نسبة الضياع الفني الطبيعي (2%).")

with tab3:
    st.header("📐 الأسس الرياضية للمنظومة الاقتصادية والفنية")
    
    st.subheader("1. معادلة الخسائر المالية (Economic Loss Equation)")
    st.latex(r"Cost_{Monthly} = P_{Theft} \times Tariff \times 24 \times 30")
    st.write("حيث $P_{Theft}$ هي القدرة المسروقة بالكيلوواط، والـ Tariff هي تسعيرة وحدة الكهرباء.")
    
    st.subheader("2. معامل عدم الاتزان (Voltage/Current Unbalance Factor)")
    st.latex(r"Unbalance\% = \frac{Max_{Deviation}}{Average_{Current}} \times 100")
    
    st.subheader("3. خوارزمية الحماية الذكية (Smart Load Shedding Logic)")
    st.code("""
    if Total_Transformer_Load > 95%:
        Disconnect_Sector(Priority='Low') # فصل الأحمال غير الحيوية
        Send_Alert_To_SCADA()
        Protect_Transformer_From_Burnout()
    """, language="python")
    
