import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# --- إعدادات الصفحة ---
st.set_page_config(page_title="نظام طاقة الأنبار - موازنة الأحمال", layout="wide")

DB_FILE = "anbar_system_v25.json"

STATIONS = {
    "مستشفى الرمادي التعليمي": {"max": 1000, "priority": 1},
    "معمل زجاج الرمادي": {"max": 1200, "priority": 2},
    "محطة مياه الورار": {"max": 900, "priority": 3},
    "جامعة الأنبار": {"max": 700, "priority": 4},
    "حي التأميم (سكني)": {"max": 500, "priority": 5}
}

# --- إدارة البيانات ---
def load_data():
    if not os.path.exists(DB_FILE):
        return {"entries": [], "load_val": 0.0, "collapsed": False}
    try:
        with open(DB_FILE, "r", encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"entries": [], "load_val": 0.0, "collapsed": False}

def save_data(data):
    # كبح القيمة برمجياً لضمان عدم خروجها عن النطاق
    data["load_val"] = float(max(0.0, min(data["load_val"], 100.0)))
    with open(DB_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def apply_system_logic(new_readings, protocol_on):
    data = load_data()
    if data["collapsed"]: return
    
    if new_readings:
        data["entries"].extend(new_readings)
        data["entries"] = data["entries"][-40:]
    
    if protocol_on:
        # --- منطق البروتوكول الجديد (الاستقرار عند 25%) ---
        target = 25.0
        if data["load_val"] > (target + 2):
            data["load_val"] -= 8.0 # تفريغ سريع للوصول للهدف
        elif data["load_val"] < (target - 2):
            data["load_val"] += 2.0 # رفع بسيط لو نزل تحت الـ 25
        else:
            # تذبذب طبيعي بسيط حول الـ 25 (بين 23% و 27%)
            data["load_val"] = random.uniform(23.0, 27.0)
    else:
        # --- بدون بروتوكول ---
        if new_readings:
            data["load_val"] += len(new_readings) * 2.5
        else:
            data["load_val"] -= 4.0 # تبريد تلقائي عند التوقف
    
    if data["load_val"] >= 100.0:
        data["load_val"] = 100.0
        data["collapsed"] = True
    
    save_data(data)

# --- الواجهة ---
st.sidebar.title("⚡ مركز سيطرة الرمادي")
page = st.sidebar.radio("القائمة الرئيسية:", ["🕹️ غرفة التحكم", "🖥️ شاشة المراقبة"])
protocol_active = st.sidebar.toggle("🛡️ بروتوكول الحماية النشط", value=False)

if st.sidebar.button("♻️ إعادة ضبط النظام (Reset)"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.rerun()

# ==========================================
# صفحة التحكم
# ==========================================
if page == "🕹️ غرفة التحكم":
    st.title("🕹️ وحدة الإرسال والتحكم الميداني")
    state = load_data()
    if state["collapsed"]:
        st.error("🚨 انقطاع كامل! النظام منهار. يرجى التصفير.")
    else:
        apply_system_logic([], protocol_active)
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🔧 التحكم اليدوي")
            for name, specs in STATIONS.items():
                val = st.slider(f"تيار {name}", 0, 1500, value=int(specs['max']*0.7), key=f"s_{name}")
                if st.button(f"إرسال قراءة {name}", key=f"b_{name}"):
                    status = "🔴 خطر" if val > specs['max'] * 0.98 else "🟡 تنبيه" if val > specs['max'] * 0.85 else "🟢 مستقر"
                    apply_system_logic([{"المنشأة": name, "التيار (A)": val, "الحالة": status, "الوقت": datetime.now().strftime("%H:%M:%S"), "timestamp": time.time()}], protocol_active)
                    st.toast(f"بث بيانات {name}")
        with col2:
            st.subheader("🚀 البث التلقائي")
            run_auto = st.checkbox("تشغيل التدفق المستمر للبيانات")
            auto_placeholder = st.empty()
            while run_auto:
                curr = load_data()
                if curr["collapsed"]: st.rerun(); break
                batch = [{"المنشأة": n, "التيار (A)": random.randint(400, 1100), "الحالة": "📡 بث", "الوقت": datetime.now().strftime("%H:%M:%S"), "timestamp": time.time()} for n in STATIONS]
                apply_system_logic(batch, protocol_active)
                auto_placeholder.info(f"📡 الضخ مستمر... الضغط: {curr['load_val']:.1f}%")
                time.sleep(1)

# ==========================================
# صفحة المراقبة
# ==========================================
else:
    st.title("🖥️ شاشة المراقبة المركزية - الأنبار")
    mon_placeholder = st.empty()
    while True:
        apply_system_logic([], protocol_active)
        state = load_data()
        with mon_placeholder.container():
            if state["collapsed"]:
                st.markdown("<div style='background-color:black; padding:50px; border: 15px solid red; text-align:center;'><h1 style='color:red;'>🚨 SYSTEM FAILURE 🚨</h1><h2 style='color:white;'>انهيار المنظومة</h2></div>", unsafe_allow_html=True)
                break
            
            curr_val = float(state["load_val"])
            # صمام أمان لمؤشر التقدم
            safe_progress = max(0.0, min(curr_val / 100.0, 1.0))
            
            p_color = "red" if curr_val > 80 else "orange" if curr_val > 50 else "green"
            st.markdown(f"### حالة ضغط السيرفر: :{p_color}[{curr_val:.1f}%]")
            st.progress(safe_progress)
            
            if state["entries"]:
                df = pd.DataFrame(state["entries"])
                st.subheader("📊 مخطط أحمال الشبكة")
                chart_data = df.pivot_table(index='الوقت', columns='المنشأة', values='التيار (A)').ffill()
                st.line_chart(chart_data)
                
                def style_rows(row):
                    if "🔴" in str(row['الحالة']): return ['background-color: #8b0000; color: white'] * len(row)
                    if "🟡" in str(row['الحالة']): return ['background-color: #705d00; color: white'] * len(row)
                    return ['background-color: #003311; color: white'] * len(row)

                st.dataframe(df.tail(15).style.apply(style_rows, axis=1), use_container_width=True)
        time.sleep(1)
                
