import streamlit as st
import pandas as pd
import numpy as np
import time

st.set_page_config(page_title="Al-Anbar Smart Grid - Exact Theft Location", layout="wide")

# --- 1. تهيئة الذاكرة ---
if 'time_step' not in st.session_state: st.session_state.time_step = 0
if 'simulated_theft_pole' not in st.session_state: st.session_state.simulated_theft_pole = None

st.session_state.time_step += 1

st.title("⚡ نظام الشبكة الذكية: التحديد الدقيق لمكان التجاوز")
st.markdown("### **إعداد الطالب: محمد نبيل**")
st.write("يحاكي هذا النظام خط تغذية (Feeder) يخرج من محطة التوزيع ويمر عبر 5 أعمدة كهرباء. النظام يحلل التوازن العقدي لتحديد مكان السرقة بدقة.")

# --- 2. القائمة الجانبية (محاكاة التجاوز الدقيق) ---
st.sidebar.header("⚠️ محاكاة التجاوز الموضعي")
st.sidebar.write("اختر العمود الذي سيحدث عليه الربط غير القانوني:")

target_pole = st.sidebar.selectbox("حدد مكان التجاوز:", ["لا يوجد تجاوز", "عمود 1", "عمود 2", "عمود 3", "عمود 4", "عمود 5"])

if target_pole != "لا يوجد تجاوز":
    st.session_state.simulated_theft_pole = target_pole
else:
    st.session_state.simulated_theft_pole = None

st.sidebar.divider()
if st.sidebar.button("♻️ تصفير النظام"):
    st.session_state.time_step = 0
    st.session_state.simulated_theft_pole = None
    st.rerun()

# --- 3. محاكاة خط التغذية (Feeder Nodal Analysis) ---
# نفترض خط تغذية يبدأ بجهد 220V وتيار كلي 100A
base_v = 220.0
feeder_nodes = ["عمود 1", "عمود 2", "عمود 3", "عمود 4", "عمود 5"]
node_data = []

# مقاومة السلك بين كل عمود والآخر (لتبسيط المحاكاة)
line_r = 0.05 

# استهلاك كل عمود (المنازل المربوطة به قانونياً)
legal_loads = {"عمود 1": 20, "عمود 2": 18, "عمود 3": 22, "عمود 4": 15, "عمود 5": 25}

current_v = base_v
total_i_in = sum(legal_loads.values()) # التيار الداخل للخط

# إضافة تيار التجاوز إذا تم تفعيله
theft_current = 0
if st.session_state.simulated_theft_pole:
    theft_current = np.random.uniform(35, 55) # تيار عالي مسروق
    total_i_in += theft_current

current_i_flowing = total_i_in

for node in feeder_nodes:
    # الاستهلاك القانوني
    legal_i = legal_loads[node] + np.random.uniform(-2, 2) 
    actual_consumed_i = legal_i
    
    # إذا كان التجاوز في هذا العمود، نزيد الاستهلاك الفعلي دون تسجيله في العدادات
    is_theft_here = (st.session_state.simulated_theft_pole == node)
    if is_theft_here:
        actual_consumed_i += theft_current
    
    # التيار الخارج للعمود التالي = التيار الداخل - الاستهلاك الفعلي في هذه العقدة
    i_out = current_i_flowing - actual_consumed_i
    
    # حساب هبوط الجهد بناءً على التيار المار (Ohm's Law)
    v_drop = current_i_flowing * line_r
    current_v -= v_drop
    
    # خوارزمية كشف المكان الدقيق (تحسب الفارق بين المسجل والمستهلك فعلياً)
    # في الواقع، النظام لا يعرف actual_consumed_i للتجاوز، بل يقيس التيار الداخل والخارج
    measured_i_in = current_i_flowing
    measured_i_out = i_out
    registered_legal_i = legal_i # ما تسجله العدادات الذكية للمنازل
    
    # الفاقد = التيار الداخل للعقدة - (التيار الخارج منها + الاستهلاك القانوني المسجل)
    current_loss = measured_i_in - (measured_i_out + registered_legal_i)
    
    if current_loss > 15: # السماحية للأخطاء البسيطة في القياس
        status = f"🪝 تجاوز مكتشف (موقع دقيق!)"
        node_color = "#800080" # بنفسجي
    else:
        status = "✅ سليم"
        node_color = "#d4edda" # أخضر
        
    node_data.append({
        "العقدة": node,
        "الجهد (V)": round(current_v, 2),
        "التيار الداخل للعقدة (A)": round(measured_i_in, 1),
        "الاستهلاك القانوني (A)": round(registered_legal_i, 1),
        "التيار المفقود (A)": round(current_loss, 1),
        "التشخيص": status
    })
    
    # تحديث التيار المار للعمود التالي
    current_i_flowing = i_out

df_feeder = pd.DataFrame(node_data)

# --- 4. العرض المرئي للبيانات ---
st.subheader("📍 تحليل عقد التوزيع (تحديد موقع التجاوز)")
st.write("يوضح الجدول التالي حسابات كيرشوف للتيار وهبوط الجهد لكل عمود على خط التغذية. النظام يبحث عن العقدة التي تحتوي على **تيار مفقود (Current Loss)** غير مبرر.")

def style_feeder(val):
    if '🪝' in str(val): return 'background-color: #800080; color: white; font-weight: bold'
    if '✅' in str(val): return 'background-color: #d4edda'
    return ''

st.table(df_feeder.style.map(style_feeder, subset=['التشخيص']))

# رسم بياني لهبوط الجهد
st.subheader("📉 الملف الجانبي لهبوط الجهد (Voltage Profile)")
st.write("لاحظ كيف يحدث هبوط حاد في الفولتية (Voltage Drop) مباشرة بعد نقطة التجاوز بسبب سحب التيار العالي.")
st.line_chart(df_feeder.set_index("العقدة")["الجهد (V)"])

time.sleep(1.5)
st.rerun()
