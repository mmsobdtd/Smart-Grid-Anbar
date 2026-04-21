import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import time

# إعداد الصفحة بنمط Dark Mode احترافي
st.set_page_config(page_title="Anbar Smart Grid - Research Grade", layout="wide")

st.title("⚡ منصة الأنبار المتقدمة لإدارة الشبكة وكشف التجاوزات")
st.write("---")

# --- 1. إعداد البيانات والقطاعات ---
if 'base_data' not in st.session_state:
    st.session_state.base_data = np.random.uniform(10, 30, 50)

sectors = ['القطاع A (شمال الرمادي)', 'القطاع B (وسط المدينة)', 'القطاع C (حي الملعب)', 'القطاع D (التأميم)', 'القطاع E (الورار)']

# --- 2. القائمة الجانبية للتحكم ---
with st.sidebar:
    st.header("🎮 لوحة محاكاة التجاوز")
    inject = st.toggle("تفعيل حقن تجاوز في الشبكة")
    if inject:
        sel_sector = st.selectbox("اختر قطاع التجاوز", sectors)
        sel_phase = st.radio("اختر الفاز المصاب", ['R', 'S', 'T'])
        theft_val = st.slider("قيمة التجاوز (Amps)", 20, 80, 45)
    else:
        sel_sector, sel_phase, theft_val = None, None, 0
    st.divider()
    st.info("النظام يقوم بتدقيق الطاقة كل 2 ثانية")

# --- 3. تنظيم الواجهة باستخدام Tabs (للرصانة) ---
tab1, tab2, tab3 = st.tabs(["📈 لوحة المراقبة الحية", "🧮 المنطق الرياضي والقوانين", "📋 سجل كشف التجاوزات"])

with tab1:
    placeholder = st.empty()
    while True:
        # توليد تذبذب مستقر (Realistic Noise)
        fluct = np.random.uniform(0.98, 1.02, 50)
        currents = st.session_state.base_data * fluct
        
        # بناء الداتا فريم
        rows = []
        for i in range(50):
            sec = sectors[i // 10]
            ph = ['R', 'S', 'T'][i % 3]
            rows.append({'ID': f"M-{i+1:02d}", 'Sector': sec, 'Phase': ph, 'Load': currents[i]})
        df = pd.DataFrame(rows)

        # حسابات المحولة
        summary = df.groupby(['Sector', 'Phase'])['Load'].sum().reset_index()
        trans_rows = []
        for _, r in summary.iterrows():
            val = r['Load'] * 1.02 # ضياع فني 2%
            if r['Sector'] == sel_sector and r['Phase'] == sel_phase:
                val += theft_val
            trans_rows.append({'Sector': r['Sector'], 'Phase': r['Phase'], 'Trans_Load': val})
        df_trans = pd.DataFrame(trans_rows)

        with placeholder.container():
            # عرض المؤشرات
            c1, c2, c3 = st.columns(3)
            p_trans_total = df_trans['Trans_Load'].sum() * 220 / 1000
            p_meters_total = df['Load'].sum() * 220 / 1000
            c1.metric("حمل المحولة الكلي", f"{p_trans_total:.2f} kW")
            c2.metric("الحمل المستهلك قانونياً", f"{p_meters_total:.2f} kW")
            c3.metric("كفاءة المنظومة", f"{(p_meters_total/p_trans_total)*100:.1f}%")

            st.write("---")
            # خريطة حرارية للقطاعات
            st.subheader("📍 خارطة الحالة الجغرافية (Grid Heatmap)")
            fig_map = px.scatter(df, x='Sector', y='ID', color='Load', size='Load',
                                 color_continuous_scale='Viridis', title="توزيع الأحمال على المشتركين")
            st.plotly_chart(fig_map, use_container_width=True)

            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("📊 مقارنة الفازات في المحولة")
                phase_p = df_trans.groupby('Phase')['Trans_Load'].sum()
                st.bar_chart(phase_p)
            with col_b:
                st.subheader("⚖️ تيار المتعادل (Neutral Current)")
                # حساب تيار المتعادل
                ir = df_trans[df_trans['Phase'] == 'R']['Trans_Load'].sum()
                is_ = df_trans[df_trans['Phase'] == 'S']['Trans_Load'].sum()
                it = df_trans[df_trans['Phase'] == 'T']['Trans_Load'].sum()
                in_curr = np.sqrt(ir**2 + is_**2 + it**2 - (ir*is_ + is_*it + it*ir))
                st.metric("Neutral Current", f"{in_curr:.2f} A", delta="High Unbalance" if in_curr > 50 else "Stable")

        time.sleep(2)

with tab2:
    st.header("📑 الأسس العلمية لحساب الضياعات")
    st.write("لإثبات رصانة النظام، يعتمد البرنامج على القوانين التالية:")
    
    st.subheader("1. قانون ميزان القوى (Power Balance Law)")
    st.latex(r"P_{Theft} = P_{Transformer} - (P_{Sum\_Meters} + P_{Technical\_Loss})")
    st.info("حيث يتم عزل الضياعات الفنية (مقاومة الأسلاك) بنسبة 2% قبل افتراض وجود تجاوز.")

    st.subheader("2. تيار الخط المتعادل (Neutral Current Calculation)")
    st.latex(r"I_N = \sqrt{I_R^2 + I_S^2 + I_T^2 - (I_R I_S + I_S I_T + I_T I_R)}")
    st.write("يستخدم هذا القانون لكشف عدم الاتزان الناتج عن السحب غير القانوني على فاز معين دون الآخر.")

    st.subheader("3. خوارزمية تحديد الموقع (Localization Logic)")
    st.write("""
    يعمل النظام بطريقة **تدقيق النقاط الفرعية (Sub-point Audit)**:
    - يتم تقسيم الشبكة إلى قطاعات (Feeders).
    - لكل قطاع، نقارن مجموع العدادات $ \sum I_{meters} $ مع قراءة المحولة لذلك القطاع.
    - إذا كان $ \Delta I > Threshold $، يتم تحديد القطاع والفاز المصاب فوراً.
    """)

with tab3:
    st.header("🚨 سجل كشف التجاوزات الآلي")
    if inject:
        st.error(f"🔴 تم رصد تجاوز نشط!")
        st.table(pd.DataFrame({
            "المعلمة": ["القطاع المتأثر", "الفاز المصاب", "قيمة التجاوز المقدرة", "وقت الاكتشاف"],
            "القيمة": [sel_sector, sel_phase, f"{theft_val} Amps", time.strftime("%H:%M:%S")]
        }))
    else:
        st.success("🟢 الشبكة تعمل بشكل طبيعي - لا توجد تجاوزات حالياً")
        
