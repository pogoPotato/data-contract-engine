import streamlit as st
from components.contract_editor import ContractEditor
import yaml

st.set_page_config(page_title="Contracts", page_icon="📝", layout="wide")

st.title("📝 Contract Management")

api_client = st.session_state.api_client

tab1, tab2 = st.tabs(["📋 List Contracts", "➕ Create Contract"])

with tab1:
    st.subheader("Your Contracts")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        search = st.text_input("🔍 Search contracts", key="search")
    with col2:
        domain_filter = st.selectbox("Filter by domain", ["All", "analytics", "finance", "marketing", "sales"])
    
    try:
        contracts = api_client.get_contracts(domain=None if domain_filter == "All" else domain_filter)
        
        if search:
            contracts = [c for c in contracts if search.lower() in c["name"].lower()]
        
        if not contracts:
            st.info("No contracts found. Create your first contract in the 'Create Contract' tab!")
        else:
            for contract in contracts:
                with st.expander(f"**{contract['name']}** (v{contract['version']})", expanded=False):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.markdown(f"**Domain:** {contract['domain']}")
                        st.markdown(f"**Version:** {contract['version']}")
                    
                    with col2:
                        st.markdown(f"**Created:** {contract['created_at'][:10]}")
                        st.markdown(f"**Status:** {'✅ Active' if contract.get('is_active', True) else '❌ Inactive'}")
                    
                    with col3:
                        if st.button("Edit", key=f"edit_{contract['id']}"):
                            st.session_state.editing_contract = contract
                            st.rerun()
                        
                        if st.button("Delete", key=f"delete_{contract['id']}", type="secondary"):
                            try:
                                api_client.delete_contract(contract['id'])
                                st.success(f"Deleted contract: {contract['name']}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to delete: {e}")
                    
                    st.markdown("**YAML Content:**")
                    st.code(contract['yaml_content'], language="yaml")
    
    except Exception as e:
        st.error(f"Failed to load contracts: {e}")

    if "editing_contract" in st.session_state:
        st.markdown("---")
        st.subheader(f"Edit Contract: {st.session_state.editing_contract['name']}")
        
        editor = ContractEditor(st.session_state.editing_contract['yaml_content'])
        new_yaml = editor.render()
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("💾 Save Changes"):
                try:
                    result = api_client.update_contract(
                        st.session_state.editing_contract['id'],
                        new_yaml
                    )
                    st.success(f"Updated to version {result['version']}")
                    del st.session_state.editing_contract
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to update: {e}")
        
        with col2:
            if st.button("Cancel"):
                del st.session_state.editing_contract
                st.rerun()

with tab2:
    st.subheader("Create New Contract")
    
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("Contract Name *", placeholder="user-events")
        domain = st.selectbox("Domain *", ["analytics", "finance", "marketing", "sales", "engineering"])
    
    with col2:
        description = st.text_area("Description", placeholder="Describe this contract...")
    
    st.markdown("**Contract Definition (YAML) *:**")
    
    default_yaml = """contract_version: "1.0"
description: "Your contract description"

schema:
  user_id:
    type: string
    required: true
    pattern: "^usr_\\\\d+$"
    description: "Unique user identifier"
  
  email:
    type: string
    format: email
    required: true
    description: "User email address"
  
  age:
    type: integer
    min: 18
    max: 120
    required: false
    description: "User age"

quality_rules:
  freshness:
    max_latency_hours: 2
  
  completeness:
    min_row_count: 100
    max_null_percentage: 5.0
  
  uniqueness:
    fields: ["user_id"]
"""
    
    editor = ContractEditor(default_yaml)
    yaml_content = editor.render()
    
    if st.button("✨ Create Contract", type="primary"):
        if not name:
            st.error("Please provide a contract name")
        elif not yaml_content:
            st.error("Please provide YAML content")
        else:
            try:
                yaml.safe_load(yaml_content)
                result = api_client.create_contract(name, domain, yaml_content, description)
                st.success(f"Created contract: {result['name']} (v{result['version']})")
                st.balloons()
            except yaml.YAMLError as e:
                st.error(f"Invalid YAML: {e}")
            except Exception as e:
                st.error(f"Failed to create contract: {e}")
