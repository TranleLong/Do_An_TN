#!/usr/bin/env bash
set -e

python manage.py migrate
python manage.py collectstatic --noinput

# Tạo superuser tự động nếu chưa có
python manage.py shell << END
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print("✓ Tạo tài khoản admin/admin123 thành công")
else:
    print("✓ Tài khoản admin đã tồn tại")
END

# Tạo dữ liệu demo (Đã tạm đóng vì thiếu file init_full_demo.py)
# python init_full_demo.py
