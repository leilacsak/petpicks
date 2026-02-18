from django.db import models
from django.conf import settings

# Create your models here.


class LotteryRound(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        COMPLETED = "COMPLETED", "Completed"

    title = models.CharField(max_length=100)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    drawn_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title


class Pet(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pets",
    )
    name = models.CharField(max_length=50)
    breed = models.CharField(max_length=50, blank=True)
    age = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.owner})"


class Entry(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    pet = models.ForeignKey(
        Pet, on_delete=models.CASCADE, related_name="entries"
    )
    round = models.ForeignKey(
        LotteryRound,
        on_delete=models.CASCADE,
        related_name="entries",
    )
    photo = models.ImageField(upload_to="pet_entries/")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    is_winner = models.BooleanField(default=False)
    winner_rank = models.PositiveSmallIntegerField(null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["pet", "round"],
                name="unique_pet_per_round"
            ),
        ]

    def __str__(self):
        return f"{self.pet.name} - {self.round.title}"

    def get_rank_display(self):
        """Return ordinal rank (1st, 2nd, 3rd)"""
        if not self.winner_rank:
            return ""
        if self.winner_rank == 1:
            return "1st"
        elif self.winner_rank == 2:
            return "2nd"
        elif self.winner_rank == 3:
            return "3rd"
        else:
            return f"{self.winner_rank}th"


class Badge(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class BadgeAward(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="badge_awards",
    )
    badge = models.ForeignKey(
        Badge, on_delete=models.CASCADE, related_name="awards"
    )
    round = models.ForeignKey(
        LotteryRound,
        on_delete=models.CASCADE,
        related_name="badge_awards",
    )
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "badge", "round"],
                name="unique_badge_award_per_round"
            ),
        ]

    def __str__(self):
        return f"{self.user} - {self.badge} ({self.round})"


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    round = models.ForeignKey(
        LotteryRound,
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
    )
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "round"],
                name="unique_notification_per_round"
            ),
        ]

    def __str__(self):
        return f"To {self.user} @ {self.created_at:%Y-%m-%d %H:%M}"


class Comment(models.Model):
    entry = models.ForeignKey(
        Entry,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Comment by {self.author} on {self.entry}"
