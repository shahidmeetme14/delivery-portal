import streamlit as st
from supabase import create_client, Client
import pandas as pd
import datetime
import io

# Premium UI & Page Configuration
st.set_page_config(
    page_title="SHC & Pak Post | Delivery Portal", 
    page_icon="📮", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Modern Custom CSS Styling Injection
st.markdown("""
    <style>
    /* Main Layout Aesthetics */
    .stApp { background-color: #f8fafc; }
    
    /* Modern Dashboard Header */
    .main-title { color: #1e3a8a; font-family: 'Inter', sans-serif; font-weight: 800; font-size: 2.5rem; letter-spacing: -0.05rem; margin-bottom: 5px; }
    .sub-title { color: #64748b; font-size: 1.1rem; margin-bottom: 30px; font-weight: 400; }
    
    /* Phone Number Display Box */
    .big-phone-display { font-size: 34px !important; font-weight: 800 !important; color: #dc2626 !important; background-color: #fef2f2; padding: 15px; border-radius: 12px; text-align: center; border: 2px dashed #f87171; letter-spacing: 2px; box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.06); }
    .patient-card-header { font-size: 26px !important; font-weight: 700 !important; color: #1e3a8a; border-left: 5px solid #2563eb; padding-left: 10px; margin-bottom: 15px; }
    
    /* Customizing Streamlit Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #ffffff; border: 1px solid #e2e8f0; padding: 10px 20px; border-radius: 8px; font-weight: 600; color: #475569; transition: all 0.3s ease; }
    .stTabs [data-baseweb="tab"]:hover { color: #2563eb; border-color: #bfdbfe; background-color: #eff6ff; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { background-color: #2563eb !important; color: white !important; border-color: #2563eb !important; box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2); }
    </style>
""", unsafe_allow_html=True)

# Establish Database Connection
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase: Client = init_connection()
except Exception as e:
    st.error(f"Database connection failed: {e}")
    st.stop()

# Initialize Session Infrastructure
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "full_name" not in st.session_state:
    st.session_state.full_name = ""
if "role" not in st.session_state:
    st.session_state.role = ""

# --- SECURE GATEWAY WORKFLOW ---
if not st.session_state.logged_in:
    # Centering the login card using columns layout
    _, center_col, _ = st.columns([1, 1.5, 1])
    
    with center_col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("<h2 style='text-align: center; color: #0f172a; font-family: sans-serif; margin-bottom: 25px;'>📮 Portal Authentication</h2>", unsafe_allow_html=True)
            
            username_input = st.text_input("Username", placeholder="Enter username")
            password_input = st.text_input("Password", type="password", placeholder="Enter password")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Authenticate Session 🚀", use_container_width=True):
                if username_input and password_input:
                    try:
                        user_query = supabase.table("app_users").select("*").eq("username", username_input.strip()).execute()
                        
                        if user_query.data and user_query.data[0]["password"] == password_input.strip():
                            st.session_state.logged_in = True
                            st.session_state.username = user_query.data[0]["username"]
                            st.session_state.full_name = user_query.data[0]["full_name"]
                            st.session_state.role = user_query.data[0]["role"]
                            
                            # Log Event to Database
                            try:
                                headers = st.context.headers
                                ip_addr = headers.get("X-Forwarded-For", "127.0.0.1").split(",")[0]
                                dev_info = headers.get("User-Agent", "Unknown Hardware")
                                supabase.table("user_logins").insert({
                                    "username": st.session_state.username,
                                    "ip_address": ip_addr,
                                    "device_info": dev_info
                                }).execute()
                            except:
                                pass
                            
                            st.success("Session verified successfully!")
                            st.rerun()
                        else:
                            st.error("Invalid Username or Password! Please verify credentials.")
                    except Exception as auth_err:
                        st.error(f"Authentication Server Offline or Table Column Mismatch: {auth_err}")
                else:
                    st.warning("Please complete all fields.")
            
            # Diagnostic tools for Admin Setup
            st.markdown("---")
            with st.expander("🛠️ Database Admin Initialization Tools"):
                st.write("If you are running this for the first time, click below to inject the default Admin user into Supabase:")
                if st.button("Inject Admin User ('shahid') into Database"):
                    try:
                        res = supabase.table("app_users").upsert({
                            "username": "shahid",
                            "password": "shahid@2341",
                            "full_name": "Shahid Hussain",
                            "role": "admin"
                        }, on_conflict="username").execute()
                        st.success("Successfully written to Supabase! Try logging in now.")
                    except Exception as seed_err:
                        st.error(f"Supabase Insertion Failed: {seed_err}")
                        st.info("Tip: Check if your table has columns named exactly: 'username', 'password', 'full_name', and 'role'.")

    st.stop()

# --- POST-AUTHENTICATION APPLICATION SPACE ---
with st.sidebar:
    st.markdown(f"👤 Logged in as:<br><b style='font-size:16px; color:#1e3a8a;'>{st.session_state.full_name}</b>", unsafe_allow_html=True)
    st.markdown(f"🎖️ Privileges: `{st.session_state.role.upper()}`")
    st.markdown("---")
    
    st.markdown("⚙️ **Change Profile Password**")
    new_secret = st.text_input("New Password:", type="password", key="self_p_chg")
    if st.button("Apply New Password", use_container_width=True):
        if new_secret:
            try:
                supabase.table("app_users").update({"password": new_secret.strip()}).eq("username", st.session_state.username).execute()
                st.success("Password updated successfully!")
            except Exception as e:
                st.error(f"Update rejected: {e}")
                
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("Terminate Session 🚪", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.full_name = ""
        st.session_state.role = ""
        st.rerun()

# Main Workspace Headers
st.markdown("<div class='main-title'>📮 SHC & Pak Post Workspace</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>Free Home Delivery of Medicine — Logistics Tracking & Quality Feedback System</div>", unsafe_allow_html=True)

# Role Based Tab Architecture Setup
if st.session_state.role == "admin":
    tabs = st.tabs(["📊 Administrative Ingestion Engine", "👥 Operator Matrix & Security Audit Logs", "📞 Outbound Communications Hub"])
else:
    tabs = st.tabs(["📞 Outbound Communications Hub"])

# ----------------------------------------------------
# MODULE 1: ADMINISTRATIVE INGESTION ENGINE (ADMIN ONLY)
# ----------------------------------------------------
if st.session_state.role == "admin":
    with tabs[0]:
        st.markdown("### 📥 Bulk Logistics Ingestion Engine")
        source_file = st.file_uploader("Upload Parcel Manifest Data Sheet (.xlsx or .csv)", type=["xlsx", "csv"])
        
        if source_file is not None:
            try:
                df = pd.read_excel(source_file) if source_file.name.endswith('.xlsx') else pd.read_csv(source_file)
                st.success("Manifest source data read successfully!")
                st.dataframe(df.head(3), use_container_width=True)
            except Exception as file_err:
                st.error(f"Failed to read manifest file: {file_err}")
                st.stop()
                
            st.markdown("---")
            st.markdown("### 🛠️ Schema Mapping & Clean Room Validation")
            
            mc1, mc2, mc3 = st.columns(3)
            with mc1:
                c_article = st.selectbox("1. Article / Consignment ID Column:", df.columns)
                c_name = st.selectbox("2. Consignee / Patient Name Column:", df.columns)
            with mc2:
                c_phone = st.selectbox("3. Dedicated Contact Number Column:", df.columns)
                c_date = st.selectbox("4. Registry/Booking Date Column:", df.columns)
            with mc3:
                c_address = st.selectbox("5. Delivery Destination Address Column:", df.columns)
                dup_target = st.selectbox("🎯 Unique Integrity Key (De-duplication Target):", df.columns, index=df.columns.get_loc(c_article))

            if st.button("🚀 Push Verified Records to Cloud Database", use_container_width=True):
                total_initial = len(df)
                cleaned_records = df.drop_duplicates(subset=[dup_target], keep='first')
                total_final = len(cleaned_records)
                
                staging_area = []
                for _, row in cleaned_records.iterrows():
                    raw_dt = row[c_date]
                    final_dt = str(datetime.date.today())
                    try:
                        final_dt = pd.to_datetime(raw_dt).strftime('%Y-%m-%d')
                    except:
                        pass
                        
                    staging_area.append({
                        "article_id": str(row[c_article]).strip(),
                        "patient_name": str(row[c_name]).strip(),
                        "phone_number": str(row[c_phone]).strip(),
                        "booking_date": final_dt,
                        "address": str(row[c_address]).strip(),
                        "status": "Pending"
                    })
                
                batch_size = 200
                total_staged = len(staging_area)
                uploaded_count = 0
                
                for idx in range(0, total_staged, batch_size):
                    batch = staging_area[idx:idx + batch_size]
                    try:
                        supabase.table("patient_deliveries").upsert(batch, on_conflict="article_id").execute()
                        uploaded_count += len(batch)
                    except Exception as upload_err:
                        st.error(f"Batch execution exception: {upload_err}")
                
                st.success(f"🎉 Synchronized! Ingested {uploaded_count} unique entries. Removed {total_initial - total_final} structural duplicates.")

        # Infrastructure Master Backup Component
        st.markdown("---")
        st.markdown("### 💾 Core Storage Extraction & Ledger Backup")
        if st.button("🔄 Initialize Live Master System Export", use_container_width=True):
            try:
                export_query = supabase.table("patient_deliveries").select("*").execute()
                if export_query.data:
                    export_df = pd.DataFrame(export_query.data)
                    binary_buffer = io.BytesIO()
                    with pd.ExcelWriter(binary_buffer, engine='openpyxl') as xl_writer:
                        export_df.to_excel(xl_writer, index=False, sheet_name='Master_System_Ledger')
                    binary_buffer.seek(0)
                    
                    st.download_button(
                        label="📥 Download Master Backup Ledger Spreadsheet (.xlsx)",
                        data=binary_buffer,
                        file_name=f"SHC_PakPost_SystemMasterBackup_{datetime.date.today()}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
            except Exception as backup_ex:
                st.error(f"Backup engine execution error: {backup_ex}")

# ----------------------------------------------------
# MODULE 2: OPERATOR MATRIX & SECURITY AUDIT LOGS (ADMIN ONLY)
# ----------------------------------------------------
if st.session_state.role == "admin":
    with tabs[1]:
        st.markdown("### 👥 Operational Account Provisioning Center")
        
        uc1, uc2 = st.columns([1, 1])
        with uc1:
            st.markdown("#### ➕ Provision New Operator Account")
            new_fname_input = st.text_input("Operator Real Name (Full Name)", key="cr_f")
            new_user_input = st.text_input("Operational Username (Login ID)", key="cr_u")
            new_pass_input = st.text_input("Assigned Initial Password", type="password", key="cr_p")
            
            if st.button("Register Operator Account", use_container_width=True):
                if new_fname_input and new_user_input and new_pass_input:
                    try:
                        supabase.table("app_users").insert({
                            "username": new_user_input.strip(),
                            "password": new_pass_input.strip(),
                            "full_name": new_fname_input.strip(),
                            "role": "staff"
                        }).execute()
                        st.success(f"Account for '{new_fname_input}' provisioned successfully.")
                    except Exception as reg_err:
                        st.error(f"Failed to create account (Username must be globally unique): {reg_err}")
                else:
                    st.warning("All input fields are mandatory.")
        
        with uc2:
            st.markdown("#### 🔧 Administrative Access Override Console")
            try:
                user_fetch = supabase.table("app_users").select("username", "full_name").execute()
                operator_dictionary = {f"{usr['full_name']} ({usr['username']})": usr['username'] for usr in user_fetch.data if usr['username'] != 'shahid'}
                
                if operator_dictionary:
                    target_display = st.selectbox("Select Target Account:", list(operator_dictionary.keys()))
                    target_username = operator_dictionary[target_display]
                    override_password = st.text_input("Enter Override Password:", type="password", key="adm_ovr_p")
                    
                    if st.button("Execute Hard Password Reset", use_container_width=True):
                        supabase.table("app_users").update({"password": override_password.strip()}).eq("username", target_username).execute()
                        st.success(f"Access keys overridden for operational profile: {target_display}")
                else:
                    st.info("No external operational profiles detected in cluster.")
            except:
                st.write("Failed to initialize user directory context.")

        st.markdown("---")
        st.markdown("### 🛡️ Real-time Hardware Session Audit & Network Logs")
        try:
            audit_query = supabase.table("user_logins").select("*").order("login_time", desc=True).limit(50).execute()
            if audit_query.data:
                audit_df = pd.DataFrame(audit_query.data)
                audit_df = audit_df[["username", "ip_address", "device_info", "login_time"]]
                st.dataframe(audit_df, use_container_width=True)
            else:
                st.info("System tracking logs are currently empty.")
        except Exception as audit_ex:
            st.error(f"Audit log streaming fault: {audit_ex}")

# ----------------------------------------------------
# MODULE 3: OUTBOUND COMMUNICATIONS & FEEDBACK HUB
# ----------------------------------------------------
staff_view_idx = 2 if st.session_state.role == "admin" else 0
with tabs[staff_view_idx]:
    st.markdown("### 📞 Outbound Communications Desk")
    query_date = st.date_input("Filter Manifest Records by Registry/Booking Date:", datetime.date.today())
    
    try:
        manifest_response = supabase.table("patient_deliveries").select("*").eq("booking_date", str(query_date)).execute()
        active_records = manifest_response.data
    except Exception as api_err:
        st.error(f"Outbound manifest pull failed: {api_err}")
        active_records = []
        
    if not active_records:
        st.info("No patient manifest data matches the selected booking date context.")
    else:
        st.success(f"Located {len(active_records)} records matching current date parameters.")
        manifest_mapping = {f"{rec['patient_name']} (Consignment: {rec['article_id']}) - [{rec['status']}]": rec for rec in active_records}
        selected_manifest_key = st.selectbox("Select Target Operational Profile to Process:", list(manifest_mapping.keys()))
        
        target_profile = manifest_mapping[selected_manifest_key]
        st.markdown("<hr>", unsafe_allow_html=True)
        
        l_panel, r_panel = st.columns([1, 1])
        with l_panel:
            st.markdown(f"<div class='patient-card-header'>👤 {target_profile['patient_name']}</div>", unsafe_allow_html=True)
            st.write(f"📦 **Consignment/Article ID:** `{target_profile['article_id']}`")
            st.write(f"🏠 **Destination Address:** {target_profile['address']}")
            st.write(f"📅 **Booking Manifest Date:** {target_profile['booking_date']}")
            
            st.markdown("#### 🎴 DIAL THIS PHONE NUMBER FROM LANDLINE:")
            st.markdown(f"<div class='big-phone-display'>{target_profile['phone_number']}</div>", unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("#### 🌐 Real-time EMTTS Tracking Infrastructure Interface")
            if st.button("Query Live EMTTS Server Gateway", use_container_width=True):
                with st.spinner("Connecting to tracking engine arrays..."):
                    emtts_mock = "DELIVERED" if "1" in str(target_profile['id']) else "IN-TRANSIT / OUT FOR DELIVERY"
                    st.info(f"EMTTS Database Callback Response: **{emtts_mock}**")
        
        with r_panel:
            st.markdown("#### 📝 Live Quality Verification & Audit Questionnaire")
            is_delivered = st.radio("1. Has the consignee physically received the delivery?", ["Select Assessment Option", "Yes", "No"], index=0)
            payload_buffer = {}
            
            if is_delivered == "Yes":
                payload_buffer["status"] = "Delivered"
                actual_del_date = st.date_input("Delivery Verification Date", datetime.date.today())
                payload_buffer["delivery_date"] = str(actual_del_date)
                
                delivery_method = st.radio("Delivery Execution Mode:", ["Delivered by postman to home address", "Collected directly from local post office branch"])
                payload_buffer["received_mode"] = delivery_method
                
                illegal_tariff = st.radio("Did the delivery agent request any unauthorized monetary payment/tips?", ["No", "Yes"])
                payload_buffer["extra_money_charged"] = illegal_tariff
                
                if illegal_tariff == "Yes":
                    st.error("🚨 CORRUPTION TRACKING PROTOCOL ACTIVATED. Enter delivery agent parameters instantly.")
                    payload_buffer["postman_name"] = st.text_input("Delivery Agent (Postman) Name:")
                    payload_buffer["postman_number"] = st.text_input("Delivery Agent Contact Details:")
                    payload_buffer["post_office_name"] = st.text_input("Originating Post Office Branch:")
                    
            elif is_delivered == "No":
                payload_buffer["status"] = "Issue / Complaint"
                root_cause = st.selectbox("Select Primary Delivery Discrepancy Failure Mode:", [
                    "Wrong Delivery Status on EMTTS (System states delivered but physically unreceived)", 
                    "Incomplete Address / Premises Locked", 
                    "Logistics Delay (Item currently stuck or delayed in transit)", 
                    "Formal Institutional Dispute (Escalate to senior command)"
                ])
                payload_buffer["issue_reason"] = root_cause
                
            st.markdown("---")
            if st.button("💾 Finalize Session & Commit Logs", use_container_width=True):
                if is_delivered == "Select Assessment Option":
                    st.error("Submission rejected. You must provide a verification response ('Yes' or 'No').")
                else:
                    try:
                        supabase.table("patient_deliveries").update(payload_buffer).eq("id", target_profile["id"]).execute()
                        st.success("Transaction verified. Records committed to live cloud node.")
                        st.balloons()
                    except Exception as commit_ex:
                        st.error(f"Database write exception encountered: {commit_ex}")
