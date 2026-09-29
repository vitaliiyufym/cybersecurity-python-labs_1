import os
import subprocess
import sys

BASE_DIR = os.path.dirname(__file__)

subprocess.run([sys.executable, os.path.join(BASE_DIR, "task1.py")], check=False)
subprocess.run([sys.executable, os.path.join(BASE_DIR, "task2.py")], check=False)
subprocess.run([sys.executable, os.path.join(BASE_DIR, "task3.py")], check=False)
