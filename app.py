import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# 1. إعدادات الصفحة الأساسية
st.set_page_config(page_title="نظام طاقة الأنبار - محاكاة الانهيار", layout="wide")

DB_FILE = "anbar_grid_data.json"

# 2. محطات الرمادي الواقعية وقدراتها
STATIONS = {
    "مستشفى الرمادي التعليمي": {"max": 1000, "priority": 1},
    "معمل زجاج الرمادي": {"max": 1200, "priority": 2},
    "محطة مياه الورار": {"max": 900, "priority": 3},
    "جامعة الأنبار": {"max": 700, "priority": 4},
    "حي التأميم (سكني)": {"max": 500, "priority": 5}
}

# --- دوال الملفات (النظام القديم) ---
def load_data():
    if not os.path.exists(DB_FILE): 
        return {"entries": [], "collapsed": False}
    try:
        with open(DB_FILE, "r", encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"entries": [], "collapsed": False}

def save_data(new_entries, force_collapse=False):
    try:
        data = load_data()
        if data.get("collapsed", False): return # لا تسجل إذا النظام منهار
        
        if force_collapse:
            data["collapsed"] = True
        else:
            data["entries"].extend(new_entries)
            # نحتفظ بآخر 100 سجل فقط
            data["entries"] = data["entries"][-100:]
            
        with open(DB_FILE, "w", encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except:
        pass

def create_log(name, current, batch_id):
    limit = STATIONS[name]["max"]
    if current < (limit * 0.8): status, level = "🟢 مستقر", 1
    elif (limit * 0.8) <= current < (limit * 0.95): status, level = "🟡 تنبيه", 2
    else: status, level = "🔴 خطر", 3
    return {
        "المنشأة": name, "التيار (A)": current, "الحالة": status,
        "الوقت": datetime.now().strftime("%H:%M:%S"),
        "timestamp": time.time(), "level": level, 
        "priority": STATIONS[name]["priority"], "batch_id": batch_id
    }

# --- القائمة الجانبية ---
st.sidebar.title("⚡ مركز سيطرة الرمادي")
page = st.sidebar.radio("القوائم:", ["🕹️ غرفة التحكم", "🖥️ شاشة المراقبة"])
st.sidebar.markdown("---")
# المفتاح الذهبي: إذا عطلت هذا، النظام سينهار عند الضغط
protocol_on = st.sidebar.toggle("تفعيل بروتوكول الحماية", value=True)

if st.sidebar.button("♻️ إعادة تشغيل (Reset)"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.rerun()

# ==========================================
# الصفحة 1: غرفة التحكم (الإرسال)
# ==========================================
if page == "🕹️ غرفة التحكم":
    st.title("🕹️ وحدة إرسال البيانات")
    
    state = load_data()
    if state.get("collapsed"):
        st.error("❌ الشبكة منهارة تماماً! اضغط Reset من القائمة الجانبية للإصلاح.")
    else:
        mode = st.selectbox("نمط العمل:", ["بث تلقائي (5 مواقع)", "يدوي (تحكم بالشريط)"])
        
        if mode == "بث تلقائي (5 مواقع)":
            run = st.checkbox("تشغيل البث المستمر")
            if run:
                placeholder = st.empty()
                while run:
                    # فحص الانهيار لحظياً
                    if load_data().get("collapsed"): break
                    
                    batch_id = time.time()
                    batch = []
                    for n in STATIONS:
                        val = random.randint(int(STATIONS[n]["max"]*0.7), int(STATIONS[n]["max"]*1.1))
                        batch.append(create_log(n, val, batch_id))
                    
                    save_data(batch)
                    with placeholder.container():
                        st.write(f"📡 يتم إرسال نبضات شاملة للشبكة... {datetime.now().strftime('%H:%M:%S')}")
                    time.sleep(1)
                    
        else:
            batch_id = time.time()
            for name in STATIONS:
                val = st.slider(f"{name}", 0, 1500, value=STATIONS[name]["max"]-100, key=name)
                # الإرسال بمجرد تحريك الشريط
                if st.session_state.get(f"prev_{name}") != val:
                    save_data([create_log(name, val, batch_id)])
                    st.session_state[f"prev_{name}"] = val

# ==========================================
# الصفحة 2: شاشة المراقبة (حيث يحدث الانهيار)
# ==========================================
else:
    st.title("🖥️ مركز مراقبة الشبكة")
    
    placeholder = st.empty()
    
    while True:
        data_store = load_data()
        entries = data_store.get("entries", [])
        is_collapsed = data_store.get("collapsed", False)
        
        with placeholder.container():
            # 1. منطق الانهيار الحتمي عند ضغط البيانات
            # إذا كان عدد السجلات > 25 والبروتوكول مطفأ -> النظام ينهار فوراً
            if not protocol_on and len(entries) > 25 and not is_collapsed:
                save_data([], force_collapse=True)
                st.rerun()

            # 2. عرض شاشة الانهيار
            if is_collapsed:
                st.markdown("""
                <div style='background-color:black; padding:50px; border: 10px solid red; text-align:center;'>
                    <h1 style='color:red; font-size: 70px;'>⚠️ SYSTEM FAILURE ⚠️</h1>
                    <h2 style='color:white;'>Buffer Overflow: 150% Load</h2>
                    <p style='color:white; font-size:20px;'>انهارت الشبكة الوطنية في الأنبار بسبب تكدس البيانات وعدم وجود بروتوكول معالجة.</p>
                </div>
                """, unsafe_allow_html=True)
                
                break

            # 3. العرض الطبيعي
            if not entries:
                st.info("بانتظار وصول البيانات من غرفة التحكم...")
            else:
                # حساب مؤشر الضغط
                pressure = len(entries) * 4 # كل سجل يمثل 4% ضغط
                color = "green" if protocol_on else "red"
                st.markdown(f"### مؤشر ضغط البيانات: :{color}[{pressure}%]")
                st.progress(min(pressure, 100) / 100)

                df = pd.DataFrame(entries)
                
                # تطبيق البروتوكول (الترتيب)
                if protocol_on:
                    df_display = df.sort_values(by=["batch_id", "level", "priority"], ascending=[False, False, True])
                    st.success("✅ البروتوكول فعال: يتم تصريف الضغط وحماية السيرفر.")
                else:
                    df_display = df.sort_values(by="timestamp", ascending=False)
                    st.warning("⚠️ تحذير: البروتوكول معطل! الضغط يتراكم (Queue is filling up).")

                # الرسم البياني
                st.line_chart(df.tail(40).pivot_table(index='الوقت', columns='المنشأة', values='التيار (A)'), height=250)
                

                # الجدول
                def style_func(row):
                    if row['level'] == 3: return ['background-color: #8b0000; color: white'] * len(row)
                    if row['level'] == 2: return ['background-color: #705d00; color: white'] * len(row)
                    return [''] * len(row)

                st.dataframe(
                    df_display[["المنشأة", "التيار (A)", "الحالة", "الوقت", "level"]].style.apply(style_func, axis=1),
                    use_container_width=True, height=500, column_config={"level": None}
                )
        
        time.sleep(1)
    
