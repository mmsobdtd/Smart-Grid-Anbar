import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# --- إعدادات الصفحة ---
st.set_page_config(page_title="نظام طاقة الأنبار - نظام الحماية المستقر", layout="wide")

DB_FILE = "anbar_final_fix.json"

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
        return {"entries": [], "load_val": 0, "collapsed": False}
    try:
        with open(DB_FILE, "r", encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"entries": [], "load_val": 0, "collapsed": False}

def save_data(data):
    with open(DB_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def apply_system_logic(new_readings, protocol_on):
    data = load_data()
    if data["collapsed"]: return
    
    # إضافة البيانات للسجل
    if new_readings:
        data["entries"].extend(new_readings)
        data["entries"] = data["entries"][-40:]
    
    if protocol_on:
        # --- تعديل البروتوكول: سحب الضغط للصفر فوراً ---
        if data["load_val"] > 1.0:
            data["load_val"] -= 15.0 # تفريغ سريع جداً
        else:
            data["load_val"] = random.uniform(0.1, 0.9) # البقاء بين 0 و 1
    else:
        # --- بدون بروتوكول ---
        if new_readings:
            # إذا فيه بيانات: الضغط يصعد
            incoming_stress = len(new_readings) * 2.5
            data["load_val"] += incoming_stress
        else:
            # إذا ما فيه بيانات: الضغط ينزل (تبريد تلقائي)
            data["load_val"] = max(0.0, data["load_val"] - 4.0)
    
    # فحص الانهيار
    if data["load_val"] >= 100:
        data["load_val"] = 100
        data["collapsed"] = True
    
    save_data(data)

# --- الواجهة ---
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
    st.title("🕹️ وحدة الإرسال والتحكم")
    
    state = load_data()
    if state["collapsed"]:
        st.error("❌ النظام منهار! يرجى عمل Reset.")
    else:
        # تحديث حالة النظام حتى لو لم نضغط شيء (من أجل التبريد/البروتوكول)
        apply_system_logic([], protocol_active)
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🔧 إرسال يدوي")
            for name, specs in STATIONS.items():
                val = st.slider(f"تيار {name}", 0, 1500, value=int(specs['max']*0.7), key=f"s_{name}")
                if st.button(f"بث قراءة {name}", key=f"b_{name}"):
                    status = "🔴 خطر" if val > specs['max'] * 0.98 else "🟡 تنبيه" if val > specs['max'] * 0.85 else "🟢 مستقر"
                    apply_system_logic([{"المنشأة": name, "التيار (A)": val, "الحالة": status, "الوقت": datetime.now().strftime("%H:%M:%S"), "timestamp": time.time()}], protocol_active)
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
                    batch.append({"المنشأة": name, "التيار (A)": v, "الحالة": status, "الوقت": datetime.now().strftime("%H:%M:%S"), "timestamp": time.time()})
                
                apply_system_logic(batch, protocol_active)
                auto_placeholder.info(f"📡 جاري البث... الضغط الحالي: {curr['load_val']:.1f}%")
                time.sleep(1)

# ==========================================
# صفحة المراقبة
# ==========================================
else:
    st.title("🖥️ شاشة المراقبة المركزية")
    mon_placeholder = st.empty()
    
    while True:
        # استدعاء المنطق (للتبريد التلقائي أو تفريغ البروتوكول)
        apply_system_logic([], protocol_active)
        state = load_data()
        
        with mon_placeholder.container():
            if state["collapsed"]:
                st.markdown("<div style='background-color:black; padding:50px; border: 15px solid red; text-align:center;'><h1 style='color:red;'>🚨 SYSTEM FAILURE 🚨</h1><h2 style='color:white;'>انهيار السيرفر</h2></div>", unsafe_allow_html=True)
                break
            
            val = state["load_val"]
            p_color = "red" if val > 80 else "orange" if val > 50 else "green"
            st.markdown(f"### مؤشر الضغط: :{p_color}[{val:.1f}%]")
            st.progress(min(val/100, 1.0))
            
            if state["entries"]:
                df = pd.DataFrame(state["entries"])
                st.subheader("📊 استهلاك الطاقة")
                chart_data = df.pivot_table(index='الوقت', columns='المنشأة', values='التيار (A)').ffill()
                st.line_chart(chart_data)
                
                # --- تلوين الصفوف بناءً على الحالة ---
                def style_rows(row):
                    if "🔴" in str(row['الحالة']): return ['background-color: #8b0000; color: white'] * len(row)
                    if "🟡" in str(row['الحالة']): return ['background-color: #705d00; color: white'] * len(row)
                    if "🟢" in str(row['الحالة']): return ['background-color: #003311; color: white'] * len(row)
                    return [''] * len(row)

                st.dataframe(df.tail(15).style.apply(style_rows, axis=1), use_container_width=True)
        
        time.sleep(1)
                                
