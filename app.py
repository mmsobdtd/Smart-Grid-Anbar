import streamlit as st
import time
import random

# Page Configuration
st.set_page_config(page_title="Privacy Guard | System Audit", page_icon="🔒", layout="centered")

# Custom UI Styling (Cyber-Professional Look)
st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #ffffff; }
    .stButton>button { 
        width: 100%; 
        border-radius: 8px; 
        height: 3.5em; 
        background-color: #1a1c24; 
        color: #00ffcc; 
        border: 1px solid #00ffcc; 
        font-weight: bold; 
    }
    .stButton>button:hover { background-color: #00ffcc; color: #1a1c24; border-color: #ffffff; }
    </style>
    """, unsafe_allow_html=True)

# Initialize Session State
if 'stage' not in st.session_state:
    st.session_state.stage = "init"

def set_stage(stage_name):
    st.session_state.stage = stage_name
    st.rerun()

# --- Stage 1: Initial Interface ---
if st.session_state.stage == "init":
    st.title("🔒 Cloud Privacy Guard")
    st.write("Welcome. This system performs a comprehensive audit of devices linked to your account to secure your personal data across the network.")
    
    if st.button("Start Cloud Security Audit"):
        with st.status("Establishing encrypted connection...", expanded=True) as status:
            time.sleep(2)
            st.write("📡 Scanning synchronization protocols...")
            time.sleep(2)
            st.write("🔗 Active linked devices detected...")
            status.update(label="Audit scan complete!", state="complete")
        set_stage("inventory")

# --- Stage 2: Device & File Inventory ---
elif st.session_state.stage == "inventory":
    st.subheader("📊 Current Connection Report")
    
    col1, col2 = st.columns(2)
    with col1:
        st.info("**Detected Devices:**\n1. Samsung Galaxy S24\n2. Apple iPad Air\n3. Windows Desktop PC")
    with col2:
        st.warning("**Status:**\nActive image synchronization detected between these 3 devices.")

    st.divider()
    st.write("📁 **Cloud Data Objects Identified:**")
    fake_data = ["Cloud_Snapshot_001.jpg", "Backup_Media_Final.png", "Sync_Cache_88.tmp"]
    for item in fake_data:
        st.text(f"📄 {item}")

    st.divider()
    if st.button("Execute Privacy Protocol (Global Cache Wipe)"):
        set_stage("purging")

# --- Stage 3: Purging Process (3-Minute Delay) ---
elif st.session_state.stage == "purging":
    st.header("⚡ Executing Purge Protocol")
    st.error("⚠️ CRITICAL: Do not close this window. System is currently disconnecting external nodes and wiping cached records to ensure your privacy.")
    
    total_wait = 180 # 3 minutes in seconds
    start_time = time.time()
    
    p_bar = st.progress(0)
    timer_display = st.empty()
    log_display = st.empty()
    
    target_devices = ["Samsung Galaxy S24", "Apple iPad Air", "Windows Desktop PC"]
    
    while time.time() - start_time < total_wait:
        elapsed = time.time() - start_time
        percent = min(int((elapsed / total_wait) * 100), 99)
        
        p_bar.progress(percent)
        timer_display.markdown(f"**Total Progress:** `{percent}%` | **Time Remaining:** `{int(total_wait - elapsed)} seconds`")
        
        # Real-time technical updates every 30 seconds
        if int(elapsed) % 30 == 0 and int(elapsed) > 0:
            idx = (int(elapsed) // 30) - 1
            if idx < len(target_devices):
                log_display.code(f"SUCCESS: Session terminated and cache wiped on [{target_devices[idx]}]", language="bash")
            
        time.sleep(1)
        
    p_bar.progress(100)
    set_stage("finished")

# --- Stage 4: Final Success Message ---
elif st.session_state.stage == "finished":
    st.balloons()
    st.success("✅ Privacy Granted Successfully.")
    
    st.markdown("""
    ### Final Security Report:
    * **Status:** All external device records have been successfully purged.
    * **Result:** **You are now the only authorized user with full access to this account's media vault.**
    """)
    
    st.info("System Notice: All active sync sessions have been revoked and your current device is now secured.")
    
    if st.button("Return to Control Center"):
        set_stage("init")
        
