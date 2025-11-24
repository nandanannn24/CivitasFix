import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings

async def send_email(to_email: str, subject: str, body: str):
    """
    Send email menggunakan SMTP
    """
    try:
        # Jika SMTP tidak dikonfigurasi, skip
        if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
            print(f"SMTP not configured. Would send email to: {to_email}")
            print(f"Subject: {subject}")
            return True

        msg = MIMEMultipart()
        msg['From'] = settings.SMTP_USERNAME
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"✅ Email sent to {to_email}")
        return True
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False

async def send_status_notification(email: str, laporan_id: int, status: str, catatan: str = None):
    """
    Kirim notifikasi status laporan
    """
    status_text = {
        'dilaporkan': 'Dilaporkan',
        'dalam_penanganan': 'Dalam Penanganan',
        'selesai': 'Selesai',
        'ditolak': 'Ditolak'
    }.get(status, status)
    
    subject = f"Update Status Laporan #{laporan_id} - CivitasFix UPN Jatim"
    
    body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(to right, #1E40AF, #10B981); color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background: #f9f9f9; }}
            .status {{ padding: 10px; border-radius: 5px; font-weight: bold; }}
            .dilaporkan {{ background: #FEF3C7; color: #92400E; }}
            .dalam_penanganan {{ background: #DBEAFE; color: #1E40AF; }}
            .selesai {{ background: #D1FAE5; color: #065F46; }}
            .ditolak {{ background: #FEE2E2; color: #991B1B; }}
            .footer {{ text-align: center; padding: 20px; color: #6B7280; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>CivitasFix UPN Veteran Jatim</h1>
                <p>Sistem Laporan Kerusakan Fasilitas Kampus</p>
            </div>
            
            <div class="content">
                <h2>Status Laporan Anda Telah Diupdate</h2>
                <p><strong>Laporan ID:</strong> #{laporan_id}</p>
                
                <div class="status {status}">
                    <strong>Status Baru:</strong> {status_text}
                </div>
                
                {f'<p><strong>Catatan:</strong> {catatan}</p>' if catatan else '<p><strong>Catatan:</strong> Tidak ada catatan tambahan</p>'}
                
                <p>Anda dapat memantau perkembangan laporan Anda melalui aplikasi CivitasFix.</p>
                
                <p>Terima kasih telah membantu menjaga fasilitas kampus kami.</p>
            </div>
            
            <div class="footer">
                <p>© 2024 CivitasFix - UPN Veteran Jawa Timur</p>
                <p>Email ini dikirim otomatis, mohon tidak membalas.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    await send_email(email, subject, body)