## What `make` is

`make` is a command-line tool that runs shortcut commands defined in a file called `Makefile`. You give a long command a short name, called a **target**, then run it with `make <target>`.

It was originally built to compile C programs. Data engineering teams use it as a **project command menu**, so everyone runs the stack the same way.

## How a target works

```makefile
down: ## Stop ALL containers (data in volumes is kept)
	$(COMPOSE) --profile "*" down
```

| Part | Meaning |
|---|---|
| `down:` | The target name, so you type `make down` |
| `## ...` | A description that `make help` shows |
| Indented line | The real command that runs. It **must start with a TAB**, not spaces |
| `$(COMPOSE)` | A variable defined at the top of the file, so it's written only once |

## How it's used in this project

| You type | What actually runs |
|---|---|
| `make up-core` | `docker compose --profile core up -d`, then waits and shows status |
| `make down` | `docker compose --profile "*" down` |
| `make health` | 3 checks: catalog, S3, Postgres row counts |
| `make smoke` | `.venv/bin/python -m pytest tests/integration/test_core_stack.py -v` |
| `make help` | Lists every target with its description |

## Why teams use it
- **Less typing, fewer mistakes:** you can't forget `--profile "*"`.
- **The commands are documented:** a new teammate runs `make help` and sees how the project works.
- **Same commands everywhere:** your laptop, a teammate's laptop and CI.

## Gotchas you've already hit
- `No rule to make target 'stop'` means that target doesn't exist in the Makefile (T8 in `troubleshooting.md`).
- Indenting a command with spaces instead of a TAB gives a `missing separator` error.
- `make clean` runs `down -v`, which **deletes all volumes**, so only use it for a full reset.

## A short version for your journal

Use this as a starting point and reword it in your own words:

> **make:** a tool that runs named shortcuts from a `Makefile`. Each target (e.g. `up-core`, `down`, `health`) wraps a longer command. Command lines must be indented with a TAB. I use it so I never mistype Docker Compose commands, and `make help` documents the project's commands.

Your next step: add the reworded version under "Learned (in my own words)" in `docs/journal/2026-11-20.md`, then run `make help` and check each target it lists matches what you wrote.