# Project execution environment

- Use `.venv312/bin/python` for this project's Python 3.12 commands and tests. The virtual environment exists; its `python` executable is a symlink to `/home/ocean3885/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu/bin/python3.12`.
- In the managed sandbox, the symlink may be visible while its target is inaccessible. This can make `.venv312/bin/python` fail with `No such file or directory`, and `test -e .venv312/bin/python` may return false. These results alone do **not** mean Python 3.12 or the virtual environment was deleted.
- If a project command fails for this reason, rerun the required command using the execution tool's host/escalated permission flow and state why access is needed. Do not reinstall Python or recreate the virtual environment solely because of this sandbox error. Do not assume that activating the virtual environment changes filesystem permissions.
- `/usr/bin/python3` is a separate interpreter and should not silently replace `.venv312/bin/python` for project validation. Check its version and dependencies first if it is intentionally used.
- Typical test command: `.venv312/bin/python -m unittest discover -s tests`.
