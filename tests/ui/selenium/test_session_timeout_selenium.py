"""Selenium UI test for expired session redirect behaviour."""

from tests.ui.selenium.pages.login_page import LoginPage
from tests.ui.selenium.pages.profile_page import ProfilePage


def test_expired_session_redirects_to_login(live_app, live_server, browser, seed_user):
    """An expired browser session should redirect protected pages to login."""
    user = seed_user(
        email="seleniumexpired@mymail.nyp.edu.sg",
        student_id="S11111111",
        display_name="Expired Selenium",
    )

    browser.get(live_server)

    serializer = live_app.session_interface.get_signing_serializer(live_app)
    expired_session = serializer.dumps(
        {
            "user_id": user["id"],
            "email": user["email"],
            "display_name": user["display_name"],
            "role": "user",
            "last_activity": 0,
        }
    )

    browser.add_cookie(
        {
            "name": live_app.config["SESSION_COOKIE_NAME"],
            "value": expired_session,
        }
    )

    ProfilePage(browser, live_server).open_profile()
    LoginPage(browser, live_server).assert_login_page_opened()
    LoginPage(browser, live_server).assert_page_contains(
        "Session expired due to inactivity"
    )
