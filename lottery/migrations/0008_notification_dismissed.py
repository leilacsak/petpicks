from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lottery', '0007_pet_uniq_pet_per_owner_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='dismissed',
            field=models.BooleanField(default=False),
        ),
    ]
