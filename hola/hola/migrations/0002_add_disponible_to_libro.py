from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('hola', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='libro',
            name='disponible',
            field=models.BooleanField(default=True),
cls
]
