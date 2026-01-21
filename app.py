import streamlit as st
from components.utils import apply_custom_css
from components.header import render_header
from components.sidebar import render_sidebar
from components.config_form import render_config_form
from components.execution import run_k6_test
from components.results import render_results

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
run_btn, target_url, method, test_name, test_type, vus, duration, payload_data = render_config_form()

# --- EXECUTION LOGIC ---
if run_btn:
    run_k6_test(target_url, method, test_name, test_type, vus, duration, payload_data)

# --- RESULTS ANALYSIS ---
render_results()

# --- FOOTER ---
st.markdown("<br><br><center><small>Built with ❤️ using Streamlit & k6</small></center>", unsafe_allow_html=True)