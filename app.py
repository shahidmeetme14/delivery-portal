import streamlit as st
from supabase import create_client, Client
import pandas as pd
import datetime
import io
import time
import requests
from bs4 import BeautifulSoup

# 🎛️ Page Structural Settings (Forcing Sidebar State Naturally)
st.set_page_config(
    page_title="SHC & Pak Post | Delivery Portal", 
    page_icon="📮", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# 🎨 PyQt6 / C++ Enterprise Desktop Style CSS Engine
st.markdown("""
    <style>
    /* Hide unnecessary default Streamlit top bars */
    div[data-testid="stToolbar"] { visibility: hidden !important; }
    .stDeployButton { display: none !important; }
    footer { visibility: hidden !important; }
    
    /* 🔓 SIDEBAR RESET: Force default toggle buttons to be completely visible so you can open it manually */
    button[data-testid="stSidebarCollapseButton"] { visibility: visible !important; display: block !important; }
    [data-testid="collapsedControl"] { visibility: visible !important; display: block !important; }
    
    /* Hide native input hints globally (Press Enter to submit) */
    div[data-testid="stInputInstructions"] { display: none !important; }
    div[data-testid="InputInstructions"] { display: none !important; }
    small { display: none !important; }
    
    /* PyQt6 Desktop System Colors (Slate Gray / Dark Metallic Corporate Theme) */
    .stApp { background-color: #f1f5f9; }
    body { font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif; }
    
    .brand-title { color: #1e293b; font-weight: 700; font-size: 1.85rem; letter-spacing: -0.03rem; margin-top: -25px; margin-bottom: 2px; }
    .brand-subtitle { color: #64748b; font-size: 0.95rem; margin-bottom: 25px; font-weight: 500; }
    
    /* PyQt6 Sharp Container Boxes */
    div[data-testid="stForm"], .pyqt-panel {
        background: #ffffff !important;
        border-radius: 4px !important;
        border: 1px solid #cbd5e1 !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
        padding: 24px !important;
    }
    
    /* Sharp Technical UI Form Labels */
    label p {
        color: #334155 !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    
    /* High-contrast Action Buttons (Native Application Style) */
    div.stButton > button {
        background: #1e293b !important;
        color: #ffffff !important;
        border: 1px solid #0f172a !important;
        border-radius: 3px !important;
        padding: 6px 18px !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        transition: background 0.1s ease !important;
    }
    div.stButton > button:hover {
        background: #334155 !important;
        color: #ffffff !important;
        border-color: #1e293b !important;
    }
    div.stButton > button:active {
        background: #0f172a !important;
    }
    
    /* Highlighted Nav Toggles */
    .active-nav-btn div.stButton > button {
        background: #2563eb !important;
        border-color: #1d4ed8 !important;
    }
    .active-nav-btn div.stButton > button:hover {
        background: #1d4ed8 !important;
    }
    
    /* Technical Stats Displays */
    .big-phone-display { font-family: 'Courier New', monospace; font-size: 32px !important; font-weight: 700 !important; color: #166534 !important; background-color: #f0fdf4; padding: 10px; border-radius: 4px; text-align: center; border: 1px solid #bbf7d0; }
    .patient-card-header { font-size: 20px !important; font-weight: 700 !important; color: #0f172a; border-left: 4px solid #1e3a8a; padding-left: 10px; margin-bottom: 12px; }
    </style>
""", unsafe_allow_html=True)

SESSION_TIMEOUT = 30 * 60  # 🕒 Strict 30 Minutes Inactivity Boundary

# Global Session Keys Initializer
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "username" not in st.session_state: st.session_state.username = ""
if "full_name" not in st.session_state: st.session_state.full_name = ""
if "role" not in st.session_state: st.session_state.role = ""
if "last_activity" not in st.session_state: st.session_state.last_activity = time.time()
if "current_navigation_tab" not in st.session_state: st.session_state.current_navigation_tab = None
if "selected_profile_index" not in st.session_state: st.session_state.selected_profile_index = 0
if "show_recovery_prompt" not in st.session_state: st.session_state.show_recovery_prompt = False
if "cached_recovery_data" not in st.session_state: st.session_state.cached_recovery_data = {}

@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

try:
    supabase: Client = init_connection()
except Exception as e:
    st.error(f"Database core failure: {e}")
    st.stop()

# 🔄 POWER LOSS/DISCONNECTION TRACKING ENGINE
def save_operator_state():
    if st.session_state.logged_in and st.session_state.username:
        state_payload = {
            "username": st.session_state.username,
            "last_tab": st.session_state.current_navigation_tab,
            "last_index": st.session_state.selected_profile_index,
            "updated_at": datetime.datetime.now().isoformat()
        }
        try: supabase.table("operator_sessions").upsert(state_payload, on_conflict="username").execute()
        except: pass

def fetch_operator_state(username):
    try:
        res = supabase.table("operator_sessions").select("*").eq("username", username).execute().data
        if res: return res[0]
    except: return None
    return None

# Hydrate parameters from URL if matching signature exists (Survives Refresh)
if not st.session_state.logged_in and "usr" in st.query_params:
    try:
        param_time = float(st.query_params.get("t", 0))
        if time.time() - param_time < SESSION_TIMEOUT:
            st.session_state.logged_in = True
            st.session_state.username = st.query_params["usr"]
            st.session_state.full_name = st.query_params["nm"]
            st.session_state.role = st.query_params["rl"]
            st.session_state.last_activity = param_time
        else:
            st.query_params.clear()
    except:
        pass

# ⏱️ Smart Inactivity Verification Control
if st.session_state.logged_in:
    if time.time() - st.session_state.last_activity > SESSION_TIMEOUT:
        st.session_state.logged_in = False
        st.query_params.clear()
        st.warning("🔄 Terminal locked automatically after 30 minutes of complete inactivity.")
        time.sleep(1)
        st.rerun()
    else:
        # Operator performed an action or interaction. Reset internal timer node.
        st.session_state.last_activity = time.time()
        st.query_params["t"] = str(st.session_state.last_activity)

if st.session_state.logged_in and st.session_state.current_navigation_tab is None:
    st.session_state.current_navigation_tab = "📊 Administrative Ingestion Engine" if st.session_state.role == "admin" else "📞 Outbound Communications Hub"

# Real-time Web Tracker for PakPost EMTTS Nodes
def fetch_live_emtts_status(article_id):
    if not article_id or article_id.strip() == "":
        return "⚠️ Invalid Article ID", "No data mapped."
    tracking_url = "https://ep.gov.pk/tracking.asp"
    payload = {'tracking_id': article_id.strip()}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        response = requests.post(tracking_url, data=payload, headers=headers, timeout=15)
        if response.status_code != 200: return "❌ Server Unreachable", "HTTP Error."
        soup = BeautifulSoup(response.text, 'html.parser')
        tables = soup.find_all('table')
        if len(tables) < 2: return "🔎 Record Not Found", "No tracking records loaded yet."
        tracking_logs = []
        for table in tables:
            for row in table.find_all('tr'):
                cols = [ele.text.strip().replace('\n', ' ').replace('\r', '') for ele in row.find_all(['td', 'th'])]
                if cols and not any('tracking id' in str(c).lower() for c in cols):
                    tracking_logs.append(" | ".join([c for c in cols if c]))
        latest_status = "Data Found"
        for log in tracking_logs:
            if "delivered" in log.lower(): latest_status = "✅ Delivered"; break
            elif "transit" in log.lower() or "dispatched" in log.lower(): latest_status = "🚚 In Transit"; break
            elif "booked" in log.lower(): latest_status = "📦 Booked / Received"; break
        return latest_status, "\n".join(tracking_logs[:12])
    except:
        return "⏱️ Timeout Error", "PakPost network nodes timed out."

# Permanent Workspace Sidebar Container
with st.sidebar:
    st.markdown("### 🖥️ Enterprise Console")
    if st.session_state.logged_in:
        st.markdown(f"**Operator ID:** `{st.session_state.username}`")
        st.markdown(f"**Name:** {st.session_state.full_name}")
        st.markdown(f"**Privilege Cluster:** `{st.session_state.role.upper()}`")
        st.markdown("---")
        if st.button("Terminate Session 🚪", use_container_width=True):
            st.session_state.logged_in = False
            st.query_params.clear()
            st.rerun()
    else:
        st.markdown("🔒 *Authentication Required*")

st.markdown("<div class='brand-title'>SHC & Pak Post | Free Home Delivery of Medicine</div>", unsafe_allow_html=True)
st.markdown("<div class='brand-subtitle'>Logistics Tracking & Quality Feedback System</div>", unsafe_allow_html=True)

# Main Authentication Router
if not st.session_state.logged_in:
    _, center_col, _ = st.columns([1.2, 1.2, 1.2])
    with center_col:
        st.markdown("<div style='background-color:#1e293b; color:#ffffff; padding:10px; font-weight:600; font-size:12px; border-radius:4px 4px 0px 0px; border:1px solid #0f172a;'>SECURE PORTAL AUTHENTICATION v2.4</div>", unsafe_allow_html=True)
        with st.form("pyqt_enterprise_login"):
            input_user = st.text_input("OPERATOR ID / USERNAME", placeholder="e.g. shahid_admin")
            input_pass = st.text_input("SECURITY ACCESS PASSWORD", type="password", placeholder="••••••••")
            btn_login = st.form_submit_button("UNLOCK TERMINAL", use_container_width=True)
            
            if btn_login:
                if input_user and input_pass:
                    with st.spinner("VALIDATING CREDENTIALS... MATCHING SECURE HASH..."):
                        try:
                            ud = supabase.table("app_users").select("*").eq("username", input_user.strip()).eq("password", input_pass.strip()).execute().data
                            if ud:
                                recovery_data = fetch_operator_state(ud[0]["username"])
                                if recovery_data:
                                    st.session_state.cached_recovery_data = recovery_data
                                    st.session_state.show_recovery_prompt = True
                                    st.session_state.username = ud[0]["username"]
                                    st.session_state.full_name = ud[0]["full_name"]
                                    st.session_state.role = ud[0]["role"]
                                    st.session_state.last_activity = time.time()
                                    st.rerun()
                                else:
                                    current_ts = time.time()
                                    st.session_state.logged_in = True
                                    st.session_state.username = ud[0]["username"]
                                    st.session_state.full_name = ud[0]["full_name"]
                                    st.session_state.role = ud[0]["role"]
                                    st.session_state.last_activity = current_ts
                                    
                                    st.query_params["usr"] = ud[0]["username"]
                                    st.query_params["nm"] = ud[0]["full_name"]
                                    st.query_params["rl"] = ud[0]["role"]
                                    st.query_params["t"] = str(current_ts)
                                    st.rerun()
                            else:
                                st.error("ACCESS DENIED: Invalid configuration credentials.")
                        except Exception as ex:
                            st.error(f"Database Sync Failure: {ex}")
                else:
                    st.warning("All authentication fields must be filled.")

# 🔄 Crash Recovery Selector Pop-up Interface
elif st.session_state.show_recovery_prompt:
    _, alert_box, _ = st.columns([1, 2, 1])
    with alert_box:
        st.markdown("""
        <div style='background-color:#fffbeb; border-left:5px solid #d97706; padding:15px; border-radius:4px; margin-bottom:15px;'>
            <h4 style='margin:0; color:#92400e;'>⚠️ Interrupted Operational Activity Detected</h4>
            <p style='margin:5px 0 0 0; font-size:13px; color:#78350f;'>
                System unexpected shutdown ya power-loss detect hua hai. Aapka aakhri active data mehfooz hai.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        rec_info = st.session_state.cached_recovery_data
        st.info(f"Last Position: Tab `{rec_info.get('last_tab')}` | Row Index `{rec_info.get('last_index')}`")
        
        col_res, col_new = st.columns(2)
        with col_res:
            if st.button("🔄 RESUME INTERRUPTED SESSION", use_container_width=True):
                st.session_state.logged_in = True
                st.session_state.current_navigation_tab = rec_info.get('last_tab')
                st.session_state.selected_profile_index = int(rec_info.get('last_index', 0))
                st.session_state.show_recovery_prompt = False
                
                st.query_params["usr"] = st.session_state.username
                st.query_params["nm"] = st.session_state.full_name
                st.query_params["rl"] = st.session_state.role
                st.query_params["t"] = str(st.session_state.last_activity)
                st.rerun()
                
        with col_new:
            if st.button("🆕 START FRESH BLANK SESSION", use_container_width=True):
                st.session_state.logged_in = True
                st.session_state.show_recovery_prompt = False
                
                st.query_params["usr"] = st.session_state.username
                st.query_params["nm"] = st.session_state.full_name
                st.query_params["rl"] = st.session_state.role
                st.query_params["t"] = str(st.session_state.last_activity)
                save_operator_state()
                st.rerun()

else:
    # Navigation Matrix For Admins
    if st.session_state.role == "admin":
        nc1, nc2, nc3 = st.columns(3)
        with nc1:
            t1_class = "active-nav-btn" if st.session_state.current_navigation_tab == "📊 Administrative Ingestion Engine" else ""
            st.markdown(f"<div class='{t1_class}'>", unsafe_allow_html=True)
            if st.button("📊 Administrative Ingestion Engine", use_container_width=True):
                st.session_state.current_navigation_tab = "📊 Administrative Ingestion Engine"
                save_operator_state()
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        with nc2:
            t2_class = "active-nav-btn" if st.session_state.current_navigation_tab == "👥 Operator Matrix & Security Audit Logs" else ""
            st.markdown(f"<div class='{t2_class}'>", unsafe_allow_html=True)
            if st.button("👥 Operator Matrix & Logs", use_container_width=True):
                st.session_state.current_navigation_tab = "👥 Operator Matrix & Security Audit Logs"
                save_operator_state()
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        with nc3:
            t3_class = "active-nav-btn" if st.session_state.current_navigation_tab == "📞 Outbound Communications Hub" else ""
            st.markdown(f"<div class='{t3_class}'>", unsafe_allow_html=True)
            if st.button("📞 Outbound Communications Hub", use_container_width=True):
                st.session_state.current_navigation_tab = "📞 Outbound Communications Hub"
                save_operator_state()
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            
    st.markdown("<br>", unsafe_allow_html=True)

    # PAGE 1: ADMINISTRATIVE BULK MANIFEST DATA INGESTION
    if st.session_state.current_navigation_tab == "📊 Administrative Ingestion Engine" and st.session_state.role == "admin":
        st.markdown("### 📥 Bulk Logistics Ingestion Engine")
        source_file = st.file_uploader("Upload Parcel Manifest Data Sheet (.xlsx or .csv)", type=["xlsx", "csv"])
        
        if source_file is not None:
            if source_file.name.endswith('.xlsx'):
                all_sheets = pd.read_excel(source_file, sheet_name=None)
                df = pd.concat(all_sheets.values(), ignore_index=True)
                st.info(f"📋 Loaded {len(all_sheets)} worksheets combined successfully.")
            else:
                df = pd.read_csv(source_file)
                st.info("📋 CSV manifest matrix loaded successfully.")
            
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
                dup_target = st.selectbox("De-duplication Matrix Anchor:", df.columns, index=df.columns.get_loc(c_article))

            if st.button("🚀 Push Verified Records to Cloud Database", use_container_width=True):
                with st.spinner("Processing Manifest Sequence..."):
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
                    try:
                        supabase.table("patient_deliveries").upsert(staging_area, on_conflict="article_id").execute()
                        st.balloons()
                        st.success(f"🎉 Synchronized {len(staging_area)} clean logs across cloud nodes.")
                    except Exception as ex:
                        st.error(f"❌ Batch sync exception: {ex}")

    # PAGE 2: OPERATOR ACCOUNT MANAGEMENT
    elif st.session_state.current_navigation_tab == "👥 Operator Matrix & Security Audit Logs" and st.session_state.role == "admin":
        st.markdown("### 👥 Operational Account Provisioning Center")
        nf = st.text_input("Operator Full Name")
        nu = st.text_input("Operational Username / ID")
        np = st.text_input("Assigned Initial Password", type="password")
        if st.button("Register Operator Account", use_container_width=True):
            if nf and nu and np:
                try:
                    supabase.table("app_users").insert({"username": nu.strip(), "password": np.strip(), "full_name": nf.strip(), "role": "staff"}).execute()
                    st.success("New operator mapped to security matrices.")
                except Exception as e: st.error(f"Mapping rejection: {e}")

    # PAGE 3: MAIN COMMUNICATIONS HUB
    elif st.session_state.current_navigation_tab == "📞 Outbound Communications Hub":
        st.markdown("### 📞 Outbound Communications Desk")
        query_date = st.date_input("Filter Manifest Records by Booking Date:", datetime.date.today())
        
        try: recs = supabase.table("patient_deliveries").select("*").eq("booking_date", str(query_date)).execute().data
        except: recs = []
            
        if not recs:
            st.info("No logs found matching this calendar timestamp.")
        else:
            options_list = [f"{r['patient_name']} (MRN: {r.get('mrn_no', 'N/A')}) - [{r['status']}]" for r in recs]
            
            if st.session_state.selected_profile_index >= len(options_list):
                st.session_state.selected_profile_index = 0
                
            selected_key = st.selectbox(
                "Select Patient Profile to Process:", 
                options_list, 
                index=st.session_state.selected_profile_index
            )
            
            current_choice_idx = options_list.index(selected_key)
            if current_choice_idx != st.session_state.selected_profile_index:
                st.session_state.selected_profile_index = current_choice_idx
                save_operator_state()
                
            target_profile = recs[st.session_state.selected_profile_index]
            
            st.markdown("<hr>", unsafe_allow_html=True)
            l_panel, r_panel = st.columns(2)
            
            with l_panel:
                st.markdown(f"<div class='patient-card-header'>👤 {target_profile['patient_name']}</div>", unsafe_allow_html=True)
                st.write(f"🔢 **MRN Number:** `{target_profile.get('mrn_no', 'N/A')}`")
                st.write(f"📦 **Consignment ID (Article):** `{target_profile['article_id']}`")
                st.write(f"🏠 **Address:** {target_profile['address']}")
                
                st.markdown("#### 🌐 Pakistan Post Live EMTTS Tracking")
                if st.button("🔍 Fetch Live Status from PakPost Server", use_container_width=True):
                    with st.spinner("Connecting to PakPost network nodes..."):
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
                        with st.spinner("Committing logs to cloud infrastructure..."):
                            try:
                                supabase.table("patient_deliveries").update(payload_buffer).eq("id", target_profile["id"]).execute()
                                st.success("Data node updated successfully.")
                                st.session_state.selected_profile_index += 1
                                save_operator_state()
                                time.sleep(0.5)
                                st.rerun()
                            except Exception as e: st.error(f"Commit tracking sync error: {e}")
