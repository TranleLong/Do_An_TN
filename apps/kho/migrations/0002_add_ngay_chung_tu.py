import datetime

from django.db import migrations, models


def _copy_ngay_chung_tu(apps, schema_editor):
    PhieuNhap = apps.get_model('kho', 'PhieuNhap')
    PhieuXuat = apps.get_model('kho', 'PhieuXuat')

    for pn in PhieuNhap.objects.all().only('id', 'ngay_nhap', 'ngay_chung_tu'):
        pn.ngay_chung_tu = pn.ngay_nhap
        pn.save(update_fields=['ngay_chung_tu'])

    for px in PhieuXuat.objects.all().only('id', 'ngay_xuat', 'ngay_chung_tu'):
        px.ngay_chung_tu = px.ngay_xuat
        px.save(update_fields=['ngay_chung_tu'])


class Migration(migrations.Migration):

    dependencies = [
        ('kho', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='phieunhap',
            name='ngay_chung_tu',
            field=models.DateField(blank=True, null=True, verbose_name='Ngày chứng từ'),
        ),
        migrations.AddField(
            model_name='phieuxuat',
            name='ngay_chung_tu',
            field=models.DateField(blank=True, null=True, verbose_name='Ngày chứng từ'),
        ),
        migrations.RunPython(_copy_ngay_chung_tu, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='phieunhap',
            name='ngay_chung_tu',
            field=models.DateField(default=datetime.date.today, verbose_name='Ngày chứng từ'),
        ),
        migrations.AlterField(
            model_name='phieuxuat',
            name='ngay_chung_tu',
            field=models.DateField(default=datetime.date.today, verbose_name='Ngày chứng từ'),
        ),
        migrations.AlterModelOptions(
            name='phieunhap',
            options={'ordering': ['-ngay_chung_tu', '-ngay_nhap', '-ngay_tao'], 'verbose_name': 'Phiếu nhập kho', 'verbose_name_plural': 'Phiếu nhập kho'},
        ),
        migrations.AlterModelOptions(
            name='phieuxuat',
            options={'ordering': ['-ngay_chung_tu', '-ngay_xuat', '-ngay_tao'], 'verbose_name': 'Phiếu xuất kho'},
        ),
    ]
