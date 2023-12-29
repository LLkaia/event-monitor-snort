# Generated by Django 4.2.7 on 2023-12-28 19:33

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Performance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField()),
                ('module', models.CharField(max_length=128)),
                ('pegcounts', models.JSONField()),
            ],
        ),
    ]
