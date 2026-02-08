import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# --- إعدادات الصفحة ---
st.set_page_config(page_title="نظام طاقة الأنبار - النسخة الاحترافية", layout="wide")

DB_FILE = "anbar_pro_v4.json"

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

def update_system(new_readings, protocol_on):
    data = load_data()
    if data["collapsed"]: return
    
    # إضافة البيانات الجديدة للسجل
    data["entries"].extend(new_readings)
    data["entries"] = data["entries"][-40:] # الحفاظ على آخر 40 سجل
    
    # حساب الضغط (جعلته أبطأ: 1.5% لكل حزمة بيانات بدلاً من 4%)
    incoming_stress = len(new_readings) * 1.5 
    
    if protocol_on:
        # البروتوكول يحاكي الضغط لكنه يمنع الانهيار (يصده عند 85%)
        potential_load = data["load_val"] + (incoming_stress * 0.4)
        data["load_val"] = min(potential_load, 85.0) 
        # تبريد طفيف بمرور الوقت
        data["load_val"] = max(0, data["load_val"] - 0.5)
    else:
        # بدون بروتوكول: الضغط يرتفع حتى الانهيار
        data["load_val"] += incoming_stress
    
    # فحص الانهيار
    if data["load_val"] >= 100:
        data["load_val"] = 100
        data["collapsed"] = True
    
    save_data(data)

# --- واجهة Streamlit الجانبية ---
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
                    # منطق الألوان القديم
                    if val < (specs['max'] * 0.85): status, level = "🟢 مستقر", 1
                    elif val < (specs['max'] * 0.98): status, level = "🟡 تنبيه", 2
                    else: status, level = "🔴 خطر", 3
                    
                    reading = [{
                        "المنشأة": name, "التيار (A)": val, "الحالة": status,
                        "الوقت": datetime.now().strftime("%H:%M:%S"),
                        "timestamp": time.time(), "level": level
                    }]
                    update_system(reading, protocol_active)
                    st.toast(f"تم إرسال {name} بنجاح")

        with col2:
            st.subheader("🚀 بث تلقائي")
            run_auto = st.checkbox("تشغيل التدفق المستمر")
            if run_auto:
                placeholder = st.empty()
                while run_auto:
                    curr = load_data()
                    if curr["collapsed"]: st.rerun(); break
                    
                    batch = []
                    for name, specs in STATIONS.items():
                        v = random.randint(int(specs['max']*0.5), int(specs['max']*1.1))
                        if v < (specs['max'] * 0.85): s, l = "🟢 مستقر", 1
                        elif v < (specs['max'] * 0.98): s, l = "🟡 تنبيه", 2
                        else: s, l = "🔴 خطر", 3
                        
                        batch.append({
                            "المنشأة": name, "التيار (A)": v, "الحالة": s,
                            "الوقت": datetime.now().strftime("%H:%M:%S"),
                            "timestamp": time.time(), "level": l
                        })
                    
                    update_system(batch, protocol_active)
                    with placeholder.container():
                        st.info(f"📡 جاري البث... الضغط الحالي: {curr['load_val']:.1f}%")
                    time.sleep(1)

# ==========================================
# صفحة المراقبة
# ==========================================
else:
    st.title("🖥️ شاشة المراقبة والبيانات")
    
    mon_placeholder = st.empty()
    
    while True:
        state = load_data()
        
        with mon_placeholder.container():
            if state["collapsed"]:
                st.markdown("""
                <div style='background-color:black; padding:50px; border: 15px solid red; text-align:center;'>
                    <h1 style='color:red; font-size: 80px;'>⚠️ SYSTEM FAILURE ⚠️</h1>
                    <h2 style='color:white;'>انهيار سيرفرات الطاقة في الرمادي</h2>
                    <p style='color:yellow;'>السبب: تراكم البيانات غير المحمية بنسبة 100%</p>
                </div>
                """, unsafe_allow_html=True)
                break
            
            # عرض عداد الضغط
            val = state["load_val"]
            p_color = "red" if val > 80 else "orange" if val > 50 else "green"
            st.markdown(f"### مؤشر ضغط المنظومة: :{p_color}[{val:.1f}%]")
            st.progress(min(val/100, 1.0))
            
            if state["entries"]:
                df = pd.DataFrame(state["entries"])
                
                # الرسم البياني
                st.subheader("📊 استهلاك المحطات اللحظي")
                chart_data = df.pivot_table(index='الوقت', columns='المنشأة', values='التيار (A)').ffill()
                st.line_chart(chart_data)
                
                # --- إعادة الألوان الأصلية للجدول ---
                def style_rows(row):
                    if "🔴" in row['الحالة']: return ['background-color: #8b0000; color: white'] * len(row)
                    if "🟡" in row['الحالة']: return ['background-color: #705d00; color: white'] * len(row)
                    if "🟢" in row['الحالة']: return ['background-color: #003311; color: white'] * len(row)
                    return [''] * len(row)

                st.subheader("📋 سجل القراءات الأخير")
                st.dataframe(
                    df.tail(15).style.apply(style_rows, axis=1),
                    use_container_width=True
                )
            else:
                st.info("بانتظار وصول البيانات...")
        
        time.sleep(1)
                        
