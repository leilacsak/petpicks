from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model


user = get_user_model()


class CorePageTests(TestCase):
    def setUp(self):
        self.user = user.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="testpassword123"
        )
        
    def test_home_page_loads_without_login(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/home.html")
        
    def test_about_page_loads_without_login(self):
        response = self.client.get(reverse("about"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/about.html")
        
    def test_navbar_shows_login_register_when_logged_out(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Login")
        self.assertContains(response, "Register")
        
    def test_navbar_shows_profile_logout_when_logged_in(self):
        self.client.login(username="testuser", password="testpassword123")
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Logout")
        self.assertTrue(
            ("My Profile" in response.content.decode())
        )
        