import streamlit as st
from components import render_header, render_footer
from views import render_upload_page, render_receipts_list, render_bulk_upload_page

st.set_page_config(page_title="Pantry Pilot", page_icon="🥘", layout="wide")

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
