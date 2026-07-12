import streamlit as st
from supabase import create_client, Client
import pandas as pd
import datetime
import io
import time

# 🎛️ Page Structural Settings
st.set_page_config(
    page_title="SHC & Pak Post | Delivery Portal", 
    page_icon="📮", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# 🎨 Premium C++ Style Tactile UI Engine (Clean Casing & Dark Mechanical Slate Theme)
st.markdown("""
    <style>
    /* 🚫 Clutter Removal Protocol */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    div[data-testid="stToolbar"] {visibility: hidden;}
    div[data-testid="InputInstructions"] {display: none !important;}
    
    /* Sleek Desktop Runtime Environment Theme Background */
    .stApp { background-color: #f1f5f9; }
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    
    /* Window Framework Brand Elements */
    .brand-title { color: #0f172a; font-weight: 800; font-size: 2.1rem; letter-spacing: -0.05rem; margin-bottom: 0px; margin-top: -30px; }
    .brand-subtitle { color: #475569; font-size: 1.05rem; margin-bottom: 30px; font-weight: 500; }
    
    /* 🧱 Ultra-Crisp Mechanical 3D Navigation & Utility Buttons CSS */
    div.stButton > button {
        background: linear-gradient(180deg, #475569 0%, #1e293b 100%) !important; /* Sleek Premium Slate Gray */
        color: #f8fafc !important;
        border: 1px solid #0f172a !important;
        border-radius: 6px !important;
        padding: 10px 22px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        text-transform: none !important; /* Preserves natural casing for premium clean readability */
        box-shadow: 0 4px 0 #0f172a, 0 6px 10px rgba(0, 0, 0, 0.12) !important;
        transition: all 0.05s ease-in-out !important;
    }
    div.stButton > button:hover {
        background: linear-gradient(180deg, #64748b 0%, #334155 100%) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 5px 0 #0f172a, 0 8px 12px rgba(0, 0, 0, 0.18) !important;
    }
    div.stButton > button:active {
        transform: translateY(3px) !important;
        box-shadow: 0 1px 0 #0f172a, 0 2px 4px rgba(0, 0, 0, 0.1) !important;
    }
    
    /* Highlighted State Override for Selected Active Tab Button (Deep Blue/Teal Accent) */
    .active-nav-btn div.stButton > button {
        background: linear-gradient(180deg, #2563eb 0%, #1d4ed8 100%) !important;
        border-color: #1e3a8a !important;
        box-shadow: 0 4px 0 #172554, 0 6px 10px rgba(37, 99, 235, 0.2) !important;
    }
    
    /* Danger/Logout Button Override Specs */
    div[data-testid="stSidebar"] div.stButton > button {
        background: linear-gradient(180deg, #ef4444 0%, #b91c1c 100%) !important;
        border-color: #7f1d1d !important;
        box-shadow: 0 4px 0 #7f1d1d !important;
    }
    div[data-testid="stSidebar"] div.stButton > button:hover {
        background: linear-gradient(180deg, #f87171 0%, #dc2626 100%) !important;
    }
    
    /* Rigid Form Containers and Desktop Panels */
    .stForm, div.custom-card {
        background: #ffffff !important;
        border-radius: 8px !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.2), 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03) !important;
        border: 1px solid #cbd5e1 !important;
        padding: 24px !important;
    }
    
    /* Metric Card Custom Outputs */
    .big-phone-display { font-size: 30px !important; font-weight: 800 !important; color: #15803d !important; background-color: #f0fdf4; padding: 12px; border-radius: 8px; text-align: center; border: 2px solid #bbf7d0; letter-spacing: 1px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.04); }
    .patient-card-header { font-size: 22px !important; font-weight: 700 !important; color: #0f172a; border-left: 6px solid #1e3a8a; padding-left: 12px; margin-bottom: 15px; }
    
    /* ⏳ Processing Animation Overlay Elements */
    .processing-pulse { color: #1d4ed8; font-weight: bold; font-size: 1.1rem; letter-spacing: 3px; animation: pulse 1.4s infinite; text-align: center; margin-top: 10px; }
    @keyframes pulse { 0%, 100% { opacity: 0.3; } 50% { opacity: 1; } }
    </style>
""", unsafe_allow_html=True)

# ⏳ SECURITY LOCKS & INTERVAL THRESHOLDS
TIMEOUT_LIMIT = 45 * 60  

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "last_activity" not in st.session_state:
    st.session_state.last_activity = time.time()
if "last_saved_entry" not in st.session_state:
    st.session_state.last_saved_entry = None
if "current_navigation_tab" not in st.session_state:
    st.session_state.current_navigation_tab = None

# Establish Secure Gateway Instance Connect
@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

try:
    supabase: Client = init_connection()
except Exception as e:
    st.error(f"Database sync fault: {e}")
    st.stop()

# 🔄 COOKIE HYDRATION: Re-populate token maps on manual window reloads
if not st.session_state.logged_in and "session_token" in st.query_params:
    try:
        preserved_user = st.query_params["session_token"]
        ud = supabase.table("app_users").select("*").eq("username", preserved_user).execute().data
        if ud:
            st.session_state.logged_in = True
            st.session_state.username = ud[0]["username"]
            st.session_state.full_name = ud[0]["full_name"]
            st.session_state.role = ud[0]["role"]
            st.session_state.last_activity = time.time()
            # Dynamic Route Protection on Refresh
            if st.session_state.current_navigation_tab is None:
                st.session_state.current_navigation_tab = "📊 Administrative Ingestion Engine" if ud[0]["role"] == "admin" else "📞 Outbound Communications Hub"
    except:
        pass

# Timeout Checker Execution Loop
if st.session_state.logged_in:
    if time.time() - st.session_state.last_activity > TIMEOUT_LIMIT:
        st.session_state.logged_in = False
        st.query_params.clear()
        st.warning("🔄 Session expired due to 45 minutes of inactivity. Please re-authenticate.")
    else:
        st.session_state.last_activity = time.time()

# Ensure navigation tab is never dangling empty
if st.session_state.logged_in and st.session_state.current_navigation_tab is None:
    st.session_state.current_navigation_tab = "📊 Administrative Ingestion Engine" if st.session_state.role == "admin" else "📞 Outbound Communications Hub"

# --- MODAL ACTION INTERFACE ---
@st.dialog("🔐 Change System Access Password")
def change_password_modal():
    st.write("Provide verification parameters to modify database access codes.")
    curr_p = st.text_input("Current Password:", type="password")
    new_p = st.text_input("New Secure Password:", type="password")
    conf_p = st.text_input("Confirm New Password:", type="password")
    
    if st.button("Commit Access Token Update", use_container_width=True):
        if not curr_p or not new_p or not conf_p:
            st.error("All validation blocks must be filled.")
        elif new_p != conf_p:
            st.error("Tokens match discrepancy! Match entries exactly.")
        else:
            try:
                verify = supabase.table("app_users").select("*").eq("username", st.session_state.username).execute()
                if verify.data and verify.data[0]["password"] == curr_p.strip():
                    supabase.table("app_users").update({"password": new_p.strip()}).eq("username", st.session_state.username).execute()
                    st.success("Access tokens modified successfully.")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Current authentication record rejected.")
            except Exception as e:
                st.error(f"Database write execution error: {e}")

# --- DESKTOP USER INTERFACE SIGN-ON FRAME ---
if not st.session_state.logged_in:
    _, center_col, _ = st.columns([1, 1.1, 1])
    with center_col:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        with st.form("portal_auth_form"):
            st.markdown("<h3 style='text-align: center; color: #1e3a8a; font-weight:700; margin-bottom: 20px;'>📮 Portal Authentication</h3>", unsafe_allow_html=True)
            user_in = st.text_input("Username Input", placeholder="Enter official assignment username", label_visibility="collapsed")
            pass_in = st.text_input("Password Input", type="password", placeholder="Enter authorization key", label_visibility="collapsed")
            
            st.markdown("<br>", unsafe_allow_html=True)
            submit_action = st.form_submit_button("Authenticate Session 🚀", use_container_width=True)
            
            if submit_action:
                if user_in and pass_in:
                    pulse_container = st.empty()
                    pulse_container.markdown("<div class='processing-pulse'>PROCESSING COMPILING LEDGERS . . . . .</div>", unsafe_allow_html=True)
                    
                    try:
                        user_query = supabase.table("app_users").select("*").eq("username", user_in.strip()).execute()
                        if user_query.data and user_query.data[0]["password"] == pass_in.strip():
                            st.session_state.logged_in = True
                            st.session_state.username = user_query.data[0]["username"]
                            st.session_state.full_name = user_query.data[0]["full_name"]
                            st.session_state.role = user_query.data[0]["role"]
                            st.session_state.last_activity = time.time()
                            st.query_params["session_token"] = user_query.data[0]["username"]
                            
                            # Hard redirect based on identity context upon first form entry
                            st.session_state.current_navigation_tab = "📊 Administrative Ingestion Engine" if user_query.data[0]["role"] == "admin" else "📞 Outbound Communications Hub"
                            
                            pulse_container.success("Access Authorized!")
                            time.sleep(0.6)
                            st.rerun()
                        else:
                            pulse_container.empty()
                            st.error("Authentication details match rejected.")
                    except Exception as err:
                        pulse_container.empty()
                        st.error(f"Cloud mapping access error: {err}")
                else:
                    st.warning("Provide complete secure values.")
    st.stop()

# --- OPERATIONAL DESKTOP SHELL AFTER ACCOUNT SIGN-ON ---
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
        st.query_params.clear()
        st.rerun()

# Layout Window Branding Blocks
st.markdown("<div class='brand-title'>SHC & Pak Post | Free Home Delivery of Medicine</div>", unsafe_allow_html=True)
st.markdown("<div class='brand-subtitle'>Logistics Tracking & Quality Feedback System</div>", unsafe_allow_html=True)

# 🧱 PREMIUM 3D SEGMENTED OPERATIONAL NAVIGATION BUTTONS MATRIX
if st.session_state.role == "admin":
    nc1, nc2, nc3 = st.columns(3)
    
    with nc1:
        t1_class = "active-nav-btn" if st.session_state.current_navigation_tab == "📊 Administrative Ingestion Engine" else ""
        st.markdown(f"<div class='{t1_class}'>", unsafe_allow_html=True)
        if st.button("📊 Administrative Ingestion Engine", use_container_width=True):
            st.session_state.current_navigation_tab = "📊 Administrative Ingestion Engine"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
    with nc2:
        t2_class = "active-nav-btn" if st.session_state.current_navigation_tab == "👥 Operator Matrix & Security Audit Logs" else ""
        st.markdown(f"<div class='{t2_class}'>", unsafe_allow_html=True)
        if st.button("👥 Operator Matrix & Logs", use_container_width=True):
            st.session_state.current_navigation_tab = "👥 Operator Matrix & Security Audit Logs"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
    with nc3:
        t3_class = "active-nav-btn" if st.session_state.current_navigation_tab == "📞 Outbound Communications Hub" else ""
        st.markdown(f"<div class='{t3_class}'>", unsafe_allow_html=True)
        if st.button("📞 Outbound Communications Hub", use_container_width=True):
            st.session_state.current_navigation_tab = "📞 Outbound Communications Hub"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
else:
    st.session_state.current_navigation_tab = "📞 Outbound Communications Hub"
    st.markdown("<div class='active-nav-btn'>", unsafe_allow_html=True)
    st.button("📞 Outbound Communications Hub", use_container_width=True, disabled=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ----------------------------------------------------
# MODULE BLOCK 1: DATA BULK INGESTION RUNTIME (ADMIN ENVIRONMENT)
# ----------------------------------------------------
if st.session_state.current_navigation_tab == "📊 Administrative Ingestion Engine" and st.session_state.role == "admin":
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
                    "booking_office": str(row[row[c_bo]]).strip() if c_bo in df.columns else "",
                    "status": "Pending"
                })
            
            try:
                supabase.table("patient_deliveries").upsert(staging_area, on_conflict="article_id").execute()
                st.success(f"Successfully processed entries into Supabase cloud node architecture.")
            except Exception as ex:
                st.error(f"Batch synchronization exception: {ex}")

# ----------------------------------------------------
# MODULE BLOCK 2: OPERATOR ACCOUNT MANAGEMENT CONTROL (ADMIN ENVIRONMENT)
# ----------------------------------------------------
elif st.session_state.current_navigation_tab == "👥 Operator Matrix & Security Audit Logs" and st.session_state.role == "admin":
    st.markdown("### 👥 Operational Account Provisioning Center")
    uc1, _ = st.columns(2)
    with uc1:
        st.markdown("#### ➕ Provision New Operator Account")
        nf = st.text_input("Operator Full Name")
        nu = st.text_input("Operational Username")
        np = st.text_input("Assigned Initial Password", type="password")
        if st.button("Register Operator Account", use_container_width=True):
            if nf and nu and np:
                try:
                    supabase.table("app_users").insert({"username": nu.strip(), "password": np.strip(), "full_name": nf.strip(), "role": "staff"}).execute()
                    st.success("New active account framework mapped successfully.")
                except Exception as e: st.error(f"Mapping rejection: {e}")

# ----------------------------------------------------
# MODULE BLOCK 3: DESKTOP QUALITY VERIFICATION COMMUNICATIONS DESK
# ----------------------------------------------------
elif st.session_state.current_navigation_tab == "📞 Outbound Communications Hub":
    st.markdown("### 📞 Outbound Communications Desk")
    
    if st.session_state.last_saved_entry:
        with st.expander("✏️ Quick-Correction Panel (Modify Last Saved Entry)", expanded=True):
            st.info(f"Modify configuration variables for your last updated record: **{st.session_state.last_saved_entry['name']}**")
            mod_status = st.selectbox("Modify Status Context:", ["Delivered", "Issue / Complaint", "Pending"])
            mod_notes = st.text_area("Adjustment Audit Failure Reasons:")
            if st.button("Commit Overwrite Changes", use_container_width=True):
                try:
                    supabase.table("patient_deliveries").update({"status": mod_status, "issue_reason": mod_notes}).eq("id", st.session_state.last_saved_entry["id"]).execute()
                    st.success("Cloud parameter entry values adjusted.")
                    st.session_state.last_saved_entry = None
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e: st.error(f"Write update fault: {e}")

    query_date = st.date_input("Filter Manifest Records by Booking Date:", datetime.date.today())
    
    try:
        recs = supabase.table("patient_deliveries").select("*").eq("booking_date", str(query_date)).execute().data
    except: recs = []
        
    if not recs:
        st.info("No logistics tracking matrices located matching this manifest date profile.")
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
                    st.error("Select verification response parameter before finalizing profile entry.")
                else:
                    try:
                        supabase.table("patient_deliveries").update(payload_buffer).eq("id", target_profile["id"]).execute()
                        st.session_state.last_saved_entry = {"id": target_profile["id"], "name": target_profile["patient_name"]}
                        st.success("Session logs pushed to database nodes.")
                        time.sleep(0.5)
                        st.rerun()
                    except Exception as e: st.error(f"Commit tracking sync error: {e}")
