import streamlit as st
import subprocess
import os
from datetime import datetime

def run_k6_test(target_url, method, project_name, csv_name, test_type, vus, duration, payload_data, headers, expected_status, threshold_p95):
    if not target_url:
        st.error("URL Wajib diisi!")
    else:
        st.session_state.test_running = True
        if not os.path.exists("results"): os.makedirs("results")
        
        # 1. Tentukan Nama Folder Proyek
        safe_folder_name = "".join(c for c in (project_name if project_name else "Default_Project") if c.isalnum() or c in (' ', '_', '-')).strip().replace(" ", "_")
        test_folder = os.path.join("results", safe_folder_name)
        if not os.path.exists(test_folder):
            os.makedirs(test_folder)

        # 2. Tentukan Nama File CSV
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        if csv_name and csv_name.strip():
            # User input custom name
            safe_filename = "".join(c for c in csv_name if c.isalnum() or c in (' ', '_', '-')).strip().replace(" ", "_")
            # Cek apakah user sudah pake .csv atau belum
            if not safe_filename.lower().endswith(".csv"):
                 safe_filename += ".csv"
            # Optional: Append timestamp kecil biar ga overwrite kalau nama sama? 
            # Atau kita biarkan overwrite? User minta "custom", biasanya expect exactly that name.
            # Tapi untuk safety data load testing, lebih baik warning atau append. 
            # Kita 'smart append' jika file sudah ada.
            
            final_filename = safe_filename
            counter = 1
            while os.path.exists(os.path.join(test_folder, final_filename)):
                base = safe_filename.replace(".csv", "")
                final_filename = f"{base}_{counter}.csv"
                counter += 1
            
            output_csv = os.path.join(test_folder, final_filename)
        else:
            # Default auto-generate timestamp
            output_csv = os.path.join(test_folder, f"{timestamp}.csv")
        
        # Environment variables for k6 script
        env = os.environ.copy()
        env["TARGET_URL"] = target_url
        env["METHOD"] = method
        env["TEST_TYPE"] = test_type
        env["MY_VUS"] = str(vus) # Ensure your script.js uses __ENV.MY_VUS
        env["MY_DURATION"] = duration # Ensure your script.js uses __ENV.MY_DURATION
        env["HEADERS"] = headers # Pass headers JSON
        env["EXPECTED_STATUS"] = str(expected_status)
        env["THRESHOLD_P95"] = str(threshold_p95)
        
        if payload_data: env["PAYLOAD_DATA"] = payload_data.replace('\n', '')

        # Live Terminal
        st.markdown("### 🖥️ Terminal Output")
        terminal = st.empty()
        full_logs = ""
        
        # Command
        cmd = ["k6", "run", "--out", f"csv={output_csv}", "k6/main.js"] # Ensure script.js exists
        
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, env=env, encoding='utf-8')
            
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None: break
                if line:
                    full_logs += line
                    terminal.code(full_logs[-2000:], language="bash") # Show last 2000 chars
            
            if process.poll() == 0 or (os.path.exists(output_csv) and os.path.getsize(output_csv) > 0):
                # SUKSES (Code 0) ATAU Ada Hasil CSV (meskipun Code != 0 karena Threshold failure)
                st.session_state.test_success = True
                st.session_state.test_results_path = output_csv
                
                if process.poll() == 0:
                    st.success("Tes Selesai dengan Sempurna!")
                else:
                    st.warning("Tes Selesai! (Warning: Beberapa request gagal atau Threshold terlampaui - Normal untuk Stress Test)")
                
                st.rerun() # Refresh to show results
            else:
                st.error("Gagal menjalankan k6. Tidak ada data output yang dihasilkan.")
        except Exception as e:
            st.error(f"Error executing k6: {e}")
        
        st.session_state.test_running = False
