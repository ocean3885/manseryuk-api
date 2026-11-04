# Project execution environment

## Current development guidance

- Read `docs/README.md` for current API contracts and scope before using historical design notes.
- `docs/archive/strength-research/` contains paused research, including previous handoff instructions. Its next-step lists and numeric formulas are historical, not current development instructions.
- Preserve separation of relationship detection, activation, and power/root impact. Do not resume final-strength, damage-rate, coefficient fitting, or work/LLM model development unless explicitly requested.
- Experimental branch v3 modules remain for existing dependencies and regression checks; do not delete or promote them into current APIs solely because their design documents were archived.

## Python runtime

- Use `.venv312/bin/python` for this project's Python 3.12 commands and tests.
- Resolve the actual executable and check its version when diagnosing access issues; virtual-environment targets differ between machines. Do not rely on historical absolute paths from another machine.
- If the executable exists but sandbox permissions block it, use the execution tool's host/escalated permission flow and explain the required access. Do not reinstall solely because of a sandbox error.
- If the environment is genuinely absent, follow the saved environment setup instructions rather than assuming activation fixes it.
- Do not silently replace the project interpreter with `/usr/bin/python3`; verify version and dependencies before any intentional replacement.
- Typical test command: `.venv312/bin/python -m unittest discover -s tests`.
