# Test Plan — SwapLah

## Sprint 3, Version 3.0.0

**Team:** Team 2 — SwapLah  
**Team members:** TAN XIU LI, FELICIA; TAN YU EN, CHARLISA; ELIJAH ONG; LEOVALAN LUCIO RICHARD; LUCAS WONG SI JIE  
**Date created:** 15 Jul 2026  
**Last updated:** 15 Jul 2026  
**GitLab project:** https://gitlab.com/nyp-sg/pet/it2112/26s1/it2112-03/assignment/team_2/swaplah

---

## 1. Introduction

This test plan documents the testing strategy and verification evidence for **Sprint 3** of **SwapLah**, a web-based student co-op marketplace for polytechnic students.

Sprint 3 focuses on **Offers and Transactions**. The purpose of this test plan is to verify that buyers can submit cash and swap offers on listings, sellers can view and manage offers received on their own listings (viewing, accepting, and rejecting), that accepting an offer automatically resolves competing offers, and that both buyers and sellers can view their completed transaction history.

### Sprint 3 Features Covered

| PBI / Issue | Sprint 3 User Story | Current Status | Priority |
| --- | --- | --- | --- |
| [#8](https://gitlab.com/nyp-sg/pet/it2112/26s1/it2112-03/assignment/team_2/swaplah/-/issues/8) | Submit a cash offer for a listing | Closed / Done | High |
| [#9](https://gitlab.com/nyp-sg/pet/it2112/26s1/it2112-03/assignment/team_2/swaplah/-/issues/9) | Submit a swap offer using one of my existing listings | Closed / Done | High |
| [#10](https://gitlab.com/nyp-sg/pet/it2112/26s1/it2112-03/assignment/team_2/swaplah/-/issues/10) | View pending offers received on my listings | Closed / Done | High |
| [#24](https://gitlab.com/nyp-sg/pet/it2112/26s1/it2112-03/assignment/team_2/swaplah/-/issues/24) | Accept an incoming offer on my listing | Closed / Done | High |
| [#25](https://gitlab.com/nyp-sg/pet/it2112/26s1/it2112-03/assignment/team_2/swaplah/-/issues/25) | Reject an incoming offer on my listing | Closed / Done | High |
| [#26](https://gitlab.com/nyp-sg/pet/it2112/26s1/it2112-03/assignment/team_2/swaplah/-/issues/26) | Automatically reject other pending offers when one is accepted | Closed / Done | High |
| [#27](https://gitlab.com/nyp-sg/pet/it2112/26s1/it2112-03/assignment/team_2/swaplah/-/issues/27) | View my transaction history as a buyer or seller | Closed / Done | Medium |

---

## 2. Scope

### 2.1 In Scope

The following items are included in Sprint 3 testing:

- Unit tests for offer submission validation, offer formatting, received-offer retrieval, accept/reject access control, and transaction history retrieval.
- API / route tests for:
  - `POST /api/offers`
  - `GET /api/offers/received`
  - `PATCH /api/offers/<offer_id>/accept`
  - `PATCH /api/offers/<offer_id>/reject`
  - `GET /api/transactions`
- Real-database integration tests (seeded SQLite data, not mocks) confirming:
  - Accepting an offer auto-rejects other pending offers on the same listing.
  - Rejecting an offer does not affect other pending offers.
  - Buyers and sellers only see their own transaction history.
- Manual browser testing for submitting cash and swap offers, viewing pending offers grouped by listing, accepting/rejecting offers, and viewing transaction history as both buyer and seller.
- Regression testing to ensure Sprint 1 and Sprint 2 features continue to pass after Sprint 3 changes.
- Static testing using pylint.
- Cyclomatic complexity checking using radon.
- Coverage checking using pytest-cov.
- GitLab CI/CD pipeline verification.
- AI prompt and refinement documentation.

### 2.2 Out of Scope

| Item | Reason |
| --- | --- |
| Real payment processing | SwapLah does not include real payment gateways; transactions are recorded internally only. |
| Review and rating testing | Reviews are outside the Sprint 3 Offers and Transactions scope. |
| Admin report moderation testing | Reporting and moderation are handled under another module / epic. |
| Load testing | Not required for the small assignment dataset and current Sprint 3 scope. |
| Full security penetration testing | GitLab SAST, dependency scanning, and secret detection are used for automated security checks. |
| Full cross-browser Selenium matrix | Manual browser testing is used for Sprint 3; Edge and Firefox matrix testing is outside Sprint 3 scope. |

---

## 3. Test Approach

### 3.1 Testing Pyramid Target

| Level | Target Count | Tool | Pipeline Stage | Purpose |
| --- | ---: | --- | --- | --- |
| Unit tests | 25–30+ | pytest | test | Verify individual offer, accept/reject, and transaction-history functions in isolation using monkeypatching. |
| API / Route tests | 25–30+ | pytest + Flask test client | test | Verify HTTP route behaviour, including real-database integration tests for auto-reject and transaction history. |
| Manual UI flows | 5 Sprint 3 flows | Manual browser testing | N/A | Verify complete offer and transaction-history user flows in a browser. |
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

### 3.4 Dynamic Testing

- **Tools:** pytest, pytest-cov, Flask test client
- **Minimum coverage required:** `>= 60%` application logic coverage
- **Team stretch target:** `>= 70%` where possible
- **Unit test design:** white-box testing, using monkeypatching to isolate the route layer from the database layer.
- **API / route test design:** black-box testing against the user story and acceptance criteria, using the Flask test client.
- **Integration test design:** real temporary SQLite database seeded with users, listings, offers, and transactions, used specifically to verify auto-reject and transaction-history SQL behaviour end to end.
- **Pipeline stage:** test

### 3.5 Acceptance Testing

- **Method:** Sprint Review demonstration, manual browser testing.
- **Assessor:** Tutor / Product Owner / Team reviewer.
- **Criteria:** Each Sprint 3 user story must be checked against its Acceptance Criteria before moving the issue to Done.
- **Evidence:** GitLab issue checklist, merge request, CI pipeline result, and this test plan.

---

## 4. Test Items

This section follows the Lesson 7 test plan structure by listing specific items to be tested, related user stories, cyclomatic complexity, minimum tests required, and risk. Cyclomatic complexity values were measured using `radon cc`.

### 4.1 Unit Test Items

| Function / Helper | Related User Story | Cyclomatic Complexity | Minimum Tests Required | Risk / Priority |
| --- | --- | ---: | ---: | --- |
| `_common_error()` | #8 / #9 Offer submission validation | 5 | 5 | High — must block unauthenticated users, missing fields, invalid offer type, missing listing, and self-offers. |
| `_validate_cash_price()` | #8 Cash offer price validation | 3 | 3 | High — must reject missing, non-numeric, and negative prices. |
| `_format_offer()` | #8 / #9 / #10 Offer response formatting | 2 | 2 | Medium — must include listing/buyer detail fields only when present. |
| `_check_offer_access()` | #24 / #25 Accept/reject shared validation | 5 | 5 | High — must enforce authentication, existence, ownership, and pending-only status for both accept and reject. |
| `get_offers_for_seller()` | #10 View pending offers | 2 | 3 | High — must return only offers on listings owned by the seller, joined with buyer/listing detail. |
| `get_offer_by_id()` | #24 / #25 Offer lookup | 2 | 2 | High — must return `None` safely for a missing offer. |
| `reject_offer()` | #25 Reject offer | 1 | 3 | High — must mark only the target offer as `Rejected`. |
| `accept_offer()` | #24 / #26 Accept offer and auto-reject | 1 | 5 | High — must mark the target offer `Accepted`, auto-reject other pending offers on the same listing, mark the listing `Sold`, and create a transaction. |
| `_create_transaction_for_offer()` | #24 Transaction record creation | 1 | 2 | High — must insert a transaction row linked to the correct offer, listing, seller, and buyer. |
| `get_transactions_for_user()` | #27 View transaction history | 4 | 4 | High — must return only the logged-in user's transactions, filtered correctly by buyer or seller role. |
| `_format_transaction()` | #27 Transaction response formatting | 1 | 2 | Medium — must format transaction fields consistently for the frontend. |

### 4.2 API / Route Test Items

| Route / Behaviour | Related User Story | Implemented Function / Scope | Cyclomatic Complexity | Minimum Tests Required | Risk / Priority |
| --- | --- | --- | ---: | ---: | --- |
| `POST /api/offers` (cash) | #8 Submit cash offer | `api_create_offer()` / `_handle_cash_offer()` | 4 / 2 | 5 | High — must validate login, required fields, price, ownership, and successful creation. |
| `POST /api/offers` (swap) | #9 Submit swap offer | `api_create_offer()` / `_handle_swap_offer()` | 4 / 3 | 5 | High — must validate login, swap listing ownership, required fields, and successful creation. |
| `GET /api/offers/received` | #10 View pending offers | `api_get_received_offers()` | 3 | 3 | High — seller must see only their own listings' offers, including an empty-state response. |
| `PATCH /api/offers/<offer_id>/accept` | #24 Accept offer | `api_accept_offer()` | 2 | 5 | High — must validate login, existence, ownership, pending status, and return the updated offer. |
| `PATCH /api/offers/<offer_id>/reject` | #25 Reject offer | `api_reject_offer()` | 2 | 6 | High — must validate login, existence, ownership, pending status, return the updated offer, and leave other offers unchanged. |
| Auto-reject on accept (real DB) | #26 Auto-reject other pending offers | `accept_offer()` via `PATCH .../accept` | 1 | 3 | High — accepting one offer must reject all other pending offers on the same listing, leave only one `Accepted` offer, and not touch unrelated records when only one offer exists. |
| `GET /api/transactions` | #27 View transaction history | `api_get_transactions()` | 4 | 5 | Medium — must return only the logged-in user's transactions for the requested role, block unauthenticated access, and handle the empty state. |

### 4.3 UI / Acceptance Test Items

| User Flow | Related User Story | Test Type | Priority | Expected Evidence |
| --- | --- | --- | --- | --- |
| Buyer submits a cash offer on a listing | #8 Submit cash offer | Manual + API / acceptance | High | Browser/API evidence that a cash offer is created with status `Pending`. |
| Buyer submits a swap offer using an existing listing | #9 Submit swap offer | Manual + API / acceptance | High | Browser/API evidence that a swap offer is created referencing the buyer's own listing. |
| Seller views pending offers grouped by listing | #10 View pending offers | Manual + API / acceptance | High | Browser/API evidence that the Offers page shows pending offers grouped by listing, with an empty state when none exist. |
| Seller accepts an incoming offer | #24 Accept offer | Manual + API / acceptance | High | Browser/API evidence that the offer status changes to `Accepted` and the listing is marked `Sold`. |
| Seller rejects an incoming offer | #25 Reject offer | Manual + API / acceptance | High | Browser/API evidence that the offer status changes to `Rejected` while other offers remain unaffected. |
| Accepting one offer auto-rejects the rest | #26 Auto-reject other pending offers | Manual + API / acceptance | High | Browser/API evidence that only one offer per listing ends up `Accepted`, with the rest automatically `Rejected`. |
| Buyer and seller view transaction history | #27 View transaction history | Manual + API / acceptance | Medium | Browser/API evidence that Buyer History and Seller History tabs show completed transactions, or an appropriate empty state. |

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
| CI/CD platform | GitLab CI/CD |
| CI image | python:3.11-slim |
| Dependencies | Installed from `requirements.txt` |
| Browser for manual verification | Chrome / Edge / Firefox |

### Test Isolation Rule

Each automated test must create and clean up its own test data. Tests must not depend on the production `swaplah.db` file, local browser state, or data created by another test. Integration tests use an isolated temporary SQLite database created via the `tmp_path` pytest fixture, monkeypatched onto `app.db.DATABASE`.

---

## 6. Entry and Exit Criteria

### 6.1 Entry Criteria

Testing can begin when:

- Sprint 3 feature branch is pushed to GitLab.
- Merge Request is created.
- No Python syntax errors exist.
- Related Sprint 3 PBI has a clear user story and acceptance criteria.
- Related Sprint 3 PBI has milestone, labels, priority, type, and story points.
- Required test files are added under `tests/unit` or `tests/api`.
- Flask app can run locally in development mode.
- Test database setup is available.
- pylint validate stage passes with score `>= 7.0`.

### 6.2 Exit Criteria — Verification

Sprint 3 verification is complete when:

- [x] All implemented unit tests pass with 0 failures.
- [x] All implemented API / route tests pass with 0 failures.
- [x] Real-database integration tests confirm auto-reject and transaction-history behaviour.
- [x] Test coverage is at least 60%.
- [x] pylint score is at least 7.0/10.
- [x] radon complexity check shows no implemented function exceeds complexity 10.
- [x] GitLab pipeline is green on the Merge Request.
- [x] No new SAST or secret detection issues are introduced.
- [x] No generated files such as `.env`, `.coverage`, `.venv`, `__pycache__`, or `swaplah.db` are committed.

### 6.3 Exit Criteria — Validation

Sprint 3 validation is complete when:

- [x] Product Owner / Tutor acceptance criteria are verified through issue checklist, MR evidence, and test results.
- [x] All Sprint 3 test cases are updated to Passing.
- [x] Sprint 3 work items are closed and moved to Done only after MRs are merged and checklists are complete.
- [x] At least one teammate reviews and approves each Merge Request.
- [x] Related GitLab issues are moved to Done after the MR is merged and the issue checklist is complete.

### 6.4 Suspension and Resumption Criteria

| Criteria Type | Condition |
| --- | --- |
| Suspension criteria | Testing stops if the Flask app cannot start, database setup fails, or CI runner fails for reasons unrelated to the code. |
| Resumption criteria | Testing resumes after the blocking defect is fixed, database setup works, and the pipeline can run again. |

---

## 7. Sprint 3 Test Cases

| Test ID | Module | Related PBI | Description | Type | Preconditions | Steps | Expected Result | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TC-S3-CASH-001 | Submit Cash Offer | #8 | Submit a valid cash offer | Positive | Buyer is logged in, listing exists and is not own listing | 1. Send `POST /api/offers` with `listingId`, `offerType: cash`, `proposedPrice` 2. Check response | Offer is created with status `Pending` | Pass |
| TC-S3-CASH-002 | Submit Cash Offer | #8 | Offer status defaults to Pending | Positive | Buyer is logged in | 1. Submit valid cash offer 2. Check returned status field | Status field equals `Pending` | Pass |
| TC-S3-CASH-003 | Submit Cash Offer | #8 | Reject offer on own listing | Negative | Buyer is logged in and owns the listing | 1. Submit cash offer on own listing | Request is blocked with a `403` forbidden error | Pass |
| TC-S3-CASH-004 | Submit Cash Offer | #8 | Reject missing proposed price | Negative | Buyer is logged in | 1. Submit cash offer without `proposedPrice` | Request is blocked with a `400` validation error | Pass |
| TC-S3-CASH-005 | Submit Cash Offer | #8 | Block logged-out user from submitting offer | Negative / Security | User is not logged in | 1. Clear session 2. Send `POST /api/offers` | Request is blocked with a `401` login required error | Pass |
| TC-S3-SWAP-001 | Submit Swap Offer | #9 | Submit a valid swap offer | Positive | Buyer is logged in and owns the swap listing | 1. Send `POST /api/offers` with `offerType: swap`, `swapListingId` | Offer is created referencing the buyer's own listing | Pass |
| TC-S3-SWAP-002 | Submit Swap Offer | #9 | Reject swap item not owned by buyer | Negative | Buyer is logged in | 1. Submit swap offer using a listing owned by someone else | Request is blocked with a `403` forbidden error | Pass |
| TC-S3-SWAP-003 | Submit Swap Offer | #9 | Reject offer on own listing | Negative | Buyer owns the target listing | 1. Submit swap offer on own listing | Request is blocked with a `403` forbidden error | Pass |
| TC-S3-SWAP-004 | Submit Swap Offer | #9 | Reject missing swap listing ID | Negative | Buyer is logged in | 1. Submit swap offer without `swapListingId` | Request is blocked with a `400` validation error | Pass |
| TC-S3-SWAP-005 | Submit Swap Offer | #9 | Block logged-out user from submitting swap offer | Negative / Security | User is not logged in | 1. Clear session 2. Send `POST /api/offers` with `offerType: swap` | Request is blocked with a `401` login required error | Pass |
| TC-S3-VIEW-001 | View Pending Offers | #10 | Seller sees pending offers on their listing | Positive | Seller owns a listing with pending offers | 1. Send `GET /api/offers/received` | Response includes all offers on the seller's listings with listing/buyer detail | Pass |
| TC-S3-VIEW-002 | View Pending Offers | #10 | Non-owner cannot view another seller's offers | Negative / Security | User does not own any listing with offers | 1. Send `GET /api/offers/received` as a different user | Response contains only that user's own listings' offers, not others' | Pass |
| TC-S3-VIEW-003 | View Pending Offers | #10 | Show empty state when no pending offers exist | Positive | Seller has no offers on any listing | 1. Send `GET /api/offers/received` | Response returns an empty `offers` list, no error | Pass |
| TC-S3-VIEW-004 | View Pending Offers | #10 | Block logged-out user from viewing offers | Negative / Security | User is not logged in | 1. Clear session 2. Send `GET /api/offers/received` | Request is blocked with a `401` login required error | Pass |
| TC-S3-ACCEPT-001 | Accept Offer | #24 | Seller accepts a pending offer | Positive | Seller owns the listing, offer is `Pending` | 1. Send `PATCH /api/offers/<offer_id>/accept` | Offer status changes to `Accepted`, listing marked `Sold`, transaction created | Pass |
| TC-S3-ACCEPT-002 | Accept Offer | #24 | Non-owner cannot accept an offer | Negative / Security | User does not own the listing | 1. Send `PATCH /api/offers/<offer_id>/accept` as a different user | Request is blocked with a `403` forbidden error | Pass |
| TC-S3-ACCEPT-003 | Accept Offer | #24 | Reject accept for missing offer | Negative | Offer ID does not exist | 1. Send `PATCH /api/offers/<invalid_id>/accept` | Request is blocked with a `404` not found error | Pass |
| TC-S3-ACCEPT-004 | Accept Offer | #24 | Reject accept for already-resolved offer | Negative | Offer status is not `Pending` | 1. Send `PATCH /api/offers/<offer_id>/accept` for a `Rejected` offer | Request is blocked with a `409` conflict error | Pass |
| TC-S3-ACCEPT-005 | Accept Offer | #24 | Block logged-out user from accepting offer | Negative / Security | User is not logged in | 1. Clear session 2. Send `PATCH /api/offers/<offer_id>/accept` | Request is blocked with a `401` login required error | Pass |
| TC-S3-REJECT-001 | Reject Offer | #25 | Seller rejects a pending offer | Positive | Seller owns the listing, offer is `Pending` | 1. Send `PATCH /api/offers/<offer_id>/reject` | Offer status changes to `Rejected` | Pass |
| TC-S3-REJECT-002 | Reject Offer | #25 | Non-owner cannot reject an offer | Negative / Security | User does not own the listing | 1. Send `PATCH /api/offers/<offer_id>/reject` as a different user | Request is blocked with a `403` forbidden error | Pass |
| TC-S3-REJECT-003 | Reject Offer | #25 | Reject reject-action for missing offer | Negative | Offer ID does not exist | 1. Send `PATCH /api/offers/<invalid_id>/reject` | Request is blocked with a `404` not found error | Pass |
| TC-S3-REJECT-004 | Reject Offer | #25 | Reject reject-action for already-resolved offer | Negative | Offer status is not `Pending` | 1. Send `PATCH /api/offers/<offer_id>/reject` for an `Accepted` offer | Request is blocked with a `409` conflict error | Pass |
| TC-S3-REJECT-005 | Reject Offer | #25 | Rejecting one offer does not affect other pending offers | Positive | Listing has two or more pending offers | 1. Reject one offer 2. Check status of the other pending offer(s) | Other pending offers remain `Pending` and unaffected | Pass |
| TC-S3-REJECT-006 | Reject Offer | #25 | Block logged-out user from rejecting offer | Negative / Security | User is not logged in | 1. Clear session 2. Send `PATCH /api/offers/<offer_id>/reject` | Request is blocked with a `401` login required error | Pass |
| TC-S3-AUTO-001 | Auto-Reject on Accept | #26 | Accepting one offer auto-rejects all other pending offers | Positive | Listing has 3 pending offers | 1. Accept one of the offers 2. Check status of the other two | The two other offers automatically change to `Rejected` | Pass |
| TC-S3-AUTO-002 | Auto-Reject on Accept | #26 | Only one offer ends up Accepted per listing | Positive | Listing has multiple pending offers | 1. Accept one offer 2. Count offers with status `Accepted` for the listing | Exactly one offer has status `Accepted` | Pass |
| TC-S3-AUTO-003 | Auto-Reject on Accept | #26 | Accepting the only pending offer does not affect unrelated records | Positive | Listing has exactly one pending offer | 1. Accept the single offer 2. Check listing status and transaction record | Listing marked `Sold`, one transaction created, no other offers altered | Pass |
| TC-S3-HIST-001 | Transaction History | #27 | Seller sees a completed transaction | Positive | Seller has at least one accepted offer | 1. Send `GET /api/transactions?role=seller` | Response includes the completed transaction with buyer detail | Pass |
| TC-S3-HIST-002 | Transaction History | #27 | Buyer sees a completed transaction | Positive | Buyer has at least one accepted offer | 1. Send `GET /api/transactions?role=buyer` | Response includes the completed transaction with seller detail | Pass |
| TC-S3-HIST-003 | Transaction History | #27 | Show empty state when no completed transactions exist | Positive | User has no completed transactions | 1. Send `GET /api/transactions?role=buyer` | Response returns an empty `transactions` list, no error | Pass |
| TC-S3-HIST-004 | Transaction History | #27 | Block logged-out user from viewing history | Negative / Security | User is not logged in | 1. Clear session 2. Send `GET /api/transactions` | Request is blocked with a `401` login required error | Pass |
| TC-S3-HIST-005 | Transaction History | #27 | User cannot see another user's transactions | Negative / Security | An unrelated user has no transactions | 1. Send `GET /api/transactions?role=buyer` and `?role=seller` as the unrelated user | Both responses return an empty `transactions` list | Pass |
| TC-S3-REG-001 | Regression | Sprint 1 / 2 | Login, registration, and listing browsing still work after Sprint 3 changes | Regression | App is running | 1. Register 2. Log in 3. Browse active listings | All Sprint 1 and Sprint 2 flows continue to work without error | Pass |
| TC-S3-REG-002 | Regression | Sprint 2 | Listing detail and offer submission buttons still render correctly | Regression | Active listing exists | 1. Open listing detail page 2. Confirm cash/swap offer forms render | Listing detail page renders without breaking after Sprint 3 route changes | Pass |

---

## 8. Manual Verification Evidence

Sprint 3 flows were manually verified in the browser in addition to automated tests, since Sprint 3 does not include Selenium UI automation.

| Manual Flow | Related PBI | Steps Verified | Status |
| --- | --- | --- | --- |
| Submit cash and swap offers from the listing detail page | #8 / #9 | Logged in as a buyer, submitted both a cash offer and a swap offer on another user's listing, confirmed both appear with status `Pending`. | Pass |
| View Pending Offers page grouped by listing | #10 | Logged in as a seller with multiple listings and offers, confirmed the Offers page groups offers under each listing with an offer count. | Pass |
| Accept an offer | #24 | Clicked Accept on a pending offer, confirmed its status updated to `Accepted` and the listing became unavailable for further offers. | Pass |
| Reject an offer | #25 | Clicked Reject on a pending offer, confirmed its status updated to `Rejected` while sibling offers were unaffected. | Pass |
| Auto-reject on accept | #26 | Seeded a listing with three pending offers, accepted one, confirmed the other two automatically changed to `Rejected` in the UI. | Pass |
| View Transaction History (buyer and seller tabs) | #27 | Logged in as a user with both purchase and sale history, confirmed Buyer History and Seller History tabs each show the correct completed transactions with item, counterparty, date, and amount. | Pass |

---

## 9. Regression Testing

Before merging any Sprint 3 Merge Request, the following regression checks must pass:

| Regression Area | Command / Method | Expected Result |
| --- | --- | --- |
| Full automated test suite | `python -m pytest -q` | All implemented tests pass. |
| Unit coverage | `python -m pytest tests/unit --cov=app --cov-fail-under=60` | Coverage is at least 60%. |
| Linting | `python -m pylint app tests --fail-under=7.0` | Score is at least 7.0/10. |
| Complexity | `python -m radon cc app/ -s` | No implemented function exceeds complexity 10. |
| Manual submit offer flow | Browser test | Buyer can submit both cash and swap offers. |
| Manual view offers flow | Browser test | Seller can view pending offers grouped by listing. |
| Manual accept/reject flow | Browser test | Seller can accept and reject offers, with auto-reject behaving correctly. |
| Manual transaction history flow | Browser test | Buyer and seller can view their own completed transactions. |
| Manual Sprint 1 / 2 regression | Browser test | Login, registration, profile management, and listing management still work. |

---

## 10. Test Data

| Data Item | Example |
| --- | --- |
| Valid buyer account | Logged-in user submitting an offer on another seller's listing. |
| Valid seller account | Logged-in user who owns the listing receiving offers. |
| Unrelated user account | Logged-in user with no relationship to a given listing or offer, used to verify access control. |
| Active listing with pending offers | Listing with 1–3 offers in status `Pending`. |
| Accepted offer | Offer with status `Accepted`, linked to a `Sold` listing and a transaction record. |
| Rejected offer | Offer with status `Rejected`. |
| Cash offer | `offerType: cash`, `proposedPrice: 25.00`. |
| Swap offer | `offerType: swap`, `swapListingId` referencing the buyer's own active listing. |
| Invalid cash offer | Missing or negative `proposedPrice`. |
| Invalid swap offer | Missing `swapListingId`, or a `swapListingId` not owned by the buyer. |
| Transaction record | Linked to an accepted offer, storing `seller_id`, `buyer_id`, `transaction_type`, and `amount`. |

---

## 11. Risks and Contingencies

| Risk | Probability | Impact | Mitigation / Contingency |
| --- | --- | --- | --- |
| Buyer submits an offer on their own listing | Low | Medium | Add ownership validation and negative test for `POST /api/offers`. |
| Non-owner views, accepts, or rejects offers on another seller's listing | Medium | High | Add ownership checks in `_check_offer_access()` and `get_offers_for_seller()`, with negative API tests. |
| Accepting an offer does not reject competing offers | Medium | High | Add a real-database integration test seeding multiple pending offers and asserting only the accepted offer remains `Accepted`. |
| Accepting an already-resolved offer causes an inconsistent state | Medium | Medium | Add a status check (`Pending` only) before accept/reject, with a `409` conflict response. |
| Transaction history leaks another user's transactions | Medium | High | Add a negative test confirming an unrelated user's history request returns an empty list. |
| `database is locked` errors during concurrent offer actions | Medium | Medium | Add a busy timeout and WAL journal mode to `get_db_connection()` to reduce SQLite lock contention. |
| Transaction record is not created when an offer is accepted | Low | High | Add a unit/integration test asserting a transaction row exists after `accept_offer()` runs. |
| Test data affects the real database | Medium | High | Use isolated temporary SQLite database fixtures (`tmp_path`) and avoid the production `swaplah.db`. |
| Pipeline fails due to missing dependency | Low | Medium | Ensure all dependencies are pinned in `requirements.txt` and installed in the GitLab CI job. |

---

## 12. Related Links

- [Sprint board](https://gitlab.com/nyp-sg/pet/it2112/26s1/it2112-03/assignment/team_2/swaplah/-/boards)
- [CI/CD pipelines](https://gitlab.com/nyp-sg/pet/it2112/26s1/it2112-03/assignment/team_2/swaplah/-/pipelines)
- [Merge requests](https://gitlab.com/nyp-sg/pet/it2112/26s1/it2112-03/assignment/team_2/swaplah/-/merge_requests)
- [Test cases](https://gitlab.com/nyp-sg/pet/it2112/26s1/it2112-03/assignment/team_2/swaplah/-/quality/test_cases)
- Unit tests: `tests/unit/`
- API tests: `tests/api/`
- AI usage logs: `AI/`

---

## 13. Sprint 3 Definition of Done

### Verification

- [x] Code committed through a feature branch and Merge Request.
- [x] Merge Request reviewed and approved by at least one teammate.
- [x] Code passes pylint with score `>= 7.0`.
- [x] Cyclomatic complexity for implemented functions does not exceed 10.
- [x] All implemented unit tests pass.
- [x] All implemented API / route tests pass.
- [x] Real-database integration tests for auto-reject and transaction history pass.
- [x] Test coverage is at least 60%.
- [x] GitLab pipeline is green on the Merge Request.
- [x] No new linting, SAST, or secret detection issues are introduced.

### Validation

- [x] Implemented acceptance criteria are confirmed with Product Owner / Tutor.
- [x] All Sprint 3 test cases are updated to Passing.
- [x] Related GitLab issues are moved to Done after the MRs are merged and the issue checklists are complete.
- [x] Sprint 3 board shows Sprint 3 work items as Closed / Done.

---

## 14. AI Prompt and Refinement Evidence

### AI Prompt Used

> Generate a Sprint 3 test plan for SwapLah Assignment 2. Sprint 3 focuses on Offers and Transactions, including submitting cash and swap offers, viewing pending offers received on a listing, accepting an incoming offer, rejecting an incoming offer, automatically rejecting other pending offers when one is accepted, and viewing transaction history as a buyer or seller. Follow the same Lesson 7 test plan format used in Sprint 1 and Sprint 2, with Introduction, Scope, Test Approach, Test Items, Test Environment, Entry and Exit Criteria, Risks, Regression Testing, Definition of Done, and at least 10 positive and negative test cases with Test ID, description, preconditions, steps, and expected results.

### Refinement Made

The AI-generated draft was reviewed and refined against the actual Sprint 3 GitLab issues under **Offers and Transactions** (#8, #9, #10, #24, #25, #26, #27). Cyclomatic complexity values in Section 4 were measured directly using `radon cc` against the implemented functions rather than estimated, so the figures reflect the actual codebase. Test case counts and IDs were cross-checked against the real test files (`tests/unit/test_manage_offers_unit.py`, `tests/unit/test_offers_unit.py`, `tests/api/test_manage_offers_api.py`, `tests/api/test_accept_reject_offers_integration.py`, `tests/unit/test_transaction_history_unit.py`, `tests/api/test_transaction_history_api.py`) to ensure every listed test case corresponds to an actual passing test.

The plan was also updated to reflect that Sprint 3 does not include Selenium UI automation; manual browser verification evidence was documented separately in Section 8 instead of a Selenium evidence table.

### Manual Review Evidence

- Test cases were mapped to the Sprint 3 PBIs and acceptance criteria.
- Unit test items were checked against implemented offer, accept/reject, and transaction-history functions.
- API test items were checked against the required offer and transaction endpoints.
- The auto-reject behaviour (#26) was specifically verified using a real temporary SQLite database seeded with multiple pending offers, rather than relying on mocked database calls, to confirm the underlying SQL update logic is correct.
- Transaction history data isolation (#27) was verified with a dedicated negative test confirming an unrelated user cannot see another user's transactions.
- All listed test cases were changed to `Pass` only after the related GitLab work items were closed and moved to Done.