from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('danh_muc', '0002_add_catalog_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='hanghoa',
            name='cao_cm',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Cao (cm)'),
        ),
        migrations.AddField(
            model_name='hanghoa',
            name='co_the_xep_chong',
            field=models.BooleanField(default=True, verbose_name='Có thể xếp chồng'),
        ),
        migrations.AddField(
            model_name='hanghoa',
            name='dai_cm',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Dài (cm)'),
        ),
        migrations.AddField(
            model_name='hanghoa',
            name='khoi_luong_kg',
            field=models.DecimalField(decimal_places=3, default=0, max_digits=10, verbose_name='Khối lượng (kg)'),
        ),
        migrations.AddField(
            model_name='hanghoa',
            name='loai_luu_tru',
            field=models.CharField(choices=[('cai', 'Cái'), ('hop', 'Hộp'), ('khay', 'Khay'), ('thung', 'Thùng'), ('kien', 'Kiện'), ('pack', 'Pack')], default='cai', max_length=20, verbose_name='Loại lưu trữ'),
        ),
        migrations.AddField(
            model_name='hanghoa',
            name='loai_o_phu_hop',
            field=models.CharField(choices=[('nho', 'Nhỏ'), ('vua', 'Vừa'), ('lon', 'Lớn'), ('nang', 'Nặng'), ('cong_kenh', 'Cồng kềnh')], default='vua', max_length=20, verbose_name='Loại ô phù hợp'),
        ),
        migrations.AddField(
            model_name='hanghoa',
            name='quy_cach_dong_goi',
            field=models.CharField(blank=True, max_length=120, verbose_name='Quy cách đóng gói'),
        ),
        migrations.AddField(
            model_name='hanghoa',
            name='rong_cm',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Rộng (cm)'),
        ),
        migrations.AddField(
            model_name='hanghoa',
            name='so_luong_toi_da_moi_o',
            field=models.IntegerField(default=10, verbose_name='Số lượng tối đa mỗi ô'),
        ),
        migrations.AddField(
            model_name='vitrikho',
            name='cao_cm',
            field=models.DecimalField(decimal_places=2, default=35, max_digits=10, verbose_name='Cao ô (cm)'),
        ),
        migrations.AddField(
            model_name='vitrikho',
            name='dai_cm',
            field=models.DecimalField(decimal_places=2, default=60, max_digits=10, verbose_name='Dài ô (cm)'),
        ),
        migrations.AddField(
            model_name='vitrikho',
            name='loai_o',
            field=models.CharField(choices=[('nho', 'Nhỏ'), ('vua', 'Vừa'), ('lon', 'Lớn'), ('nang', 'Nặng'), ('cong_kenh', 'Cồng kềnh')], default='vua', max_length=20, verbose_name='Loại ô'),
        ),
        migrations.AddField(
            model_name='vitrikho',
            name='rong_cm',
            field=models.DecimalField(decimal_places=2, default=40, max_digits=10, verbose_name='Rộng ô (cm)'),
        ),
        migrations.AddField(
            model_name='vitrikho',
            name='suc_chua_toi_da',
            field=models.IntegerField(default=20, verbose_name='Sức chứa tối đa'),
        ),
        migrations.AddField(
            model_name='vitrikho',
            name='tai_trong_toi_da_kg',
            field=models.DecimalField(decimal_places=3, default=30, max_digits=10, verbose_name='Tải trọng tối đa (kg)'),
        ),
        migrations.AddField(
            model_name='vitrikho',
            name='trang_thai',
            field=models.CharField(choices=[('hoat_dong', 'Hoạt động'), ('bao_tri', 'Bảo trì'), ('khoa', 'Khóa')], default='hoat_dong', max_length=20, verbose_name='Trạng thái'),
        ),
    ]
