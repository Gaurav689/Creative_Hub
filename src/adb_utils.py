import subprocess
import os
import sys
import io
from PIL import Image, ImageOps, ImageEnhance

def get_adb_path():
    # Use the same logic from fast_adb_observer
    local_paths = [
        "adb", 
        "adb.exe",
        "d:/contentaai/platform-tools-latest-windows/platform-tools/adb.exe",
        "platform-tools/adb.exe"
    ]
    for path in local_paths:
        try:
            subprocess.check_call([path, "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return path
        except:
            continue
    return "adb"

ADB_PATH = get_adb_path()

def capture_screenshot(dest_path):
    try:
        # 1. Raw ADB Capture
        cmd = [ADB_PATH, "exec-out", "screencap", "-p"]
        raw_bytes = subprocess.check_output(cmd)
        
        # 2. Load into Pillow for processing
        img = Image.open(io.BytesIO(raw_bytes))
        width, height = img.size
        
        # 3. UI-Stripping (Deep Crop for Tall Phones)
        # Ibis Paint menus are thick. Let's take more off top (15%) and bottom (25%)
        left = 0
        top = int(height * 0.15)
        right = width
        bottom = int(height * 0.75) 
        img_cropped = img.crop((left, top, right, bottom))
        
        # 4. Line-Boosting (Enhance Contrast & Threshold)
        # Convert to grayscale to boost lines, then back to RGB
        img_gray = ImageOps.grayscale(img_cropped)
        # Autocontrast stretches the brightness (makes faints dark)
        img_boosted = ImageOps.autocontrast(img_gray, cutoff=2)
        
        # INVERT for ControlNet (Models expect white lines on black background)
        img_inverted = ImageOps.invert(img_boosted)
        
        # Sharpen for ControlNet
        enhancer = ImageEnhance.Sharpness(img_inverted)
        img_final = enhancer.enhance(2.0).convert("RGB")

        
        # 5. Save the "Cleaned" version
        img_final.save(dest_path, "JPEG", quality=95)
        print(f"[+] Screen captured and enhanced: {os.path.basename(dest_path)}")
        return True
    except Exception as e:
        print(f"ADB Capture & Enhance Error: {e}")
        # Fallback to raw if processing fails
        try:
            with open(dest_path, "wb") as f:
                f.write(raw_bytes)
            return True
        except:
            return False

def push_to_phone(local_path, remote_folder="/sdcard/ai_imagination/"):
    try:
        filename = os.path.basename(local_path)
        remote_path = os.path.join(remote_folder, filename).replace("\\", "/")
        
        # Ensure directory exists
        subprocess.run([ADB_PATH, "shell", "mkdir", "-p", remote_folder], check=True)
        
        # Push file
        subprocess.run([ADB_PATH, "push", local_path, remote_path], check=True)
        
        # Trigger Media Scanner
        # Use 'am broadcast' for older Android, 'content' command for newer
        subprocess.run([
            ADB_PATH, "shell", "am", "broadcast", "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE", 
            "-d", f"file://{remote_path}"
        ], check=True)
        
        return remote_path
    except Exception as e:
        print(f"ADB Push Error: {e}")
        return None
