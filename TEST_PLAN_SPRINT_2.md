# Test Plan — SwapLah

## Sprint 2, Version 1.0.0

**Team:** Team 2 — SwapLah
**Team members:** Felicia, Charlisa, Lucas, Lucio, Elijah
**Date created:** 12 Jun 2026
**Last updated:** 12 Jun 2026
**GitLab project:** `https://gitlab.com/nyp-sg/pet/it2112/26s1/it2112-03/assignment/team_2/swaplah`

---

## 1. Introduction

This test plan covers Sprint 2 of SwapLah, a web-based student co-op marketplace for polytechnic students.

Sprint 2 focuses on **Item Listing Management**. These features allow sellers to create and manage their item listings, while buyers can browse, search, filter, and view listing details before contacting the seller.

This Sprint adds and verifies the following features:

* Create a new listing with Title, Description, Price, Category, Condition, and one image URL
* View all active, non-deleted listings with pagination
* Search listings by keyword in Title and Description
* Filter listings by Category, Condition, or both
* Clear Category and Condition filters individually
* Edit an existing listing as the listing owner only
* Soft-delete an existing listing as the listing owner only
* View a listing detail page with the seller’s Display Name, Email, and Contact Number
* Retrieve active listings using `GET /api/listings`
* Retrieve one listing using `GET /api/listings/<listing_id>`
* Create a listing using `POST /api/listings`
* Update a listing using `PUT /api/listings/<listing_id>`
* Soft-delete a listing using `DELETE /api/listings/<listing_id>`

---

## 2. Scope

### In Scope

* Unit tests for listing validation, price validation, search, filtering, pagination, owner-only update, and soft delete
* API / route tests for listing creation, retrieval, update, delete, search, and filter endpoints
* UI test for the end-to-end listing creation flow
* Regression testing to ensure Sprint 1 account and login features still pass
* Static analysis using pylint for all Python files
* Cyclomatic complexity checking using radon
* Test coverage checking using pytest-cov
* GitLab CI/CD pipeline verification
* GitLab Test Cases linked to related Sprint 2 PBIs

### Out of Scope

| Item                              | Reason                                                |
| --------------------------------- | ----------------------------------------------------- |
| Payment testing                   | SwapLah does not include real payment features        |
| Offer negotiation testing         | Offers and transactions are handled in another epic   |
| Review and rating testing         | Reviews are outside Sprint 2 listing management scope |
| Admin report moderation testing   | Reporting and moderation are handled in another epic  |
| Load testing                      | Not required for Sprint 2                             |
| Full security penetration testing | GitLab SAST and secret detection are used instead     |

---

## 3. Test Approach

### Testing Pyramid Target

| Level                 |              Target Count | Tool                                  | Pipeline Stage |
| --------------------- | ------------------------: | ------------------------------------- | -------------- |
| Unit tests            |                     10–15 | pytest                                | test           |
| API / Route tests     |                     10–15 | pytest + Flask test client            | test           |
| UI smoke / flow tests |                       1–2 | pytest / Selenium / Flask test client | test           |
| Static analysis       |           All `.py` files | pylint >= 7.0                         | lint           |
| Complexity check      | All application functions | radon                                 | lint           |
| Coverage check        |         Application logic | pytest-cov                            | test           |

### Static Testing

* **Tool:** pylint
* **Threshold:** >= 7.0/10
* **Purpose:** Ensure Python code follows the agreed code quality standard
* **Stage:** lint / validate

### Complexity Testing

* **Tool:** radon
* **Threshold:** Cyclomatic complexity per function should not exceed 10
* **Purpose:** Identify overly complex functions that should be refactored
* **Stage:** lint / validate

### Dynamic Testing

* **Tool:** pytest + pytest-cov
* **Minimum coverage required:** >= 60% application logic coverage
* **Team target coverage:** >= 70% where possible
* **Test design:** White-box testing for unit tests and black-box testing for route/API tests
* **Stage:** test

### Acceptance Testing

* **Method:** Sprint Review demonstration and manual browser testing
* **Assessor:** Tutor / Product Owner / Team reviewer
* **Criteria:** Acceptance Criteria for each Sprint 2 user story must be verified before the issue is moved to Done

---

## 4. Test Items

| Function / Route                         | Related PBI                          | Complexity | Minimum Tests | Priority |
| ---------------------------------------- | ------------------------------------ | ---------: | ------------: | -------- |
| `POST /api/listings`                     | Create listing                       |     Medium |             5 | High     |
| `GET /api/listings`                      | View active listings with pagination |     Medium |             4 | High     |
| `GET /api/listings?search=keyword`       | Search listings                      |     Medium |             4 | Medium   |
| `GET /api/listings?category=&condition=` | Filter listings                      |     Medium |             4 | Medium   |
| `GET /api/listings/<listing_id>`         | View listing detail                  |        Low |             3 | Medium   |
| `PUT /api/listings/<listing_id>`         | Edit own listing                     |     Medium |             5 | High     |
| `DELETE /api/listings/<listing_id>`      | Soft-delete own listing              |     Medium |             5 | High     |
| `create_listing()`                       | Create listing database helper       |        Low |             3 | High     |
| `get_all_listings()`                     | Retrieve active listings             |     Medium |             3 | High     |
| `get_listing_by_id()`                    | Retrieve listing details             |     Medium |             3 | Medium   |
| `update_listing()`                       | Update owner listing                 |     Medium |             3 | High     |
| `is_valid_price()`                       | Price validation                     |        Low |             4 | High     |
| `normalise_price()`                      | Price formatting                     |        Low |             3 | Medium   |

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
* **Dependencies:** installed from `requirements.txt`
* **Browser:** Chrome / Edge / Firefox

### Test Isolation Rule

Each automated test must create and destroy its own test data. Tests must not depend on the production `swaplah.db` file. Temporary databases or isolated fixtures should be used during test execution.

---

## 6. Entry and Exit Criteria

### Entry Criteria

Testing can begin when:

* Sprint 2 feature branch is pushed to GitLab.
* Merge Request is created.
* No Python syntax errors exist.
* Required test files are added under `tests/unit`, `tests/api`, or `tests/ui`.
* Feature acceptance criteria are written in the related GitLab issue.
* Related issue has Sprint 2 milestone, labels, priority, and story points.
* pylint validate stage passes with score >= 7.0.

### Exit Criteria — Verification

Sprint 2 verification is complete when:

* [ ] All unit tests pass with 0 failures.
* [ ] All API / route tests pass with 0 failures.
* [ ] UI listing creation flow test passes.
* [ ] Test coverage is at least 60%.
* [ ] pylint score is at least 7.0/10.
* [ ] radon complexity check shows function complexity does not exceed 10.
* [ ] GitLab pipeline is green on the Merge Request.
* [ ] No generated files such as `.env`, `.coverage`, `.venv`, `__pycache__`, or `swaplah.db` are committed.

### Exit Criteria — Validation

Sprint 2 validation is complete when:

* [ ] Product Owner / Tutor confirms Sprint 2 acceptance criteria.
* [ ] All related GitLab test cases are updated to Passing.
* [ ] At least one teammate reviews and approves the Merge Request.
* [ ] The related GitLab issue is moved to Done only after the MR is merged.

---

## 7. Sprint 2 Test Cases

| Test ID          | Module              | Related User Story                                | Description                                    | Type                | Preconditions                                              | Steps                                                                                                                       | Expected Result                                                       | Status            |
| ---------------- | ------------------- | ------------------------------------------------- | ---------------------------------------------- | ------------------- | ---------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- | ----------------- |
| TC-S2-CREATE-001 | Create Listing      | Create a new item listing                         | Create listing with valid details              | Positive            | Seller is logged in                                        | 1. Open listing creation page 2. Enter Title, Description, numeric Price, Category, Condition, and image URL 3. Submit form | Listing is created successfully and shown as an active listing        | Pass              |
| TC-S2-CREATE-002 | Create Listing      | Create a new item listing                         | Accept numeric price                           | Positive            | Seller is logged in                                        | 1. Submit listing with price `12.50` 2. Save listing                                                                        | Listing is created and price is stored in valid format                | Pass              |
| TC-S2-CREATE-003 | Create Listing      | Create a new item listing                         | Accept `Free` price                            | Positive            | Seller is logged in                                        | 1. Submit listing with price `Free` 2. Save listing                                                                         | Listing is created successfully with price shown as `Free`            | Pass              |
| TC-S2-CREATE-004 | Create Listing      | Create a new item listing                         | Accept `Swap Only` price                       | Positive            | Seller is logged in                                        | 1. Submit listing with price `Swap Only` 2. Save listing                                                                    | Listing is created successfully with price shown as `Swap Only`       | Pass              |
| TC-S2-CREATE-005 | Create Listing      | Create a new item listing                         | Reject missing required fields                 | Negative            | Seller is logged in                                        | 1. Leave Title, Description, Price, Category, Condition, or image URL blank 2. Submit form                                  | Listing is not created and an error message is displayed              | Pass              |
| TC-S2-CREATE-006 | Create Listing      | Create a new item listing                         | Reject invalid price                           | Negative            | Seller is logged in                                        | 1. Submit listing with invalid price such as `abc` or `-5` 2. Submit form                                                   | Listing is not created and price validation error is displayed        | Pass              |
| TC-S2-CREATE-007 | Create Listing      | Create a new item listing                         | Block logged-out user from creating listing    | Negative / Security | User is not logged in                                      | 1. Clear session 2. Send `POST /api/listings` with valid listing details                                                    | Request is blocked with login required message or redirect            | Pass              |
| TC-S2-CREATE-008 | Create Listing      | Create a new item listing                         | Listing stores ID and timestamps               | Positive            | Seller is logged in                                        | 1. Create valid listing 2. Check returned listing data                                                                      | Listing has unique ID, Listing Date, and last modified Timestamp      | Pass              |
| TC-S2-BROWSE-001 | Browse Listings     | View active listings with pagination              | Show active non-deleted listings only          | Positive            | Active listings exist                                      | 1. Open listings page 2. View listing results                                                                               | Only active, non-deleted listings are displayed                       | Pass              |
| TC-S2-BROWSE-002 | Browse Listings     | View active listings with pagination              | Paginate listings at 10 items per page         | Positive            | More than 10 active listings exist                         | 1. Open listings page or `GET /api/listings?page=1`                                                                         | System displays 10 listings per page                                  | Pass              |
| TC-S2-BROWSE-003 | Browse Listings     | View active listings with pagination              | Navigate to next page                          | Positive            | More than 10 active listings exist                         | 1. Open page 2 or click next page                                                                                           | Next set of active listings is displayed                              | Pass              |
| TC-S2-BROWSE-004 | Browse Listings     | View active listings with pagination              | Hide soft-deleted listing from browse results  | Negative            | A listing has status Deleted                               | 1. Open listings page 2. Check displayed listings                                                                           | Deleted listing is not shown                                          | Pass              |
| TC-S2-BROWSE-005 | Browse Listings     | Retrieve all active listings API                  | Retrieve active listings using GET API         | Positive            | Active listings exist                                      | 1. Send `GET /api/listings`                                                                                                 | API returns active listings as JSON with pagination metadata          | Pass              |
| TC-S2-SEARCH-001 | Search Listings     | Search listings by keyword                        | Search by title keyword                        | Positive            | Listings with matching title exist                         | 1. Enter keyword in search bar 2. Submit search or send `GET /api/listings?search=keyword`                                  | Listings with matching title are returned                             | Pending / Not Run |
| TC-S2-SEARCH-002 | Search Listings     | Search listings by keyword                        | Search by description keyword                  | Positive            | Listings with matching description exist                   | 1. Search using keyword found in description                                                                                | Listings with matching description are returned                       | Pending / Not Run |
| TC-S2-SEARCH-003 | Search Listings     | Search listings by keyword                        | Show no results when keyword does not match    | Negative            | No matching listings exist                                 | 1. Search for a random keyword 2. View results                                                                              | System shows no matching results                                      | Pending / Not Run |
| TC-S2-SEARCH-004 | Search Listings     | Search listings by keyword                        | Search results ordered newest first            | Positive            | Multiple matching listings exist                           | 1. Search common keyword 2. Check order of results                                                                          | Newest listings are displayed first by Listing Date                   | Pending / Not Run |
| TC-S2-FILTER-001 | Filter Listings     | Filter listings by Category and Condition         | Filter by Category                             | Positive            | Listings from different categories exist                   | 1. Select a Category filter 2. Apply filter                                                                                 | Only listings in selected Category are displayed                      | Pending / Not Run |
| TC-S2-FILTER-002 | Filter Listings     | Filter listings by Category and Condition         | Filter by Condition                            | Positive            | Listings with different conditions exist                   | 1. Select a Condition filter 2. Apply filter                                                                                | Only listings with selected Condition are displayed                   | Pending / Not Run |
| TC-S2-FILTER-003 | Filter Listings     | Filter listings by Category and Condition         | Filter by Category and Condition together      | Positive            | Listings with matching and non-matching combinations exist | 1. Select Category and Condition filters 2. Apply filters                                                                   | Only listings matching both filters are displayed                     | Pending / Not Run |
| TC-S2-FILTER-004 | Filter Listings     | Filter listings by Category and Condition         | Return no results if no listing matches filter | Negative            | No listing matches selected filter combination             | 1. Apply filter combination with no matches                                                                                 | System shows no matching results                                      | Pending / Not Run |
| TC-S2-CLEAR-001  | Clear Filters       | Clear Category and Condition filters individually | Clear Category filter only                     | Positive            | Category and Condition filters are applied                 | 1. Clear Category filter 2. View results                                                                                    | Category filter is removed while Condition filter remains active      | Pending / Not Run |
| TC-S2-CLEAR-002  | Clear Filters       | Clear Category and Condition filters individually | Clear Condition filter only                    | Positive            | Category and Condition filters are applied                 | 1. Clear Condition filter 2. View results                                                                                   | Condition filter is removed while Category filter remains active      | Pending / Not Run |
| TC-S2-CLEAR-003  | Clear Filters       | Clear Category and Condition filters individually | Clear one filter while keeping the other       | Positive            | Both filters are active                                    | 1. Clear one selected filter                                                                                                | Other filter remains active and results update correctly              | Pending / Not Run |
| TC-S2-EDIT-001   | Edit Listing        | Edit own listing                                  | Owner edits own listing successfully           | Positive            | Seller is logged in and owns listing                       | 1. Open edit listing page 2. Update listing details 3. Submit update                                                        | Listing is updated successfully                                       | Pass              |
| TC-S2-EDIT-002   | Edit Listing        | Edit own listing                                  | Update changes last modified timestamp         | Positive            | Seller owns listing                                        | 1. Record current timestamp 2. Edit listing 3. Save update                                                                  | Last modified Timestamp is updated                                    | Pass              |
| TC-S2-EDIT-003   | Edit Listing        | Edit own listing                                  | Non-owner cannot edit listing                  | Negative / Security | User is logged in but does not own listing                 | 1. Send `PUT /api/listings/<listing_id>` for another seller’s listing                                                       | Update is blocked with forbidden error                                | Pass              |
| TC-S2-EDIT-004   | Edit Listing        | Edit own listing                                  | Reject update for deleted or missing listing   | Negative            | Listing does not exist or has been deleted                 | 1. Send `PUT /api/listings/<invalid_id>`                                                                                    | System returns appropriate not found or unavailable error             | Pass              |
| TC-S2-EDIT-005   | Edit Listing        | Edit own listing                                  | Reject invalid update data                     | Negative            | Seller owns listing                                        | 1. Submit update with missing required fields or invalid price                                                              | Update fails and validation error is displayed                        | Pass              |
| TC-S2-DELETE-001 | Soft Delete Listing | Soft-delete own listing                           | Owner soft-deletes own listing                 | Positive            | Seller is logged in and owns listing                       | 1. Send `DELETE /api/listings/<listing_id>`                                                                                 | Listing status is changed to Deleted without removing database record | Pending / Not Run |
| TC-S2-DELETE-002 | Soft Delete Listing | Soft-delete own listing                           | Deleted listing hidden from active listings    | Positive            | Listing has been soft-deleted                              | 1. Open listings page or send `GET /api/listings`                                                                           | Deleted listing is not shown in active listings                       | Pending / Not Run |
| TC-S2-DELETE-003 | Soft Delete Listing | Soft-delete own listing                           | Non-owner cannot delete listing                | Negative / Security | User is logged in but does not own listing                 | 1. Send `DELETE /api/listings/<listing_id>` for another seller’s listing                                                    | Delete is blocked with forbidden error                                | Pending / Not Run |
| TC-S2-DELETE-004 | Soft Delete Listing | Soft-delete own listing                           | Reject delete for missing listing              | Negative            | Listing does not exist                                     | 1. Send `DELETE /api/listings/<invalid_id>`                                                                                 | System returns appropriate not found error                            | Pending / Not Run |
| TC-S2-DETAIL-001 | Listing Details     | View listing details and seller contact           | View active listing detail page                | Positive            | Active listing exists                                      | 1. Open `/listing/<listing_id>` or send `GET /api/listings/<listing_id>`                                                    | Listing details are displayed                                         | Pass              |
| TC-S2-DETAIL-002 | Listing Details     | View listing details and seller contact           | Seller contact information is shown            | Positive            | Active listing exists with seller account                  | 1. Open listing detail page                                                                                                 | Seller Display Name, Email, and Contact Number are displayed          | Pass              |
| TC-S2-DETAIL-003 | Listing Details     | View listing details and seller contact           | Reject invalid listing ID                      | Negative            | Listing does not exist                                     | 1. Open invalid listing detail URL or send `GET /api/listings/<invalid_id>`                                                 | System shows not found or unavailable error                           | Pass              |
| TC-S2-DETAIL-004 | Listing Details     | View listing details and seller contact           | Hide deleted listing detail                    | Negative            | Listing has been soft-deleted                              | 1. Open detail page for deleted listing                                                                                     | System shows unavailable or not found message                         | Pass              |
| TC-S2-UI-001     | UI Listing Flow     | Create listing UI test                            | End-to-end listing creation flow               | Positive / UI       | Seller account exists and user can log in                  | 1. Login 2. Open Sell/Create Listing page 3. Enter valid listing details 4. Submit 5. View listing in active listings       | User can create listing through UI and see it in active listings      | Pass              |

---

## 8. Regression Testing

Before merging any Sprint 2 Merge Request, the following regression checks must pass:

| Regression Area            | Command / Method                                            | Expected Result                                                  |
| -------------------------- | ----------------------------------------------------------- | ---------------------------------------------------------------- |
| Full automated test suite  | `python -m pytest`                                          | All tests pass                                                   |
| Unit coverage              | `python -m pytest tests/unit --cov=app --cov-fail-under=60` | Coverage is at least 60%                                         |
| Linting                    | `python -m pylint app/ --fail-under=7.0`                    | Score is at least 7.0                                            |
| Complexity                 | `python -m radon cc app/ -s`                                | No function exceeds complexity 10                                |
| Manual create listing flow | Browser test                                                | Seller can create a valid listing                                |
| Manual browse listing flow | Browser test                                                | Buyer can browse active listings                                 |
| Manual edit listing flow   | Browser test                                                | Listing owner can edit their own listing                         |
| Manual listing detail flow | Browser test                                                | Buyer can view listing details and seller contact                |
| Manual Sprint 1 regression | Browser test                                                | Login, registration, profile view, and profile update still work |

---

## 9. Risks

| Risk                                             | Probability | Impact | Mitigation                                                   |
| ------------------------------------------------ | ----------- | ------ | ------------------------------------------------------------ |
| Invalid price is accepted                        | Medium      | High   | Add positive and negative price validation tests             |
| Logged-out user creates listing                  | Medium      | High   | Add authentication guard and negative API test               |
| Non-owner edits listing                          | Medium      | High   | Add owner-only validation and negative API test              |
| Soft-deleted listing still appears               | Medium      | High   | Add status filter and regression test                        |
| Search does not check both Title and Description | Medium      | Medium | Add separate tests for title and description search          |
| Filter results are inaccurate                    | Medium      | Medium | Add Category, Condition, and combined filter tests           |
| Pagination displays wrong number of listings     | Medium      | Medium | Add tests with more than 10 listings                         |
| Last modified timestamp does not update          | Medium      | Medium | Add update timestamp test                                    |
| Listing detail exposes wrong seller info         | Low         | High   | Add seller contact verification test                         |
| Test data affects real database                  | Medium      | Medium | Use isolated test database fixtures                          |
| Pipeline fails due to missing dependency         | Medium      | Medium | Ensure dependencies are listed in `requirements.txt`         |
| Merge conflict breaks listing route              | Medium      | Medium | Pull latest develop before merging and rerun full test suite |

---

## 10. Related Links

* [Sprint board](/-/boards)
* [CI/CD pipelines](/-/pipelines)
* [Merge requests](/-/merge_requests)
* [Test cases](/-/quality/test_cases)
* [Unit tests](tests/unit/)
* [API tests](tests/api/)
* [UI tests](tests/ui/)
* [AI Usage Logs](AI/)

---

## 11. Sprint 2 Definition of Done

### Verification

* [ ] Code passes pylint with score >= 7.0.
* [ ] Cyclomatic complexity per function does not exceed 10.
* [ ] All unit tests pass.
* [ ] All API / route tests pass.
* [ ] UI listing creation flow test passes.
* [ ] Test coverage is at least 60%.
* [ ] Pipeline is green on the Merge Request.
* [ ] No new SAST or secret detection issues are introduced.

### Validation

* [ ] Acceptance Criteria are confirmed with Product Owner / Tutor.
* [ ] All Sprint 2 test cases are updated to Passing status.
* [ ] At least one teammate has reviewed and approved the Merge Request.
* [ ] Related issue is moved to Done only after the MR is merged.

---

## 12. AI Prompt and Refinement Evidence

### AI Prompt Used

"Generate a Sprint 2 test plan for SwapLah Assignment 1. Sprint 2 focuses on Item Listing Management, including create listing, view active listings with pagination, search listings, filter listings by Category and Condition, clear filters individually, edit own listing, soft-delete own listing, and view listing details with seller contact information. Follow the required test plan format with Introduction, Scope, Test Approach, Test Items, Test Environment, Entry and Exit Criteria, Risks, Regression Testing, Definition of Done, and at least 10 positive and negative test cases with Test ID, description, preconditions, steps, and expected results."

### Refinement Made

The AI-generated test plan was reviewed and refined to match the actual Sprint 2 GitLab Epic and user stories under Item Listing Management. The test cases were adjusted to match the team’s acceptance criteria for create listing, active listing pagination, search, filter, clear filter, edit listing, soft delete, and listing detail view. Completed Sprint 2 items were marked as Pass, while user stories that were still open or not fully implemented were marked as Pending / Not Run to avoid overstating the project progress. The test plan also includes regression testing to ensure Sprint 1 account management features continue to work after Sprint 2 listing changes.
