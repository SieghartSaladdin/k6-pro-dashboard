import streamlit as st
import pandas as pd
import altair as alt
import os
from datetime import datetime
from .utils import get_metric_summary, explain_metric, get_breaking_point_analysis

def generate_pdf_report(target_url, filename, stats, failure_rate, total_reqs, failed_reqs, diagnosis):
    """Generate PDF report using fpdf2"""
    try:
        from fpdf import FPDF
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Header
        pdf.set_font('Helvetica', 'B', 18)
        pdf.cell(0, 12, 'K6 Load Test Report', ln=True, align='C')
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 6, f'Generated: {datetime.now().strftime("%d %B %Y, %H:%M")}', ln=True, align='C')
        pdf.ln(8)
        
        # Test Info Box
        pdf.set_fill_color(240, 240, 240)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Helvetica', 'B', 11)
        pdf.cell(0, 8, 'Test Information', ln=True, fill=True)
        pdf.set_font('Helvetica', '', 9)
        
        # Truncate URL if too long
        display_url = target_url if len(target_url) < 80 else target_url[:77] + "..."
        pdf.cell(0, 6, f'Target URL: {display_url}', ln=True)
        pdf.cell(0, 6, f'Data Source: {filename}', ln=True)
        pdf.ln(4)
        
        # Executive Summary - Use full width cells
        pdf.set_font('Helvetica', 'B', 11)
        pdf.cell(0, 8, 'Executive Summary', ln=True, fill=True)
        pdf.set_font('Helvetica', '', 9)
        
        # Row 1
        pdf.cell(63, 7, f'Total Requests: {total_reqs:,}', border=1)
        pdf.cell(63, 7, f'Failed Requests: {failed_reqs:,}', border=1)
        pdf.cell(64, 7, f'Error Rate: {failure_rate:.2f}%', border=1, ln=True)
        
        # Row 2
        pdf.cell(63, 7, f'Avg Response: {stats["avg"]:.1f} ms', border=1)
        pdf.cell(63, 7, f'P95 Latency: {stats["p95"]:.1f} ms', border=1)
        pdf.cell(64, 7, f'P99 Latency: {stats["p99"]:.1f} ms', border=1, ln=True)
        pdf.ln(4)
        
        # Performance Verdict
        pdf.set_font('Helvetica', 'B', 11)
        pdf.cell(0, 8, 'Performance Verdict', ln=True, fill=True)
        pdf.set_font('Helvetica', '', 9)
        
        if failure_rate == 0:
            verdict = "EXCELLENT - No errors detected during the test."
        elif failure_rate < 1:
            verdict = "GOOD - Minor errors detected but within acceptable threshold."
        elif failure_rate < 5:
            verdict = "WARNING - Error rate is elevated. Investigation recommended."
        else:
            verdict = "CRITICAL - High error rate detected. Immediate action required."
        
        pdf.cell(0, 6, verdict, ln=True)
        
        if stats['p95'] < 300:
            latency_verdict = "Response time is excellent (P95 < 300ms)."
        elif stats['p95'] < 1000:
            latency_verdict = "Response time is acceptable (P95 < 1s)."
        else:
            latency_verdict = "Response time is slow (P95 > 1s). Optimization needed."
        
        pdf.cell(0, 6, latency_verdict, ln=True)
        pdf.ln(4)
        
        # Forensic Analysis
        if diagnosis:
            pdf.set_font('Helvetica', 'B', 11)
            pdf.cell(0, 8, 'Forensic Analysis (Breaking Point)', ln=True, fill=True)
            pdf.set_font('Helvetica', '', 9)
            
            if diagnosis['status'] == 'perfect':
                pdf.cell(0, 6, 'System remained stable throughout the test.', ln=True)
                pdf.cell(0, 6, f'Peak Load: {diagnosis["peak_vu"]} Users at {diagnosis["peak_rps"]} RPS', ln=True)
                pdf.cell(0, 6, 'No breaking point detected.', ln=True)
            
            elif diagnosis['status'] == 'minor_errors':
                pdf.cell(0, 6, f'Minor sporadic errors detected ({diagnosis["total_errors"]} total).', ln=True)
                pdf.cell(0, 6, f'Peak Load: {diagnosis["peak_vu"]} Users at {diagnosis["peak_rps"]} RPS', ln=True)
            
            elif diagnosis['status'] == 'broken':
                pattern_text = "Gradual degradation" if diagnosis['pattern'] == 'degradasi_bertahap' else "Sudden failure"
                
                pdf.cell(0, 6, f'BREAKING POINT at {int(diagnosis["rel_time"])} seconds into test.', ln=True)
                pdf.cell(0, 6, f'Users at Saturation: {diagnosis["vus_at_saturation"]} VUs', ln=True)
                pdf.cell(0, 6, f'Users at Error: {diagnosis["vus_at_error"]} VUs', ln=True)
                pdf.cell(0, 6, f'Throughput: {diagnosis["rps"]} RPS', ln=True)
                pdf.cell(0, 6, f'Baseline P95: {diagnosis["stable_latency"]:.0f} ms', ln=True)
                pdf.cell(0, 6, f'Degraded P95: {diagnosis["degraded_latency"]:.0f} ms', ln=True)
                pdf.cell(0, 6, f'Failure Pattern: {pattern_text}', ln=True)
        
        pdf.ln(4)
        
        # Recommendations
        pdf.set_font('Helvetica', 'B', 11)
        pdf.cell(0, 8, 'Recommendations', ln=True, fill=True)
        pdf.set_font('Helvetica', '', 9)
        
        if failure_rate > 5:
            pdf.cell(0, 6, '- Investigate server error logs immediately.', ln=True)
        if stats['p95'] > 1000:
            pdf.cell(0, 6, '- Profile database queries for optimization.', ln=True)
            pdf.cell(0, 6, '- Consider implementing caching strategies.', ln=True)
        if diagnosis and diagnosis['status'] == 'broken':
            if diagnosis['pattern'] == 'degradasi_bertahap':
                pdf.cell(0, 6, '- Check for memory leaks or connection pool issues.', ln=True)
            else:
                pdf.cell(0, 6, '- Check rate limiting and max connections config.', ln=True)
        if failure_rate == 0 and stats['p95'] < 500:
            pdf.cell(0, 6, '- System performs well. Continue monitoring.', ln=True)
        
        return bytes(pdf.output())
        
    except Exception as e:
        print(f"PDF generation error: {e}")
        return None

def render_results():
    if st.session_state.test_success and st.session_state.test_results_path and os.path.exists(st.session_state.test_results_path):
        st.divider()
        st.header("📊 Hasil Analisis")
        
        try:
            # Load Data
            df = pd.read_csv(st.session_state.test_results_path)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')

            # --- METADATA HEADER (User Friendly) ---
            filename = os.path.basename(st.session_state.test_results_path)
            
            # Coba ambil URL dr data jika ada, atau fallback ke 'Unknown'
            target_url_display = "Unknown Target"
            if 'url' in df.columns:
                # Ambil URL pertama yang tidak null/kosong
                found_urls = df['url'].dropna().unique()
                if len(found_urls) > 0:
                    target_url_display = found_urls[0]
            
            # Tampilkan Info Bar
            st.info(f"📂 **File:** `{filename}`  |  🔗 **Target:** `{target_url_display}`")

            # Filter metrics
            req_duration = df[df['metric_name'] == 'http_req_duration']
            req_failed = df[df['metric_name'] == 'http_req_failed']
            
            # Basic Stats
            total_reqs = len(req_duration)
            failed_reqs = int(req_failed['metric_value'].sum()) if not req_failed.empty else 0
            failure_rate = (failed_reqs / total_reqs * 100) if total_reqs > 0 else 0
            
            # Duration Stats
            stats = get_metric_summary(df, 'http_req_duration')
            
            # Deep Analysis - Pass overall stats for context
            diagnosis = get_breaking_point_analysis(df, stats)
            
            # --- ACTION BAR ---
            col_d1, col_d2, col_d3 = st.columns([0.70, 0.15, 0.15])
            with col_d1:
                st.write("") # Spacer
            with col_d2:
                 # Generate CSV content for download (re-read file binary)
                with open(st.session_state.test_results_path, "rb") as file:
                    st.download_button(
                        label="📥 CSV",
                        data=file,
                        file_name=os.path.basename(st.session_state.test_results_path),
                        mime="text/csv",
                        use_container_width=True
                    )
            with col_d3:
                # Generate PDF Report
                pdf_data = generate_pdf_report(
                    target_url_display, 
                    filename, 
                    stats, 
                    failure_rate, 
                    total_reqs, 
                    failed_reqs, 
                    diagnosis
                )
                if pdf_data:
                    st.download_button(
                        label="📄 PDF",
                        data=pdf_data,
                        file_name=f"report_{filename.replace('.csv', '')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
            
            # --- TAB LAYOUT ---
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "📋 Ringkasan Eksekutif", 
                "🔍 Diagnostik AI",
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

            # --- TAB 2: AI DIAGNOSTICS (IMPROVED) ---
            with tab2:
                st.subheader("🕵️ Analisis Forensik Performa")
                st.markdown("Menggunakan algoritma korelasi timestamp untuk mencari **titik retak (Breaking Point)** sistem Anda.")
                
                if diagnosis:
                    if diagnosis['status'] == 'perfect':
                        st.markdown(f"""
                        <div class="stable-card">
                            <h4>✅ Sistem Sangat Stabil!</h4>
                            <p>Tidak ditemukan satu pun error selama pengujian berlangsung.</p>
                            <hr>
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                                <div>
                                    <small>👥 Peak User</small><br>
                                    <span style="font-size: 1.5em; font-weight: bold;">{diagnosis['peak_vu']} VUs</span>
                                </div>
                                <div>
                                    <small>⚡ Max Throughput</small><br>
                                    <span style="font-size: 1.5em; font-weight: bold;">{diagnosis['peak_rps']} Req/sec</span>
                                </div>
                                <div>
                                    <small>🐢 Overall P95 Latency</small><br>
                                    <span style="font-size: 1.5em; font-weight: bold;">{diagnosis['overall_p95']:.0f} ms</span>
                                </div>
                                <div>
                                    <small>📊 Overall Avg Latency</small><br>
                                    <span style="font-size: 1.5em; font-weight: bold;">{diagnosis['overall_avg']:.0f} ms</span>
                                </div>
                            </div>
                            <hr>
                            <p><em>🎯 Sistem Anda mampu menangani beban ini tanpa masalah. Cobalah tingkatkan beban (Stress Test) untuk mencari batas maksimalnya.</em></p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    elif diagnosis['status'] == 'minor_errors':
                        st.markdown(f"""
                        <div class="stable-card">
                            <h4>⚠️ Error Minor Terdeteksi</h4>
                            <p>Total <strong>{diagnosis['total_errors']}</strong> error terjadi secara sporadis (< 1 per 5 detik). Umumnya dapat diabaikan.</p>
                            <hr>
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                                <div>
                                    <small>👥 Peak User</small><br>
                                    <span style="font-size: 1.5em; font-weight: bold;">{diagnosis['peak_vu']} VUs</span>
                                </div>
                                <div>
                                    <small>⚡ Max Throughput</small><br>
                                    <span style="font-size: 1.5em; font-weight: bold;">{diagnosis['peak_rps']} Req/sec</span>
                                </div>
                                <div>
                                    <small>🐢 Overall P95 Latency</small><br>
                                    <span style="font-size: 1.5em; font-weight: bold;">{diagnosis['overall_p95']:.0f} ms</span>
                                </div>
                                <div>
                                    <small>📊 Overall Avg Latency</small><br>
                                    <span style="font-size: 1.5em; font-weight: bold;">{diagnosis['overall_avg']:.0f} ms</span>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    elif diagnosis['status'] == 'broken':
                        # Determine Trend Text
                        if diagnosis['pattern'] == 'degradasi_bertahap':
                            trend_text = "Degradasi Bertahap"
                            trend_desc = "Latency naik signifikan sebelum error muncul. Ini menunjukkan server kelebihan beban secara gradual (saturasi)."
                        else:
                            trend_text = "Kegagalan Mendadak"
                            trend_desc = "Error muncul tiba-tiba tanpa peringatan latency tinggi sebelumnya. Kemungkinan rate limiting, connection refused, atau timeout."
                            
                        st.markdown(f"""
                        <div class="analysis-card">
                            <h4>🚨 Breaking Point Terdeteksi!</h4>
                            <p>Sistem mulai mengalami kegagalan signifikan pada <strong>detik ke-{int(diagnosis['rel_time'])}</strong> setelah tes dimulai.</p>
                            <hr>
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                                <div>
                                    <small>👥 User Saat Saturasi</small><br>
                                    <span style="font-size: 1.5em; font-weight: bold;">{diagnosis['vus_at_saturation']} VUs</span>
                                </div>
                                <div>
                                    <small>👥 User Saat Error</small><br>
                                    <span style="font-size: 1.5em; font-weight: bold;">{diagnosis['vus_at_error']} VUs</span>
                                </div>
                                <div>
                                    <small>⚡ Throughput Saat Error</small><br>
                                    <span style="font-size: 1.5em; font-weight: bold;">{diagnosis['rps']} Req/sec</span>
                                </div>
                                <div>
                                    <small>❌ Total Error</small><br>
                                    <span style="font-size: 1.5em; font-weight: bold; color: #ff4b4b;">{diagnosis['total_errors']}</span>
                                </div>
                            </div>
                            <hr>
                            <h5>📊 Analisis Latency</h5>
                            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px;">
                                <div>
                                    <small>Baseline P95 (Awal Tes)</small><br>
                                    <span style="font-weight: bold; color: #09ab3b;">{diagnosis['stable_latency']:.0f} ms</span>
                                </div>
                                <div>
                                    <small>Degraded P95 (Saat Stres)</small><br>
                                    <span style="font-weight: bold; color: #ffa500;">{diagnosis['degraded_latency']:.0f} ms</span>
                                </div>
                                <div>
                                    <small>Overall P95</small><br>
                                    <span style="font-weight: bold; color: #ff4b4b;">{diagnosis['overall_p95']:.0f} ms</span>
                                </div>
                            </div>
                            <hr>
                            <h5>📈 Pola Kejadian: {trend_text}</h5>
                            <p><em>{trend_desc}</em></p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown("### 📝 Kesimpulan Diagnostik")
                        
                        # Use OVERALL P95 for conclusion, not instant latency
                        conclusion = f"""
                        > **"Sistem berjalan stabil di awal dengan latency P95 ~{diagnosis['stable_latency']:.0f}ms. 
                        > Kegagalan mulai terjadi saat mencapai ~{diagnosis['vus_at_saturation']} User dengan throughput ~{diagnosis['rps']} RPS. 
                        > Latency P95 keseluruhan tercatat {diagnosis['overall_p95']:.0f}ms, dengan rata-rata {diagnosis['overall_avg']:.0f}ms."**
                        """
                        st.info(conclusion)
                        
                        st.markdown("#### 💡 Rekomendasi:")
                        
                        # Dynamic recommendations based on data
                        if diagnosis['overall_p95'] > 2000:
                            st.write("- 🐢 **Latency Sangat Tinggi (P95 > 2s):** Optimasi query database, cek N+1 problem, atau tambah caching layer.")
                        
                        if diagnosis['pattern'] == 'degradasi_bertahap':
                            st.write("- 📈 **Degradasi Bertahap:** Kemungkinan memory leak, connection pool exhaustion, atau CPU throttling. Monitor resource server.")
                        else:
                            st.write("- ⚡ **Kegagalan Mendadak:** Cek rate limiting, max connections di web server (Nginx/Apache), atau firewall rules.")
                        
                        if diagnosis['rps'] < 50 and diagnosis['total_errors'] > 100:
                            st.write("- 🔴 **RPS Rendah tapi Error Banyak:** Backend kemungkinan timeout atau 3rd party dependency gagal.")
                        
                        st.write(f"- 🎯 **Kapasitas Aman:** Disarankan operasikan di bawah **{int(diagnosis['vus_at_saturation'] * 0.7)} User** untuk menjaga stabilitas.")
                            
                else:
                    st.warning("Data tidak cukup untuk melakukan analisis forensik mendalam.")

            # --- TAB 3: BREAKDOWN LATENCY (Request Lifecycle) ---
            with tab3:
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

            # --- TAB 4: PERFORMANCE CHARTS ---
            with tab4:
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

            # --- TAB 5: GLOSSARY ---
            with tab5:
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
