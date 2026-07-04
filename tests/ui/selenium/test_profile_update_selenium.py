"""Selenium UI test for profile update flow."""

from tests.ui.selenium.pages.login_page import LoginPage
from tests.ui.selenium.pages.profile_page import ProfilePage


def test_user_can_update_profile_end_to_end(live_server, browser, seed_user):
    """A logged-in user should update editable profile details through the UI."""
    user = seed_user(
        email="seleniumprofile@mymail.nyp.edu.sg",
        student_id="S66666666",
        display_name="Old Selenium Name",
    )

    LoginPage(browser, live_server).open_login().login(user["email"])

    ProfilePage(browser, live_server).open_edit_profile().update_profile(
        display_name="Updated Selenium User",
        contact_number="92345678",
    )

    ProfilePage(browser, live_server).assert_url_contains("/profile")
    ProfilePage(browser, live_server).assert_page_contains("Updated Selenium User")
    ProfilePage(browser, live_server).assert_page_contains("92345678")
