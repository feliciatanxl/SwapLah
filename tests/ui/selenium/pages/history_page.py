"""Page object for the transaction history page."""

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as expected
from selenium.webdriver.support.ui import Select

from tests.ui.selenium.pages.base_page import BasePage


class HistoryPage(BasePage):
    """Actions and checks for the transaction history page."""

    SELLING_TAB = (By.CSS_SELECTOR, "button[data-bs-target='#seller-history']")
    SELLER_PANEL = (By.ID, "seller-history")
    SELLER_TABLE_CARD = (By.ID, "sellerTableCard")
    SELLER_EMPTY_STATE = (By.ID, "sellerEmptyState")
    SELLER_TRANSACTION_ROWS = (By.CSS_SELECTOR, "#sellerHistoryBody tr")
    SELLER_REVIEW_BUTTON = (By.CSS_SELECTOR, "#sellerHistoryBody .review-btn")
    RATING_SELECT = (By.ID, "reviewRating")
    COMMENT_TEXTAREA = (By.ID, "reviewComment")
    CONFIRM_REVIEW_BUTTON = (By.ID, "confirmReviewBtn")
    REVIEWED_BADGE = (By.CSS_SELECTOR, "#sellerHistoryBody .status-badge")
    HISTORY_FLASH = (By.ID, "historyFlash")

    def open_history(self):
        """Open the transaction history page."""
        return self.open("/history")

    def switch_to_selling_tab(self):
        """Switch to Selling History and wait for its asynchronous state."""
        return self.switch_to_selling_tab_and_wait()

    def switch_to_selling_tab_and_wait(self):
        """Activate Selling History and wait for its table or empty state."""
        self.click(self.SELLING_TAB)
        self.wait.until(
            lambda driver: "active" in driver.find_element(
                *self.SELLER_PANEL
            ).get_attribute("class").split()
        )
        self.wait_for_history_loaded("seller")
        return self

    def wait_for_history_loaded(self, role):
        """Wait until one role has rendered either transactions or empty state."""
        states = {
            "seller": (self.SELLER_TABLE_CARD, self.SELLER_EMPTY_STATE),
        }
        if role not in states:
            raise ValueError("role must be 'seller'")

        table_card, empty_state = states[role]
        self.wait.until(expected.any_of(
            expected.visibility_of_element_located(table_card),
            expected.visibility_of_element_located(empty_state),
        ))
        return self

    def wait_for_selling_transactions(self):
        """Wait until at least one completed sale row has rendered."""
        self.wait.until(expected.visibility_of_element_located(self.SELLER_TABLE_CARD))
        self.wait.until(expected.presence_of_all_elements_located(
            self.SELLER_TRANSACTION_ROWS
        ))
        return self

    @staticmethod
    def _row_with_title(driver, title):
        """Return the visible seller row whose item title exactly matches title."""
        for row in driver.find_elements(By.CSS_SELECTOR, "#sellerHistoryBody tr"):
            titles = row.find_elements(By.CSS_SELECTOR, "td:first-child strong")
            if titles and titles[0].is_displayed() and titles[0].text.strip() == title:
                return row
        return False

    def wait_for_transaction_title(self, title):
        """Wait for an exact listing title in the rendered Selling table."""
        self.wait_for_selling_transactions()
        self.wait.until(lambda driver: self._row_with_title(driver, title))
        return self

    def wait_for_review_action(self, title):
        """Wait until the named sale offers an enabled review action."""
        def review_button(driver):
            row = self._row_with_title(driver, title)
            if not row:
                return False
            buttons = row.find_elements(By.CSS_SELECTOR, ".review-btn")
            return buttons[0] if buttons and buttons[0].is_enabled() else False

        self.wait.until(review_button)
        return self

    def open_review_modal_for_sale(self, title):
        """Open the review modal for the sale with the exact listing title."""
        def review_button(driver):
            row = self._row_with_title(driver, title)
            if not row:
                return False
            buttons = row.find_elements(By.CSS_SELECTOR, ".review-btn")
            return buttons[0] if buttons else False

        button = self.wait.until(review_button)
        self.browser.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", button
        )
        self.browser.execute_script("arguments[0].click();", button)
        self.wait.until(expected.visibility_of_element_located(self.RATING_SELECT))
        return self

    def open_review_modal_for_first_sale(self):
        """Click 'Leave a review' on the first completed sale and wait for the modal."""
        self.safe_click(self.SELLER_REVIEW_BUTTON)
        self.wait.until(expected.visibility_of_element_located(self.RATING_SELECT))
        return self

    def submit_review(self, rating, comment=""):
        """Choose a rating, enter a comment, and submit the review modal."""
        Select(self.find(self.RATING_SELECT)).select_by_value(str(rating))

        if comment:
            self.enter_text(self.COMMENT_TEXTAREA, comment, clear=True)

        self.safe_click(self.CONFIRM_REVIEW_BUTTON)
        return self

    def wait_for_review_success(self):
        """Wait until the history page confirms a successful review."""
        flash = self.wait.until(expected.visibility_of_element_located(self.HISTORY_FLASH))
        self.wait.until(lambda _driver: "Review submitted successfully" in flash.text)
        return self

    def wait_for_transaction_reviewed(self, title):
        """Wait until the named transaction has a persistent Reviewed badge."""
        def reviewed_badge(driver):
            row = self._row_with_title(driver, title)
            if not row:
                return False
            badges = row.find_elements(By.CSS_SELECTOR, ".status-badge")
            return badges[0] if badges and badges[0].text.strip() == "Reviewed" else False

        self.wait.until(reviewed_badge)
        return self
