import streamlit as st
from components import render_header, render_footer
from views import render_upload_page, render_receipts_list, render_bulk_upload_page

st.set_page_config(
    page_title="Pantry Pilot - Smart Receipt Management",
    page_icon="🥘",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS for better UI
st.markdown(
    """
<style>
    /* Main container */
    .main > div {
        padding: 2rem 1rem;
    }
    
    /* Buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* File uploader */
    .stFileUploader {
        border-radius: 8px;
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        border-radius: 8px;
        font-weight: 500;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 1.5rem;
        font-weight: 600;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 0.75rem 1.5rem;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Header
render_header()

# Tabs
tab1, tab2, tab3 = st.tabs(["📤 Upload Receipt", "📦 Bulk Upload", "📋 My Receipts"])

with tab1:
    render_upload_page()

with tab2:
    render_bulk_upload_page()

with tab3:
    render_receipts_list()

# Footer
render_footer()
