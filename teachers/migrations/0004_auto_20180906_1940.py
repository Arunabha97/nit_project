# Generated by Django 2.1.1 on 2018-09-06 14:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('teachers', '0003_auto_20180906_1924'),
    ]

    operations = [
        migrations.AlterField(
            model_name='teacher',
            name='phone_no_1',
            field=models.IntegerField(default=0, max_length=12),
        ),
        migrations.AlterField(
            model_name='teacher',
            name='phone_no_2',
            field=models.IntegerField(blank=True, max_length=12, null=True),
        ),
    ]