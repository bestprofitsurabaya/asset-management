# MANUAL INSTRUCTION
## BPF ASSET MANAGEMENT SYSTEM v3.0

### Untuk Administrator

---

## DAFTAR ISI

1. [Pendahuluan](#1-pendahuluan)
2. [Instalasi Sistem](#2-instalasi-sistem)
3. [Login dan Keamanan](#3-login-dan-keamanan)
4. [Navigasi Utama](#4-navigasi-utama)
5. [Modul Executive Dashboard](#5-modul-executive-dashboard)
6. [Modul AI Dashboard AC](#6-modul-ai-dashboard-ac)
7. [Modul Interactive Analytics](#7-modul-interactive-analytics)
8. [Modul Manage Master Aset AC](#8-modul-manage-master-aset-ac)
9. [Modul Input Log SOW AC](#9-modul-input-log-sow-ac)
10. [Modul Manage Kendaraan](#10-modul-manage-kendaraan)
11. [Modul Input Servis Kendaraan](#11-modul-input-servis-kendaraan)
12. [Modul Dashboard Kendaraan](#12-modul-dashboard-kendaraan)
13. [Modul Maintenance Recommendations](#13-modul-maintenance-recommendations)
14. [Modul Analytics & Reports](#14-modul-analytics--reports)
15. [Modul Edit/Hapus Data](#15-modul-edithapus-data)
16. [Modul Cetak Laporan](#16-modul-cetak-laporan)
17. [Machine Learning & AI Features](#17-machine-learning--ai-features)
18. [Database Management](#18-database-management)
19. [Troubleshooting](#19-troubleshooting)
20. [FAQ](#20-faq)

---

## 1. PENDAHULUAN

### 1.1 Tentang Sistem

BPF Asset Management System adalah aplikasi manajemen aset terintegrasi untuk PT BESTPROFIT FUTURES SURABAYA. Sistem ini dirancang untuk:

- Memantau kondisi unit AC secara real-time
- Memprediksi kerusakan menggunakan Machine Learning
- Mengelola maintenance kendaraan kantor
- Memberikan rekomendasi perawatan otomatis
- Menghasilkan laporan eksekutif

### 1.2 Persyaratan Sistem

| Komponen | Minimum | Rekomendasi |
|----------|---------|-------------|
| Python | 3.9+ | 3.11+ |
| RAM | 4 GB | 8 GB |
| Storage | 1 GB | 5 GB |
| OS | Windows/Linux/Mac | Linux Server |

### 1.3 Arsitektur Sistem

```
BPF Asset Management System
├── Streamlit Frontend (Port 8501)
├── SQLite Database (data/*.db)
├── Machine Learning Models (models/*.pkl)
├── PDF Report Generator (FPDF)
└── Plotly Visualization Engine
```

---

## 2. INSTALASI SISTEM

### 2.1 Instalasi Standalone

**Langkah 1: Clone atau Download Source Code**

```bash
# Buat direktori project
mkdir bpf-asset-system
cd bpf-asset-system

# Copy semua file ke direktori ini:
# - app.py
# - database_engine.py
# - requirements.txt
# - docker-compose.yml (opsional)
# - Dockerfile (opsional)
```

**Langkah 2: Install Python Dependencies**

```bash
# Buat virtual environment (rekomendasi)
python -m venv venv

# Aktifkan virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Langkah 3: Inisialisasi Database**

```bash
# Jalankan sekali untuk membuat database
python database_engine.py
```

Output yang diharapkan:
```
Initializing BPF Asset Management Database...
Real database initialized!
Initializing Demo Database...
Demo database initialized!
```

**Langkah 4: Jalankan Aplikasi**

```bash
streamlit run app.py
```

Akses aplikasi di browser: `http://localhost:8501`

### 2.2 Instalasi dengan Docker

```bash
# Build dan jalankan dengan Docker Compose
docker-compose up -d

# Lihat logs
docker-compose logs -f

# Stop container
docker-compose down
```

### 2.3 Verifikasi Instalasi

1. Buka browser ke `http://localhost:8501`
2. Login dengan kredensial default admin
3. Pastikan dashboard muncul tanpa error

---

## 3. LOGIN DAN KEAMANAN

### 3.1 Kredensial Default

| Username | Password | Role | Hak Akses |
|----------|----------|------|-----------|
| `admin` | `admin123` | Administrator | Semua fitur, termasuk hapus data |
| `teknisi` | `teknisi123` | Teknisi | Input maintenance AC & Kendaraan |
| `manager` | `manager123` | Manager | View & manage master data |
| `demo` | `demo123` | Viewer | View only (read-only) |

### 3.2 Mengubah Password

**Metode 1: Environment Variable (Docker)**

Edit `docker-compose.yml`:
```yaml
environment:
  - BPF_USERS={"admin":{"password":"HASH_BARU","role":"admin"}}
```

**Metode 2: Edit Source Code**

Edit fungsi `load_users()` di `app.py`:
```python
return {
    "admin": {
        "password": hashlib.sha256("PASSWORD_BARU".encode('utf-8')).hexdigest(),
        "role": "admin"
    },
    # ...
}
```

**Cara Generate Hash Password:**

```python
import hashlib
password = "password_baru"
hash_value = hashlib.sha256(password.encode('utf-8')).hexdigest()
print(hash_value)
```

### 3.3 Mode Database

Sistem memiliki dua mode database:

| Mode | Database File | Penggunaan |
|------|---------------|------------|
| **REAL** | `data/bpf_ac_ai_system.db` | Produksi, data asli |
| **DEMO** | `data/bpf_ac_ai_system_demo.db` | Testing, data dummy |

**Cara Ganti Mode (Admin Only):**

1. Login sebagai `admin`
2. Di sidebar, pilih "System Settings"
3. Pilih "Database Mode": `real` atau `demo`
4. Sistem akan reload otomatis

### 3.4 Session Management

- Session timeout: Tidak ada (Streamlit default)
- Logout manual: Klik tombol "Logout" di sidebar
- Clear session: Logout akan menghapus semua session state

---

## 4. NAVIGASI UTAMA

### 4.1 Sidebar Menu

Sidebar berisi menu navigasi utama:

| Menu | Deskripsi | Akses |
|------|-----------|-------|
| **Executive Dashboard** | Ringkasan eksekutif | Semua |
| **AI Dashboard** | Prediksi kerusakan AC | Semua |
| **Interactive Analytics** | Visualisasi interaktif | Semua |
| **Manage Master Aset AC** | CRUD aset AC | Admin, Manager |
| **Input Log SOW AC** | Input maintenance AC | Admin, Teknisi |
| **Manage Kendaraan** | CRUD kendaraan | Admin, Manager |
| **Input Servis Kendaraan** | Input servis kendaraan | Admin, Teknisi |
| **Dashboard Kendaraan** | Status kendaraan | Semua |
| **Maintenance Recommendations** | Rekomendasi perawatan | Semua |
| **Analytics & Reports** | Laporan analitik | Semua |
| **Edit/Hapus Data** | Koreksi data | Admin |
| **Cetak Laporan** | Generate PDF | Semua |

### 4.2 User Info Panel

Di sidebar bagian atas menampilkan:
- Username yang sedang login
- Role/Level akses

### 4.3 Notifikasi Panel

Di sidebar, di bawah user info:
- Alert **Critical** (merah berkedip)
- Alert **Warning** (kuning)
- Alert **Info** (biru)

### 4.4 Database Mode Indicator

Di pojok kanan atas layar:
- **DEMO** (oranye) - Mode demo dengan data dummy
- **REAL** (hijau) - Mode produksi dengan data asli

---

## 5. MODUL EXECUTIVE DASHBOARD

### 5.1 Tujuan

Executive Dashboard memberikan ringkasan tingkat tinggi untuk pengambilan keputusan cepat.

### 5.2 Komponen Utama

**Executive Summary Card:**
- Total Unit AC
- Total Kendaraan
- Rata-rata Health Score
- Total Biaya Maintenance

**Key Metrics:**
- Total Maintenance AC (semua waktu)
- Total Servis Kendaraan
- Rekomendasi Pending (jumlah rekomendasi belum selesai)
- Notifikasi Belum Dibaca

**Critical Units Panel:**
- Daftar unit AC dengan health score < 60%
- Menampilkan lokasi dan health score

**Vehicle Status Panel:**
- Status kesehatan kendaraan
- Health score per kendaraan

**Top Recommendations:**
- 5 rekomendasi maintenance prioritas tertinggi
- Expandable untuk detail tindakan

### 5.3 Fitur

| Fitur | Fungsi |
|-------|--------|
| **Refresh Data** | Data di-refresh setiap reload halaman |
| **Download PDF** | Generate Executive Summary dalam format PDF |
| **Tandai Selesai** | Menandai rekomendasi sebagai completed |

### 5.4 Cara Menggunakan

1. Buka menu **Executive Dashboard**
2. Review ringkasan di bagian atas
3. Perhatikan unit kritis (warna merah)
4. Klik rekomendasi untuk melihat detail
5. Klik "Download Executive Summary PDF" untuk laporan

---

## 6. MODUL AI DASHBOARD AC

### 6.1 Tujuan

Memonitor kesehatan unit AC dan memprediksi waktu kerusakan menggunakan AI.

### 6.2 Tab AI Prediksi

**Fitur:**
- Health Score Gauge per unit AC
- Prediksi estimasi servis besar
- Deteksi anomali real-time
- Confidence score prediksi

**Filter:**
- Checkbox "Tampilkan Hanya Unit dengan Anomali"

**Cara Membaca:**
- **Confidence Stars**: *** (Tinggi), ** (Sedang), * (Rendah)
- **Warna Border**:
  - Merah: Critical/Anomali High
  - Oranye: Warning
  - Hijau: Normal

### 6.3 Tab ML Analysis

**Fitur Machine Learning:**
- Train/Retrain ML Models (Admin only)
- ML Predicted Health Score
- Confidence Interval
- Anomaly Detection (Isolation Forest)
- Remaining Useful Life (RUL) prediction
- Similar Assets Pattern

**Cara Menggunakan:**
1. Pilih asset dari dropdown
2. Klik "Train/Retrain ML Models" jika model belum ada
3. Lihat hasil prediksi ML
4. Review similar assets untuk referensi

### 6.4 Tab Statistik Lanjutan

**Visualisasi:**
- Distribusi Health Score (Bar Chart)
- Efisiensi Delta T per Unit (Bar Chart)
- Korelasi Antar Parameter (Heatmap)

### 6.5 Alert & Notifikasi

Sistem otomatis mendeteksi:
- Health Score < 50% (Critical)
- Penurunan health score cepat (>10% dalam periode)
- Anomali parameter operasional
- Arus kompresor > 30A (Critical)
- Delta T < 6 (High)

---

## 7. MODUL INTERACTIVE ANALYTICS

### 7.1 Tujuan

Visualisasi data interaktif untuk analisis mendalam.

### 7.2 Tab Health Gauge

**Fungsi:**
- Menampilkan health score dalam format gauge chart
- Informasi detail asset (lokasi, merk, tipe, dll)
- Statistik maintenance (total log, rata-rata health, rata-rata delta T)

### 7.3 Tab Degradation Timeline

**Fungsi:**
- Timeline degradasi dengan 3 subplot:
  - Health Score Trend (dengan trendline)
  - Delta T Trend
  - Ampere Trend
- Threshold lines untuk batas kritis
- Hover untuk detail nilai

**Interpretasi:**
- Garis merah putus-putus: Batas kritis (65%)
- Garis oranye: Batas minimum Delta T (8)
- Garis merah: Batas warning Ampere (25A)

### 7.4 Tab Radar Analysis

**Fungsi:**
- Multi-parameter analysis dalam format radar chart
- 6 parameter: Health Score, Delta T, Efisiensi, Arus Normal, Tekanan Stabil, Drainase
- Target minimum (garis hijau putus-putus)

**Cara Membaca:**
- Area biru: Performa aktual
- Semakin luas area, semakin baik performa
- Area di bawah garis hijau perlu perhatian

### 7.5 Tab 3D Scatter Plot

**Fungsi:**
- Analisis multivariat 3 dimensi
- Sumbu X: Ampere
- Sumbu Y: Delta T
- Sumbu Z: Health Score
- Warna: Health Score (hijau=baik, merah=buruk)
- Ukuran titik: Biaya sparepart

### 7.6 Tab Cost Analysis

**Fungsi:**
- Biaya Servis per Kendaraan (Horizontal Bar)
- Biaya Servis per Komponen (Horizontal Bar)
- Tren Biaya Servis Bulanan (Line Chart)

---

## 8. MODUL MANAGE MASTER ASET AC

### 8.1 Tujuan

Mengelola data master unit AC (CRUD operations).

### 8.2 Akses

- **Admin**: Full access (View, Add, Edit, Delete)
- **Manager**: Full access (View, Add, Edit, Delete)
- **Teknisi**: No access
- **Viewer**: No access

### 8.3 Tab View Assets

Menampilkan tabel semua aset AC dengan kolom:
- Asset ID
- Merk
- Tipe
- Kapasitas
- Lokasi
- Refrigerant
- Status

### 8.4 Tab Add New Asset

**Form Input:**
| Field | Keterangan | Contoh |
|-------|------------|--------|
| Asset ID* | ID unik | AC-16-NEW |
| Merk* | Merk AC | Daikin |
| Tipe* | Tipe AC | Split Duct |
| Kapasitas* | Kapasitas | 60.000 Btu/h |
| Lokasi* | Detail ruangan | R. Meeting |
| Refrigerant* | Jenis freon | R32 |

**Prosedur:**
1. Isi semua field bertanda *
2. Klik "TAMBAH ASET"
3. Sistem akan memvalidasi dan menyimpan

### 8.5 Tab Edit/Delete Asset

**Edit Asset:**
1. Pilih Asset ID dari dropdown
2. Edit field yang ingin diubah
3. Klik "UPDATE SPESIFIKASI"

**Delete Asset (Admin Only):**
1. Pilih Asset ID dari dropdown
2. Klik "HAPUS ASET"
3. Konfirmasi dengan mengetik "HAPUS" (mode real)

**Peringatan:** Menghapus aset akan menghapus SEMUA log maintenance terkait!

---

## 9. MODUL INPUT LOG SOW AC

### 9.1 Tujuan

Mencatat hasil maintenance rutin unit AC.

### 9.2 Akses

- **Admin**: Full access
- **Teknisi**: Full access
- **Manager**: No access
- **Viewer**: No access

### 9.3 Form Input

**Informasi Dasar:**
| Field | Keterangan |
|-------|------------|
| ID Aset AC* | Pilih dari dropdown |
| Nama Teknisi* | Auto-fill dengan username |
| Tanggal Pelaksanaan* | Default hari ini |

**Parameter Pengukuran:**
| Field | Normal Range | Keterangan |
|-------|--------------|------------|
| Voltase (V) | 380V | Tegangan listrik |
| Arus Listrik (A) | 15-20A | Arus kompresor |
| Pressure Low (Psi) | 130-150 | Tekanan rendah |
| Pressure High (Psi) | 330-370 | Tekanan tinggi |
| Suhu Return (C) | 22-26C | Suhu udara masuk |
| Suhu Supply (C) | 12-16C | Suhu udara keluar |
| Suhu Outdoor (C) | 30-35C | Suhu luar ruangan |
| Drainase* | Lancar | Kondisi pembuangan |
| Status Run* | Normal | Status operasi |

**Catatan & Biaya:**
| Field | Keterangan |
|-------|------------|
| Biaya Sparepart (Rp) | Biaya parts |
| Catatan | Tindakan yang dilakukan |

### 9.4 Auto-Calculated Values

**Delta T:**
```
Delta T = Suhu Return - Suhu Supply
```

**Health Score:**
Sistem menghitung otomatis berdasarkan:
- Delta T (bobot 50%)
- Arus listrik (bobot 20%)
- Drainase (bobot 15%)
- Tekanan (bobot 10%)
- Status Run (bobot 5%)

### 9.5 Real-Time Anomaly Detection

Saat mengisi form, sistem akan:
1. Mendeteksi anomali pada nilai input
2. Menampilkan severity (Critical/High/Medium)
3. Memberikan rekomendasi tindakan

### 9.6 Prosedur Input

1. Pilih ID Aset AC
2. Isi semua parameter pengukuran
3. Perhatikan preview Health Score
4. Review anomali yang terdeteksi
5. Isi catatan dan biaya
6. Klik "SIMPAN DATA MAINTENANCE"

---

## 10. MODUL MANAGE KENDARAAN

### 10.1 Tujuan

Mengelola data master kendaraan kantor.

### 10.2 Akses

- **Admin**: Full access
- **Manager**: Full access
- **Teknisi**: No access
- **Viewer**: No access

### 10.3 Tab Daftar Kendaraan

**Summary Metrics:**
- Total Kendaraan
- Kendaraan Aktif
- Kendaraan Service
- Total Odometer

**Vehicle Cards:**
Setiap kendaraan ditampilkan dengan:
- ID Kendaraan, Brand, Model, Tahun
- Plat Nomor, Warna, Jenis BBM
- Odometer saat ini
- Status (Aktif/Service/Nonaktif)
- Health Score dengan warna indikator

### 10.4 Tab Tambah Kendaraan

**Form Input:**
| Field | Keterangan | Contoh |
|-------|------------|--------|
| ID Kendaraan* | ID unik | VH-006 |
| Merek* | Brand | Toyota |
| Model* | Model | Innova |
| Tahun* | Tahun produksi | 2023 |
| Plat Nomor* | Nomor polisi | B 1234 ABC |
| Warna | Warna kendaraan | Hitam |
| Jenis BBM* | Bensin/Solar/Listrik/Hybrid | Bensin |
| Status* | Aktif/Nonaktif/Service | Aktif |
| Tanggal Beli* | Purchase date | 2024-01-15 |
| Odometer Awal* | Km awal | 0 |
| Catatan | Notes | - |

### 10.5 Tab Edit Kendaraan

**Fungsi:**
- Update data kendaraan
- Hapus kendaraan (dengan konfirmasi)

**Peringatan:** Menghapus kendaraan akan menghapus SEMUA log servis terkait!

### 10.6 Tab Master Komponen

**Daftar Komponen Standar:**
| Komponen | Life KM | Life Bulan |
|----------|---------|------------|
| Oli Mesin | 5.000 | 6 |
| Oli Transmisi | 40.000 | 24 |
| Ban | 40.000 | 36 |
| Aki | - | 24 |
| Filter Oli | 5.000 | 6 |
| Filter Udara | 20.000 | 12 |
| Kampas Rem Depan | 30.000 | 18 |
| Timing Belt | 80.000 | 48 |

**Tambah Komponen Baru:**
1. Isi Nama Komponen
2. Isi Standard Life (km) - isi 0 jika tidak berdasarkan jarak
3. Isi Standard Life (bulan) - isi 0 jika tidak berdasarkan waktu
4. Centang "Aktif"
5. Klik "SIMPAN KOMPONEN"

---

## 11. MODUL INPUT SERVIS KENDARAAN

### 11.1 Tujuan

Mencatat servis dan penggantian komponen kendaraan.

### 11.2 Akses

- **Admin**: Full access
- **Teknisi**: Full access
- **Manager**: No access
- **Viewer**: No access

### 11.3 Form Input

**Vehicle Info (Auto-display):**
- Odometer Saat Ini
- Merek/Model
- Plat Nomor

**Detail Servis:**
| Field | Keterangan |
|-------|------------|
| Tanggal Servis* | Default hari ini |
| Odometer* | Km saat servis |
| Komponen* | Pilih dari list |
| Jenis Servis* | Rutin/Perbaikan/Penggantian |
| Montir/Bengkel* | Nama mekanik |
| Biaya* | Total biaya |
| Catatan | Detail tambahan |

### 11.4 Informasi Standar Komponen

Saat memilih komponen, sistem menampilkan:
- Standard life (km dan bulan)
- Rekomendasi servis berikutnya (odometer)
- Estimasi tanggal servis berikutnya

### 11.5 Prosedur Input

1. Pilih kendaraan (hanya yang status Aktif)
2. Verifikasi odometer
3. Pilih komponen yang diganti/diservis
4. Pilih jenis servis
5. Isi biaya dan catatan
6. Klik "SIMPAN SERVIS"

**Catatan:** Odometer kendaraan akan otomatis terupdate jika nilai lebih besar.

---

## 12. MODUL DASHBOARD KENDARAAN

### 12.1 Tujuan

Memantau status kesehatan dan biaya pemeliharaan kendaraan.

### 12.2 Summary Metrics

- Total Kendaraan
- Kendaraan Aktif
- Total Odometer
- Total Biaya Servis

### 12.3 Cost Analysis Charts

**Biaya Servis per Kendaraan:**
- Horizontal bar chart
- Identifikasi kendaraan dengan biaya tertinggi

### 12.4 Status Kesehatan Kendaraan

**Tabel Health Score:**
| Kolom | Keterangan |
|-------|------------|
| Kendaraan | ID - Brand Model |
| Health Score | Progress bar 0-100% |
| Status | Sangat Baik/Baik/Cukup/Kritis |
| Odometer | Km saat ini |
| Usia | Bulan sejak pembelian |
| Jumlah Servis | Total servis tercatat |

### 12.5 Analisis Detail per Kendaraan

**Pilih kendaraan untuk melihat:**
- Health Score gauge
- Informasi kendaraan
- Biaya pemeliharaan (total dan per km)
- Status komponen (tabel)
- Riwayat servis (10 terakhir)
- Tren biaya servis (line chart)

---

## 13. MODUL MAINTENANCE RECOMMENDATIONS

### 13.1 Tujuan

Memberikan rekomendasi perawatan otomatis berdasarkan analisis data.

### 13.2 Cara Kerja

Sistem menganalisis:
1. **Delta T trend** - Efisiensi pendinginan
2. **Ampere trend** - Beban kompresor
3. **Tekanan freon** - Kebocoran atau masalah sistem
4. **Jadwal servis** - Preventive maintenance

### 13.3 Prioritas Rekomendasi

| Prioritas | Warna | Urgensi | Contoh |
|-----------|-------|---------|--------|
| **Critical** | Merah | 1-3 hari | Arus > 30A, Delta T < 6 |
| **High** | Oranye | 7 hari | Delta T < 8, Tekanan abnormal |
| **Medium** | Biru | 14-30 hari | Delta T < 10, Servis rutin |
| **Normal** | Hijau | 90 hari | Preventive maintenance |

### 13.4 Fitur

**Filter by Priority:**
- Multiselect untuk memfilter rekomendasi

**Actions per Rekomendasi:**
- **Tandai Selesai**: Menandai rekomendasi sebagai completed
- **Jadwalkan Ulang**: Menunda rekomendasi 7 hari

### 13.5 Contoh Rekomendasi

```
Asset: AC-01-R. BEST 8
Prioritas: High (dalam 7 hari)
Estimasi Biaya: Rp 500.000

Tindakan:
- Bersihkan filter dan evaporator
- Periksa kompresor dan kelistrikan
- Monitor tekanan freon
```

---

## 14. MODUL ANALYTICS & REPORTS

### 14.1 Tujuan

Analisis data historis dan export laporan.

### 14.2 Tab AC Analytics

**Filter:**
- Tanggal Mulai
- Tanggal Akhir

**Metrics:**
- Total Maintenance
- Rata-rata Health Score
- Rata-rata Delta T
- Total Biaya Sparepart

**Export:**
- Download CSV (filtered data)

### 14.3 Tab Vehicle Analytics

**Filter:**
- Tanggal Mulai
- Tanggal Akhir

**Metrics:**
- Total Biaya Servis (filtered)

**Export:**
- Download CSV (filtered data)

---

## 15. MODUL EDIT/HAPUS DATA

### 15.1 Tujuan

Koreksi data yang salah input (Admin Only).

### 15.2 Akses

- **Admin**: Full access
- **Lainnya**: No access

### 15.3 Tab Hapus Log AC

**Prosedur:**
1. Filter by Asset (opsional)
2. Pilih log dari dropdown
3. Review detail log (JSON)
4. Klik "HAPUS LOG AC PERMANEN"
5. Konfirmasi dengan mengetik "HAPUS"

### 15.4 Tab Hapus Servis Kendaraan

**Prosedur:**
1. Filter by Vehicle (opsional)
2. Pilih servis dari dropdown
3. Review detail servis (JSON)
4. Klik "HAPUS SERVIS KENDARAAN"
5. Konfirmasi dengan mengetik "HAPUS"

### 15.5 Tab Bulk Operations

**Backup Database:**
- Klik "Backup Database"
- File backup tersimpan di `data/backups/`

**Hapus Log Lama:**
1. Input jumlah hari (min 30)
2. Klik "Hapus Log Lama"
3. Konfirmasi dengan mengetik "HAPUS SEMUA LOG LAMA"

---

## 16. MODUL CETAK LAPORAN

### 16.1 Tujuan

Generate laporan dalam format PDF.

### 16.2 Jenis Laporan

| Laporan | Isi | Filter |
|---------|-----|--------|
| **Maintenance AC** | Log maintenance AC | Asset, Periode |
| **Status Kendaraan** | Status kesehatan kendaraan | Kendaraan |
| **Executive Summary** | Ringkasan eksekutif | Bulan berjalan |

### 16.3 Laporan Maintenance AC

**Filter:**
- Pilih Asset (Semua atau spesifik)
- Periode (Semua/30/90/1 Tahun)

**Output PDF:**
- Header PT BESTPROFIT FUTURES
- Ringkasan statistik
- Tabel detail maintenance
- Tanda tangan Manager dan Teknisi

### 16.4 Laporan Status Kendaraan

**Filter:**
- Pilih Kendaraan (Semua atau spesifik)

**Output PDF:**
- Ringkasan kendaraan
- Detail per kendaraan
- Status komponen
- Health score

### 16.5 Executive Summary PDF

**Output PDF:**
- Key metrics
- Critical units
- Vehicle health summary
- Top recommendations

### 16.6 Cara Download

1. Pilih jenis laporan
2. Atur filter yang diinginkan
3. Klik "Generate PDF Report"
4. Klik link "Download PDF" yang muncul

---

## 17. MACHINE LEARNING & AI FEATURES

### 17.1 Overview

Sistem menggunakan Machine Learning untuk:
- Prediksi health score
- Deteksi anomali
- Estimasi Remaining Useful Life (RUL)
- Pattern matching dengan aset serupa

### 17.2 Model yang Digunakan

| Model | Fungsi | Training Trigger |
|-------|--------|------------------|
| **Random Forest Regressor** | Prediksi health score | Manual/Scheduled |
| **Isolation Forest** | Deteksi anomali | Manual/Scheduled |
| **Linear Regression** | RUL estimation | On-demand |

### 17.3 Training Model

**Manual Training:**
1. Buka **AI Dashboard > ML Analysis**
2. Klik "Train/Retrain ML Models"
3. Tunggu proses selesai (1-5 menit)
4. Model tersimpan di `models/*.pkl`

**Kapan Training Diperlukan:**
- Setelah ada > 100 data log baru
- Setiap 1 bulan (rekomendasi)
- Saat akurasi prediksi menurun

### 17.4 Model Persistence

Model disimpan di direktori `models/`:
- `rf_model_real.pkl` - Random Forest (real mode)
- `rf_model_demo.pkl` - Random Forest (demo mode)
- `scaler_real.pkl` - Standard Scaler
- `anomaly_model_real.pkl` - Isolation Forest

### 17.5 Interpretasi Hasil ML

**Predicted Health Score:**
- Nilai 0-100
- Confidence Interval: Range prediksi (95% CI)

**Anomaly Detection:**
- Normal Pattern: Tidak ada anomali
- Anomaly Detected: Pola tidak normal

**Remaining Useful Life:**
- Estimasi hari sampai health score < 65%
- Confidence score prediksi

**Similar Assets:**
- Aset dengan pola degradasi serupa
- Similarity score (60-100%)

---

## 18. DATABASE MANAGEMENT

### 18.1 Struktur Database

```
data/
├── bpf_ac_ai_system.db          # Database real
├── bpf_ac_ai_system_demo.db     # Database demo
└── backups/                      # Folder backup
    └── backup_real_YYYYMMDD_HHMMSS.db
```

### 18.2 Tabel Database

| Tabel | Fungsi |
|-------|--------|
| `assets` | Master data AC |
| `vehicles` | Master data kendaraan |
| `maintenance_logs` | Log maintenance AC |
| `vehicle_service_logs` | Log servis kendaraan |
| `vehicle_components` | Master komponen kendaraan |
| `maintenance_recommendations` | Rekomendasi perawatan |
| `notifications` | Notifikasi sistem |
| `ml_models` | Metadata ML models |
| `audit_logs` | Audit trail |
| `executive_summaries` | Cache executive summary |

### 18.3 Backup Database

**Manual Backup:**
1. Buka **Edit/Hapus Data > Bulk Operations**
2. Klik "Backup Database"
3. File backup tersimpan di `data/backups/`

**Automatic Backup (Docker):**
Service backup di `docker-compose.yml` akan:
- Backup setiap 24 jam
- Menyimpan 30 backup terakhir

### 18.4 Restore Database

```bash
# Stop aplikasi
# Copy file backup ke lokasi database
cp data/backups/backup_real_20240101_120000.db data/bpf_ac_ai_system.db

# Restart aplikasi
```

### 18.5 Database Maintenance

**Vacuum (Optimize):**
```python
import database_engine as db
db.vacuum_database('real')
```

**Check Size:**
```python
size = db.get_database_size('real')
print(f"Database size: {size} MB")
```

---

## 19. TROUBLESHOOTING

### 19.1 Masalah Login

**Gejala:** Tidak bisa login dengan kredensial default

**Solusi:**
1. Pastikan menggunakan username dan password yang tepat
2. Coba gunakan Demo Mode untuk test
3. Reset password dengan generate hash baru
4. Restart aplikasi

### 19.2 Database Error

**Gejala:** Error "Database initialization failed"

**Solusi:**
1. Pastikan direktori `data/` ada dan writable
2. Hapus file database yang corrupt
3. Jalankan `python database_engine.py` manual
4. Cek permission folder

### 19.3 ML Model Error

**Gejala:** Prediksi ML tidak muncul atau error

**Solusi:**
1. Pastikan ada minimal 50 data log
2. Klik "Train/Retrain ML Models"
3. Cek folder `models/` untuk file .pkl
4. Restart aplikasi

### 19.4 PDF Generation Error

**Gejala:** Error saat generate PDF

**Solusi:**
1. Pastikan library fpdf terinstall: `pip install fpdf`
2. Cek data yang akan di-export tidak kosong
3. Kurangi jumlah data (maks 50 baris di PDF)

### 19.5 Plotly Charts Not Showing

**Gejala:** Grafik Plotly tidak muncul

**Solusi:**
1. Pastikan library plotly terinstall: `pip install plotly`
2. Clear browser cache
3. Coba di browser berbeda

### 19.6 Memory Issues

**Gejala:** Aplikasi lambat atau crash

**Solusi:**
1. Hapus log lama (> 1 tahun)
2. Batasi jumlah data di visualisasi
3. Gunakan mode demo untuk testing
4. Increase memory limit di Docker

### 19.7 Port Already in Use

**Gejala:** Error "Port 8501 already in use"

**Solusi:**
```bash
# Cari proses yang menggunakan port 8501
# Windows:
netstat -ano | findstr :8501
# Linux/Mac:
lsof -i :8501

# Kill proses atau ganti port
streamlit run app.py --server.port 8502
```

---

## 20. FAQ

### 20.1 Umum

**Q: Berapa unit AC yang bisa dikelola?**
A: Tidak ada batasan. Sistem sudah diuji dengan 50+ unit.

**Q: Apakah data aman?**
A: Database menggunakan SQLite dengan foreign key constraints. Backup otomatis tersedia.

**Q: Bisa diakses dari HP?**
A: Ya, UI sudah responsive untuk mobile devices.

### 20.2 Teknis

**Q: Bagaimana cara update aplikasi?**
A: 
1. Backup database
2. Pull kode terbaru
3. Install dependencies baru
4. Restart aplikasi

**Q: Bagaimana cara migrate database ke server lain?**
A: Copy file `data/*.db` ke server baru.

**Q: Apakah bisa menggunakan PostgreSQL/MySQL?**
A: Saat ini hanya SQLite. Custom development diperlukan untuk database lain.

### 20.3 Fitur

**Q: Bagaimana cara menambah user baru?**
A: Edit fungsi `load_users()` di `app.py` atau set environment variable.

**Q: Apakah ada notifikasi email/WhatsApp?**
A: Belum. Fitur ini dalam roadmap pengembangan.

**Q: Bisa export ke Excel?**
A: Ya, gunakan fitur Export CSV dan buka di Excel.

### 20.4 Maintenance

**Q: Seberapa sering harus training ulang ML model?**
A: Rekomendasi setiap 1 bulan atau setelah 100+ data baru.

**Q: Bagaimana cara membersihkan data lama?**
A: Gunakan fitur "Hapus Log Lama" di Edit/Hapus Data > Bulk Operations.

**Q: Apakah perlu backup rutin?**
A: Ya, lakukan backup mingguan untuk production.

---

## LAMPIRAN

### A. Daftar Asset ID Default

| Asset ID | Lokasi |
|----------|--------|
| AC-01 | R. BEST 8 |
| AC-02 | R. BEST 7, OPERATIONAL |
| AC-03 | R. BEST 6 |
| AC-04 | R. BEST 5 |
| AC-05 | R. BEST 3, VIP 8 |
| AC-06 | R. BEST 2, VIP 6 & 7 |
| AC-07 | R. BEST 1, VIP 3 & 5 |
| AC-08 | R. KARAOKE |
| AC-09 | LOUNGE 1, 2, VIP 1, 2 |
| AC-10 | R. BM & R. FINANCE |
| AC-11 | R. MEETING & RECEPTIONIST |
| AC-12 | R. TRAINER & R. SECRETARY |
| AC-13 | COMPLIANCE & TRAINING 2 |
| AC-14 | IT & R. SERVER |
| AC-15 | RUANG TRAINING 1 |

### B. Parameter Normal AC

| Parameter | Nilai Normal | Warning | Critical |
|-----------|--------------|---------|----------|
| Delta T | 10-15 C | 8-10 C | < 8 C |
| Arus Kompresor | 15-20 A | 20-25 A | > 25 A |
| Low Pressure | 130-150 Psi | 120-130 Psi | < 120 Psi |
| High Pressure | 330-370 Psi | 370-400 Psi | > 400 Psi |
| Health Score | 70-100% | 50-70% | < 50% |

### C. Kontak Support

Untuk bantuan teknis:
- Email: it2.sby@bestprofit-futures.co.id
- Internal Extension: 1234

---

**Dokumen Versi:** 1.0
**Tanggal:** 2026
**Dibuat oleh:** IT Department - PT BESTPROFIT FUTURES SURABAYA
