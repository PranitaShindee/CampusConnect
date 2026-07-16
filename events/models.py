from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils import timezone


def _unique_slug(instance, value, slug_field="slug"):
	base_slug = slugify(value)[:220] or "event"
	slug = base_slug
	counter = 1
	model = instance.__class__
	lookup = {slug_field: slug}
	existing = model.objects.filter(**lookup)
	if instance.pk:
		existing = existing.exclude(pk=instance.pk)
	while existing.exists():
		suffix = f"-{counter}"
		slug = f"{base_slug[:230 - len(suffix)]}{suffix}"
		lookup[slug_field] = slug
		existing = model.objects.filter(**lookup)
		if instance.pk:
			existing = existing.exclude(pk=instance.pk)
		counter += 1
	return slug


class Category(models.Model):
	name = models.CharField(max_length=100, unique=True)
	slug = models.SlugField(unique=True)
	description = models.TextField(blank=True)
	icon = models.CharField(max_length=50, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["name"]
		verbose_name_plural = "Categories"

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = _unique_slug(self, self.name, "slug")
		super().save(*args, **kwargs)

	def __str__(self):
		return self.name


class Event(models.Model):
	creator = models.ForeignKey(User, related_name="created_events", on_delete=models.CASCADE)
	category = models.ForeignKey(Category, related_name="events", on_delete=models.CASCADE)
	title = models.CharField(max_length=200)
	slug = models.SlugField(max_length=230, unique=True, blank=True)
	organizer = models.CharField(max_length=150)
	description = models.TextField()
	location = models.CharField(max_length=255)
	start_datetime = models.DateTimeField()
	end_datetime = models.DateTimeField()
	capacity = models.PositiveIntegerField(null=True, blank=True)
	poster = models.ImageField(upload_to="event_posters/", null=True, blank=True)
	is_published = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["start_datetime"]
		indexes = [
			models.Index(fields=["title"]),
			models.Index(fields=["start_datetime"]),
			models.Index(fields=["is_published"]),
		]

	def clean(self):
		super().clean()
		errors = {}
		if self.start_datetime and self.end_datetime and self.end_datetime <= self.start_datetime:
			errors["end_datetime"] = "End time must be later than start time."
		if self.capacity is not None and self.capacity <= 0:
			errors["capacity"] = "Capacity must be greater than zero."
		if errors:
			raise ValidationError(errors)

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = _unique_slug(self, self.title)
		self.full_clean(exclude=None)
		super().save(*args, **kwargs)

	@property
	def is_past(self):
		return self.end_datetime < timezone.now()

	@property
	def is_upcoming(self):
		return self.start_datetime > timezone.now()

	@property
	def attendee_count(self):
		return self.rsvps.filter(status=RSVP.Status.ATTENDING).count()

	@property
	def available_spots(self):
		if self.capacity is None:
			return None
		return max(self.capacity - self.attendee_count, 0)

	def get_absolute_url(self):
		return reverse("events:event_detail", kwargs={"slug": self.slug})

	def __str__(self):
		return self.title


class RSVP(models.Model):
	class Status(models.TextChoices):
		ATTENDING = "ATTENDING", "Attending"
		CANCELLED = "CANCELLED", "Cancelled"

	user = models.ForeignKey(User, related_name="rsvps", on_delete=models.CASCADE)
	event = models.ForeignKey(Event, related_name="rsvps", on_delete=models.CASCADE)
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.ATTENDING)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		constraints = [models.UniqueConstraint(fields=["user", "event"], name="unique_user_event_rsvp")]

	def clean(self):
		super().clean()
		if self.status == self.Status.ATTENDING and self.event and self.event.is_past:
			raise ValidationError({"event": "You cannot RSVP to a past event."})

	def __str__(self):
		return f"{self.user.username} - {self.event.title} ({self.status})"


class Comment(models.Model):
	event = models.ForeignKey(Event, related_name="comments", on_delete=models.CASCADE)
	author = models.ForeignKey(User, related_name="event_comments", on_delete=models.CASCADE)
	body = models.TextField(max_length=1000)
	is_approved = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-created_at"]

	def clean(self):
		super().clean()
		if not self.body or not self.body.strip():
			raise ValidationError({"body": "Comment cannot be blank."})

	def __str__(self):
		preview = self.body.strip().replace("\n", " ")
		return f"{self.author.username} on {self.event.title}: {preview[:40]}"


class UserProfile(models.Model):
	user = models.OneToOneField(User, related_name="profile", on_delete=models.CASCADE)
	student_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
	program = models.CharField(max_length=150, blank=True)
	bio = models.TextField(blank=True)
	profile_picture = models.ImageField(upload_to="profile_pictures/", null=True, blank=True)
	preferred_category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL)
	email_notifications = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"Profile for {self.user.username}"


class FavoriteEvent(models.Model):
	user = models.ForeignKey(User, related_name="favorite_events", on_delete=models.CASCADE)
	event = models.ForeignKey(Event, related_name="favorited_by", on_delete=models.CASCADE)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		constraints = [models.UniqueConstraint(fields=["user", "event"], name="unique_user_favorite_event")]

	def __str__(self):
		return f"{self.user.username} favorited {self.event.title}"


class EventHistory(models.Model):
	user = models.ForeignKey(User, related_name="event_history", null=True, blank=True, on_delete=models.SET_NULL)
	event = models.ForeignKey(Event, related_name="view_history", on_delete=models.CASCADE)
	session_key = models.CharField(max_length=40, blank=True)
	viewed_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-viewed_at"]
		indexes = [
			models.Index(fields=["user", "viewed_at"]),
			models.Index(fields=["session_key", "viewed_at"]),
		]

	def __str__(self):
		actor = self.user.username if self.user else self.session_key or "anonymous"
		return f"{actor} viewed {self.event.title}"
