from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lottery', '0008_notification_dismissed'),
    ]

    operations = [
        migrations.AddField(
            model_name='badgeaward',
            name='pet',
            field=models.ForeignKey(
                to='lottery.Pet',
                on_delete=models.CASCADE,
                related_name='badge_awards',
                default=1
            ),
        ),
        migrations.AlterUniqueTogether(
            name='badgeaward',
            unique_together={('user', 'pet', 'badge', 'round')},
        ),
    ]
