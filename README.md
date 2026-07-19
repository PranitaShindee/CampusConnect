# CampusConnect – Campus Event Board

COMP-8347 Internet Applications and Distributed Systems · University of Windsor · Group 8.

CampusConnect lets guests discover campus events and lets registered students create events, upload posters, RSVP, comment, save favorites, and review activity history.

## Features

- Django authentication, registration, POST logout, and console-based password reset
- Event CRUD with creator/staff authorization and poster validation
- Search, category/date filters, pagination, RSVP capacity checks, comments, favorites
- Session visit counters, browser cookie preference, and browsing history
- Bootstrap 5 responsive UI, Django admin, JSON demo fixture, and automated tests

## Local installation (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py loaddata initial_data
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000/. Password reset uses Django's console email backend, so the reset URL is printed in the terminal running the server. Uploaded posters and profile pictures are stored under `media/` locally.

Run quality checks with:

```powershell
python manage.py check
python manage.py makemigrations --check
python manage.py test
```

## Roles and main URLs

Guests can browse `/events/`, search, and view public pages. Members can create events and use `/dashboard/`, `/favorites/`, `/history/`, and `/profile/`. Staff additionally manage all records in `/admin/`.

## Team responsibilities

- Hemit Rana: settings, models, registration, event list/detail, README integration.
- Sarvesh Solanke: sessions, cookies, history, fixtures, tests, error pages.
- Jasmeen Kaur: event form/CRUD, RSVP, comments, favorites, interaction tests.
- Charmiben Patel: Bootstrap UI, profiles, authentication templates, information pages, accessibility.

Each member should commit their own understood work with descriptive messages; do not fabricate authorship or dates. Before submission, every member must be able to explain their models, views, forms, tests, and security choices.

## Production placeholder and limitations

Set `SECRET_KEY`, `DEBUG`, and `ALLOWED_HOSTS` through environment variables before deployment. SQLite and local media are suitable for coursework/local development; a production host may require persistent media storage and a different database.
