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
]
