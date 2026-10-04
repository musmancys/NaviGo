import os
import sys
import subprocess

def main():
    # If running with global python and a local virtualenv exists, use the virtualenv python
    venv_python_win = os.path.join(".venv", "Scripts", "python.exe")
    venv_python_posix = os.path.join(".venv", "bin", "python")

    current_python = sys.executable

    if os.path.exists(venv_python_win) and os.path.abspath(current_python) != os.path.abspath(venv_python_win):
        print(f">> Using virtual environment: {venv_python_win}")
        sys.exit(subprocess.call([venv_python_win, "run.py"] + sys.argv[1:]))
    elif os.path.exists(venv_python_posix) and os.path.abspath(current_python) != os.path.abspath(venv_python_posix):
        print(f">> Using virtual environment: {venv_python_posix}")
        sys.exit(subprocess.call([venv_python_posix, "run.py"] + sys.argv[1:]))

    # Auto-seed database if not present
    db_file = os.path.join("backend", "data", "demo_navigo.db")
    if not os.path.exists(db_file):
        print(">> First run detected: Seeding local demo database...")
        from scripts.seed_demo_data import seed_all
        seed_all()

    # Read network configuration
    is_prod = os.environ.get("APP_ENV") == "prod"
    default_host = "0.0.0.0" if is_prod else "127.0.0.1"
    host = os.environ.get("HOST", default_host)
    port = int(os.environ.get("PORT", 8000))

    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

    print(f"\n========================================================")
    print(f">> NaviGo Platform is Starting!")
    print(f">> Local URL: http://{host}:{port}")
    print(f">> API Docs:  http://{host}:{port}/docs")
    print(f">> Mode:      {'Production' if is_prod else 'Dev (Hot-Reload)'}")
    print(f"========================================================\n")

    import uvicorn
    uvicorn.run("backend.app.main:app", host=host, port=port, reload=not is_prod)

if __name__ == "__main__":
    main()
