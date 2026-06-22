# Agentic CI/CD Demo for FastAPI

The application itself is intentionally small: a FastAPI service for **meeting
room reservations** backed by in-memory storage. The value of the repository is
the delivery workflow around it:

- executable business contracts in Gherkin
- local BDD and post-deploy functional testing
- agent-assisted delivery across planning, implementation, and testing
- preview environments with GitHub Codespaces
- layered security checks for **SAST, SCA, and DAST**

## Why this repo works well for a demo

The domain is simple enough to understand in minutes, but rich enough to show
real delivery controls:

- overlap prevention
- capacity validation
- time-window validation
- future-only cancellation
- contract-driven testing

That keeps the audience focused on the **pipeline**, not the business domain.

## What the application does

The API supports:

- listing available rooms and capacities
- creating reservations
- listing reservations, optionally filtered by room
- retrieving a reservation by ID
- cancelling a future reservation

Business rules currently implemented:

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
│   └── reserva.feature
├── step_defs/
│   └── test_reserva_steps.py
└── functional/
    ├── conftest.py
    └── test_reserva_functional.py

.devcontainer/
└── devcontainer.json

.github/
├── ISSUE_TEMPLATE/
├── instructions/
├── workflows/
└── dependabot.yml
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

## Test strategy

This repository includes three complementary validation layers:

| Layer | Location | Purpose |
|---|---|---|
| Business contract | `tests/features/reserva.feature` | Defines expected behavior in Spanish Gherkin |
| Local BDD | `tests/step_defs/` | Verifies the application against the approved contract |
| Post-deploy functional | `tests/functional/` | Exercises the deployed API over HTTP |

The contract already covers:

- successful reservation creation and lookup
- successful cancellation of a future reservation
- invalid time windows
- capacity violations
- schedule overlaps
- invalid purpose length
- empty result sets
- unknown room rejection

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

Run local quality checks:

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

## Delivery pipeline

### Core CI

`ci.yml` validates pull requests with:

- scope enforcement for `[IMPL]` pull requests
- Ruff linting and formatting checks
- Bandit security scanning
- pytest-based contract validation
- merge gate aggregation

### Preview environments

`preview.yml` creates a short-lived GitHub Codespace on pushes to `main`,
waits for the FastAPI app to come up on port `8000`, publishes the preview URL,
and then triggers downstream post-deploy validation.

### Security controls

This demo includes a layered security story that is easy to explain live:

| Control | Workflow | Purpose |
|---|---|---|
| SAST | `sast.yml` | CodeQL static analysis for Python |
| SCA | `sca.yml` | Dependency Review on pull requests and scheduled `pip-audit` |
| DAST | `dast.yml` | OWASP ZAP baseline scan against the preview deployment |
| Fast feedback | `ci.yml` | Bandit in PR CI for quick Python-focused checks |

For a public repository, this is a practical setup: GitHub-native controls for
static analysis and dependency review, plus ZAP for a realistic DAST step.

## Agentic workflow

The repository also includes a three-phase agentic delivery flow:

| Phase | Workflow | Outcome |
|---|---|---|
| Planning | `agentic-plan.yml` | Generates a draft `[ATDD]` pull request with Gherkin scenarios |
| Implementation | `agentic-develop.yml` | Creates and assigns an `[IMPL]` issue |
| Functional testing | `agentic-test.yml` | Creates and assigns a `[TEST]` issue |
| Ready for review | `agentic-ready-for-review.yml` | Moves draft PRs to ready when Copilot finishes a change batch |
| Self-correction | `agentic-self-correct.yml` | Requests follow-up fixes when Copilot review suggestions exist |

This makes the repository useful both as:

1. a working FastAPI demo
2. a classroom example of an agent-governed CI/CD process

## Required GitHub configuration

If you want to use the full workflow in a live demo, configure the following.

### Labels

- `agentic-mission`
- `agentic-implementation`
- `agentic-testing`
- `needs-human-review`

### Secrets

| Secret | Purpose |
|---|---|
| `COPILOT_USER_ACCESS_TOKEN` | Assign Copilot to issues and mutate PR state where required |
| `CODESPACE_PAT` | Create and manage preview Codespaces |

### Recommended branch protection

Protect `main` with:

- pull requests required
- at least one human approval
- required status checks
- direct pushes blocked

Recommended required checks:

- `Scope Check`
- `Lint & Format`
- `Security Scan`
- `Contratos BDD`
- `CodeQL Analysis (Python)`
- `Dependency Review`

If you also want to gate deployments, add the DAST workflow as a required check
for the promotion path you use in class.

## Suggested workshop flow

1. Open the issue template in `.github/ISSUE_TEMPLATE/agentic-mission.yml`.
2. Create a business request with explicit scope and business rules.
3. Apply the `agentic-mission` label.
4. Review the generated `[ATDD]` pull request.
5. Merge the approved scenarios.
6. Let the repository create `[IMPL]` and `[TEST]` follow-up work.
7. Show CI, security checks, preview creation, functional tests, and DAST.

## Design constraints

This demo is intentionally constrained:

- no database
- no authentication or authorization
- no recurring reservations
- no partial updates
- no notifications

Those trade-offs keep the implementation compact and make the pipeline easier to
demonstrate in a classroom setting.
