import streamlit as st

class ValidationDisplay:
    def __init__(self, result: dict):
        self.result = result
    
    def render(self):
        status = self.result.get("status", "UNKNOWN")
        
        if status == "PASS":
            st.success("✅ Validation Passed!")
        else:
            st.error("❌ Validation Failed")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Status", status)
        
        with col2:
            exec_time = self.result.get("execution_time_ms", 0)
            st.metric("Execution Time", f"{exec_time:.2f} ms")
        
        errors = self.result.get("errors", [])
        if errors:
            st.markdown("### Errors")
            
            for i, error in enumerate(errors, 1):
                with st.expander(f"Error {i}: {error.get('field', 'N/A')}"):
                    st.markdown(f"**Field:** `{error.get('field', 'N/A')}`")
                    st.markdown(f"**Type:** `{error.get('error_type', 'N/A')}`")
                    st.markdown(f"**Message:** {error.get('message', 'N/A')}")
                    if "value" in error:
                        st.markdown(f"**Value:** `{error['value']}`")
