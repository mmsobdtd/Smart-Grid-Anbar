import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import time

# --- إعدادات الواجهة ---
st.set_page_config(page_title="Anbar SCADA & ADMS", layout="wide")

st.title("⚡ منصة التحكم المركزية الذكية (SCADA) - الأنبار")
st.markdown("نظام تفاعلي متكامل: مراقبة، كشف تجاوزات، تحكم بالقواطع، وتأثيرات مناخية.")
st.write("---")

# --- 1. إعداد البيانات وحالة النظام (Session State) ---
if 'base_data' not in st.session_state:
    st.session_state.base_data = np.random.uniform(10, 25, 50)

sectors = ['قطاع A (تجاري)', 'قطاع B (سكني)', 'قطاع C (مستشفى/حيوي)', 'قطاع D (سكني)', 'قطاع E (صناعي)']

# --- 2. القائمة الجانبية (محاكي الظروف) ---
with st.sidebar:
    st.header("🎛️ محاكي ظروف الشبكة")
    live_update = st.toggle("تفعيل التحديث اللحظي 🔄", value=True)
    st.divider()
    
    st.subheader("🌡️ المحاكي المناخي (تأثير الحرارة)")
    ambient_temp = st.slider("درجة حرارة الجو (°C)", 20, 55, 35)
    st.caption("ترتفع الحرارة في الرمادي صيفاً مما يقلل من سعة المحولة الفعلية (Derating).")
    
    st.divider()
    st.subheader("⚠️ سيناريوهات التجاوز")
    inject = st.toggle("حقن تجاوز (Theft)", value=False)
    if inject:
        sel_sector = st.selectbox("موقع التجاوز", sectors)
        sel_phase = st.radio("الفاز", ['R', 'S', 'T'])
        theft_val = st.slider("تيار التجاوز (Amps)", 20, 150, 80)
    else:
        sel_sector, sel_phase, theft_val = None, None, 0

    st.divider()
    max_capacity_nominal = 300 # السعة الاسمية للمحولة kW

# --- 3. تنظيم الواجهات (Tabs) ---
tab1, tab2, tab3, tab4 = st.tabs([
    "🖥️ غرفة العمليات (المراقبة)", 
    "🕹️ لوحة التحكم بالقواطع (Control)", 
    "💸 التحليل الاقتصادي", 
    "🧮 القوانين والمعايير"
])

# --- إعدادات لوحة التحكم (موجودة في Tab 2 لكن تؤثر على الحسابات) ---
with tab2:
    st.header("🕹️ لوحة السيطرة اليدوية (Circuit Breakers)")
    st.info("استخدم هذه القواطع لفصل الأحمال عن القطاعات أو الفيزات عند وصول المحولة لمرحلة الخطر (>95%).")
    
    col_cb1, col_cb2 = st.columns(2)
    with col_cb1:
        st.subheader("قواطع القطاعات (Sector CBs)")
        cb_sec_a = st.toggle("قاطع قطاع A", value=True)
        cb_sec_b = st.toggle("قاطع قطاع B", value=True)
        cb_sec_c = st.toggle("قاطع قطاع C (حيوي)", value=True)
        cb_sec_d = st.toggle("قاطع قطاع D", value=True)
        cb_sec_e = st.toggle("قاطع قطاع E", value=True)
        active_sectors = []
        if cb_sec_a: active_sectors.append(sectors[0])
        if cb_sec_b: active_sectors.append(sectors[1])
        if cb_sec_c: active_sectors.append(sectors[2])
        if cb_sec_d: active_sectors.append(sectors[3])
        if cb_sec_e: active_sectors.append(sectors[4])

    with col_cb2:
        st.subheader("قواطع الفيزات (Phase Isolators)")
        cb_ph_r = st.toggle("تغذية الفاز R", value=True)
        cb_ph_s = st.toggle("تغذية الفاز S", value=True)
        cb_ph_t = st.toggle("تغذية الفاز T", value=True)
        active_phases = []
        if cb_ph_r: active_phases.append('R')
        if cb_ph_s: active_phases.append('S')
        if cb_ph_t: active_phases.append('T')

# --- 4. المعالجة الحسابية ---
# حساب السعة الفعلية بناءً على الحرارة (خصم 1% لكل درجة فوق 30)
derating_factor = 1.0 - (max(0, ambient_temp - 30) * 0.01)
actual_capacity = max_capacity_nominal * derating_factor

fluct = np.random.uniform(0.99, 1.01, 50)
currents = st.session_state.base_data * fluct

df = pd.DataFrame({
    'ID': [f"M-{i+1:02d}" for i in range(50)],
    'Sector': [sectors[i // 10] for i in range(50)],
    'Phase': [['R', 'S', 'T'][i % 3] for i in range(50)],
    'Load_A': currents
})

# تصفية البيانات بناءً على القواطع (إذا القاطع مغلق، الحمل صفر)
df.loc[~df['Sector'].isin(active_sectors), 'Load_A'] = 0
df.loc[~df['Phase'].isin(active_phases), 'Load_A'] = 0

summary = df.groupby(['Sector', 'Phase'])['Load_A'].sum().reset_index()
trans_rows = []
for _, r in summary.iterrows():
    val = r['Load_A'] * 1.02 # 2% ضياع فني
    # إضافة التجاوز فقط إذا كان القطاع والفاز يعملان
    if inject and r['Sector'] == sel_sector and r['Phase'] == sel_phase and (sel_sector in active_sectors) and (sel_phase in active_phases):
        val += theft_val
    trans_rows.append({'Sector': r['Sector'], 'Phase': r['Phase'], 'Trans_Load': val})

df_trans = pd.DataFrame(trans_rows)

p_meters_total = (df['Load_A'].sum() * 220) / 1000
p_trans_total = (df_trans['Trans_Load'].sum() * 220) / 1000
load_percentage = (p_trans_total / actual_capacity) * 100

system_warning = ""
if load_percentage > 95:
    system_warning = f"🚨 إنذار حرج: تحميل المحولة وصل إلى {load_percentage:.1f}%. السعة الفعلية انخفضت بسبب الحرارة ({ambient_temp}°C). يرجى الانتقال للوحة التحكم وفصل الفاز الأعلى حملاً أو أحد القطاعات السكنية فوراً!"

# --- 5. عرض الواجهات ---
with tab1:
    if system_warning:
        st.error(system_warning)
        
    col_g1, col_g2, col_g3 = st.columns(3)
    
    fig_gauge1 = go.Figure(go.Indicator(
        mode = "gauge+number+delta", 
        value = load_percentage,
        delta = {'reference': 80, 'increasing': {'color': "red"}},
        title = {'text': f"تحميل المحولة (السعة: {actual_capacity:.0f}kW)"},
        gauge = {'axis': {'range': [None, 120]},
                 'bar': {'color': "darkblue"},
                 'steps': [{'range': [0, 80], 'color': "lightgreen"},
                           {'range': [80, 95], 'color': "orange"},
                           {'range': [95, 120], 'color': "red"}]}
    ))
    fig_gauge1.update_layout(height=250, margin=dict(l=10, r=10, t=30, b=10))
    col_g1.plotly_chart(fig_gauge1, use_container_width=True)

    col_g2.metric("الحرارة وتأثيرها (Derating)", f"{ambient_temp} °C", f"{(derating_factor-1)*100:.1f}% من السعة", delta_color="inverse")
    
    ir = df_trans[df_trans['Phase'] == 'R']['Trans_Load'].sum() if 'R' in active_phases else 0
    is_ = df_trans[df_trans['Phase'] == 'S']['Trans_Load'].sum() if 'S' in active_phases else 0
    it = df_trans[df_trans['Phase'] == 'T']['Trans_Load'].sum() if 'T' in active_phases else 0
    
    # تحديد الفاز الأعلى حملاً
    loads = {'R': ir, 'S': is_, 'T': it}
    highest_phase = max(loads, key=loads.get)
    
    col_g3.metric(f"الفاز الأعلى حملاً ({highest_phase})", f"{loads[highest_phase]:.1f} A", "أولوية الفصل عند الخطر", delta_color="off")

    st.write("---")
    fig_bar = px.bar(df_trans, x='Sector', y='Trans_Load', color='Phase',
                     title="الأحمال الحية للقطاعات (ينعكس عليها قرارات الفصل)", barmode='group')
    st.plotly_chart(fig_bar, use_container_width=True)

with tab3:
    st.header("💸 تقييم الأثر المالي للتجاوزات")
    if inject and (sel_sector in active_sectors) and (sel_phase in active_phases):
        theft_kw = (theft_val * 220) / 1000
        cost_per_month = theft_kw * 15 * 24 * 30
        st.error(f"🚨 هدر مالي نشط في **{sel_sector} - الفاز {sel_phase}**. الخسارة الشهرية المقدرة: {cost_per_month:,.0f} دينار.")
    else:
        st.success("✅ لا توجد تجاوزات نشطة، أو تم فصل الخط المتجاوز بواسطة القواطع.")

with tab4:
    st.header("📐 الأسس الرياضية للمحاكي")
    st.subheader("1. تأثير الحرارة على سعة المحولة (Temperature Derating)")
    st.latex(r"Capacity_{Actual} = Capacity_{Nominal} \times [1 - (T_{Ambient} - 30) \times 0.01]")
    st.write("يحاكي هذا القانون تأثير طقس الأنبار الحار على أداء المعدات الكهربائية.")
    
    st.subheader("2. موازنة الأحمال والسيطرة اليدوية")
    st.write("تم دمج قواطع الدورة (Circuit Breakers) برمجياً للسماح للمشغل بعزل القطاعات (Sectors) أو الأطوار (Phases) التي تعاني من عدم اتزان عالٍ أو تجاوز غير مسموح.")

if live_update:
    time.sleep(2)
    st.rerun()
    
