import streamlit as st
import requests
from datetime import date
from config import API_URL


def render_upload_page():
    """Render the upload receipt page"""
    st.markdown("### 📤 Upload Receipt")
    st.markdown("Upload a photo of your receipt to automatically extract and store the data.")

    # Initialize session state for upload tracking
    if "upload_success" not in st.session_state:
        st.session_state.upload_success = False
    if "upload_counter" not in st.session_state:
        st.session_state.upload_counter = 0
    if "uploaded_receipt_id" not in st.session_state:
        st.session_state.uploaded_receipt_id = None

    # Show success notification if upload was successful
    if st.session_state.upload_success and st.session_state.uploaded_receipt_id:
        st.success(f"✅ Receipt #{st.session_state.uploaded_receipt_id} uploaded successfully!")
        st.balloons()
        # Reset the flag
        st.session_state.upload_success = False

    col1, col2 = st.columns([2, 1])

    with col1:
        upload_file = st.file_uploader(
            "Choose receipt image",
            type=["jpg", "jpeg", "png"],
            help="Upload a photo of your receipt (JPG, PNG)",
            key=f"single_upload_file_{st.session_state.upload_counter}",
        )

    with col2:
        purchase_date = st.date_input(
            "Purchase Date",
            value=date.today(),
            max_value=date.today(),
            help="Date of purchase shown on receipt",
            key=f"single_upload_date_{st.session_state.upload_counter}",
        )

    if upload_file is not None:
        st.markdown("##### 🖼️ Preview")
        st.image(upload_file, caption="Receipt Image", use_container_width=True)

    st.markdown("---")

    if st.button("📤 Upload Receipt", type="primary", use_container_width=True):
        if upload_file is None:
            st.warning("⚠️ Please select a file first")
        else:
            with st.spinner("Uploading and processing..."):
                try:
                    files = {"file": (upload_file.name, upload_file, upload_file.type)}
                    data = {"purchase_date": str(purchase_date), "user_id": 1}

                    response = requests.post(f"{API_URL}/receipts", files=files, data=data)

                    if response.status_code == 201:
                        receipt = response.json()

                        # Set success state
                        st.session_state.upload_success = True
                        st.session_state.uploaded_receipt_id = receipt["id"]

                        # Display receipt details in a nice format
                        st.markdown("### ✅ Upload Successful!")

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Receipt ID", f"#{receipt['id']}")
                        with col2:
                            st.metric("Status", receipt["status"].upper())
                        with col3:
                            st.metric("Purchase Date", receipt["purchase_date"])

                        st.info(f"📁 Stored at: `{receipt['image_path']}`")

                        # Show next steps
                        st.markdown("##### 📋 Next Steps")
                        st.markdown(
                            """
                        - Your receipt is being processed automatically
                        - Check the **My Receipts** tab to view extracted data
                        - Processing typically takes 5-10 seconds
                        """
                        )

                        # Reset form by incrementing counter
                        st.session_state.upload_counter += 1
                        st.rerun()
                    else:
                        st.error(f"❌ Upload failed: {response.text}")
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to API. Is the server running?")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
