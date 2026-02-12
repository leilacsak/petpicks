from django.urls import path
from . import views


urlpatterns = [path("rounds/", views.round_list, name="round_list"),]
