# Generated by Django 3.2.6 on 2021-10-14 10:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('favorites', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='favorite',
            old_name='folder_id',
            new_name='folder',
        ),
    ]