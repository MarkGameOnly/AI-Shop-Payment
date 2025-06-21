import os
import subprocess
import threading
import time

def run():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    subprocess.call(["python", "main.py"])

threading.Thread(target=run).start()

while True:
    time.sleep(60)
