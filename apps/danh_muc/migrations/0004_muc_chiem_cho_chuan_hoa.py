from django.db import migrations, models


def backfill_suc_chua(apps, schema_editor):
    ViTriKho = apps.get_model('danh_muc', 'ViTriKho')
    ViTriKho.objects.filter(suc_chua_toi_da__lt=50).update(suc_chua_toi_da=50)


class Migration(migrations.Migration):

    dependencies = [
        ('danh_muc', '0003_add_storage_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='hanghoa',
            name='muc_chiem_cho',
            field=models.PositiveSmallIntegerField(default=1, verbose_name='Mức chiếm chỗ (1-50)'),
        ),
        migrations.AlterField(
            model_name='vitrikho',
            name='suc_chua_toi_da',
            field=models.IntegerField(default=50, verbose_name='Sức chứa tối đa'),
        ),
        migrations.RunPython(backfill_suc_chua, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='hanghoa',
            constraint=models.CheckConstraint(condition=models.Q(('muc_chiem_cho__gte', 1), ('muc_chiem_cho__lte', 50)), name='hanghoa_muc_chiem_cho_1_50'),
        ),
        migrations.AddConstraint(
            model_name='vitrikho',
            constraint=models.CheckConstraint(condition=models.Q(('suc_chua_toi_da__gt', 0)), name='vitrikho_suc_chua_duong'),
        ),
    ]
