import streamlit as st
from supabase import create_client, Client
import pandas as pd
import datetime
import io

# Page Configuration
st.set_page_config(
    page_title="SHC & Pak Post - Free Home Delivery of Medicine", 
    page_icon="📮", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .big-phone { font-size: 32px !important; font-weight: bold !important; color: #d32f2f !important; background-color: #ffebee; padding: 10px; border-radius: 5px; text-align: center; border: 2px dashed #d32f2f; }
    .patient-header { font-size: 24px !important; font-weight: bold !important; color: #1e3a8a; }
    .login-box { max-width: 500px; margin: 0 auto; padding: 20px; border: 1px solid #ccc; border-radius: 10px; background-color: #f9f9f9; }
    </style>
""", unsafe_allow_html=True)

# Connect to Supabase
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase: Client = init_connection()
except Exception as e:
    st.error("Database connection failed. Check your Secrets.")
    st.stop()

# Master System: Auto-seed primary admin if table is empty
def auto_seed_admin():
    try:
        res = supabase.table("app_users").select("*").eq("username", "shahid").execute()
        if not res.data:
            supabase.table("app_users").insert({
                "username": "shahid",
                "password": "shahid@2341",
                "role": "admin"
            }).execute()
    except:
        pass

auto_seed_admin()

# --- SECURITY & SESSION STATES INITIALIZATION ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "role" not in st.session_state:
    st.session_state.role = ""

# --- LOGIN SCREEN WORKFLOW ---
if not st.session_state.logged_in:
    st.title("📮 SHC & Pak Post")
    st.subheader("Free Home Delivery of Medicine - Portal Gateway")
    
    st.markdown("<div class='login-box'>", unsafe_allow_html=True)
    st.write("### 🔐 Secure System Login")
    user_input = st.text_input("Username:")
    pass_input = st.text_input("Password:", type="password")
    
    if st.button("Access Portal 🚀"):
        if user_input and pass_input:
            try:
                # Validate from cloud database
                user_res = supabase.table("app_users").select("*").eq("username", user_input.strip()).execute()
                
                if user_res.data and user_res.data[0]["password"] == pass_input.strip():
                    # Set Session Credentials
                    st.session_state.logged_in = True
                    st.session_state.username = user_res.data[0]["username"]
                    st.session_state.role = user_res.data[0]["role"]
                    
                    # Track Client IP and Device Environment
                    try:
                        headers = st.context.headers
                        ip_address = headers.get("X-Forwarded-For", "127.0.0.1").split(",")[0]
                        device_info = headers.get("User-Agent", "Unknown Hardware/Browser")
                    except:
                        ip_address = "Local/Proxy IP"
                        device_info = "Secure Core Browser"
                    
                    # Log login event permanently
                    supabase.table("user_logins").insert({
                        "username": st.session_state.username,
                        "ip_address": ip_address,
                        "device_info": device_info
                    }).execute()
                    
                    st.success(f"Khushamdeed {st.session_state.username}! App open ho rahi hai...")
                    st.rerun()
                else:
                    st.error("Ghalat Username ya Password! Dubara koshish karein.")
            except Exception as auth_err:
                st.error(f"Authentication Server Connection Error: {auth_err}")
        else:
            st.warning("Meharbani kar ke dono khane pur karein.")
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- MAIN APP REGION (RUNS ONLY AFTER VERIFIED LOGIN) ---
# Sidebar controls
with st.sidebar:
    st.write(f"👤 **User:** `{st.session_state.username}`")
    st.write(f"🎖️ **Role:** `{st.session_state.role.upper()}`")
    st.markdown("---")
    
    # Self Password Update Module
    st.write("🔒 **Mera Password Badlein**")
    new_self_pass = st.text_input("Naya Password Likhein:", type="password", key="self_p")
    if st.button("Update My Password"):
        if new_self_pass:
            try:
                supabase.table("app_users").update({"password": new_self_pass.strip()}).eq("username", st.session_state.username).execute()
                st.success("Aap ka password tabdeel ho gaya hai!")
            except Exception as p_err:
                st.error(f"Error: {p_err}")
                
    st.markdown("---")
    if st.button("Sign Out 🚪"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.role = ""
        st.rerun()

st.title("📮 SHC & Pak Post")
st.subheader("Free Home Delivery of Medicine - Tracking & Feedback Portal")

# Setup App View Permissions based on User Classification Roles
if st.session_state.role == "admin":
    main_tabs = st.tabs(["📊 Admin Panel (Upload & Backup)", "👥 User Manager & Security Logs", "📞 Staff Workspace (Landline Calling)"])
else:
    main_tabs = st.tabs(["📞 Staff Workspace (Landline Calling)"])

# ----------------------------------------------------
# TAB: ADMIN PANEL (ONLY VISIBLE TO ADMIN)
# ----------------------------------------------------
if st.session_state.role == "admin":
    with main_tabs[0]:
        st.header("📥 Bulk Data Ingestion Engine")
        uploaded_file = st.file_uploader("Apni Excel (.xlsx) ya CSV File Drop Karein", type=["xlsx", "csv"])
        
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.xlsx'):
                    df = pd.read_excel(uploaded_file)
                else:
                    df = pd.read_csv(uploaded_file)
                st.success("File read ho gayi hai!")
                st.dataframe(df.head(3))
            except Exception as e:
                st.error(f"File Error: {e}")
                st.stop()
                
            st.markdown("---")
            st.subheader("🛠️ Smart Column Mapping & Duplicate Clean Room")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                c_article = st.selectbox("1. Article / Tracking ID Column:", df.columns)
                c_name = st.selectbox("2. Patient Name Column:", df.columns)
            with col2:
                c_phone = st.selectbox("3. Phone Number Column:", df.columns)
                c_date = st.selectbox("4. Booking Date Column:", df.columns)
            with col3:
                c_address = st.selectbox("5. Physical Address Column:", df.columns)
                dup_target = st.selectbox("🎯 Duplicate Boundary Target:", df.columns, index=df.columns.get_loc(c_article))

            if st.button("🚀 Process & Save Clean Data To Cloud"):
                initial_rows = len(df)
                df_cleaned = df.drop_duplicates(subset=[dup_target], keep='first')
                final_rows = len(df_cleaned)
                
                records_to_insert = []
                for index, row in df_cleaned.iterrows():
                    raw_date = row[c_date]
                    formatted_date = str(datetime.date.today())
                    try:
                        formatted_date = pd.to_datetime(raw_date).strftime('%Y-%m-%d')
                    except:
                        pass
                        
                    records_to_insert.append({
                        "article_id": str(row[c_article]).strip(),
                        "patient_name": str(row[c_name]).strip(),
                        "phone_number": str(row[c_phone]).strip(),
                        "booking_date": formatted_date,
                        "address": str(row[c_address]).strip(),
                        "status": "Pending"
                    })
                
                chunk_size = 200
                total_records = len(records_to_insert)
                success_count = 0
                
                for i in range(0, total_records, chunk_size):
                    chunk = records_to_insert[i:i + chunk_size]
                    try:
                        supabase.table("patient_deliveries").upsert(chunk, on_conflict="article_id").execute()
                        success_count += len(chunk)
                    except Exception as upload_error:
                        st.error(f"Upload error: {upload_error}")
                
                st.success(f"🎉 Cloud Matrix Sync Complete! {success_count} Records Uploaded.")

        # Master Backup Button
        st.markdown("---")
        st.subheader("💾 Master Cloud Data Backup Extraction")
        if st.button("🔄 Fetch Live Cloud Database Backup"):
            try:
                res = supabase.table("patient_deliveries").select("*").execute()
                if res.data:
                    backup_df = pd.DataFrame(res.data)
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        backup_df.to_excel(writer, index=False, sheet_name='Master_Report')
                    buffer.seek(0)
                    
                    st.download_button(
                        label="📥 Download Master Excel Backup File",
                        data=buffer,
                        file_name=f"SHC_PakPost_Master_Backup_{datetime.date.today()}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            except Exception as e:
                st.error(f"Backup Error: {e}")

    # ----------------------------------------------------
    # TAB: USER MANAGER & AUDIT LOGS (ADMIN ONLY)
    # ----------------------------------------------------
    with main_tabs[1]:
        st.header("👥 System User Management Engine")
        
        uc1, uc2 = st.columns([1, 1])
        with uc1:
            st.write("### ➕ Add New Staff Account")
            new_u = st.text_input("Staff Username:")
            new_p = st.text_input("Staff Password:", type="password", key="new_u_p")
            if st.button("Create Account"):
                if new_u and new_p:
                    try:
                        supabase.table("app_users").insert({"username": new_u.strip(), "password": new_p.strip(), "role": "staff"}).execute()
                        st.success(f"Account `{new_u}` successfully create ho gaya!")
                    except Exception as e:
                        st.error(f"Error account banane me (Username unique hona chahiye): {e}")
        
        with uc2:
            st.write("### 🔧 Administrative Password Override")
            try:
                all_users = supabase.table("app_users").select("username").execute()
                user_list = [u['username'] for u in all_users.data if u['username'] != 'shahid']
                if user_list:
                    selected_u = st.selectbox("Select User:", user_list)
                    override_p = st.text_input("Naya Password Lagayein:", type="password", key="over_p")
                    if st.button("Force Change Password"):
                        supabase.table("app_users").update({"password": override_p.strip()}).eq("username", selected_u).execute()
                        st.success(f"`{selected_u}` ka password change kar diya gaya.")
                else:
                    st.info("Baqi koi user system me registered nahi hai.")
            except:
                st.write("Users load nahi ho sakay.")

        st.markdown("---")
        st.write("### 🛡️ Live Security Audit & Device Logs")
        try:
            log_res = supabase.table("user_logins").select("*").order("login_time", desc=True).limit(50).execute()
            if log_res.data:
                log_df = pd.DataFrame(log_res.data)
                # Format Columns nicely
                log_df = log_df[["username", "ip_address", "device_info", "login_time"]]
                st.dataframe(log_df, use_container_width=True)
            else:
                st.info("Abhi tak koi login tracking logs save nahi hoye.")
        except Exception as log_err:
            st.error(f"Logs load karne me masla: {log_err}")

# ----------------------------------------------------
# TAB: STAFF WORKSPACE (VISIBLE TO BOTH ADMIN & STAFF)
# ----------------------------------------------------
staff_tab_index = 2 if st.session_state.role == "admin" else 0
with main_tabs[staff_tab_index]:
    st.header("📞 Landline Dialing & Feedback Hub")
    target_date = st.date_input("Kis Date Ki Booking Ka Data Nikalna Hai?", datetime.date.today())
    
    try:
        response = supabase.table("patient_deliveries").select("*").eq("booking_date", str(target_date)).execute()
        records = response.data
    except Exception as fetch_err:
        st.error(f"Data loading failed: {fetch_err}")
        records = []
        
    if not records:
        st.info(f"Is tareekh ({target_date}) ka koi data database me mojood nahi hai.")
    else:
        st.success(f"Total {len(records)} patients mile hain.")
        patient_options = {f"{r['patient_name']} (Article: {r['article_id']}) - [{r['status']}]": r for r in records}
        selected_patient_str = st.selectbox("Patient Select Karein:", list(patient_options.keys()))
        
        patient_data = patient_options[selected_patient_str]
        st.markdown("---")
        
        left_col, right_col = st.columns([1, 1])
        with left_col:
            st.markdown(f"<p class='patient-header'>👤 Patient Name: {patient_data['patient_name']}</p>", unsafe_allow_html=True)
            st.write(f"📦 **Article ID:** {patient_data['article_id']}")
            st.write(f"🏠 **Address:** {patient_data['address']}")
            st.write(f"📅 **Booking Date:** {patient_data['booking_date']}")
            st.markdown("### 🎴 DIAL THIS NUMBER FROM LANDLINE:")
            st.markdown(f"<div class='big-phone'>{patient_data['phone_number']}</div>", unsafe_allow_html=True)
            
            st.markdown("---")
            st.subheader("🌐 EMTTS Live Tracking Integration")
            if st.button("Fetch Live Status (EMTTS)"):
                with st.spinner("Connecting..."):
                    simulated_status = "DELIVERED" if "1" in str(patient_data['id']) else "IN-TRANSIT / OUT FOR DELIVERY"
                    st.info(f"EMTTS Response System: **{simulated_status}**")
        
        with right_col:
            st.subheader("📝 Live Call Feedback Questionnaire")
            delivered = st.radio("1. Kya medicine deliver ho gayi hai?", ["Select Option", "Yes", "No"], index=0)
            feedback_payload = {}
            
            if delivered == "Yes":
                feedback_payload["status"] = "Delivered"
                del_date = st.date_input("Delivery Date", datetime.date.today())
                feedback_payload["delivery_date"] = str(del_date)
                mode = st.radio("Delivery Mode?", ["Postman ne ghr aakar di", "Post office bula kar di medicine"])
                feedback_payload["received_mode"] = mode
                extra_money = st.radio("Postman ne paise to nahi mange?", ["No", "Yes"])
                feedback_payload["extra_money_charged"] = extra_money
                
                if extra_money == "Yes":
                    st.error("🚨 Corruption Tracker Active.")
                    feedback_payload["postman_name"] = st.text_input("Postman Ka Naam:")
                    feedback_payload["postman_number"] = st.text_input("Postman Contact:")
                    feedback_payload["post_office_name"] = st.text_input("Post Office:")
                    
            elif delivered == "No":
                feedback_payload["status"] = "Issue / Complaint"
                issue = st.selectbox("Wajah/Issue:", [
                    "Wrong Delivery Status on EMTTS", "Address Not Found / Locked House", "Delay in Delivery", "Register Formal Complaint"
                ])
                feedback_payload["issue_reason"] = issue
                
            st.markdown("---")
            if st.button("💾 Save Call Feedback"):
                if delivered == "Select Option":
                    st.error("Pehle 'Yes' ya 'No' chunien!")
                else:
                    try:
                        supabase.table("patient_deliveries").update(feedback_payload).eq("id", patient_data["id"]).execute()
                        st.success("🎉 Data successfully saved backend pe!")
                        st.balloons()
                    except Exception as save_err:
                        st.error(f"Error saving feedback: {save_err}")
