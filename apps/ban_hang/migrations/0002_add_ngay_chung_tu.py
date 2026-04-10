import datetime

from django.db import migrations, models


def _copy_ngay_chung_tu(apps, schema_editor):
    DonBan = apps.get_model('ban_hang', 'DonBan')

    for don in DonBan.objects.all().only('id', 'ngay_ban', 'ngay_chung_tu'):
        don.ngay_chung_tu = don.ngay_ban
        don.save(update_fields=['ngay_chung_tu'])


class Migration(migrations.Migration):

    dependencies = [
        ('ban_hang', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='donban',
            name='ngay_chung_tu',
            field=models.DateField(blank=True, null=True, verbose_name='Ngày chứng từ'),
        ),
        migrations.RunPython(_copy_ngay_chung_tu, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='donban',
            name='ngay_chung_tu',
            field=models.DateField(default=datetime.date.today, verbose_name='Ngày chứng từ'),
        ),
        migrations.AlterModelOptions(
            name='donban',
            options={'ordering': ['-ngay_chung_tu', '-ngay_ban', '-ngay_tao'], 'verbose_name': 'Đơn bán hàng', 'verbose_name_plural': 'Đơn bán hàng'},
        ),
    ]
