"""Page object for the registration page."""

# pylint: disable=too-many-arguments,too-many-positional-arguments

from selenium.webdriver.common.by import By

from tests.ui.selenium.pages.base_page import BasePage


class RegisterPage(BasePage):
    """Actions and checks for the registration page."""

    STUDENT_ID = (By.ID, "student_id")
    EMAIL = (By.ID, "email")
    FIRST_NAME = (By.ID, "first_name")
    LAST_NAME = (By.ID, "last_name")
    DISPLAY_NAME = (By.ID, "display_name")
    CONTACT_NUMBER = (By.ID, "contact_number")
    PASSWORD = (By.ID, "password")
    CONFIRM_PASSWORD = (By.ID, "confirm_password")
    SUBMIT = (By.CSS_SELECTOR, "button[type='submit']")

    def open_register(self):
        """Open the registration page."""
        return self.open("/register")

    def register(
        self,
        student_id,
        email,
        first_name,
        last_name,
        display_name,
        contact_number,
        password,
        confirm_password,
    ):
        """Register a new account through the browser UI."""
        self.enter_text(self.STUDENT_ID, student_id)
        self.enter_text(self.EMAIL, email)
        self.enter_text(self.FIRST_NAME, first_name)
        self.enter_text(self.LAST_NAME, last_name)
        self.enter_text(self.DISPLAY_NAME, display_name)
        self.enter_text(self.CONTACT_NUMBER, contact_number)
        self.enter_text(self.PASSWORD, password)
        self.enter_text(self.CONFIRM_PASSWORD, confirm_password)
        self.safe_click(self.SUBMIT)
        return self

    def assert_registration_success(self):
        """Assert that successful registration redirects to login."""
        self.assert_url_contains("/login")
        return self.assert_page_contains("Account created successfully")
