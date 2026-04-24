import streamlit as st
import pandas as pd
import numpy as np

# إعدادات الصفحة
st.set_page_config(page_title="Al-Anbar Smart Grid - Full System", layout="wide")

# --- 1. تهيئة الذاكرة (بدون حلقات لا نهائية) ---
if 'transformers' not in st.session_state:
    # تهيئة 5 محطات وتكون جميعها قيد التشغيل مبدئياً
    st.session_state.transformers = {f"محطة {i}": {"active": True} for i in range(1, 6)}
if 'time_step' not in st.session_state: 
    st.session_state.time_step = 0

# --- 2. واجهة العناوين ---
st.title("⚡ نظام إدارة شبكة الأنبار الذكية (SCADA)")
st.markdown("### **التحكم اللحظي بالمحطات، المراقبة التفصيلية، وكشف التجاوزات**")

# --- 3. القائمة الجانبية (محاكاة وتحديث) ---
st.sidebar.header("🕹️ لوحة المحاكاة والتحكم")

if st.sidebar.button("🔄 تحديث القراءات (سحب بيانات جديدة)", use_container_width=True):
    st.session_state.time_step += 1

st.sidebar.divider()
st.sidebar.header("⚠️ محاكاة التجاوزات (السرقة)")
st.sidebar.write("اختر المحطة التي سيتم وضع حمل غير قانوني على خطها:")
target_theft = st.sidebar.selectbox("موقع التجاوز:", ["لا يوجد تجاوز"] + list(st.session_state.transformers.keys()))

# --- 4. أزرار التشغيل والإطفاء (وحدة السيطرة) ---
st.subheader("🎛️ وحدة السيطرة المركزية (التشغيل والفصل)")
cols = st.columns(5)
for idx, (name, state) in enumerate(st.session_state.transformers.items()):
    with cols[idx]:
        if state["active"]:
            # زر الإطفاء
            if st.button(f"🔴 فصل {name}", key=f"off_{name}"):
                st.session_state.transformers[name]["active"] = False
                st.rerun() # تحديث الصفحة فقط عند الضغط
        else:
            # زر التشغيل
            if st.button(f"🟢 تشغيل {name}", key=f"on_{name}"):
                st.session_state.transformers[name]["active"] = True
                st.rerun()

st.divider()

# --- 5. توليد البيانات وخوارزمية التشخيص ---
data = []
alerts_triggered = []

for name, state in st.session_state.transformers.items():
    if state["active"]:
        # القراءات الطبيعية
        v = int(np.random.uniform(215, 226))
        pf = round(np.random.uniform(0.88, 0.95), 2)
        expected_i = int(90 + 20 * np.sin(st.session_state.time_step)) # تيار متغير مع الوقت
        i_val = int(expected_i + np.random.uniform(-5, 10))

        # حقن التجاوز إذا تم اختياره
        is_theft = (target_theft == name)
        if is_theft:
            i_val += int(np.random.uniform(45, 65)) # سحب تيار عالي جداً فجأة
            pf -= np.random.uniform(0.12, 0.18)      # هبوط في معامل القدرة
            v -= int(np.random.uniform(10, 18))      # هبوط حاد في الفولتية

        # حسابات القدرة ونسبة الحمل
        p_kw = int((v * i_val * pf) / 1000)
        load_pct = int((i_val / 150) * 100)

        # تحديد الحالة والأولوية (الفرز)
        if is_theft:
            status, prio = "🪝 تجاوز مكتشف", 1
            alerts_triggered.append(f"⚠️ إنذار: هبوط فولتية غير طبيعي ({v}V) وسحب تيار عالي في {name}. اشتباه بربط غير قانوني!")
        elif load_pct >= 95:
            status, prio = "🚨 حمل زائد", 2
        elif load_pct >= 80:
            status, prio = "⚠️ تنبيه ذروة", 3
        else:
            status, prio = "✅ طبيعي", 4
    else:
        # حالة المحطة المفصولة
        v, i_val, p_kw, pf, load_pct, status, prio = 0, 0, 0, 0, 0, "🛑 مفصول", 5

    data.append({
        "المحطة": name, "V": v, "I (A)": i_val, "P (kW)": p_kw,
        "PF": pf, "Load %": f"{load_pct}%", "تفاصيل الحالة": status, "p": prio
    })

# بناء الجدول وفرزه ديناميكياً بناءً على الأولوية
df = pd.DataFrame(data)
df = df.sort_values(by="p").drop(columns=["p"])

# --- 6. نظام الإشعارات ---
if alerts_triggered:
    st.subheader("🔔 تنبيهات الشبكة")
    for a in alerts_triggered:
        st.error(a)

# --- 7. الجدول التفصيلي ---
st.subheader("📋 جدول تفاصيل القراءات (فرز ديناميكي)")

def style_row(val):
    if '🪝' in str(val): return 'background-color: #800080; color: white'
    if '🚨' in str(val): return 'background-color: #ff4b4b; color: white'
    if '⚠️' in str(val): return 'background-color: #fff3cd'
    if '✅' in str(val): return 'background-color: #d4edda'
    if '🛑' in str(val): return 'background-color: #721c24; color: white'
    return ''

st.table(df.style.map(style_row, subset=['تفاصيل الحالة']))
