from pathlib import Path
import runpy
import sys
shared = Path(__file__).resolve().parents[2] / "For_new_users" / "Scripts"
sys.path.insert(0, str(shared))
if __name__ == "__main__":
    runpy.run_path(str(shared / "UI.py"), run_name="__main__")
