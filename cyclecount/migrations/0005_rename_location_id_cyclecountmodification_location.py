# Generated by Django 4.1.4 on 2023-01-04 19:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cyclecount', '0004_countsession_completed_by_countsession_created_at_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='cyclecountmodification',
            old_name='location_id',
            new_name='location',
        ),
    ]
