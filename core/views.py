from django.shortcuts import render
from lottery.models import LotteryRound, Entry

# Create your views here.


def home(request):
    # Get the latest completed round with winners
    latest_round = (
        LotteryRound.objects.filter(
            status=LotteryRound.Status.COMPLETED
        )
        .order_by("-drawn_at")
        .first()
    )
    
    recent_winners = []
    if latest_round:
        recent_winners = (
            Entry.objects.filter(
                round=latest_round,
                status=Entry.Status.APPROVED,
                is_winner=True
            )
            .select_related("pet", "pet__owner")
            .order_by("?")[:3]  # Get 3 random winners
        )
    
    return render(
        request, 
        "core/home.html",
        {
            "latest_round": latest_round,
            "recent_winners": recent_winners,
        }
    )


def about(request):
    return render(request, "core/about.html")
