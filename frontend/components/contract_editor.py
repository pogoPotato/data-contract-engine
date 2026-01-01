import streamlit as st

class ContractEditor:
    def __init__(self, initial_content: str = ""):
        self.initial_content = initial_content
    
    def render(self) -> str:
        st.markdown("💡 **Tip:** Use YAML format for contract definition.")
        
        content = st.text_area(
            "Contract YAML",
            value=self.initial_content,
            height=400,
            help="Define your contract schema and quality rules in YAML format"
        )
        
        return content
