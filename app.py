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

# 🇵🇰 Pakistan Standard Time (PKT) Setup - No external libraries needed
PKT_TZ = datetime.timezone(datetime.timedelta(hours=5))

# 🎛️ Page Structural Settings
st.set_page_config(
    page_title="SHC & Pak Post | Free Home Delivery of Medicine", 
    page_icon="📮", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# 🔄 URL HYDRATION ENGINE (Fixed for Refresh Lock)
SESSION_TIMEOUT = 30 * 60  

if "logged_in" not in st.session_state: 
    st.session_state.logged_in = False

if not st.session_state.logged_in and "usr" in st.query_params:
    try:
        param_time = float(st.query_params.get("t", time.time()))
        if time.time() - param_time < SESSION_TIMEOUT:
            st.session_state.logged_in = True
            st.session_state.username = str(st.query_params.get("usr", ""))
            st.session_state.full_name = str(st.query_params.get("nm", ""))
            st.session_state.role = str(st.query_params.get("rl", "staff"))
            st.session_state.last_activity = time.time()  # Keep session alive on page refresh
            if "tab" in st.query_params:
                st.session_state.current_navigation_tab = str(st.query_params.get("tab"))
        else:
            st.query_params.clear()
    except Exception:
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

# --- Step 1: Admin Alert Expanders Highlighting in Closed View ---
generic_expander_highlight_css = """
/* 📦 Admin Alert Expanders - Generic Styling in closed view for highlighting */
div[data-testid="stExpander"] {
    border: 2px solid rgba(212, 175, 55, 0.4) !important; /* Gold border */
    border-radius: 8px !important;
    background-color: rgba(212, 175, 55, 0.05) !important; /* Subtle gold tint */
    box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
    margin-bottom: 20px !important;
    transition: all 0.3s ease !important;
}

div[data-testid="stExpander"] button[data-testid="stExpanderHeader"] p {
    font-weight: 800 !important;
    color: #5c1414 !important; /* Deep red matching subtitle */
}

div[data-testid="stExpander"] button[data-testid="stExpanderHeader"] p span {
    color: #5c1414 !important;
}

div[data-testid="stExpander"] button[data-testid="stExpanderHeader"] [data-testid="stExpanderToggleIcon"] {
    color: #d4af37 !important; /* Gold */
}

div[data-testid="stExpander"] > div[data-testid="stExpanderBody"] {
    padding-top: 10px !important;
    background-color: transparent !important;
}
"""

st.markdown(f"""
    <style>
    /* Complete & Absolute Removal of Streamlit Watermarks, Headers, Footers, Badges & Links */
    div[data-testid="stToolbar"], #MainMenu, footer, header,
    [data-testid="stHeader"], [data-testid="stDecoration"],
    [data-testid="stStatusWidget"], [data-testid="stActionElements"],
    .stDeployButton, .stAppDeployButton, button[kind="header"],
    [data-testid="stViewerBadge"], div[class^="viewerBadge"], div[class*="viewerBadge"],
    .viewerBadge_container__1616G, a[href*="streamlit.io"],
    div[data-testid="stBottom"], div[data-testid="stBottomBlockContainer"] {{
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        height: 0px !important;
        width: 0px !important;
        max-height: 0px !important;
        max-width: 0px !important;
        pointer-events: none !important;
        overflow: hidden !important;
    }}
    
    {generic_expander_highlight_css} 
    {sidebar_css_rule}
    
    .stApp {{ background-color: #fdfcf9; }}
    .brand-title {{ color: #a61c1c; font-weight: 800; font-size: 2.1rem; margin-bottom: 2px; }}
    .brand-subtitle {{ color: #5c1414; font-size: 1.05rem; margin-bottom: 25px; font-weight: 600; border-left: 4px solid #d4af37; padding-left: 12px; }}
    
    /* 📦 3D Premium Cards for Admin Alerts */
    .alert-3d-card {{
        background: linear-gradient(145deg, #ffffff, #fdfbf7);
        border-radius: 12px;
        box-shadow: 6px 6px 15px rgba(0,0,0,0.08), -6px -6px 15px rgba(255,255,255,0.8);
        border-left: 6px solid #cc2424;
        padding: 18px 22px;
        margin-bottom: 12px;
        border-top: 1px solid #f1f5f9;
        border-right: 1px solid #f1f5f9;
        border-bottom: 1px solid #f1f5f9;
        transition: all 0.3s ease;
    }}
    .alert-3d-card:hover {{
        transform: translateY(-3px);
        box-shadow: 8px 8px 20px rgba(0,0,0,0.12), -8px -8px 20px rgba(255,255,255,0.9);
    }}
    .alert-3d-title {{ font-size: 19px; font-weight: 800; color: #1e293b; margin-bottom: 5px; }}
    .alert-3d-subtitle {{ font-size: 14px; color: #64748b; font-weight: 500; }}
    .alert-3d-badge {{ background: #fee2e2; color: #dc2626; padding: 5px 12px; border-radius: 20px; font-weight: 700; font-size: 13px; border: 1px solid #fecaca; box-shadow: 0px 2px 4px rgba(220, 38, 38, 0.1); }}

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
    
    /* 💎 Crystal Style Navigation Buttons */
    section[data-testid="stSidebar"] div.stButton > button {{
        background: rgba(255, 255, 255, 0.05) !important;
        color: #ffffff !important;
        border: 2px solid rgba(212, 175, 55, 0.5) !important;
        border-bottom: 5px solid rgba(179, 146, 46, 0.9) !important;
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
        background: rgba(212, 175, 55, 0.15) !important;
        border-color: rgba(212, 175, 55, 0.9) !important;
        box-shadow: 0 0 15px rgba(212, 175, 55, 0.4), inset 0 1px 3px rgba(255, 255, 255, 0.2) !important;
        transform: translateY(-1px) !important;
    }}

    /* 🟡 Glossy Gold Crystal Password Button */
    div:has(> .password-btn-anchor) + div button,
    div:has(.password-btn-anchor) + div button {{
        background: linear-gradient(180deg, #ffd700 0%, #b8860b 100%) !important;
        color: #000000 !important;
        border: 2px solid rgba(255, 255, 255, 0.6) !important;
        border-bottom: 5px solid #8b6508 !important;
        border-radius: 10px !important;
        padding: 10px 20px !important;
        font-weight: 800 !important;
        text-shadow: 0px 1px 1px rgba(255, 255, 255, 0.6) !important;
    }}
    
    /* 🔴 Terminate Session Button */
    div:has(> .terminate-btn-anchor) + div button,
    div:has(.terminate-btn-anchor) + div button {{
        background: linear-gradient(180deg, #ff4d4d 0%, #c31414 100%) !important;
        color: #ffffff !important;
        border: 2px solid rgba(255, 255, 255, 0.4) !important;
        border-bottom: 5px solid #800a0a !important;
        border-radius: 10px !important;
        padding: 10px 20px !important;
        font-weight: 800 !important;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.8) !important;
    }}
    
    /* ✨ 3D Dropdowns, Inputs & Textareas */
    div[data-baseweb="select"] > div, 
    div[data-testid="stSelectbox"] div[data-baseweb="select"],
    div[data-testid="stDateInput"] > div,
    div[data-testid="stTextInput"] > div,
    div[data-testid="stNumberInput"] > div,
    div[data-testid="stTextArea"] > div {{
        background: linear-gradient(180deg, #ffffff 0%, #f1f5f9 100%) !important;
        border: 1px solid #94a3b8 !important;
        border-bottom: 4px solid #64748b !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), inset 0 1px 0 rgba(255,255,255,0.7) !important;
        transition: all 0.15s ease-in-out !important;
        overflow: hidden !important;
    }}
    
    div[data-baseweb="select"] > div > div {{
        background-color: transparent !important;
    }}
    
    div[data-baseweb="select"] > div:hover, 
    div[data-testid="stDateInput"] > div:hover,
    div[data-testid="stTextInput"] > div:hover,
    div[data-testid="stTextArea"] > div:hover {{
        border-color: #a61c1c !important;
        border-bottom: 4px solid #a61c1c !important;
        transform: translateY(-1px);
    }}

    div[data-baseweb="select"] *, 
    div[data-testid="stDateInput"] input,
    div[data-testid="stTextInput"] input,
    div[data-testid="stTextArea"] textarea {{
        color: #1e293b !important;
        font-weight: 600 !important;
    }}
    
    /* 🎨 Right Column Questionnaire Background */
    [data-testid="column"]:nth-of-type(2) {{
        background: linear-gradient(135deg, #ffffff 0%, #fdfbf7 100%);
        border: 1px solid #e2e8f0;
        border-top: 4px solid #d4af37;
        border-radius: 10px;
        padding: 22px;
        box-shadow: 0px 8px 20px -5px rgba(0,0,0,0.06);
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
        margin: 4px 0;
        display: block;
        width: 100%;
        box-sizing: border-box;
    }}
    
    .data-card {{ background: #ffffff; padding: 18px; border-radius: 8px; border: 1px solid #cbd5e1; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
    .data-card .data-row {{ margin-bottom: 12px; font-size: 15px; color: #334155; }}
    .data-card .data-value {{ font-size: 19px !important; font-weight: 700 !important; color: #a61c1c; background: #fff5f5; padding: 2px 8px; border-radius: 4px; border: 1px solid #fecaca; display: inline-block; }}
    .data-card .data-value-alt {{ font-size: 19px !important; font-weight: 700 !important; color: #b45309; font-family: monospace; background: #fffbeb; padding: 2px 8px; border-radius: 4px; border: 1px solid #fef3c7; display: inline-block; }}
    .patient-card-header {{ font-size: 22px !important; font-weight: 700 !important; color: #a61c1c; border-left: 5px solid #d4af37; padding-left: 10px; margin-bottom: 15px; }}
    
    section[data-testid="stSidebar"] .sb-headline-custom {{ font-size: 20px !important; font-weight: bold !important; color: #00E5FF !important; margin-bottom: 15px; }}
    section[data-testid="stSidebar"] .sb-login-label {{ margin-top: 15px; color: #cbd5e1 !important; font-size: 14px; }}
    section[data-testid="stSidebar"] .sb-username-display {{ font-size: 18px !important; font-weight: bold !important; color: #d4af37 !important; margin-bottom: 10px; }}
    section[data-testid="stSidebar"] .sb-privilege-label {{ margin-top: 10px; color: #cbd5e1 !important; font-size: 14px; }}
    section[data-testid="stSidebar"] .sb-privilege-label span {{ color: #39ff14 !important; font-weight: bold !important; text-shadow: 0 0 5px #39ff14, 0 0 10px #39ff14 !important; }}
    
    /* 🖨️ Absolute Print Media Optimization (Strict 1 Page Fit) */
    @media print {{
        @page {{ size: A4 portrait !important; margin: 0 !important; }}
        
        body, html {{ width: 100% !important; height: 100% !important; margin: 0 !important; padding: 0 !important; background: #fff !important; }}
        
        /* Stop empty containers from generating blank pages */
        body * {{ visibility: hidden !important; }}
        [data-testid="stSidebar"], [data-testid="stHeader"], [data-testid="stToolbar"], header, footer, iframe, .stElementContainer:has(iframe) {{ display: none !important; }}
        
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], .block-container {{
            position: absolute !important; top: 0 !important; left: 0 !important;
            height: 100vh !important; width: 100vw !important; overflow: hidden !important; 
            padding: 0 !important; margin: 0 !important; border: none !important;
        }}

        .print-manifest-card, .print-manifest-card * {{ visibility: visible !important; color: #000000 !important; background-color: transparent !important; box-shadow: none !important; text-shadow: none !important; }}
        
        .print-manifest-card {{ 
            position: absolute !important; left: 0 !important; top: 0 !important; width: 100% !important;
            height: 98vh !important; /* Force fit to exactly 1 page */
            margin: 0 !important; padding: 15px 25px !important; border: 2px solid #000000 !important; 
            background: #ffffff !important; background-color: #ffffff !important; box-sizing: border-box !important; 
            page-break-inside: avoid !important; z-index: 99999999 !important; display: block !important;
            overflow: hidden !important;
        }}
        .print-manifest-card table {{ width: 100% !important; display: table !important; border-collapse: collapse !important; margin-top: 10px !important; }}
        .print-manifest-card tr {{ display: table-row !important; page-break-inside: avoid !important; height: auto !important; }}
        .print-manifest-card td, .print-manifest-card th {{ display: table-cell !important; padding: 6px 10px !important; font-size: 13px !important; color: #000000 !important; border-bottom: 1px solid #cbd5e1 !important; }}
        .screen-only-timestamp {{ display: none !important; }}
        * {{ -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }}
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
            "updated_at": datetime.datetime.now(PKT_TZ).isoformat()
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

# URL Syncing for Refresh Page Lock Engine
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
        st.query_params["usr"] = str(st.session_state.username)
        st.query_params["nm"] = str(st.session_state.full_name)
        st.query_params["rl"] = str(st.session_state.role)
        if st.session_state.get("current_navigation_tab"):
            st.query_params["tab"] = str(st.session_state.current_navigation_tab)

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

@st.dialog("🔐 Change User Password")
def change_password_dialog():
    st.markdown("<div style='color: #475569; font-size: 14px; margin-bottom: 15px;'>Enter your current password and define a new secure key.</div>", unsafe_allow_html=True)
    curr_pass = st.text_input("Current Password", type="password", key="dlg_curr_pass")
    new_pass = st.text_input("New Password", type="password", key="dlg_new_pass")
    conf_pass = st.text_input("Confirm New Password", type="password", key="dlg_conf_pass")
    
    if st.button("Update Password 💾", use_container_width=True):
        if not curr_pass or not new_pass or not conf_pass:
            st.error("⚠️ Please fill in all password fields.")
        elif new_pass != conf_pass:
            st.error("❌ New passwords do not match!")
        else:
            with st.spinner("Verifying and updating credentials..."):
                try:
                    ud = supabase.table("app_users").select("*").eq("username", st.session_state.username).eq("password", curr_pass.strip()).execute().data
                    if ud:
                        supabase.table("app_users").update({"password": new_pass.strip()}).eq("username", st.session_state.username).execute()
                        st.success("✅ Password updated successfully!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Incorrect current password!")
                except Exception as ex:
                    st.error(f"Database error: {ex}")

@st.dialog("📊 Date-wise Verification Stats", width="large")
def user_stats_dialog():
    st.markdown("<div style='color: #475569; font-size: 14px; margin-bottom: 15px;'>Select date range to view verifications count details.</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: start_date = st.date_input("From Date", datetime.date.today() - datetime.timedelta(days=7))
    with c2: end_date = st.date_input("To Date", datetime.date.today())
    
    if st.button("Calculate Stats 🧮", use_container_width=True):
        with st.spinner("Fetching logs matrix..."):
            try:
                if st.session_state.role == "admin":
                    users_res = supabase.table("app_users").select("full_name").eq("role", "staff").execute().data
                    staff_names = [u['full_name'] for u in users_res] if users_res else []
                    
                    all_records = supabase.table("patient_deliveries").select("operator_stamp, created_at").execute().data
                    counts = {name: 0 for name in staff_names}
                    
                    for r in all_records:
                        if 'created_at' in r and r['created_at']:
                            try:
                                dt = datetime.datetime.fromisoformat(r['created_at'].replace('Z', '+00:00')).date()
                                if start_date <= dt <= end_date:
                                    op = r.get('operator_stamp')
                                    if op in counts: counts[op] += 1
                                    elif op: counts[op] = 1 
                            except: pass
                            
                    df_stats = pd.DataFrame(list(counts.items()), columns=["Operator Name", "Total Verifications"])
                    st.dataframe(df_stats, use_container_width=True)
                    
                    csv_buffer = io.StringIO()
                    df_stats.to_csv(csv_buffer, index=False)
                    st.download_button("📥 Export Staff Stats (.CSV)", data=csv_buffer.getvalue().encode('utf-8'), file_name=f"Staff_Stats_{start_date}_to_{end_date}.csv", mime="text/csv", use_container_width=True)
                else:
                    res = supabase.table("patient_deliveries").select("created_at").eq("operator_stamp", st.session_state.full_name).execute().data
                    count = 0
                    for r in res:
                        if 'created_at' in r and r['created_at']:
                            try:
                                dt = datetime.datetime.fromisoformat(r['created_at'].replace('Z', '+00:00')).date()
                                if start_date <= dt <= end_date:
                                    count += 1
                            except: pass
                    st.success(f"Total verifications between selected dates: **{count}**")
            except Exception as e:
                st.error(f"Error fetching stats: {e}")

@st.dialog("🖨️ Auto-Fetched Alert Manifest", width="large")
def open_alert_manifest(alert_data):
    st.markdown(f"**Patient Name:** {alert_data.get('patient_name', 'N/A')} &nbsp; | &nbsp; **Consignment ID:** `{alert_data.get('article_id', 'N/A')}`")
    
    with st.spinner("Connecting securely to PakPost server for real-time EMTTS Tracking data..."):
        data, err = fetch_live_emtts_status(alert_data['article_id'])
        
    if err or not data:
        emtts_status_html = f"<span style='color: #dc2626; font-weight: bold;'>⚠️ {err}</span>"
    else:
        last_entry = data["history"][-1]
        emtts_status_html = f"""
        <div style="font-weight: bold; color: #1e293b; font-size: 15px;">{last_entry["status"]}</div>
        <div style="font-size: 12px; color: #475569; margin-top: 4px;">📍 Office: {last_entry['office']} <br> 🕒 Date-Time: {last_entry['datetime']}</div>
        """
        
    print_operator = alert_data.get('operator_stamp', 'System Alert Console')
    extra_charge = alert_data.get('extra_money_charged', 'Yes')
    print_status_detail = f"""
    <b style="color: green;">Delivered</b><br>
    <span style="font-size: 13px; font-weight: 600; color: #334155; line-height: 1.4;">
        • Date: {alert_data.get('delivery_date', 'N/A')}<br>
        • Mode: {alert_data.get('received_mode', 'N/A')}<br>
        • Extra Money Requested: <b style="color: #dc2626">{extra_charge}</b>
    </span>
    """

    raw_phone = str(alert_data.get('phone_number', '')).strip()
    if not raw_phone.startswith('0') and raw_phone.isdigit():
        raw_phone = '0' + raw_phone
        
    current_pkt_time = datetime.datetime.now(PKT_TZ).strftime('%Y-%m-%d %I:%M:%S %p')
        
    st.markdown(f"""
        <div class="print-manifest-card" style="background: #ffffff; border: 2px dashed #cbd5e1; padding: 25px; border-radius: 8px; font-family: 'Segoe UI', sans-serif; color: #000000;">
            <div style="text-align: center; border-bottom: 2px solid #a61c1c; padding-bottom: 10px; margin-bottom: 20px;">
                <h2 style="margin: 0; color: #a61c1c; font-size: 22px; font-weight: 800;">PAKISTAN POST | PATIENT FEEDBACK MANIFEST</h2>
                <p style="margin: 5px 0 0 0; color: #475569; font-size: 13px; font-weight: 600;">Quality Verification & Consignee Audit Certificate</p>
            </div>
            <table style="width: 100%; border-collapse: collapse; font-size: 15px; color: #000000;">
                <tr><td style="padding: 10px; font-weight: bold; width: 35%; border-bottom: 1px solid #e2e8f0;">Patient Name:</td><td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{alert_data.get('patient_name', 'N/A')}</td></tr>
                <tr><td style="padding: 10px; font-weight: bold; border-bottom: 1px solid #e2e8f0;">MRN Number:</td><td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{alert_data.get('mrn_no', 'N/A')}</td></tr>
                <tr><td style="padding: 10px; font-weight: bold; border-bottom: 1px solid #e2e8f0;">Consignment ID (Article):</td><td style="padding: 10px; border-bottom: 1px solid #e2e8f0; font-family: monospace; font-weight: 700; color: #a61c1c;">{alert_data['article_id']}</td></tr>
                <tr><td style="padding: 10px; font-weight: bold; border-bottom: 1px solid #e2e8f0;">Contact Number:</td><td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{raw_phone if raw_phone else 'N/A'}</td></tr>
                <tr><td style="padding: 10px; font-weight: bold; border-bottom: 1px solid #e2e8f0;">Booking GPO Station:</td><td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{alert_data.get('booking_office', 'N/A')}</td></tr>
                <tr><td style="padding: 10px; font-weight: bold; border-bottom: 1px solid #e2e8f0;">Mailing Address:</td><td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{alert_data.get('address', 'N/A')}</td></tr>
                <tr><td style="padding: 10px; font-weight: bold; border-bottom: 1px solid #e2e8f0; vertical-align: top;">EMTTS Tracking Status:</td><td style="padding: 10px; border-bottom: 1px solid #e2e8f0; vertical-align: top;">{emtts_status_html}</td></tr>
                <tr><td style="padding: 10px; font-weight: bold; border-bottom: 1px solid #e2e8f0; vertical-align: top;">Verification Status:</td><td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{print_status_detail}</td></tr>
            </table>
            <div style="margin-top: 35px; display: flex; justify-content: space-between; font-size: 13px; border-top: 1px solid #cbd5e1; padding-top: 15px; color: #475569;">
                <div>
                    <b>Verified By (Operator ID):</b> {print_operator}<br>
                    <span style="font-size: 11px; color: #64748b;">Timestamp: {current_pkt_time} (PKT)</span>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    components.html("""
    <style>
    .custom-print-btn { background: linear-gradient(180deg, #cc2424 0%, #a61c1c 100%) !important; color: #ffffff !important; border: 1px solid #801414 !important; border-bottom: 4px solid #590d0d !important; border-radius: 6px !important; padding: 12px 24px !important; font-weight: 700; font-size: 14px; font-family: 'Segoe UI', sans-serif; box-shadow: 0px 4px 8px rgba(0,0,0,0.12); cursor: pointer; width: 100%; display: block; text-align: center; }
    .custom-print-btn:hover { background: linear-gradient(180deg, #e53e3e 0%, #cc2424 100%) !important; }
    body { margin: 0; padding: 0; overflow: hidden; background: transparent; }
    </style>
    <button onclick="window.parent.print()" class="custom-print-btn">🖨️ PRINT FEEDBACK MANIFEST</button>
    """, height=55)

def login_view():
    _, center_col, _ = st.columns([1, 1.4, 1])
    with center_col:
        st.markdown("<div style='background-color:#a61c1c; color:#ffffff; padding:12px; font-weight:700; font-size:13px; border-radius:6px 6px 0px 0px; border:1px solid #801414; text-align:center; margin-top: 15px;'>SECURE PORTAL AUTHENTICATION</div>", unsafe_allow_html=True)
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
                                
                                # Set query params for refresh lock instantly
                                st.query_params["usr"] = ud[0]["username"]
                                st.query_params["nm"] = ud[0]["full_name"]
                                st.query_params["rl"] = ud[0]["role"]
                                st.query_params["t"] = str(time.time())
                                
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
                                    st.session_state.last_activity = time.time()
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
                    st.session_state.last_activity = time.time()
                    st.query_params["usr"] = st.session_state.username
                    st.query_params["nm"] = st.session_state.full_name
                    st.query_params["rl"] = st.session_state.role
                    st.query_params["t"] = str(time.time())
                    if st.session_state.current_navigation_tab:
                        st.query_params["tab"] = st.session_state.current_navigation_tab
                    st.rerun()
        with col_new:
            if st.button("🆕 START FRESH BLANK SESSION", use_container_width=True):
                with st.spinner("Processing fresh terminal clear..."):
                    st.session_state.logged_in = True
                    st.session_state.show_recovery_prompt = False
                    st.session_state.current_navigation_tab = None
                    st.session_state.selected_profile_index = 0
                    st.session_state.last_activity = time.time()
                    if "tab" in st.query_params:
                        del st.query_params["tab"]
                    save_operator_state()
                    st.rerun()

def ingestion_view():
    st.session_state.current_navigation_tab = "📊 Administrative Ingestion Engine"
    st.markdown("### 📥 Bulk Articles Ingestion Engine")
    source_file = st.file_uploader("Upload Medicine Article Sheet", type=["xlsx", "csv"], key="bulk_uploader_main")
    if source_file is not None:
        file_key = f"cached_df_{source_file.name}_{source_file.size}"
        if file_key not in st.session_state:
            df = pd.read_excel(source_file, dtype=str) if source_file.name.endswith('.xlsx') else pd.read_csv(source_file, low_memory=False, dtype=str)
            st.session_state[file_key] = df
        else:
            df = st.session_state[file_key]
        
        st.write("Preview of Uploaded Data:")
        st.dataframe(df.head(), use_container_width=True)
        all_cols = df.columns.tolist()
        
        st.markdown("---")
        st.markdown("#### Map Mandatory Data Columns")
        col1, col2, col3 = st.columns(3)
        with col1:
            i_art = calculate_mapped_index(all_cols, "map_article", "article")
            st.session_state.map_article = st.selectbox("Article / Consignment ID Column", all_cols, index=i_art)
            i_name = calculate_mapped_index(all_cols, "map_name", "name")
            st.session_state.map_name = st.selectbox("Patient Name Column", all_cols, index=i_name)
            i_city = calculate_mapped_index(all_cols, "map_city", "city")
            st.session_state.map_city = st.selectbox("City Column", all_cols, index=i_city)
        with col2:
            i_phone = calculate_mapped_index(all_cols, "map_phone", "phone")
            st.session_state.map_phone = st.selectbox("Contact Number Column", all_cols, index=i_phone)
            i_date = calculate_mapped_index(all_cols, "map_date", "date")
            st.session_state.map_date = st.selectbox("Booking Date Column", all_cols, index=i_date)
            i_mrn = calculate_mapped_index(all_cols, "map_mrn", "mrn")
            st.session_state.map_mrn = st.selectbox("MRN No Column", all_cols, index=i_mrn)
        with col3:
            i_addr = calculate_mapped_index(all_cols, "map_address", "address")
            st.session_state.map_address = st.selectbox("Home Address Column", all_cols, index=i_addr)
            i_bo = calculate_mapped_index(all_cols, "map_bo", "booking")
            st.session_state.map_bo = st.selectbox("Booking Office Column", all_cols, index=i_bo)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 INGEST AND DEPLOY INTO DATABASE SERVER", use_container_width=True):
            with st.spinner(f"Processing database pipeline. Injecting records into master table..."):
                try:
                    current_db_arts = []
                    db_query = supabase.table("patient_deliveries").select("article_id").execute().data
                    if db_query:
                        current_db_arts = [r['article_id'] for r in db_query if r.get('article_id')]
                        
                    batch_payload = []
                    duplicate_logs = []
                    for idx, row in df.iterrows():
                        article_val = str(row[st.session_state.map_article]).strip() if pd.notna(row[st.session_state.map_article]) else ""
                        if article_val == "" or article_val.lower() == "nan": continue
                        if article_val in current_db_arts:
                            duplicate_logs.append({
                                "article_id": article_val, 
                                "patient_name": str(row[st.session_state.map_name]) if pd.notna(row[st.session_state.map_name]) else "", 
                                "conflict_reason": "Article ID already exists in DB"
                            })
                            continue
                            
                        phone_val = str(row[st.session_state.map_phone]).strip() if pd.notna(row[st.session_state.map_phone]) else ""
                        if phone_val and not phone_val.startswith('0') and phone_val.isdigit(): phone_val = '0' + phone_val
                        
                        rec = {
                            "article_id": article_val,
                            "patient_name": str(row[st.session_state.map_name]).strip() if pd.notna(row[st.session_state.map_name]) else "",
                            "phone_number": phone_val,
                            "address": str(row[st.session_state.map_address]).strip() if pd.notna(row[st.session_state.map_address]) else "",
                            "city": str(row[st.session_state.map_city]).strip() if pd.notna(row[st.session_state.map_city]) else "",
                            "booking_date": str(row[st.session_state.map_date]).strip() if pd.notna(row[st.session_state.map_date]) else "",
                            "mrn_no": str(row[st.session_state.map_mrn]).strip() if pd.notna(row[st.session_state.map_mrn]) else "",
                            "booking_office": str(row[st.session_state.map_bo]).strip() if pd.notna(row[st.session_state.map_bo]) else "",
                            "ingested_by": st.session_state.username,
                            "verification_status": "Pending"
                        }
                        batch_payload.append(rec)
                    
                    if batch_payload:
                        chunk_size = 500
                        for i in range(0, len(batch_payload), chunk_size):
                            supabase.table("patient_deliveries").insert(batch_payload[i:i+chunk_size]).execute()
                        st.success(f"Successfully processed {len(batch_payload)} valid records into secure database.")
                    else: st.warning("No new valid records found to push.")
                    
                    if duplicate_logs:
                        dup_df = pd.DataFrame(duplicate_logs)
                        csv_buf = io.StringIO()
                        dup_df.to_csv(csv_buf, index=False)
                        st.session_state.duplicate_log_csv = csv_buf.getvalue().encode('utf-8')
                        st.session_state.duplicate_count = len(duplicate_logs)
                        st.rerun()
                        
                except Exception as ex: st.error(f"Injection Failed: {ex}")
                
        if st.session_state.get("duplicate_log_csv") is not None:
            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander(f"⚠️ CONFLICT ALERT: {st.session_state.duplicate_count} Duplicate Articles Skipped", expanded=False):
                st.markdown("<div class='alert-3d-card'><div class='alert-3d-title'>Injection Conflicts Arrested</div><div class='alert-3d-subtitle'>These articles already exist in the central database to prevent override anomalies.</div></div>", unsafe_allow_html=True)
                st.download_button("📥 EXPORT CONFLICT LOG (.CSV)", data=st.session_state.duplicate_log_csv, file_name=f"Duplicate_Log_{datetime.date.today()}.csv", mime="text/csv", use_container_width=True)

def outbound_view():
    st.session_state.current_navigation_tab = "📞 Outbound Verification Dialler"
    st.markdown("### 🎧 Consignee Feedback Engine")
    if 'temp_search_query' not in st.session_state: st.session_state.temp_search_query = ""
    
    col_s1, col_s2, col_s3 = st.columns([1,3,1])
    with col_s2:
        search_query = st.text_input("🔍 Quick Global Search", placeholder="Article ID, Contact No, MRN, or Patient Name", value=st.session_state.temp_search_query)
        st.session_state.temp_search_query = search_query

    df = pd.DataFrame()
    with st.spinner("Synchronizing server shards..."):
        try:
            if search_query.strip():
                q = search_query.strip()
                res = supabase.table("patient_deliveries").select("*").or_(f"article_id.ilike.%{q}%, phone_number.ilike.%{q}%, patient_name.ilike.%{q}%, mrn_no.ilike.%{q}%").execute().data
            else:
                res = supabase.table("patient_deliveries").select("*").eq("verification_status", "Pending").limit(500).execute().data
            if res: df = pd.DataFrame(res)
        except Exception as e:
            st.error(f"Shards sync failed: {e}")
            return
            
    if df.empty:
        st.info("No actionable queues available matching current criteria.")
        return

    total_records = len(df)
    
    options_list = df.apply(lambda x: f"MRN: {x['mrn_no']} | ART: {x['article_id']} | NAME: {x['patient_name']} - {x['city']}", axis=1).tolist()
    
    if st.session_state.selected_profile_index >= total_records: 
        st.session_state.selected_profile_index = 0
        
    st.markdown("<hr style='margin-bottom: 25px;'>", unsafe_allow_html=True)
    
    # Custom Highlighted Selectbox for Patient Selection
    st.markdown("<div style='font-size:18px; font-weight:800; color:#a61c1c; margin-bottom:5px;'>👤 Select Patient Profile to Process:</div>", unsafe_allow_html=True)
    selected_prof_str = st.selectbox("Select Patient Profile to Process:", options_list, index=st.session_state.selected_profile_index, key="outbound_profile_select", label_visibility="collapsed")
    
    idx_selected = options_list.index(selected_prof_str)
    if idx_selected != st.session_state.selected_profile_index:
        st.session_state.selected_profile_index = idx_selected
        save_operator_state()
        st.rerun()

    active_patient = df.iloc[st.session_state.selected_profile_index].to_dict()
    raw_phone = str(active_patient.get('phone_number', '')).strip()
    if not raw_phone.startswith('0') and raw_phone.isdigit(): raw_phone = '0' + raw_phone
    
    if raw_phone: phone_display = f"<div class='big-phone-display'>☎️ {raw_phone}</div>"
    else: phone_display = "<div class='no-phone-display'>⚠️ NUMBER NOT FOUND IN FILE</div>"

    col_left, col_right = st.columns([1, 1.2], gap="large")
    
    with col_left:
        st.markdown(f"<div class='patient-card-header'>Profile Identity & Metadata</div>", unsafe_allow_html=True)
        st.markdown(phone_display, unsafe_allow_html=True)
        st.markdown(f"""
            <div class='data-card'>
                <div class='data-row'><b>Patient Name:</b> &nbsp; <span class='data-value'>{active_patient.get('patient_name', 'N/A')}</span></div>
                <div class='data-row'><b>Consignment Art ID:</b> &nbsp; <span class='data-value-alt'>{active_patient.get('article_id', 'N/A')}</span></div>
                <div class='data-row'><b>MRN ID:</b> &nbsp; {active_patient.get('mrn_no', 'N/A')}</div>
                <div class='data-row'><b>City / Location:</b> &nbsp; {active_patient.get('city', 'N/A')}</div>
                <div class='data-row'><b>Booking Origin GPO:</b> &nbsp; {active_patient.get('booking_office', 'N/A')}</div>
                <div class='data-row'><b>Dispatch Date:</b> &nbsp; {active_patient.get('booking_date', 'N/A')}</div>
                <div class='data-row'><b>Recorded Address:</b><br><span style="font-size:13px; color:#64748b; line-height: 1.4; display: block; margin-top: 5px;">{active_patient.get('address', 'N/A')}</span></div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("### 🛰️ Live Emtts Shard Request")
        if st.button("TRACK REAL-TIME STATUS", use_container_width=True):
            with st.spinner("Connecting to PakPost core..."):
                t_data, err = fetch_live_emtts_status(active_patient['article_id'])
                st.session_state.fetched_emtts_data[active_patient['article_id']] = (t_data, err)
                
        cached_emtts = st.session_state.fetched_emtts_data.get(active_patient['article_id'])
        if cached_emtts:
            t_data, err = cached_emtts
            if err or not t_data: st.error(err)
            else:
                l_entry = t_data["history"][-1]
                st.success(f"**{l_entry['status']}** at {l_entry['office']} ({l_entry['datetime']})")
                with st.expander("Expand Audit Trail History"):
                    for i, h in enumerate(reversed(t_data["history"])):
                        st.markdown(f"**{len(t_data['history'])-i}. {h['status']}**<br><span style='font-size:12px;color:gray'>{h['datetime']} - {h['office']}</span>", unsafe_allow_html=True)
                        if i < len(t_data["history"])-1: st.markdown("<hr style='margin: 5px 0px;'>", unsafe_allow_html=True)

    with col_right:
        st.markdown(f"<div class='patient-card-header'>Compliance Audit Form</div>", unsafe_allow_html=True)
        with st.form("feedback_form_engine"):
            feedback_status = st.selectbox("Current Parcel Status Verification", ["Delivered", "Undelivered", "Sent out for delivery", "RTS", "Dispatched", "Deposit", "Unresponsive/No Answer", "Wrong Number"], index=0)
            
            c1, c2 = st.columns(2)
            with c1: 
                del_date = st.date_input("Exact Delivery Date", datetime.date.today(), help="Ignore if undelivered")
            with c2: 
                received_by = st.selectbox("Handover Receiver", ["Patient Himself", "Family Member / Relative", "Neighbor", "Guard / Security", "Hospital / Clinic Staff", "Not Delivered Yet"], index=0)
                
            money_charged = st.selectbox("Were any additional delivery charges demanded by Postman?", ["No, completely free", "Yes, delivery fee demanded", "Yes, extra tip demanded", "Not Applicable"], index=0)
            
            agent_notes = st.text_area("Audit Narrative & Detailed Remarks", placeholder="Enter specific operator remarks, complaints or feedback...", height=110)
            
            submit_btn = st.form_submit_button("SUBMIT QUALITY AUDIT", use_container_width=True)
            
            if submit_btn:
                with st.spinner("Locking transaction on secure ledger..."):
                    payload = {
                        "verification_status": feedback_status,
                        "delivery_date": str(del_date),
                        "received_mode": received_by,
                        "extra_money_charged": money_charged,
                        "operator_remarks": agent_notes,
                        "operator_stamp": st.session_state.username,
                        "updated_at": datetime.datetime.now(PKT_TZ).isoformat()
                    }
                    try:
                        supabase.table("patient_deliveries").update(payload).eq("id", active_patient['id']).execute()
                        st.success("Ledger entry permanently locked.")
                        
                        if money_charged in ["Yes, delivery fee demanded", "Yes, extra tip demanded"]:
                            print_alert_payload = {
                                "patient_name": active_patient.get('patient_name', ''),
                                "mrn_no": active_patient.get('mrn_no', ''),
                                "article_id": active_patient.get('article_id', ''),
                                "phone_number": raw_phone,
                                "booking_office": active_patient.get('booking_office', ''),
                                "address": active_patient.get('address', ''),
                                "delivery_date": str(del_date),
                                "received_mode": received_by,
                                "extra_money_charged": money_charged,
                                "operator_stamp": st.session_state.username
                            }
                            open_alert_manifest(print_alert_payload)
                        else:
                            time.sleep(0.5)
                            st.session_state.selected_profile_index = min(st.session_state.selected_profile_index, total_records - 2)
                            if st.session_state.selected_profile_index < 0: st.session_state.selected_profile_index = 0
                            st.session_state.temp_search_query = ""
                            save_operator_state()
                            st.rerun()
                    except Exception as e: st.error(f"Audit failure: {e}")

def dashboard_view():
    st.session_state.current_navigation_tab = "📈 Core Analytics Server"
    st.markdown("### 🌐 Enterprise Live Metrics")
    c1, c2, c3, c4 = st.columns(4)
    with st.spinner("Executing aggregation queries on master node..."):
        try:
            today_str = datetime.datetime.now(PKT_TZ).strftime('%Y-%m-%d')
            all_data = supabase.table("patient_deliveries").select("verification_status, extra_money_charged, operator_stamp, updated_at").execute().data
            
            total_cases = len(all_data)
            delivered = sum(1 for r in all_data if r.get("verification_status") == "Delivered")
            pending = sum(1 for r in all_data if r.get("verification_status") == "Pending")
            alerts = sum(1 for r in all_data if r.get("extra_money_charged") in ["Yes, delivery fee demanded", "Yes, extra tip demanded"])
            
            today_audits = 0
            user_today_audits = 0
            for r in all_data:
                if 'updated_at' in r and r['updated_at']:
                    if today_str in r['updated_at']:
                        today_audits += 1
                        if r.get('operator_stamp') == st.session_state.username:
                            user_today_audits += 1

            c1.metric("🌍 Total Node Data", total_cases)
            c2.metric("✅ Delivered & Confirmed", delivered)
            c3.metric("⏳ Pending Action Queue", pending)
            c4.metric("🚨 Money Extortion Alerts", alerts, delta="Critical", delta_color="inverse")
            
            st.markdown("<hr>", unsafe_allow_html=True)
            sc1, sc2 = st.columns(2)
            with sc1:
                st.info(f"**Enterprise Daily Volume:** {today_audits} audits completed globally today.")
            with sc2:
                st.success(f"**Your Personal Volume:** You have cleared {user_today_audits} audits today.")
            
        except Exception as e: st.error(f"Aggregation Failed: {e}")

# Global Architecture Controller
if st.session_state.show_recovery_prompt:
    st.markdown("<div class='brand-title' style='text-align:center;'>CRASH RECOVERY CONSOLE</div>", unsafe_allow_html=True)
    recovery_view()
elif not st.session_state.logged_in:
    st.markdown("<div class='brand-title' style='text-align:center;'>PAKISTAN POST | ENTERPRISE PORTAL</div>", unsafe_allow_html=True)
    login_view()
else:
    with st.sidebar:
        st.markdown("<div class='sb-headline-custom'>SHC & PAKPOST CORE</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='sb-login-label'>Terminal Operator:</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='sb-username-display'>{st.session_state.full_name}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='sb-privilege-label'>Clearance Level: <span>{st.session_state.role.upper()}</span></div>", unsafe_allow_html=True)
        
        st.markdown("<hr style='margin: 15px 0px; border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
        
        if st.session_state.role == "admin":
            if st.button("📊 Admin Ingestion Engine", use_container_width=True):
                st.session_state.current_navigation_tab = "📊 Administrative Ingestion Engine"
                if "temp_search_query" in st.session_state: st.session_state.temp_search_query = ""
                st.query_params["tab"] = st.session_state.current_navigation_tab
                save_operator_state()
                st.rerun()
                
        if st.button("📞 Outbound Verifier", use_container_width=True):
            st.session_state.current_navigation_tab = "📞 Outbound Verification Dialler"
            st.session_state.selected_profile_index = 0
            if "temp_search_query" in st.session_state: st.session_state.temp_search_query = ""
            st.query_params["tab"] = st.session_state.current_navigation_tab
            save_operator_state()
            st.rerun()
            
        if st.button("📈 Global Metric Dashboard", use_container_width=True):
            st.session_state.current_navigation_tab = "📈 Core Analytics Server"
            if "temp_search_query" in st.session_state: st.session_state.temp_search_query = ""
            st.query_params["tab"] = st.session_state.current_navigation_tab
            save_operator_state()
            st.rerun()

        st.markdown("<hr style='margin: 15px 0px; border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
        
        if st.button("📅 Operator Analytics", use_container_width=True): user_stats_dialog()
        
        st.markdown("<div class='password-btn-anchor'></div>", unsafe_allow_html=True)
        if st.button("🔐 Renew Secure Password", use_container_width=True): change_password_dialog()
        
        st.markdown("<div class='terminate-btn-anchor'></div>", unsafe_allow_html=True)
        if st.button("🔴 Terminate Safe Session", use_container_width=True):
            st.session_state.logged_in = False
            st.query_params.clear()
            st.rerun()
            
    st.markdown(f"<div class='brand-title'>PAKISTAN POST & SHC | MEDICAL LOGISTICS HUB</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='brand-subtitle'>Currently Operational View: {st.session_state.current_navigation_tab or 'Standby Mode'}</div>", unsafe_allow_html=True)
    
    if st.session_state.current_navigation_tab == "📊 Administrative Ingestion Engine" and st.session_state.role == "admin": ingestion_view()
    elif st.session_state.current_navigation_tab == "📞 Outbound Verification Dialler": outbound_view()
    elif st.session_state.current_navigation_tab == "📈 Core Analytics Server": dashboard_view()
    else:
        st.info("Terminal active and awaiting operational command. Select an engine from the left panel.")
