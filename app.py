import streamlit as st
import pandas as pd
import time
import random
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام شبكة الرمادي الذكي", layout="wide")

# 2. تهيئة الذاكرة (بدل الملفات)
if 'history' not in st.session_state:
    st.session_state.history = []
if 'collapsed' not in st.session_state:
    st.session_state.collapsed = False

# 3. إعدادات محطات الرمادي (5 محطات)
STATIONS = {
    "مستشفى الرمادي التعليمي": {"max": 1000, "priority": 1},
    "معمل زجاج الرمادي": {"max": 1200, "priority": 2},
    "محطة ماء الورار": {"max": 800, "priority": 3},
    "جامعة الأنبار": {"max": 600, "priority": 4},
    "حي التأميم (سكني)": {"max": 500, "priority": 5}
}

# دالة توليد البيانات
def add_reading(name, current):
    # إذا النظام منهار، لا تسجل قراءات جديدة
    if st.session_state.collapsed: return

    limit = STATIONS[name]["max"]
    
    # تحديد الحالة
    if current < (limit * 0.8):
        status, level = "🟢 مستقر", 1
    elif (limit * 0.8) <= current < (limit * 0.95):
        status, level = "🟡 تنبيه", 2
    else:
        status, level = "🔴 خطر", 3

    entry = {
        "المنشأة": name,
        "التيار (A)": current,
        "الحالة": status,
        "الوقت": datetime.now().strftime("%H:%M:%S"),
        "timestamp": time.time(),
        "level": level,
        "p": STATIONS[name]["priority"]
    }
    
    # الإضافة للذاكرة وحفظ آخر 50 سجل فقط
    st.session_state.history.insert(0, entry) # الأحدث في البداية
    if len(st.session_state.history) > 50:
        st.session_state.history = st.session_state.history[:50]

# --- الواجهة الجانبية ---
with st.sidebar:
    st.title("⚡ تحكم الشبكة")
    protocol = st.toggle("تفعيل بروتوكول الحماية", value=True)
    
    st.write("---")
    if st.button("🗑️ إعادة ضبط النظام (Reset)"):
        st.session_state.history = []
        st.session_state.collapsed = False
        st.rerun()

# --- تقسيم الشاشة ---
col_control, col_monitor = st.columns([1, 2])

# === الجزء 1: لوحة التحكم (اليسار) ===
with col_control:
    st.header("🕹️ التحكم بالأحمال")
    
    # زر محاكاة الهجوم
    if st.button("🔥 ضغط عالي مفاجئ (Attack)"):
        if not protocol:
            st.session_state.collapsed = True
            st.rerun()
        else:
            # البروتوكول يمتص الهجوم
            for name in STATIONS:
                add_reading(name, random.randint(int(STATIONS[name]["max"]*0.9), int(STATIONS[name]["max"]*1.2)))
            st.toast("✅ تم تفعيل البروتوكول وحماية الشبكة من الانهيار!")

    st.write("---")
    st.write("**التحكم اليدوي (Sliders):**")
    
    # شرائط التحكم
    for name in STATIONS:
        limit = STATIONS[name]["max"]
        # استخدام مفتاح فريد لكل شريط
        val = st.slider(f"{name}", 0, int(limit*1.3), value=int(limit*0.5), key=f"slider_{name}")
        
        # كشف التغيير وإرسال البيانات فوراً
        if st.session_state.get(f"last_{name}") != val:
            add_reading(name, val)
            st.session_state[f"last_{name}"] = val
            # تحديث الصفحة لعرض التغيير فوراً في الجدول
            # نستخدم sleep صغير جداً لمنع التعليق
            time.sleep(0.05)
            st.rerun()

# === الجزء 2: شاشة المراقبة (اليمين) ===
with col_monitor:
    st.header("🖥️ مركز المراقبة")

    # 1. شاشة الانهيار
    if st.session_state.collapsed:
        st.error("⚠️ SYSTEM COLLAPSE ⚠️")
        st.markdown("""
            <div style='background-color:black; color:red; padding:20px; text-align:center; font-size:24px;'>
            <b>انهيار الشبكة بالكامل</b><br>
            توقف السيرفر عن العمل بسبب الحمل الزائد<br>
            (Buffer Overflow)
            </div>
        """, unsafe_allow_html=True)
    
    # 2. العرض الطبيعي
    else:
        if len(st.session_state.history) == 0:
            st.info("بانتظار البيانات... حرك الأشرطة لبدء العمل.")
        else:
            df = pd.DataFrame(st.session_state.history)

            # --- منطق البروتوكول ---
            if protocol:
                # ترتيب: الخطر (3) أولاً -> ثم الأهمية (1 مستشفى) -> ثم الوقت
                df = df.sort_values(by=["level", "p", "timestamp"], ascending=[False, True, False])
                st.success("✅ البروتوكول يعمل: الأولوية للمستشفى والحالات الخطرة.")
            else:
                # ترتيب زمني فقط (فوضى)
                df = df.sort_values(by="timestamp", ascending=False)
                st.warning("⚠️ تحذير: النظام يعمل بدون حماية (FIFO Mode).")

            # الرسم البياني
            st.line_chart(df.pivot_table(index='الوقت', columns='المنشأة', values='التيار (A)'), height=250)

            # الجدول الملون
            def color_row(row):
                if row['level'] == 3: return ['background-color: #8b0000; color: white'] * len(row)
                if row['level'] == 2: return ['background-color: #705d00; color: white'] * len(row)
                return [''] * len(row)

            st.dataframe(
                df[['المنشأة', 'التيار (A)', 'الحالة', 'الوقت', 'level']].style.apply(color_row, axis=1),
                use_container_width=True,
                height=400,
                column_config={"level": None} # إخفاء عمود المستوى
        )
            
