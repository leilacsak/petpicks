from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Prefetch
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .models import (
    LotteryRound,
    Pet,
    Entry,
    Badge,
    BadgeAward,
    Notification,
    Comment,
)
from .forms import EntryCreateForm, CommentForm, LotteryRoundForm
from django.contrib.admin.views.decorators import staff_member_required
import random
from django.utils import timezone
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse


def round_list(request):
    form = None
    if request.user.is_staff:
        if request.method == "POST":
            form = LotteryRoundForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Lottery round created successfully!")
                return redirect("round_list")
        else:
            form = LotteryRoundForm()
    
    rounds = LotteryRound.objects.filter(
        status=LotteryRound.Status.ACTIVE).order_by("-start_date")
    
    return render(request, "lottery/round_list.html", {
        "rounds": rounds,
        "form": form,
    })


@login_required
def enter_round(request, round_id):
    round_obj = get_object_or_404(
        LotteryRound,
        id=round_id,
        status=LotteryRound.Status.ACTIVE
    )
    
    # Check if user has already submitted to this round
    if Entry.objects.filter(pet__owner=request.user, round=round_obj).exists():
        messages.error(
            request,
            "You have already submitted an entry to this round. "
            "Only one entry per round is allowed."
        )
        return redirect("round_list")
    
    if request.method == "POST":
        form = EntryCreateForm(request.POST, request.FILES)
        if form.is_valid():
            pet, created = Pet.objects.get_or_create(
                owner=request.user,
                name=form.cleaned_data["pet_name"],
                defaults={
                    "breed": form.cleaned_data["pet_breed"],
                    "age": form.cleaned_data["pet_age"],
                }
            )
            
            # Update breed and age if pet already exists
            if not created:
                pet.breed = form.cleaned_data["pet_breed"]
                pet.age = form.cleaned_data["pet_age"]
                pet.save(update_fields=["breed", "age"])
            
            Entry.objects.create(
                round=round_obj,
                pet=pet,
                photo=form.cleaned_data["photo"],
            )
            messages.success(request, "Entry submitted successfully!")
            return redirect("profile")
    
    else:
        form = EntryCreateForm()
    
    return render(
        request,
        "lottery/enter_round.html",
        {"form": form, "round": round_obj}
    )


@login_required
def profile(request):
    entries = (
        Entry.objects.filter(pet__owner=request.user)
        .select_related("pet", "round")
        .order_by("-submitted_at")
    )

    badges = (
        BadgeAward.objects.filter(user=request.user)
        .select_related("badge", "round")
        .order_by("-awarded_at")
    )

    notifications = (
        Notification.objects.filter(user=request.user)
        .order_by("-created_at")
    )

    return render(
        request,
        "lottery/profile.html",
        {
            "entries": entries,
            "badges": badges,
            "notifications": notifications,
        },
    )
    

@staff_member_required
def moderation_queue(request):
    pending_entries = Entry.objects.filter(
        status=Entry.Status.PENDING
    ).select_related("pet", "round")
    return render(
        request,
        "lottery/moderation_queue.html",
        {"entries": pending_entries}
    )


@staff_member_required
def approve_entry(request, entry_id):
    entry = get_object_or_404(Entry, id=entry_id)
    entry.status = Entry.Status.APPROVED
    entry.save()
    return redirect("moderation_queue")


@staff_member_required
def reject_entry(request, entry_id):
    entry = get_object_or_404(Entry, id=entry_id)
    entry.status = Entry.Status.REJECTED
    entry.save()
    return redirect("moderation_queue")


@staff_member_required
def run_draw(request, round_id):
    round_obj = get_object_or_404(LotteryRound, id=round_id)

    # Lock: cannot draw twice
    if round_obj.drawn_at is not None:
        messages.warning(request, "This round has already been drawn.")
        return redirect("round_list")

    eligible = list(
        Entry.objects.filter(
            round=round_obj,
            status=Entry.Status.APPROVED
        )
    )

    if not eligible:
        messages.error(
            request, "No approved entries available for this round."
        )
        return redirect("round_list")

    winner_count = 3 if len(eligible) >= 3 else len(eligible)
    winners = random.sample(eligible, winner_count)
    
    winner_badge, _ = Badge.objects.get_or_create(
        name="Winner",
        defaults={
            "description": "Awarded for winning a PetPicks lottery round."
        }
    )

    for index, entry in enumerate(winners, start=1):
        entry.is_winner = True
        entry.winner_rank = index
        entry.save(update_fields=["is_winner", "winner_rank"])
        
        BadgeAward.objects.get_or_create(
            user=entry.pet.owner,
            badge=winner_badge,
            round=round_obj,
        )

    winner_ids = {e.id for e in winners}

    all_entries = Entry.objects.filter(
        round=round_obj,
        status=Entry.Status.APPROVED
    ).select_related("pet__owner", "pet")

    for entry in all_entries:
        if entry.id in winner_ids:
            msg = (
                f"Congratulations! '{entry.pet.name}' won the "
                f"'{round_obj.title}' lottery! 🏆"
            )
        else:
            msg = (
                f"Thanks for entering '{round_obj.title}'. "
                "Not selected this time.Try again next time! 😊"
            )

        Notification.objects.get_or_create(
            user=entry.pet.owner,
            round=round_obj,
            defaults={"message": msg}
        )

    round_obj.drawn_at = timezone.now()
    round_obj.status = LotteryRound.Status.COMPLETED
    round_obj.save()

    messages.success(
        request, f"Draw complete! Selected {winner_count} winner(s)."
    )
    return redirect("round_list")


def results(request):
    rounds = LotteryRound.objects.filter(
        status=LotteryRound.Status.COMPLETED
    ).prefetch_related(
        Prefetch(
            "entries",
            queryset=Entry.objects.select_related("pet").order_by(
                "winner_rank",
                "id",
            ),
        ),
    ).order_by("-drawn_at")
    return render(
        request,
        "lottery/results_list.html",
        {"rounds": rounds},
    )


@login_required
def entry_detail(request, entry_id):
    entry = get_object_or_404(
        Entry.objects.select_related("pet", "round"),
        id=entry_id
    )

    # Access control
    if entry.pet.owner != request.user:
        return HttpResponseForbidden(
            "You do not have permission to view this entry."
        )

    return render(
        request,
        "lottery/entry_detail.html",
        {"entry": entry}
    )


@login_required
def comment_create(request, entry_id):
    entry = get_object_or_404(
        Entry.objects.select_related("round"),
        id=entry_id,
        is_winner=True,
    )

    if entry.round.status != LotteryRound.Status.COMPLETED:
        return HttpResponseForbidden(
            "Comments are only allowed on completed rounds."
        )

    if request.method != "POST":
        return redirect("results_list")

    form = CommentForm(request.POST)
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    
    if form.is_valid():
        comment = Comment.objects.create(
            entry=entry,
            author=request.user,
            text=form.cleaned_data["text"],
        )
        
        if is_ajax:
            return JsonResponse({
                "success": True,
                "comment": {
                    "id": comment.id,
                    "author": request.user.username,
                    "text": comment.text,
                    "created_at": comment.created_at.strftime("%b %d, %Y at %I:%M %p"),
                    "edit_url": reverse("comment_edit", args=[comment.id]),
                    "delete_url": reverse("comment_delete", args=[comment.id]),
                }
            })
    
    if is_ajax:
        return JsonResponse({
            "success": False,
            "errors": form.errors,
        }, status=400)

    next_url = request.POST.get("next") or "results_list"
    return redirect(next_url)


@login_required
def comment_edit(request, comment_id):
    comment = get_object_or_404(
        Comment.objects.select_related("entry"),
        id=comment_id,
    )

    if comment.author != request.user:
        return HttpResponseForbidden(
            "You do not have permission to edit this comment."
        )

    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if request.method != "POST":
        return redirect("results_list")

    form = CommentForm(request.POST, instance=comment)
    if form.is_valid():
        form.save(update_fields=["text"])
        
        if is_ajax:
            return JsonResponse({
                "success": True,
                "comment": {
                    "id": comment.id,
                    "text": comment.text,
                }
            })

    if is_ajax:
        return JsonResponse({
            "success": False,
            "errors": form.errors,
        }, status=400)

    next_url = request.POST.get("next") or "results_list"
    return redirect(next_url)


@login_required
def comment_delete(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if comment.author != request.user:
        return HttpResponseForbidden(
            "You do not have permission to delete this comment."
        )

    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if request.method == "POST":
        comment.delete()
        
        if is_ajax:
            return JsonResponse({
                "success": True,
            })

    if is_ajax:
        return JsonResponse({
            "success": False,
            "error": "Invalid request method",
        }, status=400)

    next_url = request.POST.get("next") or "results_list"
    return redirect(next_url)