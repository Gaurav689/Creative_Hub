import os
import time
import threading
import subprocess
import json
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS

import adb_utils
import gemini_vision
import generate_anime_colab
from database import db

app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')
CORS(app)

# Configuration
OUTPUT_DIR = "d:/contentaai/data/outputs"
SHOTS_DIR = "d:/contentaai/data/phoneshots"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(SHOTS_DIR, exist_ok=True)

# Shared state
status_state = {
    "status": "Ready",
    "last_image": None,
    "is_generating": False,
    "current_manual_prompt": ""
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    return jsonify(status_state)

@app.route('/api/generate', methods=['POST'])
def generate():
    global status_state
    if status_state['is_generating']:
        return jsonify({"error": "Already generating"}), 400
    
    data = request.json
    manual_prompt = data.get('prompt', '').strip()
    status_state['current_manual_prompt'] = manual_prompt # Save for background iterations
    
    trigger_generation(manual_prompt)
    return jsonify({"success": True})

def trigger_generation(manual_prompt):
    global status_state
    status_state['is_generating'] = True
    status_state['status'] = "Capturing phone screen..."
    threading.Thread(target=process_generation, args=(manual_prompt,)).start()

def process_generation(manual_prompt):
    global status_state
    try:
        # 1. Capture
        shot_path = os.path.join(SHOTS_DIR, f"manual_{int(time.time())}.jpg")
        if not adb_utils.capture_screenshot(shot_path):
            status_state['status'] = "Error: Capture failed"
            status_state['is_generating'] = False
            return

        # 2. Vision Reasoning
        status_state['status'] = "Gemini is thinking..."
        refined_prompt = gemini_vision.get_anime_prompt_from_image(shot_path, user_context=manual_prompt)
        
        # --- SMART FALLBACK LOGIC ---
        # If Gemini fails or returns a weird artifact like '**'
        if "ERROR" in refined_prompt or len(refined_prompt.strip()) < 5 or refined_prompt.strip() == "**":
            print(f"[!] Warning: Gemini returned weak prompt '{refined_prompt}'. Using artistic fallback.")
            style_tags = "masterpiece, high quality, professional anime illustration, cinematic lighting, vivid colors, highly detailed"
            if manual_prompt:
                refined_prompt = f"{style_tags}, {manual_prompt}, beautiful digital art"
            else:
                refined_prompt = f"{style_tags}, beautiful scenery, sharp focus"
        
        status_state['status'] = f"Prompt: {refined_prompt[:30]}..."
        print(f"\n[AI REASONING] >>> {refined_prompt}\n")

        # 3. Colab Generation

        status_state['status'] = "GPU generating..."
        result_str = generate_anime_colab.send_prompt_to_colab(refined_prompt, image_path=shot_path)
        
        if "SUCCESS" in result_str:
            local_path = result_str.split("Downloaded to ")[1].strip()
            filename = os.path.basename(local_path)
            
            # 4. Push to Phone
            status_state['status'] = "Syncing gallery..."
            adb_utils.push_to_phone(local_path)
            
            # 5. Save to DB
            db.add_entry(manual_prompt, refined_prompt, local_path, "pushed_to_phone")
            
            # 6. Finalize
            status_state['last_image'] = filename
            status_state['status'] = "Success!"
        else:
            status_state['status'] = f"GPU Error: {result_str[:40]}"

    except Exception as e:
        status_state['status'] = f"Crash: {str(e)}"
    finally:
        status_state['is_generating'] = False

@app.route('/api/images/<filename>')
def serve_image(filename):
    return send_from_directory(OUTPUT_DIR, filename)

# --- BACKGROUND LISTENER FOR VOLUME BUTTONS ---
def adb_volume_listener():
    """Listens for Volume Up presses and triggers generation instantly."""
    adb_path = adb_utils.ADB_PATH
    print("[*] Volume Button Listener active (Zero-Latency mode)...")
    
    # Use -l for human readable labels, but ensure we read line-by-line without delay
    cmd = [adb_path, "shell", "getevent", "-l"]
    
    # Use a smaller buffer size for faster output flushing
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
    
    try:
        while True:
            line = process.stdout.readline()
            if not line:
                break
            # KEY_VOLUMEUP and DOWN (typical for most devices)
            if "KEY_VOLUMEUP" in line and " DOWN" in line:
                if not status_state['is_generating']:
                    print(f"\n[!] TRIGGER DETECTED: {time.strftime('%H:%M:%S')}")
                    # Trigger instantly
                    trigger_generation(status_state.get('current_manual_prompt', ''))
    except Exception as e:
        print(f"[-] Listener stopped: {e}")
    finally:
        process.terminate()

if __name__ == '__main__':
    # Start volume listener in a daemon thread
    threading.Thread(target=adb_volume_listener, daemon=True).start()
    
    # Run server
    app.run(host='0.0.0.0', port=5000, debug=False)
