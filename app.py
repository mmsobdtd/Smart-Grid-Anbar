import streamlit as st
import pandas as pd
import json
import os
import time

# إعدادات الصفحة
st.set_page_config(page_title="Anbar Smart Grid - Live", layout="wide")

DB_FILE = "grid_live_data.json"

# دالة إدارة البيانات
def load_data():
    if not os.path.exists(DB_FILE):
        data = {f"Station {i}": {"current": 200, "last_update": time.time()} for i in range(1, 5)}
        save_data(data)
        return data
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {f"Station {i}": {"current": 200, "last_update": time.time()} for i in range(1, 5)}

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

# --- واجهة التحكم الجانبية ---
st.sidebar.header("⚙️ إعدادات النظام")
mode = st.sidebar.selectbox("وضعية الشبكة:", ["مع البروتوكول (نظام ذكي)", "بدون بروتوكول (انهيار الشبكة)"])
role = st.sidebar.radio("دخول بصفتك:", ["طالب (المحطة)", "المراقب (غرفة التحكم)"])

# --- واجهة الطالب (إرسال سريع) ---
if role == "طالب (المحطة)":
    st.header("📲 إرسال البيانات اللحظي")
    station_id = st.selectbox("اختر محطتك:", [f"Station {i}" for i in range(1, 5)])
    
    # التحديث هنا يتم بمجرد تحريك السلايدر
    current_val = load_data()[station_id]["current"]
    val = st.slider(f"تحكم في تيار {station_id}:", 0, 600, current_val)
    
    if val != current_val:
        data = load_data()
        data[station_id] = {"current": val, "last_update": time.time()}
        save_data(data)
        st.success(f"جاري البث... {val} A")

# --- واجهة المراقب (تحديث تلقائي كل ثانية) ---
else:
    st.header("🖥️ شاشة المراقبة الحية (تحديث كل 1 ثانية)")
    
    # هذه المنطقة ستحدث نفسها تلقائياً كل ثانية
    @st.fragment(run_every="1s")
    def monitor_ui():
        data = load_data()
        raw_list = []
        for s, info in data.items():
            raw_list.append({"Station": s, "Current": info["current"], "Time": info["last_update"]})
        
        df = pd.DataFrame(raw_list)

        # 1. وضعية بدون بروتوكول (Chaos Mode)
        if mode == "بدون بروتوكول (انهيار الشبكة)":
            st.error("🚨 وضع الانهيار: البيانات تتداخل ولا يوجد ترتيب أولويات!")
            # عرض البيانات بترتيب عشوائي تماماً لمحاكاة ضياع الحزم (Collisions)
            st.table(df.sample(frac=1).reset_index(drop=True))
            
            if df['Current'].max() > 300:
                st.markdown("<h2 style='color:red; text-align:center;'>⚠️ تداخل في الإشارات - تأخير في الاستجابة ⚠️</h2>", unsafe_allow_html=True)

        # 2. وضعية مع البروتوكول (Priority Protocol)
        else:
            st.success("✅ البروتوكول يعمل: تنظيم البيانات حسب خطورة الحمل")
            
            # منطق البروتوكول: فرز حسب الأخطر (Current)
            df['Priority'] = df['Current'].apply(lambda x: "🔴 HIGH" if x >= 300 else ("🟢 Low" if x <= 250 else "🟡 Mid"))
            df_sorted = df.sort_values(by="Current", ascending=False)
            
            # عرض المقاييس (Metrics)
            cols = st.columns(4)
            for i, (idx, row) in enumerate(df_sorted.iterrows()):
                cols[i].metric(row['Station'], f"{row['Current']} A", row['Priority'])

            st.bar_chart(df_sorted.set_index('Station')['Current'])
            st.dataframe(df_sorted, use_container_width=True)

    # تشغيل منطقة التحديث التلقائي
    monitor_ui()

