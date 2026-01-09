import streamlit as st
import requests
from datetime import date
from config import API_URL


def render_upload_page():
    """Render the upload receipt page"""
    st.subheader("Upload Receipt")

    col1, col2 = st.columns([2, 1])

    with col1:
        upload_file = st.file_uploader(
            "Choose receipt image",
            type=["jpg", "jpeg", "png"],
            help="Upload a photo of your receipt",
            key="single_upload_file"
        )

    with col2:
        purchase_date = st.date_input(
            "Purchase Date",
            value=date.today(),
            max_value=date.today(),
            key="single_upload_date"
        )

    if upload_file is not None:
        st.image(upload_file, caption="Preview", width=300)

    if st.button("📤 Upload Receipt", type="primary"):
        if upload_file is None:
            st.warning("⚠️ Please select a file first")
        else:
            with st.spinner("Uploading..."):
                try:
                    files = {"file": (upload_file.name, upload_file, upload_file.type)}
                    data = {"purchase_date": str(purchase_date), "user_id": 1}

                    response = requests.post(f"{API_URL}/receipts", files=files, data=data)

                    if response.status_code == 201:
                        st.success("✅ Receipt uploaded successfully!")
                        st.balloons()
                        
                        # Display receipt details in a nice format
                        receipt = response.json()
                        
                        st.markdown("### 🧾 Receipt Details")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Receipt ID", f"#{receipt['id']}")
                        
                        with col2:
                            st.metric("Status", receipt['status'].upper())
                        
                        with col3:
                            st.metric("Purchase Date", receipt['purchase_date'])
                        
                        st.info(f"📁 Stored at: `{receipt['image_path']}`")
                        st.caption(f"Created: {receipt.get('created_at', 'N/A')}")
                        
                        # Optional: Show JSON in expander for debugging
                        with st.expander("🔍 View raw data"):
                            st.json(receipt)
                    else:
                        st.error(f"❌ Upload failed: {response.text}")
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to API. Is the server running?")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
