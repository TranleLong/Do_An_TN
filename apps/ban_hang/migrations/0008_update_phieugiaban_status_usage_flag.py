from django.db import migrations, models


def migrate_status_to_usage_flag(apps, schema_editor):
    PhieuGiaBan = apps.get_model('ban_hang', 'PhieuGiaBan')
    PhieuGiaBan.objects.filter(trang_thai_duyet='cho_duyet').update(trang_thai_duyet='1')
    PhieuGiaBan.objects.filter(trang_thai_duyet='da_duyet').update(trang_thai_duyet='1')
    PhieuGiaBan.objects.filter(trang_thai_duyet='tu_choi').update(trang_thai_duyet='0')


def reverse_status_to_legacy(apps, schema_editor):
    PhieuGiaBan = apps.get_model('ban_hang', 'PhieuGiaBan')
    PhieuGiaBan.objects.filter(trang_thai_duyet='1').update(trang_thai_duyet='da_duyet')
    PhieuGiaBan.objects.filter(trang_thai_duyet='0').update(trang_thai_duyet='tu_choi')


class Migration(migrations.Migration):

    dependencies = [
        ('ban_hang', '0007_alter_donban_table_alter_donban_ct_table_and_more'),
    ]

    operations = [
        migrations.RunPython(migrate_status_to_usage_flag, reverse_status_to_legacy),
        migrations.AlterField(
            model_name='phieugiaban',
            name='trang_thai_duyet',
            field=models.CharField(
                choices=[('0', 'Không sử dụng'), ('1', 'Sử dụng')],
                default='1',
                max_length=20,
                verbose_name='Trạng thái',
            ),
        ),
    ]
