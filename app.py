import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام طاقة الأنبار - محاكاة الانهيار", layout="wide")

DB_FILE = "anbar_ultimate_sim.json"

# 2. إعدادات المحطات (الرمادي)
STATIONS = {
    "مستشفى الرمادي التعليمي": {"max": 1000, "priority": 1},
    "معمل زجاج الرمادي": {"max": 1200, "priority": 2},
    "محطة مياه الورار": {"max": 900, "priority": 3},
    "جامعة الأنبار": {"max": 700, "priority": 4},
    "حي التأميم (سكني)": {"max": 500, "priority": 5}
}

# --- دوال إدارة النظام ---
def load_system_state():
    if not os.path.exists(DB_FILE): 
        return {"entries": [], "load_val": 10, "collapsed": False}
    try:
        with open(DB_FILE, "r", encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"entries": [], "load_val": 10, "collapsed": False}

def save_system_state(new_entries, protocol_on, force_collapse=False):
    try:
        data = load_system_state()
        if data["collapsed"]: return
        
        if force_collapse:
            data["collapsed"] = True
            data["load_val"] = 100
        else:
            data["entries"].extend(new_entries)
            
            # --- منطق مؤشر الضغط الحتمي ---
            if protocol_on:
                # البروتوكول يفرغ الضغط ويحافظ عليه تحت 40%
                data["load_val"] = random.randint(10, 35)
                data["entries"] = data["entries"][-10:] # تفريغ السجل
            else:
                # بدون بروتوكول: الضغط يرتفع حتماً (+20 كل ثانية)
                data["load_val"] += 20
                data["entries"] = data["entries"][-30:] # تراكم البيانات
            
            # فحص الانهيار عند وصول العداد لـ 100
            if data["load_val"] >= 100:
                data["load_val"] = 100
                data["collapsed"] = True
                
        with open(DB_FILE, "w", encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except:
        pass

def create_random_reading(name):
    limit = STATIONS[name]["max"]
    
    # عشوائية كاملة بين 50% و 100% كما طلبت
    new_val = random.randint(int(limit * 0.5), int(limit * 1.0))
    
    # تحديد الحالة (تقليل ظهور الخطر بجعله فوق 98% فقط)
    if new_val < (limit * 0.85): 
        status, level = "🟢 مستقر", 1
    elif (limit * 0.85) <= new_val < (limit * 0.98): 
        status, level = "🟡 تنبيه", 2
    else: 
        status, level = "🔴 خطر", 3

    return {
        "المنشأة": name, "التيار (A)": new_val, "الحالة": status,
        "الوقت": datetime.now().strftime("%H:%M:%S"),
        "timestamp": time.time(), "level": level, 
        "priority": STATIONS[name]["priority"], "batch_id": time.time()
    }

# --- القائمة الجانبية ---
st.sidebar.title("⚡ مركز سيطرة الرمادي")
page = st.sidebar.radio("القائمة:", ["🕹️ غرفة التحكم", "🖥️ شاشة المراقبة"])
protocol_active = st.sidebar.toggle("🛡️ تفعيل بروتوكول الحماية", value=True)

if st.sidebar.button("♻️ تصفير النظام (Reset)"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.rerun()

# ==========================================
# الصفحة 1: غرفة التحكم
# ==========================================
if page == "🕹️ غرفة التحكم":
    st.title("🕹️ وحدة الإرسال الميداني")
    
    state = load_system_state()
    if state["collapsed"]:
        st.error("❌ الشبكة منهارة! يرجى عمل Reset من القائمة الجانبية.")
    else:
        run = st.checkbox("🚀 تشغيل البث التلقائي (عشوائي)")
        if run:
            placeholder = st.empty()
            while run:
                if load_system_state()["collapsed"]: break
                
                batch = [create_random_reading(n) for n in STATIONS]
                save_system_state(batch, protocol_active)
                
                with placeholder.container():
                    st.write(f"📡 جاري ضخ البيانات العشوائية... {datetime.now().strftime('%H:%M:%S')}")
                time.sleep(1)
        
        st.write("---")
        st.write("🔧 التحكم اليدوي المباشر:")
        for name in STATIONS:
            val = st.slider(f"{name}", 0, 1500, value=int(STATIONS[name]["max"]*0.6), key=name)
            if st.session_state.get(f"m_{name}") != val:
                # محاكاة إرسال قيمة يدوية
                limit = STATIONS[name]["max"]
                if val < (limit * 0.85): s, l = "🟢 مستقر", 1
                elif (limit * 0.85) <= val < (limit * 0.98): s, l = "🟡 تنبيه", 2
                else: s, l = "🔴 خطر", 3
                
                save_system_state([{
                    "المنشأة": name, "التيار (A)": val, "الحالة": s,
                    "الوقت": datetime.now().strftime("%H:%M:%S"),
                    "timestamp": time.time(), "level": l, "priority": STATIONS[name]["priority"], "batch_id": time.time()
                }], protocol_active)
                st.session_state[f"m_{name}"] = val

# ==========================================
# الصفحة 2: شاشة المراقبة
# ==========================================
else:
    st.title("🖥️ شاشة مراقبة أحمال الرمادي")
    
    placeholder = st.empty()
    while True:
        state = load_system_state()
        entries = state["entries"]
        is_collapsed = state["collapsed"]
        current_load = state["load_val"]
        
        with placeholder.container():
            if is_collapsed:
                st.markdown("""
                <div style='background-color:black; padding:50px; border: 15px solid red; text-align:center;'>
                    <h1 style='color:red; font-size: 80px;'>⚠️ SYSTEM FAILURE ⚠️</h1>
                    <h2 style='color:white;'>انهيار السيرفر - الضغط تجاوز 100%</h2>
                    <p style='color:yellow;'>السبب: تدفق بيانات عشوائي مكثف بدون حماية.</p>
                </div>
                """, unsafe_allow_html=True)
                break

            if not entries:
                st.info("بانتظار البيانات... شغل البث من غرفة التحكم.")
            else:
                # عرض مؤشر الضغط الحتمي
                p_color = "green" if protocol_active else "red"
                st.markdown(f"### مؤشر ضغط السيرفر: :{p_color}[{current_load}%]")
                st.progress(min(current_load, 100) / 100)

                df = pd.DataFrame(entries)
                
                if protocol_active:
                    df_display = df.sort_values(by=["level", "priority", "timestamp"], ascending=[False, True, False])
                    st.success("✅ البروتوكول فعال: الضغط مستقر (دائماً < 40%).")
                else:
                    df_display = df.sort_values(by="timestamp", ascending=False)
                    st.warning("⚠️ تحذير: البروتوكول معطل! السيرفر يقترب من الانهيار.")

                # الرسم البياني العشوائي
                st.subheader("📊 مخطط الأحمال اللحظي (عشوائي)")
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
    
