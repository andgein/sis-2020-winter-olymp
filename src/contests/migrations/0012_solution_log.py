# Generated by Django 3.1.4 on 2020-12-31 15:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contests', '0011_sabotagetasktemplate'),
    ]

    operations = [
        migrations.AddField(
            model_name='solution',
            name='log',
            field=models.TextField(blank=True, help_text='Лог проверки'),
        ),
    ]