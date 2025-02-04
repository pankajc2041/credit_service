# Generated by Django 5.1.5 on 2025-02-03 19:05

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('email', models.EmailField(max_length=254)),
                ('annual_income', models.FloatField()),
                ('aadhar_id', models.CharField(max_length=255, unique=True)),
                ('credit_score', models.IntegerField(blank=True, null=True)),
                ('user_id', models.UUIDField(default=uuid.uuid4, unique=True)),
            ],
        ),
    ]
