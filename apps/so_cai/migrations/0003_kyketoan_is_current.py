from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('so_cai', '0002_kyketoan'),
    ]

    operations = [
        migrations.AddField(
            model_name='kyketoan',
            name='is_current',
            field=models.BooleanField(default=False, verbose_name='Đang sử dụng'),
        ),
    ]