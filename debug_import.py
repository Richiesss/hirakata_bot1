import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

print(f"Python executable: {sys.executable}")
print(f"CWD: {os.getcwd()}")

try:
    print("Attempting to import features.poll_manager...")
    from features import poll_manager
    print("Successfully imported features.poll_manager")
except ImportError as e:
    print(f"ImportError: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"Exception: {e}")
    import traceback
    traceback.print_exc()
