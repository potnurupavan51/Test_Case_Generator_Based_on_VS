# app_simple.py

import streamlit as st
import os
from pathlib import Path
from backend import (
    get_llm_chain, 
    get_test_case_generation_chain, 
    parse_test_cases_from_response, 
    create_excel_file
)
import docx
from pypdf import PdfReader
import io
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# --- CUSTOM STYLING ---
def add_custom_styling():
    st.markdown("""
    <style>
        /* Main app background */
        .stApp {
            background: linear-gradient(
                180deg,
                #FFFFFF 0%,
                #E3F2FD 25%,
                #90CAF9 50%,
                #42A5F5 75%,
                #1E88E5 100%
            );
            min-height: 100vh;
        }

        /* Remove all box backgrounds */
        div[data-testid="stVerticalBlock"] > div {
            background: transparent !important;
            box-shadow: none !important;
            padding: 0.3rem;
        }

        /* Title styling */
        h1 {
            color: white;
            text-align: center;
            font-size: 1.8rem;
            margin: 0.3rem 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
            font-weight: 700;
        }

        h2 {
            color: white;
            font-size: 1rem;
            margin: 0.3rem 0;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
            font-weight: 600;
        }

        /* Button styling */
        .stButton > button {
            background: white;
            color: #1e3a8a;
            border: 2px solid #1e3a8a;
            border-radius: 8px;
            padding: 0.4rem 1rem;
            font-size: 0.9rem;
            font-weight: 600;
            width: 100%;
        }
        
        .stButton > button:hover {
            background: #dbeafe;
            border-color: #3b82f6;
        }

        /* Download button */
        .stDownloadButton > button {
            background: #1e3a8a;
            color: white;
            border: 2px solid #1e3a8a;
            border-radius: 8px;
            padding: 0.4rem 1rem;
            font-size: 0.9rem;
            font-weight: 600;
            width: 100%;
        }
        
        .stDownloadButton > button:hover {
            background: #3b82f6;
            border-color: #3b82f6;
        }

        /* File uploader */
        [data-testid="stFileUploader"] {
            background: white;
            border-radius: 8px;
            padding: 0.4rem;
        }

        [data-testid="stFileUploader"] section {
            padding: 0.3rem;
            min-height: 60px;
        }

        /* Chat messages */
        .stChatMessage {
            padding: 0.3rem;
            margin: 0.2rem 0;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.3) !important;
            backdrop-filter: blur(10px);
        }
        
        /* Chat message content */
        [data-testid="stChatMessageContent"] {
            background: transparent !important;
        }

        /* Metrics */
        [data-testid="stMetric"] {
            background: white;
            padding: 0.5rem;
            border-radius: 8px;
        }

        [data-testid="stMetricValue"] {
            font-size: 1.5rem;
            color: #1e3a8a;
            font-weight: 700;
        }
        
        [data-testid="stMetricLabel"] {
            color: #333;
            font-weight: 600;
        }

        [data-testid="stMetricLabel"] {
            font-size: 0.8rem;
        }

        /* Compact dataframe */
        [data-testid="stDataFrame"] {
            border-radius: 8px;
            max-height: 150px;
        }

        /* Compact expander */
        .streamlit-expanderHeader {
            font-size: 0.85rem;
            padding: 0.2rem;
            background: rgba(255,255,255,0.8);
            border-radius: 8px;
            backdrop-filter: blur(10px);
        }

        /* Chat input */
        [data-testid="stChatInput"] {
            background: rgba(255, 255, 255, 0.9);
            border-radius: 8px;
            backdrop-filter: blur(10px);
        }

        /* Remove all padding */
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            max-width: 100%;
        }

        /* Logo styling */
        img {
            border-radius: 8px;
            background: white;
            padding: 0.5rem;
            max-width: 100%;
            height: auto;
            object-fit: contain;
            image-rendering: -webkit-optimize-contrast;
            image-rendering: crisp-edges;
        }

        /* Info/Success boxes */
        .stAlert {
            padding: 0.3rem;
            font-size: 0.85rem;
            background: white;
            border-radius: 8px;
        }

        /* Hide scrollbar */
        ::-webkit-scrollbar {
            display: none;
        }

        /* Chat container fixed height */
        [data-testid="stChatMessageContainer"] {
            max-height: 300px;
            overflow-y: auto;
        }

        /* Reduce all gaps */
        .stMarkdown, [data-testid="stVerticalBlock"] {
            gap: 0.2rem;
        }
    </style>
    """, unsafe_allow_html=True)

# --- TEXT EXTRACTION ---
def extract_text_from_file(uploaded_file):
    logger.info(f"Starting text extraction from file: {uploaded_file.name}")
    if uploaded_file is None: 
        logger.warning("No file uploaded")
        return None
    
    file_extension = uploaded_file.name.split('.')[-1].lower()
    text = ""
    
    try:
        if file_extension == "pdf":
            logger.info("Processing PDF file")
            pdf_reader = PdfReader(io.BytesIO(uploaded_file.getvalue()))
            for i, page in enumerate(pdf_reader.pages):
                text += page.extract_text() or ""
                logger.info(f"Extracted text from page {i+1}")
        elif file_extension == "docx":
            logger.info("Processing DOCX file")
            doc = docx.Document(io.BytesIO(uploaded_file.getvalue()))
            for i, para in enumerate(doc.paragraphs):
                text += para.text + "\n"
            logger.info(f"Extracted {i+1} paragraphs from DOCX")
        elif file_extension == "txt":
            logger.info("Processing TXT file")
            text = uploaded_file.getvalue().decode("utf-8")
        else:
            logger.error(f"Unsupported file type: .{file_extension}")
            st.error(f"Unsupported file type: .{file_extension}")
            return None
        
        logger.info(f"Successfully extracted {len(text)} characters")
        return text
    except Exception as e:
        logger.error(f"Error processing file: {e}", exc_info=True)
        st.error(f"Error processing file: {e}")
        return None

# --- MAIN APP ---
st.set_page_config(page_title="AI Test Case Generator", layout="wide", initial_sidebar_state="collapsed")
add_custom_styling()

logger.info("Application started")

# Header with logo
BASE_DIR = Path(__file__).parent
col_logo, col_title = st.columns([1, 4])
with col_logo:
    logo_path = os.path.join(BASE_DIR, "logo_main.png")
    
    if os.path.exists(logo_path):
        st.image(logo_path, width=180)
        logger.info("Logo loaded successfully")
    else:
        logger.warning(f"Logo not found at {logo_path}")
        st.warning("Logo image not found")

with col_title:
    st.markdown("<h1>🤖 AI Test Case Generator</h1>", unsafe_allow_html=True)

# Initialize session state
if "document_context" not in st.session_state:
    st.session_state.document_context = None
    st.session_state.document_name = None
    logger.info("Initialized document session state")
if "generated_test_cases" not in st.session_state:
    st.session_state.generated_test_cases = None
    logger.info("Initialized test cases session state")
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
    logger.info("Initialized chat session state")
if "excel_data" not in st.session_state:
    st.session_state.excel_data = None

# Load chains
@st.cache_resource
def load_chains():
    logger.info("Loading AI chains...")
    try:
        general_chain = get_llm_chain()
        test_case_chain = get_test_case_generation_chain()
        logger.info("AI chains loaded successfully")
        return general_chain, test_case_chain
    except Exception as e:
        logger.error(f"Error loading AI chains: {e}", exc_info=True)
        st.error(f"❌ Error loading AI: {e}")
        return None, None

general_chain, test_case_chain = load_chains()

# Create 2x2 grid - TOP ROW
col1, col2 = st.columns(2, gap="small")

# BOX 1: UPLOAD
with col1:
    st.markdown("## 📤 Upload")
    
    uploaded_file = st.file_uploader(
        "Document",
        type=["pdf", "docx", "txt"],
        label_visibility="collapsed"
    )
    
    if uploaded_file:
        if st.session_state.document_name != uploaded_file.name:
            logger.info(f"New file uploaded: {uploaded_file.name}")
            with st.spinner("📄 Processing..."):
                extracted_text = extract_text_from_file(uploaded_file)
                if extracted_text:
                    st.session_state.document_context = extracted_text
                    st.session_state.document_name = uploaded_file.name
                    st.session_state.generated_test_cases = None
                    st.session_state.excel_data = None
                    st.session_state.chat_messages = []
                    logger.info(f"Document processed: {len(extracted_text)} chars")
                    st.success(f"✅ {uploaded_file.name[:30]}")
        
        if st.session_state.document_name:
            if st.button("🚀 Generate", type="primary", use_container_width=True):
                logger.info("Generate button clicked")
                if test_case_chain:
                    # Create a placeholder for status updates
                    status_placeholder = st.empty()
                    
                    try:
                        # Step 1: Processing
                        status_placeholder.info("📄 Processing...")
                        logger.info("Processing document")
                        import time
                        time.sleep(0.5)
                        
                        # Step 2: Understanding
                        status_placeholder.info("🧠 Understanding...")
                        logger.info("Invoking test case generation chain")
                        response = test_case_chain.invoke({
                            "context": st.session_state.document_context, 
                            "query": "Generate comprehensive test cases"
                        })
                        logger.info("Received response from AI")
                        
                        # Step 3: Generating
                        status_placeholder.info("⚙️ Generating...")
                        test_cases_df = parse_test_cases_from_response(response)
                        logger.info(f"Parsed {len(test_cases_df)} test cases")
                        st.session_state.generated_test_cases = test_cases_df
                        
                        # Step 4: Creating Excel
                        status_placeholder.info("📊 Creating...")
                        excel_data = create_excel_file(test_cases_df)
                        logger.info(f"Created Excel file: {len(excel_data)} bytes")
                        st.session_state.excel_data = excel_data
                        
                        # Step 5: Done
                        status_placeholder.success(f"✅ Done! {len(test_cases_df)} cases")
                        time.sleep(1)
                        status_placeholder.empty()
                        st.rerun()
                        
                    except Exception as e:
                        logger.error(f"Error generating test cases: {e}", exc_info=True)
                        status_placeholder.error(f"❌ Error: {str(e)[:50]}")
                else:
                    logger.error("Test case chain not loaded")
                    st.error("❌ AI not loaded")
    else:
        st.info("👆 Upload document")

# BOX 2: DOWNLOAD
with col2:
    st.markdown("## 📥 Download")
    
    if st.session_state.generated_test_cases is not None:
        logger.info("Displaying test case statistics")
        total_cases = len(st.session_state.generated_test_cases)
        
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Total", total_cases)
        with col_b:
            try:
                high_count = (st.session_state.generated_test_cases['Priority'] == 'High').sum()
                st.metric("High", high_count)
            except:
                st.metric("High", "-")
        with col_c:
            try:
                modules = st.session_state.generated_test_cases['Module'].nunique()
                st.metric("Modules", modules)
            except:
                st.metric("Modules", "-")
        
        if st.session_state.excel_data:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            doc_name = st.session_state.document_name.split('.')[0]
            filename = f"TestCases_{doc_name}_{timestamp}.xlsx"
            
            logger.info(f"Excel ready for download: {filename}")
            
            st.download_button(
                label="📥 Download Excel",
                data=st.session_state.excel_data,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True
            )
            
            st.success(f"✅ Ready")
        
        with st.expander("👁️ Preview", expanded=False):
            # Show only top 5 test cases in preview
            preview_df = st.session_state.generated_test_cases.head(5)
            num_preview = len(preview_df)
            
            # Dynamic height: 35px per row + 50px for header
            dynamic_height = (num_preview * 35) + 50
            
            st.dataframe(
                preview_df, 
                use_container_width=True,
                height=dynamic_height
            )
            
            # Show info if there are more test cases
            total_cases = len(st.session_state.generated_test_cases)
            if total_cases > 5:
                st.info(f"📊 Showing 5 of {total_cases} test cases. Download Excel for full list.")
    else:
        st.info("📊 Results appear here")

# BOTTOM ROW - CHAT (Only visible after Excel is ready for download)
if st.session_state.excel_data is not None:
    st.markdown("## 💬 Chat")
    
    if not st.session_state.chat_messages:
        welcome = "👋 Ask me anything about your document! I remember our conversation."
        st.session_state.chat_messages.append({"role": "assistant", "content": welcome})
        logger.info("Initialized chat")
    
    # Display all messages
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input below
    if user_input := st.chat_input("Ask question...", disabled=not st.session_state.document_context):
        logger.info(f"User input: {user_input}")
        
        # Add user message and display it immediately
        st.session_state.chat_messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Generate AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    logger.info("Invoking general chain for chat")
                    if general_chain and st.session_state.document_context:
                        # Build chat history string from previous messages
                        chat_history = ""
                        for msg in st.session_state.chat_messages[:-1]:  # Exclude current message
                            role = "User" if msg["role"] == "user" else "Assistant"
                            chat_history += f"{role}: {msg['content']}\n\n"
                        
                        response = general_chain.invoke({
                            "context": st.session_state.document_context,
                            "chat_history": chat_history,
                            "query": user_input
                        })
                        logger.info("Received chat response")
                    else:
                        response = "Upload document first."
                        logger.warning("Chat attempted without document")
                    
                    st.markdown(response)
                    st.session_state.chat_messages.append({"role": "assistant", "content": response})
                    
                except Exception as e:
                    logger.error(f"Chat error: {e}", exc_info=True)
                    error_msg = f"❌ Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.chat_messages.append({"role": "assistant", "content": error_msg})

logger.info("Page render complete")
