import streamlit as st
from supabase import create_client, Client
import pandas as pd
import requests

# Page Configuration
st.set_page_config(page_title="Presented by SHAHID", layout="wide")
st.title("Presented by SHAHID")
st.subheader("Patient Delivery Feedback & Tracking Portal")

# Connect to Supabase
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase: Client = init_connection()
except Exception as e:
    st.error("Database connection configuration missing. Please complete Step 4.")
    st.stop()

# Tabs for Admin and Staff
tab1, tab2 = st.tabs(["📊 Admin Dashboard (Upload & Clean)", "📞 Staff Dashboard (Call & Feedback)"])

# ----------------- ADMIN DASHBOARD -----------------
with tab1:
    st.header("Bulk Data Upload Section")
    uploaded_file = st.file_uploader("Apni Excel (.xlsx) ya CSV File Upload Karein", type=["xlsx", "csv"])
    
    if uploaded_file is not None:
        # Read Data
        if uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file)
            
        st.write("File Data Preview (Pehli 5 rows):")
        st.dataframe(df.head())
        
        # Duplicate Removal Settings
        st.markdown("---")
        st.subheader("🛠️ Duplicate Entries Clean Karne Ka System")
        
        # Dropdown to select column for uniqueness
        dup_column = st.selectbox(
            "Woh Column Chunien Jis Se Duplicate Check Karna Hai (e.g., Article ID ya Phone):", 
            df.columns
        )
        
        if st.button("Duplicates Saaf Karein aur Database me Save Karein"):
            initial_count = len(df)
            
            # Clean Duplicates: Keep first, delete rest entirely
            df_cleaned = df.drop_duplicates(subset=[dup_column], keep='first')
            final_count = len(df_cleaned)
            removed_count = initial_count - final_count
            
            st.success(f"Mubarak ho! Total {removed_count} duplicate rows poori tarah delete kar di gayeen.")
            st.info(f"Ab {final_count} unique records database me save honay ke liye tayyar hain.")
            
            # TODO: Add Supabase insertion chunking logic in next phase

# ----------------- STAFF DASHBOARD -----------------
with tab2:
    st.header("Staff Calling Area")
    search_date = st.date_input("Kis Date Ki Booking Kholni Hai?")
    st.info("Date select karne par yahan us din ke patients ki list aur unka EMTTS live status show hoga.")
