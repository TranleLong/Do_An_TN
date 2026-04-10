from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('danh_muc', '0004_muc_chiem_cho_chuan_hoa'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='hanghoa',
            name='gia_ban_le',
        ),
        migrations.RemoveField(
            model_name='hanghoa',
            name='gia_ban_buon',
        ),
    ]
