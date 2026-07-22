"""Selenium UI test for user registration."""

from tests.ui.selenium.pages.register_page import RegisterPage


def test_user_can_register_account_end_to_end(live_server, browser):
    """A new user should be able to register through the browser UI."""
    RegisterPage(browser, live_server).open_register().register(
        student_id="S88888888",
        email="seleniumregister@mymail.nyp.edu.sg",
        first_name="Selenium",
        last_name="Register",
        display_name="Selenium Register",
        contact_number="91234567",
        password="Password123",
        confirm_password="Password123",
    ).assert_registration_success()
