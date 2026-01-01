import streamlit as st
from typing import Any

class SessionState:
    @staticmethod
    def init(key: str, default: Any):
        if key not in st.session_state:
            st.session_state[key] = default
    
    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        return st.session_state.get(key, default)
    
    @staticmethod
    def set(key: str, value: Any):
        st.session_state[key] = value
    
    @staticmethod
    def delete(key: str):
        if key in st.session_state:
            del st.session_state[key]
    
    @staticmethod
    def clear():
        st.session_state.clear()
