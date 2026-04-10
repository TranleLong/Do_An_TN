from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ban_hang', '0003_status_workflow'),
    ]

    operations = [
        migrations.AddField(
            model_name='phieuthu',
            name='trang_thai',
            field=models.CharField(
                choices=[('1', '1 - Lập phiếu'), ('2', '2 - Ghi nhận nghiệp vụ'), ('3', '3 - Sổ cái')],
                default='1',
                max_length=20,
                verbose_name='Trạng thái',
            ),
        ),
    ]
