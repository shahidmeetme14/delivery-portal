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
import sqlite3
import logging

# Setup Local Logging for File
logging.basicConfig(filename='local_logs.txt', level=logging.INFO, format='%(asctime)s - %(message)s')

# 🇵🇰 Pakistan Standard Time (PKT) Setup - No external libraries needed
PKT_TZ = datetime.timezone(datetime.timedelta(hours=5))

# ==========================================
# 🛠️ LOCAL LAPTOP DATABASE ENGINE SETUP
# ==========================================
def init_local_db():
    try:
        conn = sqlite3.connect("local_archive.db")
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS patient_deliveries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT, article_id TEXT, patient_name TEXT, 
            phone_number TEXT, booking_date TEXT, address TEXT, 
            patient_city TEXT, mrn_no TEXT, booking_office TEXT, status TEXT
        )''')
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Error initializing local DB: {e}")

init_local_db()

def insert_local_db(table_name, records):
    if not records: return
    conn = sqlite3.connect("local_archive.db")
    c = conn.cursor()
    for row in records:
        # Check and add missing columns dynamically (Auto-Column Creation)
        c.execute(f"PRAGMA table_info({table_name})")
        existing_cols = [col[1] for col in c.fetchall()]
        for key in row.keys():
            if key not in existing_cols:
                c.execute(f"ALTER TABLE {table_name} ADD COLUMN {key} TEXT")
        
        keys = ', '.join(row.keys())
        placeholders = ', '.join(['?'] * len(row))
        c.execute(f"INSERT INTO {table_name} ({keys}) VALUES ({placeholders})", tuple(row.values()))
    conn.commit()
    conn.close()

def update_local_db(table_name, payload, record_id):
    conn = sqlite3.connect("local_archive.db")
    c = conn.cursor()
    c.execute(f"PRAGMA table_info({table_name})")
    existing_cols = [col[1] for col in c.fetchall()]
    for key in payload.keys():
        if key not in existing_cols:
            c.execute(f"ALTER TABLE {table_name} ADD COLUMN {key} TEXT")
            
    set_clause = ', '.join([f"{k} = ?" for k in payload.keys()])
    values = list(payload.values())
    
    if record_id:
         values.append(record_id)
         c.execute(f"UPDATE {table_name} SET {set_clause} WHERE id = ?", values)
    else:
         keys = ', '.join(payload.keys())
         placeholders = ', '.join(['?'] * len(payload))
         c.execute(f"INSERT INTO {table_name} ({keys}) VALUES ({placeholders})", tuple(payload.values()))
         
    conn.commit()
    conn.close()

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
                
            # Log auto-login credentials to user_logins table
            try:
                supabase.table("user_logins").insert({
                    "username": st.session_state.username,
                    "full_name": st.session_state.full_name,
                    "role": st.session_state.role,
                    "login_time": datetime.datetime.now(PKT_TZ).strftime('%Y-%m-%d %I:%M:%S %p'),
                    "created_at": datetime.datetime.now(PKT_TZ).isoformat()
                }).execute()
            except Exception:
                pass
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
if "master_manifest_cache" not in st.session_state: st.session_state["master_manifest_cache"] = None

# Initialize Column Mappings Memory
mapping_keys = ["map_article", "map_name", "map_city", "map_phone", "map_date", "map_mrn", "map_address", "map_bo", "map_dup", "map_tx", "map_db_col"]
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

generic_expander_highlight_css = """
div[data-testid="stExpander"] {
    border: 2px solid rgba(212, 175, 55, 0.4) !important;
    border-radius: 8px !important;
    background-color: rgba(212, 175, 55, 0.05) !important;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
    margin-bottom: 20px !important;
    transition: all 0.3s ease !important;
}

div[data-testid="stExpander"] button[data-testid="stExpanderHeader"] p {
    font-weight: 800 !important;
    color: #5c1414 !important; 
}

div[data-testid="stExpander"] button[data-testid="stExpanderHeader"] p span {
    color: #5c1414 !important;
}

div[data-testid="stExpander"] button[data-testid="stExpanderHeader"] [data-testid="stExpanderToggleIcon"] {
    color: #d4af37 !important; 
}

div[data-testid="stExpander"] > div[data-testid="stExpanderBody"] {
    padding-top: 10px !important;
    background-color: transparent !important;
}
"""

st.markdown(f"""
    <style>
    div[data-testid="stToolbar"], #MainMenu, footer, header,
    [data-testid="stHeader"], [data-testid="stDecoration"],
    [data-testid="stStatusWidget"], [data-testid="stActionElements"],
    .stDeployButton, .stAppDeployButton, button[kind="header"],
    [data-testid="stViewerBadge"], div[class^="viewerBadge"], div[class*="viewerBadge"],
    .viewerBadge_container__1616G, a[href*="streamlit.io"],
    div[data-testid="stBottom"], div[data-testid="stBottomBlockContainer"] {{
        display: none !important; visibility: hidden !important; opacity: 0 !important;
        height: 0px !important; width: 0px !important;
    }}
    
    {generic_expander_highlight_css} 
    {sidebar_css_rule}
    
    .stApp {{ background-color: #fdfcf9; }}
    .brand-title {{ color: #a61c1c; font-weight: 800; font-size: 2.1rem; margin-bottom: 2px; }}
    .brand-subtitle {{ color: #5c1414; font-size: 1.05rem; margin-bottom: 25px; font-weight: 600; border-left: 4px solid #d4af37; padding-left: 12px; }}
    
    .alert-3d-card {{
        background: linear-gradient(145deg, #ffffff, #fdfbf7);
        border-radius: 12px;
        box-shadow: 6px 6px 15px rgba(0,0,0,0.08), -6px -6px 15px rgba(255,255,255,0.8);
        border-left: 6px solid #cc2424;
        padding: 18px 22px; margin-bottom: 12px;
        transition: all 0.3s ease;
    }}
    .alert-3d-title {{ font-size: 19px; font-weight: 800; color: #1e293b; margin-bottom: 5px; }}
    .alert-3d-subtitle {{ font-size: 14px; color: #64748b; font-weight: 500; }}
    .alert-3d-badge {{ background: #fee2e2; color: #dc2626; padding: 5px 12px; border-radius: 20px; font-weight: 700; font-size: 13px; border: 1px solid #fecaca; }}

    div[data-testid="stForm"], .pyqt-panel {{
        background: #ffffff !important; border-radius: 8px !important;
        border: 1px solid #d1c2c2 !important; box-shadow: 0 6px 12px -2px rgba(166,28,28,0.04) !important;
        padding: 30px !important;
    }}
    
    div[data-testid="stForm"] small, [data-testid="InputInstructions"] {{ display: none !important; }}
    
    div.stButton > button, div.stDownloadButton > button {{
        background: linear-gradient(180deg, #cc2424 0%, #a61c1c 100%) !important;
        color: #ffffff !important; border: 1px solid #801414 !important;
        border-bottom: 4px solid #590d0d !important; border-radius: 6px !important;
        padding: 8px 24px !important; font-weight: 700;
        box-shadow: 0px 4px 8px rgba(0,0,0,0.12) !important; transition: all 0.1s ease;
    }}
    
    section[data-testid="stSidebar"] div.stButton > button {{
        background: rgba(255, 255, 255, 0.05) !important; color: #ffffff !important;
        border: 2px solid rgba(212, 175, 55, 0.5) !important;
        border-bottom: 5px solid rgba(179, 146, 46, 0.9) !important;
        border-radius: 10px !important; padding: 10px 20px !important;
        backdrop-filter: blur(12px) !important; -webkit-backdrop-filter: blur(12px) !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37), inset 0 1px 2px rgba(255,255,255,0.1) !important;
        font-weight: 700 !important; text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.9) !important;
    }}
    
    div:has(> .password-btn-anchor) + div button, div:has(.password-btn-anchor) + div button {{
        background: linear-gradient(180deg, #ffd700 0%, #b8860b 100%) !important;
        color: #000000 !important; border: 2px solid rgba(255, 255, 255, 0.6) !important;
        border-bottom: 5px solid #8b6508 !important; border-radius: 10px !important; font-weight: 800 !important;
    }}
    
    div:has(> .terminate-btn-anchor) + div button, div:has(.terminate-btn-anchor) + div button {{
        background: linear-gradient(180deg, #ff4d4d 0%, #c31414 100%) !important;
        color: #ffffff !important; border: 2px solid rgba(255, 255, 255, 0.4) !important;
        border-bottom: 5px solid #800a0a !important; border-radius: 10px !important; font-weight: 800 !important;
    }}
    
    div[data-baseweb="select"] > div, div[data-testid="stSelectbox"] div[data-baseweb="select"],
    div[data-testid="stDateInput"] > div, div[data-testid="stTextInput"] > div,
    div[data-testid="stNumberInput"] > div, div[data-testid="stTextArea"] > div {{
        background: linear-gradient(180deg, #ffffff 0%, #f1f5f9 100%) !important;
        border: 1px solid #94a3b8 !important; border-bottom: 4px solid #64748b !important;
        border-radius: 8px !important;
    }}
    
    div[data-baseweb="select"] > div > div {{ background-color: transparent !important; }}
    
    div[data-baseweb="select"] *, div[data-testid="stDateInput"] input,
    div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea {{
        color: #1e293b !important; font-weight: 600 !important;
    }}
    
    [data-testid="column"]:nth-of-type(2) {{
        background: linear-gradient(135deg, #ffffff 0%, #fdfbf7 100%); border: 1px solid #e2e8f0;
        border-top: 4px solid #d4af37; border-radius: 10px; padding: 22px; box-shadow: 0px 8px 20px -5px rgba(0,0,0,0.06);
    }}

    .big-phone-display {{ 
        font-size: 22px !important; font-weight: 800 !important; color: #ffffff !important; 
        background: linear-gradient(180deg, #d4af37 0%, #b3922e 100%) !important; 
        padding: 6px 12px; border-radius: 4px; text-align: center; border: 1px solid #b3922e; border-bottom: 3px solid #8c7120;
    }}
    
    .no-phone-display {{
        font-size: 22px !important; font-weight: 700 !important; color: #ffffff !important; 
        background: linear-gradient(180deg, #ef4444 0%, #dc2626 100%) !important; 
        padding: 6px 12px; border-radius: 4px; text-align: center; border: 1px solid #b91c1c; border-bottom: 3px solid #991b1b;
    }}
    
    .data-card {{ background: #ffffff; padding: 18px; border-radius: 8px; border: 1px solid #cbd5e1; }}
    .data-card .data-row {{ margin-bottom: 12px; font-size: 15px; color: #334155; }}
    .data-card .data-value {{ font-size: 19px !important; font-weight: 700 !important; color: #a61c1c; background: #fff5f5; padding: 2px 8px; border-radius: 4px; border: 1px solid #fecaca; display: inline-block; }}
    .data-card .data-value-alt {{ font-size: 19px !important; font-weight: 700 !important; color: #b45309; font-family: monospace; background: #fffbeb; padding: 2px 8px; border-radius: 4px; border: 1px solid #fef3c7; display: inline-block; }}
    .patient-card-header {{ font-size: 22px !important; font-weight: 700 !important; color: #a61c1c; border-left: 5px solid #d4af37; padding-left: 10px; margin-bottom: 15px; }}
    
    section[data-testid="stSidebar"] .sb-headline-custom {{ font-size: 20px !important; font-weight: bold !important; color: #00E5FF !important; margin-bottom: 15px; }}
    section[data-testid="stSidebar"] .sb-login-label {{ margin-top: 15px; color: #cbd5e1 !important; font-size: 14px; }}
    section[data-testid="stSidebar"] .sb-username-display {{ font-size: 18px !important; font-weight: bold !important; color: #d4af37 !important; margin-bottom: 10px; }}
    section[data-testid="stSidebar"] .sb-privilege-label {{ margin-top: 10px; color: #cbd5e1 !important; font-size: 14px; }}
    section[data-testid="stSidebar"] .sb-privilege-label span {{ color: #39ff14 !important; font-weight: bold !important; text-shadow: 0 0 5px #39ff14, 0 0 10px #39ff14 !important; }}
    
    /* 🖨️ Absolute Print Media Optimization with WATERMARK & COMPACT MARGINS */
    @media print {{
        @page {{ size: A4 portrait !important; margin: 0mm !important; }}
        html, body {{ height: 100% !important; margin: 0 !important; padding: 0 !important; overflow: hidden !important; background: #ffffff !important; -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }}
        body * {{ visibility: hidden !important; }}
        [data-testid="stSidebar"], [data-testid="stHeader"], [data-testid="stToolbar"], header, footer, iframe, .stElementContainer:has(iframe), button, .custom-print-btn, [data-testid="stBottom"], div[data-testid="stBottomBlockContainer"] {{ display: none !important; visibility: hidden !important; opacity: 0 !important; }}
        
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], .block-container {{
            position: relative !important; top: 0 !important; left: 0 !important;
            height: 100% !important; overflow: hidden !important; padding: 0 !important; margin: 0 !important; border: none !important;
        }}

        .watermark-print {{
            position: fixed !important;
            top: 45% !important;
            left: 50% !important;
            transform: translate(-50%, -50%) !important;
            font-size: 65px !important;
            font-weight: 900 !important;
            color: rgba(180, 180, 180, 0.15) !important;
            z-index: -999 !important;
            white-space: nowrap !important;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
        }}

        .print-manifest-card {{ 
            visibility: visible !important; position: fixed !important; 
            top: 5mm !important; /* Brought Upwards */
            left: 15mm !important; right: 15mm !important; bottom: 15mm !important; 
            width: calc(100% - 30mm) !important; height: calc(100% - 20mm) !important; 
            box-sizing: border-box !important; margin: 0 !important; 
            padding: 10px 20px !important; /* Compact Padding */
            border: 3px double #a61c1c !important; border-radius: 0px !important; 
            background: #ffffff !important; background-color: #ffffff !important; 
            page-break-inside: avoid !important; z-index: 99999999 !important; 
            display: flex !important; flex-direction: column !important;
            justify-content: flex-start !important; overflow: hidden !important;
        }}

        .print-manifest-card * {{ visibility: visible !important; color: #000000 !important; background-color: transparent !important; box-shadow: none !important; text-shadow: none !important; }}
        .print-manifest-card table {{ width: 100% !important; display: table !important; border-collapse: collapse !important; margin-top: 5px !important; }}
        .print-manifest-card tr {{ display: table-row !important; page-break-inside: avoid !important; }}
        .print-manifest-card td, .print-manifest-card th {{ display: table-cell !important; padding: 6px 8px !important; font-size: 13px !important; color: #000000 !important; border-bottom: 1px solid #cbd5e1 !important; }}
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
    
    with st.spinner("Connecting securely to PakPost server..."):
        data, err = fetch_live_emtts_status(alert_data['article_id'])
        
    if err or not data:
        emtts_status_html = f"<span style='color: #dc2626; font-weight: bold;'>⚠️ {err}</span>"
    else:
        last_entry = data["history"][-1]
        emtts_status_html = f"""
        <div style="font-weight: bold; color: #1e293b; font-size: 14px;">{last_entry["status"]}</div>
        <div style="font-size: 11px; color: #475569; margin-top: 2px;">📍 Office: {last_entry['office']} | 🕒 {last_entry['datetime']}</div>
        """
        
    print_operator = alert_data.get('operator_stamp', 'System Alert Console')
    extra_charge = alert_data.get('extra_money_charged', 'Yes')
    print_status_detail = f"""
    <b style="color: green;">Delivered</b><br>
    <span style="font-size: 12px; font-weight: 600; color: #334155;">
        • Date: {alert_data.get('delivery_date', 'N/A')}<br>
        • Mode: {alert_data.get('received_mode', 'N/A')}<br>
        • Extra Money Requested: <b style="color: #dc2626">{extra_charge}</b>
    </span>
    """

    raw_phone = str(alert_data.get('phone_number', '')).strip()
    if not raw_phone.startswith('0') and raw_phone.isdigit(): raw_phone = '0' + raw_phone
        
    current_pkt_time = datetime.datetime.now(PKT_TZ).strftime('%Y-%m-%d %I:%M:%S %p')
        
    st.markdown(f"""
        <div class="print-manifest-card">
            <div class="watermark-print">SHC Cell Lahore GPO</div>
            <div style="text-align: center; border-bottom: 2px solid #a61c1c; padding-bottom: 2px; margin-bottom: 4px;">
                <img src="https://www.pakpost.gov.pk/images/New%20Logo%20PPO.jpg" style="height: 45px; margin-bottom: 0px;" alt="Pak Post Logo">
                <h2 style="margin: 0; color: #a61c1c; font-size: 18px; font-weight: 800;">PAKISTAN POST | PATIENT FEEDBACK MANIFEST</h2>
                <p style="margin: 0; color: #1e293b; font-size: 14px; font-weight: 700;">OFFICE OF THE CHIEF POSTMASTER LAHORE GPO</p>
                <p style="margin: 0; color: #475569; font-size: 11px; font-weight: 600;">Patient Feedback & Medicine Delivery Audit Certificate</p>
            </div>
            <table style="width: 100%; border-collapse: collapse; font-size: 13px; color: #000000;">
                <tr><td style="padding: 6px; font-weight: bold; width: 35%; border-bottom: 1px solid #e2e8f0;">Patient Name:</td><td style="padding: 6px; border-bottom: 1px solid #e2e8f0;">{alert_data.get('patient_name', 'N/A')}</td></tr>
                <tr><td style="padding: 6px; font-weight: bold; border-bottom: 1px solid #e2e8f0;">MRN Number:</td><td style="padding: 6px; border-bottom: 1px solid #e2e8f0;">{alert_data.get('mrn_no', 'N/A')}</td></tr>
                <tr><td style="padding: 6px; font-weight: bold; border-bottom: 1px solid #e2e8f0;">Consignment ID (Article):</td><td style="padding: 6px; border-bottom: 1px solid #e2e8f0; font-family: monospace; font-weight: 700; color: #a61c1c;">{alert_data['article_id']}</td></tr>
                <tr><td style="padding: 6px; font-weight: bold; border-bottom: 1px solid #e2e8f0;">Contact Number:</td><td style="padding: 6px; border-bottom: 1px solid #e2e8f0;">{raw_phone if raw_phone else 'N/A'}</td></tr>
                <tr><td style="padding: 6px; font-weight: bold; border-bottom: 1px solid #e2e8f0;">Booking GPO Station:</td><td style="padding: 6px; border-bottom: 1px solid #e2e8f0;">{alert_data.get('booking_office', 'N/A')}</td></tr>
                <tr><td style="padding: 6px; font-weight: bold; border-bottom: 1px solid #e2e8f0;">Mailing Address:</td><td style="padding: 6px; border-bottom: 1px solid #e2e8f0;">{alert_data.get('address', 'N/A')}</td></tr>
                <tr><td style="padding: 6px; font-weight: bold; border-bottom: 1px solid #e2e8f0; vertical-align: top;">EMTTS Tracking Status:</td><td style="padding: 6px; border-bottom: 1px solid #e2e8f0; vertical-align: top;">{emtts_status_html}</td></tr>
                <tr><td style="padding: 6px; font-weight: bold; border-bottom: 1px solid #e2e8f0; vertical-align: top;">Verification Status:</td><td style="padding: 6px; border-bottom: 1px solid #e2e8f0;">{print_status_detail}</td></tr>
            </table>
            <div style="margin-top: 15px; display: flex; justify-content: space-between; align-items: flex-end; font-size: 11px; border-top: 1px solid #cbd5e1; padding-top: 5px; color: #000000;">
                <div>
                    <b>Verified By (Operator ID):</b> {print_operator}<br>
                    <span style="color: #475569;">Timestamp: {current_pkt_time} (PKT)</span>
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
                                try:
                                    supabase.table("user_logins").insert({
                                        "username": ud[0]["username"],
                                        "full_name": ud[0]["full_name"],
                                        "role": ud[0]["role"],
                                        "login_time": datetime.datetime.now(PKT_TZ).strftime('%Y-%m-%d %I:%M:%S %p'),
                                        "created_at": datetime.datetime.now(PKT_TZ).isoformat()
                                    }).execute()
                                except Exception:
                                    pass
                                    
                                recovery_data = fetch_operator_state(ud[0]["username"])
                                
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
    
    # NEW: Ask where to save data
    db_target = st.radio("📂 Select Target Database for Upload:", ["Supabase Cloud (Current Year)", "Local Laptop DB (Archive)"], help="Data duplication will be checked across BOTH databases.")
    
    source_file = st.file_uploader("Upload Medicine Article Sheet", type=["xlsx", "csv"], key="bulk_uploader_main")
    
    if source_file is not None:
        file_key = f"cached_df_{source_file.name}_{source_file.size}"
        if file_key not in st.session_state:
            if source_file.name.endswith('.xlsx'):
                df = pd.read_excel(source_file, dtype=str)
            else:
                df = pd.read_csv(source_file, low_memory=False, dtype=str)
            
            df = df.fillna("")
            df = df.replace(to_replace=r'^[Nn][Aa][Nn]$', value='', regex=True)
            st.session_state[file_key] = df
        else: 
            df = st.session_state[file_key]
        
        db_cols = []
        try:
            temp_res = supabase.table("patient_deliveries").select("*").limit(1).execute()
            if temp_res.data:
                db_cols = list(temp_res.data[0].keys())
            else:
                db_cols = ["transaction_id", "article_id", "patient_name", "phone_number", "booking_date", "address", "patient_city", "mrn_no", "booking_office", "status"]
        except Exception:
            db_cols = ["transaction_id", "article_id", "patient_name", "phone_number", "booking_date", "address", "patient_city", "mrn_no", "booking_office", "status"]

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
            c_tx = st.selectbox("Transaction No Column:", df.columns, index=calculate_mapped_index(df.columns, "map_tx", "Transaction No"))
            c_dup = st.selectbox("Duplication Log Column:", df.columns, index=calculate_mapped_index(df.columns, "map_dup", "Duplicate"))

        st.markdown("---")
        st.markdown("#### ⚙️ Dynamic Unique Key & Deduplication Selection")
        dup_col1, dup_col2 = st.columns(2)
        with dup_col1:
            excel_dup_col = st.selectbox("📁 Select Excel Column for Unique Duplication Check:", df.columns, index=df.columns.get_loc(c_tx) if c_tx in df.columns else 0)
        with dup_col2:
            db_dup_col = st.selectbox("🗄️ Match with Database Table Column:", db_cols, index=db_cols.index("transaction_id") if "transaction_id" in db_cols else (db_cols.index("article_id") if "article_id" in db_cols else 0))

        if st.button("🚀 Push Verified Records to Database", use_container_width=True):
            ui_blocker = st.empty()
            ui_blocker.markdown("<style> [data-testid='stSidebar'], [data-testid='stHeader'] { pointer-events: none !important; opacity: 0.6 !important; filter: blur(0.5px) !important; } </style>", unsafe_allow_html=True)
            
            status_progress_text = st.empty()
            progress_bar_control = st.progress(0)
            
            raw_unique_vals = df[excel_dup_col].astype(str).str.strip().unique().tolist()
            raw_unique_vals = [x for x in raw_unique_vals if x not in ["", "nan", "NaN", "None"]]
            
            existing_db_records = set()
            status_progress_text.text(f"Checking Cloud Supabase for duplicates... (20% Complete)")
            progress_bar_control.progress(20)
            
            # Check Supabase
            check_batch_size = 10000
            for k in range(0, len(raw_unique_vals), check_batch_size):
                sub_batch = raw_unique_vals[k:k+check_batch_size]
                try:
                    db_res = supabase.table("patient_deliveries").select(db_dup_col).in_(db_dup_col, sub_batch).execute().data
                    for r in db_res:
                        if db_dup_col in r:
                            existing_db_records.add(str(r[db_dup_col]).strip())
                except Exception as e:
                    pass

            # Check Local DB
            status_progress_text.text(f"Checking Local Laptop DB for duplicates... (40% Complete)")
            progress_bar_control.progress(40)
            try:
                conn = sqlite3.connect("local_archive.db")
                c = conn.cursor()
                for k in range(0, len(raw_unique_vals), check_batch_size):
                    sub_batch = raw_unique_vals[k:k+check_batch_size]
                    placeholders = ','.join(['?'] * len(sub_batch))
                    try:
                        c.execute(f"SELECT {db_dup_col} FROM patient_deliveries WHERE {db_dup_col} IN ({placeholders})", sub_batch)
                        for row in c.fetchall():
                            existing_db_records.add(str(row[0]).strip())
                    except Exception: pass
                conn.close()
            except Exception: pass

            status_progress_text.text("Analyzing spreadsheet matrix structures... (60% Complete)")
            progress_bar_control.progress(60)
            
            uploaded_records_df = pd.DataFrame({
                "transaction_id": df[c_tx].astype(str).str.strip() if c_tx in df.columns else "",
                "article_id": df[c_article].astype(str).str.strip(),
                "patient_name": df[c_name].astype(str).str.strip(),
                "phone_number": df[c_phone].astype(str).str.strip(),
                "booking_date": df[c_date].astype(str).str.slice(0, 10),
                "address": df[c_address].astype(str).str.strip(),
                "patient_city": df[c_city].astype(str).str.strip(),
                "mrn_no": df[c_mrn].astype(str).str.strip(),
                "booking_office": df[c_bo].astype(str).str.strip() if c_bo in df.columns else "Lahore GPO"
            })
            
            uploaded_records_df["_dup_check_col_"] = df[excel_dup_col].astype(str).str.strip()
            uploaded_records_df = uploaded_records_df.fillna("")
            uploaded_records_df = uploaded_records_df.replace(to_replace=r'^[Nn][Aa][Nn]$', value='', regex=True)
            total_input_count = len(uploaded_records_df)

            status_progress_text.text("Filtering out duplicates... (70% Complete)")
            progress_bar_control.progress(70)
            
            is_duplicate_in_db = uploaded_records_df["_dup_check_col_"].isin(existing_db_records) | (uploaded_records_df["_dup_check_col_"] == "")
            clean_unique_records = uploaded_records_df[~is_duplicate_in_db].copy()
            clean_unique_records = clean_unique_records.drop_duplicates(subset=["_dup_check_col_"])
            
            if "_dup_check_col_" in clean_unique_records.columns:
                clean_unique_records = clean_unique_records.drop(columns=["_dup_check_col_"])
                
            total_duplicates_cleared = total_input_count - len(clean_unique_records)
            records_to_insert = clean_unique_records.to_dict(orient="records")
            
            try:
                if len(records_to_insert) > 0:
                    if db_target == "Supabase Cloud (Current Year)":
                        chunk_size = 3000
                        for i in range(0, len(records_to_insert), chunk_size):
                            chunk = records_to_insert[i:i+chunk_size]
                            supabase.table("patient_deliveries").insert(chunk).execute()
                    else:
                        insert_local_db("patient_deliveries", records_to_insert)

                st.session_state["master_manifest_cache"] = None
                status_progress_text.empty()
                progress_bar_control.empty()
                ui_blocker.empty()
                st.success(f"🟢 Success! Out of {total_input_count} records, {total_duplicates_cleared} duplicates were safely skipped. Clean unique records ({len(records_to_insert)}) have been saved to '{db_target}'.")
            except Exception as store_ex:
                ui_blocker.empty()
                st.error(f"Failed to synchronize database: {store_ex}")

    st.markdown("<br><hr style='border-top: 2px solid #cbd5e1;'><br>", unsafe_allow_html=True)
    st.markdown("### 🔍 Cloud Database Matching Engine (Admin Only)")
    st.info("Upload a file here to cross-match with the existing cloud database. This will generate a CSV report with matching status.")
    
    match_file = st.file_uploader("Upload File for Matching", type=["xlsx", "csv"], key="match_uploader_engine")
    
    if match_file is not None:
        try:
            df_match = pd.read_excel(match_file, dtype=str) if match_file.name.endswith('.xlsx') else pd.read_csv(match_file, low_memory=False, dtype=str)
            df_match = df_match.fillna("").replace(to_replace=r'^[Nn][Aa][Nn]$', value='', regex=True)
            
            with st.spinner("Fetching cloud database for matching..."):
                if "master_manifest_cache" not in st.session_state or st.session_state["master_manifest_cache"] is None:
                    try:
                        db_bytes = supabase.table("patient_deliveries").select("*").execute().data
                        if db_bytes:
                            df_cloud = pd.DataFrame(db_bytes).astype(str).fillna("").replace(to_replace=r'^[Nn][Aa][Nn]$', value='', regex=True)
                        else:
                            df_cloud = pd.DataFrame(columns=["transaction_id", "article_id", "patient_name", "phone_number", "booking_date", "address", "patient_city", "mrn_no", "booking_office", "status"])
                        st.session_state["master_manifest_cache"] = df_cloud
                    except Exception:
                        df_cloud = pd.DataFrame()
                else:
                    df_cloud = st.session_state["master_manifest_cache"]
            
            if df_cloud.empty:
                st.error("Cloud database is currently empty. Nothing to match against.")
            else:
                st.markdown("#### 🔗 Define Match Parameters")
                mc_col1, mc_col2 = st.columns(2)
                with mc_col1:
                    upload_col1 = st.selectbox("Uploaded File Field:", df_match.columns, key="uc1")
                with mc_col2:
                    cloud_col1 = st.selectbox("Cloud Database Field:", df_cloud.columns, key="cc1")
                
                if st.button("⚙️ Start Secure Matching Process", use_container_width=True):
                    ui_blocker_match = st.empty()
                    ui_blocker_match.markdown("<style> [data-testid='stSidebar'], [data-testid='stHeader'] { pointer-events: none !important; opacity: 0.6 !important; filter: blur(0.5px) !important; } </style>", unsafe_allow_html=True)
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    matched_rows = []
                    unmatched_rows = []
                    
                    total_rows = len(df_match)
                    for i, row in df_match.iterrows():
                        perc = int(((i + 1) / total_rows) * 100)
                        if i % 100 == 0 or perc == 100: 
                            progress_bar.progress(perc)
                            status_text.text(f"Processing and matching records... {perc}% Completed")
                        
                        val1 = str(row[upload_col1]).strip().lower()
                        cloud_match = df_cloud[df_cloud[cloud_col1].astype(str).str.strip().str.lower() == val1]
                        
                        if not cloud_match.empty:
                            matched_rows.append(cloud_match.iloc[0].to_dict())
                        else:
                            unmatched_dict = {col: "" for col in df_cloud.columns}
                            unmatched_dict[cloud_col1] = str(row[upload_col1])
                            unmatched_dict['Match_Status'] = 'Unmatched'
                            unmatched_rows.append(unmatched_dict)
                            
                    status_text.text("✅ Backend Matching Engine Completed!")
                    ui_blocker_match.empty()
                    st.success(f"📊 Summary Dashboard:\n- **Total Articles Scanned:** {total_rows}\n- **Successfully Matched:** {len(matched_rows)}\n- **Not Found (Unmatched):** {len(unmatched_rows)}")
                    
                    if matched_rows or unmatched_rows:
                        df_matched_export = pd.DataFrame(matched_rows)
                        df_unmatched_export = pd.DataFrame(unmatched_rows)
                        
                        if 'Match_Status' not in df_matched_export.columns and not df_matched_export.empty:
                            df_matched_export['Match_Status'] = 'Matched'
                            
                        final_export_df = pd.concat([df_matched_export, df_unmatched_export], ignore_index=True)
                        
                        csv_buffer = io.StringIO()
                        final_export_df.to_csv(csv_buffer, index=False)
                        st.download_button(
                            label="📥 Export Result & Download CSV File",
                            data=csv_buffer.getvalue().encode('utf-8'),
                            file_name=f"Cloud_Match_Results_{datetime.datetime.now().strftime('%d%m%Y_%H%M')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                        
            if st.button("🗑️ Clear Matching File & Memory", use_container_width=True):
                st.rerun()
        except Exception as e:
            st.error(f"Error reading or processing file: {e}")

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
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e: st.error(f"Error: {e}")
                
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("### 👥 Active Operators & Security Access Logs")
    col_u, col_l = st.columns(2)
    
    with col_u:
        st.markdown("#### 👤 Registered User Profiles")
        try:
            users_res = supabase.table("app_users").select("*").execute().data
            if users_res:
                df_users = pd.DataFrame(users_res)
                display_cols = [c for c in ["username", "full_name", "role"] if c in df_users.columns]
                st.dataframe(df_users[display_cols], use_container_width=True)
        except Exception as e:
            pass
            
    with col_l:
        st.markdown("#### 🕒 Real-time Session Login Logs")
        try:
            try:
                logs_res = supabase.table("user_logins").select("*").order("created_at", desc=True).limit(50).execute().data
            except Exception:
                logs_res = supabase.table("user_logins").select("*").limit(50).execute().data
                
            if logs_res:
                df_logs = pd.DataFrame(logs_res)
                if "created_at" in df_logs.columns:
                    df_logs = df_logs.sort_values(by="created_at", ascending=False)
                display_cols_logs = [c for c in ["username", "full_name", "role", "login_time", "created_at"] if c in df_logs.columns]
                st.dataframe(df_logs[display_cols_logs], use_container_width=True)
        except Exception as e:
            pass

def communications_view():
    st.session_state.current_navigation_tab = "📞 Outbound Communications Desk"
    st.markdown("### 📞 Outbound Communications Desk")
    
    query_date = st.date_input("Filter Manifest Records by Booking Date (Overridden by Search):", value=None)
    dynamic_headings = ["patient_name", "article_id", "mrn_no", "phone_number", "address", "booking_office", "transaction_id"]
    
    try:
        recent_offices_query = supabase.table("patient_deliveries").select("booking_office").limit(1000).execute().data
        unique_offices = sorted(list(set([str(r.get('booking_office', 'Lahore GPO')).strip() for r in recent_offices_query if r.get('booking_office')])))
        if "Lahore GPO" not in unique_offices: unique_offices.append("Lahore GPO")
    except:
        unique_offices = ["Lahore GPO"]
    unique_offices.insert(0, "All Offices")
    
    filter_col1, filter_col2, filter_col3 = st.columns([1.5, 1.5, 1.5])
    with filter_col1: selected_office = st.selectbox("🏥 Filter by Booking Office:", unique_offices)
    with filter_col2: search_category = st.selectbox("🔎 Search By Heading:", ["All Fields"] + dynamic_headings)
    with filter_col3: search_term = st.text_input("Enter detail to search (Live Database Search):", placeholder="Type patient detail here...").strip().lower()
    
    final_recs = []
    if not query_date and not search_term:
        st.info("📅 Please select a Date from above or use the Search bar to load patient records.")
    else:
        with st.spinner("Processing live database query across Cloud & Local DB..."):
            # 1. Fetch from Supabase
            try:
                query = supabase.table("patient_deliveries").select("*")
                if search_term:
                    if search_category == "All Fields":
                        or_cond = f"patient_name.ilike.%{search_term}%,article_id.ilike.%{search_term}%,mrn_no.ilike.%{search_term}%,phone_number.ilike.%{search_term}%,transaction_id.ilike.%{search_term}%"
                        query = query.or_(or_cond)
                    else:
                        query = query.ilike(search_category, f"%{search_term}%")
                    if selected_office != "All Offices":
                        query = query.eq("booking_office", selected_office)
                else:
                    if query_date: query = query.eq("booking_date", str(query_date))
                    if selected_office != "All Offices": query = query.eq("booking_office", selected_office)
                
                supa_data = query.limit(100).execute().data
                for r in supa_data: r['_source_db'] = 'Supabase'
                final_recs.extend(supa_data)
            except Exception as e:
                logging.error(f"Supabase search error: {e}")
                
            # 2. Fetch from Local SQLite Laptop DB
            try:
                conn = sqlite3.connect("local_archive.db")
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                query_sql = "SELECT * FROM patient_deliveries WHERE 1=1"
                params = []
                if search_term:
                    if search_category == "All Fields":
                        query_sql += " AND (patient_name LIKE ? OR article_id LIKE ? OR mrn_no LIKE ? OR phone_number LIKE ? OR transaction_id LIKE ?)"
                        like_term = f"%{search_term}%"
                        params.extend([like_term]*5)
                    else:
                        query_sql += f" AND {search_category} LIKE ?"
                        params.append(f"%{search_term}%")
                    if selected_office != "All Offices":
                        query_sql += " AND booking_office = ?"
                        params.append(selected_office)
                else:
                    if query_date:
                        query_sql += " AND booking_date = ?"
                        params.append(str(query_date))
                    if selected_office != "All Offices":
                        query_sql += " AND booking_office = ?"
                        params.append(selected_office)
                query_sql += " LIMIT 100"
                c.execute(query_sql, params)
                for row in c.fetchall():
                    row_dict = dict(row)
                    row_dict['_source_db'] = 'Local Laptop'
                    final_recs.append(row_dict)
                conn.close()
            except Exception as e:
                logging.error(f"Local search error: {e}")

        if not final_recs: 
            st.warning("No records matched your filters or search in the databases.")
        else:
            if search_term and len(final_recs) > 1:
                st.markdown("##### 📑 Multiple Matches Detected")
                display_df = pd.DataFrame(final_recs)[['patient_name', 'mrn_no', 'article_id', 'booking_office', '_source_db']]
                st.dataframe(display_df, use_container_width=True)

            for profile in final_recs:
                if "status" not in profile or str(profile.get("status")) in ["nan", "None", "", "NoneType"]:
                    profile["status"] = "Pending"

            options_list = []
            for r in final_recs:
                status_val = r.get('status', 'Pending')
                status_display = "Verified" if status_val == "Delivered" else status_val
                options_list.append(f"{str(r.get('patient_name', '')).upper()} [{r.get('_source_db')}] - {status_display}")
                
            if st.session_state.selected_profile_index >= len(options_list): st.session_state.selected_profile_index = 0
                
            selected_prof_str = st.selectbox("Select Patient Profile to Process:", options_list, index=st.session_state.selected_profile_index, key="outbound_profile_select")
            actual_index = options_list.index(selected_prof_str) if selected_prof_str in options_list else 0
            target_profile = final_recs[actual_index]
            current_article_id = target_profile['article_id']

            st.markdown("<hr>", unsafe_allow_html=True)
            l_panel, r_panel = st.columns(2)
            
            with l_panel:
                st.markdown(f"<div class='patient-card-header'>👤 {target_profile['patient_name']}</div>", unsafe_allow_html=True)
                st.markdown(f"""
                    <div class='data-card'>
                        <div class='data-row'>📂 <b>Database Record:</b><br><span style='color:blue;'>{target_profile.get('_source_db')}</span></div>
                        <div class='data-row'>🔢 <b>MRN Number:</b><br><span class='data-value'>{target_profile.get('mrn_no', 'N/A')}</span></div>
                        <div class='data-row'>📦 <b>Consignment ID:</b><br><span class='data-value-alt'>{target_profile['article_id']}</span></div>
                        <div class='data-row'>🏥 <b>Booking GPO Station:</b><br><span style='font-size:18px; font-weight:600; color:#1e293b;'>{target_profile.get('booking_office', 'Unknown GPO')}</span></div>
                        <div class='data-row'>🏠 <b>Address:</b><br><span style='font-size:17px; font-weight:600; color:#1e293b; background:#f8fafc; padding:6px; display:block; border-radius:4px; border:1px solid #e2e8f0; margin-top:4px;'>{target_profile['address']}</span></div>
                    </div>
                """, unsafe_allow_html=True)
                
                st.markdown("#### 🌐 Pakistan Post Live EMTTS Tracking")
                opt_col1, opt_col2 = st.columns(2)
                with opt_col1: data_mode = st.radio("Display Transformation:", ["Fetch Live (Raw Mode)", "Fetch Snipped Data (Mapped Mode)"])
                with opt_col2: report_scope = st.radio("Reporting Scope Evaluation:", ["Only Last Status", "All Statuses (Full History)"])
                
                if st.button("🔍 Fetch Live Status from PakPost Server", use_container_width=True):
                    with st.spinner("Connecting to EMTTS Website..."):
                        data, err = fetch_live_emtts_status(current_article_id)
                        if err: st.error(err)
                        elif data and data["history"]: st.session_state.fetched_emtts_data[current_article_id] = data
                            
                cached_emtts_lpanel = st.session_state.fetched_emtts_data.get(current_article_id)
                if cached_emtts_lpanel and "history" in cached_emtts_lpanel:
                    history_list = cached_emtts_lpanel["history"]
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
                                <div style='font-size: 20px; font-weight: 700; color: #1e293b;'>{final_status_str}</div>
                            </div>
                        """, unsafe_allow_html=True)

                st.markdown("<div style='font-size: 22px; font-weight: 800; color: #334155; margin-bottom: 6px;'>🎴 DIAL THIS PHONE NUMBER:</div>", unsafe_allow_html=True)
                raw_phone = str(target_profile.get('phone_number', '')).strip()
                if not raw_phone or raw_phone.lower() in ['none', 'nan', 'null', ''] or len(raw_phone) < 5:
                    st.markdown("<div class='no-phone-display'>⚠️ No Contact Number Available</div>", unsafe_allow_html=True)
                    raw_phone = ""
                else:
                    if not raw_phone.startswith('0') and raw_phone.isdigit(): raw_phone = '0' + raw_phone
                    st.markdown(f"<div class='big-phone-display'>{raw_phone}</div>", unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                with st.expander("🖨️ Individual Profile Print Desk"):
                    print_operator = target_profile.get('operator_stamp', st.session_state.full_name)
                    print_status = target_profile.get('status', 'Pending')
                    if str(print_status) == "nan": print_status = "Pending"
                    
                    if print_status == "Delivered":
                        delivery_date = target_profile.get('delivery_date', 'N/A')
                        received_mode = target_profile.get('received_mode', 'N/A')
                        extra_money = target_profile.get('extra_money_charged', 'N/A')
                        print_status_detail = f"""
                        <b style="color: green;">Delivered</b><br>
                        <span style="font-size: 11px; font-weight: 600; color: #334155; line-height: 1.2;">
                            • Date: {delivery_date}<br>
                            • Mode: {received_mode}<br>
                            • Extra Money: <b style="color: {'#dc2626' if extra_money != 'No' else '#1e293b'}">{extra_money}</b>
                        </span>
                        """
                    elif print_status == "Issue / Complaint":
                        issue_reason = target_profile.get('issue_reason', 'N/A')
                        print_status_detail = f"<b style='color: #dc2626;'>Issue:</b> <span style='font-size: 11px;'>{issue_reason}</span>"
                    else:
                        print_status_detail = f"<b style='color: #475569;'>{print_status}</b>"

                    cached_emtts = st.session_state.fetched_emtts_data.get(current_article_id)
                    if not cached_emtts:
                        if st.button("🔍 Fetch Status inside Print Card", use_container_width=True, key="print_direct_fetch_btn"):
                            with st.spinner("Connecting to EMTTS Website..."):
                                data, err = fetch_live_emtts_status(current_article_id)
                                if not err: 
                                    st.session_state.fetched_emtts_data[current_article_id] = data
                                    st.rerun()
                    
                    cached_emtts = st.session_state.fetched_emtts_data.get(current_article_id)

                    if cached_emtts and "history" in cached_emtts:
                        history_list = cached_emtts["history"]
                        last_entry = history_list[-1]
                        status_val = map_status(last_entry["status"])
                        emtts_status_html = f"""
                        <div style="font-weight: bold; color: #1e293b; font-size: 13px;">{status_val}</div>
                        <div style="font-size: 11px; color: #475569;">📍 Office: {last_entry['office']} | 🕒 {last_entry['datetime']}</div>
                        """
                    else:
                        emtts_status_html = "<span style='font-size: 11px;'>Live status not fetched yet</span>"

                    current_pkt_time = datetime.datetime.now(PKT_TZ).strftime('%Y-%m-%d %I:%M:%S %p')

                    st.markdown(f"""
                        <div class="print-manifest-card">
                            <div class="watermark-print">SHC Cell Lahore GPO</div>
                            <div style="text-align: center; border-bottom: 2px solid #a61c1c; padding-bottom: 2px; margin-bottom: 4px;">
                                <img src="https://www.pakpost.gov.pk/images/New%20Logo%20PPO.jpg" style="height: 45px; margin-bottom: 0px;" alt="Pak Post Logo">
                                <h2 style="margin: 0; color: #a61c1c; font-size: 18px; font-weight: 800;">PAKISTAN POST | PATIENT FEEDBACK MANIFEST</h2>
                                <p style="margin: 0; color: #1e293b; font-size: 14px; font-weight: 700;">OFFICE OF THE CHIEF POSTMASTER LAHORE GPO</p>
                                <p style="margin: 0; color: #475569; font-size: 11px; font-weight: 600;">Quality Verification & Consignee Audit Certificate</p>
                            </div>
                            <table style="width: 100%; border-collapse: collapse; font-size: 12px; color: #000000;">
                                <tr><td style="padding: 5px 8px; font-weight: bold; width: 35%; border-bottom: 1px solid #e2e8f0;">Patient Name:</td><td style="padding: 5px 8px; border-bottom: 1px solid #e2e8f0;">{target_profile['patient_name']}</td></tr>
                                <tr><td style="padding: 5px 8px; font-weight: bold; border-bottom: 1px solid #e2e8f0;">MRN Number:</td><td style="padding: 5px 8px; border-bottom: 1px solid #e2e8f0;">{target_profile.get('mrn_no', 'N/A')}</td></tr>
                                <tr><td style="padding: 5px 8px; font-weight: bold; border-bottom: 1px solid #e2e8f0;">Consignment ID:</td><td style="padding: 5px 8px; border-bottom: 1px solid #e2e8f0; font-family: monospace; font-weight: 700; color: #a61c1c;">{target_profile['article_id']}</td></tr>
                                <tr><td style="padding: 5px 8px; font-weight: bold; border-bottom: 1px solid #e2e8f0;">Contact Number:</td><td style="padding: 5px 8px; border-bottom: 1px solid #e2e8f0;">{raw_phone if raw_phone else 'N/A'}</td></tr>
                                <tr><td style="padding: 5px 8px; font-weight: bold; border-bottom: 1px solid #e2e8f0;">Booking Station:</td><td style="padding: 5px 8px; border-bottom: 1px solid #e2e8f0;">{target_profile.get('booking_office', 'N/A')}</td></tr>
                                <tr><td style="padding: 5px 8px; font-weight: bold; border-bottom: 1px solid #e2e8f0;">Mailing Address:</td><td style="padding: 5px 8px; border-bottom: 1px solid #e2e8f0;">{target_profile['address']}</td></tr>
                                <tr><td style="padding: 5px 8px; font-weight: bold; border-bottom: 1px solid #e2e8f0;">EMTTS Status:</td><td style="padding: 5px 8px; border-bottom: 1px solid #e2e8f0;">{emtts_status_html}</td></tr>
                                <tr><td style="padding: 5px 8px; font-weight: bold; border-bottom: 1px solid #e2e8f0;">Verification:</td><td style="padding: 5px 8px; border-bottom: 1px solid #e2e8f0;">{print_status_detail}</td></tr>
                            </table>
                            <div style="margin-top: 10px; display: flex; justify-content: space-between; align-items: flex-end; font-size: 11px; border-top: 1px solid #cbd5e1; padding-top: 5px; color: #000000;">
                                <div>
                                    <b>Verified By:</b> {print_operator}<br>
                                    <span style="color: #475569;">Timestamp: {current_pkt_time}</span>
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                    if cached_emtts and "history" in cached_emtts:
                        components.html("""
                        <style>
                        .custom-print-btn { background: linear-gradient(180deg, #cc2424 0%, #a61c1c 100%) !important; color: #ffffff !important; border: 1px solid #801414 !important; border-radius: 6px !important; padding: 12px 24px !important; font-weight: 700; cursor: pointer; width: 100%; display: block; text-align: center; }
                        @media print { body { display: none !important; } }
                        </style>
                        <button onclick="window.parent.print()" class="custom-print-btn">🖨️ PRINT FEEDBACK MANIFEST</button>
                        """, height=55)
            
            with r_panel:
                st.markdown("#### 📝 Live Patient Verification Questionnaire")
                allow_questionnaire = True
                if str(target_profile["status"]) not in ["Pending", "Pending Retry", "nan"]:
                    st.warning(f"⚠️ Questionnaire already processed! Status: [{target_profile['status']}]")
                    unlock_re = st.radio("Process again?", ["No", "Yes"], index=0)
                    if unlock_re == "No": allow_questionnaire = False
                
                if allow_questionnaire:
                    payload_buffer = {}
                    can_submit = False
                    
                    contact_status = st.radio("📞 Patient successfully contacted?", ["Select Option", "Yes", "No"])
                    if contact_status == "No":
                        payload_buffer["contact_status"] = "No"
                        no_contact_reason = st.selectbox("Reason for failure:", ["Select Reason", "Phone number not valid", "Phone number wrong", "Phone switched off", "Did not pick up"])
                        if no_contact_reason == "Did not pick up":
                            retry_action = st.radio("Action Strategy:", ["Mark for Retry (Pending)", "Close as Unreachable (Max Attempts Reached)"])
                            if retry_action == "Mark for Retry (Pending)": 
                                payload_buffer["status"] = "Pending Retry"
                                payload_buffer["no_contact_reason"] = "Did not pick up - Pending Retry"
                                can_submit = True
                            elif retry_action == "Close as Unreachable (Max Attempts Reached)":
                                payload_buffer["status"] = "Unreachable"
                                payload_buffer["no_contact_reason"] = "Did not pick up - Final"
                                can_submit = True
                        elif no_contact_reason != "Select Reason":
                            payload_buffer["status"] = "Unreachable"
                            payload_buffer["no_contact_reason"] = no_contact_reason
                            can_submit = True
                            
                    elif contact_status == "Yes":
                        payload_buffer["contact_status"] = "Yes"
                        is_delivered = st.radio("📦 Have they received the medicine?", ["Select Option", "Yes", "No"])
                        if is_delivered == "Yes":
                            payload_buffer["status"] = "Delivered"
                            delivery_date = st.date_input("Select received date:", datetime.date.today())
                            payload_buffer["delivery_date"] = str(delivery_date)
                            received_mode = st.radio("📍 Delivery Mode:", ["Select Mode", "Delivered by postman to home address", "Collected directly from local post office branch"])
                            payload_buffer["received_mode"] = received_mode
                            
                            if received_mode == "Delivered by postman to home address":
                                extra_money = st.radio("Did postman ask for extra money?", ["Select", "No", "Yes"])
                                if extra_money == "Yes":
                                    payload_buffer["extra_money_charged"] = "Yes"
                                    payload_buffer["postman_issue_type"] = "Extra Charges Demanded"
                                    payload_buffer["extra_money_amount"] = st.text_input("Amount (Rs.):")
                                    payload_buffer["postman_name"] = st.text_input("Postman Name:")
                                    payload_buffer["post_office_name"] = st.text_input("Concerned Post Office Name:")
                                    if payload_buffer["extra_money_amount"] and payload_buffer["post_office_name"]: can_submit = True
                                elif extra_money == "No":
                                    payload_buffer["extra_money_charged"] = "No"
                                    other_issue = st.radio("Any other issue?", ["No", "Yes"])
                                    if other_issue == "Yes":
                                        payload_buffer["postman_issue_type"] = "Other Issue"
                                        payload_buffer["issue_reason"] = st.text_area("Describe:")
                                        payload_buffer["post_office_name"] = st.text_input("Concerned Post Office Name:")
                                        if payload_buffer["issue_reason"] and payload_buffer["post_office_name"]: can_submit = True
                                    else:
                                        payload_buffer["postman_issue_type"] = "None"
                                        can_submit = True

                            elif received_mode == "Collected directly from local post office branch":
                                payload_buffer["post_office_name"] = st.text_input("Concerned Post Office Name:", key="po_name")
                                if payload_buffer["post_office_name"]: can_submit = True

                        elif is_delivered == "No":
                            payload_buffer["status"] = "Issue / Complaint"
                            addr_match = st.radio("Is address correct?", ["Select Option", "Yes - Address is correct", "No - Address is wrong"])
                            if addr_match == "No - Address is wrong":
                                new_addr = st.text_input("📝 Updated address:")
                                if new_addr:
                                    payload_buffer["updated_address"] = new_addr
                                    postman_contact = st.radio("Did postman contact patient?", ["Select", "Yes", "No"])
                                    if postman_contact == "Yes":
                                         payload_buffer["postman_contacted"] = "Yes"
                                         reason = st.selectbox("Why not received?", ["Select Reason", "Patient does not want it", "Died", "Course completed", "Other"])
                                         if reason != "Select Reason":
                                             payload_buffer["not_received_reason"] = reason
                                             payload_buffer["status"] = "RTS Requested"
                                             can_submit = True
                                    elif postman_contact == "No":
                                         payload_buffer["postman_contacted"] = "No"
                                         payload_buffer["issue_reason"] = "Postman did not contact"
                                         can_submit = True
                            elif addr_match == "Yes - Address is correct":
                                payload_buffer["updated_address"] = target_profile['address']
                                payload_buffer["issue_reason"] = "Address verified but not delivered"
                                can_submit = True
                                 
                    if can_submit:
                        if st.button("💾 Finalize Session & Commit Logs", use_container_width=True):
                            with st.spinner("Saving verification securely..."):
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
                                    # Target specific DB based on where it came from
                                    if target_profile.get("_source_db") == "Local Laptop":
                                        update_local_db("patient_deliveries", payload_buffer, target_profile.get("id"))
                                    else:
                                        if target_profile.get("id"):
                                            supabase.table("patient_deliveries").update(payload_buffer).eq("id", target_profile.get("id")).execute()
                                        else:
                                            supabase.table("patient_deliveries").insert(payload_buffer).execute()
                                    
                                    # Local Text Logging (hides bottom right processing error silently)
                                    logging.info(f"Questionnaire submitted successfully for Article ID: {payload_buffer['article_id']} by {st.session_state.full_name}")
                                    
                                    st.success("✅ Updated securely with your operator identity stamp!")
                                    st.session_state.selected_profile_index += 1
                                    save_operator_state()
                                    time.sleep(0.5)
                                    st.rerun()
                                except Exception as e: 
                                    logging.error(f"Error saving verification: {e}")
                                    st.error("Error occurred while saving. Pls check log.")

def export_center_view():
    st.session_state.current_navigation_tab = "📥 Secure Reports Export Center"
    st.markdown("### 📥 Secure Data Export & Cloud Records Center")
    st.info("💡 Note: All real-time backups are already fully updated and securely stored on the cloud storage data nodes.")
    
    ec1, ec2 = st.columns(2)
    with ec1: exp_start_date = st.date_input("From Date", datetime.date.today() - datetime.timedelta(days=30))
    with ec2: exp_end_date = st.date_input("To Date", datetime.date.today())
    
    try:
        with st.spinner("Fetching data logs matrix..."):
            all_records = supabase.table("patient_deliveries").select("*").execute().data
        if all_records:
            df_export = pd.DataFrame(all_records)
            if 'created_at' in df_export.columns:
                df_export['parsed_date'] = pd.to_datetime(df_export['created_at']).dt.date
                mask = (df_export['parsed_date'] >= exp_start_date) & (df_export['parsed_date'] <= exp_end_date)
                df_export = df_export.loc[mask].drop(columns=['parsed_date'])
            if "operator_stamp" not in df_export.columns: df_export["operator_stamp"] = "Unassigned Logs"
            
            if st.session_state.role == "admin":
                distinct_operators = list(df_export["operator_stamp"].dropna().unique())
                distinct_operators.insert(0, "Download Everything (All Operators)")
                target_selection = st.selectbox("Select Filter:", distinct_operators)
                df_final_download = df_export[df_export["operator_stamp"] == target_selection] if target_selection != "Download Everything (All Operators)" else df_export
            else:
                df_final_download = df_export[df_export["operator_stamp"] == st.session_state.full_name]
            
            if not df_final_download.empty:
                csv_buffer = io.StringIO()
                df_final_download.to_csv(csv_buffer, index=False)
                st.download_button(label="📥 Download Authenticated Sheet (.CSV)", data=csv_buffer.getvalue().encode('utf-8'), file_name=f"Log_{exp_start_date}_to_{exp_end_date}.csv", mime="text/csv", use_container_width=True)
            else: st.warning("No recorded data found.")
    except Exception as err: st.error(f"Failed to compile export ledger sheets: {err}")

# Routing Engine setup
def is_default_page(title_keyword):
    curr = st.session_state.get("current_navigation_tab")
    return curr is not None and title_keyword in curr

if not st.session_state.logged_in: 
    pages_to_display = [st.Page(login_view, title="Authentication Desk", icon="🔒")]
elif st.session_state.show_recovery_prompt: 
    pages_to_display = [st.Page(recovery_view, title="Session Recovery", icon="🔄")]
else:
    if st.session_state.role == "admin": 
        pages_to_display = [
            st.Page(ingestion_view, title="Ingestion Engine", icon="📊", default=is_default_page("Ingestion")),
            st.Page(operator_matrix_view, title="Operator Matrix", icon="👥", default=is_default_page("Operator Matrix")),
            st.Page(communications_view, title="Communications Desk", icon="📞", default=is_default_page("Communications Desk")),
            st.Page(export_center_view, title="Export Center & Backup", icon="📥", default=is_default_page("Export Center"))
        ]
    else: 
        pages_to_display = [
            st.Page(communications_view, title="Communications Desk", icon="📞", default=is_default_page("Communications Desk")),
            st.Page(export_center_view, title="My Exports & Backup", icon="📥", default=is_default_page("Export Center"))
        ]

selected_navigation_route = st.navigation(pages_to_display, position="hidden")

st.markdown("<div class='brand-title'>📮 SHC & Pak Post | Free Home Delivery of Medicine</div>", unsafe_allow_html=True)
st.markdown("<div class='brand-subtitle'>Article Tracking & Patient Feedback Report</div>", unsafe_allow_html=True)

if st.session_state.logged_in and st.session_state.role == "admin":
    try:
        alert_records_query = supabase.table("patient_deliveries").select("*").neq("extra_money_charged", "No").execute().data
        active_alerts = [a for a in alert_records_query if a.get("extra_money_charged") in ["Yes", "Under Enquiry"]]
        
        if active_alerts:
            with st.expander("🚨 Critical Corruption Alerts", expanded=False):
                for alert in active_alerts:
                    is_enquiry = (alert.get("extra_money_charged") == "Under Enquiry")
                    st.markdown(f"**{alert['patient_name']}** - Alert")
                    if st.button("🖨️ Print Manifest", key=f"print_alert_{alert['id']}"): open_alert_manifest(alert)
    except Exception: pass

if st.session_state.logged_in:
    with st.sidebar:
        st.markdown("<div class='sb-headline-custom'>🖥️ Enterprise Console</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='sb-login-label'>Logged in as:</div><div class='sb-username-display'>{st.session_state.full_name}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='sb-privilege-label'>Privilege Cluster: <span>{st.session_state.role.upper()}</span></div>", unsafe_allow_html=True)
        
        try:
            today = datetime.date.today()
            today_count = 0
            res_stats = supabase.table("patient_deliveries").select("created_at, status").execute().data
            for r in res_stats:
                if str(r.get('status', 'Pending')).strip() not in ["Pending", "Pending Retry", "nan", "None", ""]:
                    if 'created_at' in r and r['created_at']:
                        try:
                            dt = datetime.datetime.fromisoformat(r['created_at'].replace('Z', '+00:00')).date()
                            if dt == today: today_count += 1
                        except: pass
            
            st.markdown(f"<div style='border:2px solid red; color:gold; padding:10px; font-weight:bold; font-size:18px;'>Today's Count: {today_count}</div>", unsafe_allow_html=True)
        except Exception: pass
        
        if st.button("🔐 Change Password"): change_password_dialog()
        
        if not st.session_state.show_recovery_prompt:
            for pg in pages_to_display:
                if st.button(f"{pg.icon} {pg.title}", use_container_width=True, key=f"nav_btn_{pg.title}"): 
                    st.session_state.current_navigation_tab = pg.title
                    st.switch_page(pg)
                    
        if st.button("Terminate Session 🚪"):
            st.session_state.logged_in = False
            st.query_params.clear()
            st.rerun()

selected_navigation_route.run()
