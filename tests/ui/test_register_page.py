# pylint: disable=missing-module-docstring,missing-function-docstring,redefined-outer-name
from app import create_app


def test_register_page_loads():
    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as client:
        response = client.get("/register")

    assert response.status_code == 200
    assert b"Create your account" in response.data
    assert b"Student ID" in response.data
    assert b"NYP Email Address" in response.data
    assert b"Create Account" in response.data