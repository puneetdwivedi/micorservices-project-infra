# Copilot Instructions

## Project Context

This repository defines AWS infrastructure automation for a microservices project. The current target environment is `sandbox`.

Keep changes modular, focused, and consistent with the existing Python and AWS abstractions. Prefer small reusable service classes over putting AWS operations directly in scripts.

## AWS Naming Standard

All AWS resource names must follow this format:

```text
<pdw>-<service>-<reason>-<number>
```

Examples:

- `pdw-subnet-private-1`
- `pdw-subnet-private-2`
- `pdw-stack-infra`
- `pdw-ec2-vdp-1`

Naming rules:

- Use lowercase kebab-case.
- Start every resource name with `pdw`.
- Use a clear service or resource category.
- Use a short reason or purpose.
- Add a number when multiple resources of the same type exist.
- Keep names deterministic and stable across deployments.
- Use the environment in the name when resources from multiple environments can share an AWS account or region. Follow the project convention, for example `pdw-subnet-sandbox-private-1`, when the environment is needed to avoid ambiguity.
- Do not invent inconsistent abbreviations. Use the existing project vocabulary where one exists.

CloudFormation logical IDs may use PascalCase, but their deployed resource names must follow the AWS naming standard whenever AWS permits explicit names.

## Logging Standard

Use Python's `logging` module for operational output. Do not add new `print()` calls for debugging, AWS operations, deployment progress, or errors.

The log level must be configurable from the environment using `LOG_LEVEL`. Supported values are:

- `DEBUG`
- `INFO`
- `WARNING`
- `ERROR`
- `SUCCESS`

Default to `INFO` when `LOG_LEVEL` is missing or invalid. Configure logging once at the application entry point and use module-level loggers in other modules:

```python
import logging

logger = logging.getLogger(__name__)
logger.info("Starting deployment")
```

Logging guidance:

- `DEBUG`: detailed internal state useful during troubleshooting; do not log secrets.
- `INFO`: normal lifecycle events such as starting a build or syncing an artifact.
- `WARNING`: recoverable problems or fallback behavior.
- `ERROR`: an operation failed and needs attention; include useful context and exceptions.
- `SUCCESS`: successful completion messages. Because `SUCCESS` is not a standard Python logging level, represent it with a project logging helper or a documented custom level; do not silently redefine standard levels in individual modules.
- Use lazy logging formatting, for example `logger.info("Syncing %s", object_key)`.
- Never log AWS access keys, secret keys, session tokens, passwords, or other sensitive values.
- Include resource names, object keys, and operation context in messages where useful.
- Raise exceptions when a build or deployment cannot complete; logging an error must not replace correct error handling.

## Python Package Imports

- When a directory is a Python package, expose its public modules or symbols through that package's `__init__.py`.
- Consumers should import public functionality from the package, for example `from utils.services import S3Manager`, instead of importing directly from `utils.services.s3_manager`.
- Define an explicit `__all__` in each package `__init__.py` containing the names that package consumers are allowed to import.
- Keep `__all__` synchronized with the imports in `__init__.py`; do not leave stale or unrelated names in it.

Example:

```python
# utils/services/__init__.py
from .s3_manager import S3Manager

__all__ = ["S3Manager"]
```

## Infrastructure Build And Deployment

- The configured artifact bucket is `PDW_S3_BUCKET_SANDBOX_PROJECT_PARTIALS` in `utils/constants.py`.
- Artifact object keys must be rooted under `PROJECT_NAME_PREFIX`.
- Stack and template directories are synchronized to S3 with their relative paths preserved.
- Lambda source directories under `infra/lambdas` must be packaged as ZIP archives before synchronization.
- Keep S3 access behind `utils.services.s3_manager.S3Manager`.
- Keep CloudFormation access behind the abstractions in `utils.services.cft`.
- Do not hard-code credentials. Read environment configuration through the existing constants and `.env` loading approach.
- Make AWS clients injectable where practical so build and deployment logic can be tested without AWS access.

## Project Structure

```text
.
├── backend/
│   ├── auth/                 # Auth service container and source
│   ├── product/              # Product service container and source
│   └── docker-compose.yml
├── infra/
│   ├── lambdas/              # Lambda source directories; each becomes a ZIP
│   ├── stacks/               # Root CloudFormation stacks
│   └── templates/            # Reusable CloudFormation templates
├── scripts/
│   ├── build.py              # Build and synchronize infrastructure artifacts
│   ├── deploy.py             # Deployment orchestration
│   └── destroy.py             # Infrastructure teardown orchestration
├── src/
│   └── main.py               # Application entry point
├── utils/
│   ├── constants.py          # Environment values and project constants
│   └── services/
│       ├── cft.py            # CloudFormation service abstractions
│       └── s3_manager.py     # S3 bucket and synchronization operations
├── plan.md                   # Project architecture and implementation plan
├── pyproject.toml            # Python project metadata and dependencies
└── readme.MD                 # Project overview
```

When adding files, update this structure section if the new directory or module is part of the supported architecture.

## Change Guidelines

- Read nearby code before editing and preserve existing public APIs unless a change requires otherwise.
- Prefer standard library and existing dependencies before introducing new packages.
- Follow PEP 8 style and use Ruff for linting, import sorting, and formatting.
- Run `uv run ruff check .` and `uv run ruff format --check .` before completing Python changes.
- Use descriptive names, small focused functions, and type annotations for public APIs.
- Avoid mutable default arguments, broad exception handling, duplicated logic, and unnecessary global state.
- Keep functions deterministic where practical and inject external clients so AWS behavior can be tested with Moto.
- Write focused tests for new behavior, including success and failure paths for infrastructure operations.
- Validate Python changes with compilation, diagnostics, and focused tests or smoke tests.
- Keep generated artifacts, credentials, and `.env` files out of version control.
