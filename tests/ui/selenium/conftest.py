"""Shared Selenium UI test fixtures and helpers."""
# pylint: disable=redefined-outer-name,too-many-arguments,too-many-positional-arguments

import base64
import os
import socket
import threading
import time
import urllib.request

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as expected
from selenium.webdriver.support.ui import WebDriverWait
from werkzeug.security import generate_password_hash
from werkzeug.serving import make_server

from app import create_app
from app import db as db_module
from app.db import create_listing


DEFAULT_PASSWORD = "Password123"
DEFAULT_IMAGE_URL = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8"
    "/x8AAwMB/6X7pfsAAAAASUVORK5CYII="
)


@pytest.fixture()
def live_app(tmp_path, monkeypatch):
    """Create a Flask app using an isolated SQLite database."""
    monkeypatch.setattr(db_module, "DATABASE", tmp_path / "ui_test.db")

    app = create_app()
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "ui-test-secret"

    return app


def _get_ci_host_ip():
    """Return the job container IP that Selenium service container can access."""
    hostname = socket.gethostname()
    return socket.gethostbyname(hostname)


def _wait_for_server(url):
    """Wait until the Flask test server is reachable."""
    for _ in range(30):
        try:
            with urllib.request.urlopen(url, timeout=2):
                return
        except Exception:
            time.sleep(0.2)

    raise RuntimeError(f"Live server did not start: {url}")


@pytest.fixture()
def live_server(live_app):
    """Run the Flask app in a background server for Selenium."""
    selenium_remote_url = os.getenv("SELENIUM_REMOTE_URL")

    if selenium_remote_url:
        bind_host = "0.0.0.0"
        browser_host = _get_ci_host_ip()
    else:
        bind_host = "127.0.0.1"
        browser_host = "127.0.0.1"

    server = make_server(bind_host, 0, live_app)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    base_url = f"http://{browser_host}:{server.server_port}"
    _wait_for_server(base_url)

    yield base_url

    server.shutdown()
    server_thread.join(timeout=5)


@pytest.fixture()
def browser(tmp_path):
    """Create a Chrome browser for Selenium tests."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--force-device-scale-factor=1")

    selenium_remote_url = os.getenv("SELENIUM_REMOTE_URL")

    if selenium_remote_url:
        driver = webdriver.Remote(
            command_executor=selenium_remote_url,
            options=options,
        )
    else:
        options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--remote-debugging-port=0")
        options.add_argument(f"--user-data-dir={tmp_path / 'chrome-user-data'}")
        options.add_argument(f"--data-path={tmp_path / 'chrome-data'}")
        options.add_argument(f"--disk-cache-dir={tmp_path / 'chrome-cache'}")

        chrome_binary = os.getenv("CHROME_BIN")
        chromedriver_path = os.getenv("CHROMEDRIVER_PATH")

        if chrome_binary:
            options.binary_location = chrome_binary

        service = Service(chromedriver_path) if chromedriver_path else Service()
        driver = webdriver.Chrome(service=service, options=options)

    yield driver

    driver.quit()


@pytest.fixture()
def seed_user():
    """Return a helper that creates a user in the isolated UI test database."""

    def _seed_user(
        email,
        student_id,
        display_name,
        first_name="UI",
        last_name="Tester",
        contact_number="91234567",
        password=DEFAULT_PASSWORD,
        role="user",
        status="Active",
    ):
        conn = db_module.get_db_connection()
        cursor = conn.execute(
            """
            INSERT INTO users (
                student_id, first_name, last_name, display_name,
                email, contact_number, password_hash, role, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                student_id,
                first_name,
                last_name,
                display_name,
                email,
                contact_number,
                generate_password_hash(password),
                role,
                status,
            ),
        )
        conn.commit()
        conn.close()

        return {
            "id": cursor.lastrowid,
            "email": email,
            "student_id": student_id,
            "display_name": display_name,
            "password": password,
        }

    return _seed_user


@pytest.fixture()
def seed_listing():
    """Return a helper that creates a listing in the isolated UI test database."""

    def _seed_listing(
        seller_id,
        title,
        description="Selenium UI test listing.",
        price="10.00",
        category="Electronics",
        condition="Like New",
        image_url=DEFAULT_IMAGE_URL,
    ):
        return create_listing(
            seller_id=seller_id,
            title=title,
            description=description,
            price=price,
            category=category,
            condition=condition,
            image_url=image_url,
        )

    return _seed_listing


@pytest.fixture()
def login_as(live_server, browser):
    """Return a helper that logs in through the browser UI."""

    def _login_as(email, password=DEFAULT_PASSWORD):
        wait = WebDriverWait(browser, 10)

        browser.get(f"{live_server}/login")
        wait.until(expected.presence_of_element_located((By.ID, "login_email"))).send_keys(
            email
        )
        browser.find_element(By.ID, "login_password").send_keys(password)
        browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        wait.until(expected.url_contains("/profile"))

    return _login_as


@pytest.fixture()
def safe_click(browser):
    """Return a helper that scrolls to an element and clicks it using JavaScript."""

    def _safe_click(locator):
        wait = WebDriverWait(browser, 10)
        element = wait.until(expected.presence_of_element_located(locator))
        browser.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            element,
        )
        browser.execute_script("arguments[0].click();", element)
        return element

    return _safe_click


@pytest.fixture()
def listing_image(tmp_path):
    """Create a small PNG file for Selenium listing image upload."""
    image_bytes = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8"
        "/x8AAwMB/6X7pfsAAAAASUVORK5CYII="
    )
    image_path = tmp_path / "listing-test-image.png"
    image_path.write_bytes(image_bytes)
    return image_path
