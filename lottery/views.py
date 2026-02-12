from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from .models import LotteryRound, Pet, Entry
from .forms import EntryCreateForm
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404
from django.http import HttpResponseForbidden


# Create your views here.


def round_list(request):
    rounds = LotteryRound.objects.filter(
        status=LotteryRound.Status.ACTIVE).order_by("-start_date")
    
    return render(request, "lottery/round_list.html", {"rounds": rounds})


@login_required
def enter_round(request, round_id):
    round_obj = get_object_or_404(
        LotteryRound,
        id=round_id,
        status=LotteryRound.Status.ACTIVE
    )
    
    if request.method == "POST":
        form = EntryCreateForm(request.POST, request.FILES)
        if form.is_valid():
            pet = Pet.objects.create(
                owner=request.user,
                name=form.cleaned_data["pet_name"],
                breed=form.cleaned_data["pet_breed"],
                age=form.cleaned_data["pet_age"],
            )
            
            Entry.objects.create(
                round=round_obj,
                pet=pet,
                photo=form.cleaned_data["photo"],
            )
            return redirect("my_entries")
    
    else:
        form = EntryCreateForm()
    
    return render(
        request,
        "lottery/enter_round.html",
        {"form": form, "round": round_obj}
    )


@login_required
def my_entries(request):
    entries = Entry.objects.filter(
        pet__owner=request.user
    ).select_related("round", "pet").order_by("-submitted_at")
    return render(request, "lottery/my_entries.html", {"entries": entries})


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
