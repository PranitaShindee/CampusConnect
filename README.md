# CampusConnect – Campus Event Board

CampusConnect is a Django 5.x course project for COMP-8347, Internet Applications and Distributed Systems, at the University of Windsor.

## Phase 1 setup

The repository currently contains the project scaffold, a Bootstrap-based home page, and local settings for SQLite, static files, and media uploads.

## Local setup on Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Notes

- Use environment variables for `SECRET_KEY`, `DEBUG`, and `ALLOWED_HOSTS` when moving beyond local development.
- Media uploads will be stored in the local `media/` folder during development.
- Password reset will use Django's console email backend in later phases.
