import streamlit as st
import requests
from config import API_URL


def format_price(amount: str | float, currency: str = "VND") -> str:
    """Format price based on currency"""
    try:
        # Convert to float
        price = float(amount)

        # Currency-specific formatting
        if currency == "VND":
            # Vietnamese Dong - no decimals
            return f"{int(price):,}₫"
        elif currency == "USD":
            # US Dollar
            return f"${price:,.2f}"
        elif currency == "EUR":
            # Euro
            return f"€{price:,.2f}"
        elif currency == "GBP":
            # British Pound
            return f"£{price:,.2f}"
        elif currency == "JPY":
            # Japanese Yen - no decimals
            return f"¥{int(price):,}"
        else:
            # Default format
            return f"{currency} {price:,.2f}"
    except (ValueError, TypeError):
        return f"{currency} {amount}"


def render_receipt_status_badge(status: str, ocr_status: str):
    """Render a status badge with color"""
    status_colors = {"pending": "🟡", "processing": "🔵", "completed": "🟢", "failed": "🔴"}
    ocr_colors = {"pending": "⚪", "processing": "🔵", "completed": "🟢", "failed": "🔴"}
    return f"{status_colors.get(status, '⚪')} Status: **{status.upper()}** | {ocr_colors.get(ocr_status, '⚪')} OCR: **{ocr_status.upper()}**"


def render_line_items(items: list):
    """Render line items in a nice table format"""
    if not items:
        st.info("No items extracted yet")
        return

    st.markdown("##### 🛒 Line Items")

    # Create header
    col1, col2, col3, col4 = st.columns([3, 1, 1.2, 1.2])
    with col1:
        st.markdown("**Item Name**")
    with col2:
        st.markdown("**Qty**")
    with col3:
        st.markdown("**Unit Price**")
    with col4:
        st.markdown("**Total**")

    st.divider()

    # Create a formatted table
    for idx, item in enumerate(items, 1):
        currency = item.get("currency", "VND")

        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1.2, 1.2])

            with col1:
                st.markdown(f"**{idx}. {item.get('item_name', 'Unknown')}**")
                if item.get("confidence"):
                    st.caption(f"Confidence: {item['confidence']:.1%}")

            with col2:
                qty = item.get("quantity", 0)
                # Format quantity nicely
                if isinstance(qty, (int, float)):
                    formatted_qty = f"{qty:g}"  # Remove trailing zeros
                else:
                    formatted_qty = str(qty)
                st.text(formatted_qty)

            with col3:
                unit_price = item.get("unit_price", "0")
                st.text(format_price(unit_price, currency))

            with col4:
                total_price = item.get("total_price", "0")
                st.markdown(f"**{format_price(total_price, currency)}**")

            st.divider()


def render_ocr_data(ocr_data: dict):
    """Render OCR extracted data"""
    if not ocr_data:
        return

    st.markdown("##### 📝 Extracted Data (OCR)")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Merchant Information**")
        st.text(f"Name: {ocr_data.get('merchant_name', 'N/A')}")
        st.text(f"Date: {ocr_data.get('purchase_date', 'N/A')}")

    with col2:
        st.markdown("**Financial Information**")
        st.text(f"Total: ${ocr_data.get('total_amount', '0')} {ocr_data.get('currency', 'VND')}")
        st.text(f"Confidence: {ocr_data.get('confidence', 0):.1%}")

    # Show raw text if available
    if ocr_data.get("raw_text"):
        with st.expander("📄 View Raw OCR Text"):
            st.text_area("Raw Text", ocr_data["raw_text"], height=150, disabled=True)


def render_receipts_list():
    """Render the receipts list page with pagination"""
    st.markdown("### 📋 My Receipts")
    st.markdown("View and manage your uploaded receipts")

    # Initialize session state for pagination
    if "last_id" not in st.session_state:
        st.session_state.last_id = -1
    if "receipts_history" not in st.session_state:
        st.session_state.receipts_history = []

    col1, col2 = st.columns([3, 1])

    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
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
                st.caption(f"📊 Showing {len(receipts)} of {total} receipt(s)")

                for receipt in receipts:
                    # Determine expand state based on completion
                    is_completed = receipt.get("ocr_status") == "completed"

                    with st.expander(
                        f"🧾 Receipt #{receipt['id']} — {receipt['purchase_date']} — {receipt.get('merchant_name', 'Processing...')}",
                        expanded=False,
                    ):
                        # Status badges
                        st.markdown(
                            render_receipt_status_badge(
                                receipt.get("status", "pending"),
                                receipt.get("ocr_status", "pending"),
                            )
                        )

                        st.markdown("---")

                        # Basic info
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Receipt ID", f"#{receipt['id']}")
                        with col2:
                            st.metric("Purchase Date", receipt["purchase_date"])
                        with col3:
                            if receipt.get("total_amount"):
                                currency = receipt.get("currency", "VND")
                                formatted_total = format_price(receipt["total_amount"], currency)
                                st.metric("Total Amount", formatted_total)
                            else:
                                st.metric("Total Amount", "Processing...")

                        # Show OCR data if completed
                        if is_completed:
                            st.markdown("---")

                            # Show extracted metadata
                            if receipt.get("merchant_name") or receipt.get("total_amount"):
                                st.markdown("##### 📝 Extracted Data")
                                col1, col2 = st.columns(2)

                                with col1:
                                    st.markdown("**Merchant Information**")
                                    st.text(f"Name: {receipt.get('merchant_name', 'N/A')}")
                                    st.text(f"Date: {receipt.get('purchase_date', 'N/A')}")

                                with col2:
                                    st.markdown("**Financial Information**")
                                    currency = receipt.get("currency", "VND")
                                    formatted_total = format_price(
                                        receipt.get("total_amount", "0"), currency
                                    )
                                    st.text(f"Total: {formatted_total}")

                            # Fetch full details to get line items
                            try:
                                detail_response = requests.get(
                                    f"{API_URL}/receipts/{receipt['id']}"
                                )
                                if detail_response.status_code == 200:
                                    detail = detail_response.json()

                                    # Show line items
                                    if detail.get("items"):
                                        st.markdown("---")
                                        render_line_items(detail["items"])

                                    # Show raw OCR text if available
                                    if detail.get("ocr_text"):
                                        st.markdown("---")
                                        with st.expander("📄 View Raw OCR Text"):
                                            st.text_area(
                                                "Raw Text",
                                                detail["ocr_text"],
                                                height=150,
                                                disabled=True,
                                            )

                                    # Image preview
                                    if detail.get("image_url"):
                                        st.markdown("---")
                                        st.markdown("##### 🖼️ Receipt Image")
                                        st.image(
                                            detail["image_url"],
                                            caption="Receipt Image",
                                            use_container_width=True,
                                        )

                                    # Raw data (optional, collapsed by default)
                                    with st.expander("🔍 View Raw JSON"):
                                        st.json(detail)
                            except Exception as e:
                                st.error(f"Failed to fetch details: {str(e)}")
                        else:
                            # Show processing message
                            st.info("⏳ Receipt is being processed. Refresh to see updated status.")

                        st.caption(f"Created: {receipt.get('created_at', 'N/A')}")

                # Pagination controls
                if total > 0:
                    st.markdown("---")
                    col1, col2, col3 = st.columns([1, 2, 1])

                    with col1:
                        if st.button("⬅️ Previous", disabled=st.session_state.last_id == -1):
                            if st.session_state.receipts_history:
                                st.session_state.last_id = st.session_state.receipts_history.pop()
                                st.rerun()

                    with col3:
                        if st.button("Next ➡️", disabled=(total < params["limit"])):
                            st.session_state.receipts_history.append(st.session_state.last_id)
                            st.session_state.last_id = new_last_id
                            st.rerun()

        else:
            st.error(f"Failed to fetch receipts: {response.text}")
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to API. Is the server running?")
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
