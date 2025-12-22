import os, sys, shutil
from pathlib import Path
import argparse

def startup_folder() -> Path:
    # %APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
    return Path(os.getenv("APPDATA")) / r"Microsoft\Windows\Start Menu\Programs\Startup"

def create_startup_shortcut():
    # Simple approach: create a .bat file that launches `assistant start`
    sf = startup_folder()
    sf.mkdir(parents=True, exist_ok=True)
    bat_path = sf / "assistant_start.bat"
    python_exe = sys.executable
    cmd = f'"{python_exe}" -m assistant_app.main start'
    bat_path.write_text(f"@echo off\n{cmd}\n")
    print(f"Created {bat_path}")

def remove_startup_shortcut():
    bat_path = startup_folder() / "assistant_start.bat"
    if bat_path.exists():
        bat_path.unlink()
        print("Removed startup entry.")
    else:
        print("No startup entry found.")

if __name__ == "__main__":

    ap = argparse.ArgumentParser()
    ap.add_argument("--install", action="store_true")
    ap.add_argument("--remove", action="store_true")
    args = ap.parse_args()
    if args.install: create_startup_shortcut()
    elif args.remove: remove_startup_shortcut()
    else: print("Use --install or --remove")
