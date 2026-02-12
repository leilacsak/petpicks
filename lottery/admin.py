from django.contrib import admin
from .models import LotteryRound, Pet, Entry, Badge, BadgeAward, Notification

# Register your models here.
admin.site.register(LotteryRound)
admin.site.register(Pet)
admin.site.register(Entry)
admin.site.register(Badge)
admin.site.register(BadgeAward)
admin.site.register(Notification)
