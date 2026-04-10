from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kho', '0005_unify_kiemke_workflow'),
    ]

    operations = [
        migrations.AddField(
            model_name='phieunhap_ct',
            name='tk_co',
            field=models.CharField(blank=True, max_length=20, verbose_name='TK Có'),
        ),
        migrations.AddField(
            model_name='phieunhap_ct',
            name='tk_no',
            field=models.CharField(blank=True, max_length=20, verbose_name='TK Nợ'),
        ),
    ]
