CivitasFix - Sistem Pelaporan Kerusakan Fasilitas Kampus

Sistem web-based untuk pelaporan dan manajemen kerusakan fasilitas kampus UPN Veteran Jawa Timur.
Fitur Lengkap

Untuk Mahasiswa:
- Registrasi & Login akun mahasiswa
- Buat laporan kerusakan + upload foto bukti
- Lihat history laporan pribadi
- Tracking status laporan real-time

Dashboard statistik pribadi

Untuk Dosen:
- Registrasi & Login akun dosen
- Kelola semua laporan dari mahasiswa
- Update status laporan (Dilaporkan → Dalam Penanganan → Selesai/Ditolak)
- Dashboard statistik lengkap dengan analytics
- History & timeline tracking seluruh laporan
- Analytics dan reporting

Teknologi yang Digunakan
- Frontend: React 18 + TypeScript + Tailwind CSS
- Backend: Python FastAPI + SQLite + JWT Authentication
- Database: SQLite dengan SQLAlchemy ORM

CARA MENJALANKAN APLIKASI
LANGKAH 1: JALANKAN BACKEND
Buka Command Prompt/Terminal pertama, lalu ketik perintah berikut:
1. cd backend
2. pip install -r requirements.txt
3. python run.py
4. Tunggu hingga muncul pesan:
Uvicorn running on http://localhost:8000

LANGKAH 2: JALANKAN FRONTEND
1. Buka Command Prompt/Terminal kedua, lalu ketik perintah berikut:
2. cd frontend
3. npm install
4. npm start
5. Tunggu hingga browser terbuka otomatis ke: http://localhost:3000

AKUN TESTING (Sudah Tersedia)
Akun Dosen:
- Username: dosen
- Password: password123

Akun Mahasiswa:
- Username: mahasiswa
- Password: password123

CARA TESTING APLIKASI
- TESTING SEBAGAI MAHASISWA:
- Login dengan akun mahasiswa
- Klik "Buat Laporan" untuk membuat laporan baru
- Isi form dan upload foto bukti kerusakan
- Klik "Laporan Saya" untuk melihat daftar laporan
- Klik "History" untuk melacak status laporan

TESTING SEBAGAI DOSEN:
- Login dengan akun dosen
- Klik "Kelola Laporan" untuk melihat semua laporan
- Klik "Update Status" pada laporan untuk mengubah status
- Klik "History" untuk melihat timeline lengkap
- Klik "Statistik" untuk melihat dashboard analytics

TESTING FLOW LENGKAP:
1. Mahasiswa buat laporan → Status: "Dilaporkan"
2. Dosen update status → "Dalam Penanganan"
3. Dosen update status → "Selesai"
4. Mahasiswa lihat perubahan status di History

TROUBLESHOOTING
- Jika port 3000/8000 sudah digunakan:
- npx kill-port 3000
- npx kill-port 8000

Jika ada error dependencies:
- cd frontend
- rm -rf node_modules
- npm install

Jika Python packages error:
- cd backend
- pip install fastapi uvicorn sqlalchemy python-multipart python-jose[cryptography] passlib[bcrypt]

FITUR YANG BERFUNGSI

✅ Authentication & Login/Register
✅ Buat Laporan dengan Upload Foto
✅ Kelola Laporan (CRUD Lengkap)
✅ Update Status Laporan
✅ History & Timeline Tracking
✅ Dashboard Analytics & Statistik
✅ Responsive Design (Mobile & Desktop)
✅ Real-time Data Updates
✅ Error Handling & Validation
✅ Role-based Access Control

by PAPAT COMUNITY