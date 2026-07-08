"""Page object for profile and edit profile pages."""

from selenium.webdriver.common.by import By

from tests.ui.selenium.pages.base_page import BasePage


class ProfilePage(BasePage):
    """Actions and checks for profile pages."""

    DISPLAY_NAME = (By.ID, "display_name")
    CONTACT_NUMBER = (By.ID, "contact_number")
    SUBMIT = (By.CSS_SELECTOR, "button[type='submit']")

    def open_profile(self):
        """Open the profile page."""
        return self.open("/profile")

    def open_edit_profile(self):
        """Open the edit profile page."""
        return self.open("/profile/edit")

    def update_profile(self, display_name, contact_number):
        """Update editable profile details."""
        self.enter_text(self.DISPLAY_NAME, display_name, clear=True)
        self.enter_text(self.CONTACT_NUMBER, contact_number, clear=True)
        self.safe_click(self.SUBMIT)
        return self

    def logout(self):
        """Log out through the logout route."""
        return self.open("/logout")
