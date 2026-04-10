from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('danh_muc', '0009_nhomhang_bien_do_loi_nhuan'),
    ]

    operations = [
        migrations.AddField(
            model_name='khachhang',
            name='la_nhan_vien',
            field=models.BooleanField(default=False, verbose_name='Nhân viên bán hàng'),
        ),
    ]
