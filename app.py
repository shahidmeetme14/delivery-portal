import streamlit as st
from supabase import create_client, Client
import pandas as pd
import datetime
import io
import time

# Premium Page & Theme Configurations
st.set_page_config(
    page_title="SHC & Pak Post | Patient Feedback Portal", 
    page_icon="📮", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Advanced Clean CSS Injection (Removes Streamlit footprints & hides form submit hints)
st.markdown("""
    <style>
    /* 🚫 Hiding Streamlit Default Elements & Form Instructions */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    div[data-testid="stToolbar"] {visibility: hidden;}
    div[data-testid="InputInstructions"] {display: none !important;}
    
    /* Premium High-End Typography & Color Palette */
    .stApp { background-color: #f8fafc; }
    body { font-family: 'Inter', -apple-system, sans-serif; }
    
    /* Title optimization as requested (Slightly smaller, ultra clean corporate look) */
    .main-title { color: #1e3a8a; font-weight: 800; font-size: 1.9rem; letter-spacing: -0.04rem; margin-bottom: 2px; }
    .sub-title { color: #64748b; font-size: 0.95rem; margin-bottom: 25px; font-weight: 500; }
    
    /* Elite Card & Container Blocks */
    .stForm, div[data-testid="stVerticalBlock"] > div:has(div.stForm), .custom-card {
        background: #ffffff !important;
        border-radius: 12px !important;
        box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1) !important;
        border: 1px solid #e2e8f0 !important;
        padding: 24px !important;
    }
    
    /* Phone and Operational Metric Viewers */
    .big-phone-display { font-size: 32px !important; font-weight: 800 !important; color: #1e3a8a !important; background-color: #f0fdf4; padding: 14px; border-radius: 10px; text-align: center; border: 2px solid #bbf7d0; letter-spacing: 1.2px; }
    .patient-card-header { font-size: 24px !important; font-weight: 700 !important; color: #0f172a; border-left: 5px solid #1e3a8a; padding-left: 10px; margin-bottom: 15px; }
    
    /* Modern Navigation Tabs Customization */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: #f1f5f9; padding: 6px; border-radius: 8px; border: 1px solid #e2e8f0; }
    .stTabs [data-baseweb="tab"] { background-color: transparent; border: none; padding: 10px 20px; border-radius: 6px; font-weight: 600; color: #64748b; }
    .stTabs [data-baseweb="tab"]:hover { color: #0f172a; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { background-color: #ffffff !important; color: #1e3a8a !important; box-shadow: 0 1px 2px 0 rgba(0,0,0,0.05) !important; }
    </style>
""", unsafe_allow_html=True)

# ⏳ SESSION TIMEOUT & PERSISTENCE MANAGEMENT 
TIMEOUT_LIMIT = 45 * 60  # 45 Minutes in seconds

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "last_activity" not in st.session_state:
    st.session_state.last_activity = time.time()
if "saved_buffer_state" not in st.session_state:
    st.session_state.saved_buffer_state = None
if "last_saved_entry" not in st.session_state:
    st.session_state.last_saved_entry = None

# Track and handle expiration limits
if st.session_state.logged_in:
    elapsed_time = time.time() - st.session_state.last_activity
    if elapsed_time > TIMEOUT_LIMIT:
        # Save working checkpoint before flashing out context
        if "selected_patient_key" in st.session_state:
            st.session_state.saved_buffer_state = st.session_state.selected_patient_key
        st.session_state.logged_in = False
        st.warning("🔄 Session expired due to 45 minutes of inactivity. Please re-authenticate.")
    else:
        st.session_state.last_activity = time.time() # Update watch timestamp

# Initialize Remote Cloud Connect
@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

try:
    supabase: Client = init_connection()
except Exception as e:
    st.error(f"Database handshakes failed: {e}")
    st.stop()

# --- PASSWORD CHANGE INTERACTION CONSOLE (DIALOG MODAL) ---
@st.dialog("🔐 Change System Access Password")
def change_password_modal():
    st.write("Provide structural validation details to change your secure vault passkey.")
    curr_p = st.text_input("Current Password:", type="password")
    new_p = st.text_input("New Secure Password:", type="password")
    conf_p = st.text_input("Confirm New Password:", type="password")
    
    if st.button("Commit Access Token Update", use_container_width=True):
        if not curr_p or not new_p or not conf_p:
            st.error("All authentication fields must be fulfilled.")
        elif new_p != conf_p:
            st.error("Mismatch detected! New password entries must match precisely.")
        else:
            try:
                verify = supabase.table("app_users").select("*").eq("username", st.session_state.username).execute()
                if verify.data and verify.data[0]["password"] == curr_p.strip():
                    supabase.table("app_users").update({"password": new_p.strip()}).eq("username", st.session_state.username).execute()
                    st.success("Access tokens updated! Your password has been changed.")
                    time.sleep(1.5)
                    st.rerun()
                else:
                    st.error("Verification failed: Current password matches no records.")
            except Exception as e:
                st.error(f"Execution rejected by database: {e}")

# --- SECURE AUTENTICATION LAYER ---
if not st.session_state.logged_in:
    _, center_col, _ = st.columns([1, 1.2, 1])
    with center_col:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        with st.form("portal_auth_form"):
            st.markdown("<h3 style='text-align: center; color: #1e3a8a; font-weight:700;'>📮 Portal Authentication</h3>", unsafe_allow_html=True)
            user_in = st.text_input("Username Input", placeholder="Enter official assignment username", label_visibility="collapsed")
            pass_in = st.text_input("Password Input", type="password", placeholder="Enter authorization key", label_visibility="collapsed")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("Authenticate Session 🚀", use_container_width=True):
                if user_in and pass_in:
                    try:
                        user_query = supabase.table("app_users").select("*").eq("username", user_in.strip()).execute()
                        if user_query.data and user_query.data[0]["password"] == pass_in.strip():
                            st.session_state.logged_in = True
                            st.session_state.username = user_query.data[0]["username"]
                            st.session_state.full_name = user_query.data[0]["full_name"]
                            st.session_state.role = user_query.data[0]["role"]
                            st.session_state.last_activity = time.time()
                            st.success("Authorized! Fetching parameters...")
                            st.rerun()
                        else:
                            st.error("Authentication match rejected.")
                    except Exception as err:
                        st.error(f"Cloud interface error: {err}")
                else:
                    st.warning("Operational values missing.")
    st.stop()

# --- POST LOGIN CONTEXT BOUNDARY ---
if st.session_state.saved_buffer_state:
    st.info("💡 An active session checkpoint was located from your previous execution.")
    res_choice = st.radio("Choose operational checkpoint mode:", ["Resume from where you left off", "Discard and start standard pipeline"], horizontal=True)
    if res_choice == "Discard and start standard pipeline":
        st.session_state.saved_buffer_state = None
        st.rerun()

# Sidebar Configuration Workspace Area
with st.sidebar:
    st.markdown(f"👤 **Logged in as:**<br><b style='font-size:15px; color:#1e3a8a;'>{st.session_state.full_name}</b>", unsafe_allow_html=True)
    st.markdown(f"Privilege Matrix: `{st.session_state.role.upper()}`")
    st.markdown("---")
    
    # Trigger dialog box for password modification
    if st.button("🔑 Change Password", use_container_width=True):
        change_password_modal()
        
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    if st.button("Logout 🚪", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.saved_buffer_state = None
        st.rerun()

# Standardized Persistent Header Configuration Across All Access Groups
st.markdown("<div class='main-title'>SHC & Pak Post | Free Home Delivery of Medicine</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>Logistics Tracking & Quality Feedback System</div>", unsafe_allow_html=True)

# Access Control Navigation Configurations
if st.session_state.role == "admin":
    tabs = st.tabs(["📊 Administrative Ingestion Engine", "👥 Operator Matrix & Security Audit Logs", "📞 Outbound Communications Hub"])
else:
    tabs = st.tabs(["📞 Outbound Communications Hub"])

# ----------------------------------------------------
# ADMIN COMPONENT: FILE INGESTION & DATA SYNC
# ----------------------------------------------------
if st.session_state.role == "admin":
    with tabs[0]:
        st.markdown("### 📥 Bulk Logistics Ingestion Engine")
        source_file = st.file_uploader("Upload Parcel Manifest Data Sheet (.xlsx or .csv)", type=["xlsx", "csv"])
        
        if source_file is not None:
            df = pd.read_excel(source_file) if source_file.name.endswith('.xlsx') else pd.read_csv(source_file)
            st.success("Manifest read successfully!")
            
            mc1, mc2, mc3 = st.columns(3)
            with mc1:
                c_article = st.selectbox("Article ID Column:", df.columns)
                c_name = st.selectbox("Patient Name Column:", df.columns)
                c_city = st.selectbox("Patient City Column:", df.columns)
            with mc2:
                c_phone = st.selectbox("Contact Number Column:", df.columns)
                c_date = st.selectbox("Booking Date Column:", df.columns)
                c_mrn = st.selectbox("MRN No. Column:", df.columns)
            with mc3:
                c_address = st.selectbox("Address Column:", df.columns)
                c_bo = st.selectbox("Booking Office Column:", df.columns)
                dup_target = st.selectbox("De-duplication Target:", df.columns, index=df.columns.get_loc(c_article))

            if st.button("🚀 Push Verified Records to Cloud Database", use_container_width=True):
                cleaned_records = df.drop_duplicates(subset=[dup_target], keep='first')
                staging_area = []
                
                for _, row in cleaned_records.iterrows():
                    final_dt = str(datetime.date.today())
                    try: final_dt = pd.to_datetime(row[c_date]).strftime('%Y-%m-%d')
                    except: pass
                        
                    staging_area.append({
                        "article_id": str(row[c_article]).strip(),
                        "patient_name": str(row[c_name]).strip(),
                        "phone_number": str(row[c_phone]).strip(),
                        "booking_date": final_dt,
                        "address": str(row[c_address]).strip(),
                        "patient_city": str(row[c_city]).strip(),
                        "mrn_no": str(row[c_mrn]).strip(),
                        "booking_office": str(row[c_bo]).strip(),
                        "status": "Pending"
                    })
                
                try:
                    supabase.table("patient_deliveries").upsert(staging_area, on_conflict="article_id").execute()
                    st.success(f"Successfully processed and synchronized entries into Supabase server storage.")
                except Exception as ex:
                    st.error(f"Batch write failure: {ex}")

# ----------------------------------------------------
# ADMIN COMPONENT: OPERATOR MANAGEMENT CONSOLE
# ----------------------------------------------------
if st.session_state.role == "admin":
    with tabs[1]:
        st.markdown("### 👥 Operational Account Provisioning Center")
        uc1, uc2 = st.columns(2)
        with uc1:
            st.markdown("#### ➕ Provision New Operator Account")
            nf = st.text_input("Operator Full Name")
            nu = st.text_input("Operational Username")
            np = st.text_input("Assigned Initial Password", type="password")
            if st.button("Register Operator Account", use_container_width=True):
                if nf and nu and np:
                    try:
                        supabase.table("app_users").insert({"username": nu.strip(), "password": np.strip(), "full_name": nf.strip(), "role": "staff"}).execute()
                        st.success("New terminal employee profile mapped successfully.")
                    except Exception as e: st.error(f"Error mapping account: {e}")

# ----------------------------------------------------
# COMPONENT 3: COMMUNICATIONS HUB & MODIFICATION INTERFACE
# ----------------------------------------------------
staff_idx = 2 if st.session_state.role == "admin" else 0
with tabs[staff_idx]:
    st.markdown("### 📞 Outbound Communications Desk")
    
    # 📝 LAST SAVED QUICK EDIT SHORTCUT COMPONENT
    if st.session_state.last_saved_entry:
        with st.expander("✏️ Quick-Correction Panel (Modify Last Saved Entry)", expanded=False):
            st.info(f"You can overwrite the evaluation metrics for the last updated file record profile: **{st.session_state.last_saved_entry['name']}**")
            mod_status = st.selectbox("Modify Status Context:", ["Delivered", "Issue / Complaint", "Pending"])
            mod_notes = st.text_area("Adjustment Audit Comments:")
            if st.button("Commit Overwrite Changes", use_container_width=True):
                try:
                    supabase.table("patient_deliveries").update({"status": mod_status, "issue_reason": mod_notes}).eq("id", st.session_state.last_saved_entry["id"]).execute()
                    st.success("Record parameters updated dynamically.")
                    st.session_state.last_saved_entry = None
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Modification tracking exception: {e}")

    query_date = st.date_input("Filter Manifest Records by Booking Date:", datetime.date.today())
    
    try:
        recs = supabase.table("patient_deliveries").select("*").eq("booking_date", str(query_date)).execute().data
    except: recs = []
        
    if not recs:
        st.info("No matching configuration matrices located for this date profile.")
    else:
        manifest_mapping = {f"{r['patient_name']} (MRN: {r.get('mrn_no', 'N/A')}) - [{r['status']}]": r for r in recs}
        
        # Checking for auto-resume state if timeout occurred
        start_idx = 0
        if st.session_state.saved_buffer_state in manifest_mapping:
            start_idx = list(manifest_mapping.keys()).index(st.session_state.saved_buffer_state)
            st.session_state.saved_buffer_state = None # Clear after tracking fallback match
            
        selected_key = st.selectbox("Select Patient Profile to Process:", list(manifest_mapping.keys()), index=start_idx)
        st.session_state.selected_patient_key = selected_key
        
        target_profile = manifest_mapping[selected_key]
        st.markdown("<hr>", unsafe_allow_html=True)
        
        l_panel, r_panel = st.columns(2)
        with l_panel:
            st.markdown(f"<div class='patient-card-header'>👤 {target_profile['patient_name']}</div>", unsafe_allow_html=True)
            st.write(f"🔢 **MRN Number:** `{target_profile.get('mrn_no', 'N/A')}`")
            st.write(f"📦 **Consignment ID:** `{target_profile['article_id']}`")
            st.write(f"🏢 **Booking Office:** {target_profile.get('booking_office', 'N/A')}")
            st.write(f"📍 **Patient City:** {target_profile.get('patient_city', 'N/A')}")
            st.write(f"🏠 **Destination Address:** {target_profile['address']}")
            
            st.markdown("#### 🎴 DIAL THIS PHONE NUMBER FROM LANDLINE:")
            st.markdown(f"<div class='big-phone-display'>{target_profile['phone_number']}</div>", unsafe_allow_html=True)
        
        with r_panel:
            st.markdown("#### 📝 Live Quality Verification & Audit Questionnaire")
            is_delivered = st.radio("Has the consignee physically received the delivery?", ["Select Assessment Option", "Yes", "No"])
            payload_buffer = {}
            
            if is_delivered == "Yes":
                payload_buffer["status"] = "Delivered"
                payload_buffer["delivery_date"] = str(st.date_input("Delivery Verification Date", datetime.date.today()))
                payload_buffer["received_mode"] = st.radio("Delivery Execution Mode:", ["Delivered by postman to home address", "Collected directly from local post office branch"])
                payload_buffer["extra_money_charged"] = st.radio("Did the delivery agent request any unauthorized monetary payment/tips?", ["No", "Yes"])
            elif is_delivered == "No":
                payload_buffer["status"] = "Issue / Complaint"
                payload_buffer["issue_reason"] = st.selectbox("Select Primary Failure Mode:", ["Wrong Delivery Status on EMTTS", "Incomplete Address / Premises Locked", "Logistics Delay", "Formal Institutional Dispute"])
                
            if st.button("💾 Finalize Session & Commit Logs", use_container_width=True):
                if is_delivered == "Select Assessment Option":
                    st.error("Please provide a verification status choice.")
                else:
                    try:
                        supabase.table("patient_deliveries").update(payload_buffer).eq("id", target_profile["id"]).execute()
                        # Record tracking context for quick adjustment workspace overrides
                        st.session_state.last_saved_entry = {"id": target_profile["id"], "name": target_profile["patient_name"]}
                        st.success("Session changes pushed successfully.")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e: st.error(f"Commit exception: {e}")
