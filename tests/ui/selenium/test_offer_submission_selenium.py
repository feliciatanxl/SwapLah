"""Selenium UI test for cash offer submission flow."""

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as expected
from selenium.webdriver.support.ui import WebDriverWait


def test_buyer_can_submit_cash_offer_end_to_end(
    live_server,
    browser,
    seed_user,
    seed_listing,
    login_as,
    safe_click,
):
    """A buyer should submit a cash offer on another seller's listing."""
    wait = WebDriverWait(browser, 10)

    seller = seed_user(
        email="seleniumofferseller@mymail.nyp.edu.sg",
        student_id="S44444441",
        display_name="Offer Seller",
    )
    buyer = seed_user(
        email="seleniumofferbuyer@mymail.nyp.edu.sg",
        student_id="S44444442",
        display_name="Offer Buyer",
    )
    listing = seed_listing(
        seller_id=seller["id"],
        title="Selenium Offer Textbook",
        description="Listing used for Selenium cash offer flow.",
        price="20.00",
        category="Textbooks",
        condition="Good",
    )

    login_as(buyer["email"])

    browser.get(f"{live_server}/listing/{listing['id']}")

    wait.until(lambda driver: "Selenium Offer Textbook" in driver.page_source)
    wait.until(
        expected.presence_of_element_located((By.ID, "cash_offer_amount"))
    ).send_keys("18.50")

    safe_click((By.ID, "submit-cash-btn"))

    feedback = wait.until(
        expected.presence_of_element_located((By.ID, "offer-feedback"))
    )
    wait.until(lambda driver: "Cash offer submitted successfully" in feedback.text)