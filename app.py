import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# --- إعدادات الصفحة ---
st.set_page_config(page_title="نظام مراقبة طاقة الأنبار v3", layout="wide")

DB_FILE = "anbar_final_pro_v3.json"

# إعدادات المحطات مع حدود الخطر
STATIONS = {
    "مستشفى الرمادي التعليمي": {"max": 1000},
    "معمل زجاج الرمادي": {"max": 1200},
    "محطة مياه الورار": {"max": 900},
    "جامعة الأنبار": {"max": 700},
    "حي التأميم (سكني)": {"max": 500}
}

# --- إدارة البيانات ---
def load_data():
    if not os.path.exists(DB_FILE):
        return {"entries": [], "load_val": 0.0, "collapsed": False}
    try:
        with open(DB_FILE, "r", encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"entries": [], "load_val": 0.0, "collapsed": False}

def save_data(data):
    data["load_val"] = float(max(0.0, min(data["load_val"], 100.0)))
    with open(DB_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def apply_system_logic(new_readings, protocol_on):
    data = load_data()
    if data["collapsed"]: return
    
    if new_readings:
        data["entries"].extend(new_readings)
        data["entries"] = data["entries"][-50:] # حفظ آخر 50 قراءة
    
    if protocol_on:
        # منطق البروتوكول: الاستقرار حول 25%
        target = 25.0
        if data["load_val"] > (target + 2):
            data["load_val"] -= 8.0
        elif data["load_val"] < (target - 2):
            data["load_val"] += 2.0
        else:
            data["load_val"] = random.uniform(23.0, 27.0)
    else:
        # بدون بروتوكول
        if new_readings:
            data["load_val"] += len(new_readings) * 2.0
        else:
            data["load_val"] = max(0.0, data["load_val"] - 4.0) # تبريد تلقائي
    
    if data["load_val"] >= 100.0:
        data["load_val"] = 100.0
        data["collapsed"] = True
    
    save_data(data)

# --- الواجهة الجانبية ---
st.sidebar.title("⚡ مركز سيطرة الرمادي")
page = st.sidebar.radio("القائمة:", ["🕹️ غرفة التحكم", "🖥️ شاشة المراقبة"])
protocol_active = st.sidebar.toggle("🛡️ بروتوكول الحماية", value=False)

if st.sidebar.button("♻️ إعادة ضبط المنظومة"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.rerun()

# ==========================================
# صفحة التحكم
# ==========================================
if page == "🕹️ غرفة التحكم":
    st.title("🕹️ وحدة الإرسال والتحكم")
    state = load_data()
    if state["collapsed"]:
        st.error("🚨 النظام منهار! يرجى عمل Reset.")
    else:
        apply_system_logic([], protocol_active)
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🔧 إدخال يدوي")
            for name, specs in STATIONS.items():
                val = st.slider(f"تيار {name} (A)", 0, 1500, value=int(specs['max']*0.6), key=f"s_{name}")
                if st.button(f"بث قراءة {name}", key=f"b_{name}"):
                    # حساب الحالة والنسبة
                    load_pct = (val / specs['max']) * 100
                    status = "🔴 خطر" if load_pct >= 95 else "🟡 تنبيه" if load_pct >= 85 else "🟢 مستقر"
                    apply_system_logic([{
                        "المحطة": name, "التيار (A)": val, "الحد الأقصى": specs['max'],
                        "نسبة التحميل": f"{load_pct:.1f}%", "الحالة": status,
                        "الوقت": datetime.now().strftime("%H:%M:%S")
                    }], protocol_active)
                    st.toast(f"تم إرسال {name}")
        with col2:
            st.subheader("🚀 بث تلقائي")
            run_auto = st.checkbox("تشغيل التدفق المستمر")
            auto_placeholder = st.empty()
            while run_auto:
                curr = load_data()
                if curr["collapsed"]: st.rerun(); break
                batch = []
                for n, s in STATIONS.items():
                    v = random.randint(int(s['max']*0.4), int(s['max']*1.1))
                    pct = (v / s['max']) * 100
                    stt = "🔴 خطر" if pct >= 95 else "🟡 تنبيه" if pct >= 85 else "🟢 مستقر"
                    batch.append({
                        "المحطة": n, "التيار (A)": v, "الحد الأقصى": s['max'],
                        "نسبة التحميل": f"{pct:.1f}%", "الحالة": stt,
                        "الوقت": datetime.now().strftime("%H:%M:%S")
                    })
                apply_system_logic(batch, protocol_active)
                auto_placeholder.info(f"📡 الضخ مستمر... الضغط: {curr['load_val']:.1f}%")
                time.sleep(1)

# ==========================================
# صفحة المراقبة
# ==========================================
else:
    st.title("🖥️ شاشة المراقبة والتحليل اللحظي")
    mon_placeholder = st.empty()
    while True:
        apply_system_logic([], protocol_active)
        state = load_data()
        with mon_placeholder.container():
            if state["collapsed"]:
                st.markdown("<div style='background-color:#1a0000; padding:50px; border: 5px solid red; text-align:center; border-radius:15px;'><h1 style='color:red;'>🚨 SYSTEM CRASH 🚨</h1><h2 style='color:white;'>توقف كامل للمنظومة</h2></div>", unsafe_allow_html=True)
                break
            
            # عرض عداد الضغط
            val = state["load_val"]
            p_color = "red" if val > 80 else "orange" if val > 40 else "green"
            st.markdown(f"### ضغط السيرفر: :{p_color}[{val:.1f}%]")
            st.progress(max(0.0, min(val / 100.0, 1.0)))
            
            if state["entries"]:
                df = pd.DataFrame(state["entries"])
                
                # ترتيب الجدول ليظهر الأحدث في الأعلى
                df_view = df.iloc[::-1].head(15)

                # دالة تلوين متطورة ومريحة للعين
                def style_table(row):
                    if "🔴" in str(row['الحالة']):
                        return ['background-color: #4d0000; color: #ffcccc; font-weight: bold'] * len(row)
                    if "🟡" in str(row['الحالة']):
                        return ['background-color: #4d3d00; color: #ffffcc'] * len(row)
                    return ['background-color: #002611; color: #ccffdd'] * len(row)

                st.subheader("📋 حالة محطات الأنبار اللحظية")
                
                # استخدام dataframe مع إعدادات الأعمدة
                st.dataframe(
                    df_view.style.apply(style_table, axis=1),
                    use_container_width=True,
                    column_config={
                        "التيار (A)": st.column_config.NumberColumn(format="%d A"),
                        "الحد الأقصى": st.column_config.NumberColumn(format="%d A"),
                        "الوقت": st.column_config.TimeColumn(),
                        "نسبة التحميل": st.column_config.TextColumn(help="مدى اقتراب المحطة من الانفجار")
                    },
                    hide_index=True
                )
                
                st.subheader("📊 مخطط الأحمال")
                chart_data = df.pivot_table(index='الوقت', columns='المحطة', values='التيار (A)').ffill()
                st.line_chart(chart_data, height=250)
        time.sleep(1)
                    
