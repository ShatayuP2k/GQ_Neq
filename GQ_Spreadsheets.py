import pandas as pd
import numpy as np
import streamlit as st
import io
import zipfile

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def process_batch_data(master_sheet, batch_info):
    """
    Processes a single dataframe and returns BOTH AISensy and Exotel formatted dataframes.
    """
    master_sheet['Name'] = master_sheet['Name'].replace(r'^\s*$', np.nan, regex=True)
    master_sheet = master_sheet.dropna(subset=['Name']).copy()
    
    first_name = master_sheet['Name'].str.split(" ").str[0]
    last_name = master_sheet['Name'].str.split(" ").str[-1]
    
    phone_number = master_sheet['Phone'].astype(str).str.replace('+', '', regex=False).str[2:]
    email_id = master_sheet.get('Email', "")

    aisensy_df = pd.DataFrame({
        'First Name': first_name,
        'Last Name': last_name,
        'Phone Number': phone_number,
        'Email Id': email_id,
        'Batch Number': batch_info['Batch Number'],
        'Session Date': batch_info['Session Date'],
        'Time Slot': batch_info['Time Slot'],
        'Session days': batch_info['Session days'],
        'Zoom Link': master_sheet.get('Zoom Link', ""),
        'meeting id': master_sheet.get('meeting id', ""),
        'Whatsapp Link': master_sheet.get('Whatsapp Link', ""),
        'Whatsapp id': master_sheet.get('Whatsapp id', ""),
        'Batch Leader': batch_info['Batch Leader'],
        'Leader Number': "", 
        'Gender': ""         
    })
    
    exotel_df = pd.DataFrame({
        'number': phone_number,
        'first_name': first_name,
        'last_name': last_name,
        'company_name': "GitaQuest",
        'email': email_id,
        'tag': "member",
        'custom_field': '{"key":{"key1":"values1"}}'
    })
    
    return aisensy_df, exotel_df

def clear_all_data():
    """
    Callback function to completely wipe all memory and reset visual inputs.
    """
    # 1. Clear the generated tables
    st.session_state.generated_data = None
    st.session_state.is_generated = False
    
    # 2. Reset the Number of Batches counter back to 1
    st.session_state.num_batches_input = 1
    
    # 3. Force all text boxes to be completely empty, and clear the file uploaders
    for key in list(st.session_state.keys()):
        if key.startswith(('bn_', 'sd_', 'ts_', 'days_', 'bl_')):
            st.session_state[key] = ""  # Explicitly overwrite text with an empty string
        elif key.startswith('file_'):
            del st.session_state[key]   # Deleting the key is the only way to clear a file_uploader


# ==========================================
# STREAMLIT USER INTERFACE
# ==========================================

st.set_page_config(page_title="Bulk AISensy & Exotel Generator", layout="wide")
st.title("🦚 GQ Spreadsheet Generator")

# --- Initialize Session State ---
if 'generated_data' not in st.session_state:
    st.session_state.generated_data = None
if 'is_generated' not in st.session_state:
    st.session_state.is_generated = False

# ----------------- SIDEBAR -----------------
st.sidebar.markdown("<div style='text-align: center; font-size: 50px;'>🪷</div>", unsafe_allow_html=True)
st.sidebar.header("Batch Configuration")

# Notice the added key="num_batches_input" here so the clear button can control it
num_batches = st.sidebar.number_input(
    "Number of Batches to Process", 
    min_value=1, 
    max_value=10, 
    value=1, 
    key="num_batches_input"
)

all_batches_data = []

for i in range(int(num_batches)):
    with st.sidebar.expander(f"⚙️ Batch {i+1} Settings", expanded=(i==0)):
        uploaded_file = st.file_uploader(f"Upload CSV for Batch {i+1}", type=["csv"], key=f"file_{i}")
        batch_number = st.text_input("Batch Number", key=f"bn_{i}")
        session_date = st.text_input("Session Date", key=f"sd_{i}")
        time_slot = st.text_input("Time Slot", key=f"ts_{i}")
        session_days = st.text_input("Session Days", key=f"days_{i}")
        batch_leader = st.text_input("Batch Leader", key=f"bl_{i}")
        
        batch_dict = {
            'Batch Number': batch_number,
            'Session Date': session_date,
            'Time Slot': time_slot,
            'Session days': session_days,
            'Batch Leader': batch_leader,
            'File': uploaded_file
        }
        all_batches_data.append(batch_dict)

st.sidebar.divider()

# BUTTON 1: Generate Sheets
if st.sidebar.button("Generate All Sheets", type="primary", use_container_width=True):
    missing_files = [i+1 for i, b in enumerate(all_batches_data) if b['File'] is None]
    
    if missing_files:
        st.sidebar.error(f"⚠️ Missing CSV files for Batch(es): {', '.join(map(str, missing_files))}.")
        st.session_state.is_generated = False
    else:
        results = []
        for i, batch in enumerate(all_batches_data):
            df = pd.read_csv(batch['File'])
            aisensy_df, exotel_df = process_batch_data(df, batch)
            safe_batch_name = batch['Batch Number'] if batch['Batch Number'] else f"Batch_{i+1}"
            
            results.append({
                'batch_name': safe_batch_name,
                'aisensy': aisensy_df,
                'exotel': exotel_df
            })
            
        st.session_state.generated_data = results
        st.session_state.is_generated = True

# BUTTON 2: Download All 
if st.session_state.is_generated and st.session_state.generated_data:
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for item in st.session_state.generated_data:
            b_name = item['batch_name']
            
            aisensy_csv = item['aisensy'].to_csv(index=False)
            exotel_csv = item['exotel'].to_csv(index=False)
            
            zip_file.writestr(f"AISensy_{b_name}.csv", aisensy_csv)
            zip_file.writestr(f"Exotel_{b_name}.csv", exotel_csv)
            
    zip_buffer.seek(0)
    
    st.sidebar.download_button(
        label="📦 Download All (ZIP)",
        data=zip_buffer,
        file_name="All_Batch_Sheets.zip",
        mime="application/zip",
        use_container_width=True
    )

# BUTTON 3: Clear All Data
st.sidebar.button("🗑️ Clear All", on_click=clear_all_data, type="secondary", use_container_width=True)


# ----------------- MAIN AREA (PREVIEWS) -----------------
if st.session_state.is_generated and st.session_state.generated_data:
    
    tabs = st.tabs([f"{item['batch_name']} Results" for item in st.session_state.generated_data])
    
    for i, item in enumerate(st.session_state.generated_data):
        with tabs[i]:
            st.success(f"Successfully processed {len(item['aisensy'])} rows!")
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🔵 AISensy Sheet")
                st.dataframe(item['aisensy'], use_container_width=True)
            with col2:
                st.subheader("🟠 Exotel Sheet")
                st.dataframe(item['exotel'], use_container_width=True)
else:
    st.info("Configure your batches in the sidebar and click 'Generate All Sheets' to view previews here.")
