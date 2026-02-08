import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# --- إعدادات الصفحة ---
st.set_page_config(page_title="نظام طاقة الأنبار - النسخة المستقرة", layout="wide")

DB_FILE = "anbar_system_v3.json"

STATIONS = {
    "مستشفى الرمادي التعليمي": {"max": 1000, "priority": 1},
    "معمل زجاج الرمادي": {"max": 1200, "priority": 2},
    "محطة مياه الورار": {"max": 900, "priority": 3},
    "جامعة الأنبار": {"max": 700, "priority": 4},
    "حي التأميم (سكني)": {"max": 500, "priority": 5}
}

# --- إدارة الملف والبيانات ---
def load_data():
    if not os.path.exists(DB_FILE):
        return {"entries": [], "load_val": 0, "collapsed": False}
    try:
        with open(DB_FILE, "r", encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"entries": [], "load_val": 0, "collapsed": False}

def save_data(data):
    with open(DB_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def update_system(new_readings, protocol_on):
    data = load_data()
    if data["collapsed"]: return
    
    # إضافة البيانات
    data["entries"].extend(new_readings)
    data["entries"] = data["entries"][-50:] # الحفاظ على آخر 50 سجل فقط
    
    # حساب الضغط: كل حزمة بيانات تزيد الضغط
    incoming_stress = len(new_readings) * 4.0 
    
    if protocol_on:
        # البروتوكول يمتص الصدمة ويبرد النظام
        data["load_val"] += (incoming_stress * 0.1)
        data["load_val"] = max(0, data["load_val"] - 5) # تبريد مستمر
    else:
        # بدون بروتوكول: تراكم كامل للضغط
        data["load_val"] += incoming_stress
    
    # فحص الانهيار
    if data["load_val"] >= 100:
        data["load_val"] = 100
        data["collapsed"] = True
    
    save_data(data)

# --- الواجهة الجانبية ---
st.sidebar.title("⚡ تحكم طاقة الأنبار")
page = st.sidebar.radio("القائمة:", ["🕹️ غرفة التحكم", "🖥️ شاشة المراقبة"])
protocol_active = st.sidebar.toggle("🛡️ تفعيل بروتوكول الحماية", value=False)

if st.sidebar.button("♻️ تصفير النظام (Reset)"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.rerun()

# ==========================================
# صفحة التحكم (Manual & Auto)
# ==========================================
if page == "🕹️ غرفة التحكم":
    st.title("🕹️ وحدة التحكم والإرسال")
    
    state = load_data()
    if state["collapsed"]:
        st.error("❌ النظام منهار تماماً (Blackout). قم بعمل Reset من القائمة الجانبية.")
    else:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("🔧 التحكم اليدوي المباشر")
            for name, specs in STATIONS.items():
                val = st.slider(f"تيار {name}", 0, 1500, key=f"sl_{name}")
                # إذا حرك المستخدم السلايدر، نرسل بيانات ونزيد الضغط
                if st.button(f"إرسال قراءة {name}", key=f"btn_{name}"):
                    status = "🔴 خطر" if val > specs['max'] else "🟢 مستقر"
                    reading = [{
                        "المنشأة": name, "التيار (A)": val, "الحالة": status,
                        "الوقت": datetime.now().strftime("%H:%M:%S"),
                        "timestamp": time.time(), "level": 3 if val > specs['max'] else 1
                    }]
                    update_system(reading, protocol_active)
                    st.toast(f"تم إرسال بيانات {name}")

        with col2:
            st.subheader("🚀 البث التلقائي (الضغط المكثف)")
            run_auto = st.checkbox("تشغيل ضخ البيانات المستمر")
            if run_auto:
                placeholder = st.empty()
                while run_auto:
                    current_state = load_data()
                    if current_state["collapsed"]: 
                        st.rerun()
                        break
                    
                    # إنشاء بيانات عشوائية لكل المحطات
                    batch = []
                    for name in STATIONS:
                        v = random.randint(400, 1300)
                        batch.append({
                            "المنشأة": name, "التيار (A)": v, "الحالة": "📡 بث",
                            "الوقت": datetime.now().strftime("%H:%M:%S"),
                            "timestamp": time.time(), "level": 1
                        })
                    
                    update_system(batch, protocol_active)
                    with placeholder.container():
                        st.write(f"✅ جاري الضخ... الضغط الحالي: {current_state['load_val']:.1f}%")
                    time.sleep(1)

# ==========================================
# صفحة المراقبة
# ==========================================
else:
    st.title("🖥️ شاشة المراقبة المركزية")
    
    mon_placeholder = st.empty()
    
    while True:
        state = load_data()
        
        with mon_placeholder.container():
            if state["collapsed"]:
                st.markdown("""
                <div style='background-color:#1a0000; padding:100px; border: 10px solid red; text-align:center; border-radius:20px;'>
                    <h1 style='color:red; font-size: 100px;'>🚨 CRASH 🚨</h1>
                    <h2 style='color:white;'>نظام الأنبار خارج الخدمة</h2>
                    <p style='color:#ff6666;'>تجاوز ضغط البيانات الحد المسموح (100%)</p>
                </div>
                """, unsafe_allow_html=True)
                break
            
            # عرض العداد
            val = state["load_val"]
            color = "green" if val < 50 else "orange" if val < 85 else "red"
            st.markdown(f"### ضغط السيرفر الحالي: :{color}[{val:.1f}%]")
            st.progress(min(val/100, 1.0))
            
            if not state["entries"]:
                st.info("بانتظار استقبال البيانات من غرفة التحكم...")
            else:
                df = pd.DataFrame(state["entries"])
                
                # رسم بياني
                chart_data = df.pivot_table(index='الوقت', columns='المنشأة', values='التيار (A)').ffill()
                st.line_chart(chart_data)
                
                # الجدول
                st.table(df.tail(10)[["المنشأة", "التيار (A)", "الحالة", "الوقت"]])
                
        time.sleep(1)
                
