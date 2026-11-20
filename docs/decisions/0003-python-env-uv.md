# 0003 - Python environment: uv with a pinned Python 3.12

- Status: accepted
- Date: 2026-11-20

## Context
The development machine runs Ubuntu 26.04 on WSL2 with system Python 3.14.
`python3 -m venv` failed because `python3.14-venv` could not be installed: apt reported
unmet dependencies (`python3-pip-whl`, `python3-setuptools-whl`), and the problem
remained after `apt full-upgrade` and enabling the `universe` repository.

## Options considered
| Option | For | Against |
|---|---|---|
| Keep fixing apt packages | Uses the system Python | Already failed twice; ties the project to OS packaging |
| pyenv | Common, pins Python versions | Compiles Python from source; slower, needs build tools |
| **uv** | Installs its own Python, creates venvs and installs packages very fast, independent of apt | One extra tool to install |

## Decision
Use uv to create `.venv` with Python 3.12 (`uv venv --python 3.12 .venv`) and install the
project with `uv pip install -e ".[dev]"`. `make venv` runs these commands.

## Consequences
- The environment is reproducible on any machine, regardless of the OS Python.
- Python 3.12 is used instead of 3.14 because data libraries (for example PySpark)
  support new Python releases later; 3.12 is the safer choice for this stack.
- Anyone working on the repo needs uv installed (one command, documented in the README).
- Possible later improvement: commit a `uv.lock` file to pin exact package versions.
