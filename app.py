import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# --- 1. إعدادات المنظومة الأساسية ---
st.set_page_config(page_title="نظام طاقة الأنبار - الإصدار المتكامل", layout="wide")

# ملف البيانات العالمي للمزامنة بين الأجهزة
DB_FILE = "anbar_global_final_v4.json"

STATIONS_SPECS = {
    "مستشفى الرمادي التعليمي": 1000,
    "معمل زجاج الرمادي": 1200,
    "محطة مياه الورار": 900,
    "جامعة الأنبار": 700,
    "حي التأميم (سكني)": 500
}

# --- 2. إدارة البيانات والمزامنة العالمية ---
def load_data():
    if not os.path.exists(DB_FILE):
        return {"entries": [], "load_val": 0.0, "collapsed": False, "protocol_on": False, "logs": []}
    try:
        with open(DB_FILE, "r", encoding='utf-8') as f:
            data = json.load(f)
            # التأكد من وجود كافة الحقول المطلوبة للمزامنة
            if "protocol_on" not in data: data["protocol_on"] = False
            if "logs" not in data: data["logs"] = []
            return data
    except:
        return {"entries": [], "load_val": 0.0, "collapsed": False, "protocol_on": False, "logs": []}

def save_data(data):
    # صمام أمان لقيمة الضغط (0-100) لمنع أخطاء الواجهة
    data["load_val"] = float(max(0.0, min(data["load_val"], 100.0)))
    with open(DB_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def add_log(message):
    data = load_data()
    timestamp = datetime.now().strftime("%H:%M:%S")
    data["logs"].insert(0, f"[{timestamp}] {message}")
    data["logs"] = data["logs"][:10] # حفظ آخر 10 أحداث فقط
    save_data(data)

def apply_system_logic(new_readings, is_manual=False):
    data = load_data()
    if data["collapsed"]: return data
    
    is_protected = data.get("protocol_on", False)
    
    if new_readings:
        data["entries"].extend(new_readings)
        data["entries"] = data["entries"][-50:] # سعة السجل
        
        if is_protected:
            # البروتوكول: موازنة ديناميكية حول 25%
            target = 25.0
            if data["load_val"] > (target + 2): data["load_val"] -= 7.0
            elif data["load_val"] < (target - 2): data["load_val"] += 2.0
            else: data["load_val"] = random.uniform(23.0, 27.0)
        else:
            # بدون بروتوكول: الضغط يرتفع بقوة في اليدوي
            if is_manual:
                data["load_val"] += 7.0 # تأثير الضغط اليدوي
            else:
                data["load_val"] += len(new_readings) * 1.5
    else:
        # تبريد أو موازنة تلقائية عند السكون
        if is_protected:
            data["load_val"] = random.uniform(24.0, 26.0)
        else:
            data["load_val"] = max(0.0, data["load_val"] - 3.0)

    # فحص حالة الانهيار الحتمي
    if data["load_val"] >= 100.0:
        data["collapsed"] = True
        add_log("🚨 انهيار النظام بسبب تجاوز حد الضغط!")
        
    save_data(data)
    return data

# --- 3. بناء واجهة المستخدم ---
st.sidebar.title("⚡ مركز سيطرة الرمادي")
page = st.sidebar.radio("القائمة الرئيسية:", ["🕹️ غرفة التحكم", "🖥️ شاشة المراقبة"])

if st.sidebar.button("♻️ تصفير النظام العام"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.rerun()

# ==========================================
# صفحة التحكم (Control Room)
# ==========================================
if page == "🕹️ غرفة التحكم":
    st.title("🕹️ وحدة الإرسال والتحكم العالمي")
    
    state = load_data()
    
    # إدارة البروتوكول (تأثير عالمي يظهر عند الجميع)
    proto_status = st.toggle("🛡️ تفعيل بروتوكول الحماية (عام لجميع الأجهزة)", value=state["protocol_on"])
    if proto_status != state["protocol_on"]:
        state["protocol_on"] = proto_status
        status_text = "تفعيل" if proto_status else "إيقاف"
        save_data(state)
        add_log(f"تم {status_text} بروتوكول الحماية عالمياً")
        st.rerun()

    if state["collapsed"]:
        st.error("🚨 النظام في حالة انهيار! يرجى عمل Reset من القائمة الجانبية.")
    else:
        apply_system_logic([]) 
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🔧 الإرسال اليدوي (أولوية قصوى)")
            for name, m_val in STATIONS_SPECS.items():
                val = st.slider(f"{name}", 0, 1500, value=int(m_val*0.6), key=f"s_{name}")
                if st.button(f"بث {name}", key=f"b_{name}"):
                    pct = (val / m_val) * 100
                    # خطر فقط عند 95% فأكثر كما طلبت
                    stt = "🔴 خطر" if pct >= 95 else "🟡 تنبيه" if pct >= 85 else "🟢 مستقر"
                    lvl = 3 if pct >= 95 else 2 if pct >= 85 else 1
                    apply_system_logic([{
                        "المحطة": name, "التيار (A)": val, "الحالة": stt, 
                        "level": lvl, "timestamp": time.time(), "الوقت": datetime.now().strftime("%H:%M:%S"),
                        "source": "manual" # وسم الفرز اليدوي
                    }], is_manual=True)
                    st.toast(f"تم إرسال {name} يدوياً")

        with col2:
            st.subheader("🚀 البث التلقائي المستمر")
            run_auto = st.checkbox("تشغيل الإرسال التلقائي")
            auto_info = st.empty()
            while run_auto:
                curr_state = load_data()
                if curr_state["collapsed"]: st.rerun(); break
                
                batch = []
                b_time, b_clock = time.time(), datetime.now().strftime("%H:%M:%S")
                # إرسال 4 محطات بشكل عشوائي
                for n in random.sample(list(STATIONS_SPECS.keys()), 4):
                    s_max = STATIONS_SPECS[n]
                    v = random.randint(int(s_max*0.4), int(s_max*1.1))
                    pct = (v / s_max) * 100
                    stt = "🔴 خطر" if pct >= 95 else "🟡 تنبيه" if pct >= 85 else "🟢 مستقر"
                    batch.append({"المحطة": n, "التيار (A)": v, "الحالة": stt, "level": 3 if pct >= 95 else 2 if pct >= 85 else 1, "timestamp": b_time, "الوقت": b_clock, "source": "auto"})
                
                apply_system_logic(batch)
                auto_info.info(f"📡 الضغط: {load_data()['load_val']:.1f}% | البروتوكول: {'نشط' if curr_state['protocol_on'] else 'مطفي'}")
                # التحديث كل 2 ثانية في وضع البروتوكول
                time.sleep(2 if curr_state['protocol_on'] else 1)

# ==========================================
# صفحة المراقبة (Monitoring Room)
# ==========================================
else:
    st.title("🖥️ شاشة المراقبة المركزية - الأنبار")
    
    # عرض سجل الأحداث في القائمة الجانبية للمراقب
    st.sidebar.subheader("📜 سجل الأحداث")
    for log in load_data()["logs"]:
        st.sidebar.caption(log)

    mon_placeholder = st.empty()
    
    # تنسيق الجدول: أبيض، خط أسود عريض، فرز يدوي في الأعلى
    st.markdown("""
        <style>
        .stDataFrame { background-color: white !important; border: 1px solid #ccc; }
        div[data-testid="stDataFrame"] td { color: black !important; font-weight: bold; font-size: 15px; }
        .collapse-small { background-color: white; color: red; padding: 15px; border: 2px solid red; border-radius: 8px; text-align: center; font-weight: bold; width: 300px; margin: 20px auto; }
        </style>
    """, unsafe_allow_html=True)

    while True:
        state = apply_system_logic([]) 
        is_p = state.get("protocol_on", False)
        
        with mon_placeholder.container():
            if state["collapsed"]:
                st.markdown('<div class="collapse-small">🚨 النظام انهار بسبب ضغط على الشبكة</div>', unsafe_allow_html=True)
                break
            
            v = float(state["load_val"])
            p_color = "blue" if is_p else ("red" if v > 85 else "green")
            st.markdown(f"### ضغط المنظومة: :{p_color}[{v:.1f}%] {'(🛡️ محمي عالمياً)' if is_p else ''}")
            st.progress(max(0.0, min(v / 100.0, 1.0)))
            
            if state["entries"]:
                df = pd.DataFrame(state["entries"])
                
                # --- منطق الفرز الرباعي الذكي ---
                # فرز اليدوي أولاً، ثم التوقيت الأحدث، ثم الأخطر
                df_display = df.sort_values(by=['source', 'timestamp', 'level'], ascending=[False, False, False])

                def style_custom_rows(row):
                    stt = str(row['الحالة'])
                    if "🔴" in stt: return ['background-color: #ff0000; color: black'] * len(row)
                    if "🟡" in stt: return ['background-color: #ffff00; color: black'] * len(row)
                    return ['background-color: #00ff00; color: black'] * len(row)

                st.subheader("📋 حالة الشبكة اللحظية")
                st.dataframe(
                    df_display[["المحطة", "التيار (A)", "الحالة", "الوقت"]].head(20).style.apply(style_custom_rows, axis=1), 
                    use_container_width=True, hide_index=True
                )
                
                st.subheader("📊 مخطط الأحمال")
                chart_df = df.pivot_table(index='الوقت', columns='المحطة', values='التيار (A)').ffill()
                st.line_chart(chart_df, height=180)
            else:
                st.info("بانتظار وصول البيانات الميدانية...")
        
        # سرعة التحديث مرتبطة بحالة البروتوكول
        time.sleep(2 if is_p else 1)
            
