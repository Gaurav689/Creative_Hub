import subprocess
import os
import sys
import time
import socket

# Ensure we can import from src
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
try:
    import adb_utils
except ImportError:
    print("Error: Could not find src/adb_utils.py. Please run from the project root.")
    sys.exit(1)

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def setup_adb_reverse():
    try:
        adb_path = adb_utils.ADB_PATH
        print(f"[*] Connecting to phone via {adb_path}...")
        subprocess.run([adb_path, "reverse", "tcp:5000", "tcp:5000"], capture_output=True)
        print("[+] USB Bridge Active: Phone can access Hub at http://localhost:5000")
    except Exception as e:
        print(f"[-] ADB Reverse Warning: {e}")

def main():
    print("""
==================================================
   GENREATIVE ANIME - CREATIVE HUB PRO
==================================================
[*] Unified Orchestrator Starting...
""")
    
    setup_adb_reverse()
    
    local_ip = get_local_ip()
    
    print(f"\n[!] INSTRUCTIONS FOR YOUR PHONE:")
    print(f"    1. Open Chrome on your phone.")
    print(f"    2. Go to: http://localhost:5000")
    print(f"       (or http://{local_ip}:5000 if using Wi-Fi)")
    print(f"    3. PRO TIP: Switch Chrome to 'Pop-up view' or 'Split Screen'")
    print(f"       so you can see the Hub while drawing in Ibis Paint!")
    
    print("\n[!] REMOTE TRIGGER READY:")
    print("    - Press the VOLUME UP button on your phone anytime")
    print("    - The AI will capture your current Ibis Paint screen instantly.")
    print("    - Provide feedback in the browser Hub to refine the image.")
    
    print("\n--- SERVER LOGS ---")
    
    # Start the Flask server (which now includes the Volume Listener)
    try:
        env = os.environ.copy()
        # Ensure python can find modules
        env["PYTHONPATH"] = os.path.join(os.getcwd(), "src")
        subprocess.run([sys.executable, "src/creative_hub_server.py"], env=env)
    except KeyboardInterrupt:
        print("\n[*] Shutting down gracefully...")

if __name__ == "__main__":
    main()
