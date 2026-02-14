from django.urls import path
from . import views


urlpatterns = [
    path("rounds/", views.round_list, name="round_list"),
    path(
        "rounds/<int:round_id>/enter/",
        views.enter_round,
        name="enter_round",
    ),
    path("my-entries/", views.my_entries, name="my_entries"),
    path("moderation/", views.moderation_queue, name="moderation_queue"),
    path(
        "moderation/<int:entry_id>/approve/",
        views.approve_entry,
        name="approve_entry",
    ),
    path(
        "moderation/<int:entry_id>/reject/",
        views.reject_entry,
        name="reject_entry",
    ),
    path("rounds/<int:round_id>/draw/", views.run_draw, name="run_draw"),
    path("results/", views.results, name="results_list"),

]
