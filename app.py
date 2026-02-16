import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime

# إعدادات الصفحة لتكون عريضة ومنظمة
st.set_page_config(page_title="مركز سيطرة أحمال الأنبار", layout="wide")

# --- دالة تشغيل صوت الإنذار ---
def play_alarm():
    sound_html = """
        <audio autoplay>
            <source src="https://www.soundjay.com/buttons/beep-01a.mp3" type="audio/mpeg">
        </audio>
    """
    st.components.v1.html(sound_html, height=0)

# --- تهيئة البيانات في الذاكرة (Session State) ---
# أضفنا 'load_trend' لجعل الارتفاع تدريجي وليس عشوائي مفاجئ
if 'transformers' not in st.session_state:
    st.session_state.transformers = {
        f"محولة {i}": {
            "active": True, 
            "reason": "", 
            "current_load": np.random.uniform(50, 70), # تبدأ بحمل منخفض
            "temp": np.random.uniform(40, 50),
            "overload_counter": 0 # لضمان عدم الفصل اللحظي
        } for i in range(1, 5)
    }

# --- واجهة المستخدم الرئيسية ---
st.title("🔌 نظام السيطرة الذكي - محافظة الأنبار")
st.write(f"**إعداد المهندس:** محمد نبيل | **الموقع:** الرمادي - مركز السيطرة | **الوقت:** {datetime.now().strftime('%H:%M:%S')}")

# --- القائمة الجانبية ---
st.sidebar.header("🛠️ إعدادات المنظومة")
protocol_mode = st.sidebar.toggle("تفعيل بروتوكول الحماية (الفصل الآلي)", value=True)
reset_btn = st.sidebar.button("إعادة تشغيل المنظومة بالكامل")

if reset_btn:
    for name in st.session_state.transformers:
        st.session_state.transformers[name] = {
            "active": True, "reason": "", "current_load": 60, "temp": 45, "overload_counter": 0
        }
    st.rerun()

# --- معالجة البيانات والمحاكاة ---
max_capacity = 150.0  # الأمبير الأقصى
threshold = 0.90      # 90% فصل
data_for_table = []

# تحديث القراءات لكل محولة
for name, data in st.session_state.transformers.items():
    if data["active"]:
        # جعل الحمل يرتفع تدريجياً أو ينخفض بشكل واقعي
        change = np.random.uniform(-5, 12) # ميل للزيادة أكثر
        data["current_load"] = max(20, min(160, data["current_load"] + change))
        data["temp"] = max(30, min(100, data["temp"] + (change * 0.2)))
        
        load_pct = (data["current_load"] / max_capacity) * 100
        losses = (data["current_load"]**2 * 0.05) / 1000 # حساب الخسائر kW
        
        # منطق الفصل (يجب أن يستمر الخطر لـ 3 دورات قبل الفصل)
        status = "طبيعي ✅"
        if load_pct >= 90 or data["temp"] >= 85:
            status = "خطر 🚩"
            if protocol_mode:
                data["overload_counter"] += 1
                if data["overload_counter"] >= 3: # "خليها شوي تشتغل وبعدين تفصل"
                    data["active"] = False
                    data["reason"] = "تجاوز حد الـ 90% (فصل آلي)"
                    play_alarm()
            else:
                status = "خطر (تحذير يدوي) ⚠️"
        elif load_pct >= 75:
            status = "تحذير ⚠️"
            data["overload_counter"] = 0
        else:
            data["overload_counter"] = 0
    else:
        # المحولة مفصولة
        load_pct = 0
        losses = 0
        status = "فصل (TRIPPED) ❌"

    # إضافة البيانات للجدول
    data_for_table.append({
        "اسم المحطة": name,
        "التيار (A)": f"{data['current_load']:.1f}",
        "الحرارة (C°)": f"{data['temp']:.1f}",
        "نسبة الحمل": f"{load_pct:.1f}%",
        "الخسائر (kW)": f"{losses:.3f}",
        "حالة النظام": status,
        "ملاحظات": data["reason"]
    })

# --- عرض النتائج بصرياً ---

# 1. كروت العرض (Cards) مع شريط الضغط
cols = st.columns(4)
for i, name in enumerate(st.session_state.transformers):
    with cols[i]:
        d = st.session_state.transformers[name]
        load_val = (d["current_load"]/max_capacity)
        st.subheader(name)
        st.metric("الحمل", f"{int(load_val*100)}%")
        # شريط الضغط يتغير لونه حسب الحمل
        bar_color = "green" if load_val < 0.75 else "orange" if load_val < 0.9 else "red"
        st.progress(min(load_val, 1.0))
        if not d["active"]:
            st.error(f"انفصلت: {d['reason']}")

st.divider()

# 2. الجدول الكبير والمنظم (The Main Table)
st.subheader("📋 سجل القراءات اللحظية الموحد")

df = pd.DataFrame(data_for_table)

# دالة لتنسيق ألوان الجدول بشكل احترافي
def style_status(val):
    if 'طبيعي' in val: color = '#d4edda' # أخضر فاتح
    elif 'تحذير' in val: color = '#fff3cd' # أصفر فاتح
    elif 'خطر' in val: color = '#f8d7da' # أحمر فاتح
    elif 'فصل' in val: color = '#721c24; color: white' # ماروني/أحمر غامق
    else: color = 'white'
    return f'background-color: {color}'

# عرض الجدول بحجم كبير وكامل العرض
st.table(df.style.applymap(style_status, subset=['حالة النظام']))

# --- معلومات إضافية أسفل الشاشة ---
st.divider()
c1, c2, c3 = st.columns(3)
with c1:
    st.info("**معلومة:** يتم حساب الخسائر بناءً على ممانعة الأسلاك المقدرة بـ 0.05 أوم.")
with c2:
    st.info("**البروتوكول:** مضبوط للفصل بعد 3 ثوانٍ من تجاوز الحمل لنسبة 90%.")
with c3:
    if not protocol_mode:
        st.warning("**تنبيه:** وضع الحماية معطل، المحولات لن تفصل آلياً!")

# تحديث تلقائي كل ثانية
time.sleep(1)
st.rerun()
    
