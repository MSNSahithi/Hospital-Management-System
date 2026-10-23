from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as django_login, logout
from django.contrib.auth.decorators import login_required
from .serializers import SignupSerializer
from .models import User
from .forms import SignupForm, LoginForm
from notifications.email_client import send_email
from django.conf import settings
from django.http import HttpResponse
import logging

# Google OAuth libs (optional; require installation)
try:
    from google_auth_oauthlib.flow import Flow
    import requests as _requests
except ImportError:
    Flow = None
    _requests = None

logger = logging.getLogger(__name__)
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/userinfo.email",
]


def _google_redirect_uri(request):
    return getattr(settings, "GOOGLE_REDIRECT_URI", None) or request.build_absolute_uri(
        "/accounts/google-callback/"
    )


def _google_client_config():
    return {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }


def _dashboard_url(user):
    return "/doctor/dashboard/" if user.role == "DOCTOR" else "/patient/dashboard/"

# DRF imports for API endpoints
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token

@api_view(["POST"])
@permission_classes([AllowAny])
def signup(request):
    serializer = SignupSerializer(data=request.data)

    if serializer.is_valid():
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)

        return Response(
            {
                "message": "Signup successful",
                "token": token.key,
                "username": user.username,
                "role": user.role,
            },
            status=status.HTTP_201_CREATED,
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    username = request.data.get("username")
    password = request.data.get("password")

    user = authenticate(username=username, password=password)

    if not user:
        return Response(
            {"error": "Invalid username or password"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    token, created = Token.objects.get_or_create(user=user)

    return Response(
        {
            "message": "Login successful",
            "token": token.key,
            "username": user.username,
            "role": user.role,
        },
        status=status.HTTP_200_OK,
    )



# ---------------- HOME ----------------
def home(request):
    return render(request, "home.html")


# ---------------- DOCTOR ----------------
def doctor_signup_page(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.role = "DOCTOR"
            obj.set_password(form.cleaned_data["password"])
            obj.save()
            # Send welcome email asynchronously (best-effort)
            try:
                send_email("SIGNUP_WELCOME", {"to_email": obj.email, "username": obj.username, "role": obj.role})
            except Exception:
                pass
            messages.success(request, "Doctor signup successful! Now login.")
            return redirect("/doctor/login/")
    else:
        form = SignupForm()
    return render(request, "doctor_signup.html", {"form": form})


def doctor_login_page(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(username=username, password=password)
            if user is None:
                messages.error(request, "Invalid username or password")
            elif getattr(user, "role", "").upper() != "DOCTOR":
                messages.error(request, "This is Doctor login page!")
            else:
                django_login(request, user)
                messages.success(request, "Doctor login successful!")
                return redirect("/doctor/dashboard/")
    else:
        form = LoginForm()
    return render(request, "doctor_login.html", {"form": form})


@login_required
def doctor_dashboard(request):
    if request.user.role != "DOCTOR":
        messages.error(request, "Access denied!")
        return redirect("/doctor/login/")
    return render(request, "doctor_dashboard.html", {"user": request.user})


# ---------------- PATIENT ----------------
def patient_signup_page(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.role = "PATIENT"
            obj.set_password(form.cleaned_data["password"])
            obj.save()
            try:
                send_email("SIGNUP_WELCOME", {"to_email": obj.email, "username": obj.username, "role": obj.role})
            except Exception:
                pass
            messages.success(request, "Patient signup successful! Now login.")
            return redirect("/patient/login/")
    else:
        form = SignupForm()
    return render(request, "patient_signup.html", {"form": form})


def patient_login_page(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(username=username, password=password)
            if user is None:
                messages.error(request, "Invalid username or password")
            elif getattr(user, "role", "").upper() != "PATIENT":
                messages.error(request, "This is Patient login page!")
            else:
                django_login(request, user)
                messages.success(request, "Patient login successful!")
                return redirect("/patient/dashboard/")
    else:
        form = LoginForm()
    return render(request, "patient_login.html", {"form": form})


@login_required(login_url="/")
def connect_google(request):
    if request.user.role not in {"DOCTOR", "PATIENT"}:
        messages.error(request, "Only doctors and patients can connect Google Calendar.")
        return redirect("/")

    if not Flow:
        messages.error(request, "Google Calendar support is unavailable. Install the Google OAuth dependencies.")
        return redirect(_dashboard_url(request.user))

    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        messages.error(request, "Google Calendar is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.")
        return redirect(_dashboard_url(request.user))

    flow = Flow.from_client_config(
        _google_client_config(),
        scopes=GOOGLE_SCOPES,
        redirect_uri=_google_redirect_uri(request),
    )
    auth_url, state = flow.authorization_url(
        access_type="offline", include_granted_scopes="true", prompt="consent"
    )
    request.session["google_oauth_state"] = state
    request.session["google_oauth_user_id"] = request.user.pk
    return redirect(auth_url)


@login_required(login_url="/")
def google_callback(request):
    if not Flow or not _requests:
        return HttpResponse("Google OAuth libraries not installed. Install google-auth-oauthlib and google-api-python-client.")

    state = request.session.pop("google_oauth_state", None)
    user_id = request.session.pop("google_oauth_user_id", None)
    if not state or request.GET.get("state") != state or user_id != request.user.pk:
        messages.error(request, "Google Calendar connection expired or could not be verified. Please try again.")
        return redirect(_dashboard_url(request.user))

    if request.GET.get("error"):
        messages.error(request, "Google Calendar connection was cancelled.")
        return redirect(_dashboard_url(request.user))

    client_id = getattr(settings, "GOOGLE_CLIENT_ID", None)
    client_secret = getattr(settings, "GOOGLE_CLIENT_SECRET", None)
    redirect_uri = _google_redirect_uri(request)
    if not client_id or not client_secret:
        messages.error(request, "Google Calendar is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.")
        return redirect(_dashboard_url(request.user))

    flow = Flow.from_client_config(
        _google_client_config(),
        scopes=GOOGLE_SCOPES,
        state=state,
        redirect_uri=redirect_uri,
    )

    code = request.GET.get("code")
    if not code:
        messages.error(request, "Google did not return an authorization code. Please try connecting again.")
        return redirect(_dashboard_url(request.user))

    try:
        flow.fetch_token(code=code)
    except Exception:
        logger.exception("Google OAuth token exchange failed for user %s", request.user.pk)
        messages.error(request, "Google Calendar could not be connected. Please try again.")
        return redirect(_dashboard_url(request.user))
    creds = flow.credentials

    # Persist refresh token and google email (get email via userinfo endpoint)
    refresh = getattr(creds, "refresh_token", None) or request.user.google_refresh_token
    access_token = creds.token
    if refresh:
        user = request.user
        user.google_refresh_token = refresh
        email_lookup_failed = False
        # fetch userinfo
        try:
            resp = _requests.get("https://www.googleapis.com/oauth2/v2/userinfo", headers={"Authorization": f"Bearer {access_token}"}, timeout=5)
            resp.raise_for_status()
            if resp.status_code == 200:
                info = resp.json()
                user.google_email = info.get("email")
        except (_requests.RequestException, ValueError):
            logger.exception("Could not retrieve Google account email for user %s", request.user.pk)
            email_lookup_failed = True

        user.save(update_fields=["google_refresh_token", "google_email"])
        if email_lookup_failed:
            messages.warning(request, "Google Calendar is connected, but the Google account email could not be loaded.")
        else:
            messages.success(request, "Google Calendar connected successfully.")
        return redirect(_dashboard_url(user))

    messages.error(request, "Google did not provide a refresh token. Please grant offline access and try again.")
    return redirect(_dashboard_url(request.user))


@login_required
def patient_dashboard(request):
    if request.user.role != "PATIENT":
        messages.error(request, "Access denied!")
        return redirect("/patient/login/")
    return render(request, "patient_dashboard.html", {"user": request.user})


# ---------------- LOGOUT ----------------
def logout_page(request):
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect("/")
