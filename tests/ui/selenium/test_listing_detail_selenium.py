"""Selenium UI test for the complete buyer listing-detail flow."""

from selenium.webdriver.common.by import By

from tests.ui.selenium.pages.listing_detail_page import ListingDetailPage
from tests.ui.selenium.pages.login_page import LoginPage


def test_buyer_can_view_complete_listing_and_seller_details(
    live_server,
    browser,
    seed_user,
    seed_listing,
):
    """A buyer should see item details and the seller's contact information."""
    seller = seed_user(
        email="detail.seller@mymail.nyp.edu.sg",
        student_id="S66666666",
        display_name="Detail Seller",
        contact_number="92345678",
    )
    buyer = seed_user(
        email="detail.buyer@mymail.nyp.edu.sg",
        student_id="S77777777",
        display_name="Detail Buyer",
    )
    listing = seed_listing(
        seller_id=seller["id"],
        title="Selenium Detail Page Laptop",
        description="A complete listing used to verify buyer-visible information.",
        price="35.00",
        category="Electronics",
        condition="Like New",
    )

    LoginPage(browser, live_server).open_login().login(buyer["email"])

    listing_page = ListingDetailPage(browser, live_server)
    listing_page.open_listing(listing["id"])
    listing_page.assert_url_is(f"{live_server}/listing/{listing['id']}")

    listing_page.assert_page_contains("Selenium Detail Page Laptop")
    listing_page.assert_page_contains(
        "A complete listing used to verify buyer-visible information."
    )
    listing_page.assert_page_contains("35.00")
    listing_page.assert_page_contains("Electronics")
    listing_page.assert_page_contains("Like New")
    listing_page.assert_page_contains("Detail Seller")
    listing_page.assert_page_contains("detail.seller@mymail.nyp.edu.sg")
    listing_page.assert_page_contains("92345678")

    # A buyer can view the listing, but owner-only edit controls must stay hidden.
    assert not browser.find_elements(
        By.CSS_SELECTOR,
        f"a[href='/listing/{listing['id']}/edit']",
    )
