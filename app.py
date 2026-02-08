import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="نظام طاقة الأنبار - المراقبة الذكية", layout="wide")

DB_FILE = "anbar_white_table_v1.json"

STATIONS = {
    "مستشفى الرمادي التعليمي": {"max": 1000},
    "معمل زجاج الرمادي": {"max": 1200},
    "محطة مياه الورار": {"max": 900},
    "جامعة الأنبار": {"max": 700},
    "حي التأميم (سكني)": {"max": 500}
}

# --- 2. إدارة البيانات ---
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
    if data["collapsed"]: return data
    
    if new_readings:
        data["entries"].extend(new_readings)
        data["entries"] = data["entries"][-60:]
    
    if protocol_on:
        # استقرار عند 25% كما طلبت سابقاً
        target = 25.0
        if data["load_val"] > (target + 2):
            data["load_val"] -= 10.0
        elif data["load_val"] < (target - 2):
            data["load_val"] += 2.0
        else:
            data["load_val"] = random.uniform(23.0, 27.0)
    else:
        if new_readings:
            data["load_val"] += len(new_readings) * 2.0
        else:
            data["load_val"] = max(0.0, data["load_val"] - 4.0) # تبريد تلقائي
            
    if data["load_val"] >= 100.0:
        data["load_val"] = 100.0
        data["collapsed"] = True
    
    save_data(data)
    return data

# --- 3. واجهة المستخدم ---
st.sidebar.title("⚡ مركز سيطرة الرمادي")
page = st.sidebar.radio("انتقل إلى:", ["🕹️ غرفة التحكم", "🖥️ شاشة المراقبة"])
protocol_active = st.sidebar.toggle("🛡️ تفعيل بروتوكول الحماية", value=False)

if st.sidebar.button("♻️ تصفير النظام"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.rerun()

# ==========================================
# صفحة التحكم
# ==========================================
if page == "🕹️ غرفة التحكم":
    st.title("🕹️ وحدة إرسال البيانات")
    state = load_data()
    if state["collapsed"]:
        st.error("🚨 النظام منهار! يرجى عمل Reset.")
    else:
        apply_system_logic([], protocol_active)
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
                    st.toast(f"تم إرسال {name}")

        with col2:
            st.subheader("🚀 بث تلقائي (4 قراءات معاً)")
            run_auto = st.checkbox("تشغيل البث المستمر")
            auto_place = st.empty()
            while run_auto:
                if load_data()["collapsed"]: st.rerun(); break
                
                # إرسال 4 محطات بشكل واحد (Batch)
                selected = random.sample(list(STATIONS.keys()), 4)
                batch = []
                for n in selected:
                    s_max = STATIONS[n]['max']
                    v = random.randint(int(s_max*0.5), int(s_max*1.2))
                    pct = (v / s_max) * 100
                    stt = "🔴 خطر" if pct >= 95 else "🟡 تنبيه" if pct >= 85 else "🟢 مستقر"
                    batch.append({
                        "المحطة": n, "التيار (A)": v, "الحالة": stt, 
                        "level": 3 if pct >= 95 else 2 if pct >= 85 else 1,
                        "timestamp": time.time(), "الوقت": datetime.now().strftime("%H:%M:%S")
                    })
                apply_system_logic(batch, protocol_active)
                auto_place.info(f"📡 يتم ضخ 4 محطات حالياً... الضغط: {load_data()['load_val']:.1f}%")
                time.sleep(1)

# ==========================================
# صفحة المراقبة
# ==========================================
else:
    st.title("🖥️ شاشة المراقبة المركزية")
    mon_placeholder = st.empty()
    
    # تنسيق CSS لجعل خلفية الجدول بيضاء
    st.markdown("""
        <style>
        .stDataFrame {
            background-color: white;
            border-radius: 10px;
            padding: 5px;
        }
        </style>
    """, unsafe_allow_html=True)

    while True:
        state = apply_system_logic([], protocol_active)
        with mon_placeholder.container():
            if state["collapsed"]:
                st.markdown("<div style='background-color:black; padding:50px; border: 15px solid red; text-align:center;'><h1 style='color:red;'>🚨 SYSTEM FAILURE 🚨</h1></div>", unsafe_allow_html=True)
                break
            
            v = float(state.get("load_val", 0.0))
            p_color = "red" if v > 80 else "orange" if v > 40 else "green"
            st.markdown(f"### ضغط المنظومة: :{p_color}[{v:.1f}%]")
            st.progress(max(0.0, min(v / 100.0, 1.0)))
            
            if state["entries"]:
                df = pd.DataFrame(state["entries"])
                
                # --- الفرز الذكي: الأخطر (level 3) ثم الأحدث زمنياً ---
                df_display = df.sort_values(by=['level', 'timestamp'], ascending=[False, False])

                # دالة التلوين (خلفيات ملونة فاتحة مع نصوص غامقة لتناسب الجدول الأبيض)
                def style_white_table(row):
                    lvl = row.get('level', 1)
                    if lvl == 3: # أحمر
                        return ['background-color: #ffcccc; color: #800000; font-weight: bold'] * len(row)
                    if lvl == 2: # أصفر/برتقالي
                        return ['background-color: #fff4cc; color: #856404'] * len(row)
                    return ['background-color: #d4edda; color: #155724'] * len(row) # أخضر

                st.subheader("📋 سجل الحالات (الأولوية للأخطر 🔴)")
                st.dataframe(
                    df_display[["المحطة", "التيار (A)", "الحالة", "الوقت"]].head(15).style.apply(style_white_table, axis=1),
                    use_container_width=True, hide_index=True
                )
                
                st.subheader("📊 مخطط الأحمال")
                chart_df = df.pivot_table(index='الوقت', columns='المحطة', values='التيار (A)').ffill()
                st.line_chart(chart_df, height=200)
            else:
                st.info("بانتظار البيانات...")
        time.sleep(1)
                
