from django.shortcuts import render
from .models import LotteryRound

# Create your views here.


def round_list(request):
    rounds = LotteryRound.objects.filter(
        status=LotteryRound.Status.ACTIVE).order_by("-start_date")
    
    return render(request, "lottery/round_list.html", {"rounds": rounds})
