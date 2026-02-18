from django.shortcuts import render
from django.core.paginator import Paginator
from lottery.models import LotteryRound, Entry
from lottery.forms import CommentForm

COMMENTS_PER_PAGE = 3

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
            .prefetch_related("comments__author")
            .order_by("?")[:3]  # Get 3 random winners
        )

        for entry in recent_winners:
            page_param = f"comments_{entry.id}"
            page_number = request.GET.get(page_param, 1)
            comments = list(entry.comments.all())
            paginator = Paginator(comments, COMMENTS_PER_PAGE)
            entry.comment_page = paginator.get_page(page_number)

    return render(
        request,
        "core/home.html",
        {
            "latest_round": latest_round,
            "recent_winners": recent_winners,
            "comment_form": CommentForm(),
        }
    )


def about(request):
    return render(request, "core/about.html")
