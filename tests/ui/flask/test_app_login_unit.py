from app import create_app


def test_login_page_loads():
    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as client:
        response = client.get("/login")

    assert response.status_code == 200
    assert b"Welcome back" in response.data
    assert b"NYP Email Address" in response.data
    assert b"Password" in response.data
    assert b"Log In" in response.data
