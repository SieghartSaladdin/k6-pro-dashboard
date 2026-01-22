import streamlit as st
import os
import datetime

def get_readable_time(filename):
    """
    Format filename 2026-01-21_15-30-00.csv -> '21 Jan 2026, 15:30'
    """
    clean_name = filename.replace(".csv", "")
    try:
        dt = datetime.datetime.strptime(clean_name, "%Y-%m-%d_%H-%M-%S")
        return dt.strftime("%d %b %Y, %H:%M")
    except Exception:
        return clean_name

def render_sidebar():
    with st.sidebar:
        st.header("📂 Riwayat Tes")
        
        results_root = "results"
        if not os.path.exists(results_root): 
            os.makedirs(results_root)
        
        # Get list of folders (Projects/Test Names)
        test_folders = [f for f in os.listdir(results_root) if os.path.isdir(os.path.join(results_root, f))]
        
        if test_folders:
            selected_folder = st.selectbox("Pilih Kategori Tes", test_folders)
            
            # Get list of files in that folder
            folder_path = os.path.join(results_root, selected_folder)
            files = [f for f in os.listdir(folder_path) if f.endswith(".csv")]
            files.sort(reverse=True) # Newest first based on YYYY-MM-DD name
            
            if files:
                selected_file = st.selectbox(
                    "Pilih Waktu Running", 
                    files, 
                    format_func=get_readable_time
                )
                
                full_path = os.path.join(folder_path, selected_file)
                
                col_load, col_del = st.columns([3, 1])
                
                with col_load:
                    if st.button("📂 Load Data", use_container_width=True, type="secondary"):
                        st.session_state.test_results_path = full_path
                        st.session_state.test_success = True
                        st.toast(f"Memuat: {selected_folder}", icon="✅")
                        st.rerun()

                with col_del:
                    if st.button("🗑️", help="Hapus file ini", use_container_width=True, type="primary"):
                        st.session_state.confirm_delete = full_path

                # Konfirmasi Hapus
                if st.session_state.get("confirm_delete") == full_path:
                    st.error(f"Hapus permanen?")
                    c_yes, c_no = st.columns(2)
                    with c_yes:
                        if st.button("Ya", use_container_width=True, type="primary", key="del_yes"):
                            try:
                                os.remove(full_path)
                                # If folder empty, remove it too
                                if not os.listdir(folder_path):
                                    os.rmdir(folder_path)
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
                st.info("Folder kosong.")
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
