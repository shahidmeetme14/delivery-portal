import streamlit as st
from supabase import create_client, Client
import pandas as pd
import datetime
import io
import time
import requests
import urllib.request
from bs4 import BeautifulSoup

# 🎛️ Page Structural Settings
st.set_page_config(
    page_title="Presented by SHAHID | Delivery Portal", 
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
if "duplicate_log_csv" not in st.session_state: st.session_state.duplicate_log_csv = None

# Initialize Column Mappings Memory
mapping_keys = ["map_article", "map_name", "map_city", "map_phone", "map_date", "map_mrn", "map_address", "map_bo", "map_dup"]
for key in mapping_keys:
    if key not in st.session_state:
        st.session_state[key] = None

# 🎨 Premium UI Engine Styling
sidebar_css_rule = ""
if not st.session_state.logged_in:
    sidebar_css_rule = """
    [data-testid="stSidebar"] { display: none !important; visibility: hidden !important; }
    [data-testid="collapsedControl"] { display: none !important; visibility: hidden !important; }
    div[data-testid="stSidebarUserContent"] { display: none !important; }
    .st-emotion-cache-1jicfl2 { padding-left: 1rem !important; padding-right: 1rem !important; }
    """
else:
    sidebar_css_rule = """
    button[data-testid="stSidebarCollapseButton"] { display: none !important; visibility: hidden !important; }
    [data-testid="collapsedControl"] { display: none !important; visibility: hidden !important; }
    section[data-testid="stSidebar"] {
        display: block !important;
        visibility: visible !important;
        transform: translateX(0%) !important;
        min-width: 300px !important;
        max-width: 300px !important;
        background: rgba(255, 255, 255, 0.45) !important;
        backdrop-filter: blur(20px) saturate(170%) !important;
        border-right: 2px solid rgba(0, 102, 51, 0.2) !important;
        box-shadow: 5px 0px 30px rgba(0, 77, 38, 0.08) !important;
    }
    """

st.markdown(f"""
    <style>
    div[data-testid="stToolbar"] {{ visibility: hidden !important; display: none !important; }}
    .stDeployButton {{ display: none !important; }}
    footer {{ visibility: hidden !important; }}
    {sidebar_css_rule}
    
    .stApp {{ background-color: #f4f8f5; }}
    .brand-title {{ color: #004d26; font-weight: 800; font-size: 2.1rem; margin-bottom: 2px; }}
    .brand-subtitle {{ color: #3d5a4c; font-size: 1.05rem; margin-bottom: 25px; font-weight: 600; border-left: 4px solid #d4af37; padding-left: 12px; }}
    
    div[data-testid="stForm"], .pyqt-panel {{
        background: #ffffff !important;
        border-radius: 8px !important;
        border: 1px solid #c2d1c9 !important;
        box-shadow: 0 6px 12px -2px rgba(0,77,38,0.04) !important;
        padding: 30px !important;
    }}
    
    div.stButton > button, div.stDownloadButton > button {{
        background: linear-gradient(180deg, #008040 0%, #006633 100%) !important;
        color: #ffffff !important;
        border: 1px solid #004d26 !important;
        border-bottom: 4px solid #00331a !important;
        border-radius: 6px !important;
        padding: 8px 24px !important;
        font-weight: 700;
        box-shadow: 0px 4px 8px rgba(0,0,0,0.12) !important;
    }}
    
    .active-nav-btn div.stButton > button {{
        background: linear-gradient(180deg, #004d26 0%, #00331a 100%) !important;
        border-bottom: 1px solid #001a0d !important;
        transform: translateY(2px) !important;
    }}
    
    /* 📥 3D DROP-DOWNS & DATE SELECTORS UI ENGINE */
    div[data-testid="stSelectbox"] > div[data-baseweb="select"], 
    div[data-testid="stDateInput"] > div {{
        background: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-bottom: 4px solid #006633 !important;
        border-radius: 8px !important;
        box-shadow: 0px 5px 12px rgba(0, 77, 38, 0.06) !important;
        transition: all 0.2s ease-in-out;
    }}
    div[data-testid="stSelectbox"] > div[data-baseweb="select"]:hover, 
    div[data-testid="stDateInput"] > div:hover {{
        transform: translateY(-1px);
        box-shadow: 0px 7px 15px rgba(0, 102, 51, 0.12) !important;
    }}
    
    /* 📱 Premium 3D Clickable Phone Display Button */
    .big-phone-display {{ 
        font-family: 'Segoe UI', -apple-system, sans-serif; 
        font-size: 34px !important; 
        font-weight: 800 !important; 
        color: #ffffff !important; 
        background: linear-gradient(180deg, #10b981 0%, #059669 100%) !important; 
        padding: 12px; 
        border-radius: 8px; 
        text-align: center; 
        border: 1px solid #047857; 
        border-bottom: 5px solid #065f46;
        box-shadow: 0px 6px 14px rgba(5, 150, 105, 0.3);
        text-shadow: 1px 2px 3px rgba(0,0,0,0.25);
        letter-spacing: 2px;
        margin: 10px 0;
    }}
    
    /* 🚨 High Visibility Fallback Red 3D Button for Missing Contacts */
    .no-phone-display {{
        font-family: 'Segoe UI', -apple-system, sans-serif; 
        font-size: 23px !important; 
        font-weight: 700 !important; 
        color: #ffffff !important; 
        background: linear-gradient(180deg, #ef4444 0%, #dc2626 100%) !important; 
        padding: 14px; 
        border-radius: 8px; 
        text-align: center; 
        border: 1px solid #b91c1c; 
        border-bottom: 5px solid #991b1b;
        box-shadow: 0px 6px 14px rgba(220, 38, 38, 0.3);
        text-shadow: 1px 2px 3px rgba(0,0,0,0.25);
        margin: 10px 0;
    }}
    
    /* 🏷️ Premium Left Panel Data Display */
    .data-card {{
        background: #ffffff;
        padding: 18px;
        border-radius: 8px;
        border: 1px solid #cbd5e1;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    }}
    .data-row {{
        margin-bottom: 12px;
        font-size: 15px;
        color: #334155;
    }}
    .data-value {{
        font-size: 19px !important;
        font-weight: 700 !important;
        color: #004d26;
        background: #f0fdf4;
        padding: 2px 8px;
        border-radius: 4px;
        border: 1px solid #bbf7d0;
        display: inline-block;
    }}
    .data-value-alt {{
        font-size: 19px !important;
        font-weight: 700 !important;
        color: #b45309;
        font-family: monospace;
        background: #fffbeb;
        padding: 2px 8px;
        border-radius: 4px;
        border: 1px solid #fef3c7;
        display: inline-block;
    }}
    .patient-card-header {{ font-size: 22px !important; font-weight: 700 !important; color: #004d26; border-left: 5px solid #d4af37; padding-left: 10px; margin-bottom: 15px; }}
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

if st.session_state.logged_in:
    with st.sidebar:
        st.markdown("<div class='sb-headline'>🖥️ Presented by SHAHID</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='sb-name-tag'>Operator Name: <br><span class='sb-name-bold'>{st.session_state.full_name}</span></div>", unsafe_allow_html=True)
        st.markdown(f"**Role Cluster:** `{st.session_state.role.upper()}`")
        st.markdown("<br><hr style='border-top:1px solid rgba(0,102,51,0.2);'><br>", unsafe_allow_html=True)
        if st.button("Terminate Session 🚪", use_container_width=True):
            st.session_state.logged_in = False
            st.query_params.clear()
            st.rerun()

st.markdown("<div class='brand-title'>📮 SHC & Pak Post | Delivery System</div>", unsafe_allow_html=True)
st.markdown("<div class='brand-subtitle'>Secure Audit & Communication Engine</div>", unsafe_allow_html=True)

if not st.session_state.logged_in:
    _, center_col, _ = st.columns([1, 1.4, 1])
    with center_col:
        st.markdown("<div style='background-color:#006633; color:#ffffff; padding:12px; font-weight:700; font-size:13px; border-radius:6px 6px 0px 0px; border:1px solid #004d26; text-align:center;'>SECURE PORTAL AUTHENTICATION</div>", unsafe_allow_html=True)
        with st.form("pyqt_enterprise_login"):
            input_user = st.text_input("OPERATOR ID / USERNAME", placeholder="Enter Username")
            input_pass = st.text_input("SECURITY ACCESS PASSWORD", type="password", placeholder="Enter Secure Key")
            btn_login = st.form_submit_button("UNLOCK TERMINAL", use_container_width=True)
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
    # 🔘 NAVIGATION MATRIX BAR
    cols_count = 4 if st.session_state.role == "admin" else 2
    nc = st.columns(cols_count)
    
    if st.session_state.role == "admin":
        with nc[0]:
            t1 = "active-nav-btn" if st.session_state.current_navigation_tab == "📊 Administrative Ingestion Engine" else ""
            st.markdown(f"<div class='{t1}'>", unsafe_allow_html=True)
            if st.button("📊 Ingestion Engine", use_container_width=True): 
                st.session_state.current_navigation_tab = "📊 Administrative Ingestion Engine"; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        with nc[1]:
            t2 = "active-nav-btn" if st.session_state.current_navigation_tab == "👥 Operator Matrix & Security Audit Logs" else ""
            st.markdown(f"<div class='{t2}'>", unsafe_allow_html=True)
            if st.button("👥 Operator Matrix", use_container_width=True): 
                st.session_state.current_navigation_tab = "👥 Operator Matrix & Security Audit Logs"; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        with nc[2]:
            t3 = "active-nav-btn" if st.session_state.current_navigation_tab == "📞 Outbound Communications Hub" else ""
            st.markdown(f"<div class='{t3}'>", unsafe_allow_html=True)
            if st.button("📞 Communications Desk", use_container_width=True): 
                st.session_state.current_navigation_tab = "📞 Outbound Communications Hub"; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        with nc[3]:
            t4 = "active-nav-btn" if st.session_state.current_navigation_tab == "📥 Secure Reports Export Center" else ""
            st.markdown(f"<div class='{t4}'>", unsafe_allow_html=True)
            if st.button("📥 Export Center & Backup", use_container_width=True): 
                st.session_state.current_navigation_tab = "📥 Secure Reports Export Center"; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        with nc[0]:
            t1 = "active-nav-btn" if st.session_state.current_navigation_tab == "📞 Outbound Communications Hub" else ""
            st.markdown(f"<div class='{t1}'>", unsafe_allow_html=True)
            if st.button("📞 Communications Desk", use_container_width=True): 
                st.session_state.current_navigation_tab = "📞 Outbound Communications Hub"; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        with nc[1]:
            t2 = "active-nav-btn" if st.session_state.current_navigation_tab == "📥 Secure Reports Export Center" else ""
            st.markdown(f"<div class='{t2}'>", unsafe_allow_html=True)
            if st.button("📥 My Exports & Backup", use_container_width=True): 
                st.session_state.current_navigation_tab = "📥 Secure Reports Export Center"; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # PAGE 1: INGESTION
    if st.session_state.current_navigation_tab == "📊 Administrative Ingestion Engine" and st.session_state.role == "admin":
        st.markdown("### 📥 Bulk Logistics Ingestion Engine")
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

            if st.button("🚀 Push Verified Records to Cloud Database", use_container_width=True):
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
                try:
                    supabase.table("patient_deliveries").upsert(staging_area, on_conflict="article_id").execute()
                    st.success("🎉 Records uploaded smoothly onto cloud datastore nodes!")
                except Exception as ex: st.error(f"Upload error: {ex}")

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

    # PAGE 3: OUTBOUND HUB
    elif st.session_state.current_navigation_tab == "📞 Outbound Communications Hub":
        st.markdown("### 📞 Outbound Communications Desk")
        
        # 📥 3D TYPE SELECTORS MATRIX (Date, Office, Patient Selector)
        query_date = st.date_input("Filter Manifest Records by Booking Date:", datetime.date.today())
        
        try: raw_date_recs = supabase.table("patient_deliveries").select("*").eq("booking_date", str(query_date)).execute().data
        except: raw_date_recs = []
            
        if not raw_date_recs: st.info("No logs found matching this calendar timestamp.")
        else:
            unique_offices = sorted(list(set([str(r.get('booking_office', 'Lahore GPO')).strip() for r in raw_date_recs])))
            unique_offices.insert(0, "All Offices")
            
            filter_col1, filter_col2 = st.columns(2)
            with filter_col1: selected_office = st.selectbox("🏥 Filter by Booking Office / GPO Node:", unique_offices)
            with filter_col2: search_term = st.text_input("🔎 Smart Search (Name, Article ID, or MRN):").strip().lower()
                
            filtered_by_office = raw_date_recs if selected_office == "All Offices" else [r for r in raw_date_recs if str(r.get('booking_office')).strip() == selected_office]
            if search_term:
                final_recs = [r for r in filtered_by_office if search_term in str(r.get('patient_name','')).lower() or search_term in str(r.get('article_id','')).lower() or search_term in str(r.get('mrn_no','')).lower()]
            else: final_recs = filtered_by_office

            if not final_recs: st.warning("No records matched filters.")
            else:
                options_list = [f"{r['patient_name']} (MRN: {r.get('mrn_no', 'N/A')}) - [{r['status']}]" for r in final_recs]
                if st.session_state.selected_profile_index >= len(options_list): st.session_state.selected_profile_index = 0
                    
                st.selectbox("Select Patient Profile to Process:", options_list, index=st.session_state.selected_profile_index, key="outbound_profile_select")
                target_profile = final_recs[st.session_state.selected_profile_index]
                
                st.markdown("<hr>", unsafe_allow_html=True)
                l_panel, r_panel = st.columns(2)
                
                with l_panel:
                    st.markdown(f"<div class='patient-card-header'>👤 {target_profile['patient_name']}</div>", unsafe_allow_html=True)
                    
                    # 🏷️ UPGRADED LEFT PANEL DETAILS: BADA AUR NUMAYAN TEXT CORES
                    st.markdown(f"""
                        <div class='data-card'>
                            <div class='data-row'>🔢 <b>MRN Number:</b><br><span class='data-value'>{target_profile.get('mrn_no', 'N/A')}</span></div>
                            <div class='data-row'>📦 <b>Consignment ID (Article):</b><br><span class='data-value-alt'>{target_profile['article_id']}</span></div>
                            <div class='data-row'>🏥 <b>Booking GPO Station:</b><br><span style='font-size:18px; font-weight:600; color:#1e293b;'>{target_profile.get('booking_office', 'Unknown GPO')}</span></div>
                            <div class='data-row'>🏠 <b>Address:</b><br><span style='font-size:17px; font-weight:600; color:#1e293b; background:#f8fafc; padding:6px; display:block; border-radius:4px; border:1px solid #e2e8f0; margin-top:4px;'>{target_profile['address']}</span></div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("#### 🌐 Pakistan Post Live EMTTS Tracking")
                    opt_col1, opt_col2 = st.columns(2)
                    with opt_col1: data_mode = st.radio("Display Transformation:", ["Fetch Live (Raw Mode)", "Fetch Snipped Data (Mapped Mode)"])
                    with opt_col2: report_scope = st.radio("Reporting Scope Evaluation:", ["Only Last Status", "All Statuses (Full History)"])
                    
                    if st.button("🔍 Fetch Live Status from PakPost Server", use_container_width=True):
                        with st.spinner("Connecting to EMTTS Logistics..."):
                            data, err = fetch_live_emtts_status(target_profile['article_id'])
                            if err: st.error(err)
                            elif data and data["history"]:
                                history_list = data["history"]
                                last_entry = history_list[-1]
                                last_status_lower = last_entry["status"].lower()
                                
                                is_historical_anomaly = any("delivered" in h["status"].lower() or "return" in h["status"].lower() or "rts" in h["status"].lower() for h in history_list[:-1])
                                is_last_delivered = "delivered" in last_status_lower
                                is_last_rts = "return" in last_status_lower or "rts" in last_status_lower
                                
                                if is_historical_anomaly and not (is_last_delivered or is_last_rts):
                                    st.markdown("<div style='background-color:#dc2626; color:white; padding:14px; border-radius:6px; font-weight:800; text-align:center;'>⚠️ ANOMALY DETECTED: Marked Delivered/RTS in history but NOT currently!</div>", unsafe_allow_html=True)
                                
                                if is_last_delivered: st.success(f"✅ FINAL STATUS: {last_entry['status']} ({last_entry['datetime']})")
                                elif is_last_rts: st.error(f"❌ FINAL STATUS: {last_entry['status']} ({last_entry['datetime']})")
                                else: st.info(f"📍 CURRENT STATUS: {last_entry['status']} ({last_entry['office']})")

                                use_mapped = (data_mode == "Fetch Snipped Data (Mapped Mode)")
                                if report_scope == "All Statuses (Full History)":
                                    processed_rows = [{"Event": i+1, "Timestamp": h["datetime"], "Office": h["office"], "Status": map_status(h["status"]) if use_mapped else h["status"]} for i, h in enumerate(history_list)]
                                    st.dataframe(pd.DataFrame(processed_rows), use_container_width=True)
                                else:
                                    final_status_str = map_status(last_entry["status"]) if use_mapped else last_entry["status"]
                                    st.metric(label="Latest Status", value=final_status_str)

                    st.markdown("#### 🎴 DIAL THIS PHONE NUMBER FROM LANDLINE:")
                    
                    # 📱 SMART PHONE NUMBER FORMATTING ENGINE & FALLBACK ENGINE
                    raw_phone = str(target_profile.get('phone_number', '')).strip()
                    
                    if not raw_phone or raw_phone.lower() in ['none', 'nan', 'null', ''] or len(raw_phone) < 5:
                        # Fallback: Agar number na ho ya invalid ho
                        st.markdown("<div class='no-phone-display'>⚠️ No Contact Number Available</div>", unsafe_allow_html=True)
                    else:
                        # Formatting: Shuru me khud 0 lagana agar mojud na ho
                        if not raw_phone.startswith('0') and raw_phone.isdigit():
                            raw_phone = '0' + raw_phone
                        st.markdown(f"<div class='big-phone-display'>{raw_phone}</div>", unsafe_allow_html=True)
                
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
                        if is_delivered == "Select Assessment Option": st.error("Select verification response.")
                        else:
                            # 🏷️ EMBED OPERATOR NAME DIGITAL STAMP
                            payload_buffer["operator_stamp"] = st.session_state.full_name
                            try:
                                supabase.table("patient_deliveries").update(payload_buffer).eq("id", target_profile["id"]).execute()
                                st.success("Updated with operator identity stamp!")
                                st.session_state.selected_profile_index += 1
                                save_operator_state()
                                time.sleep(0.5)
                                st.rerun()
                            except Exception as e: st.error(f"Sync error: {e}")

    # PAGE 4: SECURE DATA EXPORT NODE & CLOUD BACKUP CONTROLS
    elif st.session_state.current_navigation_tab == "📥 Secure Reports Export Center":
        st.markdown("### 📥 Secure Data Export & Cloud Records Center")
        st.info("💡 Note: Saara real-time backup pehle hi cloud storage data-nodes par fully updated aur safe hai.")
        
        try:
            with st.spinner("Fetching data logs matrix..."):
                all_records = supabase.table("patient_deliveries").select("*").execute().data
            if all_records:
                df_export = pd.DataFrame(all_records)
                
                # Check mapping data architecture safety for operator stamps
                if "operator_stamp" not in df_export.columns:
                    df_export["operator_stamp"] = "Unassigned Logs"
                
                # Apply Security Access Filtration Clearances
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
