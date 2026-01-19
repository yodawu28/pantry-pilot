import streamlit as st


def render_header():
    """Render the app header with attractive styling"""
    st.markdown(
        """
    <div style="text-align: center; padding: 1rem 0;">
        <h1 style="color: #FF6B6B; margin-bottom: 0;">🥘 Pantry Pilot</h1>
        <p style="color: #6B7280; font-size: 1.1rem; margin-top: 0.5rem;">
            Smart Pantry Management • Automated Receipt Processing
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown("---")
