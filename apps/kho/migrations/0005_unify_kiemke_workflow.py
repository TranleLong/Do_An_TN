from django.db import migrations, models


def migrate_kiemke_status_forward(apps, schema_editor):
    KiemKe = apps.get_model('kho', 'KiemKe')
    mapping = {
        'dang_kiem': '1',
        'da_duyet': '2',
    }
    for old, new in mapping.items():
        KiemKe.objects.filter(trang_thai=old).update(trang_thai=new)


def migrate_kiemke_status_backward(apps, schema_editor):
    KiemKe = apps.get_model('kho', 'KiemKe')
    mapping = {
        '1': 'dang_kiem',
        '2': 'da_duyet',
        '3': 'da_duyet',
    }
    for old, new in mapping.items():
        KiemKe.objects.filter(trang_thai=old).update(trang_thai=new)


class Migration(migrations.Migration):

    dependencies = [
        ('kho', '0004_status_workflow'),
    ]

    operations = [
        migrations.RunPython(migrate_kiemke_status_forward, migrate_kiemke_status_backward),
        migrations.AlterField(
            model_name='kiemke',
            name='trang_thai',
            field=models.CharField(
                choices=[('1', '1 - Lập phiếu'), ('2', '2 - Nhập kho'), ('3', '3 - Sổ cái')],
                default='1',
                max_length=20,
            ),
        ),
    ]
