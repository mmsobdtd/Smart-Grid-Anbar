                time.sleep(1.5)
    
    # تنفيذ البروتوكول
    if protocol_on and not is_critical:
        st.sidebar.warning("🚫 البروتوكول حجب القيمة (غير ضرورية)")
    else:
        timestamp = time.strftime("%H:%M:%S")
        global_data["log"].append({
            "الوقت": timestamp, 
            "المحطة": user_id, 
            "القيمة": val, 
            "الأولوية": "🚨 عالية" if is_critical else "✅ عادية"
        })
        st.sidebar.success(f"تم الإرسال من {user_id}")

if st.sidebar.button("تصفير النظام 🗑️"):
    global_data["log"].clear()
    global_data["traffic_count"] = 0
    st.rerun()

# --- الشاشة الرئيسية (التحديث السلس) ---
# هذه الدالة تحدث الشاشة كل ثانية واحدة دون إعادة تحميل الصفحة بالكامل (No Flicker)
@st.fragment(run_every=1)
def update_dashboard():
    # تقليل مؤشر الضغط تدريجياً
    if global_data["traffic_count"] > 0:
        global_data["traffic_count"] -= 0.1

    # عرض المؤشرات العلوية (Metrics)
    m1, m2, m3 = st.columns(3)
    m1.metric("عدد القراءات المستلمة", len(global_data["log"]))
    m2.metric("حالة البروتوكول", "نشط ✅" if protocol_on else "معطل ❌")
    
    load = min(global_data["traffic_count"] / 10, 1.0)
    m3.progress(load, text="مؤشر ضغط الشبكة")

    if global_data["log"]:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📊 سجل البيانات المشترك")
            df = pd.DataFrame(global_data["log"]).sort_index(ascending=False)
            st.table(df.head(8)) # عرض آخر 8 قراءات
            
        with col2:
            st.subheader("📈 الرسم البياني اللحظي الموحد")
            chart_df = pd.DataFrame(global_data["log"])
            st.line_chart(chart_df.set_index('الوقت')['القيمة'])
    else:
        st.info("بانتظار دخول الطلاب... الشاشة ستتحدث تلقائياً فور الإرسال.")

# تشغيل تحديث الشاشة
update_dashboard()
