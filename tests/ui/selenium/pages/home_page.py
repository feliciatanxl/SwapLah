"""Page object for the homepage and listing filters."""

from selenium.webdriver.common.by import By

from tests.ui.selenium.pages.base_page import BasePage


class HomePage(BasePage):
    """Actions and checks for homepage listing search/filter UI."""

    CATEGORY = (By.ID, "category")
    CLEAR_CATEGORY = (By.CSS_SELECTOR, "[aria-label='Clear category filter']")
    CLEAR_CONDITION = (By.CSS_SELECTOR, "[aria-label='Clear condition filter']")

    def open_home(self):
        """Open the homepage."""
        return self.open("/")

    def open_with_filters(self, search, category, condition):
        """Open homepage with search, category, and condition filters."""
        path = (
            f"/?search={search}&category={category}"
            f"&condition={condition}#latest-listings"
        )
        return self.open(path)

    def clear_category_filter(self):
        """Clear only the category filter."""
        return self.safe_click(self.CLEAR_CATEGORY)

    def clear_condition_filter(self):
        """Clear only the condition filter."""
        self.find(self.CATEGORY)
        return self.safe_click(self.CLEAR_CONDITION)

    def assert_url_has(self, text):
        """Assert that current URL contains text."""
        self.wait.until(lambda driver: text in driver.current_url)
        return self

    def assert_url_does_not_have(self, text):
        """Assert that current URL does not contain text."""
        assert text not in self.browser.current_url
        return self
