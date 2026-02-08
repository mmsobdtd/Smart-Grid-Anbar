import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="نظام طاقة الأنبار - إدارة البروتوكول الداخلي", layout="wide")

DB_FILE = "anbar_internal_prot_v1.json"

STATIONS_LIST = ["مستشفى الرمادي التعليمي", "معمل زجاج الرمادي", "محطة مياه الورار", "جامعة الأنبار", "حي التأميم (سكني)"]
STATIONS_SPECS = {"مستشفى الرمادي التعليمي": 1000, "معمل زجاج الرمادي": 1200, "محطة مياه الورار": 900, "جامعة الأنبار": 700, "حي التأميم (سكني)": 500}

# تهيئة حالة البروتوكول في المتصفح
if 'protocol_active' not in st.session_state:
    st.session_state.protocol_active = False

# --- 2. إدارة البيانات ---
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
    if data["collapsed"]: return data
    
    if new_readings:
        data["entries"].extend(new_readings)
        data["entries"] = data["entries"][-40:]
    
    if protocol_on:
        target = 25.0
        if data["load_val"] > (target + 2):
            data["load_val"] -= 10.0
        elif data["load_val"] < (target - 2):
            data["load_val"] += 2.0
        else:
            data["load_val"] = random.uniform(23.0, 27.0)
    else:
        if new_readings:
            data["load_val"] += len(new_readings) * 1.5
        else:
            data["load_val"] = max(0.0, data["load_val"] - 4.0)
            
    if data["load_val"] >= 100.0:
        data["load_val"] = 100.0
        data["collapsed"] = True
    
    save_data(data)
    return data

# --- 3. الواجهة الجانبية ---
st.sidebar.title("⚡ مركز سيطرة الرمادي")
page = st.sidebar.radio("انتقل إلى:", ["🕹️ غرفة التحكم", "🖥️ شاشة المراقبة"])

if st.sidebar.button("♻️ تصفير النظام"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.session_state.protocol_active = False
    st.rerun()

# ==========================================
# صفحة التحكم
# ==========================================
if page == "🕹️ غرفة التحكم":
    st.title("🕹️ وحدة إرسال البيانات والتحكم")
    
    # زر البروتوكول داخل غرفة التحكم كما طلبت
    st.session_state.protocol_active = st.toggle("🛡️ تفعيل بروتوكول الحماية", value=st.session_state.protocol_active)
    
    state = load_data()
    if state["collapsed"]:
        st.warning("🚨 النظام في حالة انهيار.")
    else:
        apply_system_logic([], st.session_state.protocol_active)
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🔧 إرسال يدوي")
            for name, m_val in STATIONS_SPECS.items():
                val = st.slider(f"{name}", 0, 1500, value=int(m_val*0.6), key=f"s_{name}")
                if st.button(f"إرسال {name}", key=f"b_{name}"):
                    pct = (val / m_val) * 100
                    stt = "🔴 خطر" if pct >= 95 else "🟡 تنبيه" if pct >= 85 else "🟢 مستقر"
                    lvl = 3 if pct >= 95 else 2 if pct >= 85 else 1
                    apply_system_logic([{
                        "المحطة": name, "التيار (A)": val, "الحالة": stt, 
                        "level": lvl, "timestamp": time.time(), "الوقت": datetime.now().strftime("%H:%M:%S")
                    }], st.session_state.protocol_active)
                    st.toast(f"تم إرسال {name}")

        with col2:
            st.subheader("🚀 بث تلقائي")
            run_auto = st.checkbox("تشغيل البث المستمر")
            auto_place = st.empty()
            while run_auto:
                if load_data()["collapsed"]: st.rerun(); break
                batch_time = time.time()
                batch_clock = datetime.now().strftime("%H:%M:%S")
                selected = random.sample(STATIONS_LIST, 4)
                batch = []
                for n in selected:
                    s_max = STATIONS_SPECS[n]
                    v = random.randint(int(s_max*0.4), int(s_max*1.3))
                    pct = (v / s_max) * 100
                    stt = "🔴 خطر" if pct >= 95 else "🟡 تنبيه" if pct >= 85 else "🟢 مستقر"
                    batch.append({"المحطة": n, "التيار (A)": v, "الحالة": stt, "level": 3 if pct >= 95 else 2 if pct >= 85 else 1, "timestamp": batch_time, "الوقت": batch_clock})
                
                apply_system_logic(batch, st.session_state.protocol_active)
                auto_place.info(f"📡 الضغط: {load_data()['load_val']:.1f}% | الدرع: {'نشط' if st.session_state.protocol_active else 'مطفي'}")
                time.sleep(1)

# ==========================================
# صفحة المراقبة
# ==========================================
else:
    st.title("🖥️ شاشة المراقبة والتحليل")
    mon_placeholder = st.empty()
    
    st.markdown("""
        <style>
        .stDataFrame { background-color: white !important; }
        .collapse-box {
            background-color: #ffe6e6; color: #b30000; padding: 15px;
            border: 2px solid #ff4d4d; border-radius: 10px; text-align: center;
            font-weight: bold; width: fit-content; margin: 20px auto;
        }
        </style>
    """, unsafe_allow_html=True)

    while True:
        state = apply_system_logic([], st.session_state.protocol_active)
        with mon_placeholder.container():
            if state["collapsed"]:
                st.markdown('<div class="collapse-box">🚨 النظام انهار بسبب ضغط على الشبكة</div>', unsafe_allow_html=True)
                break
            
            v = float(state.get("load_val", 0.0))
            p_color = "red" if v > 80 else "orange" if v > 40 else "green"
            st.markdown(f"### ضغط السيرفر: :{p_color}[{v:.1f}%]")
            st.progress(max(0.0, min(v / 100.0, 1.0)))
            
            if state["entries"]:
                df = pd.DataFrame(state["entries"])
                df_display = df.sort_values(by=['timestamp', 'level'], ascending=[False, False])

                # دالة التلوين (الخلفية ملونة بالكامل)
                def style_custom_rows(row):
                    lvl = row.get('level', 1)
                    if lvl == 3: # أحمر كامل
                        return ['background-color: #ff0000; color: white; font-weight: bold; border: 1px solid black'] * len(row)
                    if lvl == 2: # أصفر كامل
                        return ['background-color: #ffff00; color: black; font-weight: bold; border: 1px solid black'] * len(row)
                    return ['background-color: #00ff00; color: black; font-weight: bold; border: 1px solid black'] * len(row) # أخضر كامل

                st.subheader("📋 حالة المحطات")
                st.dataframe(
                    df_display[["المحطة", "التيار (A)", "الحالة", "الوقت"]].head(20).style.apply(style_custom_rows, axis=1),
                    use_container_width=True, hide_index=True
                )
                
                chart_df = df.pivot_table(index='الوقت', columns='المحطة', values='التيار (A)').ffill()
                st.line_chart(chart_df, height=200)
            else:
                st.info("بانتظار البيانات...")
        time.sleep(1)
                         
