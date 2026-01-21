# K6 Load Testing Setup (Reusable & Dynamic)

Project ini berisi setup script **k6** yang siap pakai untuk melakukan load testing ke backend apapun. 
Dilengkapi dengan **Dashboard Streamlit (`app.py`)** untuk memudahkan konfigurasi dan visualisasi hasil tanpa mengetik command panjang.

## 📂 Struktur Folder
```
.
├── app.py              # 🖥️ Dashboard UI (Jalankan ini untuk mode GUI)
├── script.js           # 🧠 Main Logic k6
├── src/
│   └── config.js       # ⚙️ Konfigurasi Skenario Dinamis
├── results/            # 📊 Folder output CSV hasil test
└── README.md           # 📖 Dokumentasi
```

## 🚀 Cara Menjalankan (Dashboard GUI)

Cara termudah untuk menjalankan test adalah menggunakan aplikasi dashboard yang telah disediakan.

1. Pastikan Python sudah terinstall.
2. Install dependency:
   ```bash
   pip install streamlit pandas altair
   ```
3. Jalankan aplikasi:
   ```bash
   streamlit run app.py
   ```
4. Buka browser (biasanya http://localhost:8501) dan mulai testing!


## ⚡ Cara Menjalankan (Command Line / Manual)

Jika Anda lebih suka menggunakan terminal atau ingin integrasi CI/CD.

### 1. Load Test (Traffic Normal)
```powershell
k6 run -e TARGET_URL=https://test-api.k6.io/public/crocodiles/ script.js
```

### 2. Custom Stress Test (Manual VUs & Duration)
Anda bisa menentukan jumlah user (VUs) dan durasi sendiri.
```powershell
# Menjalankan 500 User selama 3 menit
k6 run -e TARGET_URL=... -e TEST_TYPE=stress -e MY_VUS=500 -e MY_DURATION=3m script.js
```

### 3. Spike Test (Lonjakan Ekstrim)
Simulasi lonjakan pengunjung tiba-tiba (e.g. Flash Sale).
```powershell
k6 run -e TARGET_URL=... -e TEST_TYPE=spike script.js
```

---

## ⚙️ Parameter Konfigurasi (Environment Variables)

Gunakan flag `-e KEY=VALUE` saat menjalankan k6.

| Variable | Default | Deskripsi |
| :--- | :--- | :--- |
| `TARGET_URL` | **Wajib** | URL e.g. `https://api.example.com/login` |
| `METHOD` | `GET` | HTTP Method: `GET`, `POST`, `PUT`, `DELETE` |
| `TEST_TYPE` | `load` | Jenis test: `load`, `stress`, `smoke`, `spike` |
| `MY_VUS` | *Auto* | Override jumlah max Virtual Users (misal: `100`, `500`) |
| `MY_DURATION`| `1m` | Override durasi fase "tahan" (misal: `30s`, `5m`) |
| `PAYLOAD_DATA` | `null` | JSON String body request. |
| `HEADERS` | `null` | JSON String custom header. |

---

## 📊 Jenis Skenario

1. **Load Test (`TEST_TYPE=load`)**
   - Simulasi hari-hari biasa.  
   - Ramp-up perlahan -> Tahan stabil -> Ramp-down.
   
2. **Stress Test (`TEST_TYPE=stress`)**
   - Mencari titik hancur server.
   - Ramp-up agresif -> Tahan beban berat.

3. **Spike Test (`TEST_TYPE=spike`)**
   - Simulasi lonjakan tiba-tiba (Flash sale / Viral).
   - Tenang -> Lonjakan Ekstrim (5-10 detik) -> Tenang.

4. **Smoke Test (`TEST_TYPE=smoke`)**
   - Cek koneksi cepat (1 User).
   - Validasi error script.

---

## 📈 Tips
- Gunakan `MY_VUS` untuk menyesuaikan beban. Jika test gagal total, turunkan VUs.
- Gunakan `app.py` untuk visualisasi grafik yang lebih mudah dipahami dibanding output terminal biasa.

---

## 🐳 Setup Menggunakan Docker

Gunakan cara ini agar tidak perlu ribet install Python dan k6 manual.

### 1. Build Image
Pastikan Docker Desktop sudah menyala, lalu jalankan:
```bash
docker build -t k6-dashboard .
```

### 2. Jalankan Container
Jalankan aplikasi di port 8501:
```bash
docker run -p 8501:8501 k6-dashboard
```
Akses di browser: `http://localhost:8501`

### 3. Simpan Hasil Test (Mount Volume)
Agar file CSV history tidak hilang saat container direstart:
**Linux/Mac:**
```bash
docker run -p 8501:8501 -v $(pwd)/results:/app/results k6-dashboard
```
**Windows (PowerShell):**
```powershell
docker run -p 8501:8501 -v ${PWD}/results:/app/results k6-dashboard
```

### 4. Upload ke Docker Hub (Opsional)
Jika Anda ingin menyimpan image ini secara online:
```bash
# Login dulu
docker login

# Tag & Push
docker tag k6-dashboard usernameanda/k6-dashboard:latest
docker push usernameanda/k6-dashboard:latest
```

---

## 🐙 Setup Menggunakan Docker Compose (Paling Mudah)

Cukup satu perintah untuk build & run sekaligus mount folder history secara otomatis.

1. Jalankan:
   ```bash
   docker-compose up -d --build
   ```

2. Buka browser: `http://localhost:8501`

3. Untuk mematikan:
   ```bash
   docker-compose down
   ```
