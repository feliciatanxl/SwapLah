"""Selenium UI test for viewing reviews on another user's public profile."""

from app import db as db_module
from tests.ui.selenium.pages.login_page import LoginPage
from tests.ui.selenium.pages.profile_page import ProfilePage


def test_viewer_sees_sellers_reviews_and_rating_on_public_profile(
    live_server, browser, seed_user, seed_listing
):
    """A logged-in viewer should see another user's rating, review count, and
    review comment on their public profile, with account controls hidden."""
    seller = seed_user(
        email="reviewedseller@mymail.nyp.edu.sg",
        student_id="S77777777",
        display_name="Reviewed Seller",
    )
    buyer = seed_user(
        email="reviewbuyer@mymail.nyp.edu.sg",
        student_id="S77777778",
        display_name="Review Buyer",
    )
    listing = seed_listing(seller["id"], title="Selenium Reviewed Item")
    offer = db_module.create_offer(listing["id"], buyer["id"], "cash", proposed_price=10.00)
    db_module.accept_offer(offer["id"])
    db_module.create_review(
        offer_id=offer["id"],
        reviewer_id=buyer["id"],
        reviewed_user_id=seller["id"],
        rating=5,
        comment="Smooth Selenium trade",
    )

    LoginPage(browser, live_server).open_login().login(buyer["email"])

    profile_page = ProfilePage(browser, live_server).open_profile_for(seller["id"])

    profile_page.assert_page_contains("Reviewed Seller")
    profile_page.assert_page_contains("Smooth Selenium trade")
    profile_page.assert_page_contains("1 review")
    profile_page.assert_page_not_contains("Edit profile")
