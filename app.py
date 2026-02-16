import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime
import base64

# إعدادات الصفحة
st.set_page_config(page_title="Anbar Grid Control Room", layout="wide")

# --- دالة تشغيل صوت الإنذار ---
def play_alarm():
    # صوت إنذار قصير (Base64)
    sound_html = f"""
        <audio autoplay>
            <source src="https://www.soundjay.com/buttons/beep-01a.mp3" type="audio/mpeg">
        </audio>
    """
    st.components.v1.html(sound_html, height=0)

# --- تهيئة البيانات (Session State) ---
if 'transformers' not in st.session_state:
    st.session_state.transformers = {
        f"محولة {i}": {"active": True, "reason": "", "history": []} for i in range(1, 5)
    }

# --- العنوان ---
st.title("📟 غرفة تحكم أحمال الأنبار الذكية")
st.markdown(f"**إشراف المهندس:** محمد نبيل | **التاريخ:** {datetime.now().strftime('%Y-%m-%d')}")

# --- القائمة الجانبية (Sidebar) ---
st.sidebar.header("🕹️ لوحة التحكم بالنظام")
protocol_mode = st.sidebar.toggle("تفعيل بروتوكول الحماية الذكي", value=True)
st.sidebar.divider()
max_temp = st.sidebar.slider("حد الحرارة الأقصى (C°)", 50, 100, 80)
max_load_pct = 90 # نسبة الفصل 90% كما طلبت

if st.sidebar.button("إعادة تشغيل كافة المحولات"):
    for t in st.session_state.transformers:
        st.session_state.transformers[t]["active"] = True
        st.session_state.transformers[t]["reason"] = ""

# --- معالجة البيانات ---
station_data = []

# عرض المحولات بشكل كروت (Cards) سريعة
cols = st.columns(4)

for idx, (name, state) in enumerate(st.session_state.transformers.items()):
    # توليد قراءات عشوائية (محاكاة للحساسات)
    voltage = np.random.uniform(215, 225)
    current = np.random.uniform(50, 150) if state["active"] else 0
    temp = np.random.uniform(40, 95) if state["active"] else 30
    resistance = 0.05
    losses = (current**2 * resistance) / 1000 # حساب الخسائر بالـ kW
    
    load_pct = (current / 150) * 100 # نسبة الحمل بالنسبة لـ 150 أمبير كحد أقصى
    
    # منطق البروتوكول (الفصل الآلي)
    status = "طبيعي ✅"
    if state["active"]:
        if protocol_mode:
            if load_pct >= max_load_pct:
                state["active"] = False
                state["reason"] = f"فصل حمل زائد ({load_pct:.1f}%)"
                play_alarm()
            elif temp >= max_temp:
                state["active"] = False
                state["reason"] = f"فصل حرارة عالية ({temp:.1f}°C)"
                play_alarm()
        
        if load_pct >= 80: status = "تحذير ⚠️"
        if load_pct >= 90: status = "خطر 🚩"
    else:
        status = "فصل (TRIPPED) ❌"

    # إضافة البيانات للجدول
    station_data.append({
        "المحطة": name,
        "الجهد (V)": f"{voltage:.1f}",
        "التيار (A)": f"{current:.1f}",
        "الحرارة (C°)": f"{temp:.1f}",
        "الخسائر (kW)": f"{losses:.3f}",
        "الحمل": f"{load_pct:.1f}%",
        "الحالة": status,
        "سبب الفصل": state["reason"]
    })

    # عرض شريط الضغط (Stress Bar) في الكروت
    with cols[idx]:
        st.subheader(name)
        st.metric("الحمل الحالي", f"{load_pct:.1f}%")
        st.progress(min(load_pct/100, 1.0)) # شريط الضغط
        if not state["active"]:
            st.error(f"انفصلت: {state['reason']}")

# --- عرض الجدول القديم المطور ---
st.divider()
st.subheader("📋 جدول القراءات اللحظية المرسل لغرفة التحكم")
df = pd.DataFrame(station_data)

# تنسيق الجدول ليظهر الألوان
def color_status(val):
    color = 'white'
    if 'خطر' in val or 'فصل' in val: color = '#ff4b4b'
    elif 'تحذير' in val: color = '#ffa500'
    elif 'طبيعي' in val: color = '#28a745'
    return f'background-color: {color}'

st.dataframe(df.style.applymap(color_status, subset=['الحالة']), use_container_width=True)

# --- ملاحظات النظام ---
st.divider()
col_info1, col_info2 = st.columns(2)
with col_info1:
    st.info(f"**وضع النظام:** {'بروتوكول الحماية مفعّل' if protocol_mode else 'وضع القراءة فقط (بدون بروتوكول)'}")
with col_info2:
    if not protocol_mode:
        st.warning("⚠️ تحذير: النظام الآن لا يفصل آلياً عند الخطر (البروتوكول معطل)!")

# تحديث الصفحة كل ثانية (Real-time)
time.sleep(1)
st.rerun()
