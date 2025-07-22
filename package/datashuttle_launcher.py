import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Import main from tui_launcher
from datashuttle.tui_launcher import main as datashuttle_main


def run():
    # Simulate: datashuttle launch
    sys.argv = ["datashuttle", "launch"]
    datashuttle_main()


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        input("\nPress Enter to exit...")
