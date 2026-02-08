import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام طاقة الأنبار - محاكاة الانهيار", layout="wide")

DB_FILE = "ramadi_crash_system.json"
MAX_LOAD_CAPACITY = 100  # السيرفر يتحمل 100 وحدة ضغط فقط

# 2. إعدادات المحطات
STATIONS = {
    "مستشفى الرمادي التعليمي": {"max": 1000, "priority": 1},
    "معمل زجاج الرمادي": {"max": 1200, "priority": 2},
    "محطة مياه الورار": {"max": 900, "priority": 3},
    "جامعة الأنبار": {"max": 700, "priority": 4},
    "حي التأميم (سكني)": {"max": 500, "priority": 5}
}

# --- دوال التعامل مع الملفات ---
def load_state():
    if not os.path.exists(DB_FILE): 
        return {"entries": [], "server_load": 0, "collapsed": False}
    try:
        with open(DB_FILE, "r", encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"entries": [], "server_load": 0, "collapsed": False}

def save_state(entries, protocol_active):
    try:
        state = load_state()
        
        # إذا النظام منهار، لا تفعل شيئاً
        if state["collapsed"]: return

        # === منطق الانهيار الحتمي ===
        if not protocol_active:
            # بدون بروتوكول: الضغط يتراكم بسرعة (كل دفعة تزيد الضغط 15 درجة)
            state["server_load"] += 15
        else:
            # مع البروتوكول: النظام يعالج البيانات (الضغط مستقر ومنخفض)
            state["server_load"] = random.randint(5, 20)

        # التحقق من الانهيار
        if state["server_load"] >= MAX_LOAD_CAPACITY:
            state["collapsed"] = True
            state["server_load"] = 100 # تثبيت العداد على 100
        else:
            state["entries"].extend(entries)
            state["entries"] = state["entries"][-100:] # الاحتفاظ بآخر 100 سجل

        with open(DB_FILE, "w", encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=4)
    except:
        pass

def reset_system():
    initial_state = {"entries": [], "server_load": 0, "collapsed": False}
    with open(DB_FILE, "w", encoding='utf-8') as f:
        json.dump(initial_state, f, ensure_ascii=False, indent=4)

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

# زر البروتوكول (هو المتحكم في الانهيار)
protocol_active = st.sidebar.toggle("تفعيل بروتوكول الحماية", value=True)

if st.sidebar.button("♻️ إعادة تشغيل النظام (Reset)"):
    reset_system()
    st.rerun()

# ==========================================
# الصفحة الأولى: غرفة التحكم
# ==========================================
if page == "🕹️ غرفة التحكم":
    st.title("🕹️ وحدة ضخ البيانات")
    
    st.info("ملاحظة: إذا عطلت البروتوكول، سيرتفع عداد الضغط حتى ينهار النظام.")
    
    mode = st.selectbox("نمط العمل:", ["بث تلقائي (ضغط مستمر)", "إرسال يدوي"])
    
    if mode == "بث تلقائي (ضغط مستمر)":
        run_auto = st.checkbox("تشغيل البث")
        
        if run_auto:
            placeholder = st.empty()
            while run_auto:
                # فحص الانهيار قبل الإرسال
                state = load_state()
                if state["collapsed"]:
                    st.error("❌ توقف الإرسال: الشبكة منهارة!")
                    break

                batch_id = time.time()
                batch = []
                for name in STATIONS:
                    val = random.randint(int(STATIONS[name]["max"]*0.7), int(STATIONS[name]["max"]*1.2))
                    batch.append(create_reading(name, val, batch_id))
                
                # حفظ البيانات (وتحديث عداد الضغط حسب حالة البروتوكول)
                save_state(batch, protocol_active)
                
                with placeholder.container():
                    st.write(f"📡 تم إرسال دفعة بيانات... {datetime.now().strftime('%H:%M:%S')}")
                
                time.sleep(1) # إرسال كل ثانية
    else:
        # الوضع اليدوي
        batch_id = time.time()
        for name in STATIONS:
            col1, col2 = st.columns([3, 1])
            with col1:
                val = st.slider(f"{name}", 0, int(STATIONS[name]["max"]*1.3), value=int(STATIONS[name]["max"]*0.6))
            with col2:
                if st.button(f"إرسال {name}"):
                    save_state([create_reading(name, val, batch_id)], protocol_active)
                    st.toast(f"تم إرسال {name}")

# ==========================================
# الصفحة الثانية: شاشة المراقبة
# ==========================================
else:
    st.title("🖥️ مركز مراقبة الشبكة")
    
    placeholder = st.empty()
    
    while True:
        state = load_state()
        entries = state["entries"]
        current_load = state["server_load"]
        is_collapsed = state["collapsed"]
        
        with placeholder.container():
            # 1. حالة الانهيار التام
            if is_collapsed:
                st.markdown(f"""
                    <div style='background-color:black; padding:50px; border: 5px solid red; text-align:center;'>
                        <h1 style='color:red; font-size: 80px;'>⚠️ SYSTEM FAILURE ⚠️</h1>
                        <h2 style='color:white;'>SERVER LOAD: {current_load}% (CRITICAL)</h2>
                        <hr>
                        <p style='color:yellow; font-size: 20px;'>انهار النظام بسبب تراكم البيانات (Buffer Overflow).</p>
                        <p style='color:white;'>الحل: قم بتفعيل البروتوكول واضغط "إعادة تشغيل النظام".</p>
                    </div>
                """, unsafe_allow_html=True)
                # نوقف الكود هنا حتى يتم عمل Reset
                break 

            # 2. العرض الطبيعي
            if not entries:
                st.info("النظام جاهز. ابدأ البث.")
            else:
                # عرض شريط الحمل (Server Load)
                load_color = "green" if current_load < 50 else "red"
                st.markdown(f"**حمل السيرفر (Server Load):** :{load_color}[{current_load}%]")
                st.progress(current_load / 100)

                df = pd.DataFrame(entries)
                
                # الترتيب حسب البروتوكول
                if protocol_active:
                    df_display = df.sort_values(by=["batch_id", "level", "priority"], ascending=[False, False, True])
                    st.success("✅ البروتوكول فعال: الحمل مستقر.")
                else:
                    df_display = df.sort_values(by="timestamp", ascending=False)
                    st.warning("⚠️ تحذير: البروتوكول معطل! الحمل يرتفع بسرعة!")

                # الرسم والجدول
                st.line_chart(df.tail(50).pivot_table(index='الوقت', columns='المنشأة', values='التيار (A)'), height=250)
                
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
        
