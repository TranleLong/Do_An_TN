# Generated manually for UC1 and UC6 updates

import datetime

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('danh_muc', '0008_khachhang_la_khach_hang_khachhang_la_nha_cung_cap_and_more'),
        ('ban_hang', '0004_add_phieuthu_status_workflow'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='donban',
            name='trang_thai',
            field=models.CharField(
                choices=[('1', '1 - Lập phiếu'), ('3', '3 - Sổ cái')],
                default='1',
                max_length=20,
                verbose_name='Trạng thái',
            ),
        ),
        migrations.AddField(
            model_name='donban',
            name='dia_chi_kh',
            field=models.CharField(blank=True, max_length=300, verbose_name='Địa chỉ KH'),
        ),
        migrations.AddField(
            model_name='donban',
            name='ma_ngoai_te',
            field=models.CharField(default='VND', max_length=10, verbose_name='Mã ngoại tệ'),
        ),
        migrations.AddField(
            model_name='donban',
            name='ma_nv_ban_hang',
            field=models.CharField(blank=True, max_length=30, verbose_name='Mã nhân viên bán hàng'),
        ),
        migrations.AddField(
            model_name='donban',
            name='mst_kh',
            field=models.CharField(blank=True, max_length=20, verbose_name='MST KH'),
        ),
        migrations.AddField(
            model_name='donban',
            name='nguoi_mua_hang',
            field=models.CharField(blank=True, max_length=120, verbose_name='Người mua hàng'),
        ),
        migrations.AddField(
            model_name='donban',
            name='tong_so_luong',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=18, verbose_name='Tổng số lượng'),
        ),
        migrations.AddField(
            model_name='donban',
            name='ty_gia',
            field=models.DecimalField(decimal_places=4, default=1, max_digits=18, verbose_name='Tỷ giá'),
        ),
        migrations.AddField(
            model_name='donban_ct',
            name='ngay_giao',
            field=models.DateField(default=datetime.date.today, verbose_name='Ngày giao'),
        ),
        migrations.CreateModel(
            name='HoaDonBan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ma_giao_dich', models.CharField(choices=[('1', '1 - Hóa đơn kiêm phiếu xuất bán'), ('2', '2 - Hóa đơn từ phiếu xuất bán')], default='1', max_length=5, verbose_name='Mã giao dịch')),
                ('so_hoa_don', models.CharField(max_length=30, unique=True, verbose_name='Số hóa đơn')),
                ('ngay_lap', models.DateField(default=datetime.date.today, verbose_name='Ngày lập')),
                ('ngay_hach_toan', models.DateField(default=datetime.date.today, verbose_name='Ngày hạch toán')),
                ('ma_ngoai_te', models.CharField(choices=[('VND', 'VND'), ('USD', 'USD')], default='VND', max_length=10, verbose_name='Mã ngoại tệ')),
                ('ty_gia', models.DecimalField(decimal_places=4, default=1, max_digits=18, verbose_name='Tỷ giá')),
                ('ten_kh', models.CharField(blank=True, max_length=200, verbose_name='Tên khách')),
                ('dia_chi', models.CharField(blank=True, max_length=300, verbose_name='Địa chỉ')),
                ('so_dien_thoai', models.CharField(blank=True, max_length=15, verbose_name='Số điện thoại')),
                ('mst', models.CharField(blank=True, max_length=20, verbose_name='MST')),
                ('nguoi_mua_hang', models.CharField(blank=True, max_length=120, verbose_name='Người mua hàng')),
                ('tk_no', models.CharField(default='131', max_length=20, verbose_name='TK nợ')),
                ('dien_giai', models.TextField(blank=True, verbose_name='Diễn giải')),
                ('trang_thai', models.CharField(choices=[('1', '1 - Lập chứng từ'), ('3', '3 - Chuyển sổ cái')], default='1', max_length=20, verbose_name='Trạng thái')),
                ('tong_so_luong', models.DecimalField(decimal_places=2, default=0, max_digits=18, verbose_name='Tổng số lượng')),
                ('tong_chiet_khau', models.DecimalField(decimal_places=0, default=0, max_digits=18, verbose_name='Tổng chiết khấu')),
                ('tien_hang', models.DecimalField(decimal_places=0, default=0, max_digits=18, verbose_name='Tiền hàng')),
                ('tong_tien_thue', models.DecimalField(decimal_places=0, default=0, max_digits=18, verbose_name='Tổng tiền thuế')),
                ('tong_cong', models.DecimalField(decimal_places=0, default=0, max_digits=18, verbose_name='Tổng cộng')),
                ('ngay_tao', models.DateTimeField(auto_now_add=True)),
                ('don_ban', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='hoa_don_lien_ket', to='ban_hang.donban', verbose_name='Đơn bán liên kết')),
                ('khach_hang', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='danh_muc.khachhang', verbose_name='Khách hàng')),
                ('nguoi_tao', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='hoa_don_ban_tao', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Hóa đơn bán hàng',
                'verbose_name_plural': 'Hóa đơn bán hàng',
                'db_table': 'ban_hang_hoadonban',
                'ordering': ['-ngay_lap', '-id'],
            },
        ),
        migrations.CreateModel(
            name='HoaDonBan_CT',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('so_luong', models.DecimalField(decimal_places=2, default=0, max_digits=18, verbose_name='Số lượng')),
                ('gia_ban', models.DecimalField(decimal_places=0, default=0, max_digits=18, verbose_name='Giá bán')),
                ('ty_le_chiet_khau', models.DecimalField(decimal_places=2, default=0, max_digits=5, verbose_name='Tỷ lệ chiết khấu (%)')),
                ('thue_suat', models.DecimalField(decimal_places=2, default=10, max_digits=5, verbose_name='Thuế suất (%)')),
                ('tk_vat_tu', models.CharField(blank=True, max_length=20, verbose_name='TK vật tư')),
                ('tk_gia_von', models.CharField(blank=True, max_length=20, verbose_name='TK giá vốn')),
                ('tk_doanh_thu', models.CharField(blank=True, max_length=20, verbose_name='TK doanh thu')),
                ('tien_chiet_khau', models.DecimalField(decimal_places=0, default=0, max_digits=18)),
                ('tien_hang', models.DecimalField(decimal_places=0, default=0, max_digits=18)),
                ('tien_thue', models.DecimalField(decimal_places=0, default=0, max_digits=18)),
                ('thanh_tien', models.DecimalField(decimal_places=0, default=0, max_digits=18)),
                ('hang_hoa', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='danh_muc.hanghoa', verbose_name='Mã hàng')),
                ('hoa_don', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chi_tiet', to='ban_hang.hoadonban', verbose_name='Hóa đơn')),
                ('kho', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='danh_muc.kho', verbose_name='Mã kho')),
            ],
            options={
                'verbose_name': 'Chi tiết hóa đơn bán hàng',
                'db_table': 'ban_hang_hoadonban_ct',
            },
        ),
    ]
