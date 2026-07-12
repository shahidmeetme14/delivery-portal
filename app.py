import streamlit as st
from supabase import create_client, Client
import pandas as pd
import datetime
import io
import time
import urllib.request
from bs4 import BeautifulSoup

# 🎛️ Page Structural Settings
st.set_page_config(
    page_title="Presented by SHAHID | Pakistan Post Audit", 
    page_icon="📮", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

SESSION_TIMEOUT = 30 * 60  

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "username" not in st.session_state: st.session_state.username = ""
if "full_name" not in st.session_state: st.session_state.full_name = ""
if "role" not in st.session_state: st.session_state.role = ""
if "last_activity" not in st.session_state: st.session_state.last_activity = time.time()
if "current_navigation_tab" not in st.session_state: st.session_state.current_navigation_tab = None
if "selected_profile_index" not in st.session_state: st.session_state.selected_profile_index = 0
if "show_recovery_prompt" not in st.session_state: st.session_state.show_recovery_prompt = False
if "cached_recovery_data" not in st.session_state: st.session_state.cached_recovery_data = {}

# 🎨 PAKISTAN POST OFFICIAL THEME ENGINE (RED & GOLD) + UI CORRECTIONS
st.markdown("""
    <style>
    /* Global Styles */
    .block-container { padding-top: 1.0rem !important; padding-bottom: 1.0rem !important; }
    
    /* 🔒 HIDING STREAMLIT FOOTER, GITHUB BADGES AND MENUS COMPLETELY */
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    div[data-testid="stDecoration"] {visibility: hidden !important;}
    [data-testid="stStatusWidget"] {visibility: hidden !important;}
    div[class^="viewerBadge"] {display: none !important;}
    .viewerBadge_container__1QSob {display: none !important;}
    
    /* Pakistan Post Brand Palette */
    .stApp { background-color: #fcf8f8; }
    .brand-title { color: #b71c1c; font-weight: 800; font-size: 1.8rem; margin-bottom: 1px; }
    .brand-subtitle { color: #d4af37; font-size: 1.0rem; margin-bottom: 15px; font-weight: 700; border-left: 4px solid #b71c1c; padding-left: 8px; }
    
    /* Centered Non-Cutting Login Box */
    .login-container {
        max-width: 450px;
        margin: 60px auto !important;
        background: #ffffff !important;
        border-radius: 8px !important;
        border-top: 5px solid #b71c1c !important;
        border-left: 1px solid #e0e0e0 !important;
        border-right: 1px solid #e0e0e0 !important;
        border-bottom: 3px solid #d4af37 !important;
        box-shadow: 0 10px 25px rgba(0,0,0,0.08) !important;
        padding: 25px !important;
    }
    
    /* Standardized Forms & Panels */
    div[data-testid="stForm"], .pyqt-panel {
        background: #ffffff !important;
        border-radius: 6px !important;
        border: 1px solid #dcdcdc !important;
        box-shadow: 0 4px 10px rgba(183, 28, 28, 0.03) !important;
        padding: 15px !important;
    }
    
    /* Buttons Customization (PakPost Red) */
    div.stButton > button, div.stDownloadButton > button {
        background: linear-gradient(180deg, #d32f2f 0%, #b71c1c 100%) !important;
        color: #ffffff !important;
        border: 1px solid #7f0000 !important;
        border-bottom: 3px solid #5f0000 !important;
        border-radius: 5px !important;
        padding: 6px 20px !important;
        font-weight: 700;
        box-shadow: 0px 3px 6px rgba(0,0,0,0.1) !important;
    }
    
    .active-nav-btn div.stButton > button {
        background: linear-gradient(180deg, #ea1c1c 0%, #d4af37 100%) !important;
        border-bottom: 1px solid #7f0000 !important;
    }
    
    /* 3D Dropdowns */
    div[data-testid="stSelectbox"] > div[data-baseweb="select"] {
        border-bottom: 3px solid #d4af37 !important;
    }
    
    /* Phone Badge */
    .big-phone-display { 
        font-size: 22px !important; font-weight: 700 !important; color: #ffffff !important; 
        background: linear-gradient(180deg, #d32f2f 0%, #b71c1c 100%) !important; 
        padding: 8px; border-radius: 6px; text-align: center; border-bottom: 3.5px solid #d4af37;
        letter-spacing: 1.5px; margin: 4px 0;
    }
    
    /* Printable Manifesto Clean CSS Layout */
    @media print {
        body * { visibility: hidden; }
        .print-manifesto-area, .print-manifesto-area * { visibility: visible; }
        .print-manifesto-area { position: absolute; left: 0; top: 0; width: 100%; border: 2px solid #000; padding: 20px; font-family: monospace; }
    }
    
    .manifesto-preview {
        background: #fff; border: 2px dashed #b71c1c; padding: 20px; border-radius: 8px; margin-top: 15px; font-family: 'Courier New', Courier, monospace;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

try: supabase = init_connection()
except Exception as e: st.stop()

def save_operator_state():
    if st.session_state.logged_in and st.session_state.username:
        try:
            supabase.table("operator_sessions").upsert({
                "username": st.session_state.username,
                "last_tab": st.session_state.current_navigation_tab,
                "last_index": st.session_state.selected_profile_index,
                "updated_at": datetime.datetime.now().isoformat()
            }, on_conflict="username").execute()
        except: pass

def fetch_operator_state(username):
    try:
        res = supabase.table("operator_sessions").select("*").eq("username", username).execute().data
        if res: return res[0]
    except: return None

def map_status(raw_status):
    s = raw_status.lower().strip()
    if "undelivered" in s: return "Undelivered"
    if "return" in s or "rts" in s: return "RTS"
    if "delivered" in s: return "Delivered"
    return raw_status.strip()

def fetch_live_emtts_status(article_id):
    url = f"https://ep.gov.pk/emtts/EPTrack_Live.aspx?ArticleIDz={article_id.strip()}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=15.0) as response:
            html = response.read().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(html, 'html.parser')
            track_div = soup.find(id="TrackDetailDiv")
            history = []
            if track_div:
                rows = track_div.find_all("tr")
                current_date = ""
                for row in rows:
                    tds = row.find_all("td")
                    if len(tds) == 1 and "20" in tds[0].text: current_date = tds[0].text.strip()
                    if len(tds) >= 4:
                        history.append({"datetime": f"{current_date} {tds[1].text.strip()}", "office": tds[2].text.strip(), "status": tds[3].text.strip()})
            if not history: return None, "🔎 No logs found."
            return {"history": history}, None
    except Exception as e: return None, str(e)

# Sidebar Identity
if st.session_state.logged_in:
    with st.sidebar:
        st.markdown("<div style='color:#b71c1c; font-weight:bold; font-size:16px;'>Presented by SHAHID</div>", unsafe_allow_html=True)
        st.markdown(f"**Operator:** {st.session_state.full_name}")
        st.markdown(f"**Role:** `{st.session_state.role.upper()}`")
        if st.button("Terminate Session 🚪", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

st.markdown("<div class='brand-title'>📮 PAKISTAN POST | DATA AUDIT SYSTEM</div>", unsafe_allow_html=True)
st.markdown("<div class='brand-subtitle'>Lahore GPO Operational Core Dashboard</div>", unsafe_allow_html=True)

# 🔐 LOGIN BOX (FIXED CUT-OFF)
if not st.session_state.logged_in and not st.session_state.show_recovery_prompt:
    st.markdown("<div class='login-container'>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align:center; color:#b71c1c; margin-top:0;'>SECURE TERMINAL LOGIN</h4>", unsafe_allow_html=True)
    input_user = st.text_input("OPERATOR USERNAME / ID")
    input_pass = st.text_input("SECURITY PASSWORD", type="password")
    btn_login = st.button("UNLOCK HUB", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    if btn_login:
        if input_user and input_pass:
            ud = supabase.table("app_users").select("*").eq("username", input_user.strip()).eq("password", input_pass.strip()).execute().data
            if ud:
                recovery_data = fetch_operator_state(ud[0]["username"])
                st.session_state.username = ud[0]["username"]
                st.session_state.full_name = ud[0]["full_name"]
                st.session_state.role = ud[0]["role"]
                if recovery_data:
                    st.session_state.cached_recovery_data = recovery_data
                    st.session_state.show_recovery_prompt = True
                else:
                    st.session_state.logged_in = True
                st.rerun()
            else: st.error("Invalid secure credentials.")

elif st.session_state.show_recovery_prompt:
    st.warning("⚠️ Unexpected system shutdown detected. Last active state is secure.")
    col_res, col_new = st.columns(2)
    with col_res:
        if st.button("🔄 RESUME SESSION"):
            st.session_state.logged_in = True
            st.session_state.current_navigation_tab = st.session_state.cached_recovery_data.get('last_tab')
            st.session_state.selected_profile_index = int(st.session_state.cached_recovery_data.get('last_index', 0))
            st.session_state.show_recovery_prompt = False
            st.rerun()
    with col_new:
        if st.button("🆕 START FRESH"):
            st.session_state.logged_in = True
            st.session_state.show_recovery_prompt = False
            save_operator_state()
            st.rerun()

else:
    # Navigation Tabs Setup
    tabs = ["📊 Administrative Ingestion Engine", "👥 Operator Matrix & Security Audit Logs", "📞 Outbound Communications Hub", "📥 Secure Reports Export Center"] if st.session_state.role == "admin" else ["📞 Outbound Communications Hub", "📥 Secure Reports Export Center"]
    if st.session_state.current_navigation_tab not in tabs: st.session_state.current_navigation_tab = tabs[0]
    
    nc = st.columns(len(tabs))
    for idx, t_name in enumerate(tabs):
        with nc[idx]:
            cls = "active-nav-btn" if st.session_state.current_navigation_tab == t_name else ""
            st.markdown(f"<div class='{cls}'>", unsafe_allow_html=True)
            if st.button(t_name, use_container_width=True):
                st.session_state.current_navigation_tab = t_name
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # PAGE 1: ADMIN INGESTION & ALERTS
    if st.session_state.current_navigation_tab == "📊 Administrative Ingestion Engine" and st.session_state.role == "admin":
        
        # 🚨 HIGH-PRIORITY CORRUPTION/COMPLAINT ALERTS SECTION
        st.markdown("### 🚨 CRITICAL ADMINISTRATIVE RED-FLAG ALERTS")
        try:
            alerts_data = supabase.table("patient_deliveries").select("*").eq("extra_money_charged", "Yes").execute().data
            if alerts_data:
                for al in alerts_data:
                    st.error(f"⚠️ **Bribery Alert:** Postman demanded extra cash from **{al['patient_name']}** (MRN: {al.get('mrn_no')}) | Article ID: `{al['article_id']}` | Stamped By: {al.get('operator_stamp')}")
            else:
                st.success("✅ No unauthorized collection reports received in this batch.")
        except: pass
        
        st.markdown("---")
        st.markdown("### 📥 Manifest Bulk Excel Ingestion")
        source_file = st.file_uploader("Upload Sheet", type=["xlsx", "csv"])
        if source_file:
            df = pd.read_excel(source_file) if source_file.name.endswith('.xlsx') else pd.read_csv(source_file)
            if st.button("🚀 Push to Cloud Database (Auto Updates Existing Rows)"):
                staging = []
                for _, r in df.iterrows():
                    staging.append({
                        "article_id": str(r.iloc[0]).strip(), "patient_name": str(r.iloc[1]).strip(),
                        "phone_number": str(r.iloc[2]).strip(), "booking_date": str(datetime.date.today()),
                        "address": str(r.iloc[3]).strip(), "status": "Pending"
                    })
                try:
                    supabase.table("patient_deliveries").upsert(staging, on_conflict="article_id").execute()
                    st.success("Data synchronized successfully onto database network nodes!")
                except Exception as ex: st.error(str(ex))

    # PAGE 3: OUTBOUND COMMUNICATION HUB
    elif st.session_state.current_navigation_tab == "📞 Outbound Communications Hub":
        query_date = st.date_input("Select Audit Target Date:", datetime.date.today())
        try: records = supabase.table("patient_deliveries").select("*").execute().data
        except: records = []
        
        if records:
            options_list = [f"{r['patient_name']} - [{r['status']}]" for r in records]
            if st.session_state.selected_profile_index >= len(options_list): st.session_state.selected_profile_index = 0
            
            st.selectbox("Select Target Record:", options_list, index=st.session_state.selected_profile_index)
            target = records[st.session_state.selected_profile_index]
            
            l_panel, r_panel = st.columns(2)
            with l_panel:
                st.markdown(f"#### 👤 Patient Profile: {target['patient_name']}")
                st.info(f"📦 **Consignment ID:** {target['article_id']}\n\n🏠 **Address:** {target['address']}")
                
                # EMTTS LIVE LOOKUP WITH ALL-STATUS AND CONDITION DETECTION
                st.markdown("#### 🌐 Live EMTTS Real-time History Path")
                if st.button("Query Live History Log Table"):
                    data, err = fetch_live_emtts_status(target['article_id'])
                    if err: st.error(err)
                    elif data:
                        h_list = data["history"]
                        
                        # High-Visibility Alert Conditions Check
                        is_del = any("delivered" in h["status"].lower() for h in h_list)
                        is_rts = any("return" in h["status"].lower() or "rts" in h["status"].lower() for h in h_list)
                        
                        if is_del: st.success(f"✅ Delivered Event Confirmed in Tracking Log history!")
                        elif is_rts: st.error(f"❌ RTS / Return to Sender Event Confirmed in Tracking History!")
                        
                        # Output full dataframe history cleanly
                        df_hist = pd.DataFrame(h_list)
                        st.dataframe(df_hist, use_container_width=True)
                
                st.markdown("#### 📱 DIAL CONTACT NUMBER:")
                st.markdown(f"<div class='big-phone-display'>{target['phone_number']}</div>", unsafe_allow_html=True)
                
            with r_panel:
                st.markdown("#### 📝 Verification Form Panel")
                is_delivered = st.radio("Is parcel physically received?", ["Select", "Yes", "No"])
                p_buffer = {}
                
                if is_delivered == "Yes":
                    p_buffer["status"] = "Delivered"
                    p_buffer["extra_money_charged"] = st.radio("Did the postman ask for extra tip/money?", ["No", "Yes"])
                elif is_delivered == "No":
                    p_buffer["status"] = "Issue / Complaint"
                
                if st.button("💾 Finalize Session & Commit Logs"):
                    p_buffer["operator_stamp"] = st.session_state.full_name
                    supabase.table("patient_deliveries").update(p_buffer).eq("id", target["id"]).execute()
                    st.success("Session Committed Successfully!")
                    st.session_state.selected_profile_index += 1
                    save_operator_state()
                    time.sleep(0.4)
                    st.rerun()
                
                # 🖨️ BEAUTIFUL PRINTABLE MANIFESTO CARD
                st.markdown("---")
                if st.button("🖨️ Generate & Print Beautiful Manifesto Layout"):
                    st.markdown(f"""
                    <div class="print-manifesto-area">
                        <div class="manifesto-preview">
                            <h2 style="text-align:center; margin:0; color:#000;">PAKISTAN POST LOGISTICS MANIFEST</h2>
                            <h4 style="text-align:center; margin:2px;">LAHORE GENERAL POST OFFICE (GPO)</h4>
                            <p style="text-align:center;">--------------------------------------------------</p>
                            <p><b>PRINTED ON:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                            <p><b>AUDIT OPERATOR:</b> {st.session_state.full_name}</p>
                            <p>--------------------------------------------------</p>
                            <p><b>PATIENT NAME:</b> {target['patient_name']}</p>
                            <p><b>CONSIGNMENT ID:</b> {target['article_id']}</p>
                            <p><b>ADDRESS:</b> {target['address']}</p>
                            <p><b>CONTACT NUMBER:</b> {target['phone_number']}</p>
                            <p>--------------------------------------------------</p>
                            <p><b>AUDIT STATUS:</b> {p_buffer.get('status', target['status'])}</p>
                            <p><b>EXTRA CASH DEMANDED:</b> {p_buffer.get('extra_money_charged', 'N/A')}</p>
                            <p>--------------------------------------------------</p>
                            <br><br><br>
                            <p style="text-align:right;">___________________________<br>Authorized Signature GPO</p>
                        </div>
                    </div>
                    <script>window.print();</script>
                    """, unsafe_allow_html=True)
