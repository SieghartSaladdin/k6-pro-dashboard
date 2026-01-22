import streamlit as st
import pandas as pd

def apply_custom_css():
    st.markdown("""
    <style>
        .main .block-container { padding-top: 2rem; padding-bottom: 3rem; }
        .stButton>button { width: 100%; border-radius: 8px; font-weight: 600; }
        [data-testid="stMetricValue"] { font-size: 1.8rem; color: #0E61FE; }
        
        /* Metric Card - Adapted to Theme */
        .metric-card { 
            background-color: var(--secondary-background-color); 
            color: var(--text-color); 
            padding: 15px; 
            border-radius: 10px; 
            border: 1px solid rgba(128, 128, 128, 0.2); 
            margin-bottom: 10px; 
        }
        
        /* Explanation Box - Adapted to Theme */
        .explanation-box { 
            background-color: var(--secondary-background-color); 
            color: var(--text-color); 
            border-left: 5px solid #0E61FE; 
            padding: 15px; 
            border-radius: 5px; 
            font-size: 0.9em; 
            margin-bottom: 20px; 
        }
        
        h3 { font-size: 1.3rem; font-weight: 700; margin-top: 20px; color: var(--text-color);}
        
        /* Analysis Card - Adapted to Theme */
        .analysis-card { 
            background-color: var(--secondary-background-color); 
            color: var(--text-color); 
            padding: 20px; 
            border-radius: 10px; 
            border-left: 6px solid #ff4b4b; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.2); 
        }
        .analysis-card h4 { color: var(--text-color); margin-top: 0; font-weight: bold; }
        .analysis-card span { color: var(--text-color); }
        .analysis-card small { color: var(--text-color); opacity: 0.8; }
        
        /* Stable Card - Adapted to Theme */
        .stable-card { 
            background-color: var(--secondary-background-color); 
            color: var(--text-color); 
            padding: 20px; 
            border-radius: 10px; 
            border-left: 6px solid #09ab3b; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.2); 
        }
        .stable-card h4 { color: var(--text-color); margin-top: 0; font-weight: bold; }
        .stable-card p, .stable-card li { color: var(--text-color); }
    </style>
    """, unsafe_allow_html=True)

def get_breaking_point_analysis(df, overall_stats=None):
    """
    Melakukan analisis deep-dive untuk mencari titik retak (Breaking Point).
    IMPROVED: Menggunakan P95 dan tren keseluruhan, bukan latency instan.
    Return: Dict info atau None jika tidak bisa dianalisis.
    """
    try:
        # 1. Resample Data per Detik
        df_copy = df.copy()
        df_copy['ts'] = pd.to_datetime(df_copy['timestamp'])
        df_sorted = df_copy.sort_values('ts')
        
        # Helper filters
        reqs = df_sorted[df_sorted['metric_name'] == 'http_req_duration']
        fails = df_sorted[df_sorted['metric_name'] == 'http_req_failed']
        vus_data = df_sorted[df_sorted['metric_name'] == 'vus']
        
        if reqs.empty: return None

        # Pivot per 5 detik (lebih smooth, mengurangi noise)
        errors_series = fails.set_index('ts').resample('5s')['metric_value'].sum().fillna(0)
        vus_series = vus_data.set_index('ts').resample('5s')['metric_value'].max().ffill().fillna(0)
        
        # PENTING: Gunakan P95 per bucket, bukan median/mean
        lat_p95_series = reqs.set_index('ts').resample('5s')['metric_value'].quantile(0.95).fillna(0)
        lat_avg_series = reqs.set_index('ts').resample('5s')['metric_value'].mean().fillna(0)
        
        rps_series = reqs.set_index('ts').resample('5s')['metric_value'].count().fillna(0) / 5  # Per detik

        # Gabungkan semua ke satu DataFrame Chronological
        analysis_df = pd.DataFrame({
            'errors': errors_series,
            'vus': vus_series,
            'latency_p95': lat_p95_series,
            'latency_avg': lat_avg_series,
            'rps': rps_series
        }).dropna()
        
        if analysis_df.empty: return None
        
        # --- OVERALL STATS (untuk konteks) ---
        total_errors = int(errors_series.sum())
        peak_vu = int(analysis_df['vus'].max())
        peak_rps = int(analysis_df['rps'].max())
        overall_p95 = overall_stats['p95'] if overall_stats else reqs['metric_value'].quantile(0.95)
        overall_avg = overall_stats['avg'] if overall_stats else reqs['metric_value'].mean()
        
        # 2. Cari Detik Pertama Error Muncul (dengan toleransi > 1 error per 5s)
        fail_points = analysis_df[analysis_df['errors'] > 1]
        
        if fail_points.empty:
            # PERFECT atau ERROR SANGAT MINOR
            if total_errors == 0:
                return {
                    'status': 'perfect',
                    'peak_vu': peak_vu,
                    'peak_rps': peak_rps,
                    'overall_p95': overall_p95,
                    'overall_avg': overall_avg
                }
            else:
                # Ada error tapi sangat sporadis (< 1 per 5s)
                return {
                    'status': 'minor_errors',
                    'total_errors': total_errors,
                    'peak_vu': peak_vu,
                    'peak_rps': peak_rps,
                    'overall_p95': overall_p95,
                    'overall_avg': overall_avg
                }
        
        # BREAKING POINT FOUND
        bp_time = fail_points.index[0]
        bp_vus = int(fail_points['vus'].iloc[0])
        bp_rps = int(fail_points['rps'].iloc[0])
        
        # 3. Analisis Latency SEBELUM Breaking Point (bukan saat error)
        # Cari momen dimana latency mulai naik drastis
        pre_incident_df = analysis_df[analysis_df.index < bp_time]
        
        stable_latency = 0
        degraded_latency = 0
        saturation_point = None
        
        if len(pre_incident_df) > 2:
            # Ambil latency P95 rata-rata di 1/3 awal tes (baseline)
            first_third = pre_incident_df.head(len(pre_incident_df) // 3)
            stable_latency = first_third['latency_p95'].mean() if not first_third.empty else 0
            
            # Cari titik dimana latency > 2x baseline (Saturation Point)
            if stable_latency > 0:
                saturated = pre_incident_df[pre_incident_df['latency_p95'] > (stable_latency * 2)]
                if not saturated.empty:
                    saturation_point = saturated.index[0]
                    degraded_latency = saturated['latency_p95'].iloc[0]
        
        # 4. Tentukan Pola Kejadian
        if saturation_point and saturation_point < bp_time:
            trend = "degradasi_bertahap"  # Latency naik dulu, baru error
            sat_vus = int(analysis_df.loc[saturation_point, 'vus'])
        else:
            trend = "sudden_failure"  # Error tiba-tiba tanpa warning
            sat_vus = bp_vus
            degraded_latency = overall_p95
        
        return {
            'status': 'broken',
            'timestamp': bp_time,
            'rel_time': (bp_time - analysis_df.index[0]).total_seconds(),
            'vus_at_error': bp_vus,
            'vus_at_saturation': sat_vus,
            'rps': bp_rps,
            'stable_latency': stable_latency,
            'degraded_latency': degraded_latency,
            'overall_p95': overall_p95,
            'overall_avg': overall_avg,
            'total_errors': total_errors,
            'peak_vu': peak_vu,
            'peak_rps': peak_rps,
            'pattern': trend
        }
            
    except Exception as e:
        print(f"Error analaysis: {e}")
        return None

def get_metric_summary(df, metric_name):
    """Extracts summary stats for a specific metric."""
    subset = df[df['metric_name'] == metric_name]['metric_value']
    if subset.empty:
        return None
    return {
        'avg': subset.mean(),
        'min': subset.min(),
        'max': subset.max(),
        'p90': subset.quantile(0.90),
        'p95': subset.quantile(0.95),
        'p99': subset.quantile(0.99),
        'count': subset.count()
    }

def explain_metric(title, text):
    """Renders a nice explanation box."""
    st.markdown(f"""
    <div class="explanation-box">
        <strong>💡 {title}</strong><br>
        {text}
    </div>
    """, unsafe_allow_html=True)
