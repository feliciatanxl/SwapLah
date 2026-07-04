"""Selenium UI test for seller soft-delete listing flow."""

from tests.ui.selenium.pages.listing_detail_page import ListingDetailPage
from tests.ui.selenium.pages.login_page import LoginPage


def test_seller_can_soft_delete_own_listing_end_to_end(
    live_server,
    browser,
    seed_user,
    seed_listing,
):
    """A seller should soft-delete their own listing from the detail page."""
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

    LoginPage(browser, live_server).open_login().login(seller["email"])

    listing_page = ListingDetailPage(browser, live_server)
    listing_page.open_listing(listing["id"])
    listing_page.assert_page_contains("Selenium Soft Delete Listing")
    listing_page.soft_delete_listing()
    listing_page.assert_url_is(f"{live_server}/")

    listing_page.open_listing(listing["id"])
    listing_page.assert_page_contains("does not exist or is no longer available")
