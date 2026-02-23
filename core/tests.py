from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.forms import ContactForm

User = get_user_model()


class CorePageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
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
        self.assertIn("My Profile", response.content.decode())

    def test_contact_form_submission_success(self):
        response = self.client.post(reverse("home"), {
            "name": "Test User",
            "email": "test@example.com",
            "message": "Hello PetPicks!"
        }, follow=True)
        self.assertContains(response, "Your message has been sent")
        # The form should be reset (empty, no errors)
        self.assertIsInstance(response.context["contact_form"], ContactForm)
        self.assertFalse(response.context["contact_form"].errors)

    def test_contact_form_validation_errors(self):
        response = self.client.post(reverse("home"), {
            "name": "",
            "email": "invalid",
            "message": ""
        }, follow=True)
        self.assertContains(response, "Please correct the errors below.")
        self.assertTrue(response.context["contact_form"].errors)
