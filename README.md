# Hospital Management System (HMS)

A web-based hospital management system built with Django. Doctors can manage availability slots, and patients can book appointments.

## Features

- Doctor and patient signup and login
- Separate doctor and patient dashboards
- Doctor availability slots
- Patient appointment booking
- Django REST Framework API with token authentication
- Optional Google Calendar integration for appointment bookings

## Technology

- Python
- Django
- Django REST Framework
- SQLite by default (PostgreSQL can also be configured)
- HTML templates

## Requirements

- Python 3.10 or later
- pip

## Setup on Windows

Open PowerShell in the project directory and run:

```powershell
cd .\mini-hms
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

Run the application
Start the development server:
python manage.py runserver
Open http://127.0.0.1:8000/ in your browser.

Main pages
Home: /
Doctor signup: /doctor/signup/
Doctor login: /doctor/login/
Patient signup: /patient/signup/
Patient login: /patient/login/
API endpoints
Signup: POST /api/accounts/signup/
Login: POST /api/accounts/login/
Optional Google Calendar integration
To enable Calendar integration, configure a Google OAuth 2.0 Web application and add this callback URL to its authorized redirect URIs:
http://127.0.0.1:8000/accounts/google-callback/

Create a mini-hms/.env file with your OAuth credentials:
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://127.0.0.1:8000/accounts/google-callback/

Restart the Django server after changing .env. Sign in and choose Connect Google to authorize Calendar access. Appointment events are added when an appointment is booked; existing bookings are not backfilled.

Run tests
python manage.py test

Project structure
mini-hms/
├── accounts_app/   # User accounts and authentication
├── booking_app/    # Availability slots and appointments
├── hms_backend/    # Django project configuration
├── notifications/  # Google and email integrations
├── templates/      # HTML pages
├── manage.py
└── requirements.txt


Keep credentials private: use your own values in `.env`, and don’t put real secrets in the README.
