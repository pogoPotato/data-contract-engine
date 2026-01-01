import streamlit as st
from components.api_client import APIClient
import os

st.set_page_config(
    page_title="Data Contract Engine",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "api_client" not in st.session_state:
    api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
    st.session_state.api_client = APIClient(api_base_url)

st.title("📋 Data Contract Engine")
st.markdown("### Automated Data Quality Enforcement")

col1, col2, col3 = st.columns(3)

try:
    summary = st.session_state.api_client.get_platform_summary()
    
    with col1:
        st.metric("Total Contracts", summary.get("total_contracts", 0))
    
    with col2:
        st.metric("Validations Today", summary.get("total_validations_today", 0))
    
    with col3:
        pass_rate = summary.get("avg_pass_rate", 0)
        st.metric("Avg Pass Rate", f"{pass_rate:.1f}%")

except Exception as e:
    st.error(f"Failed to load platform summary: {e}")

st.markdown("---")
st.markdown("### Quick Actions")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("➕ Create Contract", use_container_width=True):
        st.switch_page("pages/1_📝_Contracts.py")

with col2:
    if st.button("✅ Validate Data", use_container_width=True):
        st.switch_page("pages/2_✅_Validate.py")

with col3:
    if st.button("📊 View Dashboard", use_container_width=True):
        st.switch_page("pages/3_📊_Dashboard.py")

st.markdown("---")
st.markdown("""
**Getting Started:**
1. Create a data contract defining your schema and quality rules
2. Validate data against your contract (single records or batch files)
3. Monitor quality metrics over time in the dashboard

**Documentation:** [GitHub Repository](https://github.com/yourusername/data-contract-engine)
""")
