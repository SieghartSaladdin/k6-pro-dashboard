import http from 'k6/http';
import { check, sleep } from 'k6';
import { getScenarios, getThresholds } from './src/config.js';

// -------------------------------------------------------------------------
// INIT CONTEXT: Setup Options (Scenarios & Thresholds)
// -------------------------------------------------------------------------

export const options = {
    scenarios: {
        // Nama skenario dinamis berdasarkan env var TEST_TYPE (default: 'load')
        default: getScenarios(__ENV.TEST_TYPE || 'load'),
    },
    thresholds: getThresholds(),
};

// -------------------------------------------------------------------------
// VU CODE: Logic Test per User
// -------------------------------------------------------------------------

export default function () {
    // 1. Ambil Konfigurasi dari Environment Variables
    const BASE_URL = __ENV.TARGET_URL;
    if (!BASE_URL) {
        throw new Error('TARGET_URL environment variable is required!');
    }

    const METHOD = (__ENV.METHOD || 'GET').toUpperCase();
    
    // Parse Headers custom (format JSON string, misal: '{"Authorization":"Bearer abc", "X-Custom":"123"}')
    // Default Header: Pura-pura jadi browser Chrome LENGKAP agar tidak kena blokir 403 WAF/Cloudflare
    let HEADERS = { 
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0'
    };

    if (__ENV.HEADERS) {
        try {
            const customHeaders = JSON.parse(__ENV.HEADERS);
            HEADERS = { ...HEADERS, ...customHeaders };
        } catch (e) {
            console.error('Failed to parse HEADERS env var:', e);
        }
    }

    let PAYLOAD = null;
    if (METHOD === 'POST' || METHOD === 'PUT' || METHOD === 'PATCH') {
        if (__ENV.PAYLOAD_FILE) {
             // Jika menggunakan file path (harus ada di folder data/ dan dibaca lewat SharedArray atau open() di init context jika statis, 
             // tapi untuk fleksibilitas load testing dinamis seringkali kita pass string langsung atau read file di luar k6 dan pass sebagai ENV)
             // *Catatan K6*: open() hanya bisa di init context. 
             // Untuk dynamic payload sederhana, kita gunakan env PAYLOAD_DATA string.
             console.warn('PAYLOAD_FILE usage requires strict init context loading. Suggest providing payload json string via PAYLOAD_DATA env.');
        } 
        
        if (__ENV.PAYLOAD_DATA) {
            PAYLOAD = __ENV.PAYLOAD_DATA; // Expecting raw JSON string
        } else {
            // Default payload jika test butuh body tapi tidak disediakan
            PAYLOAD = JSON.stringify({ message: "k6 load test default payload" });
        }
    }

    // 2. Eksekusi Request
    // Tambahkan TIMEOUT agar k6 tidak hang saat menembak endpoint Streaming/SSE
    const requestConfig = { 
        headers: HEADERS,
        timeout: '5s'  // Paksa stop jika server tidak selesai merespon dalam 5 detik
    };

    let res;
    try {
        if (METHOD === 'GET') {
            res = http.get(BASE_URL, requestConfig);
        } else if (METHOD === 'POST') {
            res = http.post(BASE_URL, PAYLOAD, requestConfig);
        } else if (METHOD === 'PUT') {
            res = http.put(BASE_URL, PAYLOAD, requestConfig);
        } else if (METHOD === 'DELETE') {
            res = http.del(BASE_URL, null, requestConfig);
        } else {
            res = http.get(BASE_URL, requestConfig);
        }
    } catch (e) {
        console.error(`Request Exception: ${e}`);
        return; // Skip check jika request crash
    }

    // 3. Validasi / Check
    const expectedStatus = __ENV.EXPECTED_STATUS ? parseInt(__ENV.EXPECTED_STATUS) : 200;
    
    const checkRes = check(res, {
        [`status is ${expectedStatus}`]: (r) => r.status === expectedStatus,
        'response time < 500ms': (r) => r.timings.duration < 500,
        'response time < 1000ms': (r) => r.timings.duration < 1000,
    });

    // --- DEBUGGING ERROR ---
    // Jika status tidak sesuai, print error ke log console agar kelihatan di Terminal/Docker logs
    if (!checkRes && res.status !== expectedStatus) {
        console.error(`❌ FAILURE: ${METHOD} ${BASE_URL} -> Status: ${res.status}`);
        // Tampilkan sedikit snippet body response untuk diagnosa (misal pesan error dari server)
        if (res.body) {
             console.error(`   Body: ${res.body.toString().slice(0, 200)}...`); 
        }
    }

    // 4. Sleep (Pacing)
    // Random pause 1s - 3s (JITTER) agar tidak terdeteksi sebagai bot yang memiliki pola waktu pas 1 detik
    sleep(Math.random() * 2 + 1);
}
