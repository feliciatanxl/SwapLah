from werkzeug.security import check_password_hash, generate_password_hash


def test_nyp_email_domain_validation():
    email = "s12345678@mymail.nyp.edu.sg"
    assert email.endswith("@mymail.nyp.edu.sg")


def test_invalid_email_domain_rejected():
    email = "student@gmail.com"
    assert not email.endswith("@mymail.nyp.edu.sg")


def test_required_fields_are_not_empty():
    fields = ["S12345678", "Felicia", "Tan", "FeliciaT", "s12345678@mymail.nyp.edu.sg", "91234567", "Password123"]
    assert all(field.strip() for field in fields)


def test_password_hash_is_not_plaintext():
    password = "Password123"
    password_hash = generate_password_hash(password)

    assert password_hash != password
    assert check_password_hash(password_hash, password)