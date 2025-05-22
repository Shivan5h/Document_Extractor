import streamlit as st
import json
import tempfile
import os
import base64
from PIL import Image
import io
import pandas as pd
from anthropic_fix import extract_data_with_direct_client

st.set_page_config(page_title="Purchase Order Extractor", layout="wide")

# Set up styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    .result-container {
        padding: 1.5rem;
        background-color: #f8f9fa;
        border-radius: 0.5rem;
        margin-top: 1rem;
    }
    .json-view {
        font-family: monospace;
        white-space: pre-wrap;
        overflow-x: auto;
        background-color: #f0f0f0;
        padding: 1rem;
        border-radius: 0.3rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">Purchase Order Extractor</div>', unsafe_allow_html=True)
st.markdown("""
This app extracts structured information from purchase order PDFs using a vision model approach.
Upload a purchase order PDF and get back structured data in JSON format.
""")

# Sidebar configuration
st.sidebar.markdown('<div class="sub-header">Configuration</div>', unsafe_allow_html=True)
api_key = st.sidebar.text_input("Anthropic API Key", type="password", 
                               help="Enter your Anthropic API key to use Claude for document extraction")
extraction_mode = st.sidebar.radio(
    "Extraction Mode",
    ["Basic (Standard Fields)", "Advanced (All Fields)"],
    help="Basic mode extracts common fields, Advanced extracts all detected fields"
)

# Template for document extraction prompt
def create_extraction_prompt(pdf_data, mode="basic"):
    template = """
    You are an expert document extraction system specializing in Purchase Order extraction.
    Extract the following information from the provided purchase order document in a structured JSON format:

    1. Purchase order information: PO number, date, expiry date (if available), total amount
    2. Customer information: Customer name, address, email ID, contact number
    3. Vendor information: Vendor name, address, contact, email
    4. Table data: Products/items with their details (convert tables to JSON format)

    Rules:
    - If any information is not present in the document, use null for that field
    - Be precise with field names and values
    - Maintain the structure of tables when converting to JSON
    - For numerical values, preserve the original format (including currency symbols if present)
    - Intelligently handle different PO layouts and formatting anomalies

    Provide ONLY the JSON output with no additional explanation.
    Format the JSON using appropriate indentation for readability.
    """
    
    if mode == "advanced":
        template += """
    Additionally, extract any other fields that might be present in the document, such as:
    - Shipping information
    - Payment terms
    - Discounts
    - Tax information
    - Notes or additional comments
    """
    
    return template


# Function to convert PDF to base64
def get_pdf_as_base64(file_obj):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        temp_file.write(file_obj.getvalue())
        temp_file_path = temp_file.name
    
    with open(temp_file_path, "rb") as pdf_file:
        encoded_string = base64.b64encode(pdf_file.read()).decode()
    
    os.unlink(temp_file_path)
    return encoded_string




# Function to extract PO data using Claude vision model
def extract_po_data(pdf_base64, api_key, mode="basic"):
    # Use the direct client approach to avoid issues with the Anthropic SDK
    return extract_data_with_direct_client(
        pdf_base64=pdf_base64,
        api_key=api_key,
        prompt=create_extraction_prompt(pdf_base64, mode)
    )




# File uploader
uploaded_file = st.file_uploader("Upload Purchase Order PDF", type="pdf")

if uploaded_file is not None:
    # Display PDF preview
    with st.expander("Preview PDF", expanded=True):
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(uploaded_file.getvalue())
            temp_path = temp_file.name
        
        # Display PDF using an iframe
        pdf_display = f'<iframe src="data:application/pdf;base64,{get_pdf_as_base64(uploaded_file)}" width="100%" height="500" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    
    # Process the uploaded file
    if st.button("Extract Purchase Order Data"):
        if not api_key:
            st.error("Please enter your Anthropic API key in the sidebar to proceed.")
        else:
            with st.spinner("Extracting data from the purchase order..."):
                # Reset file pointer
                uploaded_file.seek(0)
                
                # Get PDF as base64
                pdf_base64 = get_pdf_as_base64(uploaded_file)
                
                # Extract data
                mode = "advanced" if extraction_mode == "Advanced (All Fields)" else "basic"
                extracted_data, error = extract_po_data(pdf_base64, api_key, mode)
                
                if error:
                    st.error(error)
                else:
                    # Display extracted data
                    st.markdown('<div class="sub-header">Extracted Purchase Order Data</div>', unsafe_allow_html=True)
                    
                    # JSON View
                    st.markdown('<div class="result-container">', unsafe_allow_html=True)
                    st.json(extracted_data)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Download options
                    st.markdown('<div class="sub-header">Download Options</div>', unsafe_allow_html=True)
                    json_str = json.dumps(extracted_data, indent=2)
                    st.download_button(
                        label="Download JSON",
                        data=json_str,
                        file_name="purchase_order_data.json",
                        mime="application/json"
                    )
                    
                    # Display table data if present
                    if "table_data" in extracted_data and extracted_data["table_data"]:
                        st.markdown('<div class="sub-header">Table Preview</div>', unsafe_allow_html=True)
                        
                        for table_name, table_content in extracted_data["table_data"].items():
                            st.markdown(f"**{table_name}**")
                            if isinstance(table_content, list) and len(table_content) > 0:
                                try:
                                    df = pd.DataFrame(table_content)
                                    st.dataframe(df)
                                except Exception as e:
                                    st.write(table_content)
                    
                    # Store the extracted data in session state for further use
                    st.session_state['extracted_data'] = extracted_data


# Additional info section
with st.expander("About This App"):
    st.markdown("""
    ### How It Works
    
    This application uses Claude's vision capabilities to analyze purchase order documents and extract structured information.
    
    1. **Upload**: The app accepts PDF purchase orders
    2. **Process**: The document is processed using Anthropic's Claude vision model
    3. **Extract**: Structured data is extracted including PO details, customer information, vendor details, and table data
    4. **Result**: The extracted information is presented in a structured JSON format
    
    ### Tips for Best Results
    
    - Ensure PDFs are clear and not scanned at low resolution
    - For complex tables, use the Advanced extraction mode
    - If information is missing, check if it exists in the original document
    
    ### Privacy Note
    
    All processing is done via the Anthropic API. Your API key and documents are sent directly to Anthropic.
    This app does not store any of your documents or extracted data permanently.
    """)