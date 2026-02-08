import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام طاقة الأنبار - محاكاة الانهيار", layout="wide")

# ملف البيانات وملف الحالة (فصلناهما لضمان السرعة)
DATA_FILE = "grid_data.json"
STATUS_FILE = "grid_status.json"

# 2. إعدادات المحطات
STATIONS = {
    "مستشفى الرمادي التعليمي": {"max": 1000, "priority": 1},
    "معمل زجاج الرمادي": {"max": 1200, "priority": 2},
    "محطة مياه الورار": {"max": 900, "priority": 3},
    "جامعة الأنبار": {"max": 700, "priority": 4},
    "حي التأميم (سكني)": {"max": 500, "priority": 5}
}

# --- دوال التعامل مع الملفات (محسنة) ---
def get_status():
    if not os.path.exists(STATUS_FILE):
        return {"load": 0, "collapsed": False}
    try:
        with open(STATUS_FILE, "r") as f:
            return json.load(f)
    except:
        return {"load": 0, "collapsed": False}

def update_status(load_increment, protocol_active):
    status = get_status()
    
    # إذا النظام منهار، لا تفعل شيئاً
    if status["collapsed"]: return status

    if not protocol_active:
        # بدون بروتوكول: زيادة الضغط بقوة (20% كل مرة)
        status["load"] += 20
    else:
        # مع البروتوكول: تفريغ الضغط
        status["load"] = max(0, status["load"] - 10) # ينقص الضغط
        if status["load"] < 5: status["load"] = random.randint(1, 5)

    # التحقق من الانهيار
    if status["load"] >= 100:
        status["load"] = 100
        status["collapsed"] = True
    
    # حفظ الحالة
    try:
        with open(STATUS_FILE, "w") as f:
            json.dump(status, f)
    except:
        pass
    return status

def load_entries():
    if not os.path.exists(DATA_FILE): return []
    try:
        with open(DATA_FILE, "r", encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_entries(new_batch):
    try:
        history = load_entries()
        history.extend(new_batch)
        with open(DATA_FILE, "w", encoding='utf-8') as f:
            json.dump(history[-100:], f, ensure_ascii=False, indent=4)
    except:
        pass

def reset_all():
    # تصفير كل شيء
    with open(STATUS_FILE, "w") as f:
        json.dump({"load": 0, "collapsed": False}, f)
    with open(DATA_FILE, "w", encoding='utf-8') as f:
        json.dump([], f, ensure_ascii=False)

def create_reading(name, current, batch_id):
    limit = STATIONS[name]["max"]
    if current < (limit * 0.8): status, level = "🟢 مستقر", 1
    elif (limit * 0.8) <= current < (limit * 0.95): status, level = "🟡 تنبيه", 2
    else: status, level = "🔴 خطر", 3

    return {
        "المنشأة": name, "التيار (A)": current, "الحالة": status,
        "الوقت": datetime.now().strftime("%H:%M:%S"),
        "timestamp": time.time(), "level": level, "priority": STATIONS[name]["priority"],
        "batch_id": batch_id
    }

# --- القائمة الجانبية ---
st.sidebar.title("⚡ مركز سيطرة الأنبار")
page = st.sidebar.radio("القوائم:", ["🕹️ غرفة التحكم", "🖥️ شاشة المراقبة"])
st.sidebar.markdown("---")

# زر البروتوكول
protocol_active = st.sidebar.toggle("تفعيل بروتوكول الحماية", value=True)

if st.sidebar.button("🔴 إعادة ضبط النظام (Reset)"):
    reset_all()
    st.rerun()

# ==========================================
# الصفحة الأولى: غرفة التحكم
# ==========================================
if page == "🕹️ غرفة التحكم":
    st.title("🕹️ وحدة ضخ البيانات")
    
    st.info("تعليمات: أطفئ البروتوكول وشغل البث لرؤية الانهيار.")
    
    run_auto = st.checkbox("تشغيل البث المستمر")
    
    if run_auto:
        placeholder = st.empty()
        while run_auto:
            # تحديث حالة السيرفر (الضغط)
            current_status = update_status(20, protocol_active)
            
            if current_status["collapsed"]:
                st.error("❌ توقف الإرسال: الشبكة منهارة (System Crashed)!")
                break
            
            # توليد وإرسال البيانات
            batch_id = time.time()
            batch = []
            for name in STATIONS:
                val = random.randint(int(STATIONS[name]["max"]*0.7), int(STATIONS[name]["max"]*1.2))
                batch.append(create_reading(name, val, batch_id))
            
            save_entries(batch)
            
            with placeholder.container():
                st.write(f"📡 جاري الإرسال... ضغط الشبكة الحالي: {current_status['load']}%")
            
            time.sleep(1) # ثانية واحدة بين كل نبضة

# ==========================================
# الصفحة الثانية: شاشة المراقبة
# ==========================================
else:
    st.title("🖥️ مركز مراقبة الشبكة")
    
    placeholder = st.empty()
    
    while True:
        status = get_status()
        entries = load_entries()
        
        with placeholder.container():
            # 1. شاشة الانهيار
            if status["collapsed"]:
                st.markdown(f"""
                    <div style='background-color:black; padding:50px; border: 5px solid red; text-align:center;'>
                        <h1 style='color:red; font-size: 70px;'>⚠️ SYSTEM FAILURE ⚠️</h1>
                        <h2 style='color:white;'>SERVER LOAD: 100%</h2>
                        <hr>
                        <p style='color:yellow; font-size: 20px;'>سبب الانهيار: تراكم البيانات بدون بروتوكول معالجة.</p>
                        <p style='color:white;'>الحل: قم بتفعيل البروتوكول واضغط "إعادة ضبط النظام".</p>
                    </div>
                """, unsafe_allow_html=True)
                break # نوقف التحديث

            # 2. العرض الطبيعي
            if not entries:
                st.info("النظام جاهز. ابدأ البث من غرفة التحكم.")
            else:
                # عرض مؤشر الضغط
                load_val = status["load"]
                load_color = "green" if load_val < 50 else "red"
                st.markdown(f"### مؤشر ضغط السيرفر: :{load_color}[{load_val}%]")
                st.progress(load_val / 100)

                df = pd.DataFrame(entries)
                
                if protocol_active:
                    df_display = df.sort_values(by=["batch_id", "level", "priority"], ascending=[False, False, True])
                    st.success("✅ البروتوكول فعال: يقوم بتفريغ الضغط ومعالجة الأولويات.")
                else:
                    df_display = df.sort_values(by="timestamp", ascending=False)
                    st.warning("⚠️ تحذير: البروتوكول معطل! الضغط يرتفع بسرعة!")

                # الرسم البياني
                st.line_chart(df.tail(50).pivot_table(index='الوقت', columns='المنشأة', values='التيار (A)'), height=250)

                # الجدول
                def highlight(row):
                    if row['level'] == 3: return ['background-color: #8b0000; color: white'] * len(row)
                    if row['level'] == 2: return ['background-color: #705d00; color: white'] * len(row)
                    return [''] * len(row)

                st.dataframe(
                    df_display[["المنشأة", "التيار (A)", "الحالة", "الوقت", "level"]].style.apply(highlight, axis=1),
                    use_container_width=True,
                    height=500,
                    column_config={"level": None}
                )
        
        time.sleep(1)
