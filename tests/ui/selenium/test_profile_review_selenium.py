"""Selenium UI test for viewing a profile and leaving a review from history."""

from app.db import accept_offer, create_offer

from tests.ui.selenium.pages.history_page import HistoryPage
from tests.ui.selenium.pages.login_page import LoginPage
from tests.ui.selenium.pages.profile_page import ProfilePage


def _seed_completed_deal(seed_user, seed_listing):
    """Seed a seller, buyer, listing, and an accepted offer. Returns (seller, buyer)."""
    seller = seed_user(
        email="seleniumsellerreview@mymail.nyp.edu.sg",
        student_id="S77777771",
        display_name="Selenium Seller",
    )
    buyer = seed_user(
        email="seleniumbuyerreview@mymail.nyp.edu.sg",
        student_id="S77777772",
        display_name="Selenium Buyer",
    )
    listing = seed_listing(
        seller_id=seller["id"],
        title="Selenium Review Test Item",
    )

    offer = create_offer(
        listing_id=listing["id"],
        buyer_id=buyer["id"],
        offer_type="cash",
        proposed_price=20.0,
    )
    accept_offer(offer["id"])

    return seller, buyer


def test_user_can_view_another_users_profile(live_server, browser, seed_user, seed_listing):
    """A logged-in user should be able to view another user's public profile."""
    seller, buyer = _seed_completed_deal(seed_user, seed_listing)

    LoginPage(browser, live_server).open_login().login(buyer["email"])

    profile_page = ProfilePage(browser, live_server)
    profile_page.open_profile_for(seller["id"])

    profile_page.assert_page_contains(seller["display_name"])
    profile_page.assert_page_not_contains("Edit profile")
    profile_page.assert_page_not_contains("Account Details")


def test_seller_can_leave_review_for_buyer_from_history(
    live_server, browser, seed_user, seed_listing,
):
    """A seller should submit a rating and comment for a completed sale."""
    seller, _buyer = _seed_completed_deal(seed_user, seed_listing)
    listing_title = "Selenium Review Test Item"

    LoginPage(browser, live_server).open_login().login(seller["email"])

    history_page = HistoryPage(browser, live_server)
    history_page.open_history()
    history_page.switch_to_selling_tab_and_wait()
    history_page.wait_for_transaction_title(listing_title)
    history_page.wait_for_review_action(listing_title)

    history_page.open_review_modal_for_sale(listing_title)
    history_page.submit_review(rating=5, comment="Smooth handover, would trade again.")

    history_page.wait_for_review_success()
    history_page.wait_for_transaction_reviewed(listing_title)

    browser.refresh()
    history_page.switch_to_selling_tab_and_wait()
    history_page.wait_for_transaction_title(listing_title)
    history_page.wait_for_transaction_reviewed(listing_title)
