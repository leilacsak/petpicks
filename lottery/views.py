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
    """
    Display list of active lottery rounds and optionally create new round.

    GET: Shows all active rounds
    POST: Creates new lottery round (staff members only )

    Context:
    rounds: QuerySet of active LotteryRound objects ordered by start date
    form: LotteryRoundForm for creating rounds (None if not staff)
    """
    form = None

    if request.method == "POST" and not request.user.is_staff:
        return HttpResponseForbidden("Staff only.")

    if request.user.is_staff:
        form = LotteryRoundForm(request.POST or None)
        if request.method == "POST" and form.is_valid():
            form.save()
            messages.success(
                request, "Lottery round created successfully!"
            )
            return redirect("round_list")

    now = timezone.now()
    rounds = LotteryRound.objects.filter(
        status=LotteryRound.Status.ACTIVE,
        start_date__lte=now,
        end_date__gte=now
        ).order_by("-start_date")

    return render(request, "lottery/round_list.html", {
        "rounds": rounds,
        "form": form,
    })


@login_required
def enter_round(request, round_id):
    """
    Submit a pet entry to an active lottery round.

    Users can only submit one entry per round. Creates or updates Pet record
    and creates Entry with photo. Form collects pet name, breed, age.

    Args:
    round_id: Primary key of the LotteryRound to enter

    Context:
        form: EntryCreateForm for pet submission
        round: LotteryRound object
    """
    round_obj = get_object_or_404(
        LotteryRound,
        id=round_id,
        status=LotteryRound.Status.ACTIVE
    )
    
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
                
            # Check pet + round entry uniqueness
            if Entry.objects.filter(pet=pet, round=round_obj).exists():
                messages.error(
                    request,
                    "This pet has already been entered in this round. "
                    "If you have multiple pets, try entering a different pet, "
                    "otherwise please wait for the next round to enter again."
                )
                return redirect("round_list")

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
    """
    Display user's profile with entry history, earned badges, and
    notifications.

    Shows paginated list of user's lottery entries, badges earned by round,
    and recent notifications.

    Context:
        entries: User's submitted entries with related pet and round data
        badges: User's earned badges grouped/sorted by round
        notifications: User's recent notifications ordered by date
    """
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
    """
    Display pending entries awaiting staff approval/rejection.

    Staff-only view for content moderation. Shows entries awaiting review
    with pet and round information.

    Context:
        entries: QuerySet of pending Entry objects (status=PENDING)
    """
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
    """
    Approve a pending entry for inclusion in the lottery draw.

    Staff-only. Changes entry status from PENDING to APPROVED.
    Redirects back to moderation queue after approval.

    Args:
        entry_id: Primary key of the Entry to approve
    """
    entry = get_object_or_404(Entry, id=entry_id)
    entry.status = Entry.Status.APPROVED
    entry.save()
    return redirect("moderation_queue")


@staff_member_required
def reject_entry(request, entry_id):
    """
    Reject a pending entry, excluding it from the lottery draw.

    Staff-only. Changes entry status from PENDING to REJECTED.
    Redirects back to moderation queue after rejection.

    Args:
        entry_id: Primary key of the Entry to reject
    """
    entry = get_object_or_404(Entry, id=entry_id)
    entry.status = Entry.Status.REJECTED
    entry.save()
    return redirect("moderation_queue")


@staff_member_required
def run_draw(request, round_id):
    """
    Execute the lottery draw for a completed round.

    Selects up to 3 random winners from approved entries, creates notifications
    for winners and other participants, awards "Winner" badges, marks round
    as completed. Only runs once per round.

    Args:
        round_id: Primary key of the LotteryRound to draw
    """
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
    """
    Display completed lottery rounds with winner rankings.

    Shows all finished rounds with entries sorted
    by winner rank (1st, 2nd, 3rd).
    Winning entries display comment section if user is authenticated.

    Context:
        rounds: QuerySet of completed LotteryRound objects with related entries
    """
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
def comment_create(request, entry_id):
    """
    Create a comment on a winning entry (supports AJAX and traditional POST).

    Only allows comments on entries in completed rounds. POST request creates
    and saves comment.

    Returns (AJAX):
        - success: bool
        - comment: {id, author, text, created_at, edit_url,
          delete_url} on success
        - errors: form validation errors on failure

    Args:
       entry_id: Primary key of the winning Entry to comment on
    """
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
            created_at_str = comment.created_at.strftime(
                "%b %d, %Y at %I:%M %p"
            )
            return JsonResponse({
                "success": True,
                "comment": {
                    "id": comment.id,
                    "author": request.user.username,
                    "text": comment.text,
                    "created_at": created_at_str,
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
    """
    Update a comment's text (supports AJAX and traditional POST).

    Author-only access. POST request saves updated comment text.

    Returns (AJAX):
        - success: bool
        - comment: {id, text} on success
        - errors: form validation errors on failure

    Args:
        comment_id: Primary key of the Comment to edit
    """
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
        updated_comment = form.save()

        if is_ajax:
            return JsonResponse({
                "success": True,
                "comment": {
                    "id": updated_comment.id,
                    "text": updated_comment.text,
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
    """
    Delete a comment (supports AJAX and traditional POST).

    Author-only access. POST request deletes the comment.

    Returns (AJAX):
        - success: bool
        - error: error message on failure

    Args:
        comment_id: Primary key of the Comment to delete
    """
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
