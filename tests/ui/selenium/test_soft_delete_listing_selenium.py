"""Selenium UI test for seller soft-delete listing flow."""

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By


def test_seller_can_soft_delete_own_listing_end_to_end(
    live_server,
    browser,
    seed_user,
    seed_listing,
    login_as,
):
    """A seller should soft-delete their own listing from the detail page."""
    wait = WebDriverWait(browser, 10)

    seller = seed_user(
        email="seleniumdelete@mymail.nyp.edu.sg",
        student_id="S33333333",
        display_name="Delete Seller",
    )
    listing = seed_listing(
        seller_id=seller["id"],
        title="Selenium Soft Delete Listing",
        description="Listing used for Selenium soft-delete flow.",
        price="15.00",
        category="Electronics",
        condition="Good",
    )

    login_as(seller["email"])

    browser.get(f"{live_server}/listing/{listing['id']}")

    wait.until(lambda driver: "Selenium Soft Delete Listing" in driver.page_source)

    confirm_delete = browser.find_element(By.ID, "confirm-delete-btn")
    browser.execute_script("arguments[0].click();", confirm_delete)

    wait.until(lambda driver: driver.current_url == f"{live_server}/")

    browser.get(f"{live_server}/listing/{listing['id']}")

    wait.until(lambda driver: "does not exist or is no longer available" in driver.page_source)