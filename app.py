import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# --- 1. إعدادات المنظومة الأساسية ---
st.set_page_config(page_title="نظام طاقة الأنبار - الفرز المشروط", layout="wide")

DB_FILE = "anbar_conditional_sync_v1.json"

STATIONS_SPECS = {
    "مستشفى الرمادي التعليمي": 1000,
    "معمل زجاج الرمادي": 1200,
    "محطة مياه الورار": 900,
    "جامعة الأنبار": 700,
    "حي التأميم (سكني)": 500
}

# --- 2. إدارة البيانات والمزامنة العالمية ---
def load_data():
    if not os.path.exists(DB_FILE):
        return {"entries": [], "load_val": 0.0, "collapsed": False, "protocol_on": False, "logs": []}
    try:
        with open(DB_FILE, "r", encoding='utf-8') as f:
            data = json.load(f)
            if "protocol_on" not in data: data["protocol_on"] = False
            if "logs" not in data: data["logs"] = []
            return data
    except:
        return {"entries": [], "load_val": 0.0, "collapsed": False, "protocol_on": False, "logs": []}

def save_data(data):
    data["load_val"] = float(max(0.0, min(data["load_val"], 100.0)))
    with open(DB_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def add_log(message):
    data = load_data()
    timestamp = datetime.now().strftime("%H:%M:%S")
    data["logs"].insert(0, f"[{timestamp}] {message}")
    data["logs"] = data["logs"][:10]
    save_data(data)

def apply_system_logic(new_readings, is_manual=False):
    data = load_data()
    if data["collapsed"]: return data
    
    is_protected = data.get("protocol_on", False)
    
    if new_readings:
        data["entries"].extend(new_readings)
        data["entries"] = data["entries"][-50:]
        
        if is_protected:
            # البروتوكول: موازنة ديناميكية حول 25%
            target = 25.0
            if data["load_val"] > (target + 2): data["load_val"] -= 7.0
            elif data["load_val"] < (target - 2): data["load_val"] += 2.0
            else: data["load_val"] = random.uniform(23.0, 27.0)
        else:
            # بدون بروتوكول: الضغط يرتفع
            data["load_val"] += 7.0 if is_manual else (len(new_readings) * 1.5)
    else:
        # تبريد أو موازنة تلقائية
        if is_protected:
            data["load_val"] = random.uniform(24.0, 26.0)
        else:
            data["load_val"] = max(0.0, data["load_val"] - 3.0)

    if data["load_val"] >= 100.0:
        data["collapsed"] = True
        add_log("🚨 انهيار النظام بسبب الضغط!")
        
    save_data(data)
    return data

# --- 3. بناء الواجهة ---
st.sidebar.title("⚡ مركز سيطرة الرمادي")
page = st.sidebar.radio("القائمة الرئيسية:", ["🕹️ غرفة التحكم", "🖥️ شاشة المراقبة"])

if st.sidebar.button("♻️ تصفير النظام"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.rerun()

# ==========================================
# صفحة التحكم
# ==========================================
if page == "🕹️ غرفة التحكم":
    st.title("🕹️ وحدة التحكم والإرسال")
    
    state = load_data()
    # إدارة البروتوكول عالمياً
    proto_status = st.toggle("🛡️ تفعيل بروتوكول الحماية", value=state["protocol_on"])
    if proto_status != state["protocol_on"]:
        state["protocol_on"] = proto_status
        save_data(state)
        add_log(f"تم {'تفعيل' if proto_status else 'إيقاف'} البروتوكول عالمياً")
        st.rerun()

    if state["collapsed"]:
        st.error("🚨 النظام انهار بسبب ضغط على الشبكة.")
    else:
        apply_system_logic([]) 
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🔧 الإرسال اليدوي")
            for name, m_val in STATIONS_SPECS.items():
                val = st.slider(f"{name}", 0, 1500, value=int(m_val*0.6), key=f"s_{name}")
                if st.button(f"بث {name}", key=f"b_{name}"):
                    pct = (val / m_val) * 100
                    # الخطر عند 95% فأكثر كما طلبت
                    stt = "🔴 خطر" if pct >= 95 else "🟡 تنبيه" if pct >= 85 else "🟢 مستقر"
                    lvl = 3 if pct >= 95 else 2 if pct >= 85 else 1
                    apply_system_logic([{
                        "المحطة": name, "التيار (A)": val, "الحالة": stt, 
                        "level": lvl, "timestamp": time.time(), "الوقت": datetime.now().strftime("%H:%M:%S"),
                        "source": "manual"
                    }], is_manual=True)
                    st.toast(f"تم إرسال {name}")

        with col2:
            st.subheader("🚀 البث التلقائي")
            run_auto = st.checkbox("تشغيل الإرسال")
            auto_info = st.empty()
            while run_auto:
                curr_state = load_data()
                if curr_state["collapsed"]: st.rerun(); break
                batch = []
                b_time, b_clock = time.time(), datetime.now().strftime("%H:%M:%S")
                for n in random.sample(list(STATIONS_SPECS.keys()), 4):
                    s_max = STATIONS_SPECS[n]
                    v = random.randint(int(s_max*0.4), int(s_max*1.1))
                    pct = (v / s_max) * 100
                    stt = "🔴 خطر" if pct >= 95 else "🟡 تنبيه" if pct >= 85 else "🟢 مستقر"
                    batch.append({"المحطة": n, "التيار (A)": v, "الحالة": stt, "level": 3 if pct >= 95 else 2 if pct >= 85 else 1, "timestamp": b_time, "الوقت": b_clock, "source": "auto"})
                apply_system_logic(batch)
                auto_info.info(f"📡 الضغط: {load_data()['load_val']:.1f}%")
                time.sleep(2 if curr_state['protocol_on'] else 1)

# ==========================================
# صفحة المراقبة
# ==========================================
else:
    st.title("🖥️ شاشة المراقبة المركزية")
    
    st.sidebar.subheader("📜 سجل الأحداث")
    for log in load_data()["logs"]:
        st.sidebar.caption(log)

    mon_placeholder = st.empty()
    
    st.markdown("""
        <style>
        .stDataFrame { background-color: white !important; }
        div[data-testid="stDataFrame"] td { color: black !important; font-weight: bold; }
        .collapse-small { background-color: white; color: red; padding: 15px; border: 2px solid red; border-radius: 8px; text-align: center; font-weight: bold; width: 300px; margin: 20px auto; }
        </style>
    """, unsafe_allow_html=True)

    while True:
        state = apply_system_logic([]) 
        is_p = state.get("protocol_on", False)
        
        with mon_placeholder.container():
            if state["collapsed"]:
                st.markdown('<div class="collapse-small">🚨 النظام انهار بسبب ضغط على الشبكة</div>', unsafe_allow_html=True)
                break
            
            v = float(state["load_val"])
            p_color = "blue" if is_p else ("red" if v > 85 else "green")
            st.markdown(f"### ضغط المنظومة: :{p_color}[{v:.1f}%] {'(🛡️ محمي)' if is_p else ''}")
            st.progress(max(0.0, min(v / 100.0, 1.0)))
            
            if state["entries"]:
                df = pd.DataFrame(state["entries"])
                
                # --- الفرز المشروط المطلوب ---
                if is_p:
                    # البروتوكول مفعل: فرز (يدوي أولاً، ثم زمن، ثم مستوى خطر)
                    df_display = df.sort_values(by=['source', 'timestamp', 'level'], ascending=[False, False, False])
                else:
                    # البروتوكول مطفأ: فرز زمني فقط (الأحدث أولاً)
                    df_display = df.sort_values(by='timestamp', ascending=False)

                def style_custom_rows(row):
                    stt = str(row['الحالة'])
                    if "🔴" in stt: return ['background-color: #ff0000; color: black'] * len(row)
                    if "🟡" in stt: return ['background-color: #ffff00; color: black'] * len(row)
                    return ['background-color: #00ff00; color: black'] * len(row)

                st.dataframe(
                    df_display[["المحطة", "التيار (A)", "الحالة", "الوقت"]].head(20).style.apply(style_custom_rows, axis=1), 
                    use_container_width=True, hide_index=True
                )
                
                chart_df = df.pivot_table(index='الوقت', columns='المحطة', values='التيار (A)').ffill()
                st.line_chart(chart_df, height=180)
            else:
                st.info("بانتظار البيانات...")
        
        time.sleep(2 if is_p else 1)
    
