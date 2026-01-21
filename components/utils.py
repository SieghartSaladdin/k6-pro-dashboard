import streamlit as st

def apply_custom_css():
    st.markdown("""
    <style>
        .main .block-container { padding-top: 2rem; padding-bottom: 3rem; }
        .stButton>button { width: 100%; border-radius: 8px; font-weight: 600; }
        [data-testid="stMetricValue"] { font-size: 1.8rem; color: #0E61FE; }
        .metric-card { background-color: #f9f9f9; color: #333; padding: 15px; border-radius: 10px; border: 1px solid #ddd; margin-bottom: 10px; }
        .explanation-box { background-color: #e8f4ff; color: #333; border-left: 5px solid #0E61FE; padding: 15px; border-radius: 5px; font-size: 0.9em; margin-bottom: 20px; }
        h3 { font-size: 1.3rem; font-weight: 700; margin-top: 20px;}
    </style>
    """, unsafe_allow_html=True)

def get_metric_summary(df, metric_name):
    """Extracts summary stats for a specific metric."""
    subset = df[df['metric_name'] == metric_name]['metric_value']
    if subset.empty:
        return None
    return {
        'avg': subset.mean(),
        'min': subset.min(),
        'max': subset.max(),
        'p90': subset.quantile(0.90),
        'p95': subset.quantile(0.95),
        'p99': subset.quantile(0.99),
        'count': subset.count()
    }

def explain_metric(title, text):
    """Renders a nice explanation box."""
    st.markdown(f"""
    <div class="explanation-box">
        <strong>💡 {title}</strong><br>
        {text}
    </div>
    """, unsafe_allow_html=True)
