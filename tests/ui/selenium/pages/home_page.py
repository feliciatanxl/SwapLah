"""Page object for the homepage and listing filters."""

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

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

    def open_clear_filter_link(self, locator):
        """Open the clear-filter link href directly to avoid stale element errors."""
        filter_name = {
            self.CLEAR_CATEGORY: "category",
            self.CLEAR_CONDITION: "condition",
        }[locator]

        current_url = urlsplit(self.browser.current_url)
        query = urlencode(
            [
                (key, value)
                for key, value in parse_qsl(current_url.query, keep_blank_values=True)
                if key not in {filter_name, "page"} and value
            ]
        )
        href = urlunsplit(
            (
                current_url.scheme,
                current_url.netloc,
                current_url.path or "/",
                query,
                "latest-listings",
            )
        )

        assert href, "Clear filter link must have a href."

        self.browser.get(href)
        return self

    def clear_category_filter(self):
        """Clear only the category filter."""
        return self.open_clear_filter_link(self.CLEAR_CATEGORY)

    def clear_condition_filter(self):
        """Clear only the condition filter."""
        return self.open_clear_filter_link(self.CLEAR_CONDITION)

    def assert_url_has(self, text):
        """Assert that current URL contains text."""
        self.wait.until(lambda driver: text in driver.current_url)
        return self

    def assert_url_does_not_have(self, text):
        """Assert that current URL does not contain text."""
        assert text not in self.browser.current_url
        return self
