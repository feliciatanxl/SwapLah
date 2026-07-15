"""Page object for the Edit Listing page."""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select

from tests.ui.selenium.pages.base_page import BasePage


class EditListingPage(BasePage):
    """Actions and checks for editing an existing listing."""

    TITLE = (By.ID, "title")
    DESCRIPTION = (By.ID, "description")
    PRICE = (By.ID, "price")
    PRICE_TYPE_SET = (By.ID, "price_type_set")
    CATEGORY = (By.ID, "category")
    CONDITION = (By.ID, "condition")
    IMAGE_URL = (By.ID, "image_url")
    SUBMIT = (By.CSS_SELECTOR, "#edit-listing-form button[type='submit']")

    def open_edit_listing(self, listing_id):
        """Open the edit page for a listing."""
        self.open(f"/listing/{listing_id}/edit")
        self.find(self.TITLE)
        return self

    def update_listing(
        self,
        title,
        description,
        price,
        category,
        condition,
    ):
        """Update listing fields and submit the edit form."""
        self.enter_text(self.TITLE, title, clear=True)
        self.enter_text(self.DESCRIPTION, description, clear=True)

        # Keep the test on the normal numeric-price flow.
        self.safe_click(self.PRICE_TYPE_SET)
        self.enter_text(self.PRICE, price, clear=True)

        Select(self.find(self.CATEGORY)).select_by_visible_text(category)
        Select(self.find(self.CONDITION)).select_by_visible_text(condition)

        # Existing listing images are loaded by JavaScript into this hidden input.
        self.wait.until(
            lambda driver: driver.find_element(*self.IMAGE_URL).get_attribute("value")
        )

        self.safe_click(self.SUBMIT)
        return self
