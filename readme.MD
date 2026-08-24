# Microservices Project Infrastructure

AWS infrastructure automation and containerized backend services for a microservices project.

The repository currently targets the `sandbox` environment and contains:

- `backend/`: Node.js services for authentication and products
- `infra/`: CloudFormation stacks, reusable templates, and Lambda source code
- `scripts/`, `src/`, and `utils/`: Python infrastructure automation
- `tests/`: pytest tests, including Moto-backed AWS tests

## Prerequisites

- Python 3.11 or newer
- [uv](https://docs.astral.sh/uv/)
- Docker and Docker Compose
- Node.js and npm, if running a backend service outside Docker
- AWS credentials with permission to manage the configured resources

## Project Setup

From the repository root:

```powershell
uv sync --dev
```

Create a local `.env` file when environment variables are needed:

```text
AWS_ACCESS_KEY=your-access-key
AWS_SECRET_KEY=your-secret-key
AWS_DEFAULT_REGION=ap-south-1
LOG_LEVEL=INFO
```

Do not commit `.env` or credentials. The project loads `.env` through `python-dotenv`.

## Backend Services

The backend contains two Node.js services:

- `authservice`: listens on port `3001`
- `productservice`: listens on port `3002` and calls auth at `http://authservice:3001`

### Run With Docker Compose

Start both services from the repository root:

```powershell
docker compose -f backend/docker-compose.yml up --build
```

Stop them with:

```powershell
docker compose -f backend/docker-compose.yml down
```

Local endpoints:

- Auth: `http://localhost:3001`
- Product: `http://localhost:3002`

Inside Docker, use the Compose service name `authservice` rather than `localhost` for service-to-service requests.

### Run A Service Directly

```powershell
Push-Location backend/auth
npm install
npm start
Pop-Location
```

For the product service:

```powershell
Push-Location backend/product
npm install
npm start
Pop-Location
```

Backend service test scripts are not implemented yet.

## Infrastructure Automation

### Build And Synchronize Artifacts

Run the build through the configured project command:

```powershell
uv run build
```

`uv run main` is an equivalent entry point:

```powershell
uv run main
```

The build:

1. Creates the configured S3 bucket if it does not already exist.
2. Synchronizes files from `infra/stacks`.
3. Synchronizes files from `infra/templates`.
4. Packages each non-empty directory under `infra/lambdas` as a ZIP archive.
5. Synchronizes Lambda archives to S3.

All S3 keys are rooted under `PROJECT_NAME_PREFIX` from `utils/constants.py`:

```text
microservices-project-infra/stacks/<file>
microservices-project-infra/templates/<file>
microservices-project-infra/lambdas/<lambda-name>.zip
```

The sandbox artifact bucket is `pdw-s3-bucket-sandbox-project-partials`.

S3 access is kept behind `S3Manager`, and the builder supports dependency injection for tests.

### Deployment

The deployment command is available:

```powershell
uv run deploy
```

Deployment orchestration is currently a placeholder. CloudFormation operations are implemented behind `CloudFormationClient` and `CloudFormationStack` in `utils/services/cft.py`.

### Planned AWS Components

The project plan includes:

- VPC, public/private subnets, route tables, and network routing
- ECR repositories for backend container images
- ECS cluster with auth and product services
- ECS Service Connect and ECS Exec
- CloudWatch log groups for each service
- Application Load Balancer routing `/auth` and `/product`

These components should be implemented incrementally through CloudFormation templates and stacks.

## Logging

Configure logging with `LOG_LEVEL`:

```powershell
$env:LOG_LEVEL = "DEBUG"
uv run build
Remove-Item Env:LOG_LEVEL
```

Supported levels are `DEBUG`, `INFO`, `WARNING`, `ERROR`, and `SUCCESS`. Invalid or missing values default to `INFO`.

Logging is configured once at the application entry point. Other modules use module-level loggers and lazy formatting:

```python
import logging

logger = logging.getLogger(__name__)
logger.info("Syncing %s", object_key)
```

Interactive terminal output includes level-specific colors and symbols. Never log credentials, tokens, passwords, or other secrets.

## Testing

Run the complete test suite:

```powershell
uv run pytest
```

The pytest configuration provides test discovery, verbose per-test output, parallel execution with `pytest-xdist`, terminal coverage, HTML coverage in `htmlcov/`, XML coverage in `coverage.xml`, and strict pytest settings.

AWS tests use Moto fixtures from `tests/conftest.py`, so they do not require AWS access.

## Code Quality

Run Ruff linting and formatting checks:

```powershell
uv run ruff check .
uv run ruff format --check .
```

Apply formatting when needed:

```powershell
uv run ruff format .
```

Before submitting Python changes, run Ruff and pytest. Keep functions focused, use descriptive names and type annotations for public APIs, avoid mutable default arguments, and inject external clients so AWS behavior remains testable.

## Package Imports

Public modules and classes are exported through package `__init__.py` files. Consumers should use package-level imports:

```python
from scripts import Build
from utils.services import S3Manager
```

Keep `__all__` synchronized with the public imports in each package initializer:

```python
from .s3_manager import S3Manager

__all__ = ["S3Manager"]
```

## AWS Naming Standard

AWS resource names must use lowercase kebab-case and follow:

```text
<pdw>-<service>-<reason>-<number>
```

Examples:

```text
pdw-subnet-private-1
pdw-subnet-private-2
pdw-stack-infra
pdw-ec2-vdp-1
```

Use deterministic names and include the environment when resources from multiple environments share an account or region, for example `pdw-subnet-sandbox-private-1`.

## Project Structure

```text
.
├── backend/
│   ├── auth/                 # Auth Node.js service and Dockerfile
│   ├── product/              # Product Node.js service and Dockerfile
│   └── docker-compose.yml    # Local service orchestration
├── infra/
│   ├── lambdas/              # Lambda source directories, packaged as ZIP files
│   ├── stacks/               # Root CloudFormation stacks
│   └── templates/            # Reusable CloudFormation templates
├── scripts/
│   ├── build.py              # Build and synchronize infrastructure artifacts
│   ├── deploy.py             # Deployment command entry point
│   └── destroy.py            # Destruction command entry point
├── src/
│   └── main.py               # Application and build entry point
├── tests/
│   ├── conftest.py           # Shared pytest and Moto fixtures
│   ├── test_build.py         # S3 and Lambda packaging tests
│   └── test_logging_config.py
├── utils/
│   ├── constants.py          # Environment values and project constants
│   ├── logging_config.py     # Shared logging configuration
│   └── services/
│       ├── cft.py            # CloudFormation service classes
│       └── s3_manager.py     # S3 bucket and synchronization operations
├── plan.md                   # Architecture and implementation notes
├── pyproject.toml            # Project metadata, commands, and dependencies
├── pytest.ini                # Pytest, xdist, and coverage configuration
└── README.md
```

Related documentation is available in [plan.md](plan.md) and [.github/copilot-instructions.md](.github/copilot-instructions.md).
