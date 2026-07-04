"""Selenium UI test for user registration."""

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as expected
from selenium.webdriver.support.ui import WebDriverWait


def test_user_can_register_account_end_to_end(live_server, browser, safe_click):
    """A new user should be able to register through the browser UI."""
    wait = WebDriverWait(browser, 10)

    browser.get(f"{live_server}/register")

    wait.until(expected.presence_of_element_located((By.ID, "student_id"))).send_keys(
        "S88888888"
    )
    browser.find_element(By.ID, "email").send_keys(
        "seleniumregister@mymail.nyp.edu.sg"
    )
    browser.find_element(By.ID, "first_name").send_keys("Selenium")
    browser.find_element(By.ID, "last_name").send_keys("Register")
    browser.find_element(By.ID, "display_name").send_keys("Selenium Register")
    browser.find_element(By.ID, "contact_number").send_keys("91234567")
    browser.find_element(By.ID, "password").send_keys("Password123")
    browser.find_element(By.ID, "confirm_password").send_keys("Password123")

    safe_click((By.CSS_SELECTOR, "button[type='submit']"))

    wait.until(expected.url_contains("/login"))
    assert "Account created successfully" in browser.page_source