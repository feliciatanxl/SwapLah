"""Page object for the login page."""

from selenium.webdriver.common.by import By

from tests.ui.selenium.pages.base_page import BasePage


class LoginPage(BasePage):
    """Actions and checks for the login page."""

    EMAIL = (By.ID, "login_email")
    PASSWORD = (By.ID, "login_password")
    SUBMIT = (By.CSS_SELECTOR, "button[type='submit']")

    def open_login(self):
        """Open the login page."""
        return self.open("/login")

    def login(self, email, password="Password123"):
        """Log in using the browser UI and wait until session is created."""
        self.enter_text(self.EMAIL, email)
        self.enter_text(self.PASSWORD, password)
        self.click(self.SUBMIT)
        self.assert_url_contains("/profile")
        return self

    def assert_login_page_opened(self):
        """Assert that the browser is on the login page."""
        return self.assert_url_contains("/login")

    def attempt_login(self, email, password="Password123"):
        """Submit login form without expecting successful redirect."""
        self.enter_text(self.EMAIL, email)
        self.enter_text(self.PASSWORD, password)
        self.click(self.SUBMIT)
        return self
