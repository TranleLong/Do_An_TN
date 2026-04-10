from django.db import migrations, models


def migrate_status_forward(apps, schema_editor):
    DonBan = apps.get_model('ban_hang', 'DonBan')
    mapping = {
        'nhap': '1',
        'da_xac_nhan': '2',
        'huy': '3',
    }
    for old, new in mapping.items():
        DonBan.objects.filter(trang_thai=old).update(trang_thai=new)


def migrate_status_backward(apps, schema_editor):
    DonBan = apps.get_model('ban_hang', 'DonBan')
    mapping = {
        '1': 'nhap',
        '2': 'da_xac_nhan',
        '3': 'huy',
    }
    for old, new in mapping.items():
        DonBan.objects.filter(trang_thai=old).update(trang_thai=new)


class Migration(migrations.Migration):

    dependencies = [
        ('ban_hang', '0002_add_ngay_chung_tu'),
    ]

    operations = [
        migrations.RunPython(migrate_status_forward, migrate_status_backward),
        migrations.AlterField(
            model_name='donban',
            name='trang_thai',
            field=models.CharField(
                choices=[('1', '1 - Lập phiếu'), ('2', '2 - Xuất kho'), ('3', '3 - Sổ cái')],
                default='1',
                max_length=20,
                verbose_name='Trạng thái',
            ),
        ),
    ]
