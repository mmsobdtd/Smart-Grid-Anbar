import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# --- إعدادات الصفحة ---
st.set_page_config(page_title="نظام طاقة الأنبار - النسخة الذكية", layout="wide")

DB_FILE = "anbar_system_v5.json"

STATIONS = {
    "مستشفى الرمادي التعليمي": {"max": 1000, "priority": 1},
    "معمل زجاج الرمادي": {"max": 1200, "priority": 2},
    "محطة مياه الورار": {"max": 900, "priority": 3},
    "جامعة الأنبار": {"max": 700, "priority": 4},
    "حي التأميم (سكني)": {"max": 500, "priority": 5}
}

# --- إدارة البيانات والنظام ---
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

# دالة التبريد التلقائي (تُستدعى دائماً لتخفيف الضغط عند التوقف)
def apply_cooling():
    data = load_data()
    if data["collapsed"]: return data
    
    # ينخفض الضغط بمقدار 3% تلقائياً في كل دورة إذا لم يكن هناك ضغط جديد
    if data["load_val"] > 0:
        data["load_val"] = max(0, data["load_val"] - 3.0)
        save_data(data)
    return data

def update_system(new_readings, protocol_on):
    data = load_data()
    if data["collapsed"]: return
    
    data["entries"].extend(new_readings)
    data["entries"] = data["entries"][-40:]
    
    # حساب الضغط الناتج عن البيانات الجديدة
    incoming_stress = len(new_readings) * 2.0 
    
    if protocol_on:
        # إذا البروتوكول فعال: الضغط يرتفع ببطء شديد ويقف عند حد أمان 80%
        new_val = data["load_val"] + (incoming_stress * 0.2)
        data["load_val"] = min(new_val, 80.0) 
    else:
        # بدون بروتوكول: الضغط يرتفع بحرية حتى الانهيار
        data["load_val"] += incoming_stress
    
    if data["load_val"] >= 100:
        data["load_val"] = 100
        data["collapsed"] = True
    
    save_data(data)

# --- واجهة المستخدم ---
st.sidebar.title("⚡ تحكم طاقة الأنبار")
page = st.sidebar.radio("القائمة:", ["🕹️ غرفة التحكم", "🖥️ شاشة المراقبة"])
protocol_active = st.sidebar.toggle("🛡️ تفعيل بروتوكول الحماية", value=False)

if st.sidebar.button("♻️ تصفير النظام (Reset)"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.rerun()

# ==========================================
# صفحة التحكم
# ==========================================
if page == "🕹️ غرفة التحكم":
    st.title("🕹️ وحدة الإرسال الميداني")
    
    state = load_data()
    if state["collapsed"]:
        st.error("❌ النظام منهار! يرجى عمل Reset.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🔧 إرسال يدوي")
            for name, specs in STATIONS.items():
                val = st.slider(f"تيار {name}", 0, 1500, value=int(specs['max']*0.7), key=f"s_{name}")
                if st.button(f"بث قراءة {name}", key=f"b_{name}"):
                    status = "🔴 خطر" if val > specs['max'] * 0.98 else "🟡 تنبيه" if val > specs['max'] * 0.85 else "🟢 مستقر"
                    level = 3 if "🔴" in status else 2 if "🟡" in status else 1
                    update_system([{"المنشأة": name, "التيار (A)": val, "الحالة": status, "الوقت": datetime.now().strftime("%H:%M:%S"), "timestamp": time.time(), "level": level}], protocol_active)
                    st.toast(f"تم إرسال {name}")

        with col2:
            st.subheader("🚀 بث تلقائي")
            run_auto = st.checkbox("تشغيل التدفق المستمر")
            auto_placeholder = st.empty()
            while run_auto:
                curr = load_data()
                if curr["collapsed"]: st.rerun(); break
                
                batch = []
                for name, specs in STATIONS.items():
                    v = random.randint(int(specs['max']*0.5), int(specs['max']*1.1))
                    status = "🔴 خطر" if v > specs['max'] * 0.98 else "🟡 تنبيه" if v > specs['max'] * 0.85 else "🟢 مستقر"
                    batch.append({"المنشأة": name, "التيار (A)": v, "الحالة": status, "الوقت": datetime.now().strftime("%H:%M:%S"), "timestamp": time.time(), "level": 1})
                
                update_system(batch, protocol_active)
                auto_placeholder.info(f"📡 جاري البث... الضغط الحالي: {curr['load_val']:.1f}%")
                time.sleep(1)

# ==========================================
# صفحة المراقبة
# ==========================================
else:
    st.title("🖥️ شاشة المراقبة والبيانات")
    mon_placeholder = st.empty()
    
    while True:
        # تفعيل التبريد التلقائي في كل دورة تحديث للشاشة
        state = apply_cooling()
        
        with mon_placeholder.container():
            if state["collapsed"]:
                st.markdown("<div style='background-color:black; padding:50px; border: 15px solid red; text-align:center;'><h1 style='color:red;'>⚠️ SYSTEM FAILURE ⚠️</h1><h2 style='color:white;'>انهيار السيرفر - الضغط 100%</h2></div>", unsafe_allow_html=True)
                break
            
            val = state["load_val"]
            p_color = "red" if val > 80 else "orange" if val > 50 else "green"
            st.markdown(f"### مؤشر ضغط المنظومة: :{p_color}[{val:.1f}%]")
            st.progress(min(val/100, 1.0))
            
            if state["entries"]:
                df = pd.DataFrame(state["entries"])
                st.subheader("📊 استهلاك المحطات اللحظي")
                chart_data = df.pivot_table(index='الوقت', columns='المنشأة', values='التيار (A)').ffill()
                st.line_chart(chart_data)
                
                def style_rows(row):
                    if "🔴" in str(row['الحالة']): return ['background-color: #8b0000; color: white'] * len(row)
                    if "🟡" in str(row['الحالة']): return ['background-color: #705d00; color: white'] * len(row)
                    if "🟢" in str(row['الحالة']): return ['background-color: #003311; color: white'] * len(row)
                    return [''] * len(row)

                st.subheader("📋 سجل القراءات الأخير")
                st.dataframe(df.tail(15).style.apply(style_rows, axis=1), use_container_width=True)
            else:
                st.info("بانتظار وصول البيانات...")
        
        time.sleep(1)
                    
