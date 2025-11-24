from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: str
    nama_lengkap: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class LaporanBase(BaseModel):
    judul: str
    deskripsi: str
    kategori: str
    jenis_fasilitas: str
    lokasi: str

class LaporanCreate(LaporanBase):
    pass

class LaporanResponse(LaporanBase):
    id: int
    prioritas: str
    status: str
    foto_url: Optional[str]
    user_id: int
    dosen_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class StatusHistoryBase(BaseModel):
    status: str
    catatan: Optional[str] = None

class StatusHistoryResponse(StatusHistoryBase):
    id: int
    laporan_id: int
    user_id: int
    nama_lengkap: str
    created_at: datetime

    class Config:
        from_attributes = True

class StatusUpdate(BaseModel):
    status: str
    catatan: Optional[str] = None

class StatistikResponse(BaseModel):
    total_laporan: int
    laporan_bulan_ini: int
    rata_waktu_penanganan: str
    per_status: List[dict]
    per_kategori: List[dict]
    per_fasilitas: List[dict]
    dalam_penanganan: int
    selesai: int
    ditolak: int
    dilaporkan: int

    class Config:
        from_attributes = True