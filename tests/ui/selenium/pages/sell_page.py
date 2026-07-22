"""Page object for the Sell listing page."""
# pylint: disable=too-many-positional-arguments

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as expected
from selenium.webdriver.support.select import Select

from tests.ui.selenium.pages.base_page import BasePage


class SellPage(BasePage):
    """Actions and checks for creating a listing."""

    TITLE = (By.ID, "title")
    DESCRIPTION = (By.ID, "description")
    PRICE = (By.ID, "price")
    PICKUP_LOCATION = (By.ID, "pickup_location")
    CATEGORY = (By.ID, "category")
    CONDITION = (By.ID, "condition")
    IMAGE_FILE = (By.ID, "image_file")
    IMAGE_URL = (By.ID, "image_url")
    SUBMIT = (By.CSS_SELECTOR, "button[type='submit']")

    def open_sell(self):
        """Open the sell listing page."""
        return self.open("/sell")

    def create_listing(self, title, description, price, pickup_location, image_path):
        """Fill and submit the create listing form."""
        self.enter_text(self.TITLE, title)
        self.enter_text(self.DESCRIPTION, description)
        self.enter_text(self.PRICE, price)
        self.enter_text(self.PICKUP_LOCATION, pickup_location)

        Select(self.find(self.CATEGORY)).select_by_visible_text("Electronics")
        Select(self.find(self.CONDITION)).select_by_visible_text("Like New")

        self.find(self.IMAGE_FILE).send_keys(str(image_path))
        self.wait.until(
            lambda driver: driver.find_element(*self.IMAGE_URL).get_attribute("value")
        )

        submit_button = self.find(self.SUBMIT)
        self.browser.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            submit_button,
        )
        self.wait.until(expected.element_to_be_clickable(self.SUBMIT))
        self.browser.execute_script("arguments[0].click();", submit_button)

        return self
