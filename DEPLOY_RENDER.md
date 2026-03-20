# Deploy ERP lên Render

## 1) Đẩy code lên GitHub
1. Tạo repository mới trên GitHub.
2. Push toàn bộ source code dự án lên branch chính.

## 2) Tạo PostgreSQL trên Render
1. Vào Render Dashboard -> **New** -> **PostgreSQL**.
2. Tạo DB và chờ trạng thái `Available`.
3. Copy giá trị **External Database URL** (dùng cho `DATABASE_URL`).

## 3) Tạo Web Service
1. Vào Render Dashboard -> **New** -> **Web Service**.
2. Chọn repo GitHub của dự án.
3. Cấu hình:
   - **Runtime**: Python
   - **Build Command**: `pip install -r requirements.txt && bash render-build.sh`
   - **Start Command**: `gunicorn erp_tien_huong.wsgi:application --log-file -`

## 4) Khai báo Environment Variables
Thêm các biến sau trong mục Environment:

- `SECRET_KEY`: chuỗi bí mật mạnh (tự tạo)
- `DEBUG`: `False`
- `ALLOWED_HOSTS`: `<ten-service>.onrender.com`
- `CSRF_TRUSTED_ORIGINS`: `https://<ten-service>.onrender.com`
- `DATABASE_URL`: dán External Database URL từ PostgreSQL
- `SECURE_SSL_REDIRECT`: `True`

## 5) Deploy
1. Bấm **Create Web Service**.
2. Chờ build/deploy hoàn tất.
3. Mở URL `https://<ten-service>.onrender.com` để kiểm tra.

## 6) Tạo tài khoản admin sau deploy (chạy 1 lần)
Mở Shell của Render Web Service và chạy:

`python manage.py createsuperuser`

## 7) Lưu ý
- Không dùng SQLite cho production, nên dùng PostgreSQL.
- Mỗi lần push code lên GitHub, Render sẽ tự deploy lại.
