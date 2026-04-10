import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('danh_muc', '0003_add_storage_fields'),
        ('kho', '0002_add_ngay_chung_tu'),
    ]

    operations = [
        migrations.CreateModel(
            name='TonKhoViTri',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('so_luong', models.IntegerField(default=0, verbose_name='Số lượng tại vị trí')),
                ('ngay_cap_nhat', models.DateTimeField(auto_now=True)),
                ('hang_hoa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='danh_muc.hanghoa', verbose_name='Hàng hóa')),
                ('kho', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='danh_muc.kho', verbose_name='Kho')),
                ('vi_tri', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='danh_muc.vitrikho', verbose_name='Vị trí kho')),
            ],
            options={
                'db_table': 'kho_tonkho_vitri',
                'verbose_name': 'Tồn kho theo vị trí',
                'unique_together': {('hang_hoa', 'vi_tri')},
            },
        ),
    ]
