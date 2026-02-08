import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# --- 1. إعدادات المنظومة ---
st.set_page_config(page_title="نظام طاقة الأنبار - المزامنة الكاملة", layout="wide")

DB_FILE = "anbar_global_sync_v2.json"

STATIONS_SPECS = {
    "مستشفى الرمادي التعليمي": 1000,
    "معمل زجاج الرمادي": 1200,
    "محطة مياه الورار": 900,
    "جامعة الأنبار": 700,
    "حي التأميم (سكني)": 500
}

# --- 2. إدارة البيانات العالمية ---
def load_data():
    if not os.path.exists(DB_FILE):
        return {"entries": [], "load_val": 0.0, "collapsed": False, "protocol_on": False}
    try:
        with open(DB_FILE, "r", encoding='utf-8') as f:
            data = json.load(f)
            return data
    except:
        return {"entries": [], "load_val": 0.0, "collapsed": False, "protocol_on": False}

def save_data(data):
    # ضمان بقاء القيم في النطاق الصحيح لمنع أخطاء الـ Progress Bar
    data["load_val"] = float(max(0.0, min(data["load_val"], 100.0)))
    with open(DB_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def apply_system_logic(new_readings, manual_click=False):
    data = load_data()
    if data["collapsed"]: return data
    
    is_protected = data.get("protocol_on", False)
    
    # إضافة البيانات الجديدة
    if new_readings:
        data["entries"].extend(new_readings)
        data["entries"] = data["entries"][-40:]
        
        # --- حساب الضغط ---
        if is_protected:
            # إذا البروتوكول فعال: ينجذب للـ 25%
            target = 25.0
            if data["load_val"] > target: data["load_val"] -= 5.0
            else: data["load_val"] += 1.0
        else:
            # بدون بروتوكول: الضغط يرتفع
            if manual_click:
                # الإرسال اليدوي يرفع الضغط بقوة (5% لكل ضغطة)
                data["load_val"] += 5.0
            else:
                # الإرسال التلقائي يرفع الضغط حسب عدد البيانات
                data["load_val"] += len(new_readings) * 2.0
    else:
        # حالة عدم وجود بيانات: تبريد تلقائي أو موازنة بروتوكول
        if is_protected:
            data["load_val"] = random.uniform(23.0, 27.0)
        else:
            data["load_val"] = max(0.0, data["load_val"] - 2.0)

    if data["load_val"] >= 100.0:
        data["collapsed"] = True
        
    save_data(data)
    return data

# --- 3. الواجهة الرئيسية ---
st.sidebar.title("⚡ مركز سيطرة الرمادي")
page = st.sidebar.radio("القائمة:", ["🕹️ غرفة التحكم", "🖥️ شاشة المراقبة"])

if st.sidebar.button("♻️ تصفير النظام"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.rerun()

# ==========================================
# صفحة التحكم (المرسل)
# ==========================================
if page == "🕹️ غرفة التحكم":
    st.title("🕹️ وحدة التحكم والإرسال")
    
    state = load_data()
    
    # زر البروتوكول (عالمي: يغير الحالة عند الجميع)
    proto = st.toggle("🛡️ تفعيل بروتوكول الحماية (عالمي)", value=state["protocol_on"])
    if proto != state["protocol_on"]:
        state["protocol_on"] = proto
        save_data(state)
        st.rerun()
    
    if state["collapsed"]:
        st.error("🚨 النظام منهار بسبب الضغط العالي!")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🔧 إرسال يدوي")
            for name, m_val in STATIONS_SPECS.items():
                val = st.slider(f"{name}", 0, 1500, value=int(m_val*0.6), key=f"s_{name}")
                if st.button(f"بث {name}", key=f"b_{name}"):
                    pct = (val / m_val) * 100
                    stt = "🔴 خطر" if pct >= 95 else "🟡 تنبيه" if pct >= 85 else "🟢 مستقر"
                    # استدعاء المنطق مع وسم (manual_click=True) لزيادة الضغط
                    apply_system_logic([{
                        "المحطة": name, "التيار (A)": val, "الحالة": stt, 
                        "level": 3 if pct >= 95 else 2 if pct >= 85 else 1,
                        "timestamp": time.time(), "الوقت": datetime.now().strftime("%H:%M:%S")
                    }], manual_click=True)
                    st.rerun() # لإظهار التغيير في العداد فوراً

        with col2:
            st.subheader("🚀 بث تلقائي")
            run_auto = st.checkbox("تشغيل الإرسال المستمر")
            auto_place = st.empty()
            while run_auto:
                curr = load_data()
                if curr["collapsed"]: st.rerun(); break
                
                selected = random.sample(list(STATIONS_SPECS.keys()), 4)
                batch = []
                b_time, b_clock = time.time(), datetime.now().strftime("%H:%M:%S")
                for n in selected:
                    s_max = STATIONS_SPECS[n]
                    v = random.randint(int(s_max*0.4), int(s_max*1.2))
                    pct = (v / s_max) * 100
                    batch.append({"المحطة": n, "التيار (A)": v, "الحالة": "🔴 خطر" if pct >= 95 else "🟡 تنبيه" if pct >= 85 else "🟢 مستقر", "level": 3 if pct >= 95 else 2 if pct >= 85 else 1, "timestamp": b_time, "الوقت": b_clock})
                
                apply_system_logic(batch)
                auto_place.info(f"📡 الضغط: {load_data()['load_val']:.1f}% | البروتوكول: {'نشط' if curr['protocol_on'] else 'معطل'}")
                time.sleep(1)

# ==========================================
# صفحة المراقبة (المستقبل)
# ==========================================
else:
    st.title("🖥️ شاشة المراقبة المركزية")
    mon_placeholder = st.empty()
    
    # تنسيق الجدول (خلفية بيضاء وخط أسود)
    st.markdown("""
        <style>
        .stDataFrame { background-color: white !important; }
        div[data-testid="stDataFrame"] td { color: black !important; font-weight: bold; }
        .collapse-msg { background-color: white; color: red; padding: 20px; border: 2px solid red; border-radius: 10px; text-align: center; font-weight: bold; width: 350px; margin: auto; }
        </style>
    """, unsafe_allow_html=True)

    while True:
        state = apply_system_logic([]) # نبضة النظام للتبريد أو الموازنة
        with mon_placeholder.container():
            if state["collapsed"]:
                st.markdown('<div class="collapse-msg">🚨 النظام انهار بسبب ضغط على الشبكة</div>', unsafe_allow_html=True)
                break
            
            v = float(state["load_val"])
            p_color = "blue" if state["protocol_on"] else ("red" if v > 80 else "orange" if v > 40 else "green")
            st.markdown(f"### ضغط السيرفر: :{p_color}[{v:.1f}%]")
            st.progress(max(0.0, min(v / 100.0, 1.0)))
            
            if state["entries"]:
                df = pd.DataFrame(state["entries"])
                df_display = df.sort_values(by=['timestamp', 'level'], ascending=[False, False])

                def style_table(row):
                    lvl = row.get('level', 1)
                    if lvl == 3: return ['background-color: white; color: #ff0000'] * len(row)
                    if lvl == 2: return ['background-color: white; color: #ffcc00'] * len(row)
                    return ['background-color: white; color: #00cc00'] * len(row)

                st.dataframe(df_display[["المحطة", "التيار (A)", "الحالة", "الوقت"]].head(20).style.apply(style_table, axis=1), use_container_width=True, hide_index=True)
                chart_df = df.pivot_table(index='الوقت', columns='المحطة', values='التيار (A)').ffill()
                st.line_chart(chart_df, height=200)
        time.sleep(1)
                    
