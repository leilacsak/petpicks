from django.contrib import admin
from .models import LotteryRound, Pet, Entry, Badge, BadgeAward, Notification, Comment


@admin.register(LotteryRound)
class LotteryRoundAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'start_date', 'end_date', 'drawn_at']
    list_filter = ['status', 'start_date']
    search_fields = ['title']


@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'breed', 'age']
    list_filter = ['breed']
    search_fields = ['name', 'owner__username']


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = ['pet', 'round', 'status', 'is_winner', 'winner_rank', 'submitted_at']
    list_filter = ['status', 'is_winner', 'round', 'submitted_at']
    search_fields = ['pet__name', 'pet__owner__username']


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


@admin.register(BadgeAward)
class BadgeAwardAdmin(admin.ModelAdmin):
    list_display = ['user', 'badge', 'round', 'awarded_at']
    list_filter = ['badge', 'round', 'awarded_at']
    search_fields = ['user__username']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'round', 'message', 'created_at']
    list_filter = ['round', 'created_at']
    search_fields = ['user__username', 'message']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'entry', 'created_at']
    list_filter = ['created_at']
    search_fields = ['author__username', 'text']
