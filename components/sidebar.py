import streamlit as st
import os
import datetime

def get_readable_name(filename):
    """
    Format filename Name_YYYYMMDD_HHMMSS.csv menjadi 'Name (21 Jan 15:30)'
    """
    clean_name = filename.replace(".csv", "")
    try:
        parts = clean_name.split("_")
        if len(parts) >= 3:
            # Asumsi format: Name_Project_YYYYMMDD_HHMMSS
            time_part = parts[-1]
            date_part = parts[-2]
            
            if len(date_part) == 8 and len(time_part) == 6 and date_part.isdigit() and time_part.isdigit():
                real_name = " ".join(parts[:-2]).title()
                dt = datetime.datetime.strptime(f"{date_part}{time_part}", "%Y%m%d%H%M%S")
                readable_time = dt.strftime("%d %b %Y, %H:%M")
                return f"{real_name} — {readable_time}"
    except Exception:
        pass
    return clean_name

def render_sidebar():
    with st.sidebar:
        st.header("📂 Riwayat Tes")
        
        if not os.path.exists("results"): 
            os.makedirs("results")
        
        # Ambil file dan urutkan berdasarkan waktu modifikasi (terbaru diatas)
        result_files = [f for f in os.listdir("results") if f.endswith(".csv")]
        result_files.sort(key=lambda x: os.path.getmtime(os.path.join("results", x)), reverse=True)
        
        if result_files:
            st.caption(f"Total: {len(result_files)} laporan tersimpan")
            
            selected_history = st.selectbox(
                "Pilih Laporan Lama", 
                result_files, 
                format_func=get_readable_name,
                label_visibility="collapsed"
            )
            
            col_load, col_del = st.columns([3, 1])
            
            with col_load:
                if st.button("📂 Load Data", use_container_width=True, type="secondary"):
                    st.session_state.test_results_path = os.path.join("results", selected_history)
                    st.session_state.test_success = True
                    st.toast(f"Memuat: {get_readable_name(selected_history)}", icon="✅")
                    st.rerun()

            with col_del:
                if st.button("🗑️", help="Hapus laporan ini", use_container_width=True, type="primary"):
                    st.session_state.confirm_delete = selected_history

            # Konfirmasi Hapus
            if st.session_state.get("confirm_delete") == selected_history:
                st.error(f"Hapus permanen?")
                c_yes, c_no = st.columns(2)
                with c_yes:
                    if st.button("Ya", use_container_width=True, type="primary", key="del_yes"):
                        try:
                            os.remove(os.path.join("results", selected_history))
                            st.toast("File berhasil dihapus!", icon="🗑️")
                            del st.session_state["confirm_delete"]
                            st.rerun()
                        except Exception as e:
                            st.error(f"Gagal: {e}")
                with c_no:
                    if st.button("Batal", use_container_width=True, key="del_no"):
                        del st.session_state["confirm_delete"]
                        st.rerun()

        else:
            st.info("Belum ada riwayat tes.")
            st.markdown("Run tes baru untuk melihat history disini.")
        
        st.markdown("---")
        st.markdown("### 📖 Panduan")
        with st.expander("Cara Penggunaan", expanded=False):
            st.markdown("""
            1. **Setup**: Masukkan URL & Method.
            2. **Strategi**: Pilih Load/Stress/Spike.
            3. **Run**: Klik tombol roket.
            4. **Analisis**: Hasil muncul realtime.
            """)
