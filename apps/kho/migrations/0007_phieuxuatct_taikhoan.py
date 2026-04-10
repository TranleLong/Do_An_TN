from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kho', '0006_phieunhapct_taikhoan'),
    ]

    operations = [
        migrations.AddField(
            model_name='phieuxuat_ct',
            name='tk_no',
            field=models.CharField(blank=True, max_length=20, verbose_name='TK Nợ'),
        ),
        migrations.AddField(
            model_name='phieuxuat_ct',
            name='tk_co',
            field=models.CharField(blank=True, max_length=20, verbose_name='TK Có'),
        ),
    ]
