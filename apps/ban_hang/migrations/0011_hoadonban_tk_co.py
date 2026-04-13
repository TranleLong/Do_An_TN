from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ban_hang', '0010_congno_alert_and_due_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='hoadonban',
            name='tk_co',
            field=models.CharField(default='511', max_length=20, verbose_name='TK có đối ứng'),
        ),
    ]
