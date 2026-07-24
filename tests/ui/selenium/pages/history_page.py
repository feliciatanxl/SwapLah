"""Page object for the transaction history page."""

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as expected
from selenium.webdriver.support.ui import Select

from tests.ui.selenium.pages.base_page import BasePage


class HistoryPage(BasePage):
    """Actions and checks for the transaction history page."""

    SELLING_TAB = (By.CSS_SELECTOR, "button[data-bs-target='#seller-history']")
    SELLER_REVIEW_BUTTON = (By.CSS_SELECTOR, "#sellerHistoryBody .review-btn")
    RATING_SELECT = (By.ID, "reviewRating")
    COMMENT_TEXTAREA = (By.ID, "reviewComment")
    CONFIRM_REVIEW_BUTTON = (By.ID, "confirmReviewBtn")
    REVIEWED_BADGE = (By.CSS_SELECTOR, "#sellerHistoryBody .status-badge")

    def open_history(self):
        """Open the transaction history page."""
        return self.open("/history")

    def switch_to_selling_tab(self):
        """Switch to the Selling History tab."""
        self.click(self.SELLING_TAB)
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
