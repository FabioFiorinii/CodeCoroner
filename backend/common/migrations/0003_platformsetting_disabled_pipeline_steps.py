from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0002_alter_platformsetting_model_tier'),
    ]

    operations = [
        migrations.AddField(
            model_name='platformsetting',
            name='disabled_pipeline_steps',
            field=models.JSONField(blank=True, default=list),
        ),
    ]