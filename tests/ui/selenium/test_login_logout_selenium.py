"""Selenium UI test for login, protected profile access, and logout."""

from selenium.webdriver.support import expected_conditions as expected
from selenium.webdriver.support.ui import WebDriverWait


def test_user_can_login_view_profile_and_logout(live_server, browser, seed_user, login_as):
    """A user should log in, view profile, log out, and lose protected access."""
    wait = WebDriverWait(browser, 10)

    user = seed_user(
        email="seleniumlogin@mymail.nyp.edu.sg",
        student_id="S77777777",
        display_name="Selenium Login",
    )

    browser.get(f"{live_server}/profile")
    wait.until(expected.url_contains("/login"))

    login_as(user["email"])

    wait.until(lambda driver: "Selenium Login" in driver.page_source)

    browser.get(f"{live_server}/logout")
    wait.until(expected.url_contains("/login"))
    assert "You have been logged out" in browser.page_source

    browser.get(f"{live_server}/profile")
    wait.until(expected.url_contains("/login"))