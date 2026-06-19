import subprocess
import sys
import os

os.chdir("backend")
subprocess.run([
    sys.executable, "-m", "uvicorn",
    "app_hf:app",
    "--host", "0.0.0.0",
    "--port", "7860"
])
