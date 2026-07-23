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

Sprint 4 focuses on **Reviews, Ratings, and Profile Viewing** — the area Sprint 3 explicitly marked out of scope ("Review and rating testing... outside the Sprint 3 Offers and Transactions scope"). Sprint 4 verifies that a buyer can leave a 1–5 star rating and optional comment for the seller of a completed transaction, that the review is correctly rejected when submitted by the wrong participant or for an incomplete transaction, that a user's average rating is calculated correctly from all reviews received, and that any user can view another user's profile — including their rating and reviews — without exposing that user's private account details or edit controls.

### Sprint 4 Features Covered

| PBI / Issue | Sprint 4 User Story | Current Status | Priority |
| --- | --- | --- | --- |
| [#44](https://gitlab.com/nyp-sg/pet/it2112/26s1/it2112-03/assignment/team_2/swaplah/-/issues/44) | As a buyer, leave a 1–5 star rating and optional comment for the seller after a completed transaction | Closed / Done | High |
| [#36](https://gitlab.com/nyp-sg/pet/it2112/26s1/it2112-03/assignment/team_2/swaplah/-/issues/36) | A user's average rating is calculated from all reviews received | Closed / Done | Medium |
| Retrieve reviews for a user | As a marketplace user, retrieve all reviews for a user so feedback is visible | Closed / Done | Medium |
| View another user's profile | As a marketplace user, view another user's profile (rating, reviews) without exposing their private account details or edit controls | Closed / Done | High |

---

## 2. Scope

### 2.1 In Scope

The following items are included in Sprint 4 testing:

- Unit tests for rating validation, review-target validation (the review must be for the seller of the transaction), completed-offer / buyer-ownership validation, and profile view access control (`is_own_profile`).
- API / route tests for:
  - `POST /api/reviews`
  - `GET /api/users/<user_id>/reviews` (existing coverage, referenced for completeness)
  - `GET /profile` and `GET /profile/<user_id>`
- Real-database integration tests (seeded SQLite data, not mocks) confirming:
  - A review is only accepted from the buyer of an **Accepted** offer.
  - A review is rejected for a **Pending** or **Rejected** offer.
  - A review is rejected when the `reviewee_id` does not match the listing's actual seller.
  - Average rating and review count reflect all reviews received by a user.
  - `is_own_profile` correctly hides the Edit Profile button and Account Details card on another user's profile, and shows them on your own.
- Selenium UI test for viewing another user's profile in a real browser.
- Regression testing to ensure Sprint 1–3 features continue to pass after Sprint 4 changes.
- Static testing using pylint.
- Cyclomatic complexity checking using radon (where the tool can parse the file — see Section 14 for a known limitation).
- Coverage checking using pytest-cov.
- GitLab CI/CD pipeline verification.
- AI prompt and refinement documentation.

### 2.2 Out of Scope

| Item | Reason |
| --- | --- |
| Seller leaving a review for the buyer | Not implemented on this branch — only the buyer → seller review direction (#44) exists here. |
| Editing or deleting an existing review | Not part of the Sprint 4 user stories; reviews are currently write-once. |
| Enriched profile marketplace stats (trust badge, response rate, real sales count) | The profile page currently displays placeholder values (e.g. a hardcoded "Top Seller" badge and "37" total sales) rather than data derived from real listings/offers; this is not yet implemented on this branch. |
| Review moderation / reporting | Handled under the Admin / moderation epic, not Sprint 4. |
| Real payment processing | SwapLah does not include real payment gateways. |
| Full cross-browser Selenium matrix | One representative Selenium flow is used for Sprint 4; a full Edge/Firefox matrix is out of scope. |
| Full security penetration testing | GitLab SAST, dependency scanning, and secret detection are used for automated security checks instead. |

---

## 3. Test Approach

### 3.1 Testing Pyramid Target

| Level | Target Count | Tool | Pipeline Stage | Purpose |
| --- | ---: | --- | --- | --- |
| Unit tests | 25+ | pytest | test | Verify rating validation, review-target validation, and profile view access control in isolation using monkeypatching. |
| API / Route tests | 20+ | pytest + Flask test client | test | Verify HTTP route behaviour end to end, including real-database integration tests for review submission and profile viewing. |
| Selenium UI flow | 1 Sprint 4 flow | Selenium + pytest | test (UI) | Verify viewing another user's profile in a real browser. |
| Static analysis | All `.py` files | pylint >= 7.0 | lint | Detect style, structure, and code quality issues. |
| Complexity check | All application functions | radon | lint | Confirm functions are maintainable and testable. |
| Coverage check | Application logic | pytest-cov | test | Confirm at least 60% application logic coverage. |

### 3.2 Static Testing

- **Tool:** pylint
- **Threshold:** score must be `>= 7.0/10`
- **Purpose:** Detect syntax problems, unused imports, naming issues, overly long functions, and poor code structure before dynamic tests run.
- **Pipeline stage:** lint

### 3.3 Complexity Testing

- **Tool:** radon
- **Threshold:** cyclomatic complexity per function should not exceed 10.
- **Purpose:** Identify functions that are difficult to test or should be refactored.
- **Pipeline stage:** lint
- **Rule:** If a function has complexity above 10, it is treated as high risk and should be refactored or covered with additional tests before merge.
- **Known limitation:** `app/db.py` and `app/routes/reviews.py` currently contain a byte-order-mark (BOM) character that causes this version of `radon` to fail parsing them (`ERROR: invalid non-printable character U+FEFF`). Complexity figures for functions in these two files (Section 4.1) were therefore counted manually by inspection rather than measured by the tool, and are marked accordingly. This does not affect pylint or pytest, which parse both files without issue.

### 3.4 Dynamic Testing

- **Tools:** pytest, pytest-cov, Flask test client, Selenium
- **Minimum coverage required:** `>= 60%` application logic coverage
- **Team stretch target:** `>= 70%` where possible
- **Unit test design:** white-box testing — route-level tests use monkeypatching to isolate routes from the database layer.
- **API / route test design:** black-box testing against the user story and acceptance criteria, using the Flask test client against a real temporary SQLite database.
- **Integration test design:** real temporary SQLite database seeded with users, listings, and offers, used to verify that reviews are only accepted from the correct buyer of a completed (`Accepted`) offer.
- **UI test design:** Selenium WebDriver against a live Flask test server, using the existing page-object pattern (`tests/ui/selenium/pages/`).
- **Pipeline stage:** test

### 3.5 Acceptance Testing

- **Method:** Sprint Review demonstration, manual browser testing, Selenium UI flow.
- **Assessor:** Tutor / Product Owner / Team reviewer.
- **Criteria:** Each Sprint 4 user story must be checked against its Acceptance Criteria before moving the issue to Done.
- **Evidence:** GitLab issue checklist, merge request, CI pipeline result, and this test plan.

---

## 4. Test Items

This section follows the Lesson 7 test plan structure by listing specific items to be tested, related user stories, cyclomatic complexity, minimum tests required, and risk.

### 4.1 Unit Test Items

| Function / Helper | Related User Story | Cyclomatic Complexity | Minimum Tests Required | Risk / Priority |
| --- | --- | ---: | ---: | --- |
| `_rating_error()` | #44 Rating validation | 4 (manual count — see 3.3) | 7 | High — must reject missing, non-integer, boolean, out-of-range, and float ratings. |
| `_completed_buyer_offer_error()` | #44 Completed-offer / buyer-ownership validation | 4 (manual count) | 4 | High — must reject a missing offer, a non-`Accepted` offer, and a non-buyer submitter. |
| `_review_target_error()` | #44 Review-target validation | 3 (manual count) | 3 | High — must reject a `reviewee_id` that does not match the listing's actual seller, and accept a matching or omitted `reviewee_id`. |
| `submit_review()` (route) | #44 Buyer reviews seller | 5 (manual count) | 8 | High — must chain login, rating, offer, and target validation correctly and persist the review with the right average-rating response. |
| `create_review()` | #44 / #36 Review persistence | 1 (manual count) | 2 | High — must persist `reviewer_id`, `reviewed_user_id`, `rating`, and `comment` correctly, defaulting an omitted comment to an empty string. |
| `get_user_rating_stats()` | #36 Average rating calculation | 2 (manual count) | 3 | High — must return `None` average with 0 reviews, and a numerically correct average otherwise. |
| `get_reviews_for_user()` | Retrieve reviews for a user | 1 (manual count) | 2 | Medium — must return only reviews where the user is the reviewed party. |
| `api_user_reviews()` (route) | Retrieve reviews for a user | 2 | 3 | Medium — must 404 for an unknown user and return an empty list for a user with no reviews. |
| `profile()` / `view_profile()` (routes) | View another user's profile | 2 / 3 | 6 | High — `is_own_profile` must be `True` only on `/profile`, and viewing your own ID via `/profile/<id>` must redirect to `/profile`. |
| `_get_logged_in_user_or_redirect()` | View own profile | 3 | 2 | Medium — must redirect to login when logged out or when the session user no longer exists. |

### 4.2 API / Route Test Items

| Route / Behaviour | Related User Story | Implemented Function / Scope | Minimum Tests Required | Risk / Priority |
| --- | --- | --- | ---: | --- |
| `POST /api/reviews` | #44 Buyer reviews seller | `submit_review()` | 10 | High — valid rating with/without comment, invalid ratings, missing/non-existent offer, non-`Accepted` offer, non-buyer submitter, mismatched `reviewee_id`, unauthenticated. |
| `GET /api/users/<id>/reviews` | Retrieve reviews for a user | `api_user_reviews()` | 3 (existing) | Medium — existing user with reviews, existing user with none, unknown user. |
| `GET /profile` | View own profile | `profile()` | 4 | High — shows Edit Profile / Account Details, correct average rating and review count, redirects when logged out. |
| `GET /profile/<id>` | View another user's profile | `view_profile()` | 5 | High — hides Edit Profile / Account Details, shows the seller's real rating and reviews, redirects to `/profile` for your own ID, redirects for an unknown ID. |

### 4.3 UI / Acceptance Test Items

| User Flow | Related User Story | Test Type | Priority | Expected Evidence |
| --- | --- | --- | --- | --- |
| Buyer submits a rating and comment for the seller | #44 Buyer reviews seller | API / acceptance | High | API evidence that a review is created and visible on the seller's profile. |
| A user views another user's profile and average rating | View another user's profile | Selenium + API / acceptance | High | Browser evidence that the profile page shows the average rating and review list, without an Edit Profile button or Account Details card. |
| Average rating reflects all reviews received | #36 Average rating calculation | Unit / acceptance | Medium | Unit evidence that the average is recalculated correctly as reviews accumulate. |

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
| Dependencies | Installed from `requirements.txt` |
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
- [x] Real-database integration tests confirm review submission access control and profile-view behaviour.
- [ ] Selenium UI test passes in the CI pipeline (requires the Selenium browser service; not executable in this local environment — see Section 8).
- [x] Test coverage is at least 60%.
- [x] pylint score is at least 7.0/10.
- [ ] radon complexity check passes for all files (blocked for `app/db.py` and `app/routes/reviews.py` by a pre-existing BOM encoding issue — see Section 3.3).
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
| TC-S4-SUBMIT-001 | Submit Review | #44 | Buyer submits a rating and comment for an accepted offer | Positive | Offer is `Accepted`, current user is its buyer | 1. Send `POST /api/reviews` with `offer_id`, `rating`, `comment` | Review is created (201) for the listing's seller | Pass |
| TC-S4-SUBMIT-002 | Submit Review | #44 | Comment is optional | Positive | Offer is `Accepted`, current user is its buyer | 1. Send `POST /api/reviews` with only `offer_id`, `rating` | Review is created (201) with an empty comment | Pass |
| TC-S4-SUBMIT-003 | Submit Review | #44 | Reject rating outside 1–5 | Negative | Offer is `Accepted` | 1. Send `rating: 0, 6, -1, 4.5, "five", true, null` | Request is blocked with a `400` error for every case | Pass |
| TC-S4-SUBMIT-004 | Submit Review | #44 | Reject a missing offer | Negative | No offer with the given ID | 1. Send `POST /api/reviews` with `offer_id: 999999` | Request is blocked with a `404` error | Pass |
| TC-S4-SUBMIT-005 | Submit Review | #44 | Reject a Pending offer | Negative | Offer status is `Pending` | 1. Send `POST /api/reviews` for the pending offer | Request is blocked with a `400` "Transaction not completed" error | Pass |
| TC-S4-SUBMIT-006 | Submit Review | #44 | Reject a Rejected offer | Negative | Offer status is `Rejected` | 1. Send `POST /api/reviews` for the rejected offer | Request is blocked with a `400` "Transaction not completed" error | Pass |
| TC-S4-SUBMIT-007 | Submit Review | #44 | Reject the seller of the same offer | Negative / Security | Current user is the offer's seller, not buyer | 1. Send `POST /api/reviews` as the seller | Request is blocked with a `403` error | Pass |
| TC-S4-SUBMIT-008 | Submit Review | #44 | Reject an unrelated user | Negative / Security | Current user has no relation to the offer | 1. Send `POST /api/reviews` as an unrelated user | Request is blocked with a `403` error | Pass |
| TC-S4-SUBMIT-009 | Submit Review | #44 | Reject a mismatched `reviewee_id` | Negative | `reviewee_id` does not match the listing's seller | 1. Send `POST /api/reviews` with an unrelated `reviewee_id` | Request is blocked with a `400` error | Pass |
| TC-S4-SUBMIT-010 | Submit Review | #44 | Block logged-out user | Negative / Security | User is not logged in | 1. Clear session 2. Send `POST /api/reviews` | Request is blocked with a `401` error | Pass |
| TC-S4-GETREV-001 | Retrieve Reviews | Retrieve reviews | Existing user with reviews | Positive | User has received 1+ reviews | 1. Send `GET /api/users/<id>/reviews` | Response includes all reviews received by that user | Pass |
| TC-S4-GETREV-002 | Retrieve Reviews | Retrieve reviews | Existing user with no reviews | Positive | User has received 0 reviews | 1. Send `GET /api/users/<id>/reviews` | Response returns an empty `reviews` list, no error | Pass |
| TC-S4-GETREV-003 | Retrieve Reviews | Retrieve reviews | Unknown user is rejected | Negative | User ID does not exist | 1. Send `GET /api/users/999999/reviews` | Request is blocked with a `404` error | Pass |
| TC-S4-RATING-001 | Average Rating | #36 | Average is calculated from all reviews | Positive | User has reviews with ratings 4 and 5 | 1. Compute average via `get_user_rating_stats()` | Average equals `4.5` | Pass |
| TC-S4-RATING-002 | Average Rating | #36 | Average is `None` when no reviews exist | Positive | User has 0 reviews | 1. Compute average via `get_user_rating_stats()` | `average_rating` is `None`, `review_count` is `0` | Pass |
| TC-S4-RATING-003 | Average Rating | #36 | Average updates as reviews accumulate | Positive | User starts with 1 review (rating 4) | 1. Compute average 2. Add a second review (rating 2) 3. Recompute average | First average is `4`, second average is `3` | Pass |
| TC-S4-PROFILE-001 | Profile Page | View own profile | Own profile shows edit controls | Positive | User is logged in, viewing `/profile` | 1. Send `GET /profile` | Response shows "Edit profile" button and Account Details card | Pass |
| TC-S4-PROFILE-002 | Profile Page | View another user's profile | Another user's profile hides edit controls | Positive | User A views `GET /profile/<user_B_id>` | 1. Send `GET /profile/<id>` as a different logged-in user | Response hides "Edit profile" button and Account Details card | Pass |
| TC-S4-PROFILE-003 | Profile Page | View another user's profile | Another user's profile shows their real rating | Positive | User B has 2 reviews with ratings 4 and 4 | 1. Send `GET /profile/<user_B_id>` | Response shows average rating `4` and "2 reviews" | Pass |
| TC-S4-PROFILE-004 | Profile Page | View another user's profile | Viewing your own ID redirects to `/profile` | Positive | Logged-in user requests `/profile/<own_id>` | 1. Send `GET /profile/<own_id>` | Response redirects to `/profile` | Pass |
| TC-S4-PROFILE-005 | Profile Page | View another user's profile | Unknown user ID redirects with a flash message | Negative | User ID does not exist | 1. Send `GET /profile/999999` | Response redirects to the homepage with an error flash | Pass |
| TC-S4-PROFILE-006 | Profile Page | View own profile | Own profile shows the empty-review state | Positive | User has 0 reviews | 1. Send `GET /profile` | Response shows "No reviews yet" | Pass |
| TC-S4-PROFILE-007 | Profile Page | View another user's profile | Logged-out user can still view another profile | Positive | No active session | 1. Send `GET /profile/<id>` with no session cookie | Response renders successfully (200) | Pass |
| TC-S4-REG-001 | Regression | Sprint 1–3 | Login, offers, and transaction history still work after Sprint 4 changes | Regression | App is running | 1. Register 2. Log in 3. Submit and accept an offer 4. View transaction history | All Sprint 1–3 flows continue to work without error | Pass |

---

## 8. Manual and UI Verification Evidence

| Verification Flow | Related PBI | Steps Verified | Status |
| --- | --- | --- | --- |
| View another user's profile in the browser | View another user's profile | Logged in as a buyer, opened a seller's public profile, confirmed average rating and review list render, and that the Edit Profile button and Account Details card are absent. | Pass (manual) |
| Selenium: view another user's profile | View another user's profile | `tests/ui/selenium/test_view_profile_selenium.py` drives the same flow end to end in a headless Chrome browser. | **Not executed** — no Selenium browser/driver is installed in this development environment (`pip install selenium` plus a Chrome/Chromedriver install is required; this matches the existing project constraint noted for all prior Selenium suites). The test is written to the project's existing page-object conventions and is expected to run in the GitLab CI pipeline's dedicated Selenium service. |

---

## 9. Regression Testing

Before merging any Sprint 4 Merge Request, the following regression checks must pass:

| Regression Area | Command / Method | Expected Result |
| --- | --- | --- |
| Full automated test suite (excl. Selenium) | `python -m pytest -q --ignore=tests/ui/selenium` | All implemented tests pass. |
| Unit coverage | `python -m pytest tests/unit --cov=app --cov-fail-under=60` | Coverage is at least 60%. |
| Linting | `python -m pylint app tests --fail-under=7.0` | Score is at least 7.0/10. |
| Complexity | `python -m radon cc app/ -s` | No implemented function exceeds complexity 10 (excluding the two BOM-affected files noted in Section 3.3). |
| Manual buyer-review flow | API test | Buyer can submit a review for the seller of a completed offer. |
| Manual profile view flow | Browser test | Any logged-in or logged-out user can view another user's profile, rating, and reviews. |
| Manual Sprint 1–3 regression | Browser test | Login, registration, listings, offers, and transaction history still work. |

---

## 10. Test Data

| Data Item | Example |
| --- | --- |
| Accepted offer | `status: "Accepted"`; has a `buyer_id` and a listing with a known `seller_id`. |
| Pending offer | `status: "Pending"` — must be rejected for review submission. |
| Rejected offer | `status: "Rejected"` — must be rejected for review submission. |
| Valid review | `{"offer_id": 1, "rating": 5, "comment": "Prompt payment, smooth handover."}` submitted by the offer's buyer. |
| Invalid rating values | `0`, `6`, `-1`, `4.5`, `"five"`, `true`, `null`. |
| User with a whole-number average rating | Two reviews rated `4` and `4` → average `4`. |
| User with a fractional average rating | Two reviews rated `4` and `5` → average `4.5`. |
| User with no reviews | New user account with zero rows in `reviews`. |

---

## 11. Risks and Contingencies

| Risk | Probability | Impact | Mitigation / Contingency |
| --- | --- | --- | --- |
| A user who is not the buyer of the offer submits a review | Medium | High | `_completed_buyer_offer_error()` explicitly checks `offer["buyer_id"] == session["user_id"]`, with negative tests for the seller and an unrelated user. |
| A rating outside 1–5, or a non-integer rating (float, string, boolean), is accepted | Medium | High | `_rating_error()` explicitly checks type and range before any database write; parametrized negative tests cover 7 invalid inputs. |
| A review is created for an offer that is not yet `Accepted` | Medium | High | `_completed_buyer_offer_error()` returns an error for any non-`Accepted` status; both `Pending` and `Rejected` are tested explicitly. |
| A review is misattributed to the wrong seller via a spoofed `reviewee_id` | Medium | High | `_review_target_error()` cross-checks the supplied `reviewee_id` against the listing's real `seller_id` via `get_listing_owner()`. |
| Another user's private account details (student ID, contact number) leak on their public profile | Medium | High | `is_own_profile` gates the Account Details card and Edit Profile button in the template; tests assert both are absent when viewing another user. |
| Average rating does not update as new reviews are added | Low | Medium | `get_user_rating_stats()` recomputes `AVG(rating)` directly from the `reviews` table on every call; a unit test adds a second review and confirms the average changes. |
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
- [x] Code passes pylint with score `>= 7.0`.
- [ ] Cyclomatic complexity confirmed by radon for all files (blocked for two files by a pre-existing BOM issue — see Section 3.3; complexity was otherwise counted manually and stays well under 10).
- [x] All implemented unit tests pass.
- [x] All implemented API / route tests pass.
- [x] Real-database integration tests for review submission and profile viewing pass.
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

> Generate a Sprint 4 test plan for SwapLah Assignment 2. Sprint 4 focuses on Reviews, Ratings, and Profile Viewing — the area Sprint 3 explicitly marked out of scope. Cover a buyer leaving a rating and comment for a seller after a completed (Accepted) offer, rejecting reviews for incomplete or mismatched transactions, retrieving reviews for a user, average rating calculation, and viewing another user's profile with correct own-profile-vs-other visibility. Follow the same Lesson 7 test plan format used in Sprints 1–3, with Introduction, Scope, Test Approach, Test Items, Test Environment, Entry and Exit Criteria, Risks, Regression Testing, Definition of Done, and a full test case table with positive and negative cases.

### Refinement Made

The AI-generated draft was reviewed and refined against the actual implemented code on this branch rather than assumed behaviour. This branch implements only the buyer → seller review direction (`POST /api/reviews`, keyed by `offer_id`); it does **not** implement a seller → buyer review endpoint, and its profile page does not yet compute real marketplace stats (trust badge, response rate, sales count are placeholder values in the template). Both of these were moved to Section 2.2 (Out of Scope) rather than described as implemented, since claiming otherwise would misrepresent what this branch actually does.

Cyclomatic complexity in Section 4.1 could not be measured by `radon` for `app/db.py` and `app/routes/reviews.py`, because both files contain a byte-order-mark (BOM) character that this version of `radon` fails to parse (`ERROR: invalid non-printable character U+FEFF`). Rather than omit the column or fabricate tool output, each affected function's complexity was counted manually by reading the code (counting branches/conditions +1), and is explicitly labelled "(manual count)" in the table so it is not mistaken for a radon measurement. This limitation is also called out in Section 3.3, and the corresponding radon-related Exit Criteria and Definition of Done checkboxes are left unchecked rather than marked complete.

Test case counts and IDs were cross-checked against the real test files added for this sprint (`tests/unit/test_submit_review_unit.py`, `tests/api/test_submit_review_api.py`, `tests/unit/test_profile_view_unit.py`, `tests/api/test_profile_view_api.py`), plus the pre-existing `tests/api/test_user_reviews_api.py` for review retrieval, to ensure every listed test case corresponds to an actual test.

Several Exit Criteria and Definition of Done checkboxes were deliberately left unchecked (`[ ]`) rather than marked complete, because they depend on actions this environment cannot perform or verify: MR review/approval by a teammate, the GitLab CI pipeline actually running (including its dedicated Selenium browser service), and Product Owner / Tutor sign-off. The Selenium UI test (Section 8) was written to the project's existing page-object conventions but could not be executed locally, since no Selenium browser or driver is installed in this development environment — this mirrors the same constraint documented for the project's other Selenium suites and is called out honestly rather than claimed as passing.

### Manual Review Evidence

- Test cases were mapped to the Sprint 4 PBIs (#44, #36) and to the two review-retrieval / profile-viewing stories that predate formal issue numbering in this codebase.
- Unit test items were checked against the implemented rating-validation, offer-completion, and review-target-validation functions.
- API test items were checked against the required review-submission, review-retrieval, and profile routes.
- The buyer-only submission rule (#44) was specifically verified with negative tests confirming the seller and an unrelated third party are both rejected, using a real temporary SQLite database seeded with an actual `Accepted` offer rather than mocked database calls.
- The average-rating recalculation (#36) was verified by adding a second review mid-test and confirming the computed average changed correctly, rather than only checking a single static value.
- All listed test cases were changed to `Pass` only after being run locally against the actual test files described above.
