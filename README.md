# FastAPI CI/CD Security Reference

This repository contains a small FastAPI service for meeting room reservations
and a focused GitHub Actions setup for quality and security validation.

The application is intentionally compact, but the delivery pipeline is layered:

- an orchestrated pull request validation pipeline
- SAST with CodeQL
- SCA with Dependency Review and `pip-audit`
- post-deploy functional testing
- DAST with OWASP ZAP against a preview environment

## Application overview

The API supports:

- listing available rooms and capacities
- creating reservations
- listing reservations, optionally filtered by room
- retrieving a reservation by ID
- cancelling a future reservation

Implemented business rules:

- fixed room catalog: `A`, `B`, `C`
- capacities: `4`, `8`, and `20`
- no overlapping bookings for the same room and date
- working hours restricted to `08:00`-`20:00`
- minimum duration of `15` minutes
- maximum duration of `4` hours
- room capacity enforcement
- reservation purpose must be at least `10` characters
- only future reservations can be cancelled

## Technology stack

- Python 3.11+
- FastAPI
- Pydantic v2
- pytest
- pytest-bdd
- httpx
- Ruff
- Bandit
- GitHub Actions
- GitHub CodeQL
- Dependabot / Dependency Review
- OWASP ZAP

## Repository structure

```text
src/
├── main.py
├── models.py
└── services.py

tests/
├── conftest.py
├── features/
├── step_defs/
└── functional/

.devcontainer/
└── devcontainer.json

.github/
├── dependabot.yml
└── workflows/
```

## API surface

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/api/v1/salas` | List rooms and capacities |
| `POST` | `/api/v1/reservas` | Create a reservation |
| `GET` | `/api/v1/reservas` | List reservations, optionally filtered by `sala` |
| `GET` | `/api/v1/reservas/{reserva_id}` | Retrieve a reservation by ID |
| `DELETE` | `/api/v1/reservas/{reserva_id}` | Cancel a future reservation |
| `POST` | `/api/v1/_reset` | Reset in-memory state for testing |

## Local development

Install dependencies:

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

Run the API:

```bash
python -m uvicorn src.main:app --reload
```

Open Swagger UI:

```text
http://127.0.0.1:8000/docs
```

Run local checks:

```bash
ruff check src/ tests/
ruff format --check src/ tests/
bandit -r src/
pytest tests/ -v --tb=short --strict-markers
```

Run functional tests against a deployed environment:

```bash
pytest tests/functional/ -v --tb=short --base-url="https://your-api.example"
```

## CI/CD workflows

### Pull request orchestration

`pr-validation.yml` is the entry point for pull requests. It orchestrates:

- `ci.yml`
- `sast.yml`
- `dependency-review.yml`
- `preview.yml` after the blocking checks succeed

The preview workflow then runs functional tests and DAST against the pull
request branch.

### CI

`ci.yml` is reusable and provides:

- Ruff linting
- format validation
- `Bandit Scan`
- pytest execution
- a final merge gate

### SAST

`sast.yml` is reusable for pull requests and also runs on pushes to `main` and
on a schedule.

### SCA

The SCA layer is split into two workflows:

- `dependency-review.yml` for pull request dependency changes
- `sca.yml` for scheduled and manual `pip-audit` runs
- Dependabot support through `.github/dependabot.yml`

> `Dependency Review` requires **Dependency graph** to be enabled in the
> repository security settings.

### Preview and post-deploy validation

`preview.yml` creates a short-lived GitHub Codespace on pushes to `main`,
and can also be called from the pull request pipeline. It publishes the preview
URL and triggers:

- `functional-tests.yml`
- `dast.yml`

### DAST

`dast.yml` runs an OWASP ZAP baseline scan against the deployed preview URL.

Policy:

- **High** findings fail the check
- **Medium**, **Low**, and **Informational** findings are reported in the
  workflow summary and artifact, but do not fail the check

## Required repository configuration

### Secrets

| Secret | Purpose |
|---|---|
| `CODESPACE_PAT` | Create, manage, and expose preview Codespaces |

### Repository settings

Enable the following in GitHub:

- **Actions**
- **Codespaces**
- **Dependency graph**
- **Code scanning / CodeQL**

If you are using `sast.yml`, disable GitHub's default CodeQL setup to avoid
duplicated code scanning runs.

Recommended branch protection for `main`:

- pull requests required
- required status checks
- direct pushes blocked

Suggested required checks:

- `CI / Merge Gate`
- `CI / Bandit Scan`
- `SAST / CodeQL Analysis (Python)`
- `SCA / Dependency Review`
- `Preview, Functional Tests, and DAST / Start Preview API`
- `Preview, Functional Tests, and DAST / Functional Tests / Functional Tests Against Preview`
- `Preview, Functional Tests, and DAST / DAST Scan / ZAP Baseline Scan`

## Design constraints

The implementation is intentionally constrained:

- no database
- no authentication or authorization
- no recurring reservations
- no partial updates
- no notifications

Those trade-offs keep the codebase compact while still allowing meaningful CI,
SAST, SCA, and DAST validation.

Test
