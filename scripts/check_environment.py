import importlib.util, shutil, sys
for mod in ("flask","celery","redis","flask_cors"):
    print(f"{mod}: {'installed' if importlib.util.find_spec(mod) else 'MISSING'}")
for exe in ("redis-server","redis-cli","node","npm"):
    print(f"{exe}: {shutil.which(exe) or 'not found on PATH'}")
