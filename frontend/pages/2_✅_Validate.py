import streamlit as st
import json
import pandas as pd
from components.validation_display import ValidationDisplay

st.set_page_config(page_title="Validate", page_icon="✅", layout="wide")

st.title("✅ Data Validation")

api_client = st.session_state.api_client

try:
    contracts = api_client.get_contracts()
    contract_names = {c["name"]: c["id"] for c in contracts}
    
    if not contracts:
        st.warning("No contracts available. Please create a contract first.")
        if st.button("Create Contract"):
            st.switch_page("pages/1_📝_Contracts.py")
        st.stop()
    
    selected_name = st.selectbox("Select Contract", list(contract_names.keys()))
    contract_id = contract_names[selected_name]

except Exception as e:
    st.error(f"Failed to load contracts: {e}")
    st.stop()

tab1, tab2, tab3 = st.tabs(["🔍 Single Record", "📦 Batch Upload", "📊 Recent Results"])

with tab1:
    st.subheader("Validate Single Record")
    
    st.markdown("Enter your data in JSON format:")
    
    sample_data = {
        "user_id": "usr_12345",
        "email": "test@example.com",
        "age": 25
    }
    
    data_input = st.text_area(
        "JSON Data",
        value=json.dumps(sample_data, indent=2),
        height=200,
        help="Paste your JSON data here"
    )
    
    if st.button("🚀 Validate", type="primary"):
        try:
            data = json.loads(data_input)
            
            with st.spinner("Validating..."):
                result = api_client.validate_single(contract_id, data)
            
            display = ValidationDisplay(result)
            display.render()
        
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON: {e}")
        except Exception as e:
            st.error(f"Validation failed: {e}")

with tab2:
    st.subheader("Batch File Upload")
    
    file_type = st.selectbox("File Type", ["csv", "json", "jsonl"])
    
    uploaded_file = st.file_uploader(
        f"Upload {file_type.upper()} file",
        type=[file_type],
        help=f"Upload a {file_type.upper()} file to validate all records"
    )
    
    if uploaded_file:
        st.info(f"File: {uploaded_file.name} ({uploaded_file.size / 1024:.2f} KB)")
        
        if st.button("🚀 Validate Batch", type="primary"):
            try:
                file_content = uploaded_file.read().decode('utf-8')
                
                with st.spinner("Processing batch..."):
                    result = api_client.validate_batch(contract_id, file_content, file_type)
                
                st.success("Batch validation complete!")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Records", result["total_records"])
                with col2:
                    st.metric("Passed", result["passed"])
                with col3:
                    st.metric("Failed", result["failed"])
                with col4:
                    st.metric("Pass Rate", f"{result['pass_rate']:.2f}%")
                
                if result.get("errors_summary"):
                    st.markdown("### Error Summary")
                    error_df = pd.DataFrame([
                        {"Error Type": k, "Count": v}
                        for k, v in result["errors_summary"].items()
                    ])
                    st.dataframe(error_df, use_container_width=True)
                
                if result.get("sample_errors"):
                    st.markdown("### Sample Errors")
                    for error in result["sample_errors"][:5]:
                        with st.expander(f"Record {error['record_number']} - {error['field']}"):
                            st.markdown(f"**Error:** {error['error']}")
                            st.markdown(f"**Value:** `{error['value']}`")
            
            except Exception as e:
                st.error(f"Batch validation failed: {e}")

with tab3:
    st.subheader("Recent Validation Results")
    
    limit = st.slider("Number of results", 10, 100, 50)
    
    try:
        results = api_client.get_validation_results(contract_id, limit)
        
        if not results:
            st.info("No validation results yet.")
        else:
            df_data = []
            for r in results:
                df_data.append({
                    "Timestamp": r["validated_at"][:19],
                    "Status": r["status"],
                    "Errors": len(r.get("errors", [])),
                    "Execution (ms)": f"{r['execution_time_ms']:.2f}"
                })
            
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True)
            
            pass_count = sum(1 for r in results if r["status"] == "PASS")
            pass_rate = (pass_count / len(results)) * 100
            
            st.metric("Recent Pass Rate", f"{pass_rate:.1f}%")
    
    except Exception as e:
        st.error(f"Failed to load results: {e}")
