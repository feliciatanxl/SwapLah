"""Base page object shared by Selenium UI tests."""

from selenium.webdriver.support import expected_conditions as expected
from selenium.webdriver.support.ui import WebDriverWait


class BasePage:
    """Common browser actions for all Selenium page objects."""

    def __init__(self, browser, base_url):
        self.browser = browser
        self.base_url = base_url
        self.wait = WebDriverWait(browser, 10)

    def open(self, path):
        """Open a page path on the live test server."""
        self.browser.get(f"{self.base_url}{path}")
        return self

    def find(self, locator):
        """Wait for an element to exist and return it."""
        return self.wait.until(expected.presence_of_element_located(locator))

    def enter_text(self, locator, value, clear=False):
        """Enter text into a form field."""
        element = self.find(locator)

        if clear:
            element.clear()

        element.send_keys(value)
        return self

    def click(self, locator):
        """Click an element after it is clickable."""
        self.wait.until(expected.element_to_be_clickable(locator)).click()
        return self

    def safe_click(self, locator):
        """Scroll to an element and click it using JavaScript."""
        element = self.find(locator)
        self.browser.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            element,
        )
        self.browser.execute_script("arguments[0].click();", element)
        return self

    def assert_url_contains(self, text):
        """Assert that the current URL contains text."""
        self.wait.until(expected.url_contains(text))
        return self

    def assert_url_is(self, url):
        """Assert that the current URL exactly matches the expected URL."""
        self.wait.until(expected.url_to_be(url))
        return self

    def assert_page_contains(self, text):
        """Assert that page source contains text."""
        self.wait.until(lambda driver: text in driver.page_source)
        return self

    def assert_page_not_contains(self, text):
        """Assert that page source does not contain text."""
        assert text not in self.browser.page_source
        return self
