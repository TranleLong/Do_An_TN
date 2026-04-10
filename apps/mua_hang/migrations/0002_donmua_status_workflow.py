from django.db import migrations, models


def migrate_donmua_status_forward(apps, schema_editor):
    DonMua = apps.get_model('mua_hang', 'DonMua')
    mapping = {
        'nhap': '1',
        'cho_duyet': '1',
        'da_duyet': '2',
        'nhan_1_phan': '2',
        'hoan_thanh': '2',
        'huy': '3',
    }
    for old, new in mapping.items():
        DonMua.objects.filter(trang_thai=old).update(trang_thai=new)


def migrate_donmua_status_backward(apps, schema_editor):
    DonMua = apps.get_model('mua_hang', 'DonMua')
    mapping = {
        '1': 'nhap',
        '2': 'hoan_thanh',
        '3': 'huy',
    }
    for old, new in mapping.items():
        DonMua.objects.filter(trang_thai=old).update(trang_thai=new)


class Migration(migrations.Migration):

    dependencies = [
        ('mua_hang', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(migrate_donmua_status_forward, migrate_donmua_status_backward),
        migrations.AlterField(
            model_name='donmua',
            name='trang_thai',
            field=models.CharField(
                choices=[('1', '1 - Lập phiếu'), ('2', '2 - Nhập kho'), ('3', '3 - Sổ cái')],
                default='1',
                max_length=20,
                verbose_name='Trạng thái',
            ),
        ),
    ]
