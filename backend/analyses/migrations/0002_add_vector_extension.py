from django.contrib.postgres.operations import CreateExtension
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('analyses', '0001_initial'),
    ]

    operations = [
        CreateExtension('vector'),
    ]
