import streamlit as st
import pandas as pd
import altair as alt
import os
from .utils import get_metric_summary, explain_metric

def render_results():
    if st.session_state.test_success and st.session_state.test_results_path and os.path.exists(st.session_state.test_results_path):
        st.divider()
        st.header("📊 Hasil Analisis")
        
        try:
            # Load Data
            df = pd.read_csv(st.session_state.test_results_path)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            
            # Filter metrics
            req_duration = df[df['metric_name'] == 'http_req_duration']
            req_failed = df[df['metric_name'] == 'http_req_failed']
            
            # Basic Stats
            total_reqs = len(req_duration)
            failed_reqs = int(req_failed['metric_value'].sum()) if not req_failed.empty else 0
            failure_rate = (failed_reqs / total_reqs * 100) if total_reqs > 0 else 0
            
            # Duration Stats
            stats = get_metric_summary(df, 'http_req_duration')
            
            # --- TAB LAYOUT ---
            tab1, tab2, tab3, tab4 = st.tabs([
                "📋 Ringkasan Eksekutif", 
                "⏱️ Breakdown Latency", 
                "📈 Grafik Performa", 
                "📚 Penjelasan (Glosarium)"
            ])
            
            # --- TAB 1: EXECUTIVE SUMMARY ---
            with tab1:
                st.subheader("Kesehatan API Anda")
                
                # Big Cards
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Total Request", f"{total_reqs:,}")
                c2.metric("Rata-rata Waktu (Avg)", f"{stats['avg']:.1f} ms")
                c3.metric("P95 (Mayoritas User)", f"{stats['p95']:.1f} ms", help="95% user merasakan kecepatan ini atau lebih cepat")
                c4.metric("Error Rate", f"{failure_rate:.2f}%", 
                          delta="Gawat!" if failure_rate > 1 else "Aman" if failure_rate == 0 else "Perhatian", 
                          delta_color="inverse")

                st.markdown("---")
                
                # Interpretation Logic
                col_interpret, col_chart = st.columns([1, 1])
                with col_interpret:
                    st.markdown("### 🤖 Analisis Otomatis")
                    if failure_rate > 0:
                        st.error(f"⚠️ **Ditemukan Error:** {failed_reqs} request gagal ({failure_rate:.2f}%). Cek server logs Anda.")
                    else:
                        st.success("✅ **Sempurna:** Tidak ada request yang gagal (HTTP 200 OK).")
                    
                    if stats['p95'] > 1000:
                        st.warning("⚠️ **Performa Lambat:** P95 di atas 1 detik. User mungkin merasa aplikasi berat.")
                    elif stats['p95'] < 300:
                        st.success("🚀 **Performa Cepat:** P95 di bawah 300ms. Sangat responsif!")
                    
                    explain_metric("Apa itu P95?", 
                                   "P95 (Persentil 95) berarti **5% user terburuk** merasakan latensi di atas angka ini. "
                                   "Ini metrik yang lebih jujur daripada Rata-rata (Avg) karena mengabaikan data outlier yang ekstrem.")

                with col_chart:
                    # Simple Histogram using Altair
                    if not req_duration.empty:
                        st.markdown("##### Sebaran Waktu Respon")
                        base = alt.Chart(req_duration).mark_bar().encode(
                            x=alt.X("metric_value", bin=alt.Bin(maxbins=30), title="Durasi (ms)"),
                            y='count()',
                            color=alt.value("#0E61FE")
                        ).properties(height=200)
                        st.altair_chart(base, use_container_width=True)

            # --- TAB 2: BREAKDOWN LATENCY (Request Lifecycle) ---
            with tab2:
                st.subheader("Di mana waktu terbuang?")
                st.markdown("Setiap request HTTP terdiri dari beberapa tahap. Ini membantu Anda tahu **siapa yang salah**: Jaringan atau Server?")
                
                # Get specific k6 metrics
                waiting = get_metric_summary(df, 'http_req_waiting') # TTFB (Server Processing)
                connecting = get_metric_summary(df, 'http_req_connecting') # Network/TCP
                blocked = get_metric_summary(df, 'http_req_blocked') # DNS/Queue
                
                if waiting and connecting:
                    # Create a comparison dataframe
                    lifecycle_data = pd.DataFrame({
                        'Tahapan': ['Blocked (DNS/Queue)', 'Connecting (Network)', 'Waiting (Server Processing)', 'Receiving (Download)'],
                        'Waktu (Rata-rata ms)': [
                            blocked['avg'], 
                            connecting['avg'], 
                            waiting['avg'], 
                            stats['avg'] - (blocked['avg'] + connecting['avg'] + waiting['avg']) # Approximate receiving
                        ]
                    })
                    
                    lc_col1, lc_col2 = st.columns([2, 1])
                    with lc_col1:
                        st.altair_chart(alt.Chart(lifecycle_data).mark_bar().encode(
                            x='Waktu (Rata-rata ms)',
                            y=alt.Y('Tahapan', sort=None),
                            color=alt.Color('Tahapan', legend=None)
                        ).properties(height=300), use_container_width=True)
                    
                    with lc_col2:
                        st.info("""
                        **Cara Membaca:**
                        1. **Waiting Tinggi?** -> Kode Backend Anda lambat atau Database lemot.
                        2. **Connecting Tinggi?** -> Masalah jaringan server atau latency internet.
                        3. **Blocked Tinggi?** -> Antrian request penuh atau masalah DNS.
                        """)
                else:
                    st.warning("Data detail breakdown tidak tersedia di file CSV ini.")

            # --- TAB 3: PERFORMANCE CHARTS ---
            with tab3:
                st.subheader("Timeline Performa")
                
                # Determine metric columns based on k6 version
                chart_df = df[df['metric_name'].isin(['http_req_duration', 'vus'])].pivot_table(
                    index='timestamp', columns='metric_name', values='metric_value', aggfunc='mean'
                ).reset_index()
                
                st.markdown("##### Virtual Users (Beban) vs Durasi (Kecepatan)")
                if not chart_df.empty and 'vus' in chart_df.columns:
                     # Create a dual-axis chart using Altair
                    base = alt.Chart(chart_df).encode(x='timestamp:T')
                    
                    line_duration = base.mark_line(color='#ff4b4b').encode(
                        y=alt.Y('http_req_duration', title='Durasi (ms)'),
                        tooltip=['timestamp', 'http_req_duration']
                    )
                    
                    area_vus = base.mark_area(opacity=0.3, color='#0E61FE').encode(
                        y=alt.Y('vus', title='Virtual Users'),
                        tooltip=['timestamp', 'vus']
                    )
                    
                    st.altair_chart(alt.layer(area_vus, line_duration).resolve_scale(y='independent'), use_container_width=True)
                    
                else:
                    st.caption("Data time-series tidak lengkap.")
                
                st.markdown("---")
                st.markdown("##### Throughput (Requests Per Second)")
                # Resample to 1s
                rps_df = req_duration.set_index('timestamp').resample('1s').count()[['metric_value']].reset_index()
                rps_df.columns = ['timestamp', 'RPS']
                
                st.altair_chart(alt.Chart(rps_df).mark_bar().encode(
                    x='timestamp:T',
                    y='RPS',
                    color=alt.value("green")
                ), use_container_width=True)

            # --- TAB 4: GLOSSARY ---
            with tab4:
                st.markdown("### 📚 Glosarium Metrik k6")
                st.markdown("""
                Agar tidak bingung membaca data, berikut penjelasannya:
                
                | Metrik | Penjelasan Sederhana |
                | :--- | :--- |
                | **http_req_duration** | Total waktu dari klik sampai data selesai diterima. |
                | **http_req_waiting** | Sering disebut **TTFB**. Waktu tunggu server "mikir" sebelum kirim data pertama. Kalau ini tinggi, optimasi database/kode backend Anda. |
                | **http_req_connecting** | Waktu untuk membuat koneksi TCP ke server. Kalau tinggi, cek jaringan. |
                | **vus** | Virtual Users. Berapa banyak "orang" tiruan yang sedang mengakses sistem bersamaan. |
                | **p95 (95th Percentile)** | Batas nilai untuk 95% user tercepat. Jika P95 = 500ms, artinya 95% user aksesnya < 500ms, sisanya (5%) > 500ms. |
                | **Thresholds** | Batas aman. Misalnya "Error harus < 1%". |
                """)

        except Exception as e:
            st.error(f"Gagal memproses data CSV: {str(e)}")
            st.caption("Pastikan file CSV hasil generate k6 versi terbaru.")
