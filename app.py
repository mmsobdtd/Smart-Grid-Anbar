import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# إعداد الصفحة
st.set_page_config(page_title="نظام طاقة الأنبار", layout="wide")

# ملفات الحالة (يجب أن تكون منفصلة لضمان السرعة)
STATE_FILE = "system_state.json"

# إعدادات المحطات
STATIONS = {
    "مستشفى الرمادي": {"priority": 1},
    "معمل الزجاج": {"priority": 2},
    "محطة الورار": {"priority": 3},
    "جامعة الأنبار": {"priority": 4},
    "حي التأميم": {"priority": 5}
}

# --- دوال الحالة ---
def get_state():
    if not os.path.exists(STATE_FILE):
        return {"load": 0, "crashed": False, "streaming": False}
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {"load": 0, "crashed": False, "streaming": False}

def save_state(state):
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)
    except:
        pass

# --- القائمة الجانبية ---
st.sidebar.title("⚡ تحكم النظام")
page = st.sidebar.radio("الصفحات:", ["لوحة التشغيل", "شاشة المراقبة"])
st.sidebar.markdown("---")

# زر البروتوكول (هو المفتاح)
protocol_on = st.sidebar.toggle("تفعيل الحماية (Protocol)", value=True)

# زر التصفير
if st.sidebar.button("♻️ تصفير النظام (Reset)"):
    if os.path.exists(STATE_FILE): os.remove(STATE_FILE)
    st.rerun()

# ==========================================
# الصفحة 1: لوحة التشغيل
# ==========================================
if page == "لوحة التشغيل":
    st.title("🕹️ تشغيل البث")
    
    state = get_state()
    
    # زر واحد للتشغيل
    if st.checkbox("تشغيل النظام", value=state["streaming"]):
        state["streaming"] = True
        save_state(state)
        st.success("✅ النظام يعمل! اذهب لشاشة المراقبة الآن.")
    else:
        state["streaming"] = False
        save_state(state)
        st.info("النظام متوقف.")

# ==========================================
# الصفحة 2: شاشة المراقبة (حيث يحدث الانهيار)
# ==========================================
else:
    st.title("🖥️ مراقبة الشبكة")
    
    placeholder = st.empty()
    
    # حلقة التحديث
    while True:
        state = get_state()
        
        # 1. إذا النظام منهار أصلاً
        if state["crashed"]:
            with placeholder.container():
                st.markdown("""
                <div style="background-color:black; color:red; padding:40px; text-align:center;">
                    <h1 style="font-size:80px;">💀 SYSTEM FAILURE</h1>
                    <h2>الشبكة انهارت بالكامل</h2>
                    <p>Load reached 100% due to protocol failure.</p>
                </div>
                """, unsafe_allow_html=True)
                
            time.sleep(2)
            continue # يبقى في الشاشة السوداء

        # 2. إذا النظام يعمل
        if state["streaming"]:
            # === منطق الانهيار الحتمي ===
            if not protocol_on:
                # إذا البروتوكول طافي: ارفع الضغط بسرعة جنونية (+25% كل ثانية)
                state["load"] += 25
            else:
                # إذا البروتوكول شغال: نزل الضغط
                state["load"] = 10
            
            # فحص الحد الأقصى
            if state["load"] >= 100:
                state["load"] = 100
                state["crashed"] = True
            
            save_state(state)
            
            # === العرض ===
            with placeholder.container():
                # شريط الضغط
                load_val = state["load"]
                color = "green" if load_val < 50 else "red"
                st.markdown(f"### 🔥 ضغط السيرفر: :{color}[{load_val}%]")
                st.progress(load_val / 100)
                
                if protocol_on:
                    st.success("✅ البروتوكول فعال: الضغط مستقر.")
                    # جدول وهمي يظهر البيانات مرتبة
                    data = []
                    for name in STATIONS:
                         data.append({"المنشأة": name, "الحالة": "مستقر", "التيار": random.randint(400, 800)})
                    st.dataframe(pd.DataFrame(data))
                else:
                    st.error("⚠️ تحذير: البروتوكول معطل! الانهيار وشيك!")
                    # جدول وهمي يظهر بيانات عشوائية
                    data = []
                    for name in STATIONS:
                         data.append({"المنشأة": name, "الحالة": "خطر 🔴", "التيار": random.randint(900, 1500)})
                    st.dataframe(pd.DataFrame(data))

        else:
            with placeholder.container():
                st.info("بانتظار التشغيل من اللوحة...")
        
        time.sleep(1)
