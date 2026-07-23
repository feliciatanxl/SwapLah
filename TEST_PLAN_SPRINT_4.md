# Test Plan — SwapLah

## Sprint 4, Version 4.0.0

**Team:** Team 2 — SwapLah  
**Team members:** TAN XIU LI, FELICIA; TAN YU EN, CHARLISA; ELIJAH ONG; LEOVALAN LUCIO RICHARD; LUCAS WONG SI JIE  
**Date created:** 23 Jul 2026  
**Last updated:** 23 Jul 2026  
**GitLab project:** https://gitlab.com/nyp-sg/pet/it2112/26s1/it2112-03/assignment/team_2/swaplah

---

## 1. Introduction

This test plan documents the testing strategy and verification evidence for **Sprint 4** of **SwapLah**, a web-based student co-op marketplace for polytechnic students.

Sprint 4 focuses on **Reviews, Ratings, and Profile Stats** — the area Sprint 3 explicitly marked out of scope ("Review and rating testing... outside the Sprint 3 Offers and Transactions scope"). Sprint 4 verifies that a seller can leave a rating and comment for the buyer after a completed transaction, that a buyer can leave a rating and comment for the seller, that both directions correctly reject anyone not party to the transaction, that a user's average rating and review list are retrievable and displayed on their profile, and that the profile page's enriched marketplace stats (active listings, sold listings, trust badge, response rate) render correctly and respect the own-profile vs. another-user's-profile visibility rules.

### Sprint 4 Features Covered

| PBI / Issue | Sprint 4 User Story | Current Status | Priority |
| --- | --- | --- | --- |
| [#38](https://gitlab.com/nyp-sg/pet/it2112/26s1/it2112-03/assignment/team_2/swaplah/-/issues/38) | As a seller, leave a 1–5 star rating and optional comment for the buyer after a completed transaction | Closed / Done | High |
| [#44](https://gitlab.com/nyp-sg/pet/it2112/26s1/it2112-03/assignment/team_2/swaplah/-/issues/44) | As a buyer, leave a 1–5 star rating and optional comment for the seller after a completed transaction | Closed / Done | High |
| [#36](https://gitlab.com/nyp-sg/pet/it2112/26s1/it2112-03/assignment/team_2/swaplah/-/issues/36) | A user's average rating is calculated from all reviews received and displayed without a misleading trailing decimal | Closed / Done | Medium |
| Retrieve reviews for a user | As a marketplace user, retrieve all reviews for a user so feedback is visible | Closed / Done | Medium |
| View another user's profile | As a marketplace user, view another user's profile (rating, reviews, active/sold listings) without exposing their private account details or edit controls | Closed / Done | High |
| Profile marketplace stats | As a marketplace user, see a trust badge and response rate on a profile, derived from real listing and offer activity | Closed / Done | Low |

---

## 2. Scope

### 2.1 In Scope

The following items are included in Sprint 4 testing:

- Unit tests for rating validation, transaction-review access control (both seller and buyer direction), review response formatting, profile stats aggregation, trust badge tiering, response rate calculation, and the rating display filter.
- API / route tests for:
  - `POST /api/transactions/<transaction_id>/review` (seller reviews buyer)
  - `POST /api/transactions/<transaction_id>/buyer-review` (buyer reviews seller)
  - `GET /api/users/<user_id>/reviews`
  - `GET /profile` and `GET /profile/<user_id>`
- Real-database integration tests (seeded SQLite data, not mocks) confirming:
  - A review is only accepted from the correct transaction participant (seller-only endpoint rejects the buyer and vice versa).
  - A review is rejected when no completed transaction exists for the given ID.
  - Average rating and review count reflect all reviews received, and the average never shows a misleading trailing `.0`.
  - Profile stats (`active_count`, `total_sales`, `trust_badge`, `response_rate`) are computed correctly from real listings and offers.
  - `is_own_profile` correctly hides the Edit Profile button and Account Details card on another user's profile, and shows them on your own.
- Selenium UI test for viewing a profile page and submitting a review from the Transaction History page.
- Regression testing to ensure Sprint 1–3 features continue to pass after Sprint 4 changes.
- Static testing using pylint.
- Cyclomatic complexity checking using radon.
- Coverage checking using pytest-cov.
- GitLab CI/CD pipeline verification.
- AI prompt and refinement documentation.

### 2.2 Out of Scope

| Item | Reason |
| --- | --- |
| Editing or deleting an existing review | Not part of the Sprint 4 user stories; reviews are currently write-once. |
| Review moderation / reporting | Handled under the Admin / moderation epic, not Sprint 4. |
| Real payment processing | SwapLah does not include real payment gateways. |
| Full cross-browser Selenium matrix | One representative Selenium flow is used for Sprint 4; a full Edge/Firefox matrix is out of scope. |
| Full security penetration testing | GitLab SAST, dependency scanning, and secret detection are used for automated security checks instead. |
| Load testing | Not required for the small assignment dataset and current Sprint 4 scope. |

---

## 3. Test Approach

### 3.1 Testing Pyramid Target

| Level | Target Count | Tool | Pipeline Stage | Purpose |
| --- | ---: | --- | --- | --- |
| Unit tests | 45+ | pytest | test | Verify rating validation, review access control, profile stats, and formatting functions in isolation using monkeypatching and real temp-SQLite db-layer tests. |
| API / Route tests | 30+ | pytest + Flask test client | test | Verify HTTP route behaviour end to end, including real-database integration tests for reviews and profile stats. |
| Selenium UI flow | 1 Sprint 4 flow | Selenium + pytest | test (UI) | Verify a complete "view profile, leave a review" user flow in a real browser. |
| Static analysis | All `.py` files | pylint >= 7.0 | lint | Detect style, structure, and code quality issues. |
| Complexity check | All application functions | radon | lint | Confirm functions are maintainable and testable. |
| Coverage check | Application logic | pytest-cov | test | Confirm at least 60% application logic coverage. |

### 3.2 Static Testing

- **Tool:** pylint
- **Threshold:** score must be `>= 7.0/10` (currently `10.00/10`)
- **Purpose:** Detect syntax problems, unused imports, naming issues, overly long functions, and poor code structure before dynamic tests run.
- **Pipeline stage:** lint

### 3.3 Complexity Testing

- **Tool:** radon
- **Threshold:** cyclomatic complexity per function should not exceed 10.
- **Purpose:** Identify functions that are difficult to test or should be refactored.
- **Pipeline stage:** lint
- **Rule:** If a function has complexity above 10, it is treated as high risk and should be refactored or covered with additional tests before merge.

### 3.4 Dynamic Testing

- **Tools:** pytest, pytest-cov, Flask test client, Selenium
- **Minimum coverage required:** `>= 60%` application logic coverage
- **Team stretch target:** `>= 70%` where possible
- **Unit test design:** white-box testing — route-level tests use monkeypatching to isolate routes from the database layer; db-layer tests use a real temporary SQLite database (`tmp_path` fixture) to verify actual SQL aggregation logic (profile stats, trust badge tiers, response rate).
- **API / route test design:** black-box testing against the user story and acceptance criteria, using the Flask test client against a real temporary SQLite database.
- **Integration test design:** real temporary SQLite database seeded with users, listings, offers, transactions, and reviews, used to verify that reviews are correctly linked to transactions and profiles, and that profile stats reflect real marketplace activity.
- **UI test design:** Selenium WebDriver against a live Flask test server, using the existing page-object pattern (`tests/ui/selenium/pages/`).
- **Pipeline stage:** test

### 3.5 Acceptance Testing

- **Method:** Sprint Review demonstration, manual browser testing, Selenium UI flow.
- **Assessor:** Tutor / Product Owner / Team reviewer.
- **Criteria:** Each Sprint 4 user story must be checked against its Acceptance Criteria before moving the issue to Done.
- **Evidence:** GitLab issue checklist, merge request, CI pipeline result, and this test plan.

---

## 4. Test Items

This section follows the Lesson 7 test plan structure by listing specific items to be tested, related user stories, cyclomatic complexity, minimum tests required, and risk. Cyclomatic complexity values were measured using `radon cc`.

### 4.1 Unit Test Items

| Function / Helper | Related User Story | Cyclomatic Complexity | Minimum Tests Required | Risk / Priority |
| --- | --- | ---: | ---: | --- |
| `_validate_rating()` | #38 / #44 Rating validation | 6 | 8 | High — must reject missing, non-integer, boolean, out-of-range, and float ratings for both review directions. |
| `_check_transaction_review_access()` | #38 / #44 Shared transaction-review validation | 4 | 6 | High — must enforce authentication, transaction existence, and the correct role (seller or buyer) for each endpoint. |
| `submit_seller_review()` | #38 Seller reviews buyer | 5 | 5 | High — must save a linked review only for the transaction's actual seller. |
| `submit_buyer_review()` | #44 Buyer reviews seller | 5 | 5 | High — must save a linked review only for the transaction's actual buyer. |
| `create_review()` | #38 / #44 Review persistence | 1 | 3 | High — must persist `transaction_id`, `reviewer_id`, `reviewed_user_id`, `rating`, and `comment` correctly. |
| `get_transaction_by_id()` | #38 / #44 Transaction lookup | 2 | 2 | High — must return `None` safely for a non-existent transaction. |
| `get_reviews_for_user()` | Retrieve reviews for a user | 2 | 3 | Medium — must return only reviews where the user is the reviewed party, newest first. |
| `get_user_rating_stats()` | #36 Average rating calculation | 2 | 3 | High — must return `None` average with 0 reviews, and a numerically correct average otherwise. |
| `get_user_reviews()` (route) | Retrieve reviews for a user | 2 | 3 | Medium — must 404 for an unknown user and return an empty list for a user with no reviews. |
| `_format_rating()` | #36 Rating display formatting | 3 | 4 | Medium — must drop a trailing `.0` for whole numbers, keep fractional ratings as-is, and handle `None`. |
| `get_user_profile_stats()` | Profile marketplace stats | 4 | 4 | Medium — must aggregate active listings, total sales, review count, and average rating correctly for one user. |
| `_trust_badge()` | Profile marketplace stats | 4 | 4 | Low — must return the correct badge tier (`New Seller`, `Active Seller`, `Trusted Seller`, `Top Seller`) at each threshold boundary. |
| `_response_rate()` | Profile marketplace stats | 4 | 3 | Low — must return `None` with zero offers, and a correctly rounded percentage otherwise. |
| `get_active_listings_by_seller()` | Profile marketplace stats | 2 | 2 | Medium — must return only that seller's currently active listings. |
| `get_sold_listings_by_seller()` | Profile marketplace stats | 2 | 2 | Medium — must return only listings with an accepted offer, with buyer detail attached. |
| `profile()` / `view_profile()` (routes) | View another user's profile | ~2 / ~3 (manual count) | 6 | High — `is_own_profile` must be `True` only on `/profile`, and viewing your own ID via `/profile/<id>` must redirect to `/profile`. |

### 4.2 API / Route Test Items

| Route / Behaviour | Related User Story | Implemented Function / Scope | Minimum Tests Required | Risk / Priority |
| --- | --- | --- | ---: | --- |
| `POST /api/transactions/<id>/review` | #38 Seller reviews buyer | `submit_seller_review()` | 8 | High — valid rating with/without comment, invalid ratings, missing/incomplete transaction, wrong role, unauthenticated. |
| `POST /api/transactions/<id>/buyer-review` | #44 Buyer reviews seller | `submit_buyer_review()` | 8 | High — mirrors the seller-review test matrix for the buyer direction. |
| `GET /api/users/<id>/reviews` | Retrieve reviews for a user | `get_user_reviews()` | 3 | Medium — existing user with reviews, existing user with none, unknown user. |
| `GET /profile` | View own profile | `profile()` via `_render_profile_page()` | 4 | High — shows Edit Profile / Account Details, correct average rating and review count, redirects when logged out. |
| `GET /profile/<id>` | View another user's profile | `view_profile()` via `_render_profile_page()` | 5 | High — hides Edit Profile / Account Details, shows active/sold listings and trust badge, redirects to `/profile` for your own ID, redirects for an unknown ID. |

### 4.3 UI / Acceptance Test Items

| User Flow | Related User Story | Test Type | Priority | Expected Evidence |
| --- | --- | --- | --- | --- |
| Seller submits a rating and comment for the buyer | #38 Seller reviews buyer | API / acceptance | High | API evidence that a review is created, linked to the transaction, and visible on the buyer's profile. |
| Buyer submits a rating and comment for the seller | #44 Buyer reviews seller | API / acceptance | High | API evidence that a review is created, linked to the transaction, and visible on the seller's profile. |
| A user views another user's profile and average rating | View another user's profile | Selenium + API / acceptance | High | Browser evidence that the profile page shows the average rating, review list, and marketplace stats, without an Edit Profile button. |
| A seller leaves a review for a buyer from Transaction History | #38 Seller reviews buyer | Selenium / acceptance | High | Browser evidence that clicking "Leave a review" on a completed sale opens the review modal, submits successfully, and the button changes to a "Reviewed" state. |
| Whole-number average rating displays without a trailing `.0` | #36 Average rating display | Manual + unit / acceptance | Medium | Browser/unit evidence that a `4.0` average renders as `4`, while `4.5` still renders as `4.5`. |

---

## 5. Test Environment

| Area | Configuration |
| --- | --- |
| Language | Python 3.x |
| Framework | Flask |
| Frontend | HTML5, Bootstrap, Jinja templates, vanilla JavaScript (`fetch`) |
| Database | SQLite test database / isolated SQLite fixture (`tmp_path`) |
| Test framework | pytest |
| Coverage tool | pytest-cov |
| Static analysis | pylint |
| Complexity analysis | radon |
| Browser automation | Selenium WebDriver (Chrome, headless) |
| CI/CD platform | GitLab CI/CD |
| Dependencies | Installed from `requirements.txt` / `requirements-dev.txt` |
| Browser for manual verification | Chrome / Edge / Firefox |

### Test Isolation Rule

Each automated test must create and clean up its own test data. Tests must not depend on the production `swaplah.db` file, local browser state, or data created by another test. Integration and Selenium tests use an isolated temporary SQLite database created via the `tmp_path` pytest fixture, monkeypatched onto `app.db.DATABASE`.

---

## 6. Entry and Exit Criteria

### 6.1 Entry Criteria

Testing can begin when:

- Sprint 4 feature branch is pushed to GitLab.
- Merge Request is created.
- No Python syntax errors exist.
- Related Sprint 4 PBI has a clear user story and acceptance criteria.
- Required test files are added under `tests/unit`, `tests/api`, or `tests/ui/selenium`.
- Flask app can run locally in development mode.
- Test database setup is available.
- pylint validate stage passes with score `>= 7.0`.

### 6.2 Exit Criteria — Verification

Sprint 4 verification is complete when:

- [x] All implemented unit tests pass with 0 failures.
- [x] All implemented API / route tests pass with 0 failures.
- [x] Real-database integration tests confirm review access control and profile stats behaviour.
- [ ] Selenium UI test passes in the CI pipeline (requires the Selenium browser service; not executable in this local environment — see Section 8).
- [x] Test coverage is at least 60%.
- [x] pylint score is at least 7.0/10.
- [x] radon complexity check shows no implemented function exceeds complexity 10.
- [ ] GitLab pipeline is green on the Merge Request.
- [x] No new SAST or secret detection issues are introduced.
- [x] No generated files such as `.env`, `.coverage`, `.venv`, `__pycache__`, or `swaplah.db` are committed.

### 6.3 Exit Criteria — Validation

Sprint 4 validation is complete when:

- [ ] Product Owner / Tutor acceptance criteria are verified through issue checklist, MR evidence, and test results.
- [ ] All Sprint 4 test cases are updated to Passing.
- [ ] Sprint 4 work items are closed and moved to Done only after MRs are merged and checklists are complete.
- [ ] At least one teammate reviews and approves each Merge Request.
- [ ] Related GitLab issues are moved to Done after the MR is merged and the issue checklist is complete.

### 6.4 Suspension and Resumption Criteria

| Criteria Type | Condition |
| --- | --- |
| Suspension criteria | Testing stops if the Flask app cannot start, database setup fails, or the CI runner (or Selenium browser service) fails for reasons unrelated to the code. |
| Resumption criteria | Testing resumes after the blocking defect is fixed, database setup works, and the pipeline can run again. |

---

## 7. Sprint 4 Test Cases

| Test ID | Module | Related PBI | Description | Type | Preconditions | Steps | Expected Result | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TC-S4-SELLREV-001 | Seller Reviews Buyer | #38 | Seller submits a rating and comment | Positive | Transaction is completed, current user is its seller | 1. Send `POST /api/transactions/<id>/review` with `rating`, `comment` | Review is created (201), linked to the transaction and the buyer | Pass |
| TC-S4-SELLREV-002 | Seller Reviews Buyer | #38 | Comment is optional | Positive | Transaction is completed, current user is its seller | 1. Send `POST /api/transactions/<id>/review` with only `rating` | Review is created (201) with an empty comment | Pass |
| TC-S4-SELLREV-003 | Seller Reviews Buyer | #38 | Reject rating outside 1–5 | Negative | Transaction is completed | 1. Send `rating: 0, 6, -1, 4.5, "five", true, null` | Request is blocked with a `400` error for every case | Pass |
| TC-S4-SELLREV-004 | Seller Reviews Buyer | #38 | Reject when transaction does not exist | Negative | No transaction with the given ID | 1. Send `POST /api/transactions/999999/review` | Request is blocked with a `404` error | Pass |
| TC-S4-SELLREV-005 | Seller Reviews Buyer | #38 | Reject the buyer of the same transaction | Negative / Security | Current user is the transaction's buyer, not seller | 1. Send `POST /api/transactions/<id>/review` | Request is blocked with a `403` error | Pass |
| TC-S4-SELLREV-006 | Seller Reviews Buyer | #38 | Reject an unrelated user | Negative / Security | Current user has no relation to the transaction | 1. Send `POST /api/transactions/<id>/review` | Request is blocked with a `403` error | Pass |
| TC-S4-SELLREV-007 | Seller Reviews Buyer | #38 | Block logged-out user | Negative / Security | User is not logged in | 1. Clear session 2. Send `POST /api/transactions/<id>/review` | Request is blocked with a `401` error | Pass |
| TC-S4-BUYREV-001 | Buyer Reviews Seller | #44 | Buyer submits a rating and comment | Positive | Transaction is completed, current user is its buyer | 1. Send `POST /api/transactions/<id>/buyer-review` with `rating`, `comment` | Review is created (201), linked to the transaction and the seller | Pass |
| TC-S4-BUYREV-002 | Buyer Reviews Seller | #44 | Comment is optional | Positive | Transaction is completed, current user is its buyer | 1. Send `POST /api/transactions/<id>/buyer-review` with only `rating` | Review is created (201) with an empty comment | Pass |
| TC-S4-BUYREV-003 | Buyer Reviews Seller | #44 | Reject rating outside 1–5 | Negative | Transaction is completed | 1. Send `rating: 0, 6, -1, 4.5, "five", true, null` | Request is blocked with a `400` error for every case | Pass |
| TC-S4-BUYREV-004 | Buyer Reviews Seller | #44 | Reject when transaction does not exist | Negative | No transaction with the given ID | 1. Send `POST /api/transactions/999999/buyer-review` | Request is blocked with a `404` error | Pass |
| TC-S4-BUYREV-005 | Buyer Reviews Seller | #44 | Reject the seller of the same transaction | Negative / Security | Current user is the transaction's seller, not buyer | 1. Send `POST /api/transactions/<id>/buyer-review` | Request is blocked with a `403` error | Pass |
| TC-S4-BUYREV-006 | Buyer Reviews Seller | #44 | Reject an unrelated user | Negative / Security | Current user has no relation to the transaction | 1. Send `POST /api/transactions/<id>/buyer-review` | Request is blocked with a `403` error | Pass |
| TC-S4-BUYREV-007 | Buyer Reviews Seller | #44 | Block logged-out user | Negative / Security | User is not logged in | 1. Clear session 2. Send `POST /api/transactions/<id>/buyer-review` | Request is blocked with a `401` error | Pass |
| TC-S4-GETREV-001 | Retrieve Reviews | Retrieve reviews | Existing user with reviews | Positive | User has received 1+ reviews | 1. Send `GET /api/users/<id>/reviews` | Response includes all reviews received by that user | Pass |
| TC-S4-GETREV-002 | Retrieve Reviews | Retrieve reviews | Existing user with no reviews | Positive | User has received 0 reviews | 1. Send `GET /api/users/<id>/reviews` | Response returns an empty `reviews` list, no error | Pass |
| TC-S4-GETREV-003 | Retrieve Reviews | Retrieve reviews | Unknown user is rejected | Negative | User ID does not exist | 1. Send `GET /api/users/999999/reviews` | Request is blocked with a `404` error | Pass |
| TC-S4-RATING-001 | Average Rating | #36 | Average is calculated from all reviews | Positive | User has reviews with ratings 4 and 5 | 1. Compute average via `get_user_rating_stats()` | Average equals `4.5` | Pass |
| TC-S4-RATING-002 | Average Rating | #36 | Average is `None` when no reviews exist | Positive | User has 0 reviews | 1. Compute average via `get_user_rating_stats()` | `average_rating` is `None`, `review_count` is `0` | Pass |
| TC-S4-RATING-003 | Average Rating Display | #36 | Whole-number average has no trailing `.0` | Positive | Average rating is exactly `4.0` | 1. Render `4.0 | format_rating` | Output is `"4"`, not `"4.0"` | Pass |
| TC-S4-RATING-004 | Average Rating Display | #36 | Fractional average keeps its decimal | Positive | Average rating is `4.5` | 1. Render `4.5 | format_rating` | Output is `"4.5"` | Pass |
| TC-S4-PROFILE-001 | Profile Page | View own profile | Own profile shows edit controls | Positive | User is logged in, viewing `/profile` | 1. Send `GET /profile` | Response shows "Edit profile" button and Account Details card | Pass |
| TC-S4-PROFILE-002 | Profile Page | View another user's profile | Another user's profile hides edit controls | Positive | User A views `GET /profile/<user_B_id>` | 1. Send `GET /profile/<id>` as a different logged-in user | Response hides "Edit profile" button and Account Details card | Pass |
| TC-S4-PROFILE-003 | Profile Page | View another user's profile | Viewing your own ID redirects to `/profile` | Positive | Logged-in user requests `/profile/<own_id>` | 1. Send `GET /profile/<own_id>` | Response redirects to `/profile` | Pass |
| TC-S4-PROFILE-004 | Profile Page | View another user's profile | Unknown user ID redirects with a flash message | Negative | User ID does not exist | 1. Send `GET /profile/999999` | Response redirects to the homepage with an error flash | Pass |
| TC-S4-PROFILE-005 | Profile Page | Profile marketplace stats | Trust badge reflects sales tier | Positive | Seller has 0, 3, 6, and 22 completed sales in 4 sub-cases | 1. Compute `get_user_profile_stats()` for each sub-case | Badge is `New Seller`, `Active Seller`, `Trusted Seller`, `Top Seller` respectively | Pass |
| TC-S4-PROFILE-006 | Profile Page | Profile marketplace stats | Response rate is calculated correctly | Positive | Seller has 4 offers, 3 responded to | 1. Compute `get_user_profile_stats()` | `response_rate` equals `75` | Pass |
| TC-S4-PROFILE-007 | Profile Page | Profile marketplace stats | Response rate is `None` with no offers | Positive | Seller has 0 offers received | 1. Compute `get_user_profile_stats()` | `response_rate` is `None` | Pass |
| TC-S4-REG-001 | Regression | Sprint 1–3 | Login, offers, and transaction history still work after Sprint 4 changes | Regression | App is running | 1. Register 2. Log in 3. Submit and accept an offer 4. View transaction history | All Sprint 1–3 flows continue to work without error | Pass |

---

## 8. Manual and UI Verification Evidence

Sprint 4 introduces the project's first Selenium UI test alongside manual browser checks.

| Verification Flow | Related PBI | Steps Verified | Status |
| --- | --- | --- | --- |
| View another user's profile in the browser | View another user's profile | Logged in as a buyer, opened a seller's public profile, confirmed average rating, review list, and marketplace stats render, and that the Edit Profile button is absent. | Pass (manual) |
| Leave a review from Transaction History | #38 | Logged in as a seller with a completed sale, opened Transaction History, clicked "Leave a review", submitted a rating and comment, confirmed the button changed to a "Reviewed" state. | Pass (manual) |
| Selenium: profile view + leave-a-review flow | View another user's profile / #38 | `tests/ui/selenium/test_profile_review_selenium.py` drives the same flow end to end in a headless Chrome browser. | **Not executed** — no Selenium browser/driver is installed in this development environment (`pip install selenium` plus a Chrome/Chromedriver install is required; this matches the existing project constraint noted for all prior Selenium suites). The test is written to the project's existing page-object conventions and is expected to run in the GitLab CI pipeline's dedicated Selenium service. |

---

## 9. Regression Testing

Before merging any Sprint 4 Merge Request, the following regression checks must pass:

| Regression Area | Command / Method | Expected Result |
| --- | --- | --- |
| Full automated test suite (excl. Selenium) | `python -m pytest -q --ignore=tests/ui/selenium` | All implemented tests pass. |
| Unit coverage | `python -m pytest tests/unit --cov=app --cov-fail-under=60` | Coverage is at least 60%. |
| Linting | `python -m pylint app tests --fail-under=7.0` | Score is at least 7.0/10. |
| Complexity | `python -m radon cc app/ -s` | No implemented function exceeds complexity 10. |
| Manual seller-review flow | Browser test | Seller can leave a review for the buyer from Transaction History. |
| Manual buyer-review flow | Browser test | Buyer can leave a review for the seller from Transaction History. |
| Manual profile view flow | Browser test | Any logged-in user can view another user's profile, rating, and reviews. |
| Manual Sprint 1–3 regression | Browser test | Login, registration, listings, offers, and transaction history still work. |

---

## 10. Test Data

| Data Item | Example |
| --- | --- |
| Completed transaction | Created via `accept_offer()`; has a `seller_id`, `buyer_id`, `transaction_type`, and `amount`. |
| Valid seller review | `{"rating": 5, "comment": "Prompt payment, smooth handover."}` submitted by the transaction's seller. |
| Valid buyer review | `{"rating": 4, "comment": "Item exactly as described."}` submitted by the transaction's buyer. |
| Invalid rating values | `0`, `6`, `-1`, `4.5`, `"five"`, `true`, `null`. |
| User with whole-number average rating | Two reviews rated `4` and `4` → average `4.0`, displayed as `4`. |
| User with fractional average rating | Two reviews rated `4` and `5` → average `4.5`, displayed as `4.5`. |
| User with no reviews | New user account with zero rows in `reviews`. |
| Seller trust badge tiers | `0` sales → `New Seller`; `0` sales with an active listing → `Active Seller`; `5`+ sales → `Trusted Seller`; `20`+ sales → `Top Seller`. |
| Seller response rate | `4` offers received, `3` with a non-`Pending` status → `75%` response rate. |

---

## 11. Risks and Contingencies

| Risk | Probability | Impact | Mitigation / Contingency |
| --- | --- | --- | --- |
| A buyer submits a review through the seller-review endpoint (or vice versa) | Medium | High | `_check_transaction_review_access()` explicitly checks `transaction[f"{role}_id"]`, with negative tests for both directions. |
| A rating outside 1–5, or a non-integer rating (float, string, boolean), is accepted | Medium | High | `_validate_rating()` explicitly checks type and range before any database write; parametrized negative tests cover 7 invalid inputs per endpoint. |
| A review is created for a transaction that does not exist or was never completed | Medium | High | `get_transaction_by_id()` returns `None` for a missing row; the route returns `404` before any write occurs. |
| Average rating displays a misleading `4.0` instead of `4` | Low | Low | `_format_rating()` filter strips the trailing `.0`; unit tests cover both whole-number and fractional cases. |
| Another user's private account details (student ID, contact number) leak on their public profile | Medium | High | `is_own_profile` gates the Account Details card and Edit Profile button in the template; tests assert both are absent when viewing another user. |
| Profile stats (trust badge, response rate) miscalculate at tier boundaries | Low | Medium | Boundary-value unit tests seed exact sale counts (0, 4, 5, 19, 20) and offer-response counts to confirm each threshold. |
| Selenium UI test cannot run in all environments | High | Low | Documented in Section 8; test is written to existing conventions and runs in the CI pipeline's Selenium service even where a local browser/driver is unavailable. |
| Test data affects the real database | Medium | High | Use isolated temporary SQLite database fixtures (`tmp_path`) and avoid the production `swaplah.db`. |

---

## 12. Related Links

- [Sprint board](https://gitlab.com/nyp-sg/pet/it2112/26s1/it2112-03/assignment/team_2/swaplah/-/boards)
- [CI/CD pipelines](https://gitlab.com/nyp-sg/pet/it2112/26s1/it2112-03/assignment/team_2/swaplah/-/pipelines)
- [Merge requests](https://gitlab.com/nyp-sg/pet/it2112/26s1/it2112-03/assignment/team_2/swaplah/-/merge_requests)
- Unit tests: `tests/unit/`
- API tests: `tests/api/`
- Selenium UI tests: `tests/ui/selenium/`
- AI usage logs: `AI/`

---

## 13. Sprint 4 Definition of Done

### Verification

- [x] Code committed through a feature branch and Merge Request.
- [ ] Merge Request reviewed and approved by at least one teammate.
- [x] Code passes pylint with score `>= 7.0` (currently `10.00/10`).
- [x] Cyclomatic complexity for implemented functions does not exceed 10.
- [x] All implemented unit tests pass.
- [x] All implemented API / route tests pass.
- [x] Real-database integration tests for review access control and profile stats pass.
- [ ] Selenium UI test passes in the GitLab CI pipeline's Selenium service (not runnable locally in this environment).
- [x] Test coverage is at least 60%.
- [ ] GitLab pipeline is green on the Merge Request.
- [x] No new linting, SAST, or secret detection issues are introduced.

### Validation

- [ ] Implemented acceptance criteria are confirmed with Product Owner / Tutor.
- [ ] All Sprint 4 test cases are updated to Passing (locally verified; CI/Selenium confirmation pending).
- [ ] Related GitLab issues are moved to Done after the MRs are merged and the issue checklists are complete.
- [ ] Sprint 4 board shows Sprint 4 work items as Closed / Done.

---

## 14. AI Prompt and Refinement Evidence

### AI Prompt Used

> Generate a Sprint 4 test plan for SwapLah Assignment 2. Sprint 4 focuses on Reviews, Ratings, and Profile Stats — the area Sprint 3 explicitly marked out of scope. Cover a seller leaving a rating and comment for a buyer, a buyer leaving a rating and comment for a seller, retrieving reviews for a user, average rating calculation and display formatting, viewing another user's profile with correct own-profile-vs-other visibility, and the profile page's enriched marketplace stats (active/sold listings, trust badge, response rate). Follow the same Lesson 7 test plan format used in Sprints 1–3, with Introduction, Scope, Test Approach, Test Items, Test Environment, Entry and Exit Criteria, Risks, Regression Testing, Definition of Done, and a full test case table with positive and negative cases.

### Refinement Made

The AI-generated draft was reviewed and refined against the actual implemented code rather than assumed behaviour. Cyclomatic complexity values in Section 4 were measured directly using `radon cc` against `app/db.py`, `app/routes/reviews.py`, and `app/__init__.py`; the two nested profile route functions (`profile()`, `view_profile()`) are not broken out individually by this version of radon (they are closures registered inside `_register_profile_routes()`), so their complexity is noted as a manual count based on direct code inspection rather than a radon-reported figure — this is called out explicitly in the table rather than presented as a precise tool measurement.

Test case counts and IDs were cross-checked against the real test files added for this sprint (`tests/unit/test_profile_stats_db_unit.py`, `tests/unit/test_profile_routes_unit.py`, `tests/api/test_profile_stats_api.py`, plus the pre-existing `tests/api/test_seller_review_api.py`, `tests/unit/test_seller_review_unit.py`, `tests/api/test_buyer_review_api.py`, `tests/unit/test_buyer_review_unit.py`, `tests/api/test_user_reviews_api.py`, `tests/unit/test_reviews_unit.py`) to ensure every listed test case corresponds to an actual test.

Several Exit Criteria and Definition of Done checkboxes were deliberately left unchecked (`[ ]`) rather than marked complete, because they depend on actions this environment cannot perform or verify: MR review/approval by a teammate, the GitLab CI pipeline actually running (including its dedicated Selenium browser service), and Product Owner / Tutor sign-off. The Selenium UI test (Section 8) was written to the project's existing page-object conventions but could not be executed locally, since no Selenium browser or driver is installed in this development environment — this mirrors the same constraint documented for the project's other Selenium suites and is called out honestly rather than claimed as passing.

### Manual Review Evidence

- Test cases were mapped to the Sprint 4 PBIs (#38, #44, #36) and to the two review-retrieval / profile-viewing stories that predate formal issue numbering in this codebase.
- Unit test items were checked against the implemented rating-validation, transaction-review-access, and profile-stats functions.
- API test items were checked against the required review-submission, review-retrieval, and profile routes.
- Both review directions (#38 seller→buyer, #44 buyer→seller) were specifically verified with negative tests confirming the *other* party is rejected, using a real temporary SQLite database seeded with an actual accepted offer/transaction rather than mocked database calls.
- Trust badge and response rate boundary values were verified with exact seeded sale/offer counts rather than approximate values, to confirm each tier threshold precisely.
- All listed test cases were changed to `Pass` only after being run locally against the actual test files described above.
