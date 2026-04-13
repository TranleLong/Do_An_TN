from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ban_hang', '0008_update_phieugiaban_status_usage_flag'),
    ]

    operations = [
        migrations.AddField(
            model_name='hoadonban',
            name='ma_nv_ban_hang',
            field=models.CharField(blank=True, max_length=30, verbose_name='Mã nhân viên bán hàng'),
        ),
    ]
