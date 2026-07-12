import streamlit as st
from supabase import create_client, Client
import pandas as pd
import datetime
import io
import time
import hashlib

# 🎛️ Page Configuration & Styling Framework
st.set_page_config(
    page_title="SHC & Pak Post | Delivery Portal", 
    page_icon="📮", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# 🎨 Advanced Professional CSS for Dynamic Micro-Animations & Custom UI Elements
st.markdown("""
    <style>
    /* 🚫 Hiding Default Streamlit Interface Clutter */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    div[data-testid="stToolbar"] {visibility: hidden;}
    div[data-testid="InputInstructions"] {display: none !important;}
    
    /* Global Look & Feel */
    .stApp { background-color: #f8fafc; }
    body { font-family: 'Inter', system-ui, sans-serif; }
    
    /* Exact Brand Title Styling Matching the Provided Visuals */
    .brand-title { color: #0f172a; font-weight: 800; font-size: 2.1rem; letter-spacing: -0.05rem; margin-bottom: 0px; }
    .brand-subtitle { color: #64748b; font-size: 1.05rem; margin-bottom: 25px; font-weight: 500; }
    
    /* 🌌 Premium Button Micro-Animations (Applies to all interactive actions) */
    div.stButton > button {
        background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%) !important;
        color: white !important;
        border-radius: 8px !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        border: none !important;
        box-shadow: 0 4px 6px -1px rgba(30, 58, 138, 0.15) !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    div.stButton > button:hover {
        background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 15px -3px rgba(30, 58, 138, 0.3) !important;
    }
    div.stButton > button:active {
        transform: translateY(1px) !important;
    }
    
    /* Special Logout Styling Override */
    div[data-testid="stSidebar"] div.stButton > button {
        background: #ffffff !important;
        color: #ef4444 !important;
        border: 1px solid #fee2e2 !important;
        box-shadow: none !important;
    }
    div[data-testid="stSidebar"] div.stButton > button:hover {
        background: #fef2f2 !important;
        color: #dc2626 !important;
        border-color: #fca5a5 !important;
    }
    
    /* Smooth Input Field Custom Layouts */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        border-radius: 8px !important;
        border: 1px solid #cbd5e1 !important;
        transition: all 0.2s ease !important;
    }
    .stTextInput input:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15) !important;
    }
    
    /* Elegant Content Bounding Cards */
    .stForm, div.custom-card {
        background: #ffffff !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.03), 0 2px 4px -1px rgba(0,0,0,0.02) !important;
        border: 1px solid #e2e8f0 !important;
        padding: 24px !important;
    }
    
    /* Modern Navigation Tabs Customization */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: #e2e8f0; padding: 6px; border-radius: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: transparent; border: none; padding: 12px 24px; border-radius: 8px; font-weight: 600; color: #475569; transition: all 0.2s ease; }
    .stTabs [data-baseweb="tab"]:hover { color: #0f172a; background-color: #cbd5e1; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { background-color: #ffffff !important; color: #1e3a8a !important; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.08) !important; }
    
    /* Metric Card Viewports */
    .big-phone-display { font-size: 32px !important; font-weight: 800 !important; color: #16a34a !important; background-color: #f0fdf4; padding: 14px; border-radius: 10px; text-align: center; border: 2px solid #bbf7d0; letter-spacing: 1.2px; }
    .patient-card-header { font-size: 24px !important; font-weight: 700 !important; color: #0f172a; border-left: 5px solid #1e3a8a; padding-left: 12px; margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

# ⏳ PERSISTENT REFRESH MANAGER & TIMEOUT STRATEGY
TIMEOUT_LIMIT = 45 * 60  # 45 Minutes

# Initialization of structural runtime containers
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "last_activity" not in st.session_state:
    st.session_state.last_activity = time.time()
if "last_saved_entry" not in st.session_state:
    st.session_state.last_saved_entry = None

# Establish Database Connection
@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

try:
    supabase: Client = init_connection()
except Exception as e:
    st.error(f"Database interface offline: {e}")
    st.stop()

# 🔄 COOKIE-EMULATOR: Browser url state token checking mechanism
if not st.session_state.logged_in and "session_token" in st.query_params:
    token_username = st.query_params["session_token"]
    try:
        user_data = supabase.table("app_users").select("*").eq("username", token_username).execute()
        if user_data.data:
            # Re-auth matching validation index maps
            st.session_state.logged_in = True
            st.session_state.username = user_data.data[0]["username"]
            st.session_state.full_name = user_data.data[0]["full_name"]
            st.session_state.role = user_data.data[0]["role"]
            st.session_state.last_activity = time.time()
    except:
        pass

# Timeout computation
if st.session_state.logged_in:
    if time.time() - st.session_state.last_activity > TIMEOUT_LIMIT:
        st.session_state.logged_in = False
        st.query_params.clear()
        st.warning("🔄 Session expired due to 45 minutes of inactivity. Please re-authenticate.")
    else:
        st.session_state.last_activity = time.time()

# --- PASSWORD CHANGE INTERACTION CONSOLE (DIALOG MODAL) ---
@st.dialog("🔐 Change System Access Password")
def change_password_modal():
    st.write("Provide structural validation details to change your secure vault passkey.")
    curr_p = st.text_input("Current Password:", type="password")
    new_p = st.text_input("New Secure Password:", type="password")
    conf_p = st.text_input("Confirm New Password:", type="password")
    
    if st.button("Commit Access Token Update", use_container_width=True):
        if not curr_p or not new_p or not conf_p:
            st.error("All fields must be filled out.")
        elif new_p != conf_p:
            st.error("Mismatch detected! New entries must match precisely.")
        else:
            try:
                verify = supabase.table("app_users").select("*").eq("username", st.session_state.username).execute()
                if verify.data and verify.data[0]["password"] == curr_p.strip():
                    supabase.table("app_users").update({"password": new_p.strip()}).eq("username", st.session_state.username).execute()
                    st.success("Access tokens updated! Your password has been changed.")
                    time.sleep(1.2)
                    st.rerun()
                else:
                    st.error("Verification failed: Current password matches no records.")
            except Exception as e:
                st.error(f"Execution rejected by database: {e}")

# --- AUTHENTICATION SCREEN INTERFACE ---
if not st.session_state.logged_in:
    _, center_col, _ = st.columns([1, 1.1, 1])
    with center_col:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        with st.form("portal_auth_form"):
            st.markdown("<h3 style='text-align: center; color: #1e3a8a; font-weight:700; margin-bottom: 20px;'>📮 Portal Authentication</h3>", unsafe_allow_html=True)
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
                            
                            # Persistent state mapping inside web url parameters
                            st.query_params["session_token"] = user_query.data[0]["username"]
                            st.success("Authorized! Fetching parameters...")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("Authentication match rejected.")
                    except Exception as err:
                        st.error(f"Cloud interface error: {err}")
                else:
                    st.warning("Operational values missing.")
    st.stop()

# --- MAIN POST-LOGIN WORKSPACE WORKFLOW ---
with st.sidebar:
    st.markdown(f"👤 **Logged in as:**<br><b style='font-size:15px; color:#1e3a8a;'>{st.session_state.full_name}</b>", unsafe_allow_html=True)
    st.markdown(f"Privilege Matrix: `{st.session_state.role.upper()}`")
    st.markdown("---")
    
    if st.button("🔑 Change Password", use_container_width=True):
        change_password_modal()
        
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    if st.button("Logout 🚪", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.last_saved_entry = None
        st.query_params.clear() # Wipe URL parameter bindings completely
        st.rerun()

# Brand Identity Headers Mapped Identically to Original Specs
st.markdown("<div class='brand-title'>SHC & Pak Post | Free Home Delivery of Medicine</div>", unsafe_allow_html=True)
st.markdown("<div class='brand-subtitle'>Logistics Tracking & Quality Feedback System</div>", unsafe_allow_html=True)

# Access Control Navigation Configuration Setup
if st.session_state.role == "admin":
    tabs = st.tabs(["📊 Administrative Ingestion Engine", "👥 Operator Matrix & Security Audit Logs", "📞 Outbound Communications Hub"])
else:
    tabs = st.tabs(["📞 Outbound Communications Hub"])

# ----------------------------------------------------
# ADMIN INTERFACE MODULE: DATA INGESTION ENGINE
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
# ADMIN INTERFACE MODULE: OPERATOR SETTINGS
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
# GENERAL WORKSPACE MODULE: LOGISTICS COMMUNICATIONS DATA
# ----------------------------------------------------
staff_idx = 2 if st.session_state.role == "admin" else 0
with tabs[staff_idx]:
    st.markdown("### 📞 Outbound Communications Desk")
    
    # 📝 LIVE EDIT CORRECTION SHIFT CONSOLE FOR PREVIOUS DATA ENTRY
    if st.session_state.last_saved_entry:
        with st.expander("✏️ Quick-Correction Panel (Modify Last Saved Entry)", expanded=True):
            st.info(f"You can overwrite the evaluation metrics for the last updated file record profile: **{st.session_state.last_saved_entry['name']}**")
            mod_status = st.selectbox("Modify Status Context:", ["Delivered", "Issue / Complaint", "Pending"])
            mod_notes = st.text_area("Adjustment Audit Comments / Failure Reason:")
            if st.button("Commit Overwrite Changes", use_container_width=True):
                try:
                    supabase.table("patient_deliveries").update({"status": mod_status, "issue_reason": mod_notes}).eq("id", st.session_state.last_saved_entry["id"]).execute()
                    st.success("Record parameters updated dynamically.")
                    st.session_state.last_saved_entry = None
                    time.sleep(0.8)
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
        selected_key = st.selectbox("Select Patient Profile to Process:", list(manifest_mapping.keys()))
        
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
                        st.session_state.last_saved_entry = {"id": target_profile["id"], "name": target_profile["patient_name"]}
                        st.success("Session changes pushed successfully.")
                        time.sleep(0.8)
                        st.rerun()
                    except Exception as e: st.error(f"Commit exception: {e}")
