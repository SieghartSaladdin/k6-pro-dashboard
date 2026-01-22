import streamlit as st
import os

def render_config_form():
    with st.expander("🛠️ Konfigurasi Tes Baru", expanded=not st.session_state.test_success):
        col1, col2 = st.columns([1, 1], gap="large")
        
        # --- Column 1: Target & Request Info ---
        with col1:
            st.markdown("### 1. Target & Data")
            target_url = st.text_input("Target URL", "http://test-api.k6.io/public/crocodiles/", help="Endpoint API yang akan dites.")
            
            c1_sub, c2_sub = st.columns([1, 2])
            with c1_sub:
                method = st.selectbox("Method", ["GET", "POST", "PUT", "DELETE"], index=0)
            
            with c2_sub:
                # --- FOLDER / PROJECT SELECTION ---
                if not os.path.exists("results"): os.makedirs("results")
                # Get existing folders
                existing_projects = [f for f in os.listdir("results") if os.path.isdir(os.path.join("results", f))]
                
                # Options: existing + Create New
                project_options = ["➕ Buat Proyek Baru"] + existing_projects
                
                selected_project = st.selectbox("Pilih Proyek (Folder)", project_options)
                
                if selected_project == "➕ Buat Proyek Baru":
                    project_name = st.text_input("Nama Proyek Baru", placeholder="e.g. My_Project_V1")
                else:
                    project_name = selected_project
                
                # --- CSV FILENAME INPUT ---
                # Default filename format suggests standard usage but allows custom overrides
                csv_name = st.text_input("Nama File Output (Optional)", 
                                         placeholder="Biarkan kosong untuk auto-generate (Timestamp)",
                                         help="Jika diisi 'Run1', hasil akan menjadi 'Run1.csv'. Jika kosong akan menggunakan timestamp.")


            payload_data = ""
            if method in ["POST", "PUT"]:
                st.markdown("##### Payload Data")
                
                # Check data directory
                data_files = []
                if os.path.exists("data"):
                    data_files = [f for f in os.listdir("data") if f.endswith(".json")]
                
                tab_manual, tab_file = st.tabs(["📝 Manual Input", "📂 Load File"])
                
                with tab_manual:
                    manual_payload = st.text_area("JSON Body", '{"key": "value"}', height=150, help="Paste raw JSON disini.")
                    
                with tab_file:
                    if data_files:
                        selected_file = st.selectbox("Pilih File (dari folder data/)", data_files)
                        if selected_file:
                             with open(os.path.join("data", selected_file), "r") as f:
                                 file_payload = f.read()
                             st.caption(f"Preview: {file_payload[:50]}...")
                    else:
                        st.warning("Folder 'data/' kosong atau belum ada file .json")
                        file_payload = ""

                # Determine which payload to use
                # Prioritize File if tab is active (Streamlit tabs don't have 'active' state easily accessible in logic without session state tracking, 
                # but we can assume simplicity: if they selected a file, use it, else manual)
                # A better approach: specific toggle
                payload_source = st.radio("Sumber Payload", ["Manual", "File"], horizontal=True, label_visibility="collapsed")
                
                if payload_source == "File" and data_files:
                    payload_data = file_payload
                else:
                    payload_data = manual_payload

        # --- Column 2: Scenario Strategy (Dynamic) ---
        with col2:
            st.markdown("### 2. Strategi Load Test")
            test_type = st.selectbox(
                "Pilih Skenario", 
                ["load", "stress", "spike", "smoke"], 
                index=0,
                format_func=lambda x: x.capitalize()
            )

            # Dynamic Form based on Selection
            if test_type == "load":
                st.info("ℹ️ **Load Test**: Simulasi trafik normal. User naik perlahan (Ramp-up), stabil, lalu turun.")
                vus = st.number_input("Target User Stabil (VUs)", min_value=1, max_value=5000, value=200, 
                                      help="Berapa user aktif bersamaan di kondisi normal?")
                duration = st.text_input("Durasi Waktu Stabil", value="1m", 
                                         help="Berapa lama mereka mengakses sistem? (contoh: 5m, 10m)")

            elif test_type == "stress":
                st.warning("⚠️ **Stress Test**: Mencari titik batas server. User naik agresif melebihi kapasitas.")
                vus = st.number_input("Titik Puncak User (Peak VUs)", min_value=1, max_value=10000, value=500,
                                      help="Maksimal user untuk menyiksa server.")
                duration = st.text_input("Durasi Penyiksaan", value="2m", 
                                         help="Berapa lama server 'disiksa' di puncak beban?")

            elif test_type == "spike":
                st.error("🔥 **Spike Test**: Lonjakan tiba-tiba (Flash Sale). Tenang -> BOOM -> Tenang.")
                vus = st.number_input("Lonjakan Trafik (Peak VUs)", min_value=1, max_value=10000, value=1000,
                                      help="Jumlah user yang tiba-tiba menyerbu dalam waktu singkat.")
                duration = st.text_input("Durasi Lonjakan", value="1m", 
                                         help="Berapa lama lonjakan bertahan sebelum hilang?")

            elif test_type == "smoke":
                st.success("✅ **Smoke Test**: Validasi script (1 User). Cek apakah koneksi berhasil.")
                vus = 1
                st.metric("Virtual Users", "1 User", help="Smoke test selalu menggunakan 1 user.")
                duration = st.text_input("Durasi Cek", value="10s", 
                                         help="Waktu singkat untuk verifikasi (contoh: 10s, 30s).")

        # --- Advanced Options ---
        with st.expander("⚙️ Opsi Lanjutan (Headers & Thresholds)"):
            st.markdown("##### Custom Headers (JSON)")
            headers = st.text_area(
                "Request Headers", 
                value='{"Authorization": "Bearer <token>", "Content-Type": "application/json"}',
                help="Masukkan headers dalam format JSON."
            )
            
            c3, c4 = st.columns(2)
            with c3:
                expected_status = st.number_input("Expected HTTP Status", value=200, help="Status code yang dianggap sukses.")
            with c4:
                threshold_p95 = st.number_input("Max P95 Latency (ms)", value=500, help="Batas toleransi latency P95.")

        st.markdown("---")
        run_btn = st.button("🚀 Jalankan Tes Sekarang", disabled=st.session_state.test_running, type="primary")
        
        return run_btn, target_url, method, project_name, csv_name, test_type, vus, duration, payload_data, headers, expected_status, threshold_p95

