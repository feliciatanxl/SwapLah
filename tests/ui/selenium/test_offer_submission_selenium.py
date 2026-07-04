"""Selenium UI test for cash offer submission flow."""

from tests.ui.selenium.pages.listing_detail_page import ListingDetailPage
from tests.ui.selenium.pages.login_page import LoginPage


def test_buyer_can_submit_cash_offer_end_to_end(
    live_server,
    browser,
    seed_user,
    seed_listing,
):
    """A buyer should submit a cash offer on another seller's listing."""
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

    LoginPage(browser, live_server).open_login().login(buyer["email"])

    listing_page = ListingDetailPage(browser, live_server)
    listing_page.open_listing(listing["id"])
    listing_page.assert_page_contains("Selenium Offer Textbook")
    listing_page.submit_cash_offer("18.50").assert_cash_offer_success()
