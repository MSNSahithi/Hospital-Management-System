from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, override_settings


class DatabaseSettingsFallbackTests(SimpleTestCase):
    def test_database_settings_fallback_to_sqlite(self):
        from hms_backend import settings as settings_module

        db_settings = settings_module.get_database_settings()

        self.assertEqual(db_settings["default"]["ENGINE"], "django.db.backends.sqlite3")


@override_settings(
    GOOGLE_CLIENT_ID="test-client-id",
    GOOGLE_CLIENT_SECRET="test-client-secret",
    GOOGLE_REDIRECT_URI="http://testserver/accounts/google-callback/",
)
class GoogleCalendarConnectionTests(TestCase):
    def setUp(self):
        self.doctor = get_user_model().objects.create_user(
            username="calendar-doctor",
            password="pass123",
            role="DOCTOR",
        )
        self.client.force_login(self.doctor)

    @patch("accounts_app.views._requests")
    @patch("accounts_app.views.Flow")
    def test_oauth_callback_saves_refresh_token_and_google_email(self, flow_class, requests):
        flow = flow_class.from_client_config.return_value
        flow.authorization_url.return_value = (
            "https://accounts.google.com/test-consent",
            "test-state",
        )
        flow.credentials = SimpleNamespace(
            refresh_token="test-refresh-token",
            token="test-access-token",
        )
        requests.get.return_value.status_code = 200
        requests.get.return_value.json.return_value = {"email": "doctor@example.com"}

        start_response = self.client.get("/accounts/connect-google/")
        callback_response = self.client.get(
            "/accounts/google-callback/",
            {"state": "test-state", "code": "test-code"},
        )

        self.assertRedirects(
            start_response,
            "https://accounts.google.com/test-consent",
            fetch_redirect_response=False,
        )
        self.assertRedirects(
            callback_response,
            "/doctor/dashboard/",
            fetch_redirect_response=False,
        )
        self.doctor.refresh_from_db()
        self.assertEqual(self.doctor.google_refresh_token, "test-refresh-token")
        self.assertEqual(self.doctor.google_email, "doctor@example.com")
        flow.fetch_token.assert_called_once_with(code="test-code")
        requests.get.assert_called_once_with(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": "Bearer test-access-token"},
            timeout=5,
        )

    @patch("accounts_app.views.Flow")
    def test_oauth_callback_rejects_invalid_state(self, flow_class):
        session = self.client.session
        session["google_oauth_state"] = "expected-state"
        session["google_oauth_user_id"] = self.doctor.pk
        session.save()

        response = self.client.get(
            "/accounts/google-callback/",
            {"state": "wrong-state", "code": "test-code"},
        )

        self.assertRedirects(response, "/doctor/dashboard/", fetch_redirect_response=False)
        flow_class.from_client_config.assert_not_called()
