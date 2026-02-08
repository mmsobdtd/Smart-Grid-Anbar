import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# --- إعدادات الصفحة ---
st.set_page_config(page_title="نظام طاقة الأنبار - الفرز الذكي", layout="wide")

DB_FILE = "anbar_smart_sort_v4.json"

STATIONS = {
    "مستشفى الرمادي التعليمي": {"max": 1000},
    "معمل زجاج الرمادي": {"max": 1200},
    "محطة مياه الورار": {"max": 900},
    "جامعة الأنبار": {"max": 700},
    "حي التأميم (سكني)": {"max": 500}
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
    data["load_val"] = float(max(0.0, min(data["load_val"], 100.0)))
    with open(DB_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def apply_system_logic(new_readings, protocol_on):
    data = load_data()
    if data["collapsed"]: return
    
    if new_readings:
        data["entries"].extend(new_readings)
        data["entries"] = data["entries"][-60:] # حفظ آخر 60 قراءة للفرز
    
    if protocol_on:
        # استقرار البروتوكول عند 25%
        target = 25.0
        if data["load_val"] > (target + 2):
            data["load_val"] -= 8.0
        elif data["load_val"] < (target - 2):
            data["load_val"] += 2.0
        else:
            data["load_val"] = random.uniform(23.0, 27.0)
    else:
        if new_readings:
            data["load_val"] += len(new_readings) * 1.5 # ضغط متناسب مع عدد البيانات
        else:
            data["load_val"] = max(0.0, data["load_val"] - 4.0)
    
    if data["load_val"] >= 100.0:
        data["load_val"] = 100.0
        data["collapsed"] = True
    
    save_data(data)

# --- الواجهة الجانبية ---
st.sidebar.title("⚡ مركز سيطرة الرمادي")
page = st.sidebar.radio("القائمة:", ["🕹️ غرفة التحكم", "🖥️ شاشة المراقبة"])
protocol_active = st.sidebar.toggle("🛡️ تفعيل بروتوكول الحماية", value=False)

if st.sidebar.button("♻️ إعادة ضبط المنظومة"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.rerun()

# ==========================================
# صفحة التحكم
# ==========================================
if page == "🕹️ غرفة التحكم":
    st.title("🕹️ وحدة الإرسال والتحكم")
    state = load_data()
    if state["collapsed"]:
        st.error("🚨 النظام منهار! يرجى عمل Reset.")
    else:
        apply_system_logic([], protocol_active)
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🔧 إرسال يدوي")
            for name, specs in STATIONS.items():
                val = st.slider(f"تيار {name}", 0, 1500, value=int(specs['max']*0.6), key=f"s_{name}")
                if st.button(f"بث {name}", key=f"b_{name}"):
                    pct = (val / specs['max']) * 100
                    stt = "🔴 خطر" if pct >= 95 else "🟡 تنبيه" if pct >= 85 else "🟢 مستقر"
                    lvl = 3 if pct >= 95 else 2 if pct >= 85 else 1
                    apply_system_logic([{
                        "المحطة": name, "التيار (A)": val, "الحد الأقصى": specs['max'],
                        "الحالة": stt, "level": lvl, "timestamp": time.time(),
                        "الوقت": datetime.now().strftime("%H:%M:%S")
                    }], protocol_active)
                    st.toast(f"تم إرسال {name}")
        with col2:
            st.subheader("🚀 بث تلقائي (4 محطات/ثانية)")
            run_auto = st.checkbox("تشغيل التدفق المستمر")
            auto_placeholder = st.empty()
            while run_auto:
                curr = load_data()
                if curr["collapsed"]: st.rerun(); break
                
                # اختيار 4 محطات عشوائية فقط كما طلبت
                random_stations = random.sample(list(STATIONS.keys()), 4)
                batch = []
                for n in random_stations:
                    s_max = STATIONS[n]['max']
                    v = random.randint(int(s_max*0.5), int(s_max*1.1))
                    pct = (v / s_max) * 100
                    stt = "🔴 خطر" if pct >= 95 else "🟡 تنبيه" if pct >= 85 else "🟢 مستقر"
                    lvl = 3 if pct >= 95 else 2 if pct >= 85 else 1
                    batch.append({
                        "المحطة": n, "التيار (A)": v, "الحد الأقصى": s_max,
                        "الحالة": stt, "level": lvl, "timestamp": time.time(),
                        "الوقت": datetime.now().strftime("%H:%M:%S")
                    })
                
                apply_system_logic(batch, protocol_active)
                auto_placeholder.info(f"📡 يتم إرسال 4 حزم بيانات... الضغط: {curr['load_val']:.1f}%")
                time.sleep(1)

# ==========================================
# صفحة المراقبة
# ==========================================
else:
    st.title("🖥️ شاشة المراقبة والفرز الذكي")
    mon_placeholder = st.empty()
    while True:
        apply_system_logic([], protocol_active)
        state = load_data()
        with mon_placeholder.container():
            if state["collapsed"]:
                st.markdown("<div style='background-color:#1a0000; padding:50px; border: 5px solid red; text-align:center;'><h1 style='color:red;'>🚨 SYSTEM CRASH 🚨</h1></div>", unsafe_allow_html=True)
                break
            
            val = state["load_val"]
            p_color = "red" if val > 80 else "orange" if val > 40 else "green"
            st.markdown(f"### ضغط السيرفر: :{p_color}[{val:.1f}%]")
            st.progress(max(0.0, min(val / 100.0, 1.0)))
            
            if state["entries"]:
                df = pd.DataFrame(state["entries"])
                
                # --- منطق الفرز الذكي ---
                if protocol_active:
                    # فرز حسب مستوى الخطر (الأحمر أولاً) ثم حسب الوقت (الأحدث أولاً)
                    df_display = df.sort_values(by=['level', 'timestamp'], ascending=[False, False]).head(15)
                else:
                    # فرز حسب الوقت فقط (الأحدث أولاً)
                    df_display = df.sort_values(by='timestamp', ascending=False).head(15)

                def style_table(row):
                    if row['level'] == 3: return ['background-color: #4d0000; color: white'] * len(row)
                    if row['level'] == 2: return ['background-color: #4d3d00; color: white'] * len(row)
                    return ['background-color: #002611; color: white'] * len(row)

                st.subheader("📋 حالة المحطات (أولوية الخطر تظهر في الأعلى 🛡️)" if protocol_active else "📋 سجل القراءات (حسب الزمن)")
                st.dataframe(
                    df_display[["المحطة", "التيار (A)", "الحالة", "الوقت"]].style.apply(style_table, axis=1),
                    use_container_width=True, hide_index=True
                )
                
                st.subheader("📊 تحليل الأحمال")
                chart_data = df.pivot_table(index='الوقت', columns='المحطة', values='التيار (A)').ffill()
                st.line_chart(chart_data, height=200)
        time.sleep(1)
                    
