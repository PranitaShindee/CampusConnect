from django.utils import timezone

from .models import FavoriteEvent
from .utils import nav_categories


def site_globals(request):
    data = {
        "nav_categories": nav_categories(),
        "current_year": timezone.now().year,
    }
    if request.user.is_authenticated:
        data["favorite_event_ids"] = set(
            FavoriteEvent.objects.filter(user=request.user).values_list("event_id", flat=True)
        )
    else:
        data["favorite_event_ids"] = set()
    return data
