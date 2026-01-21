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
    let HEADERS = { 'Content-Type': 'application/json' };
    if (__ENV.HEADERS) {
        try {
            const customHeaders = JSON.parse(__ENV.HEADERS);
            HEADERS = { ...HEADERS, ...customHeaders };
        } catch (e) {
            console.error('Failed to parse HEADERS env var:', e);
        }
    }

    // Load Payload (Bisa dari file atau string JSON langsung)
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
    let res;
    if (METHOD === 'GET') {
        res = http.get(BASE_URL, { headers: HEADERS });
    } else if (METHOD === 'POST') {
        res = http.post(BASE_URL, PAYLOAD, { headers: HEADERS });
    } else if (METHOD === 'PUT') {
        res = http.put(BASE_URL, PAYLOAD, { headers: HEADERS });
    } else if (METHOD === 'DELETE') {
        res = http.del(BASE_URL, null, { headers: HEADERS });
    } else {
        // Fallback default GET
        res = http.get(BASE_URL, { headers: HEADERS });
    }

    // 3. Validasi / Check
    const expectedStatus = __ENV.EXPECTED_STATUS ? parseInt(__ENV.EXPECTED_STATUS) : 200;
    
    check(res, {
        [`status is ${expectedStatus}`]: (r) => r.status === expectedStatus,
        'response time < 500ms': (r) => r.timings.duration < 500,
        'response time < 1000ms': (r) => r.timings.duration < 1000,
    });

    // 4. Sleep (Pacing)
    // Random pause 0.5s - 1.5s agar request tidak terlalu robotik (opsional, tergantung case)
    sleep(1);
}
