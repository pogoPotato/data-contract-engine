import streamlit as st
import pandas as pd
from components.metrics_charts import MetricsCharts

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

st.title("📊 Quality Metrics Dashboard")

api_client = st.session_state.api_client

try:
    contracts = api_client.get_contracts()
    
    if not contracts:
        st.warning("No contracts available.")
        st.stop()
    
    contract_names = {c["name"]: c["id"] for c in contracts}
    selected_name = st.selectbox("Select Contract", list(contract_names.keys()))
    contract_id = contract_names[selected_name]

except Exception as e:
    st.error(f"Failed to load contracts: {e}")
    st.stop()

days = st.slider("Time Range (days)", 7, 90, 30)

try:
    metrics = api_client.get_daily_metrics(contract_id, days)
    
    if not metrics:
        st.info("No metrics data available yet. Start validating data to see metrics!")
        st.stop()
    
    # FIX: Properly handle the metrics data structure
    metrics_data = []
    for metric in metrics:
        row = {
            'date': metric.get('date'),
            'total_validations': metric.get('total_validations', 0),
            'passed': metric.get('passed', 0),
            'failed': metric.get('failed', 0),
            'pass_rate': metric.get('pass_rate', 0.0),
            'quality_score': metric.get('quality_score', 0.0),
            'avg_execution_time_ms': metric.get('avg_execution_time_ms', 0.0)
        }
        
        # Handle top_errors which might be a list of tuples
        if 'top_errors' in metric:
            row['top_errors'] = metric['top_errors']
        
        metrics_data.append(row)
    
    df = pd.DataFrame(metrics_data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_pass_rate = df['pass_rate'].mean()
        st.metric("Avg Pass Rate", f"{avg_pass_rate:.1f}%")
    
    with col2:
        total_validations = df['total_validations'].sum()
        st.metric("Total Validations", f"{int(total_validations):,}")
    
    with col3:
        latest_score = df['quality_score'].iloc[-1] if len(df) > 0 else 0
        st.metric("Quality Score", f"{latest_score:.1f}")
    
    with col4:
        avg_exec_time = df['avg_execution_time_ms'].mean()
        st.metric("Avg Exec Time", f"{avg_exec_time:.2f} ms")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Pass Rate Trend")
        fig = MetricsCharts.pass_rate_line(df)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Validation Volume")
        fig = MetricsCharts.volume_stacked_bar(df)
        st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Quality Score Trend")
    fig = MetricsCharts.quality_score_area(df)
    st.plotly_chart(fig, use_container_width=True)
    
    if 'top_errors' in df.columns:
        st.subheader("Top Error Types")
        
        all_errors = {}
        for errors_list in df['top_errors']:
            if errors_list and isinstance(errors_list, list):
                for error_item in errors_list:
                    if isinstance(error_item, (list, tuple)) and len(error_item) == 2:
                        error_type, count = error_item
                        all_errors[error_type] = all_errors.get(error_type, 0) + count
        
        if all_errors:
            fig = MetricsCharts.error_distribution_bar(all_errors)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No error data available for the selected time range.")

except Exception as e:
    st.error(f"Failed to load metrics: {e}")
    import traceback
    st.code(traceback.format_exc())