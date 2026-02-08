import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# --- 1. إعدادات المنظومة ---
st.set_page_config(page_title="نظام طاقة الأنبار - الفرز اليدوي المطور", layout="wide")

DB_FILE = "anbar_manual_priority_v1.json"

STATIONS_SPECS = {
    "مستشفى الرمادي التعليمي": 1000,
    "معمل زجاج الرمادي": 1200,
    "محطة مياه الورار": 900,
    "جامعة الأنبار": 700,
    "حي التأميم (سكني)": 500
}

if 'protocol_active' not in st.session_state:
    st.session_state.protocol_active = False

# --- 2. إدارة البيانات العالمية ---
def load_data():
    if not os.path.exists(DB_FILE):
        return {"entries": [], "load_val": 0.0, "collapsed": False, "protocol_on": False}
    try:
        with open(DB_FILE, "r", encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"entries": [], "load_val": 0.0, "collapsed": False, "protocol_on": False}

def save_data(data):
    data["load_val"] = float(max(0.0, min(data["load_val"], 100.0)))
    with open(DB_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def apply_system_logic(new_readings, is_manual=False):
    data = load_data()
    if data["collapsed"]: return data
    
    is_protected = data.get("protocol_on", False)
    
    if new_readings:
        data["entries"].extend(new_readings)
        data["entries"] = data["entries"][-50:] # زيادة السعة قليلاً
        
        if is_protected:
            # البروتوكول: موازنة نحو الـ 25%
            target = 25.0
            if data["load_val"] > target: data["load_val"] -= 4.0
            else: data["load_val"] += 1.0
        else:
            # بدون بروتوكول: الضغط يرتفع
            data["load_val"] += 5.0 if is_manual else (len(new_readings) * 1.5)
    else:
        # تبريد أو موازنة تلقائية
        if is_protected:
            data["load_val"] = random.uniform(23.0, 27.0)
        else:
            data["load_val"] = max(0.0, data["load_val"] - 2.0)

    if data["load_val"] >= 100.0:
        data["collapsed"] = True
        
    save_data(data)
    return data

# --- 3. الواجهة ---
st.sidebar.title("⚡ مركز سيطرة الرمادي")
page = st.sidebar.radio("القائمة:", ["🕹️ غرفة التحكم", "🖥️ شاشة المراقبة"])

if st.sidebar.button("♻️ تصفير النظام"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.rerun()

# ==========================================
# صفحة التحكم (غرفة العمليات)
# ==========================================
if page == "🕹️ غرفة التحكم":
    st.title("🕹️ وحدة الإرسال اليدوي والتلقائي")
    
    state = load_data()
    # مزامنة حالة البروتوكول عالمياً
    st.session_state.protocol_active = st.toggle("🛡️ تفعيل بروتوكول الحماية", value=state.get("protocol_on", False))
    if st.session_state.protocol_active != state.get("protocol_on", False):
        state["protocol_on"] = st.session_state.protocol_active
        save_data(state)
        st.rerun()

    if state["collapsed"]:
        st.error("🚨 النظام انهار بسبب ضغط الشبكة.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🔧 الإرسال اليدوي الفوري")
            for name, m_val in STATIONS_SPECS.items():
                val = st.slider(f"{name}", 0, 1500, value=int(m_val*0.6), key=f"s_{name}")
                if st.button(f"إرسال قراءة {name}", key=f"b_{name}"):
                    pct = (val / m_val) * 100
                    # الخطر عند 95% كما طلبت
                    stt = "🔴 خطر" if pct >= 95 else "🟡 تنبيه" if pct >= 85 else "🟢 مستقر"
                    apply_system_logic([{
                        "المحطة": name, "التيار (A)": val, "الحالة": stt, 
                        "level": 4 if st.session_state.protocol_active else (3 if pct >= 95 else 2 if pct >= 85 else 1),
                        "timestamp": time.time(), "الوقت": datetime.now().strftime("%H:%M:%S"),
                        "type": "manual"
                    }], is_manual=True)
                    st.toast(f"بث يدوي: {name}")

        with col2:
            st.subheader("🚀 البث التلقائي")
            run_auto = st.checkbox("تشغيل الإرسال المستمر")
            auto_place = st.empty()
            while run_auto:
                if load_data()["collapsed"]: st.rerun(); break
                batch = []
                b_time, b_clock = time.time(), datetime.now().strftime("%H:%M:%S")
                for n in random.sample(list(STATIONS_SPECS.keys()), 4):
                    s_max = STATIONS_SPECS[n]
                    v = random.randint(int(s_max*0.4), int(s_max*1.1))
                    pct = (v / s_max) * 100
                    batch.append({"المحطة": n, "التيار (A)": v, "الحالة": "🟢 مستقر", "level": 1, "timestamp": b_time, "الوقت": b_clock, "type": "auto"})
                
                apply_system_logic(batch)
                auto_place.info(f"📡 الضغط الحالي: {load_data()['load_val']:.1f}%")
                time.sleep(2 if st.session_state.protocol_active else 1)

# ==========================================
# صفحة المراقبة (شاشة المراقبين)
# ==========================================
else:
    st.title("🖥️ شاشة المراقبة المركزية")
    mon_placeholder = st.empty()
    
    st.markdown("""
        <style>
        .stDataFrame { background-color: white !important; }
        div[data-testid="stDataFrame"] td { color: black !important; font-weight: bold; }
        .collapse-msg { background-color: white; color: red; padding: 20px; border: 2px solid red; border-radius: 10px; text-align: center; margin: auto; }
        </style>
    """, unsafe_allow_html=True)

    while True:
        state = apply_system_logic([]) 
        with mon_placeholder.container():
            if state["collapsed"]:
                st.markdown('<div class="collapse-msg">🚨 النظام انهار بسبب ضغط على الشبكة</div>', unsafe_allow_html=True)
                break
            
            v = float(state["load_val"])
            is_p = state.get("protocol_on", False)
            p_color = "blue" if is_p else ("red" if v > 80 else "green")
            st.markdown(f"### ضغط المنظومة: :{p_color}[{v:.1f}%] {'(🛡️ البروتوكول نشط)' if is_p else ''}")
            st.progress(max(0.0, min(v / 100.0, 1.0)))
            
            if state["entries"]:
                df = pd.DataFrame(state["entries"])
                # الفرز: اليدوي (Manual) يأخذ الأولوية القصوى في الأعلى عند تفعيل البروتوكول
                if is_p:
                    # فرز حسب: النوع (يدوي أولاً)، ثم المستوى، ثم التوقيت
                    df_display = df.sort_values(by=['type', 'level', 'timestamp'], ascending=[False, False, False])
                else:
                    df_display = df.sort_values(by='timestamp', ascending=False)

                def style_white(row):
                    stt = str(row['الحالة'])
                    if "🔴" in stt: return ['background-color: white; color: red'] * len(row)
                    if "🟡" in stt: return ['background-color: white; color: #ccaa00'] * len(row)
                    return ['background-color: white; color: green'] * len(row)

                st.dataframe(df_display[["المحطة", "التيار (A)", "الحالة", "الوقت"]].head(15).style.apply(style_white, axis=1), use_container_width=True, hide_index=True)
                st.line_chart(df.pivot_table(index='الوقت', columns='المحطة', values='التيار (A)').ffill(), height=200)
            else:
                st.info("بانتظار البيانات...")
        
        # التحديث كل 2 ثانية في حالة البروتوكول كما طلبت
        time.sleep(2 if is_p else 1)
    
