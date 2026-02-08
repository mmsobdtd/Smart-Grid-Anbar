import streamlit as st
import pandas as pd
import json
import os
import time
import random
from datetime import datetime

# --- إعدادات الصفحة ---
st.set_page_config(page_title="نظام طاقة الأنبار - محاكاة الانهيار الذكي", layout="wide")

DB_FILE = "anbar_power_db.json"

# --- إعدادات المحطات في الرمادي ---
STATIONS = {
    "مستشفى الرمادي التعليمي": {"max": 1000, "priority": 1},
    "معمل زجاج الرمادي": {"max": 1200, "priority": 2},
    "محطة مياه الورار": {"max": 900, "priority": 3},
    "جامعة الأنبار": {"max": 700, "priority": 4},
    "حي التأميم (سكني)": {"max": 500, "priority": 5}
}

# --- دوال إدارة النظام ---
def load_system_state():
    if not os.path.exists(DB_FILE): 
        return {"entries": [], "load_val": 0, "collapsed": False}
    try:
        with open(DB_FILE, "r", encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"entries": [], "load_val": 0, "collapsed": False}

def save_system_state(new_entries, protocol_on):
    data = load_system_state()
    if data["collapsed"]: return
    
    # 1. إضافة البيانات الجديدة
    data["entries"].extend(new_entries)
    
    # 2. منطق الضغط (الانهيار يعتمد على عدد البيانات)
    # كل قراءة مرسلة تزيد الضغط بمقدار 3% بشكل أساسي
    data_volume = len(new_entries)
    
    if protocol_on:
        # البروتوكول يقلل تأثير البيانات بنسبة 90% ويقوم بتبريد السيرفر
        pressure_increase = data_volume * 0.5
        data["load_val"] += pressure_increase
        data["load_val"] -= 2 # تبريد تلقائي (Auto-cool)
    else:
        # بدون بروتوكول: كل بيان يرفع الضغط بقوة (5% لكل محطة)
        pressure_increase = data_volume * 5.0
        data["load_val"] += pressure_increase

    # 3. التأكد من حدود المؤشر
    if data["load_val"] < 0: data["load_val"] = 0
    if data["load_val"] >= 100:
        data["load_val"] = 100
        data["collapsed"] = True
        
    # تقليص حجم السجل للحفاظ على الأداء
    data["entries"] = data["entries"][-60:] 
    
    with open(DB_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def create_random_reading(name):
    limit = STATIONS[name]["max"]
    new_val = random.randint(int(limit * 0.4), int(limit * 1.1))
    
    if new_val < (limit * 0.85): status, level = "🟢 مستقر", 1
    elif (limit * 0.85) <= new_val < (limit * 0.98): status, level = "🟡 تنبيه", 2
    else: status, level = "🔴 خطر", 3

    return {
        "المنشأة": name, "التيار (A)": new_val, "الحالة": status,
        "الوقت": datetime.now().strftime("%H:%M:%S"),
        "timestamp": time.time(), "level": level, 
        "priority": STATIONS[name]["priority"]
    }

# --- القائمة الجانبية ---
st.sidebar.title("⚡ مركز سيطرة الرمادي")
st.sidebar.markdown("---")
page = st.sidebar.radio("انتقل إلى:", ["🕹️ غرفة التحكم (الإرسال)", "🖥️ شاشة المراقبة (الاستلام)"])
protocol_active = st.sidebar.toggle("🛡️ تفعيل بروتوكول الحماية", value=True)

if st.sidebar.button("♻️ تصفير النظام (Reset)"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.rerun()

# ==========================================
# الصفحة 1: غرفة التحكم (مصدر الضغط)
# ==========================================
if page == "🕹️ غرفة التحكم (الإرسال)":
    st.title("🕹️ وحدة إرسال البيانات الميدانية")
    st.info("ملاحظة: كلما زاد عدد المحطات التي ترسل بياناتها، زاد الضغط على السيرفر.")
    
    state = load_system_state()
    if state["collapsed"]:
        st.error("❌ الـسـيـرفـر مـنـهـار! يرجى عمل ريست من القائمة الجانبية.")
    else:
        # اختيار المحطات التي سترسل بيانات الآن
        selected_stations = st.multiselect("اختر المحطات لبث بياناتها:", list(STATIONS.keys()), default=list(STATIONS.keys()))
        
        run = st.checkbox("🚀 بدء البث التلقائي المستمر")
        
        if run:
            placeholder = st.empty()
            while run:
                # التحقق من الانهيار داخل الحلقة
                if load_system_state()["collapsed"]:
                    st.rerun()
                    break
                
                # إنشاء بيانات للمحطات المختارة فقط
                batch = [create_random_reading(n) for n in selected_stations]
                save_system_state(batch, protocol_active)
                
                with placeholder.container():
                    st.success(f"📡 يتم الآن إرسال {len(batch)} حزم بيانات من محطات الرمادي...")
                    st.write(f"الوقت الحالي: {datetime.now().strftime('%H:%M:%S')}")
                time.sleep(1)

# ==========================================
# الصفحة 2: شاشة المراقبة (نتيجة الضغط)
# ==========================================
else:
    st.title("🖥️ شاشة المراقبة المركزية - الأنبار")
    
    placeholder = st.empty()
    while True:
        state = load_system_state()
        is_collapsed = state["collapsed"]
        current_load = state["load_val"]
        entries = state["entries"]
        
        with placeholder.container():
            if is_collapsed:
                st.markdown("""
                <div style='background-color:black; padding:50px; border: 15px solid red; text-align:center;'>
                    <h1 style='color:red; font-size: 80px;'>⚠️ SYSTEM CRASH ⚠️</h1>
                    <h2 style='color:white;'>انهيار منظومة البيانات في الرمادي</h2>
                    <p style='color:yellow; font-size: 20px;'>السبب: تدفق بيانات هائل تجاوز قدرة المعالجة (الضغط 100%)</p>
                    <p style='color:gray;'>يرجى تفعيل بروتوكول الحماية وإعادة تشغيل النظام</p>
                </div>
                """, unsafe_allow_html=True)
                break

            # عرض مؤشر الضغط الحقيقي
            col1, col2 = st.columns([1, 3])
            with col1:
                st.metric("مؤشر الضغط الحالي", f"{current_load:.1f}%")
            with col2:
                p_color = "red" if current_load > 80 else "orange" if current_load > 50 else "green"
                st.markdown(f"**حالة السيرفر:** :{p_color}[{'حرجة' if current_load > 80 else 'مستقرة'}]")
                st.progress(min(current_load / 100, 1.0))

            if not entries:
                st.warning("⚠️ لا توجد بيانات قادمة... تأكد من تشغيل البث من غرفة التحكم.")
            else:
                df = pd.DataFrame(entries)
                df_display = df.sort_values(by="timestamp", ascending=False)

                # رسم بياني للأحمال
                st.subheader("📊 تحليل تدفق الطاقة اللحظي")
                chart_df = df.pivot_table(index='الوقت', columns='المنشأة', values='التيار (A)').ffill()
                st.line_chart(chart_df)

                # جدول البيانات مع التلوين
                def style_critical(row):
                    if row['level'] == 3: return ['background-color: #450000; color: white'] * len(row)
                    return [''] * len(row)

                st.dataframe(
                    df_display[["المنشأة", "التيار (A)", "الحالة", "الوقت"]].style.apply(style_critical, axis=1),
                    use_container_width=True
                )
        
        time.sleep(1)
                
