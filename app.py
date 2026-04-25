import streamlit as st
import pandas as pd
import numpy as np

# إعدادات الصفحة
st.set_page_config(page_title="Al-Anbar Smart Street", layout="wide")

# --- 1. التنسيق الجمالي (CSS) لجعل الواجهة احترافية ---
st.markdown("""
    <style>
    .node-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        border: 2px solid #e6e9ef;
    }
    .theft-node {
        background-color: #ffecec;
        border: 2px solid #ff4b4b;
        animation: blinker 1.5s linear infinite;
    }
    @keyframes blinker {
        50% { opacity: 0.6; }
    }
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. تهيئة البيانات ---
if 'theft_loc' not in st.session_state: st.session_state.theft_loc = "لا يوجد"
if 'step' not in st.session_state: st.session_state.step = 0

# استهلاك 5 بيوت (قراءات العدادات الشرعية بالأمبير)
legal_houses = {
    "بيت 1": 15, "بيت 2": 12, "بيت 3": 20, "بيت 4": 10, "بيت 5": 18
}
total_legal = sum(legal_houses.values())

# --- 3. القائمة الجانبية (لوحة التحكم الاحترافية) ---
with st.sidebar:
    st.header("⚡ التحكم بالمنظومة")
    if st.button("🔄 تحديث القراءات اللحظية", type="primary"):
        st.session_state.step += 1
    
    st.divider()
    st.subheader("🪝 افتعال تجاوز (للفحص)")
    options = ["لا يوجد", "بين المحولة وعامود 1", "بين عامود 1 و 2", "بين عامود 2 و 3", "بين عامود 3 و 4"]
    st.session_state.theft_loc = st.selectbox("اختر مكان التجاوز بدقة:", options)
    
    if st.button("🗑️ إعادة ضبط النظام"):
        st.session_state.theft_loc = "لا يوجد"
        st.rerun()

# --- 4. الحسابات الهندسية (القدرة المسحوبة vs المفروضة) ---
theft_value = 0
if st.session_state.theft_loc != "لا يوجد":
    theft_value = 45 # قيمة التجاوز بالأمبير

# القدرة الكلية المسحوبة من المحولة (التيار الفعلي)
transformer_supply = total_legal + theft_value + np.random.uniform(1, 3) # إضافة فاقد فني بسيط

# --- 5. عرض النتائج والتحليل (Header Metrics) ---
st.title("🏙️ مراقب شارع الأنبار الذكي")
col_m1, col_m2, col_m3 = st.columns(3)

with col_m1:
    st.metric("القدرة الخارجة من المحولة", f"{round(transformer_supply, 1)} A")
with col_m2:
    st.metric("مجموع استهلاك البيوت (الشرعي)", f"{total_legal} A")
with col_m3:
    diff = round(transformer_supply - total_legal, 1)
    status_color = "normal" if diff < 5 else "inverse"
    st.metric("الفارق (الضياعات/التجاوز)", f"{diff} A", delta=f"{diff} A", delta_color=status_color)

st.divider()

# --- 6. تمثيل الشارع (المحولة -> الأعمدة -> البيوت) ---
st.subheader("📍 الخريطة المرئية لتدفق الطاقة")

# إنشاء 5 أعمدة لتمثيل مسار الشارع
c1, c2, c3, c4, c5 = st.columns(5)

# دالة لرسم العنصر (Node)
def draw_node(col, title, icon, subtitle, is_theft=False):
    css_class = "node-card theft-node" if is_theft else "node-card"
    col.markdown(f"""
        <div class="{css_class}">
            <h3>{icon}</h3>
            <b>{title}</b><br>
            <small>{subtitle}</small>
        </div>
        """, unsafe_allow_html=True)

with c1:
    draw_node(c1, "المحولة الرئيسية", "⚡", "بداية التغذية")
    st.write("➡️")

with c2:
    is_hit = (st.session_state.theft_loc == "بين المحولة وعامود 1")
    draw_node(c2, "عامود 1", "🗼", "يغذي بيت 1", is_hit)
    st.caption(f"🏠 بيت 1: {legal_houses['بيت 1']}A")
    if is_hit: st.error("🪝 تجاوز هنا!")
    st.write("➡️")

with c3:
    is_hit = (st.session_state.theft_loc == "بين عامود 1 و 2")
    draw_node(c3, "عامود 2", "🗼", "يغذي بيت 2", is_hit)
    st.caption(f"🏠 بيت 2: {legal_houses['بيت 2']}A")
    if is_hit: st.error("🪝 تجاوز هنا!")
    st.write("➡️")

with c4:
    is_hit = (st.session_state.theft_loc == "بين عامود 2 و 3")
    draw_node(c4, "عامود 3", "🗼", "يغذي بيت 3 و 4", is_hit)
    st.caption(f"🏠 بيت 3+4: {legal_houses['بيت 3']+legal_houses['بيت 4']}A")
    if is_hit: st.error("🪝 تجاوز هنا!")
    st.write("➡️")

with c5:
    is_hit = (st.session_state.theft_loc == "بين عامود 3 و 4")
    draw_node(c5, "عامود 4", "🗼", "يغذي بيت 5", is_hit)
    st.caption(f"🏠 بيت 5: {legal_houses['بيت 5']}A")
    if is_hit: st.error("🪝 تجاوز هنا!")

st.divider()

# --- 7. التقرير التشخيصي النهائي ---
st.subheader("📝 تقرير المهندس المناوب")
col_rep1, col_rep2 = st.columns(2)

with col_rep1:
    st.info(f"""
    **مقارنة القدرة:**
    * المحولة تسحب حالياً: **{round(transformer_supply, 1)} أمبير**.
    * مجموع عدادات البيوت تسجل: **{total_legal} أمبير**.
    * نسبة الفاقد غير المفسر: **{round((diff/transformer_supply)*100, 1)}%**.
    """)

with col_rep2:
    if st.session_state.theft_loc != "لا يوجد":
        st.warning(f"""
        **تحديد الموقع:**
        تم رصد تجاوز مؤكد في المنطقة الواقعة **[{st.session_state.theft_loc}]**.
        
        **الإجراء المطلوب:**
        إرسال فرقة تفتيش لفحص الأسلاك الممتدة بين هاتين النقطتين.
        """)
    else:
        st.success("الشبكة تعمل بكفاءة عالية. لا توجد مؤشرات على وجود تجاوزات حالياً.")
    
