# SwapLah - Student Co-op Marketplace

SwapLah is a web-based student co-op marketplace built for polytechnic students to securely buy, sell, and swap pre-owned items such as textbooks, lab equipment, electronics, stationery, and clothing within a trusted campus community.

The application is built using Flask, SQLite, HTML, CSS, Bootstrap, REST API routes, automated testing, and GitLab CI/CD to follow professional software development practices.

---

## Project Overview

SwapLah allows registered polytechnic students to:

- Create an account using an NYP student email.
- Log in securely.
- Manage their account profile.
- Create and manage item listings.
- Browse, search, and filter active marketplace listings.
- View listing details and seller contact information.
- Submit offers for marketplace items.

The project is developed using Agile and DevOps practices, including user stories, sprint planning, merge requests, automated testing, code quality checks, and security scanning.

---

## Tech Stack

| Area | Technology |
|---|---|
| Backend | Python Flask |
| Frontend | HTML5, CSS, Bootstrap, Jinja Templates |
| Database | SQLite |
| Testing | Pytest, Selenium |
| Code Quality | Pylint, Radon |
| CI/CD | GitLab CI/CD |
| Security Scanning | GitLab SAST, Secret Detection, Dependency Scanning |
| Version Control | Git and GitLab |

---

## Features Implemented

### Sprint 1 - User Account Management and Authentication

Sprint 1 focuses on user registration, login, profile management, and session security.

Implemented features:

- Student registration with required account details:
  - Student ID
  - First Name
  - Last Name
  - Display Name
  - Email
  - Contact Number
  - Password
- NYP email validation using `@mymail.nyp.edu.sg`.
- Duplicate Email and Student ID validation.
- Passwords stored securely using password hashing.
- Secure login using registered credentials.
- Invalid login handling.
- Suspended user login prevention.
- User logout.
- View account details.
- Update editable profile details.
- Email and Student ID are protected and cannot be changed through profile update.
- 30-minute inactivity session timeout.
- Protected pages redirect logged-out or expired-session users back to login.

Sprint 1 evidence includes:

- Unit tests for registration, login, password hashing, profile update, and session timeout.
- API/route tests for authentication and protected access.
- Selenium UI tests for registration, login/logout, profile update, session timeout, and suspended login.
- GitLab work items linked to Sprint 1 milestone.
- AI usage log entries for authentication-related work.

---

### Sprint 2 - Item Listing Management

Sprint 2 focuses on creating, viewing, searching, filtering, editing, and soft-deleting item listings.

Implemented features:

- Create item listings with:
  - Title
  - Description
  - Price
  - Category
  - Condition
  - Image URL
- Price supports:
  - Numeric values
  - `Free`
  - `Swap Only`
- Listings include:
  - Unique ID
  - Listing Date
  - Last Modified Timestamp
- View active, non-deleted listings.
- Pagination with 10 items per page.
- Search listings by keyword against Title and Description.
- Search results ordered by newest listing first.
- Filter listings by Category.
- Filter listings by Condition.
- Filter listings by both Category and Condition.
- Clear Category and Condition filters individually.
- View listing detail page.
- Listing detail page shows:
  - Item details
  - Seller Display Name
  - Seller Email
  - Seller Contact Number
- Edit own listing only.
- Update to a listing updates the Last Modified Timestamp.
- Soft-delete own listing only.
- Soft-deleted listings remain in the database but are hidden from active listings.

Sprint 2 evidence includes:

- Unit tests for listing validation, pagination, search, filtering, owner-only editing, and soft delete.
- API tests for create, retrieve, update, delete, search, and filter listing endpoints.
- Selenium UI tests for listing creation, search/filter/clear filters, and soft delete.
- GitLab work items linked to Sprint 2 milestone.
- AI usage log entries for listing-related work.

---

## Main API Endpoints

### Listing APIs

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/listings` | Returns active listings as JSON. Supports search, category, and condition query parameters. |
| GET | `/api/listings/<listing_id>` | Returns a single active listing by ID. |
| POST | `/api/listings` | Creates a new listing. Requires login. |
| PUT | `/api/listings/<listing_id>` | Updates a listing. Only the listing owner can update. |
| DELETE | `/api/listings/<listing_id>` | Soft-deletes a listing. Only the listing owner can delete. |

### Offer APIs

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/offers` | Submits an offer. Requires login. |

---

## Project Structure

```text
swaplah/
├── AI/
│   └── 254381C_AI_LOG.md
├── app/
│   ├── routes/
│   ├── static/
│   ├── templates/
│   ├── __init__.py
│   └── db.py
├── tests/
│   ├── api/
│   ├── unit/
│   └── ui/
│       ├── flask/
│       └── selenium/
│           ├── pages/
│           ├── conftest.py
│           ├── test_listing_creation_selenium.py
│           ├── test_listing_search_filter_selenium.py
│           ├── test_login_logout_selenium.py
│           ├── test_offer_submission_selenium.py
│           ├── test_profile_update_selenium.py
│           ├── test_registration_selenium.py
│           ├── test_session_timeout_selenium.py
│           ├── test_soft_delete_listing_selenium.py
│           └── test_suspended_login_selenium.py
├── .gitignore
├── .gitlab-ci.yml
├── README.md
├── requirements.txt
├── setup.cfg
└── pytest.ini
```

---

## Local Development Setup

To contribute to this project, set up a local Python virtual environment. This ensures that all developers use the same project dependencies and prevents conflicts with global Python packages.

---

## Prerequisites

Install Python 3.11 or above.

Check your Python version:

```bash
python --version
```

---

## Step 1: Clone the Repository

```bash
git clone <repository-url>
cd swaplah
```

Replace `<repository-url>` with the GitLab repository URL.

---

## Step 2: Create a Virtual Environment

```bash
python -m venv .venv
```

For macOS or Linux, use this if `python` does not work:

```bash
python3 -m venv .venv
```

---

## Step 3: Activate the Virtual Environment

### Windows Command Prompt

```bash
.venv\Scripts\activate.bat
```

### Windows PowerShell

```bash
.venv\Scripts\Activate.ps1
```

### macOS or Linux

```bash
source .venv/bin/activate
```

You should see `(.venv)` at the beginning of the terminal prompt after activation.

---

## Step 4: Install Dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

---

## Step 5: Environment Variables

This project uses environment variables for configuration values that should not be committed to GitLab.

1. Copy `.env.example`.
2. Rename the copy to `.env`.
3. Fill in your local configuration values.
4. Ensure `.env` remains ignored by `.gitignore`.

---

## Step 6: Run the Application

Start the Flask development server:

```bash
flask run
```

Or run directly using Python if the project setup requires it:

```bash
python run.py
```

The application should run locally at:

```text
http://127.0.0.1:5000
```

---

## Testing

The project includes unit tests, API tests, Flask UI tests, Selenium UI tests, code quality checks, and complexity checks.

---

## Run All Tests

```bash
python -m pytest -q
```

---

## Run Unit Tests

```bash
python -m pytest tests/unit
```

Run unit tests with coverage:

```bash
python -m pytest tests/unit --cov=app --cov-report=term-missing
```

---

## Run API Tests

```bash
python -m pytest tests/api
```

---

## Run UI Tests

```bash
python -m pytest tests/ui
```

---

## Run Selenium UI Tests Only

```bash
python -m pytest tests/ui/selenium
```

---

## Run Code Quality Checks

```bash
python -m pylint app tests
```

---

## Run Cyclomatic Complexity Check

```bash
python -m radon cc app/ -s
```

---

## Key Selenium UI Tests

| Test File | Purpose |
|---|---|
| `test_registration_selenium.py` | Tests end-to-end account registration. |
| `test_login_logout_selenium.py` | Tests login, profile access, logout, and protected page restriction. |
| `test_profile_update_selenium.py` | Tests profile update flow. |
| `test_session_timeout_selenium.py` | Tests session timeout behaviour. |
| `test_suspended_login_selenium.py` | Tests suspended user login rejection. |
| `test_listing_creation_selenium.py` | Tests end-to-end listing creation. |
| `test_listing_search_filter_selenium.py` | Tests listing search, filter, and clear filter behaviour. |
| `test_soft_delete_listing_selenium.py` | Tests owner-only soft delete flow. |

---

## Page Object Model

The Selenium UI tests use the Page Object Model pattern to keep test scripts clean and maintainable.

Page Object files are located in:

```text
tests/ui/selenium/pages/
```

Examples include:

- `base_page.py`
- `login_page.py`
- `register_page.py`
- `profile_page.py`
- `home_page.py`
- `sell_page.py`
- `listing_detail_page.py`

---

## GitLab CI/CD Pipeline

The GitLab CI/CD pipeline is configured in:

```text
.gitlab-ci.yml
```

The pipeline includes:

- Linting with Pylint.
- Cyclomatic complexity checks with Radon.
- Unit tests with coverage reporting.
- API tests.
- Selenium UI tests using a headless Chrome Selenium service.
- SAST security scanning.
- Secret detection.
- Dependency scanning.

The pipeline must pass before merge requests are merged into the protected branch.

---

## CI/CD Jobs

| Job | Purpose |
|---|---|
| `linting_job` | Runs Pylint and Radon complexity checks. |
| `unit_testing_job` | Runs unit tests with coverage. |
| `api_testing_job` | Runs API tests. |
| `ui_testing_job` | Runs Flask UI and Selenium UI tests. |
| `semgrep-sast` | Runs static application security testing. |
| `secret_detection` | Scans for committed secrets. |
| `gemnasium-python-dependency_scanning` | Scans Python dependencies. |

---

## Security Measures

Security-related features include:

- Passwords are hashed before storage.
- Suspended users are blocked from logging in.
- Protected pages require an active session.
- Sessions expire after 30 minutes of inactivity.
- Secrets are not hardcoded in source code.
- `.env` is ignored and not committed to the repository.
- GitLab SAST and secret detection are included in the pipeline.
- Owner-only checks are enforced for listing update and delete actions.

---

## Code Quality Standards

The project follows these code quality standards:

- Python code must pass Pylint.
- Functions should remain short and readable.
- Cyclomatic complexity should not exceed the assignment threshold.
- Repeated UI automation logic is moved into Selenium Page Object classes.
- Tests are organised into `unit`, `api`, and `ui` folders.
- All feature changes are committed through GitLab branches and merge requests.

---

## Git Workflow

Recommended workflow:

```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
```

After making changes:

```bash
python -m pytest -q
python -m pylint app tests
python -m radon cc app/ -s
```

Then commit and push:

```bash
git add <changed-files>
git commit -m "type: short description"
git push origin feature/your-feature-name
```

Create a merge request into `develop` and ensure the pipeline passes before merging.

---

## AI Usage Declaration

AI assistance was used for selected parts of planning, test writing, troubleshooting, and documentation.

All significant AI usage is documented in:

```text
AI/254381C_AI_LOG.md
```

The AI log includes:

- Date of AI usage.
- Tool used.
- Prompt or task given.
- Output kept or changed.
- Reason for keeping or changing the output.

All AI-generated content was reviewed, edited, and tested before being committed.

---

## Deactivating the Virtual Environment

When finished, deactivate the virtual environment:

```bash
deactivate
```

---

## Contributors

Team 2 - SwapLah

Primary sprint ownership in this evidence branch:

- Sprint 1: User Account Management and Authentication
- Sprint 2: Item Listing Management
