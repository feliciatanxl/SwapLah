"""Page object for listing detail page actions."""

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as expected

from tests.ui.selenium.pages.base_page import BasePage


class ListingDetailPage(BasePage):
    """Actions and checks for listing detail page."""

    CASH_OFFER_AMOUNT = (By.ID, "cash_offer_amount")
    SUBMIT_CASH = (By.ID, "submit-cash-btn")
    OFFER_FEEDBACK = (By.ID, "offer-feedback")
    CONFIRM_DELETE = (By.ID, "confirm-delete-btn")

    def open_listing(self, listing_id):
        """Open a listing detail page."""
        return self.open(f"/listing/{listing_id}")

    def submit_cash_offer(self, amount):
        """Submit a cash offer."""
        self.wait.until(
            expected.presence_of_element_located(self.CASH_OFFER_AMOUNT)
        ).send_keys(amount)
        self.safe_click(self.SUBMIT_CASH)
        return self

    def assert_cash_offer_success(self):
        """Assert that cash offer was submitted successfully."""
        feedback = self.find(self.OFFER_FEEDBACK)
        self.wait.until(
            lambda _driver: "Cash offer submitted successfully" in feedback.text
        )
        return self

    def soft_delete_listing(self):
        """Soft-delete the current listing."""
        confirm_delete = self.find(self.CONFIRM_DELETE)
        self.browser.execute_script("arguments[0].click();", confirm_delete)
        return self
