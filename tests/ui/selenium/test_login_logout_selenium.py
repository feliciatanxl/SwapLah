"""Selenium UI test for login, protected profile access, and logout."""

from tests.ui.selenium.pages.login_page import LoginPage
from tests.ui.selenium.pages.profile_page import ProfilePage


def test_user_can_login_view_profile_and_logout(live_server, browser, seed_user):
    """A user should log in, view profile, log out, and lose protected access."""
    user = seed_user(
        email="seleniumlogin@mymail.nyp.edu.sg",
        student_id="S77777777",
        display_name="Selenium Login",
    )

    ProfilePage(browser, live_server).open_profile()
    LoginPage(browser, live_server).assert_login_page_opened()

    LoginPage(browser, live_server).open_login().login(user["email"])
    ProfilePage(browser, live_server).assert_page_contains("Selenium Login")

    ProfilePage(browser, live_server).logout()
    LoginPage(browser, live_server).assert_login_page_opened()
    LoginPage(browser, live_server).assert_page_contains("You have been logged out")

    ProfilePage(browser, live_server).open_profile()
    LoginPage(browser, live_server).assert_login_page_opened()
