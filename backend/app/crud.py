import asyncpg
from app import schemas, auth
from typing import List, Optional

# User CRUD
async def create_user(user: schemas.UserCreate, conn: asyncpg.Connection) -> asyncpg.Record:
    hashed_password = auth.hash_password(user.password)
    query = """
        INSERT INTO users (username, email, password_hash, role, nama_lengkap)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id, username, email, role, nama_lengkap, created_at
    """
    return await conn.fetchrow(query, user.username, user.email, hashed_password, user.role, user.nama_lengkap)

async def get_user_by_username(username: str, conn: asyncpg.Connection) -> asyncpg.Record:
    query = "SELECT * FROM users WHERE username = $1"
    return await conn.fetchrow(query, username)

# Laporan CRUD
async def create_laporan(laporan: schemas.LaporanCreate, user_id: int, conn: asyncpg.Connection) -> asyncpg.Record:
    # Tentukan prioritas berdasarkan jenis_fasilitas dan kategori
    prioritas = "rendah"
    if laporan.jenis_fasilitas.lower() in ["listrik", "komputer", "proyektor", "ac"]:
        prioritas = "tinggi"
    elif laporan.jenis_fasilitas.lower() in ["kursi", "meja", "papan tulis", "pintu", "jendela"]:
        prioritas = "sedang"
    
    # Jika kategori rusak_berat, naikkan prioritas
    if laporan.kategori == "rusak_berat":
        if prioritas == "sedang":
            prioritas = "tinggi"
        elif prioritas == "rendah":
            prioritas = "sedang"

    query = """
        INSERT INTO laporan (judul, deskripsi, kategori, jenis_fasilitas, prioritas, foto_url, user_id)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING *
    """
    return await conn.fetchrow(query, laporan.judul, laporan.deskripsi, laporan.kategori, laporan.jenis_fasilitas, prioritas, laporan.foto_url, user_id)

async def get_laporan_by_id(laporan_id: int, conn: asyncpg.Connection) -> asyncpg.Record:
    query = "SELECT * FROM laporan WHERE id = $1"
    return await conn.fetchrow(query, laporan_id)

async def get_laporan_by_user(user_id: int, conn: asyncpg.Connection) -> List[asyncpg.Record]:
    query = "SELECT * FROM laporan WHERE user_id = $1 ORDER BY created_at DESC"
    return await conn.fetch(query, user_id)

async def get_all_laporan(conn: asyncpg.Connection) -> List[asyncpg.Record]:
    query = "SELECT * FROM laporan ORDER BY created_at DESC"
    return await conn.fetch(query)

async def update_status_laporan(laporan_id: int, status: str, catatan: Optional[str], dosen_id: int, conn: asyncpg.Connection) -> asyncpg.Record:
    # Update laporan
    query = """
        UPDATE laporan 
        SET status = $1, dosen_id = $2, updated_at = CURRENT_TIMESTAMP
        WHERE id = $3
        RETURNING *
    """
    updated_laporan = await conn.fetchrow(query, status, dosen_id, laporan_id)
    
    # Insert history
    history_query = """
        INSERT INTO status_history (laporan_id, status, catatan, user_id)
        VALUES ($1, $2, $3, $4)
    """
    await conn.execute(history_query, laporan_id, status, catatan, dosen_id)
    
    return updated_laporan

async def get_history_by_laporan(laporan_id: int, conn: asyncpg.Connection) -> List[asyncpg.Record]:
    query = "SELECT * FROM status_history WHERE laporan_id = $1 ORDER BY created_at DESC"
    return await conn.fetch(query, laporan_id)