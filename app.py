import streamlit as st
import pandas as pd
import json
import os

# إعدادات الصفحة
st.set_page_config(page_title="Anbar Smart Grid", layout="wide")

# ملف بسيط لتخزين البيانات (قاعدة بيانات مصغرة) لكي تظهر التحديثات للكل
DB_FILE = "grid_data.json"

def load_data():
    if not os.path.exists(DB_FILE):
        initial_data = {f"Station {i}": 200 for i in range(1, 5)}
        save_data(initial_data)
        return initial_data
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

# تحميل البيانات الحالية
current_loads = load_data()

# القائمة الجانبية للتنقل بين الأدوار
st.sidebar.title("🛂 اختيار الدور")
role = st.sidebar.selectbox("من أنت؟", ["طالب (إدخال بيانات)", "مراقب (غرفة التحكم)"])

# --- واجهة الطالب ---
if role == "طالب (إدخال بيانات)":
    st.header("📲 واجهة المحطة الفرعية")
    st.info("قم بتعديل حمل محطتك وسيتم تحديثه في غرفة التحكم فوراً.")
    
    station_id = st.selectbox("اختر رقم محطتك:", [f"Station {i}" for i in range(1, 5)])
    
    # منزلق (Slider) لتعديل الأمبيرية
    new_val = st.slider(f"تعديل تيار {station_id} (Amps):", 0, 600, current_loads[station_id])
    
    if st.button("إرسال البيانات إلى السيرفر"):
        current_loads[station_id] = new_val
        save_data(current_loads)
        st.success(f"تم إرسال القيمة {new_val} أمبير بنجاح!")

# --- واجهة التحكم ---
else:
    st.header("🖥️ غرفة التحكم المركزية - جامعة الأنبار")
    
    # تحويل البيانات إلى جدول
    df = pd.DataFrame(list(current_loads.items()), columns=['Station', 'Current'])
    
    # تطبيق منطق البروتوكول (الأولوية)
    # التيار > 300A (أولوية قصوى) | التيار < 250A (إلغاء الأولوية)
    def check_priority(row):
        if row['Current'] >= 300: return "🔴 HIGH PRIORITY"
        elif row['Current'] <= 250: return "🟢 Normal"
        else: return "🟡 Monitoring"

    df['Status'] = df.apply(check_priority, axis=1)
    
    # فرز البيانات (البروتوكول يضع المشاكل في الأعلى)
    df = df.sort_values(by="Current", ascending=False)

    # عرض الإحصائيات في مربعات (Metrics)
    col1, col2, col3, col4 = st.columns(4)
    cols = [col1, col2, col3, col4]
    for i, (idx, row) in enumerate(df.iterrows()):
        color = "normal" if row['Current'] < 300 else "inverse"
        cols[i].metric(row['Station'], f"{row['Current']} A", delta=row['Status'], delta_color=color)

    st.divider()
    
    # الرسم البياني للأحمال
    st.subheader("📊 الرسم البياني لتوزيع الأحمال")
    st.bar_chart(df.set_index('Station')['Current'])
    
    # جدول البيانات التفصيلي
    st.subheader("📋 جدول مراقبة البروتوكول")
    st.table(df)

    # تنبيهات ذكية
    high_load_stations = df[df['Current'] >= 300]['Station'].tolist()
    if high_load_stations:
        st.error(f"⚠️ تحذير: حمل زائد في {', '.join(high_load_stations)}! البروتوكول يوجه الطاقة للمناطق الحرجة.")
        
