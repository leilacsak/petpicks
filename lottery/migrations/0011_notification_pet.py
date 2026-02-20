#  Add pet field to Notification and update unique constraint
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            'lottery',
            '0010_remove_badgeaward_unique_badge_award_per_round_and_more'
        ),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='pet',
            field=models.ForeignKey(
                to='lottery.Pet',
                on_delete=models.CASCADE,
                related_name='notifications',
                null=True,
                blank=True
            ),
        ),
        migrations.AlterUniqueTogether(
            name='notification',
            unique_together={('user', 'pet', 'round')},
        ),
    ]
