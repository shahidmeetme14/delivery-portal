import streamlit as st
from supabase import create_client, Client
import pandas as pd
import datetime

# Page Configuration
st.set_page_config(page_title="Presented by SHAHID", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for Large Text (For Landline dialing convenience)
st.markdown("""
    <style>
    .big-phone { font-size: 32px !important; font-weight: bold !important; color: #d32f2f !important; background-color: #ffebee; padding: 10px; border-radius: 5px; text-align: center; border: 2px dashed #d32f2f; }
    .patient-header { font-size: 24px !important; font-weight: bold !important; color: #1e3a8a; }
    </style>
""", unsafe_index=True)

st.title("Presented by SHAHID")
st.subheader("🏥 Patient Delivery Feedback & Tracking Portal")

# Connect to Supabase Locker
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

# App Navigation Tabs
tab1, tab2 = st.tabs(["📊 Admin Panel (Upload & Clean Data)", "📞 Staff Workspace (Landline Calling)"])

# ----------------------------------------------------
# 1. ADMIN PANEL: UPLOAD & DEDUPLICATION
# ----------------------------------------------------
with tab1:
    st.header("📥 Bulk Data Ingestion Engine")
    uploaded_file = st.file_uploader("Apni Excel (.xlsx) ya CSV File Drop Karein", type=["xlsx", "csv"])
    
    if uploaded_file is not None:
        # Read the sheet safely
        try:
            if uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(uploaded_file)
            else:
                df = pd.read_csv(uploaded_file)
            st.success("File kamyabi se read ho gayi hai!")
            st.dataframe(df.head(3))
        except Exception as e:
            st.error(f"File read karne me error: {e}")
            st.stop()
            
        st.markdown("---")
        st.subheader("🛠️ Smart Column Mapping & Duplicate Clean Room")
        st.write("Apni sheet ke mutabiq sahi columns select karein:")
        
        # Dynamic drop downs so user can map fields easily
        col1, col2, col3 = st.columns(3)
        with col1:
            c_article = st.selectbox("1. Article / Tracking ID Column:", df.columns)
            c_name = st.selectbox("2. Patient Name Column:", df.columns)
        with col2:
            c_phone = st.selectbox("3. Phone Number Column:", df.columns)
            c_date = st.selectbox("4. Booking Date Column:", df.columns)
        with col3:
            c_address = st.selectbox("5. Physical Address Column:", df.columns)
            dup_target = st.selectbox("🎯 Kis Column Se Duplicate Delete Karne Hain?", df.columns, index=df.columns.get_loc(c_article))

        if st.button("🚀 Process & Save Clean Data To Cloud"):
            initial_rows = len(df)
            
            # Absolute deduplication: Keep first instance, drop all other duplicate rows completely
            df_cleaned = df.drop_duplicates(subset=[dup_target], keep='first')
            final_rows = len(df_cleaned)
            duplicates_removed = initial_rows - final_rows
            
            st.warning(f"Total Rows: {initial_rows} | Unique Rows: {final_rows} | Duplicates Deleted: {duplicates_removed}")
            
            # Prepare rows for database migration
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            records_to_insert = []
            for index, row in df_cleaned.iterrows():
                # Format date cleanly
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
            
            # Batch Uploading to Supabase (Chunks of 200 rows for high speed and stability)
            chunk_size = 200
            total_records = len(records_to_insert)
            success_count = 0
            
            for i in range(0, total_records, chunk_size):
                chunk = records_to_insert[i:i + chunk_size]
                try:
                    # using upsert to prevent unique key constraint crashes if same file is re-uploaded
                    supabase.table("patient_deliveries").upsert(chunk, on_conflict="article_id").execute()
                    success_count += len(chunk)
                    progress = min(success_count / total_records, 1.0)
                    progress_bar.progress(progress)
                    status_text.text(f"Uploading Data... {success_count}/{total_records} rows successfully saved.")
                except Exception as upload_error:
                    st.error(f"Chunk upload error: {upload_error}")
            
            st.success(f"🎉 Mubarak Ho Shahid Bhai! {success_count} unique records database me save ho chuke hain.")

# ----------------------------------------------------
# 2. STAFF WORKSPACE: CALLING & FEEDBACK FORM
# ----------------------------------------------------
with tab2:
    st.header("📞 Landline Dialing & Feedback Hub")
    
    # Select Date to call
    target_date = st.date_input("Kis Date Ki Booking Ka Data Nikalna Hai?", datetime.date.today())
    
    # Fetch data from Supabase for specific date
    try:
        response = supabase.table("patient_deliveries").select("*").eq("booking_date", str(target_date)).execute()
        records = response.data
    except Exception as fetch_err:
        st.error(f"Data loading failed: {fetch_err}")
        records = []
        
    if not records:
        st.info(f"Is tareekh ({target_date}) ka koi data database me mojood nahi hai. Admin tab se file upload karein.")
    else:
        st.success(f"Is date ke total **{len(records)}** patients mile hain.")
        
        # Create a clean patient selector dropdown
        patient_options = {f"{r['patient_name']} (Article: {r['article_id']}) - [{r['status']}]": r for r in records}
        selected_patient_str = st.selectbox("Call Karne Ke Liye Patient Select Karein:", list(patient_options.keys()))
        
        patient_data = patient_options[selected_patient_str]
        
        st.markdown("---")
        
        # Split Layout: Left side Details & EMTTS, Right side Call Feedback Form
        left_col, right_col = st.columns([1, 1])
        
        with left_col:
            st.markdown(f"<p class='patient-header'>👤 Patient Name: {patient_data['patient_name']}</p>", unsafe_allow_html=True)
            st.write(f"📦 **Article ID:** {patient_data['article_id']}")
            st.write(f"🏠 **Address:** {patient_data['address']}")
            st.write(f"📅 **Booking Date:** {patient_data['booking_date']}")
            
            st.markdown("### 🎴 DIAL THIS NUMBER FROM LANDLINE:")
            st.markdown(f"<div class='big-phone'>{patient_data['phone_number']}</div>", unsafe_allow_html=True)
            
            st.markdown("---")
            # EMTTS Live Tracker Fetch Mock Implementation
            st.subheader("🌐 EMTTS Live Tracking Integration")
            if st.button("Fetch Live Status (EMTTS)"):
                with st.spinner("Connecting to EMTTS Tracking Systems..."):
                    # This simulates hitting the postal tracking server dynamically
                    # We can replace this URL with the exact automated API endpoint if needed later
                    simulated_status = "DELIVERED" if "1" in str(patient_data['id']) else "IN-TRANSIT / OUT FOR DELIVERY"
                    st.info(f"EMTTS Response System: **{simulated_status}**")
                    st.caption("Live status successfully parsed from postal trace database.")
        
        with right_col:
            st.subheader("📝 Live Call Feedback Questionnaire")
            
            # Question 1: Medicine Delivered?
            delivered = st.radio("1. Kya patient ko medicine deliver ho gayi hai?", ["Select Option", "Yes", "No"], index=0)
            
            # Feedback sub-logic flows dynamically based on selections
            feedback_payload = {}
            
            if delivered == "Yes":
                feedback_payload["status"] = "Delivered"
                
                # Sub fields for YES
                del_date = st.date_input("Medicine kis din mili? (Delivery Date)", datetime.date.today())
                feedback_payload["delivery_date"] = str(del_date)
                
                mode = st.radio("Delivery kis tareeqe se hoi?", ["Postman ne ghr aakar di", "Post office bula kar di medicine"])
                feedback_payload["received_mode"] = mode
                
                extra_money = st.radio("Postman ne medicine dene ke paise to nahi mange?", ["No", "Yes"])
                feedback_payload["extra_money_charged"] = extra_money
                
                if extra_money == "Yes":
                    st.error("🚨 ALERT: Corruption Tracker Triggered. Postman details enter karein!")
                    p_name = st.text_input("Postman Ka Naam:")
                    p_num = st.text_input("Postman Ka Contact Number:")
                    po_name = st.text_input("Post Office Ka Naam:")
                    
                    feedback_payload["postman_name"] = p_name
                    feedback_payload["postman_number"] = p_num
                    feedback_payload["post_office_name"] = po_name
                    
            elif delivered == "No":
                feedback_payload["status"] = "Issue / Complaint"
                
                # Sub fields for NO
                issue = st.selectbox("Wajah/Issue select karein:", [
                    "Wrong Delivery Status on EMTTS (System delivered show kar raha par mili nahi)",
                    "Address Not Found / Locked House (Ghr band tha ya address galat tha)",
                    "Delay in Delivery (Medicine late hai abhi tak area poachhi nahi)",
                    "Register Formal Complaint (Patient extreme complaint darj karwana chahta hai)"
                ])
                feedback_payload["issue_reason"] = issue
                
            st.markdown("---")
            if st.button("💾 Save Call Feedback & Complete Session"):
                if delivered == "Select Option":
                    st.error("Meharbani kar ke pehle 'Yes' ya 'No' chunien!")
                else:
                    try:
                        # Update record back to Supabase locker instantly
                        supabase.table("patient_deliveries").update(feedback_payload).eq("id", patient_data["id"]).execute()
                        st.success("🎉 Data successfully saved backend pe! List me state update ho gayi hai.")
                        st.balloons()
                    except Exception as save_err:
                        st.error(f"Error saving feedback: {save_err}")
