from django.shortcuts import render
from django.core.paginator import Paginator
from lottery.models import LotteryRound, Entry
from lottery.forms import CommentForm


COMMENTS_PER_PAGE = 3


def home(request):
    # Get the latest completed round that has at least 1 winner
    latest_round = (
        LotteryRound.objects.filter(
            status=LotteryRound.Status.COMPLETED,
            entries__is_winner=True,
        )
        .distinct()
        .order_by("-drawn_at")
        .first()
    )

    recent_winners = []
    if latest_round:
        recent_winners = (
            Entry.objects.filter(
                round=latest_round,
                is_winner=True
            )
            .select_related("pet", "pet__owner")
            .prefetch_related("comments__author")
            .order_by("winner_rank", "id")[:3]
        )

        for entry in recent_winners:
            page_param = f"comments_{entry.id}"
            page_number = request.GET.get(page_param, 1)
            comments = list(entry.comments.all().order_by("-created_at"))
            paginator = Paginator(comments, COMMENTS_PER_PAGE)
            entry.comment_page = paginator.get_page(page_number)

    comment_forms = {}
    for entry in recent_winners:
        comment_forms[entry.id] = CommentForm(prefix=f"entry_{entry.id}")

    return render(
        request,
        "core/home.html",
        {
            "latest_round": latest_round,
            "recent_winners": recent_winners,
            "comment_forms": comment_forms,
        }
    )


def about(request):
    return render(request, "core/about.html")
