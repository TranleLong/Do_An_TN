import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ban_hang', '0009_hoadonban_ma_nv_ban_hang'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='donban',
            name='han_thanh_toan',
            field=models.DateField(blank=True, null=True, verbose_name='Hạn thanh toán'),
        ),
        migrations.CreateModel(
            name='CongNoCanhBaoConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bat_canh_bao_qua_han', models.BooleanField(default=True, verbose_name='Bật cảnh báo nợ quá hạn')),
                ('ngay_cap_nhat', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='cong_no_canh_bao_config', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Thiết lập cảnh báo công nợ',
                'verbose_name_plural': 'Thiết lập cảnh báo công nợ',
                'db_table': 'ban_hang_congno_canhbao_config',
            },
        ),
    ]
