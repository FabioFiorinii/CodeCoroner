from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('repositories', '0003_repository_groups'),
    ]

    operations = [
        migrations.AddField(
            model_name='repository',
            name='auto_pull',
            field=models.BooleanField(default=False),
        ),
    ]
