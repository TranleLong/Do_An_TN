from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ban_hang', '0005_donban_hoadonban_update'),
    ]

    operations = [
        migrations.AlterField(
            model_name='donban',
            name='trang_thai',
            field=models.CharField(
                choices=[
                    ('1', '1 - Lập chứng từ'),
                    ('2', '2 - Chờ duyệt'),
                    ('3', '3 - Duyệt'),
                    ('4', '4 - Treo'),
                ],
                default='1',
                max_length=20,
                verbose_name='Trạng thái',
            ),
        ),
    ]
