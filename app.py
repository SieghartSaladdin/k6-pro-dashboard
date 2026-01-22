import streamlit as st
from ui.utils import apply_custom_css
from ui.header import render_header
from ui.sidebar import render_sidebar
from ui.config_form import render_config_form
from ui.execution import run_k6_test
from ui.results import render_results

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="k6 Pro Dashboard of Rfiq",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- APPLY STYLING ---
apply_custom_css()

# --- HEADER ---
render_header()

# --- INIT SESSION STATE ---
if 'test_running' not in st.session_state: st.session_state.test_running = False
if 'test_results_path' not in st.session_state: st.session_state.test_results_path = None
if 'test_success' not in st.session_state: st.session_state.test_success = False

# --- SIDEBAR ---
render_sidebar()

# --- CONFIGURATION (FORM) ---
run_btn, target_url, method, project_name, csv_name, test_type, vus, duration, payload_data, headers, expected_status, threshold_p95 = render_config_form()

# --- EXECUTION LOGIC ---
if run_btn:
    run_k6_test(target_url, method, project_name, csv_name, test_type, vus, duration, payload_data, headers, expected_status, threshold_p95)

# --- RESULTS ANALYSIS ---
render_results()

# --- FOOTER ---
st.markdown("<br><br><center><small>Built with ❤️ using Streamlit & k6</small></center>", unsafe_allow_html=True)