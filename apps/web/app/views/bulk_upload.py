import streamlit as st
import requests
from datetime import date
from config import API_URL


def render_bulk_upload_page():
    """Render the bulk upload receipts page"""
    st.subheader("Bulk Upload Receipts")

    # Initialize session state for upload tracking
    if "bulk_upload_counter" not in st.session_state:
        st.session_state.bulk_upload_counter = 0

    col1, col2 = st.columns([2, 1])

    with col1:
        upload_files = st.file_uploader(
            "Choose receipt images",
            type=["jpg", "jpeg", "png"],
            help="Upload multiple photos of your receipts",
            accept_multiple_files=True,
            key=f"bulk_upload_files_{st.session_state.bulk_upload_counter}",
        )

    with col2:
        purchase_date = st.date_input(
            "Purchase Date",
            value=date.today(),
            max_value=date.today(),
            key=f"bulk_upload_date_{st.session_state.bulk_upload_counter}",
        )

    if upload_files:
        st.info(f"📎 {len(upload_files)} file(s) selected")

        # Show preview in columns
        cols = st.columns(min(len(upload_files), 3))
        for idx, file in enumerate(upload_files[:3]):
            with cols[idx]:
                st.image(file, caption=f"Preview {idx+1}")

        if len(upload_files) > 3:
            st.caption(f"... and {len(upload_files) - 3} more file(s)")

    if st.button("📤 Upload All Receipts", type="primary"):
        if not upload_files:
            st.warning("⚠️ Please select at least one file")
        else:
            with st.spinner(f"Uploading {len(upload_files)} receipt(s)..."):
                try:
                    # Prepare files for upload
                    files = [("files", (f.name, f.getvalue(), f.type)) for f in upload_files]
                    data = {"purchase_date": str(purchase_date), "user_id": 1}

                    response = requests.post(f"{API_URL}/receipts/bulk", files=files, data=data)

                    if response.status_code == 201:
                        result = response.json()
                        st.success(f"✅ Successfully uploaded {result['total']} receipt(s)!")
                        st.balloons()

                        # Display summary
                        st.markdown("### 📊 Upload Summary")
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.metric("Total Uploaded", result["total"])

                        with col2:
                            st.metric("Purchase Date", str(purchase_date))

                        with col3:
                            st.metric("Status", "UPLOADED")

                        st.info("💡 Check the 'My Receipts' tab to view your uploaded receipts")

                        # Optional: Show raw response
                        with st.expander("🔍 View raw response"):
                            st.json(result)

                        # Reset form by incrementing counter
                        st.session_state.bulk_upload_counter += 1
                        st.rerun()
                    else:
                        st.error(f"❌ Upload failed: {response.text}")
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to API. Is the server running?")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
