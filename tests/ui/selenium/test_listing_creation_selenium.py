"""Selenium UI test for end-to-end listing creation."""

from tests.ui.selenium.pages.home_page import HomePage
from tests.ui.selenium.pages.login_page import LoginPage
from tests.ui.selenium.pages.sell_page import SellPage


def test_seller_can_create_listing_end_to_end(
    live_server,
    browser,
    seed_user,
    listing_image,
):
    """Seller should log in and create a listing through the browser UI."""
    test_title = "Selenium Listing Creation Test"
    user = seed_user(
        email="uitestuser@mymail.nyp.edu.sg",
        student_id="S99999999",
        display_name="UI Tester",
    )

    LoginPage(browser, live_server).open_login().login(user["email"])
    LoginPage(browser, live_server).assert_url_contains("/profile")

    SellPage(browser, live_server).open_sell().create_listing(
        title=test_title,
        description="Created through Selenium end-to-end UI test.",
        price="12.50",
        pickup_location="NYP Library",
        image_path=listing_image,
    )

    HomePage(browser, live_server).assert_url_is(f"{live_server}/")
    HomePage(browser, live_server).assert_page_contains(test_title)
