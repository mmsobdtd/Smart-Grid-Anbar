import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="نظام طاقة الأنبار - شاشة المراقبة المستقرة", layout="wide")

# تغيير اسم الملف لضمان البدء ببيانات نظيفة وتجنب أخطاء التنسيقات القديمة
DB_FILE = "anbar_data_final_v10.json"

STATIONS = {
    "مستشفى الرمادي التعليمي": {"max": 1000},
    "معمل زجاج الرمادي": {"max": 1200},
    "محطة مياه الورار": {"max": 900},
    "جامعة الأنبار": {"max": 700},
    "حي التأميم (سكني)": {"max": 500}
}

# --- 2. دوال النظام الأساسية ---
def load_data():
    if not os.path.exists(DB_FILE):
        return {"entries": [], "load_val": 0.0, "collapsed": False}
    try:
        with open(DB_FILE, "r", encoding='utf-8') as f:
            data = json.load(f)
            # التأكد من وجود المفاتيح الأساسية لتجنب الـ Crash
            if "entries" not in data: data["entries"] = []
            if "load_val" not in data: data["load_val"] = 0.0
            if "collapsed" not in data: data["collapsed"] = False
            return data
    except:
        return {"entries": [], "load_val": 0.0, "collapsed": False}

def save_data(data):
    try:
        # صمام أمان لقيمة الضغط
        data["load_val"] = float(max(0.0, min(data["load_val"], 100.0)))
        with open(DB_FILE, "w", encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except:
        pass

def apply_system_logic(new_readings, protocol_on):
    data = load_data()
    if data["collapsed"]: return data
    
    if new_readings:
        data["entries"].extend(new_readings)
        data["entries"] = data["entries"][-50:]
    
    if protocol_on:
        # استقرار عند 25%
        target = 25.0
        if data["load_val"] > (target + 2):
            data["load_val"] -= 10.0
        elif data["load_val"] < (target - 2):
            data["load_val"] += 2.0
        else:
            data["load_val"] = random.uniform(23.0, 27.0)
    else:
        if new_readings:
            data["load_val"] += len(new_readings) * 2.5
        else:
            data["load_val"] = max(0.0, data["load_val"] - 3.0) # تبريد أبطأ قليلاً
            
    if data["load_val"] >= 100.0:
        data["load_val"] = 100.0
        data["collapsed"] = True
    
    save_data(data)
    return data

# --- 3. واجهة المستخدم ---
st.sidebar.title("⚡ مركز سيطرة الرمادي")
page = st.sidebar.radio("القائمة:", ["🕹️ غرفة التحكم", "🖥️ شاشة المراقبة"])
protocol_active = st.sidebar.toggle("🛡️ تفعيل بروتوكول الحماية", value=False)

if st.sidebar.button("♻️ تصفير النظام"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.rerun()

# ==========================================
# صفحة التحكم (Control Room)
# ==========================================
if page == "🕹️ غرفة التحكم":
    st.title("🕹️ وحدة الإرسال الميداني")
    state = load_data()
    
    if state["collapsed"]:
        st.error("🚨 النظام متوقف بسبب الانهيار! اضغط Reset.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🔧 إرسال يدوي")
            for name, specs in STATIONS.items():
                val = st.slider(f"{name}", 0, 1500, value=int(specs['max']*0.6), key=f"s_{name}")
                if st.button(f"إرسال {name}", key=f"b_{name}"):
                    pct = (val / specs['max']) * 100
                    stt = "🔴 خطر" if pct >= 95 else "🟡 تنبيه" if pct >= 85 else "🟢 مستقر"
                    apply_system_logic([{
                        "المحطة": name, "التيار (A)": val, "الحالة": stt, 
                        "level": 3 if pct >= 95 else 2 if pct >= 85 else 1,
                        "timestamp": time.time(), "الوقت": datetime.now().strftime("%H:%M:%S")
                    }], protocol_active)
                    st.toast(f"بث موفق: {name}")

        with col2:
            st.subheader("🚀 البث التلقائي (4 محطات)")
            run_auto = st.checkbox("تشغيل البث المستمر")
            auto_place = st.empty()
            while run_auto:
                # التحقق من الحالة داخل الحلقة
                if load_data()["collapsed"]: st.rerun(); break
                
                selected = random.sample(list(STATIONS.keys()), 4)
                batch = []
                for n in selected:
                    s_max = STATIONS[n]['max']
                    v = random.randint(int(s_max*0.5), int(s_max*1.1))
                    pct = (v / s_max) * 100
                    stt = "🔴 خطر" if pct >= 95 else "🟡 تنبيه" if pct >= 85 else "🟢 مستقر"
                    batch.append({
                        "المحطة": n, "التيار (A)": v, "الحالة": stt, 
                        "level": 3 if pct >= 95 else 2 if pct >= 85 else 1,
                        "timestamp": time.time(), "الوقت": datetime.now().strftime("%H:%M:%S")
                    })
                apply_system_logic(batch, protocol_active)
                auto_place.info(f"📡 يتم ضخ البيانات... الضغط: {load_data()['load_val']:.1f}%")
                time.sleep(1)

# ==========================================
# صفحة المراقبة (Monitoring Room)
# ==========================================
else:
    st.title("🖥️ شاشة المراقبة المركزية")
    # مكان فارغ للتحديث اللحظي
    mon_placeholder = st.empty()
    
    while True:
        # 1. تحديث منطق النظام (تبريد أو بروتوكول)
        state = apply_system_logic([], protocol_active)
        
        with mon_placeholder.container():
            # حالة الانهيار
            if state["collapsed"]:
                st.error("🚨⚠️ النظام في حالة انهيار كامل (CRASH) ⚠️🚨")
                st.markdown("<h2 style='text-align:center; color:white;'>توقف تدفق الطاقة والبيانات</h2>", unsafe_allow_html=True)
                break
            
            # 2. عرض المؤشر (مع الحماية القصوى من الخطأ الذي ظهر سابقاً)
            v = float(state.get("load_val", 0.0))
            safe_v = max(0.0, min(v / 100.0, 1.0))
            
            p_color = "red" if v > 80 else "orange" if v > 40 else "green"
            st.markdown(f"### ضغط المنظومة: :{p_color}[{v:.1f}%]")
            st.progress(safe_v)
            
            # 3. عرض الجدول والرسوم
            if state["entries"]:
                try:
                    df = pd.DataFrame(state["entries"])
                    
                    # فرز البيانات حسب الطلب: (الأحمر أولاً ثم الأحدث) عند تفعيل البروتوكول
                    if protocol_active:
                        df_display = df.sort_values(by=['level', 'timestamp'], ascending=[False, False])
                    else:
                        df_display = df.sort_values(by='timestamp', ascending=False)

                    # تلوين الصفوف
                    def style_rows(row):
                        lvl = row.get('level', 1)
                        if lvl == 3: return ['background-color: #4d0000; color: white'] * len(row)
                        if lvl == 2: return ['background-color: #4d3d00; color: white'] * len(row)
                        return ['background-color: #002611; color: white'] * len(row)

                    st.dataframe(
                        df_display[["المحطة", "التيار (A)", "الحالة", "الوقت"]].head(15).style.apply(style_rows, axis=1),
                        use_container_width=True, hide_index=True
                    )
                    
                    # الرسم البياني (محمي بتجربة القيمة)
                    st.subheader("📊 تحليل الأحمال")
                    chart_df = df.pivot_table(index='الوقت', columns='المحطة', values='التيار (A)').ffill()
                    st.line_chart(chart_df, height=200)
                except Exception as e:
                    st.warning(f"جاري مزامنة البيانات... ({e})")
            else:
                st.info("بانتظار استقبال البيانات من غرفة التحكم...")
        
        time.sleep(1)
            
