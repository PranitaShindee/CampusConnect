from django.contrib import admin

from .models import Category, Comment, Event, EventHistory, FavoriteEvent, RSVP, UserProfile


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
	list_display = ("name", "slug", "created_at")
	search_fields = ("name", "slug")
	ordering = ("name",)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
	list_display = ("title", "category", "creator", "start_datetime", "is_published")
	list_filter = ("category", "is_published", "start_datetime")
	search_fields = ("title", "organizer", "location", "description")
	ordering = ("start_datetime",)
	date_hierarchy = "start_datetime"
	readonly_fields = ("created_at", "updated_at", "slug")


@admin.register(RSVP)
class RSVPAdmin(admin.ModelAdmin):
	list_display = ("user", "event", "status", "created_at")
	list_filter = ("status", "created_at")
	search_fields = ("user__username", "event__title")
	ordering = ("-created_at",)
	date_hierarchy = "created_at"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
	list_display = ("event", "author", "is_approved", "created_at")
	list_filter = ("is_approved", "created_at")
	search_fields = ("event__title", "author__username", "body")
	ordering = ("-created_at",)
	date_hierarchy = "created_at"


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
	list_display = ("user", "student_id", "preferred_category", "email_notifications", "updated_at")
	list_filter = ("preferred_category", "email_notifications")
	search_fields = ("user__username", "student_id", "program")
	ordering = ("user__username",)


@admin.register(FavoriteEvent)
class FavoriteEventAdmin(admin.ModelAdmin):
	list_display = ("user", "event", "created_at")
	search_fields = ("user__username", "event__title")
	ordering = ("-created_at",)


@admin.register(EventHistory)
class EventHistoryAdmin(admin.ModelAdmin):
	list_display = ("event", "user", "session_key", "viewed_at")
	list_filter = ("viewed_at",)
	search_fields = ("event__title", "user__username", "session_key")
	ordering = ("-viewed_at",)
	date_hierarchy = "viewed_at"

