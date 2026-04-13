from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kho', '0008_tonkho_so_luong_loi_alter_phieunhap_loai_nhap_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='phieunhap',
            name='ngay_hach_toan',
            field=models.DateField(auto_now_add=False, default=None, null=True, verbose_name='Ngày hạch toán'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='phieunhap',
            name='ngay_lap',
            field=models.DateField(auto_now_add=False, default=None, null=True, verbose_name='Ngày lập'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='phieuxuat',
            name='ngay_hach_toan',
            field=models.DateField(auto_now_add=False, default=None, null=True, verbose_name='Ngày hạch toán'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='phieuxuat',
            name='ngay_lap',
            field=models.DateField(auto_now_add=False, default=None, null=True, verbose_name='Ngày lập'),
            preserve_default=False,
        ),
        migrations.RunSQL(
            sql=(
                "UPDATE kho_phieunhap SET ngay_lap = COALESCE(ngay_nhap, ngay_chung_tu), "
                "ngay_hach_toan = COALESCE(ngay_chung_tu, ngay_nhap);"
            ),
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql=(
                "UPDATE kho_phieuxuat SET ngay_lap = COALESCE(ngay_xuat, ngay_chung_tu), "
                "ngay_hach_toan = COALESCE(ngay_chung_tu, ngay_xuat);"
            ),
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.AlterField(
            model_name='phieunhap',
            name='ngay_hach_toan',
            field=models.DateField(verbose_name='Ngày hạch toán'),
        ),
        migrations.AlterField(
            model_name='phieunhap',
            name='ngay_lap',
            field=models.DateField(verbose_name='Ngày lập'),
        ),
        migrations.AlterField(
            model_name='phieuxuat',
            name='ngay_hach_toan',
            field=models.DateField(verbose_name='Ngày hạch toán'),
        ),
        migrations.AlterField(
            model_name='phieuxuat',
            name='ngay_lap',
            field=models.DateField(verbose_name='Ngày lập'),
        ),
    ]
