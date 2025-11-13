import subprocess
import sys

result = subprocess.run([sys.executable, "db_connector.py"], capture_output=True, text=True)
print("--- STDOUT ---")
print(result.stdout)
print("--- STDERR ---")
print(result.stderr)
