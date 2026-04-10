from django.db import migrations, models


def migrate_status_forward(apps, schema_editor):
    PhieuNhap = apps.get_model('kho', 'PhieuNhap')
    PhieuXuat = apps.get_model('kho', 'PhieuXuat')
    mapping_nhap = {
        'nhap': '1',
        'da_nhap': '2',
        'huy': '3',
    }
    mapping_xuat = {
        'nhap': '1',
        'da_xuat': '2',
        'huy': '3',
    }
    for old, new in mapping_nhap.items():
        PhieuNhap.objects.filter(trang_thai=old).update(trang_thai=new)
    for old, new in mapping_xuat.items():
        PhieuXuat.objects.filter(trang_thai=old).update(trang_thai=new)


def migrate_status_backward(apps, schema_editor):
    PhieuNhap = apps.get_model('kho', 'PhieuNhap')
    PhieuXuat = apps.get_model('kho', 'PhieuXuat')
    mapping_nhap = {
        '1': 'nhap',
        '2': 'da_nhap',
        '3': 'huy',
    }
    mapping_xuat = {
        '1': 'nhap',
        '2': 'da_xuat',
        '3': 'huy',
    }
    for old, new in mapping_nhap.items():
        PhieuNhap.objects.filter(trang_thai=old).update(trang_thai=new)
    for old, new in mapping_xuat.items():
        PhieuXuat.objects.filter(trang_thai=old).update(trang_thai=new)


class Migration(migrations.Migration):

    dependencies = [
        ('kho', '0003_tonkhovitri'),
    ]

    operations = [
        migrations.RunPython(migrate_status_forward, migrate_status_backward),
        migrations.AlterField(
            model_name='phieunhap',
            name='trang_thai',
            field=models.CharField(
                choices=[('1', '1 - Lập phiếu'), ('2', '2 - Nhập kho'), ('3', '3 - Sổ cái')],
                default='1',
                max_length=20,
                verbose_name='Trạng thái',
            ),
        ),
        migrations.AlterField(
            model_name='phieuxuat',
            name='trang_thai',
            field=models.CharField(
                choices=[('1', '1 - Lập phiếu'), ('2', '2 - Xuất kho'), ('3', '3 - Sổ cái')],
                default='1',
                max_length=20,
                verbose_name='Trạng thái',
            ),
        ),
    ]
