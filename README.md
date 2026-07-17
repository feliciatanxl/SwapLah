# SwapLah

SwapLah is a Flask and SQLite web application for NYP students to register, log in, manage profiles, create item listings, browse active listings, and submit offers. This repository is structured for the IT2112 Agile DevOps assignment with pytest, Selenium, Postman/Newman, Pylint, Radon, GitLab CI, SBOM generation, and security gates.

## Python Version

Use Python 3.11 for GitLab CI parity. The local repository has also been verified with the bundled virtual environment on Python 3.14.

## Local Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

Install runtime dependencies:

```powershell
python -m pip install -r requirements.txt
```

Install development dependencies:

```powershell
python -m pip install -r requirements-dev.txt
```

## Environment Variables

`SECRET_KEY` is required. The app does not use a hardcoded fallback.

Safe local setup:

1. Copy `.env.example` to `.env`.
2. Set `SECRET_KEY` to a long random local value.
3. Do not commit `.env`; it is ignored by `.gitignore`.

GitLab CI sets a test-only `SECRET_KEY` for automated checks. Production or deployment environments must provide their own secret through protected CI/CD variables or hosting configuration.

Manual GitLab setup for CI:

1. Go to `GitLab -> Settings -> CI/CD -> Variables`.
2. Add a variable with key `SECRET_KEY`.
3. Enter a non-empty test/deployment value in GitLab only; do not paste the value into repository files or documentation.
4. Set the visibility/protection options according to the branch and merge-request pipeline policy used by the project.
5. Save the variable before running feature-branch or merge-request pipelines.

Pytest receives its test-only key from `tests/conftest.py`. Newman and the Flask server used by the `newman-api-tests` job receive `SECRET_KEY` from the GitLab CI/CD variable environment.

## Database

The SQLite database file is `swaplah.db` for local development. Tables are created automatically by `init_db()` when the Flask app starts. Local database files are ignored by Git.

## Run The App

```powershell
$env:SECRET_KEY = "replace-with-a-long-local-secret"
python run.py
```

The app starts with Flask's development server.

## Test Commands

Run the complete pytest suite:

```powershell
python -m pytest
```

Run unit tests:

```powershell
python -m pytest tests/unit
```

Run API tests:

```powershell
python -m pytest tests/api
```

Run Flask UI tests:

```powershell
python -m pytest tests/ui/flask
```

Run Selenium tests when Chrome or Chromium and a compatible driver are available:

```powershell
python -m pytest tests/ui/selenium
```

Run coverage:

```powershell
python -m pytest tests/unit --cov=app --cov-report=term-missing
```

Run Pylint:

```powershell
python -m pylint app tests scripts
```

Run Radon:

```powershell
python -m radon cc app -s
```

Run the function-length and complexity gate:

```powershell
python scripts/code_quality_gate.py
```

The gate fails if an application function exceeds 40 physical source lines or cyclomatic complexity 10.

## Newman

Postman assets:

- Collection: `postman/swaplah-api-tests.postman_collection.json`
- Environment: `postman/swaplah-ci.postman_environment.json`

Run locally only when Node.js and Newman are installed:

```powershell
newman run postman/swaplah-api-tests.postman_collection.json --environment postman/swaplah-ci.postman_environment.json
```

GitLab CI installs Newman in the `newman-api-tests` job.

## API Examples

Health:

```http
GET /api/health
```

Response:

```json
{"status": "ok"}
```

Listings:

```http
GET /api/listings?page=1&search=calculator&category=Electronics&condition=Good
GET /api/listings/1
POST /api/listings
PUT /api/listings/1
DELETE /api/listings/1
```

User reviews:

```http
GET /api/users/1/reviews
```

Response for an existing user with no reviews:

```json
{"reviews": []}
```

## Admin Authorization

`/admin` is protected server-side. Active admin users are allowed. Logged-in normal users and suspended users receive `403`. Unauthenticated users are redirected to login. Navigation visibility is not treated as authorization.

## GitLab Pipeline

Pipeline stages:

- `validate`: Pylint, Radon report, function-length and complexity gate.
- `test`: unit tests with coverage, API tests.
- `ui-test`: Flask UI and Selenium UI tests.
- `api-test`: Newman/Postman API tests.
- `security`: GitLab SAST, dependency scanning, secret detection, CycloneDX SBOM, security gate.
- `build`: reproducible source archive.
- `deploy`: publishes the verified build archive to GitLab Generic Package Registry.

## SBOM

Generate locally:

```powershell
python scripts/generate_sbom.py -r requirements.txt -r requirements-dev.txt -o swaplah-sbom.cdx.json
```

GitLab publishes `swaplah-sbom.cdx.json` as both an artifact and `artifacts:reports:cyclonedx`. Download it from the `cyclonedx-sbom` job artifacts.

## Security Gate

GitLab security templates are included for SAST, dependency scanning, and secret detection. The `security-gate` job inspects:

- `gl-sast-report.json`
- `gl-dependency-scanning-report.json`
- `gl-secret-detection-report.json`

The gate fails when:

- SAST contains a High or Critical vulnerability.
- Dependency scanning contains a High or Critical vulnerability.
- Secret detection contains any finding.
- An expected report is missing.

Approved exceptions should be handled manually through a documented merge request discussion and a narrow, reviewed GitLab scanner rule or project policy. Do not add broad automatic ignores.

## Build Artifact

Generate locally:

```powershell
python scripts/build_package.py -o dist/swaplah-build.zip
```

The archive includes application Python files, templates, static assets, Postman files, scripts, README, dependency files, and safe configuration examples. It excludes `.git`, virtual environments, caches, local databases, `.env`, SBOM output, reports, and temporary files. GitLab publishes the archive from the `build-archive` job.

## Deployment

The `deploy-package` job publishes `dist/swaplah-build.zip` from the `build-archive` job to GitLab Generic Package Registry. The package name is `swaplah`, the package version is the commit short SHA, and the uploaded filename remains `swaplah-build.zip`.

The upload URL is built from GitLab predefined CI variables:

```text
${CI_API_V4_URL}/projects/${CI_PROJECT_ID}/packages/generic/swaplah/${CI_COMMIT_SHORT_SHA}/swaplah-build.zip
```

Default-branch pipelines deploy automatically after the required earlier stages and `build-archive` pass. Merge request and feature-branch pipelines show `deploy-package` as a manual job, and the pipeline is not blocked when that manual job is not started. Tag pipelines do not deploy because this project does not define a tag-release process.

The deploy job authenticates with `CI_JOB_TOKEN` using the `JOB-TOKEN` request header. No real secret, password, token, project ID, or project URL is stored in the repository.

Find the package in GitLab at:

```text
GitLab -> Deploy -> Package Registry
```

This deployment does not provide a live hosted Flask URL. Live hosting would require a real hosting target such as a VM, container platform, or cloud service, plus its deployment configuration and required CI/CD variables.
