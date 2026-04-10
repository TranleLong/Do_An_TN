from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('danh_muc', '0005_remove_gia_ban_fields'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='hanghoa',
            name='barcode',
        ),
    ]
