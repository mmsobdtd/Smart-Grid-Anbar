import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# إعداد الصفحة
st.set_page_config(page_title="نظام طاقة الأنبار - الشبكة الشاملة", layout="wide")

DB_FILE = "grid_full_system.json"

# --- 1. توسيع الشبكة لتشمل 10 منشآت ---
LOCATIONS = {
    "مستشفى الرمادي التعليمي": {"avg": 400, "priority": 10},
    "معمل زجاج الرمادي": {"avg": 500, "priority": 10},
    "جامعة الأنبار (المجمع)": {"avg": 350, "priority": 8},
    "حي التأميم (سكني)": {"avg": 300, "priority": 7},
    "مبنى المحافظة (الإدارة)": {"avg": 250, "priority": 9},
    "محطة مياه الورار": {"avg": 450, "priority": 9},
    "سوق الرمادي الكبير": {"avg": 200, "priority": 6},
    "حي الأندلس": {"avg": 280, "priority": 5},
    "ملعب الرمادي الأولمبي": {"avg": 600, "priority": 4},
    "إنارة الشوارع الرئيسية": {"avg": 150, "priority": 3}
}

def load_data():
    if not os.path.exists(DB_FILE): return []
    try:
        with open(DB_FILE, "r", encoding='utf-8') as f:
            content = f.read()
            return json.loads(content) if content else []
    except: return []

def save_data(entries):
    history = load_data()
    history.extend(entries)
    # نحتفظ بآخر 150 سجل (لأن البيانات زادت)
    with open(DB_FILE, "w", encoding='utf-8') as f:
        json.dump(history[-150:], f, ensure_ascii=False)

def create_entry(name, current, batch_id):
    avg = LOCATIONS[name]["avg"]
    if current < avg: status, level = "🟢 مستقر", 1
    elif avg <= current < (avg * 1.2): status, level = "🟡 تنبيه", 2
    else: status, level = "🔴 خطر", 3
    
    return {
        "المنشأة": name, 
        "التيار (A)": current, 
        "الحالة": status,
        "الوقت": datetime.now().strftime("%H:%M:%S"),
        "timestamp": time.time(), 
        "level": level,
        "batch_id": batch_id
    }

# --- القائمة الجانبية ---
st.sidebar.title("🛂 مركز السيطرة")
page = st.sidebar.radio("انتقل إلى:", ["🕹️ لوحة التحكم", "🖥️ شاشة المراقبة"])
protocol_active = st.sidebar.toggle("تفعيل بروتوكول الأولويات", value=True)

if st.sidebar.button("🗑️ مسح السجلات"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.rerun()

# --- الصفحة 1: لوحة التحكم ---
if page == "🕹️ لوحة التحكم":
    st.title("🕹️ وحدة التحكم بالشبكة (10 قطاعات)")
    
    input_mode = st.selectbox("نمط العمل:", ["تلقائي (بث شامل 10 مواقع)", "يدوي (نبضات فردية)"])
    
    # 1. الوضع التلقائي (10 مواقع دفعة واحدة)
    if input_mode == "تلقائي (بث شامل 10 مواقع)":
        run_auto = st.toggle("🚀 بدء البث الجماعي الموحد", value=False)
        if run_auto:
            st.success("📡 البث نشط... يتم إرسال بيانات الـ 10 منشآت كل ثانية.")
            placeholder = st.empty()
            while run_auto:
                current_batch_id = time.time()
                batch = []
                for n in LOCATIONS.keys():
                    # توليد قيم عشوائية تحاكي الواقع
                    val = random.randint(int(LOCATIONS[n]["avg"]*0.7), int(LOCATIONS[n]["avg"]*1.6))
                    batch.append(create_entry(n, val, current_batch_id))
                
                save_data(batch)
                with placeholder.container():
                    st.write(f"✅ تم تحديث الشبكة بالكامل (10 قراءات) عند: {datetime.now().strftime('%H:%M:%S')}")
                time.sleep(1)
                st.rerun()
                
    # 2. الوضع اليدوي (زر لكل منشأة)
    else:
        st.subheader("🎛️ لوحة الإرسال اليدوي (Direct Pulse)")
        st.info("حدد القيمة ثم اضغط 'إرسال' لبث البيانات للموقع المحدد فقط.")
        
        # تقسيم الشاشة لعمودين لترتيب الـ 10 منشآت
        col1, col2 = st.columns(2)
        locations_list = list(LOCATIONS.keys())
        
        # النصف الأول
        with col1:
            for i in range(5):
                name = locations_list[i]
                st.markdown(f"**{name}**")
                c_slider, c_btn = st.columns([3, 1])
                val = c_slider.slider(f"A", 0, 800, value=LOCATIONS[name]["avg"], key=f"s_{i}", label_visibility="collapsed")
                if c_btn.button("إرسال", key=f"b_{i}"):
                    # إرسال نبضة فردية
                    batch_id = time.time()
                    save_data([create_entry(name, val, batch_id)])
                    st.toast(f"تم إرسال بيانات {name} بنجاح!")
        
        # النصف الثاني
        with col2:
            for i in range(5, 10):
                name = locations_list[i]
                st.markdown(f"**{name}**")
                c_slider, c_btn = st.columns([3, 1])
                val = c_slider.slider(f"A", 0, 800, value=LOCATIONS[name]["avg"], key=f"s_{i}", label_visibility="collapsed")
                if c_btn.button("إرسال", key=f"b_{i}"):
                    # إرسال نبضة فردية
                    batch_id = time.time()
                    save_data([create_entry(name, val, batch_id)])
                    st.toast(f"تم إرسال بيانات {name} بنجاح!")

# --- الصفحة 2: شاشة المراقبة ---
else:
    st.title("🖥️ مركز المراقبة والتحليل اللحظي")

    @st.fragment(run_every="1s")
    def update_monitor():
        data = load_data()
        
        # المخطط البياني
        st.subheader("📊 المخطط الزمني للأحمال (Live Trend)")
        if data:
            df_chart = pd.DataFrame(data)
            # نأخذ آخر 50 قراءة فقط للرسم ليكون واضحاً
            chart_data = df_chart.tail(50).pivot_table(index='الوقت', columns='المنشأة', values='التيار (A)').ffill()
            st.line_chart(chart_data, height=300)
        
        # الجدول
        st.subheader("📋 سجل البيانات (Live Feed)")
        if not data:
            st.warning("⚠️ لا توجد بيانات. ابدأ البث من لوحة التحكم.")
            return
            
        df = pd.DataFrame(data)
        
        # --- منطق الفرز (Batch + Priority) ---
        if protocol_active:
            # 1. ترتيب حسب رقم الدفعة (الأحدث فوق)
            # 2. ترتيب حسب الخطر داخل الدفعة الواحدة
            df_display = df.sort_values(by=["batch_id", "level"], ascending=[False, False])
        else:
            # ترتيب زمني فقط
            df_display = df.sort_values(by="timestamp", ascending=False)

        # التنسيق
        def style_rows(row):
            if row['level'] == 3: return ['background-color: #800000; color: white; font-weight: bold'] * len(row)
            if row['level'] == 2: return ['background-color: #705d00; color: white'] * len(row)
            return [''] * len(row)

        cols_to_show = ["المنشأة", "التيار (A)", "الحالة", "الوقت"]
        st.dataframe(
            df_display[cols_to_show + ['level']].style.apply(style_rows, axis=1),
            use_container_width=True, 
            height=600,
            column_config={"level": None}
        )

    update_monitor()
    
