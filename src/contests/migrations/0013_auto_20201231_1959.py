# Generated by Django 3.1.4 on 2020-12-31 16:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contests', '0012_solution_log'),
    ]

    operations = [
        migrations.AlterField(
            model_name='problem',
            name='input_data',
            field=models.TextField(blank=True, help_text='Входные данные'),
        ),
    ]
