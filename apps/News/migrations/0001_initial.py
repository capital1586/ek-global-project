# Generated by Django 5.1 on 2025-04-03 06:14

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='News',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('headline', models.CharField(max_length=255)),
                ('news_content', models.TextField()),
                ('news_link', models.URLField()),
                ('image_url', models.URLField()),
                ('news_date', models.DateTimeField()),
                ('tags', models.CharField(blank=True, max_length=255, null=True)),
                ('description', models.TextField()),
                ('categories', models.CharField(max_length=100)),
                ('news_id', models.IntegerField(unique=True)),
                ('author_name', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name_plural': 'News',
                'ordering': ['-news_date'],
            },
        ),
    ]
