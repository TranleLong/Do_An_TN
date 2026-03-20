import os

# Cấu hình media và static dirs
import erp_tien_huong.settings as st
os.makedirs(st.BASE_DIR / 'static' / 'css', exist_ok=True)
os.makedirs(st.BASE_DIR / 'static' / 'img', exist_ok=True)
os.makedirs(st.BASE_DIR / 'static' / 'js', exist_ok=True)
os.makedirs(st.BASE_DIR / 'media' / 'hang_hoa', exist_ok=True)

# Khởi tạo migrate
os.system('python manage.py makemigrations core danh_muc kho ban_hang mua_hang')
os.system('python manage.py migrate')
