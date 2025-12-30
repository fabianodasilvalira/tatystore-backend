import sys
import os
sys.path.append("/app")

# Tenta importar app
try:
    from app.main import app
    print("SUCCESS: Imported app.main")
except ImportError as e:
    print(f"ERROR: Could not import app.main: {e}")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: Exception importing app.main: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nDEBUG ROUTES LIST:")
for route in app.routes:
    path = getattr(route, "path", "No path")
    methods = getattr(route, "methods", "No methods")
    print(f"{path} {methods}")
