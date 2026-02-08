import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام طاقة الأنبار - محاكاة الانهيار", layout="wide")

# ملفات النظام
DATA_FILE = "grid_final_data.json"
STATE_FILE = "grid_state.json"

# 2. إعدادات المحطات
STATIONS = {
    "مستشفى الرمادي التعليمي": {"max": 1000, "priority": 1},
    "معمل زجاج الرمادي": {"max": 1200, "priority": 2},
    "محطة مياه الورار": {"max": 900, "priority": 3},
    "جامعة الأنبار": {"max": 700, "priority": 4},
    "حي التأميم (سكني)": {"max": 500, "priority": 5}
}

# --- دوال التعامل مع الملفات ---
def get_state():
    if not os.path.exists(STATE_FILE):
        return {"load": 0, "collapsed": False, "streaming": False}
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {"load": 0, "collapsed": False, "streaming": False}

def update_state(new_state):
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(new_state, f)
    except:
        pass

def load_data():
    if not os.path.exists(DATA_FILE): return []
    try:
        with open(DATA_FILE, "r", encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_data(new_batch):
    try:
        history = load_data()
        history.extend(new_batch)
        with open(DATA_FILE, "w", encoding='utf-8') as f:
            json.dump(history[-100:], f, ensure_ascii=False, indent=4)
    except:
        pass

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

# زر البروتوكول (هو المتحكم الرئيسي)
protocol_active = st.sidebar.toggle("تفعيل بروتوكول الحماية", value=True)

if st.sidebar.button("🔴 إعادة ضبط النظام (Reset)"):
    # تصفير كل شيء
    update_state({"load": 0, "collapsed": False, "streaming": False})
    if os.path.exists(DATA_FILE): os.remove(DATA_FILE)
    st.rerun()

# ==========================================
# الصفحة الأولى: غرفة التحكم
# ==========================================
if page == "🕹️ غرفة التحكم":
    st.title("🕹️ وحدة ضخ البيانات")
    
    st.info("قم بتفعيل البث من هنا، ثم انتقل لشاشة المراقبة لرؤية النتائج.")
    
    # قراءة الحالة الحالية
    state = get_state()
    
    # زر تشغيل البث (يخزن الحالة في الملف)
    if st.checkbox("تشغيل البث المستمر", value=state["streaming"]):
        state["streaming"] = True
        update_state(state)
        st.success("📡 البث نشط! انتقل الآن لشاشة المراقبة.")
        
        # محاكاة إرسال بيانات (لكي يرى المستخدم شيئاً هنا أيضاً)
        if st.button("إرسال دفعة يدوية"):
            batch_id = time.time()
            batch = [create_reading(n, random.randint(400, 1000), batch_id) for n in STATIONS]
            save_data(batch)
            st.toast("تم الإرسال")
    else:
        state["streaming"] = False
        update_state(state)

# ==========================================
# الصفحة الثانية: شاشة المراقبة
# ==========================================
else:
    st.title("🖥️ مركز مراقبة الشبكة")
    
    placeholder = st.empty()
    
    # حلقة التحديث المستمر (هنا يحدث السحر)
    while True:
        # 1. قراءة الحالة والبيانات
        state = get_state()
        data = load_data()
        
        with placeholder.container():
            # أ. شاشة الانهيار
            if state["collapsed"]:
                st.markdown(f"""
                    <div style='background-color:black; padding:50px; border: 5px solid red; text-align:center;'>
                        <h1 style='color:red; font-size: 80px;'>⚠️ SYSTEM FAILURE ⚠️</h1>
                        <h2 style='color:white;'>SERVER LOAD: 100%</h2>
                        <hr>
                        <p style='color:yellow; font-size: 24px;'>تم اختراق سعة السيرفر وانهيار الشبكة!</p>
                        <p style='color:white;'>السبب: تدفق بيانات عالي بدون بروتوكول حماية.</p>
                    </div>
                """, unsafe_allow_html=True)
                
                # إيقاف التحديث لتجميد الشاشة
                time.sleep(5) 
                continue

            # ب. منطق زيادة الضغط (داخل شاشة المراقبة)
            if state["streaming"]:
                # توليد بيانات وهمية وكأنها قادمة من المحطات
                batch_id = time.time()
                new_batch = [create_reading(n, random.randint(int(STATIONS[n]["max"]*0.7), int(STATIONS[n]["max"]*1.1)), batch_id) for n in STATIONS]
                save_data(new_batch)
                data.extend(new_batch)
                
                # === المنطق الحاسم للانهيار ===
                if not protocol_active:
                    # بدون بروتوكول: الضغط يرتفع بسرعة (20% كل ثانية)
                    state["load"] += 20
                else:
                    # مع البروتوكول: الضغط ينخفض ومستقر
                    state["load"] = 10
                
                # التحقق من الحد الأقصى
                if state["load"] >= 100:
                    state["load"] = 100
                    state["collapsed"] = True
                
                # حفظ الحالة الجديدة
                update_state(state)

            # ج. عرض البيانات
            if not data and not state["streaming"]:
                st.warning("⚠️ بانتظار تشغيل البث من غرفة التحكم...")
            else:
                # عرض شريط الضغط
                load_val = state["load"]
                load_color = "green" if load_val < 50 else "red"
                st.markdown(f"### 🌡️ ضغط السيرفر: :{load_color}[{load_val}%]")
                st.progress(load_val / 100)

                df = pd.DataFrame(data)
                if not df.empty:
                    # الترتيب
                    if protocol_active:
                        df_display = df.sort_values(by=["batch_id", "level", "priority"], ascending=[False, False, True])
                        st.success("✅ البروتوكول فعال: حماية النظام نشطة.")
                    else:
                        df_display = df.sort_values(by="timestamp", ascending=False)
                        st.error("⚠️ تحذير: البروتوكول معطل! خطر الانهيار وشيك!")

                    # الرسم البياني
                    st.line_chart(df.tail(40).pivot_table(index='الوقت', columns='المنشأة', values='التيار (A)'), height=250)

                    # الجدول
                    def highlight(row):
                        if row['level'] == 3: return ['background-color: #8b0000; color: white'] * len(row)
                        if row['level'] == 2: return ['background-color: #705d00; color: white'] * len(row)
                        return [''] * len(row)

                    st.dataframe(
                        df_display[["المنشأة", "التيار (A)", "الحالة", "الوقت"]].style.apply(highlight, axis=1),
                        use_container_width=True,
                        height=400
                    )
        
        # انتظار ثانية قبل التحديث التالي
        time.sleep(1)
