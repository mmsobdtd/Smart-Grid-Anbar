import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# --- 1. إعدادات الصفحة الأساسية ---
st.set_page_config(page_title="نظام طاقة الأنبار - الإصدار المستقر", layout="wide")

DB_FILE = "anbar_ultra_stable_v1.json"

STATIONS = {
    "مستشفى الرمادي التعليمي": {"max": 1000},
    "معمل زجاج الرمادي": {"max": 1200},
    "محطة مياه الورار": {"max": 900},
    "جامعة الأنبار": {"max": 700},
    "حي التأميم (سكني)": {"max": 500}
}

# --- 2. إدارة قواعد البيانات (JSON) ---
def load_data():
    if not os.path.exists(DB_FILE):
        return {"entries": [], "load_val": 0.0, "collapsed": False}
    try:
        with open(DB_FILE, "r", encoding='utf-8') as f:
            content = f.read()
            if not content: return {"entries": [], "load_val": 0.0, "collapsed": False}
            return json.loads(content)
    except:
        return {"entries": [], "load_val": 0.0, "collapsed": False}

def save_data(data):
    # مشبك أمان لقيمة الضغط (0-100)
    data["load_val"] = float(max(0.0, min(data["load_val"], 100.0)))
    try:
        with open(DB_FILE, "w", encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"خطأ في الحفظ: {e}")

def apply_system_logic(new_readings, protocol_on):
    data = load_data()
    if data["collapsed"]: return data
    
    # إضافة القراءات الجديدة
    if new_readings:
        data["entries"].extend(new_readings)
        # الاحتفاظ بآخر 60 قراءة فقط لضمان سرعة المعالجة
        data["entries"] = data["entries"][-60:]
    
    # منطق الضغط والبروتوكول
    if protocol_on:
        # البروتوكول: يسحب الضغط لمنطقة الـ 25%
        target = 25.0
        if data["load_val"] > (target + 2):
            data["load_val"] -= 10.0 # تفريغ سريع
        elif data["load_val"] < (target - 2):
            data["load_val"] += 2.0 # رفع بسيط للاستقرار
        else:
            data["load_val"] = random.uniform(23.0, 27.0) # تذبذب طبيعي
    else:
        # بدون بروتوكول
        if new_readings:
            # الضغط يرتفع بناءً على كمية البيانات (2.5 لكل حزمة)
            data["load_val"] += len(new_readings) * 2.5
        else:
            # التبريد التلقائي عند توقف الإرسال
            data["load_val"] = max(0.0, data["load_val"] - 4.0)
    
    # فحص الانهيار الحتمي
    if data["load_val"] >= 100.0:
        data["load_val"] = 100.0
        data["collapsed"] = True
    
    save_data(data)
    return data

# --- 3. الواجهة الجانبية ---
st.sidebar.title("⚡ مركز سيطرة الرمادي")
st.sidebar.markdown("---")
page = st.sidebar.radio("القائمة الرئيسية:", ["🕹️ غرفة التحكم", "🖥️ شاشة المراقبة"])
protocol_active = st.sidebar.toggle("🛡️ تفعيل بروتوكول الحماية", value=False)

if st.sidebar.button("♻️ إعادة ضبط النظام"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.rerun()

# ==========================================
# صفحة التحكم (إرسال البيانات)
# ==========================================
if page == "🕹️ غرفة التحكم":
    st.title("🕹️ وحدة الإرسال الميداني")
    state = load_data()
    
    if state["collapsed"]:
        st.error("🚨 المنظومة منهارة تماماً! يرجى عمل Reset من الجانب.")
    else:
        # تحديث دوري (للتبريد أو البروتوكول)
        apply_system_logic([], protocol_active)
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🔧 إرسال يدوي منفرد")
            for name, specs in STATIONS.items():
                val = st.slider(f"{name}", 0, 1500, value=int(specs['max']*0.6), key=f"s_{name}")
                if st.button(f"بث قراءة {name}", key=f"b_{name}"):
                    pct = (val / specs['max']) * 100
                    stt = "🔴 خطر" if pct >= 95 else "🟡 تنبيه" if pct >= 85 else "🟢 مستقر"
                    lvl = 3 if pct >= 95 else 2 if pct >= 85 else 1
                    apply_system_logic([{
                        "المحطة": name, "التيار (A)": val, "الحالة": stt, 
                        "level": lvl, "timestamp": time.time(),
                        "الوقت": datetime.now().strftime("%H:%M:%S")
                    }], protocol_active)
                    st.toast(f"تم إرسال {name}")

        with col2:
            st.subheader("🚀 بث تلقائي (4 محطات)")
            run_auto = st.checkbox("تشغيل التدفق المستمر")
            auto_place = st.empty()
            while run_auto:
                curr_state = load_data()
                if curr_state["collapsed"]: st.rerun(); break
                
                # اختيار 4 محطات عشوائية
                selected = random.sample(list(STATIONS.keys()), 4)
                batch = []
                for n in selected:
                    s_max = STATIONS[n]['max']
                    v = random.randint(int(s_max*0.5), int(s_max*1.1))
                    pct = (v / s_max) * 100
                    stt = "🔴 خطر" if pct >= 95 else "🟡 تنبيه" if pct >= 85 else "🟢 مستقر"
                    lvl = 3 if pct >= 95 else 2 if pct >= 85 else 1
                    batch.append({
                        "المحطة": n, "التيار (A)": v, "الحالة": stt, 
                        "level": lvl, "timestamp": time.time(),
                        "الوقت": datetime.now().strftime("%H:%M:%S")
                    })
                
                apply_system_logic(batch, protocol_active)
                auto_place.info(f"📡 يتم إرسال بيانات عشوائية... الضغط: {curr_state['load_val']:.1f}%")
                time.sleep(1)

# ==========================================
# صفحة المراقبة (عرض البيانات المفرزة)
# ==========================================
else:
    st.title("🖥️ شاشة المراقبة والتحليل الذكي")
    mon_place = st.empty()
    
    while True:
        # نبضة النظام للتبريد أو البروتوكول
        state = apply_system_logic([], protocol_active)
        
        with mon_place.container():
            if state["collapsed"]:
                st.markdown("""
                <div style='background-color:black; padding:50px; border: 10px solid red; text-align:center;'>
                    <h1 style='color:red;'>🚨 SYSTEM FAILURE 🚨</h1>
                    <h2 style='color:white;'>انهيار سيرفرات الطاقة</h2>
                </div>
                """, unsafe_allow_html=True)
                break
            
            # 1. عداد الضغط
            v = state["load_val"]
            p_color = "red" if v > 80 else "orange" if v > 40 else "green"
            st.markdown(f"### ضغط المنظومة الحالي: :{p_color}[{v:.1f}%]")
            # حماية st.progress من القيم غير الصحيحة
            st.progress(max(0.0, min(v / 100.0, 1.0)))
            
            # 2. عرض البيانات
            if state["entries"]:
                df = pd.DataFrame(state["entries"])
                
                # --- منطق الفرز الذكي المطلوب ---
                if protocol_active:
                    # فرز حسب: المستوى (3 أولاً)، ثم الزمن (الأحدث أولاً)
                    df_display = df.sort_values(by=['level', 'timestamp'], ascending=[False, False])
                    st.success("🛡️ وضع الحماية النشط: يتم فرز المخاطر في أعلى السجل.")
                else:
                    # فرز حسب الزمن فقط
                    df_display = df.sort_values(by='timestamp', ascending=False)
                    st.warning("⚠️ وضع الحماية معطل: الفرز يتم حسب زمن الوصول.")

                # 3. الجدول الملون
                def color_rows(row):
                    if row['level'] == 3: return ['background-color: #4d0000; color: #ffcccc'] * len(row)
                    if row['level'] == 2: return ['background-color: #4d3d00; color: #ffffcc'] * len(row)
                    return ['background-color: #002611; color: #ccffdd'] * len(row)

                st.dataframe(
                    df_display[["المحطة", "التيار (A)", "الحالة", "الوقت"]].head(15).style.apply(color_rows, axis=1),
                    use_container_width=True, hide_index=True
                )
                
                # 4. المخطط البياني
                st.subheader("📊 تحليل الأحمال اللحظي")
                chart_data = df.pivot_table(index='الوقت', columns='المحطة', values='التيار (A)').ffill()
                st.line_chart(chart_data, height=200)
            else:
                st.info("بانتظار استقبال البيانات من غرفة التحكم...")
                
        time.sleep(1)
        
