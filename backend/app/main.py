from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
import aiofiles
import os
import uuid
from typing import List, Optional
from datetime import datetime
import json

from app import schemas, auth, email
from app.database import get_connection, create_tables
from app.config import settings

# Initialize FastAPI app
app = FastAPI(
    title="CivitasFix API", 
    description="API untuk Laporan Kerusakan Fasilitas Kampus UPN Veteran Jatim",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# CORS configuration - PERBAIKI INI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
# Create uploads directory if not exists
if not os.path.exists("uploads"):
    os.makedirs("uploads")

# Mount static files for uploaded images
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Database connection dependency
def get_db():
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()

# Authentication dependency - PERBAIKI INI
async def get_current_user(
    token: str = Depends(oauth2_scheme),  # ✅ Gunakan oauth2_scheme
    conn = Depends(get_db)
):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token tidak valid",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Verify token
        payload = auth.verify_token(token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token tidak valid atau expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Use helper function to execute query
        users = execute_query(conn, "SELECT * FROM users WHERE username = ?", (payload.get("sub"),))
        if not users:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User tidak ditemukan",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = users[0]
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Helper function untuk execute query
def execute_query(conn, query, params=None):
    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        # For SELECT queries, return results
        if query.strip().upper().startswith('SELECT'):
            columns = [desc[0] for desc in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            return results
        elif query.strip().upper().startswith('INSERT'):
            conn.commit()
            return cursor.lastrowid
        else:
            conn.commit()
            return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()

# Create tables on startup
@app.on_event("startup")
async def startup_event():
    create_tables()
    print("✅ CivitasFix API started successfully!")
    print("📚 API Documentation available at: http://localhost:8000/docs")

# ==================== AUTH ENDPOINTS ====================

@app.post("/register", response_model=schemas.UserResponse)
async def register(user: schemas.UserCreate, conn = Depends(get_db)):
    """
    Register user baru (mahasiswa atau dosen)
    """
    try:
        # ✅ VALIDASI PASSWORD: Max 72 characters untuk bcrypt
        if len(user.password) > 72:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password tidak boleh lebih dari 72 karakter"
            )
        
        # ✅ VALIDASI PASSWORD: Min 6 characters  
        if len(user.password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password minimal 6 karakter"
            )

        # Cek username sudah ada
        existing_users = execute_query(
            conn, 
            "SELECT * FROM users WHERE username = ? OR email = ?", 
            (user.username, user.email)
        )
        
        if existing_users:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username atau email sudah terdaftar"
            )
        
        # Validasi role
        if user.role not in ["mahasiswa", "dosen"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role harus 'mahasiswa' atau 'dosen'"
            )
        
        # Hash password
        hashed_password = auth.hash_password(user.password)
        
        # Insert user
        user_id = execute_query(
            conn,
            "INSERT INTO users (username, email, password_hash, role, nama_lengkap) VALUES (?, ?, ?, ?, ?)",
            (user.username, user.email, hashed_password, user.role, user.nama_lengkap)
        )
        
        # Get created user
        new_users = execute_query(conn, "SELECT * FROM users WHERE id = ?", (user_id,))
        if not new_users:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
            
        new_user = new_users[0]
        return new_user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during registration: {str(e)}"
        )

@app.post("/login", response_model=schemas.Token)
async def login(user_login: schemas.UserLogin, conn = Depends(get_db)):
    """
    Login user dengan username dan password
    """
    try:
        users = execute_query(conn, "SELECT * FROM users WHERE username = ?", (user_login.username,))
        
        if not users or not auth.verify_password(user_login.password, users[0]['password_hash']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Username atau password salah",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_data = users[0]
        access_token = auth.create_access_token(data={"sub": user_data['username']})
        return {"access_token": access_token, "token_type": "bearer"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during login: {str(e)}"
        )

@app.get("/users/me", response_model=schemas.UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get informasi user yang sedang login
    """
    return current_user

# ==================== LAPORAN ENDPOINTS ====================

@app.post("/laporan", response_model=schemas.LaporanResponse)
async def buat_laporan(
    judul: str = Form(...),
    deskripsi: str = Form(...),
    kategori: str = Form(...),
    jenis_fasilitas: str = Form(...),
    lokasi: str = Form(...),
    foto: Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user),
    conn = Depends(get_db)
):
    """
    Buat laporan kerusakan baru (hanya mahasiswa)
    """
    if current_user['role'] != 'mahasiswa':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Hanya mahasiswa yang dapat membuat laporan"
        )
    
    try:
        # Upload foto jika ada
        foto_url = None
        if foto and foto.filename:
            try:
                # Validate file type
                if not foto.content_type.startswith('image/'):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="File harus berupa gambar (JPEG, PNG, dll.)"
                    )
                
                # Generate unique filename
                file_extension = foto.filename.split(".")[-1] if "." in foto.filename else "jpg"
                filename = f"{uuid.uuid4()}.{file_extension}"
                file_location = f"uploads/{filename}"
                
                # Save file
                async with aiofiles.open(file_location, "wb") as f:
                    content = await foto.read()
                    await f.write(content)
                
                foto_url = f"http://localhost:8000/uploads/{filename}"
                
            except HTTPException:
                raise
            except Exception as e:
                print(f"Upload error: {e}")
                # Continue without photo if upload fails
        
        # Tentukan prioritas otomatis berdasarkan jenis fasilitas dan kategori
        prioritas = "rendah"
        jenis_fasilitas_lower = jenis_fasilitas.lower()
        
        # Fasilitas elektronik dan penting dapat prioritas tinggi
        if any(keyword in jenis_fasilitas_lower for keyword in 
               ["proyektor", "ac", "komputer", "listrik", "internet", "jaringan", "server"]):
            prioritas = "tinggi"
        # Fasilitas umum dapat prioritas sedang
        elif any(keyword in jenis_fasilitas_lower for keyword in 
                 ["kursi", "meja", "papan tulis", "pintu", "jendela", "toilet", "lampu", "washtafel"]):
            prioritas = "sedang"
        
        # Naikkan prioritas jika rusak berat
        if kategori == "rusak_berat":
            if prioritas == "sedang":
                prioritas = "tinggi"
            elif prioritas == "rendah":
                prioritas = "sedang"

        # Insert laporan
        laporan_id = execute_query(
            conn, 
            """INSERT INTO laporan (judul, deskripsi, kategori, jenis_fasilitas, lokasi, prioritas, foto_url, user_id, status) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (judul, deskripsi, kategori, jenis_fasilitas, lokasi, prioritas, foto_url, current_user['id'], 'dilaporkan')
        )
        
        # Get created laporan
        laporans = execute_query(conn, "SELECT * FROM laporan WHERE id = ?", (laporan_id,))
        if not laporans:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create laporan"
            )
            
        new_laporan = laporans[0]
        return new_laporan
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating laporan: {str(e)}"
        )

@app.get("/laporan/me", response_model=List[schemas.LaporanResponse])
async def get_my_laporan(
    current_user: dict = Depends(get_current_user), 
    conn = Depends(get_db)
):
    """
    Get semua laporan milik user yang login (mahasiswa)
    """
    try:
        laporans = execute_query(
            conn, 
            "SELECT * FROM laporan WHERE user_id = ? ORDER BY created_at DESC", 
            (current_user['id'],)
        )
        return laporans
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting laporan: {str(e)}"
        )

@app.get("/laporan", response_model=List[schemas.LaporanResponse])
async def get_all_laporan(
    current_user: dict = Depends(get_current_user), 
    conn = Depends(get_db)
):
    """
    Get semua laporan (hanya dosen)
    """
    if current_user['role'] != 'dosen':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Hanya dosen yang dapat melihat semua laporan"
        )
    
    try:
        laporans = execute_query(
            conn, 
            "SELECT * FROM laporan ORDER BY created_at DESC"
        )
        return laporans
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting laporan: {str(e)}"
        )

@app.get("/laporan/{laporan_id}", response_model=schemas.LaporanResponse)
async def get_laporan_detail(
    laporan_id: int, 
    current_user: dict = Depends(get_current_user), 
    conn = Depends(get_db)
):
    """
    Get detail laporan by ID
    """
    try:
        laporans = execute_query(conn, "SELECT * FROM laporan WHERE id = ?", (laporan_id,))
        if not laporans:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Laporan tidak ditemukan"
            )
        
        laporan_data = laporans[0]
        
        # Cek akses: mahasiswa hanya bisa lihat laporan sendiri
        if (current_user['role'] == 'mahasiswa' and 
            laporan_data['user_id'] != current_user['id']):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Akses ditolak"
            )
        
        return laporan_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting laporan detail: {str(e)}"
        )

@app.put("/laporan/{laporan_id}/status", response_model=schemas.LaporanResponse)
async def update_status(
    laporan_id: int,
    status_update: schemas.StatusUpdate,
    current_user: dict = Depends(get_current_user),
    conn = Depends(get_db)
):
    """
    Update status laporan (hanya dosen)
    """
    if current_user['role'] != 'dosen':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Hanya dosen yang dapat mengupdate status laporan"
        )
    
    try:
        # Cek laporan exists
        laporans = execute_query(conn, "SELECT * FROM laporan WHERE id = ?", (laporan_id,))
        if not laporans:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Laporan tidak ditemukan"
            )
        
        laporan_data = laporans[0]
        
        # Update laporan status
        execute_query(
            conn,
            "UPDATE laporan SET status = ?, dosen_id = ?, updated_at = datetime('now') WHERE id = ?",
            (status_update.status, current_user['id'], laporan_id)
        )
        
        # Insert status history
        execute_query(
            conn,
            "INSERT INTO status_history (laporan_id, status, catatan, user_id) VALUES (?, ?, ?, ?)",
            (laporan_id, status_update.status, status_update.catatan, current_user['id'])
        )
        
        # Get user email for notification (jika ada SMTP configured)
        if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
            try:
                user_results = execute_query(
                    conn, 
                    "SELECT email FROM users WHERE id = ?", 
                    (laporan_data['user_id'],)
                )
                if user_results:
                    user_email = user_results[0]['email']
                    
                    # Send email notification
                    await email.send_status_notification(
                        user_email, 
                        laporan_id, 
                        status_update.status, 
                        status_update.catatan
                    )
            except Exception as e:
                print(f"Email notification error: {e}")
                # Continue without email if failed
        
        # Get updated laporan
        updated_laporans = execute_query(conn, "SELECT * FROM laporan WHERE id = ?", (laporan_id,))
        if not updated_laporans:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get updated laporan"
            )
            
        updated_laporan = updated_laporans[0]
        return updated_laporan
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating status: {str(e)}"
        )

@app.get("/laporan/{laporan_id}/history", response_model=List[schemas.StatusHistoryResponse])
async def get_history(
    laporan_id: int, 
    current_user: dict = Depends(get_current_user), 
    conn = Depends(get_db)
):
    """
    Get history status untuk laporan tertentu
    """
    try:
        # Cek apakah user berhak akses history ini
        laporans = execute_query(conn, "SELECT * FROM laporan WHERE id = ?", (laporan_id,))
        if not laporans:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Laporan tidak ditemukan"
            )
        
        laporan_data = laporans[0]
        if (current_user['role'] == 'mahasiswa' and 
            laporan_data['user_id'] != current_user['id']):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Akses ditolak"
            )
        
        history = execute_query(
            conn,
            """SELECT sh.*, u.nama_lengkap 
               FROM status_history sh 
               JOIN users u ON sh.user_id = u.id 
               WHERE sh.laporan_id = ? 
               ORDER BY sh.created_at DESC""",
            (laporan_id,)
        )
        return history
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting history: {str(e)}"
        )

# ==================== STATISTIK ENDPOINTS ====================

# ==================== STATISTIK ENDPOINTS ====================

@app.get("/statistik", response_model=schemas.StatistikResponse)
async def get_statistik(
    current_user: dict = Depends(get_current_user), 
    conn = Depends(get_db)
):
    """
    Get statistik laporan (hanya dosen) - PERBAIKI DENGAN DATA REAL
    """
    if current_user['role'] != 'dosen':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Hanya dosen yang dapat melihat statistik"
        )
    
    try:
        # Total laporan
        total_result = execute_query(conn, "SELECT COUNT(*) as count FROM laporan")
        total = total_result[0]['count'] if total_result else 0
        
        # Laporan bulan ini (SQLite format) - PERBAIKI QUERY
        bulan_ini_result = execute_query(
            conn,
            "SELECT COUNT(*) as count FROM laporan WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')"
        )
        bulan_ini = bulan_ini_result[0]['count'] if bulan_ini_result else 0
        
        # Laporan per status - PERBAIKI: Hitung masing-masing status
        status_dilaporkan = execute_query(conn, "SELECT COUNT(*) as count FROM laporan WHERE status = 'dilaporkan'")
        status_dalam_penanganan = execute_query(conn, "SELECT COUNT(*) as count FROM laporan WHERE status = 'dalam_penanganan'")
        status_selesai = execute_query(conn, "SELECT COUNT(*) as count FROM laporan WHERE status = 'selesai'")
        status_ditolak = execute_query(conn, "SELECT COUNT(*) as count FROM laporan WHERE status = 'ditolak'")
        
        # Format status stats untuk response
        status_stats = [
            {"status": "dilaporkan", "count": status_dilaporkan[0]['count'] if status_dilaporkan else 0},
            {"status": "dalam_penanganan", "count": status_dalam_penanganan[0]['count'] if status_dalam_penanganan else 0},
            {"status": "selesai", "count": status_selesai[0]['count'] if status_selesai else 0},
            {"status": "ditolak", "count": status_ditolak[0]['count'] if status_ditolak else 0}
        ]
        
        # Laporan per kategori - PERBAIKI QUERY
        kategori_stats = execute_query(
            conn,
            "SELECT kategori, COUNT(*) as count FROM laporan GROUP BY kategori"
        )
        
        # Laporan per fasilitas (top 10) - PERBAIKI QUERY
        fasilitas_stats = execute_query(
            conn,
            """SELECT jenis_fasilitas, COUNT(*) as count 
               FROM laporan 
               GROUP BY jenis_fasilitas 
               ORDER BY count DESC 
               LIMIT 10"""
        )
        
        # Hitung rata-rata waktu penanganan - PERBAIKI DENGAN LOGIKA REAL
        avg_time_result = execute_query(
            conn,
            """SELECT AVG(julianday(updated_at) - julianday(created_at)) as avg_days 
               FROM laporan WHERE status = 'selesai'"""
        )
        
        avg_days = avg_time_result[0]['avg_days'] if avg_time_result and avg_time_result[0]['avg_days'] else 0
        rata_waktu_penanganan = f"{avg_days:.1f} hari" if avg_days > 0 else "Belum ada data"
        
        # Format response - PASTIKAN SESUAI DENGAN SCHEMA
        statistik_data = {
            "total_laporan": total,
            "laporan_bulan_ini": bulan_ini,
            "rata_waktu_penanganan": rata_waktu_penanganan,
            "per_status": status_stats,
            "per_kategori": kategori_stats if kategori_stats else [],
            "per_fasilitas": fasilitas_stats if fasilitas_stats else [],
            "dalam_penanganan": status_dalam_penanganan[0]['count'] if status_dalam_penanganan else 0,
            "selesai": status_selesai[0]['count'] if status_selesai else 0,
            "ditolak": status_ditolak[0]['count'] if status_ditolak else 0,
            "dilaporkan": status_dilaporkan[0]['count'] if status_dilaporkan else 0
        }
        
        return statistik_data
        
    except Exception as e:
        print(f"Error in statistik: {e}")
        # Return default data jika error
        return {
            "total_laporan": 0,
            "laporan_bulan_ini": 0,
            "rata_waktu_penanganan": "0 hari",
            "per_status": [],
            "per_kategori": [],
            "per_fasilitas": [],
            "dalam_penanganan": 0,
            "selesai": 0,
            "ditolak": 0,
            "dilaporkan": 0
        }

# ==================== UPLOAD ENDPOINTS ====================

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload file (foto) untuk laporan
    """
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="File harus berupa gambar (JPEG, PNG, dll.)"
            )
        
        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Seek back to start
        
        if file_size > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File terlalu besar. Maksimal 10MB"
            )
        
        # Generate unique filename
        file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        filename = f"{uuid.uuid4()}.{file_extension}"
        file_location = f"uploads/{filename}"
        
        # Save file
        async with aiofiles.open(file_location, "wb") as f:
            content = await file.read()
            await f.write(content)
        
        return {
            "filename": filename,
            "url": f"http://localhost:8000/uploads/{filename}",
            "message": "File berhasil diupload",
            "size": file_size
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file: {str(e)}"
        )

# ==================== HEALTH CHECK & ROOT ====================

@app.get("/")
async def root():
    """
    Root endpoint - API information
    """
    return {
        "message": "Selamat datang di CivitasFix API - UPN Veteran Jatim",
        "version": "1.0.0",
        "description": "Sistem Laporan Kerusakan Fasilitas Kampus",
        "docs": "/docs",
        "endpoints": {
            "auth": ["POST /register", "POST /login", "GET /users/me"],
            "laporan": [
                "POST /laporan", 
                "GET /laporan/me", 
                "GET /laporan", 
                "GET /laporan/{id}", 
                "PUT /laporan/{id}/status",
                "GET /laporan/{id}/history"
            ],
            "statistik": ["GET /statistik"],
            "upload": ["POST /upload"],
            "health": ["GET /health"]
        }
    }

@app.get("/health")
async def health_check(conn = Depends(get_db)):
    """
    Health check endpoint
    """
    try:
        # Test database connection
        execute_query(conn, "SELECT 1")
        
        # Check if tables exist
        tables = execute_query(
            conn, 
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('users', 'laporan', 'status_history')"
        )
        
        table_status = {
            "users": any(table['name'] == 'users' for table in tables),
            "laporan": any(table['name'] == 'laporan' for table in tables),
            "status_history": any(table['name'] == 'status_history' for table in tables)
        }
        
        return {
            "status": "healthy",
            "database": "connected",
            "tables": table_status,
            "timestamp": datetime.now().isoformat(),
            "environment": "development"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail=f"Service unhealthy: {str(e)}"
        )

# ==================== ERROR HANDLERS ====================

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Endpoint tidak ditemukan"},
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Terjadi kesalahan internal server"},
    )

@app.exception_handler(422)
async def validation_error_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": "Data yang dikirim tidak valid"},
    )

# Application entry point
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )