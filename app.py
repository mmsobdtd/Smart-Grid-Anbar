import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام طاقة الأنبار - المراقبة الذكية", layout="wide")

DB_FILE = "anbar_smart_grid_v8.json"
MAX_CAPACITY = 30 # الحد الأقصى للسجلات قبل الانهيار

# 2. إعدادات محطات الرمادي
STATIONS = {
    "مستشفى الرمادي التعليمي": {"max": 1000, "priority": 1},
    "معمل زجاج الرمادي": {"max": 1200, "priority": 2},
    "محطة مياه الورار": {"max": 900, "priority": 3},
    "جامعة الأنبار": {"max": 700, "priority": 4},
    "حي التأميم (سكني)": {"max": 500, "priority": 5}
}

# --- دوال النظام ---
def load_data():
    if not os.path.exists(DB_FILE): 
        return {"entries": [], "collapsed": False}
    try:
        with open(DB_FILE, "r", encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"entries": [], "collapsed": False}

def save_data(new_entries, protocol_active, force_collapse=False):
    try:
        data = load_data()
        if data.get("collapsed"): return
        
        if force_collapse:
            data["collapsed"] = True
        else:
            data["entries"].extend(new_entries)
            
            # منطق إدارة الضغط:
            # إذا البروتوكول فعال، نقوم بتصريف البيانات القديمة فوراً لإبقاء الضغط منخفضاً
            if protocol_active:
                data["entries"] = data["entries"][-10:] # الاحتفاظ بـ 10 فقط (ضغط منخفض)
            else:
                # بدون بروتوكول، نترك البيانات تتراكم حتى الحد الأقصى
                data["entries"] = data["entries"][-MAX_CAPACITY:]
                
        with open(DB_FILE, "w", encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except:
        pass

def create_reading(name, prev_val):
    limit = STATIONS[name]["max"]
    
    # خوارزمية التغير التدريجي (Smooth Variation):
    # بدلاً من العشوائية المطلقة، نغير القيمة السابقة بنسبة +/- 2% فقط
    change = random.uniform(-0.02, 0.02) * limit
    new_val = prev_val + change
    
    # التأكد من بقاء القيمة ضمن حدود المعقول (40% إلى 105% من الحمل)
    new_val = max(limit * 0.4, min(new_val, limit * 1.05))
    
    # تحديد الحالة (تقليل احتمالية الخطر بجعلها تبدأ من 96% من الحمل)
    if new_val < (limit * 0.85): status, level = "🟢 مستقر", 1
    elif (limit * 0.85) <= new_val < (limit * 0.96): status, level = "🟡 تنبيه", 2
    else: status, level = "🔴 خطر", 3 # خطر نادر

    return int(new_val), {
        "المنشأة": name, "التيار (A)": int(new_val), "الحالة": status,
        "الوقت": datetime.now().strftime("%H:%M:%S"),
        "timestamp": time.time(), "level": level, 
        "priority": STATIONS[name]["priority"], "batch_id": time.time()
    }

# --- القائمة الجانبية ---
st.sidebar.title("⚡ تحكم كهرباء الأنبار")
page = st.sidebar.radio("القوائم:", ["🕹️ غرفة التحكم", "🖥️ شاشة المراقبة"])
protocol_on = st.sidebar.toggle("🛡️ تفعيل بروتوكول الحماية", value=True)

if st.sidebar.button("♻️ إعادة ضبط (Reset)"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.session_state.clear()
    st.rerun()

# ==========================================
# الصفحة 1: غرفة التحكم
# ==========================================
if page == "🕹️ غرفة التحكم":
    st.title("🕹️ وحدة إرسال الإشارات الميدانية")
    
    state = load_data()
    if state.get("collapsed"):
        st.error("❌ النظام منهار! اضغط Reset للإصلاح.")
    else:
        run = st.checkbox("🚀 تشغيل البث التلقائي الواقعي")
        if run:
            placeholder = st.empty()
            # تهيئة القيم الأولية في الذاكرة
            if 'last_vals' not in st.session_state:
                st.session_state.last_vals = {n: STATIONS[n]["max"]*0.7 for n in STATIONS}

            while run:
                if load_data().get("collapsed"): break
                
                batch = []
                for n in STATIONS:
                    new_val, log = create_reading(n, st.session_state.last_vals[n])
                    st.session_state.last_vals[n] = new_val
                    batch.append(log)
                
                save_data(batch, protocol_on)
                with placeholder.container():
                    st.write(f"✅ يتم البث تدريجياً... {datetime.now().strftime('%H:%M:%S')}")
                time.sleep(1)
        
        st.write("---")
        st.write("🔧 التحكم اليدوي السلس:")
        for name in STATIONS:
            val = st.slider(f"{name}", 0, 1500, value=int(STATIONS[name]["max"]*0.7), key=name)
            if st.session_state.get(f"m_{name}") != val:
                save_data([create_reading(name, val)[1]], protocol_on)
                st.session_state[f"m_{name}"] = val

# ==========================================
# الصفحة 2: شاشة المراقبة
# ==========================================
else:
    st.title("🖥️ مركز مراقبة شبكة الرمادي")
    
    placeholder = st.empty()
    while True:
        data_store = load_data()
        entries = data_store.get("entries", [])
        is_collapsed = data_store.get("collapsed", False)
        
        with placeholder.container():
            # 1. منطق الانهيار الحتمي
            if not protocol_on and len(entries) >= MAX_CAPACITY and not is_collapsed:
                save_data([], protocol_on, force_collapse=True)
                st.rerun()

            if is_collapsed:
                st.markdown("""
                <div style='background-color:black; padding:50px; border: 10px solid red; text-align:center;'>
                    <h1 style='color:red; font-size: 70px;'>⚠️ SYSTEM FAILURE ⚠️</h1>
                    <h2 style='color:white;'>انهيار بسبب تجاوز سعة المعالجة (100%)</h2>
                </div>
                """, unsafe_allow_html=True)
                
                break

            if not entries:
                st.info("بانتظار البيانات...")
            else:
                # 2. مؤشر الضغط (لا يتجاوز 100%)
                pressure = (len(entries) / MAX_CAPACITY) * 100
                p_color = "green" if protocol_on else "red"
                st.markdown(f"### مؤشر ضغط البيانات: :{p_color}[{int(pressure)}%]")
                st.progress(min(pressure, 100) / 100)

                df = pd.DataFrame(entries)
                
                if protocol_on:
                    # البروتوكول يفرز ويحمي السيرفر
                    df_display = df.sort_values(by=["level", "priority", "timestamp"], ascending=[False, True, False])
                    st.success("✅ البروتوكول فعال: يتم تصريف الأحمال بانتظام.")
                else:
                    df_display = df.sort_values(by="timestamp", ascending=False)
                    st.warning("⚠️ تحذير: البروتوكول معطل! السيرفر يمتلئ بالبيانات.")

                # الرسم البياني السلس
                st.subheader("📊 مخطط توزيع الأحمال اللحظي")
                chart_df = df.pivot_table(index='الوقت', columns='المنشأة', values='التيار (A)').ffill()
                st.line_chart(chart_df, height=250)
                

                # الجدول
                def style_row(row):
                    if row['level'] == 3: return ['background-color: #8b0000; color: white'] * len(row)
                    if row['level'] == 2: return ['background-color: #705d00; color: white'] * len(row)
                    return [''] * len(row)

                st.dataframe(
                    df_display[["المنشأة", "التيار (A)", "الحالة", "الوقت", "level"]].style.apply(style_row, axis=1),
                    use_container_width=True, height=450, column_config={"level": None}
                )
        
        time.sleep(1)
                
