import sqlite3
import os
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Gunakan SQLite untuk development
DATABASE_URL = "sqlite:///./civitasfix.db"

def get_connection():
    """Get SQLite database connection"""
    try:
        conn = sqlite3.connect("civitasfix.db", check_same_thread=False)
        conn.row_factory = sqlite3.Row  # This enables column access by name
        
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise e

def create_tables():
    """Create tables dengan SQLite"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # SQLite schema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT CHECK (role IN ('mahasiswa', 'dosen')) NOT NULL,
                nama_lengkap TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS laporan (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                judul TEXT NOT NULL,
                deskripsi TEXT NOT NULL,
                kategori TEXT CHECK (kategori IN ('rusak_berat', 'rusak_ringan')) NOT NULL,
                jenis_fasilitas TEXT NOT NULL,
                lokasi TEXT NOT NULL,
                prioritas TEXT CHECK (prioritas IN ('tinggi', 'sedang', 'rendah')) NOT NULL,
                foto_url TEXT,
                status TEXT CHECK (status IN ('dilaporkan', 'dalam_penanganan', 'selesai', 'ditolak')) DEFAULT 'dilaporkan',
                user_id INTEGER REFERENCES users(id),
                dosen_id INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS status_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                laporan_id INTEGER REFERENCES laporan(id),
                status TEXT NOT NULL,
                catatan TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER REFERENCES users(id)
            )
        ''')
        
        conn.commit()
        print("✅ SQLite tables created successfully!")
        
        # Insert sample data for testing
        insert_sample_data(conn, cursor)
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def insert_sample_data(conn, cursor):
    """Insert sample data untuk testing"""
    try:
        # Check if users already exist
        cursor.execute("SELECT COUNT(*) as count FROM users")
        result = cursor.fetchone()
        user_count = result[0] if result else 0
        
        if user_count == 0:
            print("📝 Inserting sample data...")
            
            # ✅ FIX: Gunakan password sederhana tanpa hash kompleks
            sample_users = [
                # Format: (username, email, password_plain, role, nama_lengkap)
                ('admin', 'admin@upnjatim.ac.id', 'admin123', 'dosen', 'Admin UPN'),
                ('dosen01', 'dosen01@upnjatim.ac.id', 'dosen123', 'dosen', 'Dr. Ahmad, M.Kom'),
                ('mahasiswa01', 'mahasiswa01@student.upnjatim.ac.id', 'mhs123', 'mahasiswa', 'Budi Santoso'),
                ('mahasiswa02', 'mahasiswa02@student.upnjatim.ac.id', 'mhs123', 'mahasiswa', 'Siti Rahayu')
            ]
            
            for user in sample_users:
                try:
                    # Hash password menggunakan auth.hash_password
                    from app.auth import hash_password
                    hashed_password = hash_password(user[2])
                    
                    cursor.execute(
                        "INSERT OR IGNORE INTO users (username, email, password_hash, role, nama_lengkap) VALUES (?, ?, ?, ?, ?)",
                        (user[0], user[1], hashed_password, user[3], user[4])
                    )
                    print(f"✅ User {user[0]} created")
                except Exception as e:
                    print(f"❌ Error inserting user {user[0]}: {e}")
                    # Skip user ini dan lanjutkan
            
            # Sample reports
            sample_reports = [
                ('Kursi rusak di A301', 'Terdapat 2 kursi yang kakinya patah di ruang A301', 'rusak_ringan', 'Kursi Kuliah', 'Gedung A Lantai 3 Ruang A301', 'sedang', None, 3, 'dilaporkan'),
                ('Proyektor tidak menyala', 'Proyektor di ruang B202 mati total, tidak ada display', 'rusak_berat', 'Proyektor', 'Gedung B Lantai 2 Ruang B202', 'tinggi', None, 3, 'dalam_penanganan'),
            ]
            
            for report in sample_reports:
                try:
                    cursor.execute(
                        "INSERT INTO laporan (judul, deskripsi, kategori, jenis_fasilitas, lokasi, prioritas, foto_url, user_id, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        report
                    )
                except Exception as e:
                    print(f"Error inserting report: {e}")
            
            conn.commit()
            print("✅ Sample data inserted successfully!")
            
    except Exception as e:
        print(f"❌ Error in sample data: {e}")
        conn.rollback()