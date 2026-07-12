import streamlit as st
from supabase import create_client, Client
import pandas as pd
import datetime
import io
import time
import requests
from bs4 import BeautifulSoup

# 🎛️ Page Structural Settings
st.set_page_config(
    page_title="SHC & Pak Post | Delivery Portal", 
    page_icon="📮", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# 🎨 Premium UI Engine Dark Mechanical Slate Theme
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    div[data-testid="stToolbar"] {visibility: hidden;}
    div[data-testid="InputInstructions"] {display: none !important;}
    
    /* 🛠️ FIX: Forces the Sidebar Arrow to ALWAYS stay visible even if header is hidden */
    button[data-testid="collapsedControl"] {
        visibility: visible !important;
        background-color: #1e293b !important;
        color: #f8fafc !important;
        border-radius: 4px !important;
        margin-top: 5px !important;
        margin-left: 5px !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2) !important;
    }
    
    .stApp { background-color: #f1f5f9; }
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    
    .brand-title { color: #0f172a; font-weight: 800; font-size: 2.1rem; letter-spacing: -0.05rem; margin-bottom: 0px; margin-top: -30px; }
    .brand-subtitle { color: #475569; font-size: 1.05rem; margin-bottom: 30px; font-weight: 500; }
    
    div.stButton > button {
        background: linear-gradient(180deg, #475569 0%, #1e293b 100%) !important;
        color: #f8fafc !important;
        border: 1px solid #0f172a !important;
        border-radius: 6px !important;
        padding: 10px 22px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
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
    
    .active-nav-btn div.stButton > button {
        background: linear-gradient(180deg, #2563eb 0%, #1d4ed8 100%) !important;
        border-color: #1e3a8a !important;
        box-shadow: 0 4px 0 #172554, 0 6px 10px rgba(37, 99, 235, 0.2) !important;
    }
    
    .stForm, div.custom-card {
        background: #ffffff !important;
        border-radius: 8px !important;
        border: 1px solid #cbd5e1 !important;
        padding: 24px !important;
    }
    
    .big-phone-display { font-size: 30px !important; font-weight: 800 !important; color: #15803d !important; background-color: #f0fdf4; padding: 12px; border-radius: 8px; text-align: center; border: 2px solid #bbf7d0; letter-spacing: 1px; }
    .patient-card-header { font-size: 22px !important; font-weight: 700 !important; color: #0f172a; border-left: 6px solid #1e3a8a; padding-left: 12px; margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

TIMEOUT_LIMIT = 45 * 60  

# 🔐 Safe Core Initialization State
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "last_activity" not in st.session_state: st.session_state.last_activity = time.time()
if "current_navigation_tab" not in st.session_state: st.session_state.current_navigation_tab = None
if "full_name" not in st.session_state: st.session_state.full_name = ""
if "role" not in st.session_state: st.session_state.role = ""

@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

try:
    supabase: Client = init_connection()
except Exception as e:
    st.error(f"Database sync fault: {e}")
    st.stop()

# 🌐 REAL WEB SCRAPER FOR PAKISTAN POST EMTTS
def fetch_live_emtts_status(article_id):
    if not article_id or article_id.strip() == "":
        return "⚠️ Invalid Article ID", "No data mapped."
    
    tracking_url = f"https://ep.gov.pk/tracking.asp"
    payload = {'tracking_id': article_id.strip()}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.post(tracking_url, data=payload, headers=headers, timeout=15)
        if response.status_code != 200:
            return "❌ Server Unreachable", f"Pak Post server returned HTTP Status {response.status_code}."
        
        soup = BeautifulSoup(response.text, 'html.parser')
        tables = soup.find_all('table')
        
        if len(tables) < 2:
            return "🔎 Record Not Found", "Pakistan Post has no active tracking records for this Article ID yet."
        
        tracking_logs = []
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cols = [ele.text.strip().replace('\n', ' ').replace('\r', '') for ele in row.find_all(['td', 'th'])]
                if cols and not any('tracking id' in str(c).lower() for c in cols):
                    tracking_logs.append(" | ".join([c for c in cols if c]))
        
        latest_status = "Data Found"
        for log in tracking_logs:
            if "delivered" in log.lower():
                latest_status = "✅ Delivered"
                break
            elif "transit" in log.lower() or "dispatched" in log.lower():
                latest_status = "🚚 In Transit"
                break
            elif "booked" in log.lower():
                latest_status = "📦 Booked / Received at Office"
                break
        
        clean_log_output = "\n".join(tracking_logs[:12])
        return latest_status, clean_log_output if clean_log_output else "Tracking sheet template layout parse error."
        
    except requests.exceptions.Timeout:
        return "⏱️ Timeout Error", "Pakistan Post server took too long to respond. Please try again."
    except Exception as e:
        return "⚠️ Integration Link Broken", f"Failed to crawl tracking engine data: {str(e)}"

# Cookie Session Hydration (Token Link Reader)
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
    except: pass

if st.session_state.logged_in:
    if time.time() - st.session_state.last_activity > TIMEOUT_LIMIT:
        st.session_state.logged_in = False
        st.query_params.clear()
        st.warning("🔄 Session expired due to inactivity.")
    else:
        st.session_state.last_activity = time.time()

if st.session_state.logged_in and st.session_state.current_navigation_tab is None:
    st.session_state.current_navigation_tab = "📊 Administrative Ingestion Engine" if st.session_state.role == "admin" else "📞 Outbound Communications Hub"

# Sidebar Workspace Layout
with st.sidebar:
    if st.session_state.logged_in:
        st.markdown(f"👤 **Logged in as:**<br><b style='font-size:15px; color:#1e3a8a;'>{st.session_state.full_name}</b>", unsafe_allow_html=True)
        st.markdown(f"Privilege Matrix: `{st.session_state.role.upper()}`")
        st.markdown("---")
        if st.button("Logout 🚪", use_container_width=True):
            st.session_state.logged_in = False
            st.query_params.clear()
            st.rerun()
    else:
        st.markdown("🔒 **Session Status: Locked**", unsafe_allow_html=True)

st.markdown("<div class='brand-title'>SHC & Pak Post | Free Home Delivery of Medicine</div>", unsafe_allow_html=True)
st.markdown("<div class='brand-subtitle'>Logistics Tracking & Quality Feedback System</div>", unsafe_allow_html=True)

# Main Navigation Tabs Matrix
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
    if st.session_state.logged_in:
        st.session_state.current_navigation_tab = "📞 Outbound Communications Hub"

st.markdown("<br>", unsafe_allow_html=True)

# 🔐 AUTHENTICATION GATE & BACKUP LOGIN PANEL
if not st.session_state.logged_in:
    st.markdown("### 🔒 Secure Portal Authentication")
    
    with st.form("portal_fallback_login"):
        st.info("💡 Link session dropped or bare URL detected. Please enter your database credentials to unlock the terminal.")
        input_user = st.text_input("Username / Operator ID")
        input_pass = st.text_input("Security Password", type="password")
        btn_login = st.form_submit_button("Verify & Unlock Portal", use_container_width=True)
        
        if btn_login:
            if input_user and input_pass:
                try:
                    ud = supabase.table("app_users").select("*").eq("username", input_user.strip()).eq("password", input_pass.strip()).execute().data
                    if ud:
                        st.session_state.logged_in = True
                        st.session_state.username = ud[0]["username"]
                        st.session_state.full_name = ud[0]["full_name"]
                        st.session_state.role = ud[0]["role"]
                        st.session_state.last_activity = time.time()
                        st.success("✅ Access Granted! Synchronizing workspace context...")
                        time.sleep(0.6)
                        st.rerun()
                    else:
                        st.error("❌ Invalid Username or Password. Authentication rejected.")
                except Exception as ex:
                    st.error(f"Database Node Error: {ex}")
            else:
                st.warning("Please fill out both fields to execute secure verification.")
else:
    # ----------------------------------------------------
    # ADMIN INGESTION HUB
    # ----------------------------------------------------
    if st.session_state.current_navigation_tab == "📊 Administrative Ingestion Engine" and st.session_state.role == "admin":
        st.markdown("### 📥 Bulk Logistics Ingestion Engine")
        source_file = st.file_uploader("Upload Parcel Manifest Data Sheet (.xlsx or .csv)", type=["xlsx", "csv"])
        
        if source_file is not None:
            if source_file.name.endswith('.xlsx'):
                all_sheets = pd.read_excel(source_file, sheet_name=None)
                df = pd.concat(all_sheets.values(), ignore_index=True)
                st.info(f"📋 File read successfully! Loaded {len(all_sheets)} sheets combined.")
            else:
                df = pd.read_csv(source_file)
                st.info("📋 CSV loaded successfully.")
            
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
                        "booking_office": str(row[c_bo]).strip() if c_bo in df.columns else "",
                        "status": "Pending"
                    })
                
                with st.spinner("⏳ Compiling manifest matrices and pushing pipelines to Supabase Node... Please wait."):
                    try:
                        response = supabase.table("patient_deliveries").upsert(staging_area, on_conflict="article_id").execute()
                        st.balloons()
                        st.success(f"🎉 **Operation Complete!** Successfully processed and synchronized **{len(staging_area)}** unique records into the cloud server database architectural layer.")
                    except Exception as ex:
                        st.error(f"❌ **Batch synchronization exception:** {ex}")
                        st.info("💡 **Supabase Setup Tip:** If you see an RLS policy error, please disable Row-Level Security (RLS) for the 'patient_deliveries' table in your Supabase Dashboard or use the 'service_role' secret key.")

    # ----------------------------------------------------
    # OPERATOR PROVISIONING HUB
    # ----------------------------------------------------
    elif st.session_state.current_navigation_tab == "👥 Operator Matrix & Security Audit Logs" and st.session_state.role == "admin":
        st.markdown("### 👥 Operational Account Provisioning Center")
        nf = st.text_input("Operator Full Name")
        nu = st.text_input("Operational Username")
        np = st.text_input("Assigned Initial Password", type="password")
        if st.button("Register Operator Account", use_container_width=True):
            if nf and nu and np:
                try:
                    supabase.table("app_users").insert({"username": nu.strip(), "password": np.strip(), "full_name": nf.strip(), "role": "staff"}).execute()
                    st.success("New active account mapped successfully.")
                except Exception as e: st.error(f"Mapping rejection: {e}")

    # ----------------------------------------------------
    # OUTBOUND CALLS & LIVE TRACKING DESK
    # ----------------------------------------------------
    elif st.session_state.current_navigation_tab == "📞 Outbound Communications Hub":
        st.markdown("### 📞 Outbound Communications Desk")
        
        query_date = st.date_input("Filter Manifest Records by Booking Date:", datetime.date.today())
        
        try: recs = supabase.table("patient_deliveries").select("*").eq("booking_date", str(query_date)).execute().data
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
                st.write(f"📦 **Consignment ID (Article):** `{target_profile['article_id']}`")
                st.write(f"🏠 **Address:** {target_profile['address']}")
                
                st.markdown("#### 🌐 Pakistan Post Live EMTTS Tracking")
                if st.button("🔍 Fetch Live Status from PakPost Server", use_container_width=True):
                    with st.spinner(f"Connecting to official PakPost network to trace {target_profile['article_id']}..."):
                        live_status, trace_detail = fetch_live_emtts_status(target_profile['article_id'])
                        
                        st.metric(label="Latest Detected Status", value=live_status)
                        st.text_area("Full EMTTS Tracking History Logs:", value=trace_detail, height=180)
                
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
                            st.success("Session logs pushed to database nodes successfully.")
                            time.sleep(0.5)
                            st.rerun()
                        except Exception as e: st.error(f"Commit tracking sync error: {e}")
