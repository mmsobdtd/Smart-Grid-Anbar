import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="نظام طاقة الأنبار - المراقبة المركزية", layout="wide")

DB_FILE = "anbar_final_pro_v10.json"

STATIONS_LIST = ["مستشفى الرمادي التعليمي", "معمل زجاج الرمادي", "محطة مياه الورار", "جامعة الأنبار", "حي التأميم (سكني)"]
STATIONS_SPECS = {"مستشفى الرمادي التعليمي": 1000, "معمل زجاج الرمادي": 1200, "محطة مياه الورار": 900, "جامعة الأنبار": 700, "حي التأميم (سكني)": 500}

# تهيئة حالة البروتوكول في الـ Session
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
    # صمام أمان لمنع الخطأ البرمجي (الموجود في صورتك)
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
        # منطق الـ 25% (يصعد وينزل حولها)
        target = 25.0
        if data["load_val"] > (target + 2):
            data["load_val"] -= 5.0 # تفريغ تدريجي
        elif data["load_val"] < (target - 2):
            data["load_val"] += 2.0 # صعود تدريجي
        else:
            data["load_val"] = random.uniform(23.0, 27.0) # تذبذب طبيعي
    else:
        # بدون بروتوكول
        if new_readings:
            data["load_val"] += len(new_readings) * 2.0
        else:
            data["load_val"] = max(0.0, data["load_val"] - 4.0) # تبريد تلقائي
            
    if data["load_val"] >= 100.0:
        data["load_val"] = 100.0
        data["collapsed"] = True
    
    save_data(data)
    return data

# --- 3. الواجهة الجانبية ---
st.sidebar.title("⚡ مركز سيطرة الرمادي")
page = st.sidebar.radio("القائمة الرئيسية:", ["🕹️ غرفة التحكم", "🖥️ شاشة المراقبة"])

if st.sidebar.button("♻️ تصفير النظام"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.session_state.protocol_active = False
    st.rerun()

# ==========================================
# صفحة التحكم (فيها زر البروتوكول)
# ==========================================
if page == "🕹️ غرفة التحكم":
    st.title("🕹️ وحدة الإرسال والتحكم")
    
    # نقل الزر إلى هنا كما طلبت
    st.session_state.protocol_active = st.toggle("🛡️ تفعيل بروتوكول الحماية", value=st.session_state.protocol_active)
    
    state = load_data()
    if state["collapsed"]:
        st.warning("⚠️ النظام انهار بسبب ضغط على الشبكة. يرجى التصفير.")
    else:
        apply_system_logic([], st.session_state.protocol_active)
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🔧 إرسال يدوي")
            for name, m_val in STATIONS_SPECS.items():
                val = st.slider(f"{name}", 0, 1500, value=int(m_val*0.6), key=f"s_{name}")
                if st.button(f"إرسال قراءة {name}", key=f"b_{name}"):
                    pct = (val / m_val) * 100
                    stt = "🔴 خطر" if pct >= 95 else "🟡 تنبيه" if pct >= 85 else "🟢 مستقر"
                    apply_system_logic([{
                        "المحطة": name, "التيار (A)": val, "الحالة": stt, 
                        "level": 3 if pct >= 95 else 2 if pct >= 85 else 1,
                        "timestamp": time.time(), "الوقت": datetime.now().strftime("%H:%M:%S")
                    }], st.session_state.protocol_active)
                    st.toast(f"تم البث: {name}")

        with col2:
            st.subheader("🚀 بث تلقائي (مجموعات رباعية)")
            run_auto = st.checkbox("بدء الضخ المستمر")
            auto_place = st.empty()
            while run_auto:
                if load_data()["collapsed"]: st.rerun(); break
                b_time = time.time()
                b_clock = datetime.now().strftime("%H:%M:%S")
                selected = random.sample(STATIONS_LIST, 4)
                batch = []
                for n in selected:
                    s_max = STATIONS_SPECS[n]
                    v = random.randint(int(s_max*0.4), int(s_max*1.3))
                    pct = (v / s_max) * 100
                    stt = "🔴 خطر" if pct >= 95 else "🟡 تنبيه" if pct >= 85 else "🟢 مستقر"
                    batch.append({"المحطة": n, "التيار (A)": v, "الحالة": stt, "level": 3 if pct >= 95 else 2 if pct >= 85 else 1, "timestamp": b_time, "الوقت": b_clock})
                
                apply_system_logic(batch, st.session_state.protocol_active)
                auto_place.info(f"📡 الضغط: {load_data()['load_val']:.1f}% | البروتوكول: {'نشط' if st.session_state.protocol_active else 'معطل'}")
                time.sleep(1)

# ==========================================
# صفحة المراقبة (الجدول الأبيض الملون)
# ==========================================
else:
    st.title("🖥️ شاشة المراقبة والتحليل")
    mon_placeholder = st.empty()
    
    # CSS لجعل الجدول أبيض والمربع الصغير للانهيار
    st.markdown("""
        <style>
        .stDataFrame { background-color: white !important; padding: 10px; border-radius: 10px; }
        .collapse-small {
            background-color: #ffe6e6; color: #b30000; padding: 15px;
            border: 2px solid #ff4d4d; border-radius: 8px; text-align: center;
            font-weight: bold; width: 300px; margin: 20px auto;
        }
        </style>
    """, unsafe_allow_html=True)

    while True:
        state = apply_system_logic([], st.session_state.protocol_active)
        with mon_placeholder.container():
            # المربع الصغير عند الانهيار
            if state["collapsed"]:
                st.markdown('<div class="collapse-small">🚨 النظام انهار بسبب ضغط على الشبكة</div>', unsafe_allow_html=True)
                break
            
            v = float(state.get("load_val", 0.0))
            p_color = "red" if v > 80 else "orange" if v > 40 else "green"
            st.markdown(f"### ضغط السيرفر: :{p_color}[{v:.1f}%]")
            # صمام أمان المؤشر لمنع الـ Exception
            st.progress(max(0.0, min(v / 100.0, 1.0)))
            
            if state["entries"]:
                df = pd.DataFrame(state["entries"])
                # الفرز: أحدث مجموعة في الأعلى، والأخطر يتصدر المجموعة
                df_display = df.sort_values(by=['timestamp', 'level'], ascending=[False, False])

                # دالة التلوين الصريح (خلفية كاملة السطر)
                def style_full_rows(row):
                    lvl = row.get('level', 1)
                    if lvl == 3: # أحمر كامل
                        return ['background-color: #ff0000; color: white; font-weight: bold'] * len(row)
                    if lvl == 2: # أصفر كامل
                        return ['background-color: #ffff00; color: black; font-weight: bold'] * len(row)
                    return ['background-color: #00ff00; color: black; font-weight: bold'] * len(row) # أخضر كامل

                st.subheader("📋 حالة المحطات")
                st.dataframe(
                    df_display[["المحطة", "التيار (A)", "الحالة", "الوقت"]].head(20).style.apply(style_full_rows, axis=1),
                    use_container_width=True, hide_index=True
                )
                
                st.subheader("📊 مخطط الأحمال")
                chart_df = df.pivot_table(index='الوقت', columns='المحطة', values='التيار (A)').ffill()
                st.line_chart(chart_df, height=200)
            else:
                st.info("بانتظار البيانات...")
        time.sleep(1)
        
