# Generated by Django 3.1.7 on 2021-03-11 18:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0002_auto_20210311_1823'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fact',
            name='boolean_fact',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='quiz.booleanfact'),
        ),
        migrations.AlterField(
            model_name='fact',
            name='numeric_fact',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='quiz.numericfact'),
        ),
    ]
