# Linter in some environments may report "Import 'django.urls' could not be resolved from source".
# Add a type ignore comment to suppress that static analysis warning while keeping the runtime import.
from django.urls import path  # type: ignore
from . import views

app_name = "accounts_app"

urlpatterns = [
    # Home
    path("", views.home, name="home"),

    # Doctor Pages
    path("doctor/signup/", views.doctor_signup_page, name="doctor_signup"),
    path("doctor/login/", views.doctor_login_page, name="doctor_login"),
    # dashboard routes handled by booking_app to keep responsibilities separated

    # Patient Pages
    path("patient/signup/", views.patient_signup_page, name="patient_signup"),
    path("patient/login/", views.patient_login_page, name="patient_login"),
    # dashboard routes handled by booking_app to keep responsibilities separated

    # Logout
    path("logout/", views.logout_page, name="logout"),

    # Google connect (placeholder) - if you have Google OAuth client ID/secret, implement
    path("accounts/connect-google/", views.connect_google, name="connect_google"),
    path("accounts/google-callback/", views.google_callback, name="google_callback"),

    # API (Postman / frontend API calls)
    path("api/accounts/signup/", views.signup, name="api_signup"),
    path("api/accounts/login/", views.login, name="api_login"),
]
