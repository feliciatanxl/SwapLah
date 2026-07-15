"""Selenium UI test for suspended user login rejection."""

from tests.ui.selenium.pages.login_page import LoginPage


def test_suspended_user_cannot_login_end_to_end(live_server, browser, seed_user):
    """A suspended user should be blocked from logging in through the UI."""
    suspended_user = seed_user(
        email="seleniumsuspended@mymail.nyp.edu.sg",
        student_id="S22222222",
        display_name="Suspended Selenium",
        status="Suspended",
    )

    login_page = LoginPage(browser, live_server)
    login_page.open_login().attempt_login(suspended_user["email"])

    login_page.assert_login_page_opened()
    login_page.assert_page_contains("Your account has been suspended")
