"""Selenium UI test for the complete edit-listing owner flow."""

from app.db import get_listing_by_id
from tests.ui.selenium.pages.edit_listing_page import EditListingPage
from tests.ui.selenium.pages.listing_detail_page import ListingDetailPage
from tests.ui.selenium.pages.login_page import LoginPage


def test_seller_can_edit_own_listing_end_to_end(
    live_server,
    browser,
    seed_user,
    seed_listing,
):
    """An owner should edit a listing and see the saved changes."""
    seller = seed_user(
        email="seleniumedit@mymail.nyp.edu.sg",
        student_id="S44444444",
        display_name="Edit Seller",
    )
    listing = seed_listing(
        seller_id=seller["id"],
        title="Original Selenium Listing",
        description="Original description before the Selenium edit.",
        price="10.00",
        category="Electronics",
        condition="Good",
    )

    updated_title = "Updated Selenium Listing"
    updated_description = "Updated successfully through the owner edit flow."

    LoginPage(browser, live_server).open_login().login(seller["email"])

    edit_page = EditListingPage(browser, live_server)
    edit_page.open_edit_listing(listing["id"])
    edit_page.update_listing(
        title=updated_title,
        description=updated_description,
        price="28.50",
        category="Textbooks",
        condition="Like New",
    )

    detail_page = ListingDetailPage(browser, live_server)
    detail_page.assert_url_is(f"{live_server}/listing/{listing['id']}")
    detail_page.assert_page_contains(updated_title)
    detail_page.assert_page_contains(updated_description)
    detail_page.assert_page_contains("28.50")
    detail_page.assert_page_contains("Textbooks")
    detail_page.assert_page_contains("Like New")
    detail_page.assert_page_not_contains("Original Selenium Listing")

    saved_listing = get_listing_by_id(listing["id"])
    assert saved_listing is not None
    assert saved_listing["title"] == updated_title
    assert saved_listing["description"] == updated_description
    assert saved_listing["price"] == "28.50"
    assert saved_listing["category"] == "Textbooks"
    assert saved_listing["condition"] == "Like New"
