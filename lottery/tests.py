import io
import shutil
import tempfile
from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from .models import LotteryRound, Pet, Entry


User = get_user_model()


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class LotteryCoreFeatureTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        # Clean up MEDIA_ROOT temp directory created by override_settings
        media_root = getattr(cls.settings, "MEDIA_ROOT", None)
        super().tearDownClass()
        if media_root:
            shutil.rmtree(media_root, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create_user(
            username="user1", password="pass12345"
        )
        self.staff = User.objects.create_user(
            username="staff1", password="pass12345", is_staff=True
        )

        now = timezone.now()
        self.active_round = LotteryRound.objects.create(
            title="Active Round",
            start_date=now - timezone.timedelta(days=1),
            end_date=now + timezone.timedelta(days=1),
            status=LotteryRound.Status.ACTIVE,
        )

    def _upload_photo(self, name="pet.png"):
        """
        Generate a real in-memory PNG so Pillow verify() passes in form
        validation.
        """
        f = io.BytesIO()
        Image.new("RGB", (1, 1)).save(f, format="PNG")
        f.seek(0)
        return SimpleUploadedFile(name, f.read(), content_type="image/png")

    # -------------------------
    # AUTH ACCESS
    # -------------------------
    def test_guest_cannot_access_profile(self):
        resp = self.client.get(reverse("profile"))
        self.assertEqual(resp.status_code, 302)  # redirect to login

    def test_guest_cannot_access_enter_round(self):
        resp = self.client.get(
            reverse("enter_round", args=[self.active_round.id])
        )
        self.assertEqual(resp.status_code, 302)

    def test_nonstaff_cannot_access_moderation_queue(self):
        self.client.login(username="user1", password="pass12345")
        resp = self.client.get(reverse("moderation_queue"))
        self.assertIn(resp.status_code, (302, 403))

    def test_staff_can_access_moderation_queue(self):
        self.client.login(username="staff1", password="pass12345")
        resp = self.client.get(reverse("moderation_queue"))
        self.assertEqual(resp.status_code, 200)

    # -------------------------
    # ENTRY CREATION
    # -------------------------
    def test_logged_in_user_can_create_entry(self):
        self.client.login(username="user1", password="pass12345")

        resp = self.client.post(
            reverse("enter_round", args=[self.active_round.id]),
            data={
                "pet_name": "Bella",
                "pet_breed": "Golden Retriever",
                "pet_age_number": "2",
                "pet_age_unit": "year(s)",
                "photo": self._upload_photo(),
            },
            follow=True,
        )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            Pet.objects.filter(owner=self.user, name="Bella").count(), 1
        )
        self.assertEqual(
            Entry.objects.filter(round=self.active_round).count(), 1
        )

    # -------------------------
    # PERMISSIONS / RULE: 1 PET PER ROUND
    # -------------------------
    def test_cannot_submit_same_pet_twice_same_round(self):
        """
        Verifies your rule: one entry per pet per round.
        Requires enter_round view duplicate check to be pet+round
        (not user+round).
        """
        self.client.login(username="user1", password="pass12345")

        # First submission
        self.client.post(
            reverse("enter_round", args=[self.active_round.id]),
            data={
                "pet_name": "Bella",
                "pet_breed": "Golden Retriever",
                "pet_age_number": "2",
                "pet_age_unit": "year(s)",
                "photo": self._upload_photo("pet1.png"),
            },
            follow=True,
        )

        self.assertEqual(
            Entry.objects.filter(round=self.active_round).count(), 1
        )

        # Second submission same pet name (same owner+name => same Pet)
        resp = self.client.post(
            reverse("enter_round", args=[self.active_round.id]),
            data={
                "pet_name": "Bella",
                "pet_breed": "Golden Retriever",
                "pet_age_number": "2",
                "pet_age_unit": "year(s)",
                "photo": self._upload_photo("pet2.png"),
            },
            follow=True,
        )

        self.assertEqual(
            Entry.objects.filter(round=self.active_round).count(), 1
        )
        self.assertTrue(
            "already been entered" in resp.content.decode().lower()
        )

    def test_user_can_enter_same_round_with_different_pets(self):
        self.client.login(username="user1", password="pass12345")

        # First pet
        resp1 = self.client.post(
            reverse("enter_round", args=[self.active_round.id]),
            data={
                "pet_name": "Bella",
                "pet_breed": "Golden Retriever",
                "pet_age_number": "2",
                "pet_age_unit": "year(s)",
                "photo": self._upload_photo("pet1.png"),
            },
            follow=True,
        )
        self.assertEqual(resp1.status_code, 200)
        self.assertEqual(
            Entry.objects.filter(round=self.active_round).count(), 1
        )

        # Second pet (different name)
        resp2 = self.client.post(
            reverse("enter_round", args=[self.active_round.id]),
            data={
                "pet_name": "Max",
                "pet_breed": "Labrador",
                "pet_age_number": "3",
                "pet_age_unit": "year(s)",
                "photo": self._upload_photo("pet2.png"),
            },
            follow=True,
        )
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(
            Entry.objects.filter(round=self.active_round).count(), 2
        )
        self.assertFalse(
            "already been entered" in resp2.content.decode().lower()
        )

    # -------------------------
    # ADMIN DRAW + WINNER COUNT
    # -------------------------
    def _make_approved_entry(self, owner, pet_name, round_obj):
        pet = Pet.objects.create(
            owner=owner,
            name=pet_name,
            breed="Breed",
            age="1 year(s)"
        )
        return Entry.objects.create(
            pet=pet,
            round=round_obj,
            photo=self._upload_photo(f"{pet_name}.png"),
            status=Entry.Status.APPROVED,
        )

    def test_nonstaff_cannot_run_draw(self):
        self.client.login(username="user1", password="pass12345")
        resp = self.client.get(
            reverse("run_draw", args=[self.active_round.id])
        )
        self.assertIn(resp.status_code, (302, 403))

    def test_staff_run_draw_selects_exactly_3_winners_when_3plus_entries(self):
        # Create 4 approved entries with different owners
        u2 = User.objects.create_user("user2", password="pass12345")
        u3 = User.objects.create_user("user3", password="pass12345")
        u4 = User.objects.create_user("user4", password="pass12345")

        self._make_approved_entry(self.user, "Bella", self.active_round)
        self._make_approved_entry(u2, "Max", self.active_round)
        self._make_approved_entry(u3, "Luna", self.active_round)
        self._make_approved_entry(u4, "Milo", self.active_round)

        self.client.login(username="staff1", password="pass12345")
        resp = self.client.get(
            reverse("run_draw", args=[self.active_round.id]),
            follow=True
        )
        self.assertEqual(resp.status_code, 200)

        self.active_round.refresh_from_db()
        self.assertEqual(
            self.active_round.status, LotteryRound.Status.COMPLETED
        )
        self.assertIsNotNone(self.active_round.drawn_at)

        self.assertEqual(
            Entry.objects.filter(
                round=self.active_round, is_winner=True
            ).count(),
            3
        )

    def test_staff_run_draw_handles_fewer_than_3_entries(self):
        # Only 2 approved entries
        u2 = User.objects.create_user("user2b", password="pass12345")
        self._make_approved_entry(self.user, "Bella", self.active_round)
        self._make_approved_entry(u2, "Max", self.active_round)

        self.client.login(username="staff1", password="pass12345")
        self.client.get(
            reverse("run_draw", args=[self.active_round.id]), follow=True
        )

        self.assertEqual(
            Entry.objects.filter(
                round=self.active_round, is_winner=True
            ).count(),
            2
        )

    def test_cannot_run_draw_twice_for_same_round(self):
        u2 = User.objects.create_user("user2c", password="pass12345")
        u3 = User.objects.create_user("user3c", password="pass12345")

        self._make_approved_entry(self.user, "Bella", self.active_round)
        self._make_approved_entry(u2, "Max", self.active_round)
        self._make_approved_entry(u3, "Luna", self.active_round)

        self.client.login(username="staff1", password="pass12345")
        self.client.get(
            reverse("run_draw", args=[self.active_round.id]), follow=True
        )

        winners_after_first = Entry.objects.filter(
            round=self.active_round, is_winner=True
        ).count()
        self.assertEqual(winners_after_first, 3)

        # Attempt second run
        resp = self.client.get(
            reverse("run_draw", args=[self.active_round.id]),
            follow=True
        )
        winners_after_second = Entry.objects.filter(
            round=self.active_round, is_winner=True
        ).count()
        self.assertEqual(winners_after_second, 3)

        # Confirm warning message appeared
        self.assertTrue(
            ("already been drawn" in resp.content.decode().lower())

        )
