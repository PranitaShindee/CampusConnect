from datetime import timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Category, Comment, Event, FavoriteEvent, RSVP


class CampusConnectTestCase(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Technology")
        self.owner = User.objects.create_user("owner", "owner@example.com", "TestPass123!")
        self.other = User.objects.create_user("other", "other@example.com", "TestPass123!")
        start = timezone.now() + timedelta(days=2)
        self.event = Event.objects.create(
            creator=self.owner, category=self.category, title="Python Workshop", organizer="CS Club",
            description="Learn Django basics.", location="Odette 101", start_datetime=start,
            end_datetime=start + timedelta(hours=2), capacity=2,
        )


class ModelTests(CampusConnectTestCase):
    def test_category_string_and_auto_slug(self):
        self.assertEqual(str(self.category), "Technology")
        self.assertEqual(self.category.slug, "technology")

    def test_event_unique_slug_and_capacity(self):
        start = timezone.now() + timedelta(days=3)
        second = Event.objects.create(creator=self.owner, category=self.category, title="Python Workshop", organizer="Club", description="x", location="Room", start_datetime=start, end_datetime=start + timedelta(hours=1))
        self.assertNotEqual(self.event.slug, second.slug)
        self.assertEqual(self.event.available_spots, 2)

    def test_invalid_event_dates_are_rejected(self):
        event = Event(creator=self.owner, category=self.category, title="Invalid", organizer="Club", description="x", location="Room", start_datetime=timezone.now(), end_datetime=timezone.now() - timedelta(hours=1))
        with self.assertRaises(ValidationError):
            event.full_clean()

    def test_rsvp_and_favorite_unique_constraints(self):
        RSVP.objects.create(user=self.owner, event=self.event)
        FavoriteEvent.objects.create(user=self.owner, event=self.event)
        with self.assertRaises(Exception):
            RSVP.objects.create(user=self.owner, event=self.event)
        with self.assertRaises(Exception):
            FavoriteEvent.objects.create(user=self.owner, event=self.event)


class AuthenticationAndPermissionsTests(CampusConnectTestCase):
    def test_registration_and_duplicate_email(self):
        response = self.client.post(reverse("events:register"), {"username": "newuser", "first_name": "New", "last_name": "User", "email": "new@example.com", "password1": "StrongPass123!", "password2": "StrongPass123!"})
        self.assertRedirects(response, reverse("events:dashboard"))
        self.client.logout()
        response = self.client.post(reverse("events:register"), {"username": "third", "first_name": "", "last_name": "", "email": "NEW@example.com", "password1": "StrongPass123!", "password2": "StrongPass123!"})
        self.assertContains(response, "already registered")

    def test_protected_create_redirects_and_owner_permissions(self):
        response = self.client.get(reverse("events:event_create"))
        self.assertEqual(response.status_code, 302)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse("events:event_update", args=[self.event.slug])).status_code, 403)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(reverse("events:event_update", args=[self.event.slug])).status_code, 200)

    def test_public_pages_and_password_reset_are_available(self):
        for name in ("home", "event_list", "about", "contact", "terms", "password_reset"):
            self.assertEqual(self.client.get(reverse(f"events:{name}")).status_code, 200)


class EventInteractionTests(CampusConnectTestCase):
    def test_search_by_title_organizer_and_category(self):
        self.assertContains(self.client.get(reverse("events:event_list"), {"q": "python", "date": "all"}), "Python Workshop")
        self.assertContains(self.client.get(reverse("events:event_list"), {"q": "cs club", "category": self.category.id, "date": "all"}), "Python Workshop")
        self.assertContains(self.client.get(reverse("events:event_list"), {"q": "nothing", "date": "all"}), "No events matched")

    def test_rsvp_cancel_favorite_and_comment(self):
        self.client.force_login(self.other)
        url = reverse("events:toggle_rsvp", args=[self.event.slug])
        self.client.post(url)
        self.assertEqual(RSVP.objects.get(user=self.other, event=self.event).status, RSVP.Status.ATTENDING)
        self.client.post(url)
        self.assertEqual(RSVP.objects.get(user=self.other, event=self.event).status, RSVP.Status.CANCELLED)
        favorite_url = reverse("events:toggle_favorite", args=[self.event.slug])
        self.client.post(favorite_url)
        self.assertTrue(FavoriteEvent.objects.filter(user=self.other, event=self.event).exists())
        comment_url = reverse("events:add_comment", args=[self.event.slug])
        self.client.post(comment_url, {"body": "Helpful event!"})
        comment = Comment.objects.get(author=self.other)
        self.assertEqual(comment.body, "Helpful event!")
        self.client.post(reverse("events:delete_comment", args=[comment.pk]))
        self.assertFalse(Comment.objects.exists())

    def test_full_event_and_blank_comment_are_rejected(self):
        RSVP.objects.create(user=self.owner, event=self.event)
        self.event.capacity = 1
        self.event.save()
        self.client.force_login(self.other)
        self.client.post(reverse("events:toggle_rsvp", args=[self.event.slug]))
        self.assertFalse(RSVP.objects.filter(user=self.other, event=self.event, status=RSVP.Status.ATTENDING).exists())
        self.client.post(reverse("events:add_comment", args=[self.event.slug]), {"body": "   "})
        self.assertFalse(Comment.objects.exists())


class SessionTests(CampusConnectTestCase):
    def test_visit_counter_recent_history_and_cookie(self):
        self.client.get(reverse("events:home"))
        self.client.get(reverse("events:home"))
        self.assertEqual(self.client.session["total_visits"], 2)
        response = self.client.get(reverse("events:event_list"), {"category": self.category.id, "date": "all"})
        self.assertIn("campusconnect_preferred_category", response.cookies)
        self.client.get(reverse("events:event_detail", args=[self.event.slug]))
        self.assertEqual(self.client.session["recently_viewed_event_ids"], [self.event.id])
