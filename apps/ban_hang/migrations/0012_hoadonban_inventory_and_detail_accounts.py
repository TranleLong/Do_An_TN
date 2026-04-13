from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ban_hang', '0011_hoadonban_tk_co'),
    ]

    operations = [
        migrations.AddField(
            model_name='hoadonban_ct',
            name='tk_thue',
            field=models.CharField(blank=True, max_length=20, verbose_name='TK thuế'),
        ),
    ]
