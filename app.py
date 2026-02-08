import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام طاقة الأنبار - محاكاة الانهيار", layout="wide")

DB_FILE = "anbar_crash_sim.json"

# 2. إعدادات المحطات
STATIONS = {
    "مستشفى الرمادي التعليمي": {"max": 1000, "priority": 1},
    "معمل زجاج الرمادي": {"max": 1200, "priority": 2},
    "محطة مياه الورار": {"max": 900, "priority": 3},
    "جامعة الأنبار": {"max": 700, "priority": 4},
    "حي التأميم (سكني)": {"max": 500, "priority": 5}
}

# --- دوال الملفات ---
def load_data():
    if not os.path.exists(DB_FILE): return {"entries": [], "collapsed": False}
    try:
        with open(DB_FILE, "r", encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"entries": [], "collapsed": False}

def save_data(new_entries, force_collapse=False):
    try:
        data = load_data()
        
        # إذا النظام منهار، لا تحفظ أي شيء جديد
        if data["collapsed"]: return

        if force_collapse:
            data["collapsed"] = True
        else:
            data["entries"].extend(new_entries)
            # نحتفظ بآخر 150 سجل
            data["entries"] = data["entries"][-150:]
        
        with open(DB_FILE, "w", encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except:
        pass

def reset_system():
    empty_db = {"entries": [], "collapsed": False}
    with open(DB_FILE, "w", encoding='utf-8') as f:
        json.dump(empty_db, f, ensure_ascii=False, indent=4)

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
st.sidebar.title("⚡ مركز السيطرة")
page = st.sidebar.radio("القوائم:", ["🕹️ غرفة التحكم", "🖥️ شاشة المراقبة"])
st.sidebar.markdown("---")
protocol_active = st.sidebar.toggle("تفعيل بروتوكول الحماية", value=True)

if st.sidebar.button("🔴 إعادة تشغيل النظام (Reset)"):
    reset_system()
    st.rerun()

# ==========================================
# الصفحة الأولى: غرفة التحكم
# ==========================================
if page == "🕹️ غرفة التحكم":
    st.title("🕹️ وحدة الضغط والإرسال")
    
    mode = st.selectbox("نمط العمل:", ["بث تلقائي (ضغط عالي)", "إرسال يدوي"])
    
    if mode == "بث تلقائي (ضغط عالي)":
        st.info("هذا الوضع يرسل كميات ضخمة من البيانات لمحاكاة الضغط.")
        run_auto = st.checkbox("تشغيل البث المستمر")
        
        if run_auto:
            placeholder = st.empty()
            while run_auto:
                # التحقق مما إذا انهار النظام
                current_state = load_data()
                if current_state["collapsed"]:
                    st.error("❌ توقف الإرسال: الشبكة انهارت! اضغط Reset من القائمة الجانبية.")
                    break

                # توليد بيانات
                batch_id = time.time()
                batch = []
                for name in STATIONS:
                    val = random.randint(int(STATIONS[name]["max"]*0.7), int(STATIONS[name]["max"]*1.2))
                    batch.append(create_reading(name, val, batch_id))
                
                # === محاكاة الانهيار ===
                # إذا البروتوكول مطفأ، وهناك بيانات كثيرة (>20)، نرسل إشارة الانهيار
                if not protocol_active and len(current_state["entries"]) > 20:
                    # احتمالية الانهيار تزيد مع كل ثانية
                    if random.random() < 0.3: # 30% احتمال انهيار في كل نبضة
                        save_data([], force_collapse=True)
                        continue

                save_data(batch)
                with placeholder.container():
                    st.write(f"📡 جاري ضخ البيانات... الوقت: {datetime.now().strftime('%H:%M:%S')}")
                
                time.sleep(0.8) # سرعة عالية قليلاً

    else:
        st.write("إرسال يدوي دقيق:")
        batch_id = time.time()
        for name in STATIONS:
            col1, col2 = st.columns([3, 1])
            with col1:
                val = st.slider(f"{name}", 0, int(STATIONS[name]["max"]*1.3), value=int(STATIONS[name]["max"]*0.6), key=name)
            with col2:
                if st.button(f"إرسال {name}"):
                    save_data([create_reading(name, val, batch_id)])
                    st.toast(f"تم إرسال {name}")

# ==========================================
# الصفحة الثانية: شاشة المراقبة
# ==========================================
else:
    st.title("🖥️ مركز مراقبة الشبكة")
    
    placeholder = st.empty()
    
    while True:
        data_packet = load_data()
        entries = data_packet["entries"]
        is_collapsed = data_packet["collapsed"]
        
        with placeholder.container():
            # 1. حالة الانهيار (الشاشة السوداء/الحمراء)
            if is_collapsed:
                st.markdown("""
                    <div style='background-color:black; padding:40px; border: 5px solid red; text-align:center;'>
                        <h1 style='color:red; font-size: 60px;'>⚠️ SYSTEM FAILURE ⚠️</h1>
                        <h3 style='color:white;'>Network Congestion Detected</h3>
                        <p style='color:white;'>انهارت الشبكة بسبب الضغط العالي وعدم تفعيل بروتوكول الحماية.</p>
                        <hr>
                        <p style='color:yellow;'>الحل: اضغط زر "إعادة تشغيل النظام" وقم بتفعيل البروتوكول.</p>
                    </div>
                """, unsafe_allow_html=True)
                
            
            # 2. الحالة الطبيعية
            elif not entries:
                st.warning("⚠️ لا توجد بيانات. ابدأ البث من غرفة التحكم.")
            else:
                df = pd.DataFrame(entries)
                
                # حساب "مؤشر الضغط" للعرض
                buffer_usage = len(df)
                if not protocol_active:
                    st.error(f"⚠️ تحذير: البروتوكول معطل! ضغط الشبكة: {buffer_usage}% (خطر الانهيار)")
                    # شريط تقدم يوضح اقتراب الانهيار
                    st.progress(min(buffer_usage, 100) / 100)
                else:
                    st.success(f"✅ البروتوكول فعال. يتم معالجة الضغط بذكاء.")
                    st.progress(0.1) # ضغط منخفض دائماً

                # الترتيب والعرض
                if protocol_active:
                    df_display = df.sort_values(by=["batch_id", "level", "priority"], ascending=[False, False, True])
                else:
                    df_display = df.sort_values(by="timestamp", ascending=False)

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
        
        # إذا انهار النظام، نوقف التحديث لتجميد الشاشة على الخطأ
        if is_collapsed:
            break
            
        time.sleep(1)
                
