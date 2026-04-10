import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('danh_muc', '0006_remove_barcode'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaiKhoanKeToan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ma_tk', models.CharField(max_length=20, unique=True, verbose_name='Mã tài khoản')),
                ('ten_tk', models.CharField(max_length=255, verbose_name='Tên tài khoản')),
                ('trang_thai', models.BooleanField(default=True, verbose_name='Trạng thái')),
                ('tk_me', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tai_khoan_con', to='danh_muc.taikhoanketoan', verbose_name='Tài khoản mẹ')),
            ],
            options={
                'verbose_name': 'Tài khoản kế toán',
                'verbose_name_plural': 'Danh mục tài khoản kế toán',
                'db_table': 'danh_muc_taikhoanketoan',
                'ordering': ['ma_tk'],
            },
        ),
        migrations.AddField(
            model_name='hanghoa',
            name='nha_cung_cap',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='danh_muc.nhacungcap', verbose_name='Nhà cung cấp chính'),
        ),
    ]
