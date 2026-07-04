"""Selenium UI test for profile update flow."""

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as expected
from selenium.webdriver.support.ui import WebDriverWait


def test_user_can_update_profile_end_to_end(live_server, browser, seed_user, login_as, safe_click):
    """A logged-in user should update editable profile details through the UI."""
    wait = WebDriverWait(browser, 10)

    user = seed_user(
        email="seleniumprofile@mymail.nyp.edu.sg",
        student_id="S66666666",
        display_name="Old Selenium Name",
    )

    login_as(user["email"])

    browser.get(f"{live_server}/profile/edit")

    display_name = wait.until(
        expected.presence_of_element_located((By.ID, "display_name"))
    )
    display_name.clear()
    display_name.send_keys("Updated Selenium User")

    contact_number = browser.find_element(By.ID, "contact_number")
    contact_number.clear()
    contact_number.send_keys("92345678")

    safe_click((By.CSS_SELECTOR, "button[type='submit']"))

    wait.until(expected.url_contains("/profile"))
    wait.until(lambda driver: "Updated Selenium User" in driver.page_source)
    assert "92345678" in browser.page_source