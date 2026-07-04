"""Selenium UI test for end-to-end listing creation."""

import base64
import threading

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as expected
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from werkzeug.security import generate_password_hash
from werkzeug.serving import make_server

from app import create_app
from app import db as db_module


TEST_EMAIL = "uitestuser@mymail.nyp.edu.sg"
TEST_PASSWORD = "Password123"
TEST_TITLE = "Selenium Listing Creation Test"


def create_ui_test_user():
    """Insert one active user for the Selenium login flow."""
    conn = db_module.get_db_connection()
    conn.execute(
        """
        INSERT INTO users (
            student_id, first_name, last_name, display_name,
            email, contact_number, password_hash, role, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "S99999999",
            "UI",
            "Tester",
            "UI Tester",
            TEST_EMAIL,
            "91234567",
            generate_password_hash(TEST_PASSWORD),
            "user",
            "Active",
        ),
    )
    conn.commit()
    conn.close()


@pytest.fixture()
def live_app(tmp_path, monkeypatch):
    """Create a Flask app using an isolated SQLite database."""
    monkeypatch.setattr(db_module, "DATABASE", tmp_path / "ui_test.db")

    app = create_app()
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "ui-test-secret"

    create_ui_test_user()

    return app


@pytest.fixture()
def live_server(live_app):
    """Run the Flask app in a background server for Selenium."""
    server = make_server("127.0.0.1", 0, live_app)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    yield f"http://127.0.0.1:{server.server_port}"

    server.shutdown()
    server_thread.join(timeout=5)


@pytest.fixture()
def browser():
    """Create a headless Chrome browser for Selenium tests."""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--force-device-scale-factor=1")

    driver = webdriver.Chrome(service=Service(), options=options)

    yield driver

    driver.quit()


@pytest.fixture()
def listing_image(tmp_path):
    """Create a small PNG file for the listing image upload."""
    image_bytes = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8"
        "/x8AAwMB/6X7pfsAAAAASUVORK5CYII="
    )
    image_path = tmp_path / "listing-test-image.png"
    image_path.write_bytes(image_bytes)
    return image_path


def test_seller_can_create_listing_end_to_end(live_server, browser, listing_image):
    """Seller should log in and create a listing through the browser UI."""
    wait = WebDriverWait(browser, 10)

    browser.get(f"{live_server}/login")

    wait.until(expected.presence_of_element_located((By.ID, "login_email"))).send_keys(
        TEST_EMAIL
    )
    browser.find_element(By.ID, "login_password").send_keys(TEST_PASSWORD)
    browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    wait.until(expected.url_contains("/profile"))

    browser.get(f"{live_server}/sell")

    wait.until(expected.presence_of_element_located((By.ID, "title"))).send_keys(
        TEST_TITLE
    )
    browser.find_element(By.ID, "description").send_keys(
        "Created through Selenium end-to-end UI test."
    )
    browser.find_element(By.ID, "price").send_keys("12.50")
    browser.find_element(By.ID, "pickup_location").send_keys("NYP Library")
    Select(browser.find_element(By.ID, "category")).select_by_visible_text("Electronics")
    Select(browser.find_element(By.ID, "condition")).select_by_visible_text("Like New")

    browser.find_element(By.ID, "image_file").send_keys(str(listing_image))

    wait.until(
        lambda driver: driver.find_element(By.ID, "image_url").get_attribute("value")
    )

    submit_button = wait.until(
        expected.presence_of_element_located((By.CSS_SELECTOR, "button[type='submit']"))
    )

    browser.execute_script(
        "arguments[0].scrollIntoView({block: 'center'});",
        submit_button,
    )

    wait.until(expected.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))

    browser.execute_script("arguments[0].click();", submit_button)

    wait.until(expected.url_to_be(f"{live_server}/"))
    wait.until(lambda driver: TEST_TITLE in driver.page_source)