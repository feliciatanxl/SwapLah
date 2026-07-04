"""Selenium UI test for listing search, filters, and individual clear buttons."""

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as expected
from selenium.webdriver.support.ui import WebDriverWait


def test_buyer_can_search_filter_and_clear_listing_filters(
    live_server,
    browser,
    seed_user,
    seed_listing,
    safe_click,
):
    """A buyer should search, filter, and clear category/condition individually."""
    wait = WebDriverWait(browser, 10)

    seller = seed_user(
        email="seleniumfilter@mymail.nyp.edu.sg",
        student_id="S55555555",
        display_name="Filter Seller",
    )

    seed_listing(
        seller_id=seller["id"],
        title="Selenium Laptop Charger",
        description="USB-C laptop charger for testing search filters.",
        category="Electronics",
        condition="Like New",
    )
    seed_listing(
        seller_id=seller["id"],
        title="Selenium Python Textbook",
        description="Programming book for filter negative case.",
        category="Textbooks",
        condition="Good",
    )

    browser.get(
        f"{live_server}/?search=laptop&category=Electronics"
        "&condition=Like+New#latest-listings"
    )

    wait.until(lambda driver: "Selenium Laptop Charger" in driver.page_source)
    assert "Selenium Python Textbook" not in browser.page_source

    safe_click((By.CSS_SELECTOR, "[aria-label='Clear category filter']"))

    wait.until(lambda driver: "condition=Like+New" in driver.current_url)
    assert "category=Electronics" not in browser.current_url

    browser.get(
        f"{live_server}/?search=laptop&category=Electronics"
        "&condition=Like+New#latest-listings"
    )

    wait.until(expected.presence_of_element_located((By.ID, "condition")))
    safe_click((By.CSS_SELECTOR, "[aria-label='Clear condition filter']"))

    wait.until(lambda driver: "category=Electronics" in driver.current_url)
    assert "condition=Like+New" not in browser.current_url