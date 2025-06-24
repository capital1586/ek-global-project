# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('News', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='news',
            name='source_domain',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ] 