"""Selenium UI test for listing search, filters, and individual clear buttons."""

from tests.ui.selenium.pages.home_page import HomePage
from tests.ui.selenium.pages.login_page import LoginPage


def test_buyer_can_search_filter_and_clear_listing_filters(
    live_server,
    browser,
    seed_user,
    seed_listing,
):
    """A buyer should search, filter, and clear category/condition individually."""
    seller = seed_user(
        email="seleniumfilter@mymail.nyp.edu.sg",
        student_id="S55555555",
        display_name="Filter Seller",
    )
    buyer = seed_user(
        email="seleniumfilterbuyer@mymail.nyp.edu.sg",
        student_id="S55555556",
        display_name="Filter Buyer",
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

    LoginPage(browser, live_server).open_login().login(buyer["email"])

    home_page = HomePage(browser, live_server)
    home_page.open_with_filters("laptop", "Electronics", "Like+New")
    home_page.assert_page_contains("Selenium Laptop Charger")
    home_page.assert_page_not_contains("Selenium Python Textbook")

    home_page.clear_category_filter()
    home_page.assert_url_has("condition=Like+New")
    home_page.assert_url_does_not_have("category=Electronics")

    home_page.open_with_filters("laptop", "Electronics", "Like+New")
    home_page.clear_condition_filter()
    home_page.assert_url_has("category=Electronics")
    home_page.assert_url_does_not_have("condition=Like+New")
