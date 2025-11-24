-- Database initialization for CivitasFix UPN Veteran Jatim

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) CHECK (role IN ('mahasiswa', 'dosen')) NOT NULL,
    nama_lengkap VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS laporan (
    id SERIAL PRIMARY KEY,
    judul VARCHAR(200) NOT NULL,
    deskripsi TEXT NOT NULL,
    kategori VARCHAR(50) CHECK (kategori IN ('rusak_berat', 'rusak_ringan')) NOT NULL,
    jenis_fasilitas VARCHAR(100) NOT NULL,
    prioritas VARCHAR(20) CHECK (prioritas IN ('tinggi', 'sedang', 'rendah')) NOT NULL,
    foto_url VARCHAR(255),
    status VARCHAR(20) CHECK (status IN ('dilaporkan', 'dalam_penanganan', 'selesai', 'ditolak')) DEFAULT 'dilaporkan',
    user_id INTEGER REFERENCES users(id),
    dosen_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS status_history (
    id SERIAL PRIMARY KEY,
    laporan_id INTEGER REFERENCES laporan(id),
    status VARCHAR(20) NOT NULL,
    catatan TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER REFERENCES users(id)
);

-- Insert sample data untuk testing
INSERT INTO users (username, email, password_hash, role, nama_lengkap) VALUES
('admin', 'admin@upnjatim.ac.id', '$2b$12$EXAMPLEHASH', 'dosen', 'Admin UPN'),
('dosen01', 'dosen01@upnjatim.ac.id', '$2b$12$EXAMPLEHASH', 'dosen', 'Dr. Ahmad, M.Kom'),
('mahasiswa01', 'mahasiswa01@student.upnjatim.ac.id', '$2b$12$EXAMPLEHASH', 'mahasiswa', 'Budi Santoso');