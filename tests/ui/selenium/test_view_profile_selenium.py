"""Selenium UI test for viewing another user's public profile."""

from app.db import create_review

from tests.ui.selenium.pages.login_page import LoginPage
from tests.ui.selenium.pages.profile_page import ProfilePage


def test_user_can_view_another_users_profile_and_rating(live_server, browser, seed_user):
    """A logged-in user should view another user's profile, rating, and reviews."""
    seller = seed_user(
        email="seleniumviewseller@mymail.nyp.edu.sg",
        student_id="S88888881",
        display_name="Selenium Seller",
    )
    viewer = seed_user(
        email="seleniumviewer@mymail.nyp.edu.sg",
        student_id="S88888882",
        display_name="Selenium Viewer",
    )

    create_review(
        reviewer_id=viewer["id"],
        reviewed_user_id=seller["id"],
        rating=5,
        comment="Smooth handover, would trade again.",
    )

    LoginPage(browser, live_server).open_login().login(viewer["email"])

    profile_page = ProfilePage(browser, live_server)
    profile_page.open_profile_for(seller["id"])

    profile_page.assert_page_contains(seller["display_name"])
    profile_page.assert_page_contains("Smooth handover, would trade again.")
    profile_page.assert_page_contains("Reviews (1)")
    profile_page.assert_page_not_contains("Edit profile")
    profile_page.assert_page_not_contains("Account Details")
