import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# إعداد الصفحة
st.set_page_config(page_title="نظام توزيع أحمال الرمادي", layout="wide")

DB_FILE = "ramadi_grid_system.json"

# --- 1. إعدادات محطات الرمادي الواقعية ---
# max_load: الحد الأقصى للأمبيرية قبل الخطر
# priority: الأولوية (1 هو الأعلى أهمية)
STATIONS = {
    "مستشفى الرمادي التعليمي": {"max_load": 1200, "priority": 1},   # أهم منشأة
    "معمل زجاج الرمادي": {"max_load": 1500, "priority": 2},         # منشأة صناعية حساسة
    "محطة ماء الورار": {"max_load": 1000, "priority": 3},           # بنية تحتية
    "جامعة الأنبار": {"max_load": 800, "priority": 4},              # مؤسسة تعليمية
    "حي التأميم (سكني)": {"max_load": 600, "priority": 5}           # حمل سكني
}

def load_data():
    if not os.path.exists(DB_FILE): return []
    try:
        with open(DB_FILE, "r", encoding='utf-8') as f:
            content = f.read()
            return json.loads(content) if content else []
    except: return []

def save_data(entry):
    history = load_data()
    # التحقق من حالة الانهيار الأخيرة
    if history and history[-1].get("status") == "SYSTEM_COLLAPSE":
        # إذا النظام منهار، لا تقبل بيانات جديدة إلا بعد التصفير أو مرور وقت
        pass 
    history.append(entry)
    with open(DB_FILE, "w", encoding='utf-8') as f:
        json.dump(history[-80:], f, ensure_ascii=False)

def determine_status(name, current):
    limit = STATIONS[name]["max_load"]
    # منطق واقعي: الخطر نادر الحدوث
    if current < (limit * 0.85):
        return "🟢 مستقر", 1
    elif (limit * 0.85) <= current < (limit * 0.95):
        return "🟡 تحذير", 2
    else:
        return "🔴 حمل حرج", 3

# --- القائمة الجانبية ---
st.sidebar.title("⚡ تحكم كهرباء الرمادي")
page = st.sidebar.radio("انتقل إلى:", ["🕹️ غرفة التحكم", "🖥️ شاشة المراقبة"])
st.sidebar.markdown("---")
protocol_active = st.sidebar.toggle("🛡️ تفعيل بروتوكول الحماية", value=True)

if st.sidebar.button("🗑️ إعادة تشغيل النظام"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.rerun()

# --- الصفحة 1: غرفة التحكم (إرسال) ---
if page == "🕹️ غرفة التحكم":
    st.title("🕹️ وحدة التحكم بالأحمال")
    
    # تهيئة متغير لتتبع سرعة النقر
    if 'last_click_time' not in st.session_state:
        st.session_state.last_click_time = time.time()

    mode = st.selectbox("وضعية التشغيل:", ["يدوي (شريط التحكم)", "محاكاة الضغط العالي"])

    # 1. الوضع اليدوي (الشريط)
    if mode == "يدوي (شريط التحكم)":
        st.info("حرك الشريط لتغيير الحمل. التحريك السريع بدون بروتوكول سيسبب انهياراً.")
        
        for name in STATIONS.keys():
            limit = STATIONS[name]["max_load"]
            # القيمة الافتراضية تكون آمنة (60% من الحمل)
            default_val = int(limit * 0.6)
            
            # الشريط يرسل البيانات تلقائياً عند التحريك
            val = st.slider(f"{name} (Max: {limit}A)", 0, int(limit*1.2), value=default_val, key=name)
            
            # كشف التغيير (عندما يحرك المستخدم الشريط)
            if st.session_state.get(f"prev_{name}") != val:
                current_time = time.time()
                time_diff = current_time - st.session_state.last_click_time
                st.session_state.last_click_time = current_time
                
                # === منطق الانهيار (Crash Logic) ===
                # إذا كان الفرق الزمني قليل (حركة سريعة جداً) والبروتوكول مطفأ
                if time_diff < 0.3 and not protocol_active:
                    save_data([{
                        "المنشأة": "SYSTEM", "التيار (A)": 0, "الحالة": "SYSTEM_COLLAPSE",
                        "الوقت": datetime.now().strftime("%H:%M:%S"), "timestamp": time.time(), "level": 99
                    }])
                    st.error("🚨 حدث ضغط عالي! الشبكة تنهار بسبب سرعة البيانات!")
                else:
                    # الوضع الطبيعي
                    status_text, level = determine_status(name, val)
                    entry = {
                        "المنشأة": name, "التيار (A)": val, "الحالة": status_text,
                        "الوقت": datetime.now().strftime("%H:%M:%S"),
                        "timestamp": time.time(), "level": level, "p": STATIONS[name]["priority"]
                    }
                    save_data([entry])
                
                st.session_state[f"prev_{name}"] = val

    # 2. وضع محاكاة الضغط (Stress Test)
    else:
        if st.button("تشغيل هجوم بيانات (Stress Test)"):
            st.warning("جاري إرسال 50 نبضة في الثانية...")
            # إذا البروتوكول طافي -> انهيار
            if not protocol_active:
                time.sleep(1)
                save_data([{
                    "المنشأة": "SYSTEM", "التيار (A)": 0, "الحالة": "SYSTEM_COLLAPSE",
                    "الوقت": datetime.now().strftime("%H:%M:%S"), "timestamp": time.time(), "level": 99
                }])
            else:
                # البروتوكول فعال -> يعالج البيانات
                batch = []
                for _ in range(10): # محاكاة 10 قراءات سريعة
                    n = random.choice(list(STATIONS.keys()))
                    # نادراً ما نعطي قيمة خطرة
                    if random.random() < 0.1: # 10% احتمال خطر
                        v = int(STATIONS[n]["max_load"] * 1.1)
                    else:
                        v = int(STATIONS[n]["max_load"] * 0.7)
                    s, l = determine_status(n, v)
                    batch.append({
                        "المنشأة": n, "التيار (A)": v, "الحالة": s,
                        "الوقت": datetime.now().strftime("%H:%M:%S"),
                        "timestamp": time.time(), "level": l, "p": STATIONS[n]["priority"]
                    })
                save_data(batch)
                st.success("✅ البروتوكول نجح في استيعاب الهجوم وحماية الشبكة.")

# --- الصفحة 2: شاشة المراقبة ---
else:
    st.title("🖥️ مركز مراقبة شبكة الرمادي")

    @st.fragment(run_every="1s")
    def monitor_grid():
        data = load_data()
        
        # 1. فحص الانهيار أولاً
        if data and data[-1].get("status") == "SYSTEM_COLLAPSE" or \
           any(d.get("level") == 99 for d in data[-20:]): # فحص آخر 20 سجل
            
            st.markdown("""
                <div style="background-color:black; color:red; padding:50px; text-align:center; border: 5px solid red;">
                <h1>⚠️ NETWORK COLLAPSE ⚠️</h1>
                <h2>انهيار الشبكة بالكامل</h2>
                <p>توقف النظام بسبب تدفق البيانات الزائد وعدم وجود بروتوكول تنظيم.</p>
                <p>Buffer Overflow Detected</p>
                </div>
                """, unsafe_allow_html=True)
            return # إيقاف عرض باقي الصفحة

        # 2. العرض الطبيعي
        if not data:
            st.info("النظام مستقر. بانتظار البيانات...")
            return

        df = pd.DataFrame(data)
        
        # تصفية بيانات النظام الداخلية
        df = df[df['level'] != 99]

        # الرسم البياني
        st.subheader("📊 استهلاك الأحمال (Live Load)")
        chart_df = df.pivot_table(index='الوقت', columns='المنشأة', values='التيار (A)').ffill()
        st.line_chart(chart_df, height=250)

        # الجدول
        st.subheader("📋 حالة المحطات (Real-time Status)")
        
        # --- خوارزمية البروتوكول ---
        if protocol_active:
            # الترتيب حسب: 1. مستوى الخطر (الأحمر فوق) 2. أولوية المنشأة (المستشفى فوق الجامعة) 3. الوقت
            df_display = df.sort_values(by=["level", "p", "timestamp"], ascending=[False, True, False])
        else:
            # بدون بروتوكول: فوضى (ترتيب زمني فقط)
            df_display = df.sort_values(by="timestamp", ascending=False)

        def highlight(row):
            if row['level'] == 3: return ['background-color: #8b0000; color: white; font-weight: bold'] * len(row)
            if row['level'] == 2: return ['background-color: #bdb76b; color: black'] * len(row)
            return [''] * len(row)

        st.dataframe(
            df_display.drop(columns=['timestamp', 'level', 'p'], errors='ignore').style.apply(highlight, axis=1),
            use_container_width=True,
            height=500
        )

    monitor_grid()
                    
