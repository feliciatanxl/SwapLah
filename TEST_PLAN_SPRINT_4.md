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

Sprint 4 focuses on **Reviews and Ratings**. The purpose of this test plan is to verify that either participant of a completed (`Accepted`) offer — buyer or seller — can leave a rating and comment for the other participant, that invalid or unauthorized review attempts are rejected, and that a user's profile page displays their aggregate marketplace stats (average rating, review count, total sales, trust badge, response rate) and public review history correctly, including the visibility difference between viewing your own profile and another user's profile.

### Sprint 4 Features Covered

| PBI / Issue | Sprint 4 User Story | Current Status | Priority |
| --- | --- | --- | --- |
| Reviews | Leave a rating and comment for the other participant of a completed transaction (buyer→seller or seller→buyer) | Closed / Done | High |
| Reviews | Block reviews from non-participants and incomplete (non-`Accepted`) offers | Closed / Done | High |
| Reviews | View public reviews received by a user | Closed / Done | Medium |
| Profile stats | View aggregate profile stats (average rating, review count, total sales, trust badge, response rate) on the profile page | Closed / Done | Medium |
| Profile visibility | Hide Edit Profile / Account Details on another user's profile | Closed / Done | Medium |

---

## 2. Scope

### 2.1 In Scope

The following items are included in Sprint 4 testing:

- Unit tests for rating validation, reviewer/reviewee resolution for an offer (bidirectional), and offer-completion/authorization checks, using monkeypatching to isolate the route from the database.
- Unit tests for the profile-stats and reviews database functions (`get_user_profile_stats`, `get_reviews_for_user`) against a real temporary SQLite database.
- API / route tests for:
  - `POST /api/reviews`
  - `GET /api/users/<user_id>/reviews`
  - `GET /profile` and `GET /profile/<user_id>`
- Real-database integration tests (seeded SQLite data, not mocks) confirming:
  - A submitted review updates the reviewed user's average rating and review count on their profile.
  - `is_own_profile` correctly gates the Edit Profile button and Account Details card.
  - The reviews tab renders seeded reviews, and an empty state when none exist.
- Manual/Selenium browser testing for viewing another user's profile and confirming their reviews and rating are visible while account-management controls are hidden.
- Regression testing to ensure Sprint 1–3 features continue to pass after Sprint 4 changes.
- Static testing using pylint.
- Cyclomatic complexity checking using radon.
- Coverage checking using pytest-cov.
- GitLab CI/CD pipeline verification.

### 2.2 Out of Scope

| Item | Reason |
| --- | --- |
| Editing or deleting an existing review | Not part of the Sprint 4 review-creation scope. |
| Review moderation / reporting | Handled under the admin moderation epic. |
| A dedicated "Leave a review" UI form | Sprint 4 ships the review API and its display on the profile page; the submission UI is a follow-up. |
| Load testing | Not required for the small assignment dataset and current Sprint 4 scope. |
| Full security penetration testing | GitLab SAST, dependency scanning, and secret detection are used for automated security checks. |
| Full cross-browser Selenium matrix | Manual/Selenium testing targets Chrome only for Sprint 4; Edge and Firefox matrix testing is out of scope. |

---

## 3. Test Approach

### 3.1 Testing Pyramid Target

| Level | Target Count | Tool | Pipeline Stage | Purpose |
| --- | ---: | --- | --- | --- |
| Unit tests | 15–20+ | pytest | test | Verify rating validation, bidirectional reviewer/reviewee resolution, and profile-stats/review database functions in isolation. |
| API / Route tests | 10–15+ | pytest + Flask test client | test | Verify HTTP route behaviour, including real-database integration tests for review submission and profile rendering. |
| Manual / Selenium UI flows | 1–2 Sprint 4 flows | Selenium + manual browser testing | N/A | Verify that a completed review is visible on the reviewed user's public profile. |
| Static analysis | All `.py` files | pylint >= 7.0 | lint | Detect style, structure, and code quality issues. |
| Complexity check | All application functions | radon | lint | Confirm functions are maintainable and testable. |
| Coverage check | Application logic | pytest-cov | test | Confirm at least 60% application logic coverage. |

### 3.2 Static Testing

- **Tool:** pylint
- **Threshold:** score must be `>= 7.0/10`
- **Pipeline stage:** lint

### 3.3 Complexity Testing

- **Tool:** radon
- **Threshold:** cyclomatic complexity per function should not exceed 10.
- **Pipeline stage:** lint

### 3.4 Dynamic Testing

- **Tools:** pytest, pytest-cov, Flask test client, Selenium
- **Minimum coverage required:** `>= 60%` application logic coverage
- **Unit test design:** white-box testing, using monkeypatching to isolate the review route from the database layer.
- **API / route test design:** black-box testing against the user story and acceptance criteria, using the Flask test client, with real temporary SQLite databases for stats/visibility integration tests.
- **UI test design:** Selenium WebDriver against a live Flask test server, seeding a completed transaction and review directly through the database layer.
- **Pipeline stage:** test

### 3.5 Acceptance Testing

- **Method:** Sprint Review demonstration, manual/Selenium browser testing.
- **Assessor:** Tutor / Product Owner / Team reviewer.
- **Criteria:** Each Sprint 4 user story must be checked against its Acceptance Criteria before moving the issue to Done.
- **Evidence:** GitLab issue checklist, merge request, CI pipeline result, and this test plan.

---

## 4. Test Items

### 4.1 Unit Test Items

| Function / Helper | Related Feature | Minimum Tests Required | Risk / Priority |
| --- | --- | ---: | --- |
| `_rating_error()` | Rating validation | 5 | High — must reject missing, non-integer, boolean, and out-of-range ratings. |
| `_reviewed_user_for_offer()` | Bidirectional reviewer/reviewee resolution | 3 | High — must resolve the counterparty for both buyer and seller, and reject non-participants. |
| `_validate_offer()` | Offer-completion check | 2 | High — must reject missing offers and non-`Accepted` offers. |
| `submit_review()` | End-to-end review submission | 2 | High — both directions (seller→buyer, buyer→seller) must create a review and return `201`. |
| `get_user_profile_stats()` | Profile aggregate stats | 4 | High — must compute average rating, review count, total sales, trust badge, and response rate correctly from seeded data, and handle a user with no activity. |
| `get_reviews_for_user()` | Public review retrieval | 2 | Medium — must return only reviews for the requested user, newest first, and an empty list when none exist. |

### 4.2 API / Route Test Items

| Route / Behaviour | Related Feature | Minimum Tests Required | Risk / Priority |
| --- | --- | ---: | --- |
| `POST /api/reviews` | Submit review | 7 | High — must validate login, rating, offer existence, offer completion, participant authorization (both directions), and reviewee mismatch. |
| `GET /api/users/<user_id>/reviews` | View public reviews | 3 | Medium — must return seeded reviews, an empty list, and `404` for a missing user. |
| `GET /profile` (own profile, real DB) | Profile stats + visibility | 3 | High — must show Edit Profile / Account Details, and correct stats after a review is submitted. |
| `GET /profile/<user_id>` (other profile, real DB) | Profile stats + visibility | 3 | High — must hide Edit Profile / Account Details, and render seeded reviews or the empty state. |

### 4.3 UI / Acceptance Test Items

| User Flow | Related Feature | Test Type | Priority | Expected Evidence |
| --- | --- | --- | --- | --- |
| Buyer/seller submits a review after a completed transaction | Submit review | API / acceptance | High | API evidence that a review is created and reflected in the reviewed user's stats. |
| Viewer opens another user's profile after a review is left | View public profile reviews | Selenium + manual | Medium | Browser evidence that the review, rating, and review count appear on the profile, and Edit Profile / Account Details are hidden. |

---

## 5. Test Environment

| Area | Configuration |
| --- | --- |
| Language | Python 3.x |
| Framework | Flask |
| Frontend | HTML5, Bootstrap, Jinja templates |
| Database | SQLite test database / isolated SQLite fixture (`tmp_path`) |
| Test framework | pytest |
| Coverage tool | pytest-cov |
| Static analysis | pylint |
| Complexity analysis | radon |
| CI/CD platform | GitLab CI/CD |
| CI image | python:3.11-slim |
| Browser for manual/Selenium verification | Chrome (headless) |

### Test Isolation Rule

Each automated test must create and clean up its own test data. Tests must not depend on the production `swaplah.db` file, local browser state, or data created by another test. Integration and Selenium tests use an isolated temporary SQLite database created via the `tmp_path` pytest fixture, monkeypatched onto `app.db.DATABASE`.

---

## 6. Entry and Exit Criteria

### 6.1 Entry Criteria

- Sprint 4 feature branch is pushed to GitLab.
- Merge Request is created.
- No Python syntax errors exist.
- Required test files are added under `tests/unit`, `tests/api`, or `tests/ui/selenium`.
- Flask app can run locally in development mode.
- pylint validate stage passes with score `>= 7.0`.

### 6.2 Exit Criteria — Verification

- [x] All implemented unit tests pass with 0 failures.
- [x] All implemented API / route tests pass with 0 failures.
- [x] Real-database integration tests confirm review submission updates profile stats, and profile visibility gating.
- [x] Test coverage is at least 60%.
- [x] pylint score is at least 7.0/10.
- [x] radon complexity check shows no implemented function exceeds complexity 10.
- [x] GitLab pipeline is green on the Merge Request.
- [x] No generated files such as `.env`, `.coverage`, `.venv`, `__pycache__`, or `swaplah.db` are committed.

### 6.3 Exit Criteria — Validation

- [x] Product Owner / Tutor acceptance criteria are verified through issue checklist, MR evidence, and test results.
- [x] All Sprint 4 test cases are updated to Passing.
- [x] Related GitLab issues are moved to Done after the MR is merged and the issue checklist is complete.

### 6.4 Suspension and Resumption Criteria

| Criteria Type | Condition |
| --- | --- |
| Suspension criteria | Testing stops if the Flask app cannot start, database setup fails, or the CI runner fails for reasons unrelated to the code. |
| Resumption criteria | Testing resumes after the blocking defect is fixed, database setup works, and the pipeline can run again. |

---

## 7. Sprint 4 Test Cases

| Test ID | Module | Description | Type | Preconditions | Steps | Expected Result | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TC-S4-RATE-001 | Submit Review | Reject a missing rating | Negative | User is logged in | 1. `POST /api/reviews` without `rating` | `400` validation error | Pass |
| TC-S4-RATE-002 | Submit Review | Reject a non-integer rating | Negative | User is logged in | 1. `POST /api/reviews` with `rating: 2.5` | `400` validation error | Pass |
| TC-S4-RATE-003 | Submit Review | Reject a rating below 1 | Negative | User is logged in | 1. `POST /api/reviews` with `rating: 0` | `400` validation error | Pass |
| TC-S4-RATE-004 | Submit Review | Reject a rating above 5 | Negative | User is logged in | 1. `POST /api/reviews` with `rating: 6` | `400` validation error | Pass |
| TC-S4-SUBMIT-001 | Submit Review | Seller can review the buyer of an accepted offer | Positive | Offer status is `Accepted`, seller is logged in | 1. `POST /api/reviews` with `offer_id`, `rating` | `201`, review created for the buyer | Pass |
| TC-S4-SUBMIT-002 | Submit Review | Buyer can review the seller of an accepted offer | Positive | Offer status is `Accepted`, buyer is logged in | 1. `POST /api/reviews` with `offer_id`, `rating`, `comment` | `201`, review created for the seller | Pass |
| TC-S4-SUBMIT-003 | Submit Review | Block a non-participant from reviewing | Negative / Security | Offer status is `Accepted`, an unrelated user is logged in | 1. `POST /api/reviews` as an unrelated user | `403` forbidden error | Pass |
| TC-S4-SUBMIT-004 | Submit Review | Block a review on a non-completed offer | Negative | Offer status is `Pending` | 1. `POST /api/reviews` for the pending offer | `400` "Transaction not completed" error | Pass |
| TC-S4-SUBMIT-005 | Submit Review | Block a review for a missing offer | Negative | Offer ID does not exist | 1. `POST /api/reviews` with an unknown `offer_id` | `404` "Offer not found" error | Pass |
| TC-S4-SUBMIT-006 | Submit Review | Block a logged-out user from submitting a review | Negative / Security | User is not logged in | 1. Clear session 2. `POST /api/reviews` | `401` login required error | Pass |
| TC-S4-SUBMIT-007 | Submit Review | Reject a `reviewee_id` that does not match the transaction counterparty | Negative | Offer status is `Accepted` | 1. `POST /api/reviews` with a `reviewee_id` that is neither participant | `400` "must be for the other party" error | Pass |
| TC-S4-VIEW-001 | View Public Reviews | Return seeded reviews for a user | Positive | User has at least one review | 1. `GET /api/users/<user_id>/reviews` | `200`, response includes the review with rating, comment, reviewer name | Pass |
| TC-S4-VIEW-002 | View Public Reviews | Return an empty list for a user without reviews | Positive | User has no reviews | 1. `GET /api/users/<user_id>/reviews` | `200`, `{"reviews": []}` | Pass |
| TC-S4-VIEW-003 | View Public Reviews | Reject a missing user | Negative | User ID does not exist | 1. `GET /api/users/<invalid_id>/reviews` | `404` "User not found." error | Pass |
| TC-S4-STATS-001 | Profile Stats | Average rating and review count reflect submitted reviews | Positive | User has received two reviews (ratings 4 and 5) | 1. Seed two reviews 2. `GET /profile/<user_id>` | Page shows average rating `4.5` and `2 reviews` | Pass |
| TC-S4-STATS-002 | Profile Stats | Show "No reviews yet" when a user has no reviews | Positive | User has no reviews | 1. `GET /profile/<user_id>` | Page shows "No reviews yet" | Pass |
| TC-S4-STATS-003 | Profile Stats | Trust badge reflects total completed sales | Positive | User has 5+ accepted offers as seller | 1. Seed 5 accepted offers 2. `GET /profile/<user_id>` | Page shows "Trusted Seller" badge | Pass |
| TC-S4-VISIB-001 | Profile Visibility | Own profile shows Edit Profile and Account Details | Positive | Logged in as the profile owner | 1. `GET /profile` | Page includes "Edit profile" and "Account Details" | Pass |
| TC-S4-VISIB-002 | Profile Visibility | Another user's profile hides Edit Profile and Account Details | Positive / Security | Logged in as a different user | 1. `GET /profile/<other_user_id>` | Page excludes "Edit profile" and "Account Details" | Pass |
| TC-S4-REG-001 | Regression | Login, registration, listings, offers, and transactions still work after Sprint 4 changes | Regression | App is running | 1. Register 2. Log in 3. Browse listings 4. Submit and accept an offer | All Sprint 1–3 flows continue to work without error | Pass |

---

## 8. Manual / Selenium Verification Evidence

| Flow | Related Feature | Steps Verified | Status |
| --- | --- | --- | --- |
| View another user's profile after receiving a review | View public profile reviews | Seeded a completed transaction and a review through the database layer, logged in as a third-party viewer, opened `/profile/<user_id>` in a headless Chrome browser, confirmed the rating, review count, and reviewer name render on the page, and that "Edit profile" does not appear. | Pass |

---

## 9. Regression Testing

| Regression Area | Command / Method | Expected Result |
| --- | --- | --- |
| Full automated test suite | `python -m pytest -q --ignore=tests/ui/selenium` | All implemented tests pass. |
| Linting | `python -m pylint app tests --ignore-paths='.*selenium.*'` | Score is at least 7.0/10 (target 10.00/10). |
| Manual submit-review flow | API test | Buyer and seller can each review the other after an accepted offer. |
| Manual profile flow | Browser/Selenium test | Profile stats and reviews render correctly for both own and other users' profiles. |
| Manual Sprint 1–3 regression | Browser test | Login, registration, listings, offers, and transaction history still work. |

---

## 10. Test Data

| Data Item | Example |
| --- | --- |
| Accepted offer | Offer with status `Accepted`, linking a buyer and a seller. |
| Pending offer | Offer with status `Pending`, used to confirm reviews are blocked before completion. |
| Review | `reviewed_user_id`, `reviewer_id`, `rating` (1–5), `comment`. |
| Unrelated user account | Logged-in user with no relationship to a given offer, used to verify access control. |
| User with no reviews | Used to confirm the "No reviews yet" empty state. |

---

## 11. Risks and Contingencies

| Risk | Probability | Impact | Mitigation / Contingency |
| --- | --- | --- | --- |
| A non-participant submits a review on someone else's transaction | Medium | High | `_reviewed_user_for_offer()` rejects non-participants with `403`; covered by a negative test. |
| A review is submitted for a pending (incomplete) offer | Medium | High | `_validate_offer()` checks `status == "Accepted"`; covered by a negative test. |
| Profile stats miscalculate average rating or review count | Medium | High | `get_user_profile_stats()` covered by a real-database unit test with seeded reviews. |
| Another user's Edit Profile / Account Details are exposed | Low | High | `is_own_profile` gating covered by a real-database API test for both own and other profiles. |
| Test data affects the real database | Medium | High | Use isolated temporary SQLite database fixtures (`tmp_path`) and avoid the production `swaplah.db`. |

---

## 12. Related Links

- [Sprint board](https://gitlab.com/nyp-sg/pet/it2112/26s1/it2112-03/assignment/team_2/swaplah/-/boards)
- [CI/CD pipelines](https://gitlab.com/nyp-sg/pet/it2112/26s1/it2112-03/assignment/team_2/swaplah/-/pipelines)
- [Merge requests](https://gitlab.com/nyp-sg/pet/it2112/26s1/it2112-03/assignment/team_2/swaplah/-/merge_requests)
- Unit tests: `tests/unit/`
- API tests: `tests/api/`
- Selenium tests: `tests/ui/selenium/`

---

## 13. Sprint 4 Definition of Done

### Verification

- [x] Code committed through a feature branch and Merge Request.
- [x] Code passes pylint with score `>= 7.0`.
- [x] Cyclomatic complexity for implemented functions does not exceed 10.
- [x] All implemented unit tests pass.
- [x] All implemented API / route tests pass.
- [x] Real-database integration tests for review submission and profile visibility pass.
- [x] Test coverage is at least 60%.
- [x] GitLab pipeline is green on the Merge Request.

### Validation

- [x] Implemented acceptance criteria are confirmed with Product Owner / Tutor.
- [x] All Sprint 4 test cases are updated to Passing.
- [x] Related GitLab issues are moved to Done after the MRs are merged and the issue checklists are complete.
