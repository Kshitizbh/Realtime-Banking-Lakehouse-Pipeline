# Troubleshooting log

Errors **I actually hit**, newest at the bottom. (`runbook.md` lists problems we *expect*; this file records what *really* happened.)
Format: symptom → cause → fix → lesson. Paste exact error messages, but remove passwords and keys first.

---

### T1. Laptop crashed on my first attempt at this project
- **When:** before 2026-11-19 (previous attempt)
- **Symptom:** the whole laptop froze or crashed while Docker was running.
- **Cause:** WSL2 had no memory cap, every heavy service was running at once, and the setups were heavyweight (Spark master + workers, multi-container Airflow, etc.).
- **Fix:** cap WSL in `.wslconfig`, set a memory limit on every compose service, use lightweight modes (Spark local, Airflow standalone, Redpanda), and start only the profiles a milestone needs.
- **Lesson:** design the local stack around the laptop's limits from day one.

### T2. `.wslconfig` was ignored
- **When:** 2026-11-20
- **Symptom:** `nproc` still showed 32 (expected 12); swap still 4.0Gi.
- **Cause:** Notepad saved the file as `.wslconfig.txt`. File Explorer hides known extensions, so the name looked correct; its type said "Text Document".
- **Fix:** delete the `.txt` file and write the real one from PowerShell with `Set-Content -Path "$env:USERPROFILE\.wslconfig" -Encoding ascii`. Quit Docker Desktop, run `wsl --shutdown`, and reopen Ubuntu.
- **Lesson:** turn on File Explorer → View → Show → File name extensions. Check config changes took effect (`nproc`, `free -h`); don't assume they did.

### T3. VS Code pop-up about `\\wsl.localhost`
- **When:** 2026-11-20
- **Symptom:** security pop-up when VS Code opened the Ubuntu folder.
- **Cause:** VS Code was reading the Ubuntu files as a Windows network path instead of connecting into Ubuntu.
- **Fix:** install the Microsoft "WSL" extension, close VS Code, and run `code .` from the Ubuntu terminal. Bottom-left should show "WSL: Ubuntu".
- **Lesson:** the editor window runs on Windows; the work (terminal, Python, Git) should run inside Linux.

### T4. Working in the wrong copy of the repo
- **When:** 2026-11-20
- **Symptom:** prompt showed `/mnt/d/Realtime-Banking-Lakehouse-Pipeline`.
- **Cause:** two copies existed (D: drive and Ubuntu); I opened the retired D: copy.
- **Fix:** `cd ~/projects/Realtime-Banking-Lakehouse-Pipeline`; rename the D: folder to `OLD_do_not_use`.
- **Lesson:** check the prompt shows `~/projects/...` before running anything. The two copies only sync through GitHub.

### T5. `make venv` failed
- **When:** 2026-11-20
- **Symptom:** virtual environment creation failed. <!-- paste the exact error if you still have it -->
- **Cause:** Ubuntu had Python 3.14 but not its `venv` package.
- **Fix:** `sudo apt update && sudo apt install -y python3.14-venv`, then `make venv` again.
- **Lesson:** Ubuntu splits Python into several apt packages; `venv` isn't always included.

### T6. Persistence test: `DELETE` returned 404 "Namespace does not exist"
- **When:** 2026-11-20
- **Symptom:** 404 with a long Java error trace from the catalog.
- **Cause:** typo. Created `presist_check`, tried to delete `persist_check`.
- **Fix:** `curl -s -X DELETE http://localhost:8181/v1/namespaces/presist_check`
- **Lesson:** read the error message before assuming the service is broken. The 404 showed the catalog validates requests.

### T7. `docker compose down` did nothing
- **When:** 2026-11-20
- **Symptom:** the command exited silently; containers were still running in `docker ps`.
- **Cause:** every service is in a Compose profile, and a plain `down` only acts on *active* profiles.
- **Fix:** `docker compose --profile "*" down` (this is what `make down` runs).
- **Lesson:** with profiles, always pass `--profile` (or use the Makefile) to avoid orphaned containers using RAM.

### T8. `make: *** No rule to make target 'stop'`
- **When:** 2026-11-20
- **Symptom:** `make stop` failed; `make ps` worked.
- **Cause:** the Makefile has `down` but no `stop` target.
- **Fix:** use `make down`, or add `stop` / `start` targets (command lines must start with a TAB).
- **Lesson:** `grep -n "target" Makefile` shows what exists. Note: `make clean` runs `down -v`, which **deletes all volumes**.