# Generated by Django 3.2.22 on 2023-10-13 22:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vote', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='showreel',
            name='status',
            field=models.CharField(choices=[('OPEN', 'Open to submissions'), ('VOTE', 'Open to votes'), ('CLOSED', 'Closed')], default='CLOSED', max_length=6),
        ),
    ]
