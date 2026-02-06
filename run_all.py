import subprocess
import time
import sys
import os
import socket
import webview

# Paths
ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT, "backend")
FRONTEND_DIR = os.path.join(ROOT, "frontend")

def wait_for_port(port, timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return True
        time.sleep(0.5)
    return False

def main():
    print("[Launcher] Starting VidAutoDown Desktop...")

    # 1. Start Backend
    print("[Launcher] Starting Backend Engine...")
    venv_python = os.path.join(BACKEND_DIR, "venv", "Scripts", "python.exe")
    backend_cmd = [
        venv_python, "-m", "uvicorn", 
        "backend.main:app", 
        "--host", "127.0.0.1", 
        "--port", "8000"
    ]
    # No console window for backend
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = 0 # SW_HIDE

    backend_proc = subprocess.Popen(
        backend_cmd, 
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": ROOT},
        startupinfo=si
    )

    # 2. Start Frontend
    print("[Launcher] Starting UI Layer...")
    # npm run dev is fine, but for "prod" look we might settle for dev for now
    # We hide its window too if possible, but shell=True makes that hard on Windows without extra steps
    # For now we let it show or minimize it. 
    # Actually, we can use the same startupinfo workaround if we call node directly, but npm is a bat file.
    frontend_proc = subprocess.Popen(
        ["npm", "run", "dev"], 
        cwd=FRONTEND_DIR, 
        shell=True
        # stderr=subprocess.DEVNULL,
        # stdout=subprocess.DEVNULL 
    )

    # 3. Wait for services
    print("[Launcher] Waiting for connection...")
    if not wait_for_port(8000) or not wait_for_port(3000):
        print("Error: Services failed to start.")
        backend_proc.terminate()
        os.system(f"taskkill /F /T /PID {frontend_proc.pid} >nul 2>&1")
        return

    # 4. Launch Desktop Window
    print("[Launcher] Opening Window...")
    webview.create_window(
        "VidAutoDown", 
        "http://localhost:3000",
        width=1120,
        height=760,
        min_size=(900, 600),
        background_color='#0f172a'
    )
    
    webview.start()

    # 5. Cleanup on Close
    print("[Launcher] Shutting down...")
    backend_proc.terminate()
    if sys.platform == "win32":
        os.system(f"taskkill /F /T /PID {frontend_proc.pid} >nul 2>&1")
        os.system(f"taskkill /F /T /PID {backend_proc.pid} >nul 2>&1")
    else:
        frontend_proc.terminate()

if __name__ == "__main__":
    main()
