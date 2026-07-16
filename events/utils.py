from datetime import timedelta

from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from .models import Category, EventHistory, UserProfile


def safe_redirect_target(request, fallback):
    target = request.POST.get("next") or request.GET.get("next") or fallback
    if url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}):
        return target
    return fallback


def ensure_user_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def update_visit_session(request):
    today = timezone.localdate().isoformat()
    session = request.session
    session["total_visits"] = session.get("total_visits", 0) + 1
    if session.get("visit_date") != today:
        session["visit_date"] = today
        session["daily_visits"] = 1
    else:
        session["daily_visits"] = session.get("daily_visits", 0) + 1
    session["last_visit_date"] = today
    session.modified = True
    return session["total_visits"], session["daily_visits"], today


def update_recently_viewed(request, event_id):
    recent_ids = request.session.get("recently_viewed_event_ids", [])
    if recent_ids and recent_ids[-1] == event_id:
        return recent_ids
    recent_ids = [item for item in recent_ids if item != event_id]
    recent_ids.append(event_id)
    recent_ids = recent_ids[-5:]
    request.session["recently_viewed_event_ids"] = recent_ids
    request.session.modified = True
    return recent_ids


def record_event_history(request, event):
    session = request.session
    if not session.session_key:
        session.save()
    session_key = session.session_key or ""
    user = request.user if request.user.is_authenticated else None
    cutoff = timezone.now() - timedelta(seconds=30)
    recent_history = EventHistory.objects.filter(event=event, viewed_at__gte=cutoff)
    if user:
        recent_history = recent_history.filter(user=user)
    else:
        recent_history = recent_history.filter(session_key=session_key)
    if recent_history.exists():
        return None
    return EventHistory.objects.create(user=user, event=event, session_key=session_key)


def set_response_cookies(response, request, preferred_category=None):
    today = timezone.localdate().isoformat()
    response.set_cookie("campusconnect_last_visit", today, max_age=60 * 60 * 24 * 30)
    if preferred_category:
        response.set_cookie("campusconnect_preferred_category", preferred_category, max_age=60 * 60 * 24 * 30)
    if request.COOKIES.get("campusconnect_welcome_dismissed") is None:
        response.set_cookie("campusconnect_welcome_dismissed", "0", max_age=60 * 60 * 24 * 30)
    return response


def nav_categories():
    return Category.objects.only("name", "slug").order_by("name")
