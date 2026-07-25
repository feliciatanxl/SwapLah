# Test Plan — SwapLah

## Sprint 2, Version 2.1.0

**Team:** Team 2 — SwapLah
**Team members:** TAN XIU LI, FELICIA; TAN YU EN, CHARLISA; ELIJAH ONG; LEOVALAN LUCIO RICHARD; LUCAS WONG SI JIE
**Date created:** 12 Jun 2026
**Last updated:** 25 Jul 2026
**GitLab project:** https://gitlab.com/nyp-sg/pet/it2112/26s1/it2112-03/assignment/team_2/swaplah

---

## 1. Introduction

This test plan documents the testing strategy and final verification evidence for **Sprint 2** of **SwapLah**, a web-based student co-op marketplace for polytechnic students.

Sprint 2 focuses on **Item Listing Management**. The purpose of this test plan is to verify that sellers can create and manage their own listings safely, while buyers can browse, search, filter, clear filters, and view active listings before contacting sellers.

### Sprint 2 Features Covered

| PBI / Issue | Sprint 2 User Story | Current Status | Priority |
| --- | --- | --- | --- |
| [#4](https://gitlab.com/nyp-sg/pet/it2112/26s1/it2112-03/assignment/team_2/swaplah/-/issues/4) | Create a new item listing | Closed / Done | High |
| [#5](https://gitlab.com/nyp-sg/pet/it2112/26s1/it2112-03/assignment/team_2/swaplah/-/issues/5) | View active listings with pagination | Closed / Done | High |
| [#6](https://gitlab.com/nyp-sg/pet/it2112/26s1/it2112-03/assignment/team_2/swaplah/-/issues/6) | Search listings by keyword | Closed / Done | Medium |
| [#7](https://gitlab.com/nyp-sg/pet/it2112/26s1/it2112-03/assignment/team_2/swaplah/-/issues/7) | Filter listings by Category and Condition | Closed / Done | Medium |
| [#20](https://gitlab.com/nyp-sg/pet/it2112/26s1/it2112-03/assignment/team_2/swaplah/-/issues/20) | Clear Category and Condition filters individually | Closed / Done | Medium |
| [#21](https://gitlab.com/nyp-sg/pet/it2112/26s1/it2112-03/assignment/team_2/swaplah/-/issues/21) | Edit own listing | Closed / Done | High |
| [#22](https://gitlab.com/nyp-sg/pet/it2112/26s1/it2112-03/assignment/team_2/swaplah/-/issues/22) | Soft-delete own listing | Closed / Done | High |
| [#23](https://gitlab.com/nyp-sg/pet/it2112/26s1/it2112-03/assignment/team_2/swaplah/-/issues/23) | View listing details and seller contact information | Closed / Done | High |

---

## 2. Scope

### 2.1 In Scope

The following items are included in Sprint 2 testing:

- Unit tests for listing price validation, listing field extraction, required field validation, listing creation, listing retrieval, search, filter, owner-only update, soft-delete, and seller listing retrieval.
- API / route tests for:
  - `GET /api/listings`
  - `POST /api/listings`
  - `GET /api/listings/<listing_id>`
  - `PUT /api/listings/<listing_id>`
  - `DELETE /api/listings/<listing_id>`
  - `GET /api/listings?search=keyword`
  - `GET /api/listings?category=value&condition=value`
- Selenium UI tests for Sprint 2 item-listing flows:
  - End-to-end listing creation
  - Search, filter, and individual clear filter behaviour
  - Listing detail viewing
  - Edit listing behaviour
  - Soft-delete listing behaviour
- Page Object Model support for Selenium tests under `tests/ui/selenium/pages/`.
- Manual browser testing for listing creation, browsing, pagination, search, filter, clear filter, edit, listing detail, and soft-delete behaviour.
- Regression testing to ensure Sprint 1 account management features continue to pass after Sprint 2 listing changes.
- Static testing using pylint.
- Cyclomatic complexity checking using radon.
- Coverage checking using pytest-cov.
- GitLab CI/CD pipeline verification.
- AI prompt and refinement documentation.

### 2.2 Out of Scope

| Item | Reason |
| --- | --- |
| Payment testing | SwapLah does not include real payment features in Sprint 2. |
| Full offer negotiation testing | Offers and transactions are handled under a separate module / epic. |
| Review and rating testing | Reviews are outside the Sprint 2 Item Listing Management scope. |
| Admin report moderation testing | Reporting and moderation are handled under another module / epic. |
| Load testing | Not required for the small assignment dataset and current Sprint 2 scope. |
| Full security penetration testing | GitLab SAST, dependency scanning, and secret detection are used for automated security checks. |
| Full cross-browser Selenium matrix | Selenium tests run in headless Chrome / Chromium. Edge and Firefox matrix testing is outside Sprint 2 scope. |

---

## 3. Test Approach

### 3.1 Testing Pyramid Target

| Level | Target Count | Tool | Pipeline Stage | Purpose |
| --- | ---: | --- | --- | --- |
| Unit tests | 10–15+ | pytest | test | Verify individual listing helper functions and database functions. |
| API / Route tests | 10–15+ | pytest + Flask test client | test | Verify HTTP route behaviour from the outside. |
| UI smoke / flow tests | 5 Sprint 2 Selenium flows | Selenium WebDriver + headless Chrome | test | Verify complete listing-related user flows in a browser. |
| Static analysis | All `.py` files | pylint >= 10.0 | validate | Detect style, structure, and code quality issues. |
| Complexity check | All application functions | radon | validate | Confirm functions are maintainable and testable. |
| Coverage check | Application logic | pytest-cov | test | Confirm at least 75% unit coverage for the current A-band gate and at least 60% for the assignment minimum. |

### 3.2 Static Testing

- **Tool:** pylint
- **Threshold:** score must be `10.0/10`
- **Purpose:** Detect syntax problems, unused imports, naming issues, overly long functions, and poor code structure before dynamic tests run.
- **Pipeline stage:** validate

### 3.3 Complexity Testing

- **Tool:** radon
- **Threshold:** cyclomatic complexity per function should not exceed 10.
- **Purpose:** Identify functions that are difficult to test or should be refactored.
- **Pipeline stage:** validate
- **Rule:** If a function has complexity above 10, it is treated as high risk and should be refactored or covered with additional tests before merge.

### 3.4 Dynamic Testing

- **Tools:** pytest, pytest-cov, Flask test client, Selenium WebDriver
- **Assignment minimum coverage:** `>= 60%` application logic coverage
- **A-band / current pipeline threshold:** `>= 75%` unit coverage
- **Actual final unit coverage:** 77%
- **Unit test design:** white-box testing, because developers know the internal branches and validation logic.
- **API / route test design:** black-box testing, because tests verify request/response behaviour against the user story and acceptance criteria.
- **Selenium test design:** browser-based end-to-end testing for complete user flows.
- **Pipeline stage:** test

### 3.5 Acceptance Testing

- **Method:** Sprint Review demonstration, manual browser testing, and Selenium headless browser testing.
- **Assessor:** Tutor / Product Owner / Team reviewer.
- **Criteria:** Each Sprint 2 user story must be checked against its Acceptance Criteria before moving the issue to Done.
- **Evidence:** GitLab issue checklist, merge request, CI pipeline result, Selenium/UI test results, and this test plan.

---

## 4. Test Items

This section follows the Lesson 7 test plan structure by listing specific items to be tested, related user stories, cyclomatic complexity, minimum tests required, and risk.

Complexity values are numeric for implemented Python functions. Items marked **N/A** are UI behaviours or browser-level flows where the test target is not a single Python function.

### 4.1 Unit Test Items

| Function / Helper | Related User Story | Cyclomatic Complexity | Minimum Tests Required | Risk / Priority |
| --- | --- | ---: | ---: | --- |
| `is_valid_price()` | #4 Create listing price validation | 4 | 4 | High — must accept numeric values, `Free`, and `Swap Only`, while rejecting invalid formats. |
| `normalise_price()` | #4 Create listing price formatting | 3 | 3 | Medium — price must be stored consistently for UI and API responses. |
| `_extract_fields()` | #4 / #21 Create and update listing | 3 | 3 | High — field extraction supports both `imageUrl` and `image_url`. |
| `_has_missing_fields()` | #4 / #21 Required listing fields | 2 | 2 | High — missing required fields must be blocked. |
| `_validate_listing_fields()` | #4 / #21 Listing validation | 3 | 3 | High — validates required fields and price before database changes. |
| `_get_validated_fields()` | #4 / #21 Request body validation | 3 | 3 | High — invalid JSON or invalid fields must return safe errors. |
| `create_listing()` | #4 Create new listing | 1 | 3 | High — creates listing record with unique ID, listing date, and last modified timestamp. |
| `get_all_listings()` | #5 Browse active listings | 1 | 2 | High — buyers must only see active listings. |
| `search_active_listings()` | #6 / #7 Search and filter listings | 3 | 4 | Medium — search and filter results must match keyword, category, and condition rules. |
| `get_listing_by_id()` | #23 Listing detail page | 2 | 2 | High — must return active listing details or `None` safely. |
| `ensure_listing_status_column()` | #5 / #22 Soft-delete support | 2 | 2 | Medium — old databases must receive the `status` column safely. |
| `update_listing()` | #21 Edit own listing | 3 | 3 | High — must block non-owners and update last modified timestamp. |
| `soft_delete_listing()` | #22 Soft-delete listing | 3 | 3 | High — must mark listing as `Deleted` without removing the database record. |
| `get_listing_owner()` | #21 / #22 Owner validation | 2 | 2 | High — edit and delete permissions depend on correct owner lookup. |
| `get_listings_by_seller()` | #21 / swap dropdown support | 1 | 2 | Medium — seller-specific listing retrieval must be correct. |

### 4.2 API / Route Test Items

| Route / Behaviour | Related User Story | Implemented Function / Scope | Cyclomatic Complexity | Minimum Tests Required | Risk / Priority |
| --- | --- | --- | ---: | ---: | --- |
| `GET /api/listings` | #5 Browse active listings with pagination | `api_get_active_listings()` | 1 | 4 | High — buyers must only see active, non-deleted listings with correct pagination metadata. |
| `POST /api/listings` | #4 Create new listing | `api_create_listing()` | 3 | 6 | High — must validate login, required fields, price, and successful creation. |
| `GET /api/listings/<listing_id>` | #23 Listing details | `api_get_listing_detail()` | 2 | 3 | High — must show listing and seller details, and reject missing/deleted listings. |
| `PUT /api/listings/<listing_id>` | #21 Edit own listing | `api_update_listing()` | 4 | 5 | High — must validate authentication, ownership, input data, and successful update. |
| `DELETE /api/listings/<listing_id>` | #22 Soft-delete own listing | `api_delete_listing()` | 4 | 5 | High — must validate authentication, ownership, missing/deleted listing states, and successful soft-delete. |
| Search by keyword using `?search=` | #6 Search listings | `api_get_active_listings()` / filter query logic | 2 | 4 | Medium — keyword must match Title and Description and return newest first. |
| Filter by `?category=` and `?condition=` | #7 Filter listings | `api_get_active_listings()` / filter query logic | 2 | 4 | Medium — category, condition, and combined filters must return correct listings. |
| Clear Category and Condition filters individually | #20 Clear filters | UI query-parameter behaviour | N/A | 3 | Medium — clearing one filter must preserve the other active filter and search keyword. |

### 4.3 UI / Acceptance Test Items

| User Flow | Related User Story | Test Type | Priority | Expected Evidence |
| --- | --- | --- | --- | --- |
| End-to-end listing creation flow | #4 Create listing | Selenium UI / acceptance | High | Selenium test showing seller can create a listing and view it afterward. |
| Browse active listing cards with pagination | #5 Browse listings | Manual + API / acceptance | High | Browser/API evidence that active listing cards display with pagination. |
| Search and filter listing results | #6 / #7 Search and filter | Selenium UI / acceptance | Medium | Selenium test showing keyword search, Category filter, and Condition filter work. |
| Clear filters individually | #20 Clear filters | Selenium UI / acceptance | Medium | Selenium test showing Category and Condition filters can be cleared individually. |
| Open listing detail page and view seller contact information | #23 Listing detail | Manual + API / acceptance | High | Browser/API evidence that listing details and seller contact information appear. |
| Owner edits own listing successfully | #21 Edit listing | Manual + API / acceptance | High | Browser/API evidence that owner can edit and changes are saved. |
| Owner soft-deletes own listing | #22 Soft delete | Selenium UI / acceptance | High | Selenium test showing owner can soft-delete and listing becomes unavailable to buyers. |

---

## 5. Test Environment

| Area | Configuration |
| --- | --- |
| Language | Python 3.x |
| Framework | Flask |
| Frontend | HTML5, Bootstrap, Jinja templates |
| Database | SQLite test database / isolated SQLite fixture |
| Test framework | pytest |
| Coverage tool | pytest-cov |
| Static analysis | pylint |
| Complexity analysis | radon |
| UI automation | Selenium WebDriver |
| Browser for Selenium | Headless Chrome / Chromium |
| CI/CD platform | GitLab CI/CD |
| CI image | python:3.11-bookworm |
| Dependencies | Installed from `requirements-dev.txt` for development, testing, quality, and CI checks |
| Browser for manual verification | Chrome / Edge / Firefox |

### Test Isolation Rule

Each automated test must create and clean up its own test data. Tests must not depend on the production `swaplah.db` file, local browser state, or data created by another test. Temporary databases or isolated fixtures should be used during test execution.

---

## 6. Entry and Exit Criteria

### 6.1 Entry Criteria

Testing can begin when:

- Sprint 2 feature branch is pushed to GitLab.
- Merge Request is created.
- No Python syntax errors exist.
- Related Sprint 2 PBI has a clear user story and acceptance criteria.
- Related Sprint 2 PBI has milestone, labels, priority, type, and story points.
- Required test files are added under `tests/unit`, `tests/api`, or `tests/ui`.
- Selenium Page Object Model files are added under `tests/ui/selenium/pages/` when UI flows are automated.
- Flask app can run locally in development mode.
- Test database setup is available.
- pylint validate stage passes with score `10.0/10`.

### 6.2 Exit Criteria — Verification

Sprint 2 verification is complete when:

- [x] Focused listing/timezone regression passes locally with 0 failures: 60 passed.
- [x] Saved unit/API/UI pytest reports show 0 failures: 84 unit, 43 API, and 2 UI tests passed.
- [x] UI listing creation flow test passes.
- [x] Search/filter Selenium UI flow test passes.
- [x] Listing detail Selenium UI flow test passes.
- [x] Edit listing Selenium UI flow test passes.
- [x] Soft-delete Selenium UI flow test passes.
- [x] Test coverage is at least 75% for the current A-band gate and at least 60% for the assignment minimum: 77%.
- [x] pylint score is 10.00/10 against the 10.0 target.
- [x] radon complexity check shows no implemented function exceeds complexity 10; highest is B(7).
- [ ] GitLab pipeline is green on the Merge Request (user-reported, not repository-verifiable locally).
- [x] No new SAST or secret detection issues are introduced.
- [x] No generated files such as `.env`, `.coverage`, `.venv`, `__pycache__`, or `swaplah.db` are committed.

### 6.3 Exit Criteria — Validation

Sprint 2 validation is complete when:

- [ ] Product Owner / Tutor acceptance criteria are verified through issue checklist, MR evidence, and test results.
- [x] All Sprint 2 test cases are updated to Passing.
- [x] Sprint 2 work items are closed and moved to Done only after MRs are merged and checklists are complete.
- [ ] At least one teammate reviews and approves the Merge Request.
- [x] Related GitLab issue is moved to Done after the MR is merged and the issue checklist is complete.

### 6.4 Suspension and Resumption Criteria

| Criteria Type | Condition |
| --- | --- |
| Suspension criteria | Testing stops if the Flask app cannot start, database setup fails, Selenium WebDriver cannot launch, or CI runner fails for reasons unrelated to the code. |
| Resumption criteria | Testing resumes after the blocking defect is fixed, database setup works, browser driver setup works, and the pipeline can run again. |

---

## 7. Sprint 2 Test Cases

| Test ID | Module | Related PBI | Description | Type | Preconditions | Steps | Expected Result | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TC-S2-CREATE-001 | Create Listing | #4 | Create listing with valid details | Positive | Seller is logged in | 1. Open listing creation page 2. Enter Title, Description, numeric Price, Category, Condition, and image URL 3. Submit form | Listing is created successfully and shown as an active listing | Pass |
| TC-S2-CREATE-002 | Create Listing | #4 | Accept numeric price | Positive | Seller is logged in | 1. Submit listing with price `12.50` 2. Save listing | Listing is created and price is stored in valid format | Pass |
| TC-S2-CREATE-003 | Create Listing | #4 | Accept `Free` price | Positive | Seller is logged in | 1. Submit listing with price `Free` 2. Save listing | Listing is created successfully with price shown as `Free` | Pass |
| TC-S2-CREATE-004 | Create Listing | #4 | Accept `Swap Only` price | Positive | Seller is logged in | 1. Submit listing with price `Swap Only` 2. Save listing | Listing is created successfully with price shown as `Swap Only` | Pass |
| TC-S2-CREATE-005 | Create Listing | #4 | Reject missing required fields | Negative | Seller is logged in | 1. Leave Title, Description, Price, Category, Condition, or image URL blank 2. Submit form | Listing is not created and an error message is displayed | Pass |
| TC-S2-CREATE-006 | Create Listing | #4 | Reject invalid price | Negative | Seller is logged in | 1. Submit listing with invalid price such as `abc` or `-5` 2. Submit form | Listing is not created and price validation error is displayed | Pass |
| TC-S2-CREATE-007 | Create Listing | #4 | Block logged-out user from creating listing | Negative / Security | User is not logged in | 1. Clear session 2. Send `POST /api/listings` with valid listing data | Request is blocked with login required message or redirect | Pass |
| TC-S2-CREATE-008 | Create Listing | #4 | Listing stores ID and timestamps | Positive | Seller is logged in | 1. Create valid listing 2. Check returned listing data | Listing has unique ID, Listing Date, and last modified Timestamp | Pass |
| TC-S2-BROWSE-001 | Browse Listings | #5 | Show active non-deleted listings only | Positive | Active listings exist | 1. Open listings page 2. View listing results | Only active, non-deleted listings are displayed | Pass |
| TC-S2-BROWSE-002 | Browse Listings | #5 | Paginate listings at 10 items per page | Positive | More than 10 active listings exist | 1. Open listings page or send `GET /api/listings?page=1` | System displays 10 listings per page | Pass |
| TC-S2-BROWSE-003 | Browse Listings | #5 | Navigate to next page | Positive | More than 10 active listings exist | 1. Open page 2 or click next page | Next set of active listings is displayed | Pass |
| TC-S2-BROWSE-004 | Browse Listings | #5 | Hide soft-deleted listing from browse results | Negative | A listing has status `Deleted` | 1. Open listings page 2. Check displayed listings | Deleted listing is not shown | Pass |
| TC-S2-BROWSE-005 | Browse Listings | #5 | Retrieve active listings using GET API | Positive | Active listings exist | 1. Send `GET /api/listings` | API returns active listings as JSON with pagination metadata | Pass |
| TC-S2-SEARCH-001 | Search Listings | #6 | Search by title keyword | Positive | Listings with matching title exist | 1. Enter keyword in search bar 2. Submit search or send `GET /api/listings?search=keyword` | Listings with matching title are returned | Pass |
| TC-S2-SEARCH-002 | Search Listings | #6 | Search by description keyword | Positive | Listings with matching description exist | 1. Search using keyword found in description | Listings with matching description are returned | Pass |
| TC-S2-SEARCH-003 | Search Listings | #6 | Show no results when keyword does not match | Negative | No matching listings exist | 1. Search for a random keyword 2. View results | System shows no matching results | Pass |
| TC-S2-SEARCH-004 | Search Listings | #6 | Search results ordered newest first | Positive | Multiple matching listings exist | 1. Search common keyword 2. Check order of results | Newest listings are displayed first by Listing Date | Pass |
| TC-S2-FILTER-001 | Filter Listings | #7 | Filter by Category | Positive | Listings from different categories exist | 1. Select a Category filter 2. Apply filter | Only listings in selected Category are displayed | Pass |
| TC-S2-FILTER-002 | Filter Listings | #7 | Filter by Condition | Positive | Listings with different conditions exist | 1. Select a Condition filter 2. Apply filter | Only listings with selected Condition are displayed | Pass |
| TC-S2-FILTER-003 | Filter Listings | #7 | Filter by Category and Condition together | Positive | Listings with matching and non-matching combinations exist | 1. Select Category and Condition filters 2. Apply filters | Only listings matching both filters are displayed | Pass |
| TC-S2-FILTER-004 | Filter Listings | #7 | Return no results if no listing matches filter | Negative | No listing matches selected filter combination | 1. Apply filter combination with no matches | System shows no matching results | Pass |
| TC-S2-CLEAR-001 | Clear Filters | #20 | Clear Category filter only | Positive | Category and Condition filters are applied | 1. Clear Category filter 2. View results | Category filter is removed while Condition filter remains active | Pass |
| TC-S2-CLEAR-002 | Clear Filters | #20 | Clear Condition filter only | Positive | Category and Condition filters are applied | 1. Clear Condition filter 2. View results | Condition filter is removed while Category filter remains active | Pass |
| TC-S2-CLEAR-003 | Clear Filters | #20 | Clear one filter while keeping the other | Positive | Both filters are active | 1. Clear one selected filter | Other filter remains active and results update correctly | Pass |
| TC-S2-EDIT-001 | Edit Listing | #21 | Owner edits own listing successfully | Positive | Seller is logged in and owns listing | 1. Open edit listing page 2. Update listing details 3. Submit update | Listing is updated successfully | Pass |
| TC-S2-EDIT-002 | Edit Listing | #21 | Update changes last modified timestamp | Positive | Seller owns listing | 1. Record current timestamp 2. Edit listing 3. Save update | Last modified Timestamp is updated | Pass |
| TC-S2-EDIT-003 | Edit Listing | #21 | Non-owner cannot edit listing | Negative / Security | User is logged in but does not own listing | 1. Send `PUT /api/listings/<listing_id>` for another seller’s listing | Update is blocked with forbidden error | Pass |
| TC-S2-EDIT-004 | Edit Listing | #21 | Reject update for deleted or missing listing | Negative | Listing does not exist or has already been deleted | 1. Send `PUT /api/listings/<invalid_id>` | System returns appropriate not found or unavailable error | Pass |
| TC-S2-EDIT-005 | Edit Listing | #21 | Reject invalid update data | Negative | Seller owns listing | 1. Submit update with missing required fields or invalid price | Update fails and validation error is displayed | Pass |
| TC-S2-DELETE-001 | Soft Delete Listing | #22 | Owner soft-deletes own listing | Positive | Seller is logged in and owns listing | 1. Send `DELETE /api/listings/<listing_id>` or click Delete in UI | Listing status is changed to `Deleted` without removing database record | Pass |
| TC-S2-DELETE-002 | Soft Delete Listing | #22 | Deleted listing hidden from active listings | Positive | Listing has been soft-deleted | 1. Open listings page or send `GET /api/listings` | Deleted listing is not shown in active listings | Pass |
| TC-S2-DELETE-003 | Soft Delete Listing | #22 | Non-owner cannot delete listing | Negative / Security | User is logged in but does not own listing | 1. Send `DELETE /api/listings/<listing_id>` for another seller’s listing | Delete is blocked with forbidden error | Pass |
| TC-S2-DELETE-004 | Soft Delete Listing | #22 | Reject delete for missing listing | Negative | Listing does not exist | 1. Send `DELETE /api/listings/<invalid_id>` | System returns appropriate not found error | Pass |
| TC-S2-DETAIL-001 | Listing Details | #23 | View active listing detail page | Positive | Active listing exists | 1. Open `/listing/<listing_id>` or send `GET /api/listings/<listing_id>` | Listing details are displayed | Pass |
| TC-S2-DETAIL-002 | Listing Details | #23 | Seller contact information is shown | Positive | Active listing exists with seller account | 1. Open listing detail page | Seller Display Name, Email, and Contact Number are displayed | Pass |
| TC-S2-DETAIL-003 | Listing Details | #23 | Reject invalid listing ID | Negative | Listing does not exist | 1. Open invalid listing detail URL or send `GET /api/listings/<invalid_id>` | System shows not found or unavailable error | Pass |
| TC-S2-DETAIL-004 | Listing Details | #23 | Hide deleted listing detail | Negative | Listing has been soft-deleted | 1. Open detail page for deleted listing | System shows unavailable or not found message | Pass |
| TC-S2-UI-001 | UI Listing Flow | #4 | End-to-end listing creation flow | Positive / Selenium UI | Seller account exists and user can log in | 1. Login 2. Open Sell/Create Listing page 3. Enter valid listing details 4. Submit 5. View listing in active listings | User can create listing through UI and see it in active listings | Pass |
| TC-S2-UI-002 | UI Search / Filter Flow | #6 / #7 / #20 | Search, filter, and clear filters through browser UI | Positive / Selenium UI | Listing test data exists | 1. Search keyword 2. Apply Category filter 3. Apply Condition filter 4. Clear one filter | Results update correctly and active filter state is preserved | Pass |
| TC-S2-UI-003 | UI Listing Detail Flow | #23 | View listing detail through browser UI | Positive / Selenium UI | Buyer is logged in and active listing exists | 1. Login 2. Open listing card/detail URL 3. View details and seller contact | Listing details and seller contact information are displayed | Pass |
| TC-S2-UI-004 | UI Edit Listing Flow | #21 | Edit own listing through browser UI | Positive / Selenium UI | Seller owns listing | 1. Login as owner 2. Open edit listing page 3. Update details 4. Save | Listing changes are saved and visible on detail page | Pass |
| TC-S2-UI-005 | UI Soft Delete Flow | #22 | Soft-delete listing through browser UI | Positive / Selenium UI | Seller owns listing | 1. Login as owner 2. Open listing detail 3. Soft-delete listing 4. Reopen detail page | Listing becomes unavailable / hidden after soft delete | Pass |
| TC-S2-REG-001 | Regression | Sprint 1 Account Management | Registration still works after listing changes | Regression | App is running and registration form is available | 1. Open Register page 2. Register with valid NYP email and required details | Account is created and password is stored as a hash | Pass |
| TC-S2-REG-002 | Regression | Sprint 1 Account Management | Login still works after listing changes | Regression | Registered user exists | 1. Open Login page 2. Submit valid email and password | User logs in and can access protected pages | Pass |
| TC-S2-REG-003 | Regression | Sprint 1 Profile Management | Profile view and update still work after listing changes | Regression | User is logged in | 1. Open profile page 2. Edit editable fields 3. Save | Profile is updated while Email and Student ID remain locked | Pass |

---

## 8. Sprint 2 Selenium UI Test Evidence

The Sprint 2 listing-related Selenium tests are stored under `tests/ui/selenium/`. The tests use shared fixtures and Page Object Model classes under `tests/ui/selenium/pages/`.

| Selenium Test Script | Related PBI | User Flow Covered | Status |
| --- | --- | --- | --- |
| `test_listing_creation_selenium.py` | #4 | Seller logs in, creates a listing through the UI, uploads/selects image data, submits the form, and confirms the listing appears | Pass |
| `test_listing_search_filter_selenium.py` | #6 / #7 / #20 | Buyer searches listings, applies Category and Condition filters, and clears filters individually | Pass |
| `test_listing_detail_selenium.py` | #23 | Logged-in buyer opens a listing detail page and confirms listing and seller contact details render | Pass |
| `test_edit_listing_selenium.py` | #21 | Listing owner edits their listing through the UI and confirms the saved changes appear on the detail page | Pass |
| `test_soft_delete_listing_selenium.py` | #22 | Seller soft-deletes own listing and confirms the listing is no longer available to buyers | Pass |

### Page Object Model Structure

| Page Object File | Purpose |
| --- | --- |
| `base_page.py` | Shared waits, element finding, text entry, clicking, URL checks, and text assertions. |
| `login_page.py` | Login form actions and login-page assertions. |
| `home_page.py` | Homepage search, category/condition filter, and clear-filter actions. |
| `sell_page.py` | Listing creation form actions. |
| `edit_listing_page.py` | Listing edit form actions. |
| `listing_detail_page.py` | Listing detail actions such as offer/soft-delete buttons and page assertions. |

---

## 9. Regression Testing

Before merging any Sprint 2 Merge Request, the following regression checks must pass:

| Regression Area | Command / Method | Expected Result |
| --- | --- | --- |
| Full automated test suite | `python -m pytest -q` | All implemented tests pass. |
| Unit coverage | `python -m pytest tests/unit --cov=app --cov-report=term-missing` | Coverage is at least 75% for the current A-band gate and at least 60% for the assignment minimum. |
| UI tests | `python -m pytest tests/ui` | Flask UI smoke tests and Selenium UI tests pass. |
| Sprint 2 Selenium listing tests | `python -m pytest tests/ui/selenium/test_listing_creation_selenium.py tests/ui/selenium/test_listing_search_filter_selenium.py tests/ui/selenium/test_listing_detail_selenium.py tests/ui/selenium/test_edit_listing_selenium.py tests/ui/selenium/test_soft_delete_listing_selenium.py` | Five Sprint 2 listing UI flows pass in headless browser. |
| Linting | `python -m pylint app tests scripts` | Score is 10.00/10 against the 10.0 target. |
| Complexity | `python -m radon cc app/ -s` | No implemented function exceeds complexity 10. |
| Manual create listing flow | Browser test | Seller can create a valid listing. |
| Manual browse listing flow | Browser test | Buyer can browse active listings. |
| Manual search/filter/clear flow | Browser test | Buyer can search, filter, and clear filters individually. |
| Manual edit listing flow | Browser test | Listing owner can edit their own listing. |
| Manual soft-delete flow | Browser test | Listing owner can soft-delete own listing and buyers no longer see it. |
| Manual listing detail flow | Browser test | Buyer can view listing details and seller contact information. |
| Manual Sprint 1 regression | Browser test | Login, registration, profile view, and profile update still work. |

---

## 10. Test Data

| Data Item | Example |
| --- | --- |
| Valid seller account | Logged-in active user with seller role or normal user account. |
| Other user account | Logged-in user who does not own the selected listing. |
| Active listing | Title: `Casio Calculator`, Category: `Electronics`, Condition: `Good`, Price: `12.50`. |
| Soft-deleted listing | Listing with `status = Deleted`. |
| Search keyword with matches | `calculator`, `book`, `laptop`. |
| Search keyword with no matches | `zzzzunknown`. |
| Valid price values | `10`, `12.50`, `Free`, `Swap Only`. |
| Invalid price values | `abc`, `-5`, `12.999`, blank price. |
| Invalid listing data | Missing title, missing description, missing price, missing category, missing condition, or missing image URL. |

---

## 11. Risks and Contingencies

| Risk | Probability | Impact | Mitigation / Contingency |
| --- | --- | --- | --- |
| Invalid price is accepted | Medium | High | Add positive and negative price validation tests for numeric, `Free`, `Swap Only`, invalid text, and negative values. |
| Logged-out user creates listing | Medium | High | Add authentication guard and negative API test for `POST /api/listings`. |
| Non-owner edits listing | Medium | High | Add ownership validation and negative API test for `PUT /api/listings/<listing_id>`. |
| Non-owner deletes listing | Medium | High | Add ownership validation and negative API test for `DELETE /api/listings/<listing_id>`. |
| Soft-deleted listing still appears | Medium | High | Add status filtering and regression tests confirming only active listings are returned. |
| Search does not check both Title and Description | Medium | Medium | Add separate tests for title keyword and description keyword. |
| Filter results are inaccurate | Medium | Medium | Add Category, Condition, and combined filter tests. |
| Clear filter removes the wrong query parameter | Medium | Medium | Add UI and route tests confirming one filter can be cleared while the other remains active. |
| Pagination displays wrong number of listings | Medium | Medium | Add tests using more than 10 active listings. |
| Last modified timestamp does not update | Medium | Medium | Add update timestamp test for edit listing. |
| Listing detail exposes wrong seller information | Low | High | Add seller contact verification test for listing detail page. |
| Test data affects real database | Medium | High | Use isolated SQLite test database fixtures and avoid production `swaplah.db`. |
| Pipeline fails due to missing browser dependency | Medium | Medium | Ensure Selenium, Chromium, and Chromium Driver are installed in the GitLab UI testing job. |
| License compliance warning appears for test dependencies | Medium | Low | Document that Selenium/browser dependencies are testing-only and verify security scanning has no new vulnerabilities. |

---

## 12. Related Links

- [Sprint board](https://gitlab.com/nyp-sg/pet/it2112/26s1/it2112-03/assignment/team_2/swaplah/-/boards)
- [CI/CD pipelines](https://gitlab.com/nyp-sg/pet/it2112/26s1/it2112-03/assignment/team_2/swaplah/-/pipelines)
- [Merge requests](https://gitlab.com/nyp-sg/pet/it2112/26s1/it2112-03/assignment/team_2/swaplah/-/merge_requests)
- [Test cases](https://gitlab.com/nyp-sg/pet/it2112/26s1/it2112-03/assignment/team_2/swaplah/-/quality/test_cases)
- Unit tests: `tests/unit/`
- API tests: `tests/api/`
- UI tests: `tests/ui/`
- Selenium tests: `tests/ui/selenium/`
- Selenium Page Object Model: `tests/ui/selenium/pages/`
- AI usage logs: `AI/`

---

## 13. Sprint 2 Definition of Done

### Verification

- [x] Code committed through a feature branch and Merge Request.
- [ ] Merge Request reviewed and approved by at least one teammate.
- [x] Code passes pylint with score `10.00/10` against the 10.0 target.
- [x] Cyclomatic complexity for implemented functions does not exceed 10.
- [x] All implemented unit tests pass.
- [x] All implemented API / route tests pass.
- [x] UI listing creation flow test passes.
- [x] Search/filter Selenium UI flow test passes.
- [x] Listing detail Selenium UI flow test passes.
- [x] Edit listing Selenium UI flow test passes.
- [x] Soft-delete Selenium UI flow test passes.
- [x] Test coverage is at least 75% for the current A-band gate and at least 60% for the assignment minimum.
- [ ] GitLab pipeline is green on the Merge Request (user-reported, not repository-verifiable locally).
- [x] No new linting, SAST, or secret detection issues are introduced.

### Validation

- [ ] Implemented acceptance criteria are confirmed with Product Owner / Tutor.
- [x] All Sprint 2 test cases are updated to Passing.
- [x] Related GitLab issues are moved to Done after the MRs are merged and the issue checklists are complete.
- [x] Sprint 2 board shows Sprint 2 work items as Closed / Done.

---

## 14. AI Prompt and Refinement Evidence

### AI Prompt Used

> Generate a Sprint 2 test plan for SwapLah Assignment 1. Sprint 2 focuses on Item Listing Management, including create listing, view active listings with pagination, search listings, filter listings by Category and Condition, clear filters individually, edit own listing, soft-delete own listing, and view listing details with seller contact information. Follow the Lesson 7 test plan format with Introduction, Scope, Test Approach, Test Items, Test Environment, Entry and Exit Criteria, Risks, Regression Testing, Definition of Done, and at least 10 positive and negative test cases with Test ID, description, preconditions, steps, and expected results.

### Refinement Made

The AI-generated draft was reviewed and refined against the actual Sprint 2 GitLab issues under **Item Listing Management**. The original plan had some items marked as `Pending / Not Run` because search, filter, clear filter, and soft-delete were not fully verified at that time. After the Sprint 2 work items and merge requests were completed, the plan was updated so all Sprint 2 features are marked as `Closed / Done` and all related test cases are marked as `Pass`.

The test plan was also updated to include Selenium UI evidence for Sprint 2 item-listing flows. Selenium coverage now documents listing creation, search/filter/clear filters, listing detail viewing, edit listing, and soft-delete listing flows. The plan also records the Page Object Model structure under `tests/ui/selenium/pages/`, which centralises Selenium locators, waits, actions, and assertions.

### Manual Review Evidence

- Test cases were mapped to the Sprint 2 PBIs and acceptance criteria.
- Unit test items were checked against implemented listing helper functions and route handlers.
- API test items were checked against the required listing endpoints.
- Selenium test items were mapped only to Sprint 2 item-listing user flows.
- Search, filter, clear filter, and soft-delete items were changed from `Pending / Not Run` to `Pass` only after the related GitLab work items were closed and moved to Done.
- The plan was structured using the Lesson 7 test plan format and expanded with regression testing, DoD, Selenium/POM evidence, and AI prompt/refinement evidence for final submission.

---

## 15. Final Repository Evidence Update

Evidence captured on 25 Jul 2026 from the current repository and local verification:

| Evidence item | Final value |
| --- | --- |
| Focused listing/timezone pytest regression | 60 passed |
| Saved unit test report | 84 passed, 0 failures |
| Saved API test report | 43 passed, 0 failures |
| Saved Flask UI test report | 2 passed, 0 failures |
| Saved unit coverage report | 75.69% line coverage |
| Newman API regression | 24 requests, 48 assertions, 0 failures |
| Newman HTML report | `reports/newman-report.html` |
| Sprint 2 Selenium listing scripts present | 5 scripts: creation, search/filter, detail, edit, soft delete |
| Pylint target and result | Target 10.0; result 10.00/10 |
| Highest cyclomatic complexity | B(7), `_common_error` in `app/routes/offers.py` |
| Longest application function | 38 lines, `_register_simple_page_routes` in `app/__init__.py` |
| Code-quality gate | Passed |
| Development dependencies | `requirements-dev.txt` |
| Selenium pipeline job name | `selenium-ui-tests` |
| Pipeline stages | validate, test, ui-test, api-test, security, build, deploy |

Current pipeline jobs in `.gitlab-ci.yml`: `pylint-application`, `code-quality-gate`, `pytest-unit-tests`, `pytest-api-tests`, `selenium-ui-tests`, `newman-api-tests`, `semgrep-sast`, `secret_detection`, `gemnasium-python-dependency_scanning`, `cyclonedx-sbom`, `security-gate`, `build-archive`, and `deploy-package`.

The final evidence preserves the historical refinement explanation above: earlier Pending / Not Run labels were changed only after repository tests and sprint evidence were available. This cleanup does not reopen or modify GitLab sprint history.
