import streamlit as st

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
                test_name = st.text_input("Nama Tes", placeholder="e.g. Tes_Login")

            payload_data = ""
            if method in ["POST", "PUT"]:
                payload_data = st.text_area("JSON Body Payload", '{"key": "value"}', height=150, help="Masukkan JSON body untuk request POST/PUT.")

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

        st.markdown("---")
        run_btn = st.button("🚀 Jalankan Tes Sekarang", disabled=st.session_state.test_running, type="primary")
        
        return run_btn, target_url, method, test_name, test_type, vus, duration, payload_data
