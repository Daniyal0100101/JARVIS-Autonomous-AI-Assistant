# Repository Guidelines

## Project Structure & Module Organization
`main.py` is the CLI entry point and wires together authentication, mode switching, and the Rich-based terminal UI. Core assistant behavior lives in `modules/`, with focused files such as `text_to_speech.py`, `speech_recognition.py`, `system_control.py`, `apps_automation.py`, and `utils.py` for shared helpers plus the tool-execution pipeline. Dependency inputs live in both `requirements.txt` and `Requirements/requirements.txt`; the installer prefers the latter. Local secrets stay in `.env`, while user-created files like `modules/password.py` and `modules/contacts.py` must remain untracked.

## Build, Test, and Development Commands
Create and activate a virtual environment before installing packages.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python install_requirements.py
python main.py
python -m py_compile main.py modules\*.py
```

`python install_requirements.py` installs dependencies with retry logic and platform-specific guidance. `python main.py` launches Jarvis locally. `python -m py_compile ...` is the safest repo-wide smoke check currently available.

## Coding Style & Naming Conventions
Follow PEP 8 with 4-space indentation, descriptive snake_case for functions and modules, and UPPER_CASE for constants like slash-command maps. Keep functions narrowly scoped, prefer short docstrings on public helpers, and preserve the existing pattern of isolating system, speech, and automation concerns into separate module files. The repo does not currently enforce Black, Ruff, or mypy, so keep formatting clean and consistent by hand.

## Testing Guidelines
There is no dedicated `tests/` directory yet. For changes, add focused tests when you introduce logic that can be exercised outside device APIs; otherwise, run targeted smoke checks such as `python -m py_compile main.py modules\*.py` and a manual `python main.py` startup check. Name future test files `test_<module>.py`.

## Commit & Pull Request Guidelines
Recent history favors short, imperative subjects such as `Fix cross-platform arrow key detection...` and `fix: critical cross-platform and thread safety issues`. Use a concise verb-first summary, keep unrelated fixes out of the same commit, and mention the affected subsystem when useful. PRs should explain the user-visible change, note any platform-specific impact (Windows/macOS/Linux), link the issue if one exists, and include terminal screenshots only when UI output changed.

## Security & Configuration Tips
Do not commit `.env`, generated passwords, contact lists, or API keys. When documenting setup, point contributors to `.env.example` and note that audio, camera, and OS automation features may require local permissions or native packages.
