import streamlit as st
import subprocess
import os
from datetime import datetime

def run_k6_test(target_url, method, test_name, test_type, vus, duration, payload_data):
    if not target_url:
        st.error("URL Wajib diisi!")
    else:
        st.session_state.test_running = True
        if not os.path.exists("results"): os.makedirs("results")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c for c in (test_name if test_name else "test") if c.isalnum() or c in (' ', '_', '-')).strip().replace(" ", "_")
        output_csv = os.path.join("results", f"{safe_name}_{timestamp}.csv")
        
        # Environment variables for k6 script
        env = os.environ.copy()
        env["TARGET_URL"] = target_url
        env["METHOD"] = method
        env["TEST_TYPE"] = test_type
        env["MY_VUS"] = str(vus) # Ensure your script.js uses __ENV.MY_VUS
        env["MY_DURATION"] = duration # Ensure your script.js uses __ENV.MY_DURATION
        if payload_data: env["PAYLOAD_DATA"] = payload_data.replace('\n', '')

        # Live Terminal
        st.markdown("### 🖥️ Terminal Output")
        terminal = st.empty()
        full_logs = ""
        
        # Command
        cmd = ["k6", "run", "--out", f"csv={output_csv}", "script.js"] # Ensure script.js exists
        
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, env=env, encoding='utf-8')
            
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None: break
                if line:
                    full_logs += line
                    terminal.code(full_logs[-2000:], language="bash") # Show last 2000 chars
            
            if process.poll() == 0:
                st.session_state.test_success = True
                st.session_state.test_results_path = output_csv
                st.success("Tes Selesai!")
                st.rerun() # Refresh to show results
            else:
                st.error("Terjadi error pada k6.")
        except Exception as e:
            st.error(f"Error executing k6: {e}")
        
        st.session_state.test_running = False
