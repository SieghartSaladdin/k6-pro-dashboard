// Konfigurasi Thresholds (Batas toleransi error & latency)
// Dapat di-override melalui Environment Variables
export const getThresholds = () => {
    return {
        http_req_failed: ['rate<0.01'], // Error rate harus di bawah 1%
        http_req_duration: [
            `p(95)<${__ENV.THRESHOLD_P95 || 500}`,  // 95% request harus di bawah 500ms (default)
            `p(99)<${__ENV.THRESHOLD_P99 || 1000}`, // 99% request harus di bawah 1000ms (default)
        ],
    };
};

// Konfigurasi Skenario Load Testing
export const getScenarios = (type) => {
    /* 
       Ambil parameter dinamis dari Env Variables
       - MY_VUS: Target virtual users (default tergantung profil)
       - MY_DURATION: Durasi fase utama/hold (default tergantung profil)
    */
    const TARGET_VUS = __ENV.MY_VUS ? parseInt(__ENV.MY_VUS) : null;
    const HOLD_DURATION = __ENV.MY_DURATION || '1m';

    const scenarios = {
        // 1. Load Test: Simulasi traffic normal
        // Naik pelan-pelan -> Tahan -> Turun
        load: {
            executor: 'ramping-vus',
            startVUs: 0,
            stages: [
                { duration: '30s', target: Math.ceil((TARGET_VUS || 20) * 0.2) }, // Warm-up ke 20%
                { duration: '1m', target: TARGET_VUS || 200 },                    // Naik ke Target 100%
                { duration: HOLD_DURATION, target: TARGET_VUS || 200 },           // Tahan di Peak
                { duration: '30s', target: 0 },                                   // Ramp-down
            ],
            gracefulRampDown: '30s',
        },
        
        // 2. Stress Test: Mencari titik hancur (Breaking Point)
        // Naik cepat -> Tahan tinggi
        stress: {
            executor: 'ramping-vus',
            startVUs: 0, 
            stages: [
                { duration: '30s', target: Math.ceil((TARGET_VUS || 500) * 0.5) }, // Naik cepat ke 50%
                { duration: '1m', target: TARGET_VUS || 500 },                     // Dorong ke Target 100%
                { duration: HOLD_DURATION, target: TARGET_VUS || 500 },            // Siksa terus
                { duration: '1m', target: 0 },                                     // Recovery
            ],
            gracefulRampDown: '1m',
        },

        // 3. Spike Test: Lonjakan tiba-tiba
        // Tenang -> BOOM -> Tenang
        spike: {
            executor: 'ramping-vus',
            startVUs: 0,
            stages: [
                { duration: '10s', target: 0 },
                { duration: '10s', target: TARGET_VUS || 1000 },  // Lonjakan ekstrem
                { duration: HOLD_DURATION, target: TARGET_VUS || 1000 }, 
                { duration: '10s', target: 0 },
            ],
            gracefulRampDown: '1m',
        },

        // 4. Smoke Test: Verifikasi script berfungsi
        smoke: {
            executor: 'constant-vus',
            vus: 1, 
            duration: HOLD_DURATION !== '1m' ? HOLD_DURATION : '10s', // Default 10s kalau tidak diset
        }
    };

    return scenarios[type] || scenarios['load'];
};
