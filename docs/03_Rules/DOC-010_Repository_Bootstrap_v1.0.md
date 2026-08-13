# DOC-010_Repository_Bootstrap_v1.0

## Status
Approved for initial repository bootstrap.

## Purpose
Define the physical repository structure and minimum engineering conventions for ORION.

## Repository principles
1. GitHub Private is the official remote repository.
2. The repository is the Single Source of Truth for approved code and documentation.
3. `main` contains stable, releasable states.
4. Development work must be traceable through commits and changelog entries.
5. No production code is accepted without tests appropriate to its risk.

## Directory standard
- `docs/` — official documentation.
- `src/` — application source code.
- `tests/` — automated tests.
- `config/` — non-secret configuration.
- `scripts/` — developer and operational scripts.
- `assets/` — static project assets.
- `data/` — controlled datasets and schemas; secrets are prohibited.
- `adr/` — architecture decisions.
- `releases/` — release manifests and packaged artifacts.
- `.github/` — GitHub automation and templates.

## Branching
- `main` — stable code.
- `develop` — integration branch.
- `feature/*` — isolated development.

## Versioning
Semantic Versioning: `MAJOR.MINOR.PATCH`.
Bootstrap release: `v0.1.0`.

## Commit convention
Use traceable prefixes such as `INIT`, `DOC`, `MOD`, `TEST`, `FIX`, and `REL`.

## Definition of Done
A change is complete when applicable code, tests, documentation and configuration are updated, tests pass, and the change is traceable in Git.

## Security
Secrets, credentials, API keys and personal data must not be committed. Use environment variables or secret management.

## Initial release
`v0.1.0` — Repository Bootstrap.
