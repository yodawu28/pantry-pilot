import streamlit as st
import requests
from config import API_URL


def render_receipts_list():
    """Render the receipts list page with pagination"""
    st.subheader("My Receipts")

    # Initialize session state for pagination
    if "last_id" not in st.session_state:
        st.session_state.last_id = -1
    if "receipts_history" not in st.session_state:
        st.session_state.receipts_history = []

    col1, col2 = st.columns([3, 1])

    with col2:
        if st.button("🔄 Refresh"):
            st.session_state.last_id = -1
            st.session_state.receipts_history = []
            st.rerun()

    try:
        # Fetch receipts with pagination
        params = {"user_id": 1, "last_id": st.session_state.last_id, "limit": 10}
        response = requests.get(f"{API_URL}/receipts", params=params, timeout=5)

        if response.status_code == 200:
            data = response.json()
            receipts = data.get("receipts", [])
            total = data.get("total", 0)
            new_last_id = data.get("last_id", -1)

            if not receipts and st.session_state.last_id == -1:
                st.info("📭 No receipts yet. Upload one in the **Upload Receipt** tab!")
            else:
                st.caption(f"Showing {total} receipt(s)")

                for receipt in receipts:
                    with st.expander(
                        f"🧾 Receipt #{receipt['id']} — {receipt['purchase_date']}", expanded=False
                    ):
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Status", receipt["status"].upper())
                        col2.metric("Purchase Date", receipt["purchase_date"])
                        col3.metric("Receipt ID", f"#{receipt['id']}")

                        st.caption(f"Created: {receipt['created_at']}")

                        if st.button("View Details", key=f"view_{receipt['id']}"):
                            detail_response = requests.get(f"{API_URL}/receipts/{receipt['id']}")
                            if detail_response.status_code == 200:
                                detail = detail_response.json()

                                st.markdown("#### Receipt Details")

                                # Basic info
                                info_col1, info_col2 = st.columns(2)
                                with info_col1:
                                    st.write("**Receipt ID:**", detail.get("id"))
                                    st.write("**User ID:**", detail.get("user_id"))
                                    st.write("**Status:**", detail.get("status", "").upper())
                                with info_col2:
                                    st.write("**Purchase Date:**", detail.get("purchase_date"))
                                    st.write("**Created At:**", detail.get("created_at"))
                                    st.write("**Updated At:**", detail.get("updated_at"))

                                # Image preview
                                if detail.get("image_url"):
                                    st.markdown("**Receipt Image:**")
                                    st.image(detail["image_url"], caption="Receipt Image")

                                # Raw data (optional, collapsed by default)
                                with st.expander("🔍 View Raw JSON"):
                                    st.json(detail)
                            else:
                                st.error("Failed to fetch receipt details")

                # Pagination controls
                if total > 0 and new_last_id != -1:
                    st.markdown("---")
                    col1, col2, col3 = st.columns([1, 2, 1])

                    with col1:
                        if st.button("⬅️ Previous", disabled=st.session_state.last_id == -1):
                            # Go back (would need to store history for this)
                            if st.session_state.receipts_history:
                                st.session_state.last_id = st.session_state.receipts_history.pop()
                                st.rerun()

                    with col3:
                        if st.button("Next ➡️", disabled=(total < params["limit"])):
                            # Store current last_id in history
                            st.session_state.receipts_history.append(st.session_state.last_id)
                            st.session_state.last_id = new_last_id
                            st.rerun()

        else:
            st.error(f"Failed to fetch receipts: {response.text}")
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to API")
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
