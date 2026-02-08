import streamlit as st
import pandas as pd
import json
import os
import time
import random

# إعدادات الصفحة
st.set_page_config(page_title="Smart Grid Protocol Demo", layout="wide")

DB_FILE = "grid_state.json"

# دالة لإدارة البيانات المشتركة بين الطلاب والسيرفر
def load_data():
    if not os.path.exists(DB_FILE):
        data = {f"Station {i}": {"current": 200, "timestamp": time.time()} for i in range(1, 5)}
        save_data(data)
        return data
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

# تحميل البيانات الحالية
current_loads = load_data()

# --- القائمة الجانبية (التحكم في العرض) ---
st.sidebar.title("🎮 لوحة التحكم بالعرض")
mode = st.sidebar.radio("اختر وضع النظام:", ["بدون بروتوكول (Chaos)", "مع البروتوكول (Smart)"])
role = st.sidebar.selectbox("من أنت؟", ["طالب (المحطة)", "المراقب (غرفة التحكم)"])

# --- واجهة الطالب (تحديث لحظي) ---
if role == "طالب (المحطة)":
    st.header("📲 وحدة تحكم المحطة الفرعية")
    station_id = st.selectbox("اختر رقم محطتك:", list(current_loads.keys()))
    
    # تحديث البيانات فور تغيير المنزلق
    val = st.slider("اسحب لتغيير الأمبيرية (I):", 0, 600, current_loads[station_id]["current"])
    
    if val != current_loads[station_id]["current"]:
        current_loads[station_id]["current"] = val
        current_loads[station_id]["timestamp"] = time.time()
        save_data(current_loads)
        st.success(f"تم تحديث البيانات لحظياً: {val} A")

# --- واجهة المراقب (غرفة التحكم) ---
else:
    st.header("🖥️ غرفة التحكم المركزية - جامعة الأنبار")
    st.write(f"الوضع الحالي: **{mode}**")
    
    # زر للتحديث اليدوي (لأن الطلاب يرسلون بياناتهم باستمرار)
    if st.button("تحديث لوحة البيانات 🔄"):
        st.rerun()

    # تحويل البيانات لجدول
    raw_data = []
    for s, info in current_loads.items():
        raw_data.append({"Station": s, "Current": info["current"], "Time": info["timestamp"]})
    df = pd.DataFrame(raw_data)

    # --- سيناريو 1: بدون بروتوكول (انهيار الشبكة) ---
    if mode == "بدون بروتوكول (Chaos)":
        st.error("🚨 تحذير: النظام يعمل بدون قواعد (No Protocol)")
        st.warning("الملاحظة: البيانات تصل بشكل عشوائي، لا يوجد ترتيب للأولويات، النظام عرضة للانهيار.")
        
        # محاكاة "فوضى": عرض البيانات بترتيب زمني عشوائي أو غير مرتب
        st.subheader("📋 سجل الحزم الواردة (تداخل البيانات)")
        st.write("بيانات خام متداخلة (Collisions):")
        st.table(df.sample(frac=1)) # عرض البيانات بترتيب عشوائي تماماً لمحاكاة التداخل
        
        # محاكاة الانهيار بصرياً
        if df['Current'].max() > 400:
            st.markdown("<h1 style='color:red; text-align:center;'>SYSTEM OVERLOAD - NETWORK COLLAPSE</h1>", unsafe_allow_html=True)
            st.image("https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJmNjR4bm16Z3R6Z3R6Z3R6Z3R6Z3R6Z3R6Z3R6Z3R6Z3R6JmVwPXYxX2ludGVybmFsX2dpZl9ieV9pZCZjdD1n/3o7TKMGpxPucK8hLJC/giphy.gif", width=400)

    # --- سيناريو 2: مع البروتوكول (تنظيم وأولوية) ---
    else:
        st.success("✅ البروتوكول الذكي نشط (Priority Protocol Active)")
        
        # تطبيق منطق الأولويات: 300A (خطر) | 250A (طبيعي)
        def classify(c):
            if c >= 300: return "🔴 HIGH PRIORITY (Critical)"
            elif c <= 250: return "🟢 Normal"
            else: return "🟡 Warning"

        df['Status'] = df['Current'].apply(classify)
        
        # الفرز حسب الأولوية (الأخطر في الأعلى)
        df_sorted = df.sort_values(by="Current", ascending=False)
        
        # عرض الرسوم البيانية المنظمة
        st.subheader("📊 مراقبة استقرار الأحمال")
        st.bar_chart(df_sorted.set_index('Station')['Current'])

        

        # عرض الجدول المنظم
        st.subheader("📋 جدول البيانات المنظم حسب الأولوية")
        st.dataframe(df_sorted.style.highlight_max(axis=0, color='red'), use_container_width=True)

        # التنبيهات
        critical = df_sorted[df_sorted['Current'] >= 300]
        if not critical.empty:
            for _, row in critical.iterrows():
                st.toast(f"🚨 تنبيه عاجل: {row['Station']} تجاوزت الحد المسموح!", icon="🔥")
                
