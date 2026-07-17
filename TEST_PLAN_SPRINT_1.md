# Test Plan — SwapLah

## Sprint 1, Version 1.0.0

**Team:** Team 2 — SwapLah
**Team members:** Felicia, Charlisa, Lucas, Lucio, Elijah
**Date created:** 12 Jun 2026
**Last updated:** 15 Jul 2026
**GitLab project:** `https://gitlab.com/nyp-sg/pet/it2112/26s1/it2112-03/assignment/team_2/swaplah`

---

## 1. Introduction

This test plan covers Sprint 1 of SwapLah, a web-based student co-op marketplace for polytechnic students.

Sprint 1 focuses on **User Account Management and Authentication**. These features ensure that students can create accounts, log in securely, view and update their account details, and are protected from unauthorised access.

This Sprint adds and verifies the following features:

* Student account registration with NYP email validation (#1)
* Secure login for registered users (#2)
* View account details for logged-in users (#3)
* Update account details except Email and Student ID (#16)
* Automatic logout after 30 minutes of inactivity (#17)
* Protected pages blocked for logged-out users (#18)
* Suspended users prevented from logging in (#19)

---

## 2. Scope

### In Scope

* Unit tests for new and modified authentication and profile functions
* API / route tests for registration, login, profile view, profile update, and access control
* Regression testing to ensure Sprint 1 features continue to pass after each merge
* Static analysis using pylint for all Python files
* Cyclomatic complexity checking using radon
* Test coverage checking using pytest-cov
* Manual browser testing for Sprint 1 acceptance criteria
* Selenium headless browser tests for Sprint 1 authentication and account-management flows
* Page Object Model structure for Sprint 1 Selenium UI tests under `tests/ui/selenium/pages/`
* GitLab CI/CD pipeline verification
* GitLab Test Cases linked to related Sprint 1 PBIs

### Out of Scope

| Item                            | Reason                                                                                      |
| ------------------------------- | ------------------------------------------------------------------------------------------- |
| Performance testing             | Not required for Sprint 1 and not part of Assignment 1 scope                                |
| Load testing                    | SwapLah is a student project and does not require traffic simulation for Sprint 1           |
| Security penetration testing    | GitLab SAST and secret detection are used instead                                           |
| Item listing end-to-end flow    | Item listing features are handled outside the Sprint 1 account-management scope             |
| Offers and transactions testing | Offers are outside Sprint 1 account management scope                                        |
| Review and rating testing       | Reviews are not part of Sprint 1 scope                                                      |
| Full cross-browser matrix testing | Selenium tests run in headless Chrome only; Edge/Firefox matrix testing is outside Sprint 1 scope |

---

## 3. Test Approach

### Testing Pyramid Target

| Level             |              Target Count | Tool                       | Pipeline Stage |
| ----------------- | ------------------------: | -------------------------- | -------------- |
| Unit tests        |                     10–15 | pytest                     | test           |
| API / Route tests |                     10–15 | pytest + Flask test client | test           |
| UI smoke tests    |                       1–2 | pytest / Flask test client | test           |
| Sprint 1 Selenium E2E tests |              5 | Selenium WebDriver + Page Object Model + headless Chrome | test |
| Static analysis   |           All `.py` files | pylint >= 10.0             | validate       |
| Complexity check  | All application functions | radon                      | validate       |
| Coverage check    |         Application logic | pytest-cov                 | test           |

### Static Testing

* **Tool:** pylint
* **Threshold:** 10.0/10
* **Purpose:** Ensure Python code follows the agreed code quality standard
* **Stage:** validate, before dynamic tests

### Complexity Testing

* **Tool:** radon
* **Threshold:** Cyclomatic complexity per function should not exceed 10
* **Purpose:** Identify overly complex functions that should be refactored
* **Stage:** validate

### Dynamic Testing

* **Tool:** pytest + pytest-cov + Selenium WebDriver
* **Assignment minimum coverage:** >= 60% application logic coverage
* **A-band / current pipeline threshold:** >= 75% unit coverage
* **Actual final unit coverage:** 77%
* **Sprint 1 UI automation target:** >= 5 Selenium UI scripts running in a headless browser
* **Sprint 1 Selenium evidence:** 5 Selenium E2E tests for registration, login/logout/protected access, profile update, session timeout, and suspended login rejection
* **Test design:** White-box testing for unit tests, black-box testing for route/API tests, and browser-based end-to-end testing for Sprint 1 UI flows
* **Stage:** test

### Acceptance Testing

* **Method:** Sprint Review demonstration, manual browser testing, and Selenium headless browser testing
* **Assessor:** Tutor / Product Owner / Team reviewer
* **Criteria:** Acceptance Criteria for each Sprint 1 user story must be verified
* **Sprint 1 Selenium coverage:** Registration, login/logout, protected page access, profile update, session timeout, and suspended login rejection

---

## 4. Test Items

| Function / Route               | Related PBI | Complexity | Minimum Tests | Priority |
| ------------------------------ | ----------- | ---------: | ------------: | -------- |
| `/register`                    | #1          |     Medium |             4 | High     |
| `_handle_register()`           | #1          |     Medium |             4 | High     |
| `/login`                       | #2          |     Medium |             4 | High     |
| `_handle_login()`              | #2, #19     |     Medium |             5 | High     |
| `/profile`                     | #3, #18     |        Low |             3 | High     |
| `/profile/edit`                | #16, #18    |     Medium |             5 | High     |
| `get_user_by_email()`          | #2, #19     |        Low |             2 | High     |
| `get_user_by_id()`             | #3, #16     |        Low |             2 | High     |
| `update_user_account()`        | #16         |     Medium |             3 | High     |
| `/logout`                      | #2          |        Low |             1 | Medium   |
| Session timeout logic          | #17         |     Medium |             2 | High     |
| Protected route access control | #18         |     Medium |             4 | High     |
| Selenium registration flow     | #1          |     Medium |             1 | High     |
| Selenium login/logout and protected access flow | #2, #3, #18 | Medium | 1 | High |
| Selenium profile update flow   | #16         |     Medium |             1 | High     |
| Selenium session timeout flow  | #17         |     Medium |             1 | High     |
| Selenium suspended login flow  | #19         |     Medium |             1 | High     |

---

## 5. Test Environment

* **Language:** Python 3.x
* **Framework:** Flask
* **Database:** SQLite
* **Test framework:** pytest
* **Coverage tool:** pytest-cov
* **Static analysis:** pylint
* **Complexity analysis:** radon
* **CI/CD platform:** GitLab CI/CD
* **Dependencies:** installed from `requirements-dev.txt` for development, testing, quality, and CI checks
* **Browser:** Chrome / Edge / Firefox for manual checks; headless Chrome / Chromium for Selenium CI tests

### Test Isolation Rule

Each automated test must create and destroy its own test data. Tests must not depend on the production `swaplah.db` file. Temporary databases or isolated fixtures should be used during test execution.

---

## 6. Entry and Exit Criteria

### Entry Criteria

Testing can begin when:

* Sprint 1 feature branch is pushed to GitLab.
* Merge Request is created.
* No Python syntax errors exist.
* Required test files are added under `tests/unit`, `tests/api`, or `tests/ui`.
* Sprint 1 Selenium page object classes are added under `tests/ui/selenium/pages/` when UI flows are automated.
* Feature acceptance criteria are written in the related GitLab issue.
* Related issue has Sprint 1 milestone, labels, priority, and story points.
* pylint validate stage passes with score 10.0/10.

### Exit Criteria — Verification

Sprint 1 verification is complete when:

* [ ] All unit tests pass with 0 failures.
* [ ] All API / route tests pass with 0 failures.
* [ ] UI smoke tests and Sprint 1 Selenium headless browser tests pass.
* [ ] Test coverage is at least 75% for the current A-band gate and at least 60% for the assignment minimum.
* [ ] pylint score is 10.00/10 against the 10.0 target.
* [ ] radon complexity check shows function complexity does not exceed 10.
* [ ] GitLab pipeline is green on the Merge Request, including `selenium-ui-tests`.
* [ ] No generated files such as `.env`, `.coverage`, `.venv`, `__pycache__`, or `swaplah.db` are committed.

### Exit Criteria — Validation

Sprint 1 validation is complete when:

* [ ] Product Owner / Tutor confirms Sprint 1 acceptance criteria.
* [ ] All related GitLab test cases are updated to Passing.
* [ ] At least one teammate reviews and approves the Merge Request.
* [ ] The related GitLab issue is moved to Done only after the MR is merged.

---

## 7. Sprint 1 Test Cases

| Test ID           | Module          | Related PBI | Description                                   | Type                | Preconditions                                      | Steps                                                                                                                                                       | Expected Result                                                                                     | Status            |
| ----------------- | --------------- | ----------- | --------------------------------------------- | ------------------- | -------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- | ----------------- |
| TC-S1-REG-001     | Registration    | #1          | Register with valid NYP email                 | Positive            | User is not registered                             | 1. Open `/register` 2. Enter valid Student ID, First Name, Last Name, Display Name, NYP email, Contact Number, Password and Confirm Password 3. Submit form | Account is created successfully, password is stored as a hash, and user is redirected to login page | Pass              |
| TC-S1-REG-002     | Registration    | #1          | Reject non-NYP email                          | Negative            | User is on register page                           | 1. Open `/register` 2. Enter an email that does not end with `@mymail.nyp.edu.sg` 3. Submit form                                                            | Registration is rejected and an error message is displayed                                          | Pass              |
| TC-S1-REG-003     | Registration    | #1          | Reject empty required fields                  | Negative            | User is on register page                           | 1. Open `/register` 2. Leave one or more required fields empty 3. Submit form                                                                               | Account is not created and required field error message is displayed                                | Pass              |
| TC-S1-REG-004     | Registration    | #1          | Reject duplicate email or Student ID          | Negative            | Existing account already exists                    | 1. Register a user successfully 2. Submit another registration using the same email or Student ID                                                           | Registration fails and duplicate account error message is displayed                                 | Pass              |
| TC-S1-REG-005     | Registration    | #1          | Store password as hash instead of plaintext   | Security / Unit     | User registration function is available            | 1. Register a user with a known password 2. Inspect stored password value in test database                                                                  | Stored password is not equal to plaintext password and can be verified using password hash checking | Pass              |
| TC-S1-LOGIN-001   | Login           | #2          | Login with valid credentials                  | Positive            | Registered active user exists                      | 1. Open `/login` 2. Enter valid email and password 3. Submit form                                                                                           | User logs in successfully, session is created, and user is redirected to profile or protected page  | Pass              |
| TC-S1-LOGIN-002   | Login           | #2          | Reject wrong password                         | Negative            | Registered user exists                             | 1. Open `/login` 2. Enter valid email but wrong password 3. Submit form                                                                                     | Login fails and invalid email or password message is shown                                          | Pass              |
| TC-S1-LOGIN-003   | Login           | #2          | Reject missing credentials                    | Negative            | User is on login page                              | 1. Open `/login` 2. Submit form with missing email or password                                                                                              | Login fails and required credentials message is shown                                               | Pass              |
| TC-S1-LOGIN-004   | Login           | #2          | Create correct session after successful login | Positive            | Registered active user exists                      | 1. Login with valid credentials 2. Check session data                                                                                                       | Session contains user ID, email, display name, and role                                             | Pass              |
| TC-S1-SUSP-001    | Suspended Login | #19         | Block suspended user from logging in          | Negative / Security | Suspended user account exists                      | 1. Open `/login` 2. Enter suspended user credentials 3. Submit form                                                                                         | Login is blocked and suspended account message is shown                                             | Pass |
| TC-S1-SUSP-002    | Suspended Login | #19         | Allow active user to log in                   | Positive            | Active registered user exists                      | 1. Open `/login` 2. Enter active user credentials 3. Submit form                                                                                            | Active user logs in successfully                                                                    | Pass |
| TC-S1-PROF-001    | Profile         | #3          | View account details when logged in           | Positive            | User is logged in                                  | 1. Login 2. Open `/profile`                                                                                                                                 | Student ID, First Name, Last Name, Display Name, Email, and Contact Number are displayed            | Pass              |
| TC-S1-PROF-002    | Profile         | #3, #18     | Redirect logged-out user from profile         | Negative            | User is not logged in                              | 1. Clear session or log out 2. Open `/profile` directly                                                                                                     | User is redirected to login page with an access message                                             | Pass              |
| TC-S1-PROF-003    | Profile         | #3          | Invalid session redirects to login            | Negative            | Session contains invalid user ID                   | 1. Manually set invalid user ID in session 2. Open `/profile`                                                                                               | Session is cleared and user is asked to log in again                                                | Pass              |
| TC-S1-UPD-001     | Update Profile  | #16         | Update editable account details               | Positive            | User is logged in                                  | 1. Open `/profile/edit` 2. Update First Name, Last Name, Display Name and Contact Number 3. Submit form                                                     | Updated details are saved and displayed on profile page                                             | Pass              |
| TC-S1-UPD-002     | Update Profile  | #16         | Email and Student ID cannot be changed        | Negative            | User is logged in                                  | 1. Open `/profile/edit` 2. Attempt to modify Email or Student ID through form or request data 3. Submit update                                              | Email and Student ID remain unchanged                                                               | Pass              |
| TC-S1-UPD-003     | Update Profile  | #16         | Reject invalid contact number                 | Negative            | User is logged in                                  | 1. Open `/profile/edit` 2. Enter invalid contact number 3. Submit form                                                                                      | Update fails and contact number validation error is shown                                           | Pass              |
| TC-S1-UPD-004     | Update Profile  | #16         | Reject password mismatch                      | Negative            | User is logged in                                  | 1. Open `/profile/edit` 2. Enter different Password and Confirm Password values 3. Submit form                                                              | Update fails and password mismatch error is shown                                                   | Pass              |
| TC-S1-UPD-005     | Update Profile  | #16         | Update password successfully                  | Positive            | User is logged in                                  | 1. Open `/profile/edit` 2. Enter matching new password and confirm password 3. Submit form 4. Log out and log in with new password                          | Password is updated securely and user can log in using the new password                             | Pass              |
| TC-S1-AUTH-001    | Protected Pages | #18         | Block logged-out user from profile page       | Negative / Security | User is logged out                                 | 1. Open `/profile` directly                                                                                                                                 | User is redirected to login page                                                                    | Pass              |
| TC-S1-AUTH-002    | Protected Pages | #18         | Block logged-out user from edit profile page  | Negative / Security | User is logged out                                 | 1. Open `/profile/edit` directly                                                                                                                            | User is redirected to login page                                                                    | Pass              |
| TC-S1-AUTH-003    | Protected Pages | #18         | Block logged-out user from sell page          | Negative / Security | User is logged out                                 | 1. Open `/sell` directly                                                                                                                                    | User is redirected to login page or access is blocked                                               | Pass |
| TC-S1-AUTH-004    | Protected Pages | #18         | Block logged-out user from offers page        | Negative / Security | User is logged out                                 | 1. Open `/offers` directly                                                                                                                                  | User is redirected to login page or access is blocked                                               | Pass |
| TC-S1-SESSION-001 | Session Timeout | #17         | Auto logout after 30 minutes of inactivity    | Negative / Security | User is logged in and session timeout logic exists | 1. Login 2. Simulate last activity older than 30 minutes 3. Open protected page                                                                             | Session expires, user is logged out, and user is redirected to login page                           | Pass |
| TC-S1-SESSION-002 | Session Timeout | #17         | Keep active session before 30 minutes         | Positive            | User is logged in and session is still active      | 1. Login 2. Access protected page before 30 minutes of inactivity                                                                                           | User remains logged in and can access protected page                                                | Pass |
| TC-S1-LOGOUT-001  | Logout          | #2          | User logs out successfully                    | Positive            | User is logged in                                  | 1. Click logout or open `/logout` 2. Try to access profile again                                                                                            | Session is cleared and user is redirected to login page                                             | Pass              |

---

## 8. Sprint 1 Selenium UI Test Cases

The Sprint 1 Selenium UI tests are stored under `tests/ui/selenium/` and use the Page Object Model pattern with page classes stored under `tests/ui/selenium/pages/`. These tests run in headless Chrome / Chromium through the GitLab `selenium-ui-tests` job.

This section only documents Sprint 1 account-management and authentication flows. Item listing, offer, review, and reporting flows are outside this Sprint 1 test plan.

| Test ID          | Test Script                         | Related PBI | Complete User Flow Covered | Expected Result | Status |
| ---------------- | ----------------------------------- | ----------- | -------------------------- | --------------- | ------ |
| TC-S1-SEL-001    | `test_registration_selenium.py`     | #1          | User opens register page, enters valid NYP account details, and submits registration | User is redirected to login page with success message | Pass |
| TC-S1-SEL-002    | `test_login_logout_selenium.py`     | #2, #3, #18 | User logs in, views profile, logs out, and attempts protected access again | User can view profile when logged in and is redirected after logout | Pass |
| TC-S1-SEL-003    | `test_profile_update_selenium.py`   | #16         | Logged-in user edits display name and contact number through the browser | Updated details are saved and shown on profile page | Pass |
| TC-S1-SEL-004    | `test_session_timeout_selenium.py`  | #17         | Expired browser session is simulated and a protected page is opened | Session expires and user is redirected to login page | Pass |
| TC-S1-SEL-005    | `test_suspended_login_selenium.py`  | #19         | Suspended user attempts to log in with valid credentials | Login is blocked and suspended account message appears | Pass |

### Sprint 1 Selenium Page Object Model Structure

| Page Object File | Purpose |
| ---------------- | ------- |
| `base_page.py` | Shared waiting, element finding, text entry, clicking, and assertion helpers |
| `login_page.py` | Login form actions and login page assertions |
| `register_page.py` | Registration form actions and registration success assertion |
| `profile_page.py` | Profile, edit profile, and logout actions |


## 9. Regression Testing

Before merging any Sprint 1 Merge Request, the following regression checks must pass:

| Regression Area             | Command / Method                                            | Expected Result                                    |
| --------------------------- | ----------------------------------------------------------- | -------------------------------------------------- |
| Full automated test suite   | `python -m pytest -q`                                       | All tests pass                                     |
| Unit coverage               | `python -m pytest tests/unit --cov=app --cov-report=term-missing` | Coverage is at least 75% for the current A-band gate and at least 60% for the assignment minimum |
| Linting                     | `python -m pylint app tests scripts`                        | Score is 10.00/10 against the 10.0 target          |
| Complexity                  | `python -m radon cc app/ -s`                                | No function exceeds complexity 10                  |
| Manual registration flow    | Browser test                                                | User can register with valid NYP email             |
| Manual login flow           | Browser test                                                | Registered active user can log in successfully     |
| Manual suspended login flow | Browser test                                                | Suspended user cannot log in                       |
| Manual profile flow         | Browser test                                                | Logged-in user can view and update account details |
| Manual protected page flow  | Browser test                                                | Logged-out user cannot access protected pages      |
| Manual session timeout flow | Browser test / simulated test                               | Inactive session expires after 30 minutes          |
| Sprint 1 Selenium UI suite   | `python -m pytest tests/ui/selenium/test_registration_selenium.py tests/ui/selenium/test_login_logout_selenium.py tests/ui/selenium/test_profile_update_selenium.py tests/ui/selenium/test_session_timeout_selenium.py tests/ui/selenium/test_suspended_login_selenium.py` | 5 Sprint 1 Selenium tests pass in headless browser |

---

## 10. Risks

| Risk                                                | Probability | Impact | Mitigation                                                           |
| --------------------------------------------------- | ----------- | ------ | -------------------------------------------------------------------- |
| Duplicate email or Student ID handling fails        | Medium      | High   | Add negative registration tests for duplicate records                |
| Password is stored in plaintext                     | Low         | High   | Verify password is hashed before storing                             |
| Non-NYP email is accepted                           | Medium      | High   | Add validation and negative test case                                |
| Logged-out users can access protected pages         | Medium      | High   | Add route guards and negative access-control tests                   |
| Suspended users can still log in                    | Medium      | High   | Check user status during login and add suspended user tests          |
| Session timeout is not enforced correctly           | Medium      | High   | Add timeout logic and tests simulating inactivity                    |
| Profile update changes Email or Student ID          | Low         | High   | Keep Email and Student ID read-only and exclude them from update SQL |
| Test data affects real database                     | Medium      | Medium | Use isolated test database fixtures                                  |
| Pipeline fails due to missing dependency            | Medium      | Medium | Install development dependencies from `requirements-dev.txt` in CI    |
| Code quality fails due to long or complex functions | Medium      | Medium | Refactor route logic into helper functions where needed              |

---

## 11. Related Links

* [Sprint board](/-/boards)
* [CI/CD pipelines](/-/pipelines)
* [Merge requests](/-/merge_requests)
* [Test cases](/-/quality/test_cases)
* [Unit tests](tests/unit/)
* [API tests](tests/api/)
* [UI tests](tests/ui/)
* [AI Usage Logs](AI/)

---

## 12. Sprint 1 Definition of Done

### Verification

* [x] Code passes pylint with score 10.00/10 against the 10.0 target.
* [x] Cyclomatic complexity per function does not exceed 10.
* [x] All unit tests pass: 77 passed.
* [x] All API / route tests pass: 70 passed.
* [x] UI smoke tests and Sprint 1 Selenium headless browser tests pass.
* [x] Test coverage is at least 75% for the current A-band gate and at least 60% for the assignment minimum.
* [ ] Pipeline is green on the Merge Request, including validate, test, ui-test, api-test, security, build, and deploy jobs (user-reported, not repository-verifiable locally).

### Validation

* [ ] Acceptance Criteria are confirmed with Product Owner / Tutor.
* [ ] All Sprint 1 test cases are updated to Passing status.
* [ ] At least one teammate has reviewed and approved the Merge Request.
* [ ] Related issue is moved to Done only after the MR is merged.

---

## 13. AI Prompt and Refinement Evidence

### AI Prompt Used

"Generate a Sprint 1 test plan for SwapLah Assignment 1. Sprint 1 focuses on User Account Management and Authentication, including registration, login, view account details, update account details, protected pages, suspended login prevention, and 30-minute inactivity logout. Follow the required test plan format with Introduction, Scope, Test Approach, Test Items, Test Environment, Entry and Exit Criteria, Risks, Regression Testing, Definition of Done, and at least 10 positive and negative test cases with Test ID, description, preconditions, steps, and expected results."

### Refinement Made

The AI-generated test plan was reviewed and refined to match the actual Sprint 1 GitLab issues used by the SwapLah team: #1, #2, #3, #16, #17, #18, and #19. The test cases were adjusted to match the team’s acceptance criteria and implementation status. Earlier drafts used Pending / Not Run for items that had not yet been verified; this final update removes outdated wording that implied current Sprint 1 repository tests were still pending. The plan now distinguishes the 60% assignment minimum from the 75% A-band/current pipeline threshold.
The test plan was later updated after Sprint 1 Selenium UI automation was added. The UI testing scope was expanded from simple Flask smoke tests to include 5 Sprint 1 Selenium end-to-end tests running in a headless browser. The Selenium tests were also refactored using the Page Object Model pattern, where shared locators and page actions are stored under `tests/ui/selenium/pages/`. This update was made to align the Sprint 1 test plan with the actual authentication and account-management UI test evidence.

---

## 14. Final Repository Evidence Update

Evidence captured on 15 Jul 2026 from the current repository:

| Evidence item | Final value |
| --- | --- |
| Full pytest suite | 159 passed |
| Unit tests | 77 passed |
| Unit coverage | 77% |
| API tests | 70 passed |
| Flask UI tests | 2 passed |
| Selenium tests | 10 passed |
| Pylint target and result | Target 10.0; result 10.00/10 |
| Highest cyclomatic complexity | B(7), `_common_error` in `app/routes/offers.py` |
| Longest application function | 38 lines, `_register_simple_page_routes` in `app/__init__.py` |
| Code-quality gate | Passed |
| Development dependencies | `requirements-dev.txt` |
| Selenium pipeline job name | `selenium-ui-tests` |
| Pipeline stages | validate, test, ui-test, api-test, security, build, deploy |

Current pipeline jobs in `.gitlab-ci.yml`: `pylint-application`, `code-quality-gate`, `pytest-unit-tests`, `pytest-api-tests`, `selenium-ui-tests`, `newman-api-tests`, `semgrep-sast`, `secret_detection`, `gemnasium-python-dependency_scanning`, `cyclonedx-sbom`, `security-gate`, `build-archive`, and `deploy-package`.

