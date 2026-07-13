import streamlit as st
from supabase import create_client, Client
import pandas as pd
import datetime
import io
import time
import urllib.request
from bs4 import BeautifulSoup

# 🎛️ Page Structural Settings (No "Presented by SHAHID" as requested)
st.set_page_config(
    page_title="EMTTS Delivery Portal | Pakistan Post", 
    page_icon="📮", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# 🔄 URL HYDRATION ENGINE
SESSION_TIMEOUT = 30 * 60  

if "logged_in" not in st.session_state: 
    st.session_state.logged_in = False

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

# Initialize Global App States
if "username" not in st.session_state: st.session_state.username = ""
if "full_name" not in st.session_state: st.session_state.full_name = ""
if "role" not in st.session_state: st.session_state.role = ""
if "last_activity" not in st.session_state: st.session_state.last_activity = time.time()
if "current_navigation_tab" not in st.session_state: st.session_state.current_navigation_tab = None
if "selected_profile_index" not in st.session_state: st.session_state.selected_profile_index = 0
if "show_recovery_prompt" not in st.session_state: st.session_state.show_recovery_prompt = False
if "cached_recovery_data" not in st.session_state: st.session_state.cached_recovery_data = {}

# Initialize Column Mappings Memory
mapping_keys = ["map_article", "map_name", "map_city", "map_phone", "map_date", "map_mrn", "map_address", "map_bo", "map_dup"]
for key in mapping_keys:
    if key not in st.session_state:
        st.session_state[key] = None

# 🎨 EP.GOV.PK Premium Red & Gold Theme + Frosted Glass Sidebar Styling
sidebar_css_rule = ""
if not st.session_state.logged_in:
    sidebar_css_rule = """
    [data-testid="stSidebar"] { display: none !important; visibility: hidden !important; }
    [data-testid="collapsedControl"] { display: none !important; visibility: hidden !important; }
    """
else:
    sidebar_css_rule = """
    button[data-testid="stSidebarCollapseButton"] { display: none !important; visibility: hidden !important; }
    [data-testid="collapsedControl"] { display: none !important; visibility: hidden !important; }
    section[data-testid="stSidebar"] {
        display: block !important;
        visibility: visible !important;
        transform: translateX(0%) !important;
        min-width: 270px !important;
        max-width: 270px !important;
        background: rgba(25, 25, 25, 0.85) !important;
        backdrop-filter: blur(25px) saturate(180%) !important;
        -webkit-backdrop-filter: blur(25px) saturate(180%) !important;
        border-right: 2px solid #D4AF37 !important;
        box-shadow: 10px 0px 40px rgba(0, 0, 0, 0.5) !important;
    }
    """

st.markdown(f"""
    <style>
    /* Global Styling & Red-Gold Palette */
    .block-container {{ padding-top: 1.0rem !important; padding-bottom: 1.0rem !important; }}
    div[data-testid="stToolbar"] {{ visibility: hidden !important; display: none !important; }}
    .stDeployButton {{ display: none !important; }}
    footer {{ visibility: hidden !important; display: none !important; }}
    [data-testid="stViewerBadge"] {{ display: none !important; }}
    
    {sidebar_css_rule}
    
    /* Global Input Helper Text ("Press Enter to submit form" removal) */
    div[data-testid="stInputHelperText"] {{
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
    }}
    
    /* App Canvas styling */
    .stApp {{ background-color: #faf8f5; }}
    
    .brand-title {{ color: #A30000; font-weight: 800; font-size: 1.8rem; margin-bottom: 2px; line-height: 1.2; letter-spacing: 0.5px; }}
    .brand-subtitle {{ color: #5a5a5a; font-size: 0.9rem; margin-bottom: 15px; font-weight: 600; border-left: 3px solid #D4AF37; padding-left: 8px; }}
    
    /* Frosted Sidebar Custom Text */
    .sb-section-title {{
        color: #aeaeae !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        letter-spacing: 1.5px;
        margin-bottom: 4px;
        text-transform: uppercase;
    }}
    .sb-logged-name {{
        color: #D4AF37 !important;
        font-size: 20px !important;
        font-weight: 800 !important;
        text-shadow: 0px 2px 4px rgba(0,0,0,0.6);
        letter-spacing: 0.5px;
    }}
    .sb-badge-privilege {{
        color: #FFFFFF !important;
        font-size: 11px !important;
        font-weight: bold !important;
        background: rgba(163, 0, 0, 0.45);
        padding: 3px 10px;
        border-radius: 4px;
        border: 1px solid rgba(163, 0, 0, 0.6);
        display: inline-block;
        margin-top: 5px;
        letter-spacing: 1px;
    }}
    
    /* Login panel box styling */
    div[data-testid="stForm"] {{
        background: #ffffff !important;
        border-radius: 8px !important;
        border: 1px solid #e0d5c1 !important;
        box-shadow: 0 10px 25px rgba(163, 0, 0, 0.05) !important;
        padding: 25px !important;
    }}
    
    /* Red-Gold Premium Buttons with Animations */
    div.stButton > button, div.stDownloadButton > button {{
        background: linear-gradient(180deg, #A30000 0%, #7A0000 100%) !important;
        color: #ffffff !important;
        border: 1px solid #7A0000 !important;
        border-bottom: 3.5px solid #5C0000 !important;
        border-radius: 4px !important;
        font-weight: 700;
        font-size: 14px !important;
        box-shadow: 0px 4px 10px rgba(163, 0, 0, 0.15) !important;
        transition: all 0.15s ease-in-out !important;
    }}
    div.stButton > button:hover, div.stDownloadButton > button:hover {{
        background: linear-gradient(180deg, #B50000 0%, #8A0000 100%) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0px 6px 14px rgba(163, 0, 0, 0.25) !important;
    }}
    div.stButton > button:active, div.stDownloadButton > button:active {{
        transform: translateY(1.5px) !important;
        border-bottom: 1px solid #5C0000 !important;
        box-shadow: 0px 2px 4px rgba(0,0,0,0.2) !important;
    }}
    
    /* Active tab buttons styling */
    .active-nav-btn div.stButton > button {{
        background: linear-gradient(180deg, #D4AF37 0%, #AA8725 100%) !important;
        color: #000000 !important;
        border: 1px solid #AA8725 !important;
        border-bottom: 2px solid #7D6114 !important;
    }}
    
    /* Premium Dropdown & Selectbox Look Restored */
    div[data-testid="stSelectbox"] > div[data-baseweb="select"], 
    div[data-testid="stDateInput"] > div {{
        background: #ffffff !important;
        border: 1px solid #d4cfc5 !important;
        border-radius: 4px !important;
        box-shadow: none !important;
    }}
    
    /* Dynamic Contact Number Display */
    .big-phone-display {{ 
        font-family: 'Segoe UI', sans-serif; 
        font-size: 22px !important; 
        font-weight: 700 !important; 
        color: #ffffff !important; 
        background: linear-gradient(180deg, #A30000 0%, #7A0000 100%) !important; 
        padding: 8px 15px; 
        border-radius: 4px; 
        text-align: center; 
        border: 1px solid #7A0000; 
        border-bottom: 3.5px solid #5C0000;
        box-shadow: 0px 4px 12px rgba(163, 0, 0, 0.2);
        letter-spacing: 1.5px;
        margin: 5px 0;
    }}
    
    .no-phone-display {{
        font-family: 'Segoe UI', sans-serif; 
        font-size: 15px !important; 
        font-weight: 700 !important; 
        color: #ffffff !important; 
        background: #555555 !important; 
        padding: 8px 12px; 
        border-radius: 4px; 
        text-align: center; 
        margin: 5px 0;
    }}
    
    .patient-card-header {{ font-size: 18px !important; font-weight: 700 !important; color: #A30000; border-left: 4px solid #D4AF37; padding-left: 8px; margin-bottom: 10px; }}
    </style>
""", unsafe_allow_html=True)

@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

try:
    supabase: Client = init_connection()
except Exception as e:
    st.error(f"Database core failure: {e}")
    st.stop()

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

def calculate_mapped_index(df_cols, session_key, alternative_match_string):
    saved_val = st.session_state.get(session_key)
    if saved_val in df_cols:
        return list(df_cols).index(saved_val)
    for idx, name in enumerate(df_cols):
        if alternative_match_string.lower() in str(name).lower():
            return idx
    return 0

if st.session_state.logged_in:
    if time.time() - st.session_state.last_activity > SESSION_TIMEOUT:
        st.session_state.logged_in = False
        st.query_params.clear()
        st.warning("🔄 Terminal locked automatically after 30 minutes of complete inactivity.")
        time.sleep(1)
        st.rerun()
    else:
        st.session_state.last_activity = time.time()
        st.query_params["t"] = str(st.session_state.last_activity)

if st.session_state.logged_in and st.session_state.current_navigation_tab is None:
    st.session_state.current_navigation_tab = "📊 Administrative Ingestion Engine" if st.session_state.role == "admin" else "📞 Outbound Communications Hub"

def map_status(raw_status):
    s = raw_status.lower().strip()
    if "undelivered" in s: return "Undelivered"
    if "sent out for delivery" in s: return "Sent out for delivery"
    if "return" in s or "rts" in s: return "RTS"
    if "delivered" in s: return "Delivered"
    if s.startswith("dispatch") or "dispatch" in s: return "Dispatched"
    if "deposit" in s: return "Deposit"
    return raw_status.strip()

def fetch_live_emtts_status(article_id):
    if not article_id or article_id.strip() == "":
        return None, "⚠️ Invalid Article ID"
    url = f"https://ep.gov.pk/emtts/EPTrack_Live.aspx?ArticleIDz={article_id.strip()}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=20.0) as response:
            html = response.read().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(html, 'html.parser')
            mrn = soup.find(id="lblMRNNumber").text.strip() if soup.find(id="lblMRNNumber") else ""
            b_office = soup.find(id="LblBookingOffice").text.strip() if soup.find(id="LblBookingOffice") else ""
            d_office = soup.find(id="LblDeliveryOffice").text.strip() if soup.find(id="LblDeliveryOffice") else ""
            track_div = soup.find(id="TrackDetailDiv")
            history = []
            if track_div:
                rows = track_div.find_all("tr")
                current_date = ""
                for row in rows:
                    tds = row.find_all("td")
                    if len(tds) == 1 and "20" in tds[0].text:
                        current_date = tds[0].text.strip()
                    if len(tds) >= 4:
                        history.append({
                            "datetime": f"{current_date} {tds[1].text.strip()}",
                            "office": tds[2].text.strip(),
                            "status": tds[3].text.strip()
                        })
            if not history: return None, "🔎 No tracking logs found for this Article ID."
            return {"mrn": mrn, "booking_office": b_office, "delivery_office": d_office, "history": history}, None
    except Exception as e:
        return None, f"Server Timeout / Failed: {str(e)}"

# Glassmorphism Sidebar Render (With Gold Username & Proper Styling)
if st.session_state.logged_in:
    with st.sidebar:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<div class='sb-section-title'>LOGGED IN AS:</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='sb-logged-name'>{st.session_state.full_name}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='sb-badge-privilege'>{st.session_state.role.upper()} PRIVILEGES</div>", unsafe_allow_html=True)
        st.markdown("<br><hr style='border-top:1px solid rgba(255,255,255,0.15);'><br>", unsafe_allow_html=True)
        if st.button("🚪 Terminate Session", use_container_width=True):
            st.session_state.logged_in = False
            st.query_params.clear()
            st.rerun()

st.markdown("<div class='brand-title'>📮 EMTTS & Pak Post | Delivery System</div>", unsafe_allow_html=True)
st.markdown("<div class='brand-subtitle'>Secure Audit & Communication Engine</div>", unsafe_allow_html=True)

# LOGIN PAGE
if not st.session_state.logged_in:
    _, center_col, _ = st.columns([0.8, 1.4, 0.8])
    with center_col:
        st.markdown("<div style='background-color:#A30000; color:#ffffff; padding:12px; font-weight:700; font-size:14px; border-radius:6px 6px 0px 0px; border:1px solid #7A0000; text-align:center; letter-spacing: 0.5px;'>SECURE PORTAL AUTHENTICATION</div>", unsafe_allow_html=True)
        with st.form("pyqt_enterprise_login"):
            input_user = st.text_input("OPERATOR ID / USERNAME", placeholder="Enter Username")
            input_pass = st.text_input("SECURITY ACCESS PASSWORD", type="password", placeholder="Enter Secure Key")
            btn_login = st.form_submit_button("LOGIN TO PORTAL", use_container_width=True)
            if btn_login:
                if input_user and input_pass:
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
                                st.session_state.logged_in = True
                                st.session_state.username = ud[0]["username"]
                                st.session_state.full_name = ud[0]["full_name"]
                                st.session_state.role = ud[0]["role"]
                                st.rerun()
                        else: st.error("ACCESS DENIED: Invalid credentials.")
                    except Exception as ex: st.error(f"Database Sync Failure: {ex}")

elif st.session_state.show_recovery_prompt:
    _, alert_box, _ = st.columns([1, 2, 1])
    with alert_box:
        st.info("System unexpected shutdown detect hua hai. Last active session data mehfooz hai.")
        col_res, col_new = st.columns(2)
        with col_res:
            if st.button("🔄 RESUME INTERRUPTED SESSION", use_container_width=True):
                st.session_state.logged_in = True
                st.session_state.current_navigation_tab = st.session_state.cached_recovery_data.get('last_tab')
                st.session_state.selected_profile_index = int(st.session_state.cached_recovery_data.get('last_index', 0))
                st.session_state.show_recovery_prompt = False
                st.rerun()
        with col_new:
            if st.button("🆕 START FRESH BLANK SESSION", use_container_width=True):
                st.session_state.logged_in = True
                st.session_state.show_recovery_prompt = False
                save_operator_state()
                st.rerun()

else:
    cols_count = 4 if st.session_state.role == "admin" else 2
    nc = st.columns(cols_count)
    
    if st.session_state.role == "admin":
        with nc[0]:
            t1 = "active-nav-btn" if st.session_state.current_navigation_tab == "📊 Administrative Ingestion Engine" else ""
            st.markdown(f"<div class='{t1}'>", unsafe_allow_html=True)
            if st.button("📊 Administrative Ingestion Engine", use_container_width=True): 
                st.session_state.current_navigation_tab = "📊 Administrative Ingestion Engine"; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        with nc[1]:
            t2 = "active-nav-btn" if st.session_state.current_navigation_tab == "👥 Operator Matrix & Security Audit Logs" else ""
            st.markdown(f"<div class='{t2}'>", unsafe_allow_html=True)
            if st.button("👥 Operator Matrix & Security Audit Logs", use_container_width=True): 
                st.session_state.current_navigation_tab = "👥 Operator Matrix & Security Audit Logs"; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        with nc[2]:
            t3 = "active-nav-btn" if st.session_state.current_navigation_tab == "📞 Outbound Communications Hub" else ""
            st.markdown(f"<div class='{t3}'>", unsafe_allow_html=True)
            if st.button("📞 Outbound Communications Hub", use_container_width=True): 
                st.session_state.current_navigation_tab = "📞 Outbound Communications Hub"; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        with nc[3]:
            t4 = "active-nav-btn" if st.session_state.current_navigation_tab == "📥 Secure Reports Export Center" else ""
            st.markdown(f"<div class='{t4}'>", unsafe_allow_html=True)
            if st.button("📥 Secure Reports Export Center", use_container_width=True): 
                st.session_state.current_navigation_tab = "📥 Secure Reports Export Center"; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        with nc[0]:
            t1 = "active-nav-btn" if st.session_state.current_navigation_tab == "📞 Outbound Communications Hub" else ""
            st.markdown(f"<div class='{t1}'>", unsafe_allow_html=True)
            if st.button("📞 Outbound Communications Hub", use_container_width=True): 
                st.session_state.current_navigation_tab = "📞 Outbound Communications Hub"; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        with nc[1]:
            t2 = "active-nav-btn" if st.session_state.current_navigation_tab == "📥 Secure Reports Export Center" else ""
            st.markdown(f"<div class='{t2}'>", unsafe_allow_html=True)
            if st.button("📥 Secure Reports Export Center", use_container_width=True): 
                st.session_state.current_navigation_tab = "📥 Secure Reports Export Center"; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # PAGE 1: HYBRID INGESTION
    if st.session_state.current_navigation_tab == "📊 Administrative Ingestion Engine" and st.session_state.role == "admin":
        st.markdown("### 🚨 Critical Security Red-Flag Alerts")
        try:
            flagged_recs = supabase.table("patient_deliveries").select("*").eq("extra_money_charged", "Yes").execute().data
            if flagged_recs:
                for record in flagged_recs:
                    col_alert, col_action = st.columns([4, 1])
                    with col_alert:
                        st.error(f"⚠️ **Extra Money Alert:** Postman demanded cash from **{record['patient_name']}** | Article: `{record['article_id']}` | Op Stamp: {record.get('operator_stamp')}")
                    with col_action:
                        # Action Button to Resolve Directly
                        if st.button("Resolve Alert ✅", key=f"res_{record['id']}", use_container_width=True):
                            supabase.table("patient_deliveries").update({"extra_money_charged": "No"}).eq("id", record["id"]).execute()
                            st.success("Alert resolved successfully!")
                            time.sleep(0.5)
                            st.rerun()
            else:
                st.success("✅ No unauthorized monetary flags detected in current database pipeline.")
        except:
            pass
            
        st.markdown("---")
        st.markdown("### 📥 Bulk Logistics Ingestion Engine (Free Storage Mode)")
        
        target_upload_date = st.date_input("Assign Target Booking Date for Sheet:", datetime.date.today())
        source_file = st.file_uploader("Upload Parcel Manifest Sheet", type=["xlsx", "csv"])
        
        if source_file is not None:
            file_key = f"cached_df_{source_file.name}_{source_file.size}"
            if file_key not in st.session_state:
                df = pd.read_excel(source_file) if source_file.name.endswith('.xlsx') else pd.read_csv(source_file)
                st.session_state[file_key] = df
            else: df = st.session_state[file_key]
            
            mc1, mc2, mc3 = st.columns(3)
            with mc1:
                c_article = st.selectbox("Article ID Column:", df.columns, index=calculate_mapped_index(df.columns, "map_article", "Article ID"))
                c_name = st.selectbox("Patient Name Column:", df.columns, index=calculate_mapped_index(df.columns, "map_name", "Name"))
            with mc2:
                c_phone = st.selectbox("Contact Number Column:", df.columns, index=calculate_mapped_index(df.columns, "map_phone", "MobileNo"))
                c_date = st.selectbox("Booking Date Column:", df.columns, index=calculate_mapped_index(df.columns, "map_date", "Booking Date"))
            with mc3:
                c_mrn = st.selectbox("MRN No. Column:", df.columns, index=calculate_mapped_index(df.columns, "map_mrn", "MRN No"))
                c_address = st.selectbox("Address Column:", df.columns, index=calculate_mapped_index(df.columns, "map_address", "Address"))
                c_city = st.selectbox("City Column:", df.columns, index=calculate_mapped_index(df.columns, "map_city", "City"))
                c_bo = st.selectbox("Booking Office Column:", df.columns, index=calculate_mapped_index(df.columns, "map_bo", "Booking Office"))

            if st.button("🚀 Push Sheet to Supabase Free Cloud Storage", use_container_width=True):
                staging_area = []
                for _, row in df.iterrows():
                    staging_area.append({
                        "article_id": str(row[c_article]).strip(),
                        "patient_name": str(row[c_name]).strip(),
                        "phone_number": str(row[c_phone]).strip(),
                        "booking_date": str(row[c_date])[:10],
                        "address": str(row[c_address]).strip(),
                        "patient_city": str(row[c_city]).strip(),
                        "mrn_no": str(row[c_mrn]).strip(),
                        "booking_office": str(row[c_bo]).strip() if c_bo in df.columns else "Lahore GPO",
                        "status": "Pending"
                    })
                
                clean_df = pd.DataFrame(staging_area)
                csv_buffer = io.BytesIO()
                clean_df.to_csv(csv_buffer, index=False)
                csv_bytes = csv_buffer.getvalue()
                
                filename = f"manifest_{str(target_upload_date)}.csv"
                try:
                    try: supabase.storage.from_("manifests").remove([filename])
                    except: pass
                    
                    supabase.storage.from_("manifests").upload(
                        path=filename,
                        file=csv_bytes,
                        file_options={"content-type": "text/csv"}
                    )
                    st.success(f"🎉 Manifest backup file saved successfully as '{filename}'!")
                except Exception as ex: 
                    st.error(f"Cloud Bucket Storage Connection Error: {ex}. Please check that bucket 'manifests' is created in Supabase.")

    # PAGE 2: OPERATOR MATRIX
    elif st.session_state.current_navigation_tab == "👥 Operator Matrix & Security Audit Logs" and st.session_state.role == "admin":
        st.markdown("### 👥 Operational Account Provisioning")
        nf = st.text_input("Operator Full Name")
        nu = st.text_input("Operational Username / ID")
        np = st.text_input("Assigned Initial Password", type="password")
        if st.button("Register Operator Account", use_container_width=True):
            if nf and nu and np:
                try:
                    supabase.table("app_users").insert({"username": nu.strip(), "password": np.strip(), "full_name": nf.strip(), "role": "staff"}).execute()
                    st.success("Operator registered successfully!")
                except Exception as e: st.error(f"Error: {e}")

    # PAGE 3: OUTBOUND COMMUNICATIONS HUB (With Animated Loader & "No Data Found" Check)
    elif st.session_state.current_navigation_tab == "📞 Outbound Communications Hub":
        
        sel_col1, sel_col2, sel_col3 = st.columns([1, 1.2, 1.8])
        
        with sel_col1:
            query_date = st.date_input("Select Booking Date:", datetime.date.today())
        
        raw_date_recs = []
        is_loaded = False

        # ⏳ Animated Loading Spinner during data fetching process
        with st.spinner("⏳ Connecting to system and processing data nodes..."):
            # Attempt 1: Fetch from Cloud Storage Bucket File
            filename = f"manifest_{str(query_date)}.csv"
            try:
                storage_file_bytes = supabase.storage.from_("manifests").download(filename)
                if storage_file_bytes:
                    raw_date_recs = pd.read_csv(io.BytesIO(storage_file_bytes)).to_dict(orient="records")
                    is_loaded = True
            except:
                raw_date_recs = []
                
            # Attempt 2 (Fallback): Query Database Table Directly (In case file isn't in Storage yet)
            if not is_loaded:
                try:
                    db_recs = supabase.table("patient_deliveries").select("*").eq("booking_date", str(query_date)).execute().data
                    if db_recs:
                        raw_date_recs = db_recs
                        is_loaded = True
                except:
                    pass

        # ❌ If absolutely no records are found after processing
        if not is_loaded or not raw_date_recs: 
            st.error(f"❌ No data found against this date ({query_date}). Please upload a sheet first.")
        else:
            # Check DB for updates to overlay
            try:
                db_recs = supabase.table("patient_deliveries").select("*").eq("booking_date", str(query_date)).execute().data
                db_map = {r['article_id']: r for r in db_recs} if db_recs else {}
            except:
                db_map = {}

            # Overlay real-time statuses
            for record in raw_date_recs:
                art_id = str(record['article_id']).strip()
                if art_id in db_map:
                    record['id'] = db_map[art_id]['id']
                    record['status'] = db_map[art_id]['status']
                    record['extra_money_charged'] = db_map[art_id].get('extra_money_charged', 'No')
                    record['operator_stamp'] = db_map[art_id].get('operator_stamp', '')
                else:
                    record['id'] = None # Flag for new insertion

            unique_offices = sorted(list(set([str(r.get('booking_office', 'Lahore GPO')).strip() for r in raw_date_recs])))
            unique_offices.insert(0, "All Offices")
            
            with sel_col2: 
                selected_office = st.selectbox("Booking Office Node:", unique_offices)
                
            filtered_by_office = raw_date_recs if selected_office == "All Offices" else [r for r in raw_date_recs if str(r.get('booking_office')).strip() == selected_office]
            
            with sel_col3:
                search_term = st.text_input("Smart Filter (Name / Article ID / MRN):").strip().lower()
                
            if search_term:
                final_recs = [r for r in filtered_by_office if search_term in str(r.get('patient_name','')).lower() or search_term in str(r.get('article_id','')).lower() or search_term in str(r.get('mrn_no','')).lower()]
            else: 
                final_recs = filtered_by_office

            if not final_recs: 
                st.warning("No records matched the filter criteria.")
            else:
                options_list = [f"{r['patient_name']} (MRN: {r.get('mrn_no', 'N/A')}) - [{r['status']}]" for r in final_recs]
                if st.session_state.selected_profile_index >= len(options_list): st.session_state.selected_profile_index = 0
                    
                st.selectbox("Select Patient Profile to Process:", options_list, index=st.session_state.selected_profile_index, key="outbound_profile_select")
                target_profile = final_recs[st.session_state.selected_profile_index]
                
                st.markdown("<hr>", unsafe_allow_html=True)
                l_panel, r_panel = st.columns(2)
                
                with l_panel:
                    st.markdown(f"<div class='patient-card-header'>👤 {target_profile['patient_name']}</div>", unsafe_allow_html=True)
                    
                    st.markdown(f"""
                        <div style="background:#ffffff; padding:15px; border-radius:6px; border:1px solid #e2d8c5; margin-bottom:15px;">
                            <div style="margin-bottom:8px;">🔢 <b>MRN Number:</b> <span style="font-weight:700; color:#A30000;">{target_profile.get('mrn_no', 'N/A')}</span></div>
                            <div style="margin-bottom:8px;">📦 <b>Consignment ID:</b> <span style="font-weight:700; font-family:monospace; color:#A30000;">{target_profile['article_id']}</span></div>
                            <div style="margin-bottom:8px;">🏥 <b>GPO Station:</b> <span style="font-weight:600;">{target_profile.get('booking_office', 'Unknown GPO')}</span></div>
                            <div>🏠 <b>Address:</b> <span style="font-size:13px; font-weight:500; background:#f9f9f9; padding:4px 8px; display:inline-block; border-radius:4px; border:1px solid #eee; margin-top:3px;">{target_profile['address']}</span></div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("#### 🌐 EMTTS Tracking Engine")
                    opt_col1, opt_col2 = st.columns(2)
                    with opt_col1: data_mode = st.radio("Mode Mapping:", ["Fetch Live (Raw)", "Fetch Snipped (Mapped)"])
                    with opt_col2: report_scope = st.radio("History Scope:", ["Only Last Status", "Full History"])
                    
                    if st.button("🔍 Query PakPost Servers", use_container_width=True):
                        with st.spinner("Connecting to EMTTS..."):
                            data, err = fetch_live_emtts_status(target_profile['article_id'])
                            if err: st.error(err)
                            elif data and data["history"]:
                                history_list = data["history"]
                                last_entry = history_list[-1]
                                
                                history_has_delivered = any("delivered" in h["status"].lower() for h in history_list)
                                history_has_rts = any("return" in h["status"].lower() or "rts" in h["status"].lower() for h in history_list)
                                
                                if history_has_delivered:
                                    st.success(f"✅ Delivered Status Found in Tracking Path! Last Status: {last_entry['status']} ({last_entry['datetime']})")
                                elif history_has_rts:
                                    st.error(f"❌ RTS / Return Status Found in Tracking Path! Last Status: {last_entry['status']} ({last_entry['datetime']})")
                                else:
                                    st.info(f"📍 Current Status Log: {last_entry['status']} ({last_entry['office']})")

                                use_mapped = (data_mode == "Fetch Snipped (Mapped)")
                                
                                if report_scope == "Full History":
                                    processed_rows = [{"Event": i+1, "Timestamp": h["datetime"], "Office": h["office"], "Status": map_status(h["status"]) if use_mapped else h["status"]} for i, h in enumerate(history_list)]
                                    st.dataframe(pd.DataFrame(processed_rows), use_container_width=True)
                                else:
                                    final_status_str = map_status(last_entry["status"]) if use_mapped else last_entry["status"]
                                    st.markdown(f"<div style='font-size:14px; font-weight:600; color:#A30000; background:#fdf2f2; padding:8px 12px; border-radius:4px; border:1px solid #f5c2c2;'><b>Latest Status Update:</b> {final_status_str} ({last_entry['datetime']})</div>", unsafe_allow_html=True)

                    st.markdown("#### 🎴 DIAL THIS PHONE NUMBER:")
                    raw_phone = str(target_profile.get('phone_number', '')).strip()
                    if not raw_phone or raw_phone.lower() in ['none', 'nan', 'null', ''] or len(raw_phone) < 5:
                        st.markdown("<div class='no-phone-display'>⚠️ No Contact Number Available</div>", unsafe_allow_html=True)
                    else:
                        if not raw_phone.startswith('0') and raw_phone.isdigit():
                            raw_phone = '0' + raw_phone
                        st.markdown(f"<div class='big-phone-display'>{raw_phone}</div>", unsafe_allow_html=True)
                
                with r_panel:
                    st.markdown("#### 📝 Verification Audit Questionnaire")
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
                        if is_delivered == "Select Assessment Option": st.error("Select verification response.")
                        else:
                            payload_buffer["operator_stamp"] = st.session_state.full_name
                            payload_buffer["article_id"] = target_profile["article_id"]
                            payload_buffer["patient_name"] = target_profile["patient_name"]
                            payload_buffer["mrn_no"] = target_profile.get('mrn_no', '')
                            payload_buffer["booking_office"] = target_profile.get('booking_office', 'Lahore GPO')
                            payload_buffer["booking_date"] = target_profile["booking_date"]
                            payload_buffer["address"] = target_profile["address"]
                            payload_buffer["phone_number"] = target_profile["phone_number"]
                            
                            try:
                                if target_profile.get("id"):
                                    supabase.table("patient_deliveries").update(payload_buffer).eq("id", target_profile["id"]).execute()
                                else:
                                    supabase.table("patient_deliveries").upsert(payload_buffer, on_conflict="article_id").execute()
                                    
                                st.success("Updated cleanly with operator identity stamp!")
                                st.session_state.selected_profile_index += 1
                                save_operator_state()
                                time.sleep(0.5)
                                st.rerun()
                            except Exception as e: st.error(f"Sync error: {e}")

                    # 🖨️ HIGH-END OFFICIAL MANIFESTO DOCUMENT PRINT SYSTEM
                    st.markdown("---")
                    if st.button("🖨️ Print Official Manifesto Document", use_container_width=True):
                        st.markdown(f"""
                        <div class="print-manifest-card">
                            <table style="width:100%; border-collapse:collapse; font-family:Arial, sans-serif;">
                                <tr>
                                    <td style="text-align:left; width:15%;"><span style="font-size:45px;">📮</span></td>
                                    <td style="text-align:center; width:70%;">
                                        <h2 style="margin:0; color:#A30000; font-size:24px; letter-spacing:1px;">PAKISTAN POST LOGISTICS REPORT</h2>
                                        <h5 style="margin:4px 0; color:#555; font-size:12px;">LAHORE GENERAL POST OFFICE (GPO) | SECURE AUDIT</h5>
                                    </td>
                                    <td style="text-align:right; width:15%; font-size:11px; color:#444;"><b>CONFIDENTIAL</b></td>
                                </tr>
                            </table>
                            <hr style="border:1.5px solid #A30000; margin:15px 0;">
                            
                            <table style="width:100%; font-size:14px; line-height:2; border-spacing:10px;">
                                <tr>
                                    <td style="width:25%;"><b>Patient Name:</b></td>
                                    <td style="border-bottom:1px dotted #ccc;">{target_profile['patient_name']}</td>
                                    <td style="width:20%;"><b>MRN Number:</b></td>
                                    <td style="border-bottom:1px dotted #ccc;">{target_profile.get('mrn_no', 'N/A')}</td>
                                </tr>
                                <tr>
                                    <td><b>Consignment ID:</b></td>
                                    <td style="border-bottom:1px dotted #ccc; font-family:monospace; font-weight:bold; color:#A30000;">{target_profile['article_id']}</td>
                                    <td><b>GPO Origin Node:</b></td>
                                    <td style="border-bottom:1px dotted #ccc;">{target_profile.get('booking_office', 'Lahore GPO')}</td>
                                </tr>
                                <tr>
                                    <td><b>Contact Number:</b></td>
                                    <td style="border-bottom:1px dotted #ccc;">{target_profile.get('phone_number', 'N/A')}</td>
                                    <td><b>Verification Date:</b></td>
                                    <td style="border-bottom:1px dotted #ccc;">{datetime.date.today()}</td>
                                </tr>
                                <tr>
                                    <td><b>Delivery Address:</b></td>
                                    <td colspan="3" style="border-bottom:1px dotted #ccc;">{target_profile['address']}</td>
                                </tr>
                            </table>
                            
                            <div style="margin-top:25px; padding:15px; background:#faf4f4; border:1px solid #A30000; border-radius:4px;">
                                <h4 style="margin:0 0 10px 0; color:#A30000;">AUDIT EVALUATION SUMMARY</h4>
                                <table style="width:100%; font-size:13px;">
                                    <tr>
                                        <td><b>Physical Delivery Status:</b> {payload_buffer.get('status', target_profile['status'])}</td>
                                        <td><b>Extra Tips/Charges Flagged:</b> {payload_buffer.get('extra_money_charged', target_profile.get('extra_money_charged', 'No'))}</td>
                                    </tr>
                                    <tr>
                                        <td colspan="2" style="padding-top:8px;"><b>Verified Officer Stamp:</b> {st.session_state.full_name} (System Operator)</td>
                                    </tr>
                                </table>
                            </div>
                            
                            <table style="width:100%; margin-top:70px; font-size:13px;">
                                <tr>
                                    <td style="text-align:left; width:40%; border-top:1px solid #333;"><br>System Operator Signature</td>
                                    <td style="width:20%;"></td>
                                    <td style="text-align:right; width:40%; border-top:1px solid #333;"><br>Authorized Officer GPO Stamp</td>
                                </tr>
                            </table>
                        </div>
                        <script>window.print();</script>
                        """, unsafe_allow_html=True)

    # PAGE 4: SECURE DATA EXPORT NODE
    elif st.session_state.current_navigation_tab == "📥 Secure Reports Export Center":
        st.markdown("### 📥 Secure Data Export & Cloud Records Center")
        st.info("💡 Note: Saara real-time backup pehle hi cloud storage data-nodes par fully updated aur safe hai.")
        
        try:
            with st.spinner("Fetching data logs matrix..."):
                all_records = supabase.table("patient_deliveries").select("*").execute().data
            if all_records:
                df_export = pd.DataFrame(all_records)
                if "operator_stamp" not in df_export.columns:
                    df_export["operator_stamp"] = "Unassigned Logs"
                
                if st.session_state.role == "admin":
                    st.markdown("#### 🛠️ Admin Export Panel (Full Ledger Control)")
                    distinct_operators = list(df_export["operator_stamp"].dropna().unique())
                    distinct_operators.insert(0, "Download Everything (All Operators combined)")
                    
                    target_selection = st.selectbox("Select Data Slice / Operator Filter Target:", distinct_operators)
                    if target_selection != "Download Everything (All Operators combined)":
                        df_final_download = df_export[df_export["operator_stamp"] == target_selection]
                    else:
                        df_final_download = df_export
                else:
                    st.markdown("#### 🔒 Operator Export Panel (Your Individual Action Log)")
                    df_final_download = df_export[df_export["operator_stamp"] == st.session_state.full_name]
                    st.write(f"Total verified entries stamped under your account: `{len(df_final_download)}`")
                
                if not df_final_download.empty:
                    csv_buffer = io.StringIO()
                    df_final_download.to_csv(csv_buffer, index=False)
                    csv_data = csv_buffer.getvalue().encode('utf-8')
                    
                    st.download_button(
                        label="📥 Download Authenticated Security Sheet (.CSV File)",
                        data=csv_data,
                        file_name=f"Verified_Deliveries_Log_{datetime.date.today()}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                else:
                    st.warning("No recorded data matching your credentials or filters found inside the backup matrix.")
            else:
                st.warning("Cloud database nodes are currently empty.")
        except Exception as err:
            st.error(f"Failed to compile export ledger sheets: {err}")
