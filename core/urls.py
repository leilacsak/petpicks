from django.urls import path
from . import views
from django.shortcuts import redirect


# Redirect view for /contact/ to home with anchor

def contact_redirect(request):
    return redirect('/#contact-form')


urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("contact/", contact_redirect, name="contact"),
]
