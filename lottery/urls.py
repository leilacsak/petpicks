from django.urls import path
from . import views


urlpatterns = [
    path("rounds/", views.round_list, name="round_list"),
    path(
        "rounds/<int:round_id>/enter/",
        views.enter_round,
        name="enter_round",
    ),
    path("profile/", views.profile, name="profile"),
    path(
        "notification/dismiss/",
        views.dismiss_notification,
        name="dismiss_notification",
    ),
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
    path(
        "entries/<int:entry_id>/comments/",
        views.comment_create,
        name="comment_create",
    ),
    path(
        "comments/<int:comment_id>/edit/",
        views.comment_edit,
        name="comment_edit",
    ),
    path(
        "comments/<int:comment_id>/delete/",
        views.comment_delete,
        name="comment_delete",
    ),
    path("entries/<int:entry_id>/edit/", views.edit_entry, name="edit_entry"),
    path(
        "entries/<int:entry_id>/delete/",
        views.delete_entry,
        name="delete_entry",
    ),
]
