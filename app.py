import streamlit as st
from supabase import create_client, Client
import pandas as pd
import datetime
import io
import time
import requests
import urllib.request
from bs4 import BeautifulSoup
import streamlit.components.v1 as components

# 🎛️ Page Structural Settings
st.set_page_config(
    page_title="SHC & Pak Post | Delivery System", 
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
if "fetched_emtts_data" not in st.session_state: st.session_state.fetched_emtts_data = {}

# Initialize Column Mappings Memory
mapping_keys = ["map_article", "map_name", "map_city", "map_phone", "map_date", "map_mrn", "map_address", "map_bo", "map_dup"]
for key in mapping_keys:
    if key not in st.session_state:
        st.session_state[key] = None

# 🎨 Premium UI Engine Styling - Customized to ep.gov.pk Red & Gold Theme with Crystal Black Sidebar
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
        background: linear-gradient(180deg, #111111 0%, #222222 100%) !important;
        backdrop-filter: blur(20px) saturate(170%) !important;
        border-right: 2px solid rgba(212, 175, 55, 0.4) !important;
        box-shadow: 5px 0px 30px rgba(0, 0, 0, 0.6) !important;
    }
    section[data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    section[data-testid="stSidebar"] button div * {
        color: #ffffff !important;
    }
    """

st.markdown(f"""
    <style>
    div[data-testid="stToolbar"] {{ visibility: hidden !important; display: none !important; }}
    .stDeployButton {{ display: none !important; }}
    footer {{ visibility: hidden !important; display: none !important; }}
    [data-testid="stViewerBadge"] {{ display: none !important; visibility: hidden !important; }}
    div[class^="viewerBadge"] {{ display: none !important; visibility: hidden !important; }}
    .viewerBadge_container__1616G {{ display: none !important; visibility: hidden !important; }}
    .stAppDeployButton {{ display: none !important; visibility: hidden !important; }}
    {sidebar_css_rule}
    
    .stApp {{ background-color: #fdfcf9; }}
    .brand-title {{ color: #a61c1c; font-weight: 800; font-size: 2.1rem; margin-bottom: 2px; }}
    .brand-subtitle {{ color: #5c1414; font-size: 1.05rem; margin-bottom: 25px; font-weight: 600; border-left: 4px solid #d4af37; padding-left: 12px; }}
    
    div[data-testid="stForm"], .pyqt-panel {{
        background: #ffffff !important;
        border-radius: 8px !important;
        border: 1px solid #d1c2c2 !important;
        box-shadow: 0 6px 12px -2px rgba(166,28,28,0.04) !important;
        padding: 30px !important;
    }}
    
    div[data-testid="stForm"] small, [data-testid="InputInstructions"] {{
        display: none !important;
    }}
    
    div.stButton > button, div.stDownloadButton > button {{
        background: linear-gradient(180deg, #cc2424 0%, #a61c1c 100%) !important;
        color: #ffffff !important;
        border: 1px solid #801414 !important;
        border-bottom: 4px solid #590d0d !important;
        border-radius: 6px !important;
        padding: 8px 24px !important;
        font-weight: 700;
        box-shadow: 0px 4px 8px rgba(0,0,0,0.12) !important;
        transition: all 0.1s ease;
    }}
    
    div.stButton > button:active, div.stDownloadButton > button:active {{
        transform: scale(0.98);
        box-shadow: inset 0px 2px 5px rgba(0,0,0,0.3) !important;
    }}
    
    /* 💎 Crystal Style Navigation Buttons with 3D Gold Border */
    section[data-testid="stSidebar"] div.stButton > button {{
        background: rgba(255, 255, 255, 0.05) !important;
        color: #ffffff !important;
        border: 2px solid rgba(212, 175, 55, 0.5) !important;
        border-bottom: 5px solid rgba(179, 146, 46, 0.9) !important; /* Rich 3D Gold shadow base */
        border-radius: 10px !important;
        padding: 10px 20px !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37), inset 0 1px 2px rgba(255,255,255,0.1) !important;
        transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
        font-weight: 700 !important;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.9) !important;
    }}
    
    section[data-testid="stSidebar"] div.stButton > button:hover {{
        background: rgba(212, 175, 55, 0.15) !important; /* Elegant golden crystal glow */
        border-color: rgba(212, 175, 55, 0.9) !important;
        box-shadow: 0 0 15px rgba(212, 175, 55, 0.4), inset 0 1px 3px rgba(255, 255, 255, 0.2) !important;
        transform: translateY(-1px) !important;
    }}
    
    section[data-testid="stSidebar"] div.stButton > button:active {{
        transform: translateY(3px) !important;
        border-bottom: 2px solid rgba(179, 146, 46, 0.9) !important;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.5), inset 0 1px 1px rgba(0,0,0,0.3) !important;
    }}

    /* 🔴 Terminate Session Button - Glossy Red Look styling via Anchor Selector & Direct Siblings */
    div[data-testid="element-container"]:has(.terminate-btn-anchor) + div[data-testid="element-container"] button,
    div:has(> .terminate-btn-anchor) + div.element-container div.stButton > button,
    div:has(> * > .terminate-btn-anchor) + div.element-container div.stButton > button,
    div.terminate-btn-anchor + div.stButton > button {{
        background: linear-gradient(180deg, #ff3b30 0%, #c31414 100%) !important;
        color: #ffffff !important;
        border: 2px solid rgba(255, 59, 48, 0.6) !important;
        border-bottom: 5px solid #8a0c0c !important;
        border-radius: 10px !important;
        padding: 10px 20px !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        box-shadow: 0 8px 32px 0 rgba(195, 20, 20, 0.3), inset 0 1px 3px rgba(255,255,255,0.4) !important;
        transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
        font-weight: 700 !important;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.6) !important;
    }}
    div[data-testid="element-container"]:has(.terminate-btn-anchor) + div[data-testid="element-container"] button:hover,
    div:has(> .terminate-btn-anchor) + div.element-container div.stButton > button:hover,
    div:has(> * > .terminate-btn-anchor) + div.element-container div.stButton > button:hover,
    div.terminate-btn-anchor + div.stButton > button:hover {{
        background: linear-gradient(180deg, #ff453a 0%, #d31818 100%) !important;
        border-color: rgba(255, 59, 48, 0.9) !important;
        box-shadow: 0 0 20px rgba(255, 59, 48, 0.5), inset 0 1px 4px rgba(255, 255, 255, 0.5) !important;
        transform: translateY(-1px) !important;
    }}
    div[data-testid="element-container"]:has(.terminate-btn-anchor) + div[data-testid="element-container"] button:active,
    div:has(> .terminate-btn-anchor) + div.element-container div.stButton > button:active,
    div:has(> * > .terminate-btn-anchor) + div.element-container div.stButton > button:active,
    div.terminate-btn-anchor + div.stButton > button:active {{
        transform: translateY(3px) !important;
        border-bottom: 2px solid #8a0c0c !important;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.5), inset 0 1px 1px rgba(0,0,0,0.3) !important;
    }}
    
    /* 🖨️ Parent-Level Custom Print Button */
    .custom-print-btn {{
        background: linear-gradient(180deg, #cc2424 0%, #a61c1c 100%) !important;
        color: #ffffff !important;
        border: 1px solid #801414 !important;
        border-bottom: 4px solid #590d0d !important;
        border-radius: 6px !important;
        padding: 12px 24px !important;
        font-weight: 700;
        font-size: 14px;
        font-family: 'Segoe UI', sans-serif;
        box-shadow: 0px 4px 8px rgba(0,0,0,0.12);
        cursor: pointer;
        width: 100%;
        margin-top: 15px;
        transition: all 0.1s ease;
        display: block;
        text-align: center;
    }}
    .custom-print-btn:hover {{
        background: linear-gradient(180deg, #e53e3e 0%, #cc2424 100%) !important;
    }}
    .custom-print-btn:active {{
        transform: scale(0.99);
        box-shadow: inset 0px 2px 5px rgba(0,0,0,0.3) !important;
    }}
    
    div[data-testid="stSelectbox"] > div[data-baseweb="select"], 
    div[data-testid="stDateInput"] > div,
    div[data-testid="stTextInput"] > div {{
        background: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-bottom: 3px solid #b1bccd !important;
        border-radius: 6px !important;
        box-shadow: 0px 1px 2px rgba(0,0,0,0.05) !important;
        transition: all 0.15s ease-in-out;
    }}
    
    div[data-testid="stSelectbox"] > div[data-baseweb="select"]:hover, 
    div[data-testid="stDateInput"] > div:hover,
    div[data-testid="stTextInput"] > div:hover {{
        background: #ffffff !important;
        border-color: #a61c1c !important;
        box-shadow: 0px 2px 4px rgba(166,28,28,0.08) !important;
    }}

    div[data-testid="stSelectbox"] *, 
    div[data-testid="stDateInput"] input,
    div[data-testid="stTextInput"] input {{
        color: #1e293b !important;
        font-weight: 600 !important;
    }}
    
    div[data-testid="stTextInput"] input[type="password"] {{
        background: transparent !important;
        color: #1e293b !important;
    }}
    
    .big-phone-display {{ 
        font-family: 'Segoe UI', -apple-system, sans-serif; 
        font-size: 22px !important; 
        font-weight: 800 !important; 
        color: #ffffff !important; 
        background: linear-gradient(180deg, #d4af37 0%, #b3922e 100%) !important; 
        padding: 6px 12px; 
        border-radius: 4px; 
        text-align: center; 
        border: 1px solid #b3922e; 
        border-bottom: 3px solid #8c7120;
        box-shadow: 0px 2px 5px rgba(212, 175, 55, 0.15);
        text-shadow: 1px 1px 1px rgba(0,0,0,0.15);
        letter-spacing: 1px;
        margin: 4px 0;
        display: block;
        width: 100%;
        box-sizing: border-box;
    }}
    
    .no-phone-display {{
        font-family: 'Segoe UI', -apple-system, sans-serif; 
        font-size: 22px !important; 
        font-weight: 700 !important; 
        color: #ffffff !important; 
        background: linear-gradient(180deg, #ef4444 0%, #dc2626 100%) !important; 
        padding: 6px 12px; 
        border-radius: 4px; 
        text-align: center; 
        border: 1px solid #b91c1c; 
        border-bottom: 3px solid #991b1b;
        box-shadow: 0px 2px 5px rgba(220, 38, 38, 0.15);
        text-shadow: 1px 1px 1px rgba(0,0,0,0.15);
        margin: 4px 0;
        display: block;
        width: 100%;
        box-sizing: border-box;
    }}
    
    .data-card {{
        background: #ffffff;
        padding: 18px;
        border-radius: 8px;
        border: 1px solid #cbd5e1;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    }}
    .data-card .data-row {{
        margin-bottom: 12px;
        font-size: 15px;
        color: #334155;
    }}
    .data-card .data-value {{
        font-size: 19px !important;
        font-weight: 700 !important;
        color: #a61c1c;
        background: #fff5f5;
        padding: 2px 8px;
        border-radius: 4px;
        border: 1px solid #fecaca;
        display: inline-block;
    }}
    .data-card .data-value-alt {{
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
    .patient-card-header {{ font-size: 22px !important; font-weight: 700 !important; color: #a61c1c; border-left: 5px solid #d4af37; padding-left: 10px; margin-bottom: 15px; }}
    
    section[data-testid="stSidebar"] .sb-headline-custom {{ font-size: 20px !important; font-weight: bold !important; color: #d4af37 !important; margin-bottom: 15px; }}
    section[data-testid="stSidebar"] .sb-login-label {{ margin-top: 15px; color: #cbd5e1 !important; font-size: 14px; }}
    section[data-testid="stSidebar"] .sb-username-display {{ font-size: 18px !important; font-weight: bold !important; color: #d4af37 !important; margin-bottom: 10px; }}
    section[data-testid="stSidebar"] .sb-privilege-label {{ margin-top: 10px; color: #cbd5e1 !important; font-size: 14px; }}
    section[data-testid="stSidebar"] .sb-privilege-label span {{
        color: #39ff14 !important;
        font-weight: bold !important;
        text-shadow: 0 0 5px #39ff14, 0 0 10px #39ff14, 0 0 20px #39ff14 !important;
    }}
    
    /* 🖨️ Absolute Print Media Optimization (Perfect A4 Portrait Layout) */
    @media print {{
        @page {{
            size: A4 portrait !important;
            margin: 15mm !important; /* Standard clean margin space on A4 sheets */
        }}
        html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMainViewContainer"], .main, .block-container {{
            height: auto !important;
            overflow: visible !important;
            overflow-x: visible !important;
            overflow-y: visible !important;
            background: #ffffff !important;
            background-color: #ffffff !important;
            padding: 0 !important;
            margin: 0 !important;
        }}
        /* Hide all UI elements, sidebars, buttons, headers by default to prevent leaking */
        body * {{ 
            visibility: hidden !important; 
        }}
        [data-testid="stSidebar"], 
        [data-testid="stHeader"], 
        [data-testid="stToolbar"], 
        .stDeployButton, 
        footer, 
        button, 
        iframe, 
        .stButton,
        [data-testid="collapsedControl"] {{
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
            width: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
        }}
        /* Enable and Re-display ONLY the manifest card and its nested children */
        .print-manifest-card, .print-manifest-card * {{ 
            visibility: visible !important; 
            display: revert !important;
        }}
        /* Anchor the manifest cleanly to the top-left of the physical paper page */
        .print-manifest-card {{ 
            position: absolute !important; 
            left: 0 !important; 
            top: 0 !important; 
            width: 100% !important; 
            max-width: 180mm !important; /* Fits precisely on standard A4 paper width */
            height: auto !important;
            border: none !important; 
            box-shadow: none !important; 
            background: #ffffff !important;
            padding: 0px !important; /* Prevents visual offset on layout printing */
            margin: 0 !important;
            box-sizing: border-box !important;
            display: block !important;
            z-index: 9999999 !important;
            page-break-inside: avoid !important;
        }}
        .print-manifest-card table {{
            width: 100% !important;
            table-layout: fixed !important;
            border-collapse: collapse !important;
            margin-top: 15px !important;
            page-break-inside: avoid !important;
        }}
        .print-manifest-card td {{
            word-wrap: break-word !important;
            overflow-wrap: break-word !important;
            white-space: normal !important;
            padding: 8px 10px !important;
            font-size: 14px !important;
            color: #000000 !important;
            border-bottom: 1px solid #e2e8f0 !important;
        }}
        /* Force color backgrounds to render properly (e.g. red anomaly box, warning headers) */
        * {{
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
        }}
    }}
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


# ==========================================
# 📑 MULTI-PAGE DECLARATIONS (VIEWS)
# ==========================================

def login_view():
    _, center_col, _ = st.columns([1, 1.4, 1])
    with center_col:
        st.markdown("<div style='background-color:#a61c1c; color:#ffffff; padding:12px; font-weight:700; font-size:13px; border-radius:6px 6px 0px 0px; border:1px solid #801414; text-align:center;'>SECURE PORTAL AUTHENTICATION</div>", unsafe_allow_html=True)
        with st.form("pyqt_enterprise_login"):
            input_user = st.text_input("OPERATOR ID / USERNAME", placeholder="Enter Username")
            input_pass = st.text_input("SECURITY ACCESS PASSWORD", type="password", placeholder="Enter Secure Key")
            btn_login = st.form_submit_button("UNLOCK TERMINAL", use_container_width=True)
            if btn_login:
                with st.spinner("Processing portal authentication..."):
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


def recovery_view():
    _, alert_box, _ = st.columns([1, 2, 1])
    with alert_box:
        st.info("Unexpected system shutdown detected. Last active session data has been safely recovered.")
        col_res, col_new = st.columns(2)
        with col_res:
            if st.button("🔄 RESUME INTERRUPTED SESSION", use_container_width=True):
                with st.spinner("Processing session recovery..."):
                    st.session_state.logged_in = True
                    st.session_state.current_navigation_tab = st.session_state.cached_recovery_data.get('last_tab')
                    st.session_state.selected_profile_index = int(st.session_state.cached_recovery_data.get('last_index', 0))
                    st.session_state.show_recovery_prompt = False
                    st.rerun()
        with col_new:
            if st.button("🆕 START FRESH BLANK SESSION", use_container_width=True):
                with st.spinner("Processing fresh terminal clear..."):
                    st.session_state.logged_in = True
                    st.session_state.show_recovery_prompt = False
                    save_operator_state()
                    st.rerun()


def ingestion_view():
    st.session_state.current_navigation_tab = "📊 Administrative Ingestion Engine"
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
            c_mrn = st.selectbox("MRN No. Column:", df.columns, index=calculate_mapped_index(df.columns, "map_mrn", "MRN No"))
        with mc2:
            c_phone = st.selectbox("Contact Number Column:", df.columns, index=calculate_mapped_index(df.columns, "map_phone", "MobileNo"))
            c_date = st.selectbox("Booking Date Column:", df.columns, index=calculate_mapped_index(df.columns, "map_date", "Booking Date"))
            c_address = st.selectbox("Address Column:", df.columns, index=calculate_mapped_index(df.columns, "map_address", "Address"))
        with mc3:
            c_city = st.selectbox("City Column:", df.columns, index=calculate_mapped_index(df.columns, "map_city", "City"))
            c_bo = st.selectbox("Booking Office Column:", df.columns, index=calculate_mapped_index(df.columns, "map_bo", "Booking Office"))
            c_dup = st.selectbox("Duplication Log Column:", df.columns, index=calculate_mapped_index(df.columns, "map_dup", "Duplicate"))

        if st.button("🚀 Push Verified Records to Cloud Database & Storage Bucket", use_container_width=True):
            status_progress_text = st.empty()
            progress_bar_control = st.progress(0)
            
            status_progress_text.text("Connecting with cloud storage nodes... (15% Complete)")
            progress_bar_control.progress(15)
            
            try:
                existing_master_bytes = supabase.storage.from_("manifests").download("master_manifest_store.csv")
                master_ledger_df = pd.read_csv(io.BytesIO(existing_master_bytes), dtype=str)
            except Exception:
                master_ledger_df = pd.DataFrame(columns=[
                    "article_id", "patient_name", "phone_number", "booking_date", 
                    "address", "patient_city", "mrn_no", "booking_office", "transaction_no"
                ])

            status_progress_text.text("Analyzing spreadsheet matrix structures... (45% Complete)")
            progress_bar_control.progress(45)
            
            new_manifest_rows = []
            for _, row_data in df.iterrows():
                new_manifest_rows.append({
                    "article_id": str(row_data[c_article]).strip(),
                    "patient_name": str(row_data[c_name]).strip(),
                    "phone_number": str(row_data[c_phone]).strip(),
                    "booking_date": str(row_data[c_date])[:10],
                    "address": str(row_data[c_address]).strip(),
                    "patient_city": str(row_data[c_city]).strip(),
                    "mrn_no": str(row_data[c_mrn]).strip(),
                    "booking_office": str(row_data[c_bo]).strip() if c_bo in df.columns else "Lahore GPO",
                    "transaction_no": str(row_data[c_dup]).strip() if c_dup in df.columns else ""
                })
            uploaded_records_df = pd.DataFrame(new_manifest_rows, dtype=str)
            total_input_count = len(uploaded_records_df)

            status_progress_text.text("Scanning master datastore for cross-duplications... (75% Complete)")
            progress_bar_control.progress(75)
            
            is_duplicate_by_transaction = uploaded_records_df["transaction_no"].isin(master_ledger_df["transaction_no"]) & (uploaded_records_df["transaction_no"] != "") & (uploaded_records_df["transaction_no"] != "nan")
            global_duplication_mask = is_duplicate_by_transaction
            
            clean_unique_records = uploaded_records_df[~global_duplication_mask]
            if "transaction_no" in clean_unique_records.columns:
                clean_unique_records = clean_unique_records.drop_duplicates(subset=["transaction_no"])
            
            total_duplicates_cleared = total_input_count - len(clean_unique_records)
            
            final_consolidated_df = pd.concat([master_ledger_df, clean_unique_records], ignore_index=True)
            
            status_progress_text.text("Synchronizing clean ledger stream into cloud core... (95% Complete)")
            progress_bar_control.progress(95)
            
            master_csv_buffer = io.StringIO()
            final_consolidated_df.to_csv(master_csv_buffer, index=False)
            master_csv_bytes = master_csv_buffer.getvalue().encode('utf-8')
            
            try:
                try: supabase.storage.from_("manifests").remove(["master_manifest_store.csv"])
                except: pass
                
                supabase.storage.from_("manifests").upload(path="master_manifest_store.csv", file=master_csv_bytes, file_options={"content-type": "text/csv"})
                
                status_progress_text.empty()
                progress_bar_control.empty()
                
                st.success(f"🟢 Success: File processed successfully! Out of {total_input_count} total records, {total_duplicates_cleared} duplicate entries were detected and removed based on the selected deduplication parameters. The remaining unique records have been securely saved.")
            except Exception as store_ex:
                st.error(f"Failed to synchronize master stream archive: {store_ex}")


def operator_matrix_view():
    st.session_state.current_navigation_tab = "👥 Operator Matrix & Security Audit Logs"
    st.markdown("### 👥 Operational Account Provisioning")
    nf = st.text_input("Operator Full Name")
    nu = st.text_input("Operational Username / ID")
    np = st.text_input("Assigned Initial Password", type="password")
    if st.button("Register Operator Account", use_container_width=True):
        with st.spinner("Processing operator provisioning logic..."):
            if nf and nu and np:
                try:
                    supabase.table("app_users").insert({"username": nu.strip(), "password": np.strip(), "full_name": nf.strip(), "role": "staff"}).execute()
                    st.success("Operator registered successfully!")
                except Exception as e: st.error(f"Error: {e}")


def communications_view():
    st.session_state.current_navigation_tab = "📞 Outbound Communications Hub"
    st.markdown("### 📞 Outbound Communications Desk")
    
    query_date = st.date_input("Filter Manifest Records by Booking Date:", datetime.date.today())
    
    with st.spinner("Processing cloud storage lookup and database audit..."):
        try:
            existing_master_bytes = supabase.storage.from_("manifests").download("master_manifest_store.csv")
            master_ledger_df = pd.read_csv(io.BytesIO(existing_master_bytes), dtype=str)
            filtered_master_rows = master_ledger_df[master_ledger_df["booking_date"] == str(query_date)]
            raw_date_recs = filtered_master_rows.to_dict(orient="records")
        except Exception:
            raw_date_recs = []
            
        try:
            db_action_logs = supabase.table("patient_deliveries").select("*").eq("booking_date", str(query_date)).execute().data
            db_logs_dictionary = {str(item["article_id"]).strip(): item for item in db_action_logs}
        except Exception:
            db_logs_dictionary = {}
            
    if not raw_date_recs: 
        st.info("No record found against selected date.")
    else:
        for profile in raw_date_recs:
            article_key = str(profile["article_id"]).strip()
            if article_key in db_logs_dictionary:
                profile["id"] = db_logs_dictionary[article_key]["id"]
                profile["status"] = db_logs_dictionary[article_key].get("status", "Pending")
                profile["delivery_date"] = db_logs_dictionary[article_key].get("delivery_date")
                profile["received_mode"] = db_logs_dictionary[article_key].get("received_mode")
                profile["extra_money_charged"] = db_logs_dictionary[alert_key].get("extra_money_charged") if 'alert_key' in locals() else db_logs_dictionary[article_key].get("extra_money_charged")
                profile["issue_reason"] = db_logs_dictionary[article_key].get("issue_reason")
                profile["operator_stamp"] = db_logs_dictionary[article_key].get("operator_stamp")
            else:
                profile["id"] = None
                profile["status"] = "Pending"

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
                
            selected_prof_str = st.selectbox("Select Patient Profile to Process:", options_list, index=st.session_state.selected_profile_index, key="outbound_profile_select")
            
            actual_index = options_list.index(selected_prof_str) if selected_prof_str in options_list else 0
            target_profile = final_recs[actual_index]
            
            if target_profile["status"] in ["Delivered", "Issue / Complaint"]:
                st.warning(f"⚠️ Note: The questionnaire for this patient has already been processed! Current Status: [{target_profile['status']}]")

            st.markdown("<hr>", unsafe_allow_html=True)
            l_panel, r_panel = st.columns(2)
            
            with l_panel:
                st.markdown(f"<div class='patient-card-header'>👤 {target_profile['patient_name']}</div>", unsafe_allow_html=True)
                
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
                            st.session_state.fetched_emtts_data[target_profile['article_id']] = data
                            
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
                                st.markdown(f"""
                                    <div style='background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 14px; margin-bottom: 15px;'>
                                        <div style='font-size: 13px; font-weight: 600; color: #475569; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;'>Latest Status</div>
                                        <div style='font-size: 20px; font-weight: 700; color: #1e293b; line-height: 1.3; word-wrap: break-word;'>{final_status_str}</div>
                                    </div>
                                """, unsafe_allow_html=True)

                st.markdown("<div style='font-size: 22px; font-weight: 800; color: #334155; margin-bottom: 6px;'>🎴 DIAL THIS PHONE NUMBER FROM LANDLINE:</div>", unsafe_allow_html=True)
                
                raw_phone = str(target_profile.get('phone_number', '')).strip()
                if not raw_phone or raw_phone.lower() in ['none', 'nan', 'null', ''] or len(raw_phone) < 5:
                    st.markdown("<div class='no-phone-display'>⚠️ No Contact Number Available</div>", unsafe_allow_html=True)
                    raw_phone = ""
                else:
                    if not raw_phone.startswith('0') and raw_phone.isdigit():
                        raw_phone = '0' + raw_phone
                    st.markdown(f"<div class='big-phone-display'>{raw_phone}</div>", unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                with st.expander("🖨️ Individual Profile Print Desk"):
                    print_operator = target_profile.get('operator_stamp', st.session_state.full_name)
                    
                    print_status = target_profile.get('status', 'Pending')
                    print_status_detail = f"[{print_status}]"
                    if print_status == "Delivered":
                        delivery_date = target_profile.get('delivery_date', 'N/A')
                        received_mode = target_profile.get('received_mode', 'N/A')
                        extra_money = target_profile.get('extra_money_charged', 'N/A')
                        print_status_detail = f"""
                        <b style="color: green;">Delivered</b><br>
                        <span style="font-size: 13px; font-weight: 600; color: #334155; line-height: 1.4;">
                            • Date: {delivery_date}<br>
                            • Mode: {received_mode}<br>
                            • Extra Money Requested/Tips: <b style="color: {'#dc2626' if extra_money == 'Yes' else '#1e293b'}">{extra_money}</b>
                        </span>
                        """
                    elif print_status == "Issue / Complaint":
                        issue_reason = target_profile.get('issue_reason', 'N/A')
                        print_status_detail = f"""
                        <b style="color: #dc2626;">Issue / Complaint</b><br>
                        <span style="font-size: 13px; font-weight: 600; color: #334155; line-height: 1.4;">
                            • Reason: {issue_reason}
                        </span>
                        """
                    else:
                        print_status_detail = f"<b style='color: #475569;'>Pending Verification</b>"

                    current_article_id = target_profile['article_id']
                    cached_emtts = st.session_state.fetched_emtts_data.get(current_article_id)

                    if not cached_emtts:
                        st.info("ℹ️ Live tracking status has not been fetched from the main engine above.")
                        st.markdown("##### 📥 Fetch EMTTS Live Status Directly in Print Desk")
                        print_data_mode = st.radio("Print Display Transformation:", ["Fetch Live (Raw Mode)", "Fetch Snipped Data (Mapped Mode)"], key="print_data_mode_sel")
                        print_report_scope = st.radio("Print Reporting Scope:", ["Only Last Status", "All Statuses (Full History)"], key="print_report_scope_sel")
                        
                        if st.button("🔍 Fetch Status inside Print Card", use_container_width=True, key="print_direct_fetch_btn"):
                            with st.spinner("Connecting to EMTTS Logistics..."):
                                data, err = fetch_live_emtts_status(current_article_id)
                                if err:
                                    st.error(err)
                                else:
                                    st.session_state.fetched_emtts_data[current_article_id] = data
                                    st.success("Successfully loaded live status! Now you can print.")
                                    st.rerun()
                    
                    cached_emtts = st.session_state.fetched_emtts_data.get(current_article_id)

                    if cached_emtts and "history" in cached_emtts:
                        history_list = cached_emtts["history"]
                        active_data_mode = st.session_state.get("print_data_mode_sel", data_mode)
                        use_mapped = (active_data_mode == "Fetch Snipped Data (Mapped Mode)")
                        
                        last_entry = history_list[-1]
                        status_val = map_status(last_entry["status"]) if use_mapped else last_entry["status"]
                        
                        print_historical_anomaly = any("delivered" in h["status"].lower() or "return" in h["status"].lower() or "rts" in h["status"].lower() for h in history_list[:-1])
                        last_status_lower_print = last_entry["status"].lower()
                        print_last_delivered = "delivered" in last_status_lower_print
                        print_last_rts = "return" in last_status_lower_print or "rts" in last_status_lower_print
                        
                        print_anomaly_box_html = ""
                        if print_historical_anomaly and not (print_last_delivered or print_last_rts):
                            print_anomaly_box_html = """
                            <div class="anomaly-warning-box" style="background-color: #dc2626 !important; color: #ffffff !important; padding: 12px; border-radius: 6px; font-weight: bold; font-size: 13px; margin-bottom: 15px; border: 1px solid #b91c1c; word-wrap: break-word; white-space: normal; line-height: 1.4; -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important;">
                                ⚠️ ANOMALY DETECTED: Marked Delivered/RTS in history but NOT currently!
                            </div>
                            """
                        
                        emtts_status_html = f"""
                        {print_anomaly_box_html}
                        <div style="font-weight: bold; color: #1e293b; font-size: 15px; word-wrap: break-word; white-space: normal; line-height: 1.4;">{status_val}</div>
                        <div style="font-size: 12px; color: #475569; margin-top: 4px; line-height: 1.3;">
                            📍 Office: {last_entry['office']} <br> 🕒 Date-Time: {last_entry['datetime']}
                        </div>
                        """
                    else:
                        emtts_status_html = "<span style='color: #94a3b8; font-style: italic; font-size: 13px;'>Live status not fetched yet (Use options above to fetch)</span>"

                    st.markdown(f"""
                        <div class="print-manifest-card" style="background: #ffffff; border: 2px dashed #cbd5e1; padding: 25px; border-radius: 8px; font-family: 'Segoe UI', sans-serif; color: #000000;">
                            <div style="text-align: center; border-bottom: 2px solid #a61c1c; padding-bottom: 10px; margin-bottom: 20px;">
                                <h2 style="margin: 0; color: #a61c1c; font-size: 22px; font-weight: 800;">PAKISTAN POST LOGISTICS MANIFEST</h2>
                                <p style="margin: 5px 0 0 0; color: #475569; font-size: 13px; font-weight: 600;">Quality Verification & Consignee Audit Certificate</p>
                            </div>
                            <table style="width: 100%; border-collapse: collapse; font-size: 15px; color: #000000;">
                                <tr>
                                    <td style="padding: 10px; font-weight: bold; width: 35%; border-bottom: 1px solid #e2e8f0;">Patient Name:</td>
                                    <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{target_profile['patient_name']}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 10px; font-weight: bold; border-bottom: 1px solid #e2e8f0;">MRN Number:</td>
                                    <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{target_profile.get('mrn_no', 'N/A')}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 10px; font-weight: bold; border-bottom: 1px solid #e2e8f0;">Consignment ID (Article):</td>
                                    <td style="padding: 10px; border-bottom: 1px solid #e2e8f0; font-family: monospace; font-weight: 700; color: #a61c1c;">{target_profile['article_id']}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 10px; font-weight: bold; border-bottom: 1px solid #e2e8f0;">Contact Number:</td>
                                    <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{raw_phone if raw_phone else 'N/A'}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 10px; font-weight: bold; border-bottom: 1px solid #e2e8f0;">Booking GPO Station:</td>
                                    <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{target_profile.get('booking_office', 'N/A')}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 10px; font-weight: bold; border-bottom: 1px solid #e2e8f0;">Mailing Address:</td>
                                    <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{target_profile['address']}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 10px; font-weight: bold; border-bottom: 1px solid #e2e8f0; vertical-align: top;">EMTTS Tracking Status:</td>
                                    <td style="padding: 10px; border-bottom: 1px solid #e2e8f0; vertical-align: top;">{emtts_status_html}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 10px; font-weight: bold; border-bottom: 1px solid #e2e8f0; vertical-align: top;">Verification Status:</td>
                                    <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{print_status_detail}</td>
                                </tr>
                            </table>
                            <div style="margin-top: 35px; display: flex; justify-content: space-between; font-size: 13px; border-top: 1px solid #cbd5e1; padding-top: 15px; color: #475569;">
                                <div><b>Verified By (Operator ID):</b> {print_operator}</div>
                                <div><b>System Print Timestamp:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                    # 🖨️ Direct Printing Script (Uses Components Iframe to reliably trigger parent window print)
                    components.html(f"""
                    <style>
                    .custom-print-btn {{
                        background: linear-gradient(180deg, #cc2424 0%, #a61c1c 100%) !important;
                        color: #ffffff !important;
                        border: 1px solid #801414 !important;
                        border-bottom: 4px solid #590d0d !important;
                        border-radius: 6px !important;
                        padding: 12px 24px !important;
                        font-weight: 700;
                        font-size: 14px;
                        font-family: 'Segoe UI', sans-serif;
                        box-shadow: 0px 4px 8px rgba(0,0,0,0.12);
                        cursor: pointer;
                        width: 100%;
                        margin: 0;
                        box-sizing: border-box;
                        transition: all 0.1s ease;
                        display: block;
                        text-align: center;
                    }}
                    .custom-print-btn:hover {{
                        background: linear-gradient(180deg, #e53e3e 0%, #cc2424 100%) !important;
                    }}
                    .custom-print-btn:active {{
                        transform: scale(0.99);
                        box-shadow: inset 0px 2px 5px rgba(0,0,0,0.3) !important;
                    }}
                    body {{
                        margin: 0;
                        padding: 0;
                        overflow: hidden;
                        background: transparent;
                    }}
                    </style>
                    <button onclick="window.parent.print()" class="custom-print-btn">🖨️ PRINT LOGISTICS MANIFEST</button>
                    """, height=55)

                    st.markdown('<p style="font-size:12px; color:#64748b; margin-top:8px; text-align:center;">💡 Tip: Clicking the button above or pressing <b>Ctrl + P</b> will cleanly print only this manifest certificate on a full page.</p>', unsafe_allow_html=True)
            
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
                    with st.spinner("Processing transaction submission rules..."):
                        if is_delivered == "Select Assessment Option": st.error("Select verification response.")
                        else:
                            payload_buffer["operator_stamp"] = st.session_state.full_name
                            payload_buffer["article_id"] = target_profile["article_id"]
                            payload_buffer["patient_name"] = target_profile["patient_name"]
                            payload_buffer["phone_number"] = target_profile["phone_number"]
                            payload_buffer["booking_date"] = target_profile["booking_date"]
                            payload_buffer["address"] = target_profile["address"]
                            payload_buffer["patient_city"] = target_profile["patient_city"]
                            payload_buffer["mrn_no"] = target_profile["mrn_no"]
                            payload_buffer["booking_office"] = target_profile["booking_office"]
                            
                            try:
                                supabase.table("patient_deliveries").upsert(payload_buffer, on_conflict="article_id").execute()
                                st.success("Updated with operator identity stamp!")
                                st.session_state.selected_profile_index += 1
                                save_operator_state()
                                time.sleep(0.5)
                                st.rerun()
                            except Exception as e: st.error(f"Sync error: {e}")


def export_center_view():
    st.session_state.current_navigation_tab = "📥 Secure Reports Export Center"
    st.markdown("### 📥 Secure Data Export & Cloud Records Center")
    st.info("💡 Note: All real-time backups are already fully updated and securely stored on the cloud storage data nodes.")
    
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


# ==========================================
# 🗺️ DYNAMIC PORTAL ROUTING ENGINE
# ==========================================

# 1. Dynamic Native Page Mapping based on Security Context and States
if not st.session_state.logged_in:
    # Login Mode - Safe Isolation without navigation links
    pages_to_display = [
        st.Page(login_view, title="Authentication Desk", icon="🔒")
    ]
elif st.session_state.show_recovery_prompt:
    # Session Recovery Override State
    pages_to_display = [
        st.Page(recovery_view, title="Session Recovery", icon="🔄")
    ]
else:
    # Active Account Operational Matrix Setup
    if st.session_state.role == "admin":
        pages_to_display = [
            st.Page(ingestion_view, title="Ingestion Engine", icon="📊"),
            st.Page(operator_matrix_view, title="Operator Matrix", icon="👥"),
            st.Page(communications_view, title="Communications Desk", icon="📞"),
            st.Page(export_center_view, title="Export Center & Backup", icon="📥")
        ]
    else:
        pages_to_display = [
            st.Page(communications_view, title="Communications Desk", icon="📞"),
            st.Page(export_center_view, title="My Exports & Backup", icon="📥")
        ]

# Initialize Routing (Position set to hidden so default sidebar links don't show)
selected_navigation_route = st.navigation(pages_to_display, position="hidden")

# 2. Global Header Branding & Complaints Alert Engine (Will render on all sub-pages automatically)
st.markdown("<div class='brand-title'>📮 SHC & Pak Post | Delivery System</div>", unsafe_allow_html=True)
st.markdown("<div class='brand-subtitle'>Secure Audit & Communication Engine</div>", unsafe_allow_html=True)

if st.session_state.logged_in and st.session_state.role == "admin":
    try:
        unauthorized_charges = supabase.table("patient_deliveries").select("*").eq("extra_money_charged", "Yes").execute().data
        if unauthorized_charges:
            st.markdown("### 🚨 Critical Corruption & Extra Charges Alerts")
            for alert in unauthorized_charges:
                alert_col1, alert_col2 = st.columns([4, 1])
                with alert_col1:
                    st.error(f"⚠️ **Postman Alert (Extra Charges Issue):** Extra money requested/charged for **{alert['patient_name']}** (MRN: {alert.get('mrn_no', 'N/A')}, Consignment ID: {alert['article_id']}). Stamped by Operator: **{alert.get('operator_stamp', 'Staff')}**\n\n*(Note: This log will display extended postman information upon questionnaire configuration updates)*")
                with alert_col2:
                    if st.button("Dismiss / Resolve ✅", key=f"resolve_charge_{alert['id']}", use_container_width=True):
                        with st.spinner("Processing alert resolution..."):
                            supabase.table("patient_deliveries").update({"extra_money_charged": "Yes (Resolved)"}).eq("id", alert["id"]).execute()
                            st.success("Alert successfully cleared from active view!")
                            time.sleep(0.5)
                            st.rerun()
            st.markdown("<hr style='border-top: 1px solid #cc2424;'>", unsafe_allow_html=True)
            
        resolved_charges = supabase.table("patient_deliveries").select("*").eq("extra_money_charged", "Yes (Resolved)").execute().data
        if resolved_charges:
            with st.expander("📁 View Resolved Alert History Logs (Past Reports Archive - Extra Charges Issues)"):
                history_df = pd.DataFrame(resolved_charges)
                column_mapping_view = {
                    "patient_name": "Patient Name",
                    "mrn_no": "MRN Number",
                    "article_id": "Consignment ID",
                    "operator_stamp": "Reported By (Operator)",
                    "booking_date": "Booking Date"
                }
                history_df_filtered = history_df[[col for col in column_mapping_view.keys() if col in history_df.columns]].rename(columns=column_mapping_view)
                st.dataframe(history_df_filtered, use_container_width=True, hide_index=True)
    except:
        pass


# 3. Render Sidebar Session Meta Information, Navigation Buttons & Session Kill Switch
if st.session_state.logged_in:
    with st.sidebar:
        st.markdown("<div class='sb-headline-custom'>🖥️ Enterprise Console</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='sb-login-label'>Logged in as:</div><div class='sb-username-display'>{st.session_state.full_name}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='sb-privilege-label'>Privilege Cluster: <span>{st.session_state.role.upper()}</span></div>", unsafe_allow_html=True)
        
        # Navigation Portion
        if not st.session_state.show_recovery_prompt:
            st.markdown("<br><hr style='border-top: 2px solid rgba(212,175,55,0.4); margin: 10px 0;'><br>", unsafe_allow_html=True)
            st.markdown("<div style='font-size: 15px; font-weight: 800; color: #d4af37; margin-bottom: 12px; letter-spacing: 1.5px;'>📂 SYSTEM NAVIGATION</div>", unsafe_allow_html=True)
            
            for pg in pages_to_display:
                is_active = (pg == selected_navigation_route)
                if is_active:
                    button_label = f"▶️ **{pg.icon} {pg.title}**"
                else:
                    button_label = f"{pg.icon} {pg.title}"
                    
                if st.button(button_label, use_container_width=True, key=f"nav_btn_{pg.title}"):
                    st.switch_page(pg)
                    
        st.markdown("<br><hr style='border-top: 2px solid rgba(212,175,55,0.4); margin: 10px 0;'><br>", unsafe_allow_html=True)
        
        # Sibling Anchor for Custom Glossy Red Button Styling
        st.markdown("<div class='terminate-btn-anchor'></div>", unsafe_allow_html=True)
        if st.button("Terminate Session 🚪", use_container_width=True):
            with st.spinner("Processing session termination..."):
                st.session_state.logged_in = False
                st.query_params.clear()
                st.rerun()


# 4. Streamlit Routing Engine Execution
selected_navigation_route.run()
