import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام طاقة الأنبار - المراقبة الذكية", layout="wide")

DB_FILE = "anbar_final_simulation.json"
MAX_BUFFER = 40 # الحد الأقصى لتراكم البيانات قبل الانهيار الحتمي

# 2. إعدادات المحطات (الرمادي)
STATIONS = {
    "مستشفى الرمادي التعليمي": {"max": 1000, "priority": 1},
    "معمل زجاج الرمادي": {"max": 1200, "priority": 2},
    "محطة مياه الورار": {"max": 900, "priority": 3},
    "جامعة الأنبار": {"max": 700, "priority": 4},
    "حي التأميم (سكني)": {"max": 500, "priority": 5}
}

# --- دوال إدارة البيانات ---
def load_system():
    if not os.path.exists(DB_FILE): 
        return {"entries": [], "load_val": 10, "collapsed": False}
    try:
        with open(DB_FILE, "r", encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"entries": [], "load_val": 10, "collapsed": False}

def save_system(new_entries, protocol_on, force_collapse=False):
    try:
        data = load_system()
        if data["collapsed"]: return
        
        if force_collapse:
            data["collapsed"] = True
            data["load_val"] = 100
        else:
            data["entries"].extend(new_entries)
            
            # --- منطق مؤشر الضغط (Server Load) ---
            if protocol_on:
                # البروتوكول يفرغ الضغط ويحافظ عليه بين 15% و 35%
                data["load_val"] = random.randint(15, 35)
                data["entries"] = data["entries"][-10:] # تفريغ السجل أولاً بأول
            else:
                # بدون بروتوكول: الضغط يرتفع تدريجياً (+15 لكل دفعة)
                data["load_val"] += 15
                data["entries"] = data["entries"][-MAX_BUFFER:] # تراكم البيانات
            
            # التحقق من الانهيار الحتمي
            if data["load_val"] >= 100:
                data["load_val"] = 100
                data["collapsed"] = True
                
        with open(DB_FILE, "w", encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except:
        pass

def create_smooth_reading(name, prev_val):
    limit = STATIONS[name]["max"]
    
    # تغير تدريجي (بين 50% و 100% من الحمل)
    # القيمة تتغير بنسبة بسيطة (+/- 3%) عن القيمة السابقة
    variation = random.uniform(-0.03, 0.03) * limit
    new_val = prev_val + variation
    
    # حصر القيمة في النطاق الواقعي الذي طلبته (50% إلى 100%)
    new_val = max(limit * 0.5, min(new_val, limit * 1.0))
    
    # تحديد الحالة (الخطر يظهر فقط فوق 97%)
    if new_val < (limit * 0.85): status, level = "🟢 مستقر", 1
    elif (limit * 0.85) <= new_val < (limit * 0.97): status, level = "🟡 تنبيه", 2
    else: status, level = "🔴 خطر", 3

    return int(new_val), {
        "المنشأة": name, "التيار (A)": int(new_val), "الحالة": status,
        "الوقت": datetime.now().strftime("%H:%M:%S"),
        "timestamp": time.time(), "level": level, 
        "priority": STATIONS[name]["priority"], "batch_id": time.time()
    }

# --- القائمة الجانبية ---
st.sidebar.title("⚡ سيطرة كهرباء الأنبار")
page = st.sidebar.radio("القائمة:", ["🕹️ غرفة التحكم", "🖥️ شاشة المراقبة"])
protocol_active = st.sidebar.toggle("🛡️ تفعيل بروتوكول الحماية", value=True)

if st.sidebar.button("♻️ إعادة تشغيل (Reset)"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.session_state.clear()
    st.rerun()

# ==========================================
# الصفحة 1: غرفة التحكم
# ==========================================
if page == "🕹️ غرفة التحكم":
    st.title("🕹️ وحدة التحكم الميدانية")
    
    state = load_system()
    if state["collapsed"]:
        st.error("❌ النظام منهار! يرجى عمل Reset للإصلاح.")
    else:
        run = st.checkbox("🚀 بدء البث التلقائي (تغير تدريجي)")
        if run:
            if 'vals' not in st.session_state:
                st.session_state.vals = {n: STATIONS[n]["max"]*0.7 for n in STATIONS}

            placeholder = st.empty()
            while run:
                if load_system()["collapsed"]: break
                
                batch = []
                for n in STATIONS:
                    new_v, log = create_smooth_reading(n, st.session_state.vals[n])
                    st.session_state.vals[n] = new_v
                    batch.append(log)
                
                save_system(batch, protocol_active)
                with placeholder.container():
                    st.write(f"📡 يتم البث الآن بواقعية... {datetime.now().strftime('%H:%M:%S')}")
                time.sleep(1)
        
        st.write("---")
        st.write("🔧 التحكم اليدوي (عن طريق الشريط):")
        for name in STATIONS:
            val = st.slider(f"{name}", 0, 1500, value=int(STATIONS[name]["max"]*0.75), key=name)
            if st.session_state.get(f"m_{name}") != val:
                save_system([create_smooth_reading(name, val)[1]], protocol_active)
                st.session_state[f"m_{name}"] = val

# ==========================================
# الصفحة 2: شاشة المراقبة
# ==========================================
else:
    st.title("🖥️ مركز مراقبة محطات الرمادي")
    
    placeholder = st.empty()
    while True:
        state = load_system()
        entries = state["entries"]
        is_collapsed = state["collapsed"]
        load_pct = state["load_val"]
        
        with placeholder.container():
            if is_collapsed:
                st.markdown("""
                <div style='background-color:black; padding:50px; border: 10px solid red; text-align:center;'>
                    <h1 style='color:red; font-size: 80px;'>⚠️ SYSTEM FAILURE ⚠️</h1>
                    <h2 style='color:white;'>انهيار الشبكة - تجاوز حد الضغط 100%</h2>
                </div>
                """, unsafe_allow_html=True)
                
                break

            if not entries:
                st.info("بانتظار وصول البيانات...")
            else:
                # 2. مؤشر الضغط (Server Load)
                color = "green" if protocol_active else "red"
                st.markdown(f"### مؤشر ضغط البيانات: :{color}[{load_pct}%]")
                st.progress(min(load_pct, 100) / 100)

                df = pd.DataFrame(entries)
                
                if protocol_active:
                    # البروتوكول يفرز ويحمي (المستشفى والخطر في الأعلى)
                    df_display = df.sort_values(by=["level", "priority", "timestamp"], ascending=[False, True, False])
                    st.success("✅ البروتوكول فعال: الضغط تحت السيطرة (دائماً < 40%).")
                else:
                    df_display = df.sort_values(by="timestamp", ascending=False)
                    st.warning("⚠️ تحذير: البروتوكول معطل! الضغط يرتفع بشكل خطير.")

                # الرسم البياني الواقعي
                st.subheader("📊 مخطط توزيع الأحمال (Live Trend)")
                chart_df = df.pivot_table(index='الوقت', columns='المنشأة', values='التيار (A)').ffill()
                st.line_chart(chart_df, height=250)
                

                # الجدول الملون
                def style_func(row):
                    if row['level'] == 3: return ['background-color: #8b0000; color: white'] * len(row)
                    if row['level'] == 2: return ['background-color: #705d00; color: white'] * len(row)
                    return [''] * len(row)

                st.dataframe(
                    df_display[["المنشأة", "التيار (A)", "الحالة", "الوقت", "level"]].style.apply(style_func, axis=1),
                    use_container_width=True, height=450, column_config={"level": None}
                )
        
        time.sleep(1)
    
