import os
import io
import json
import urllib.request
import urllib.parse
import argparse
import sys
import uuid
import time
from dotenv import load_dotenv

# Load API keys and URLs
load_dotenv()

def upload_image(image_path, url):
    """Uploads an image to ComfyUI and returns the filename."""
    url = url.rstrip('/')
    with open(image_path, 'rb') as f:
        image_data = f.read()
    
    # Multipart/form-data boundary
    boundary = '----ComfyUIBoundary'
    filename = os.path.basename(image_path)
    
    body = (
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="image"; filename="{filename}"\r\n'
        'Content-Type: image/jpeg\r\n\r\n'
    ).encode('utf-8') + image_data + f'\r\n--{boundary}--\r\n'.encode('utf-8')
    
    req = urllib.request.Request(f"{url}/upload/image", data=body)
    req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
    req.add_header('Bypass-Tunnel-Reminder', 'true')
    req.add_header('User-Agent', 'localtunnel')
    
    try:
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read())
            return res.get('name')
    except Exception as e:
        print(f"Image Upload Error: {e}")
        return None

def queue_prompt(prompt_workflow, url):
    """Sends the ComfyUI workflow JSON to the Colab API for generation."""
    # Ensure URL doesn't have a trailing slash so /prompt works correctly
    url = url.rstrip('/')
    
    # ComfyUI API requires a 'client_id' to track the request
    client_id = str(uuid.uuid4())
    p = {"prompt": prompt_workflow, "client_id": client_id}
    
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(f"{url}/prompt", data=data)
    
    # --- CRITICAL HEADERS ---
    req.add_header('Content-Type', 'application/json')
    # Bypass localtunnel anti-phishing landing page
    req.add_header('Bypass-Tunnel-Reminder', 'true')
    # Use a non-standard User-Agent to further ensure bypass
    req.add_header('User-Agent', 'localtunnel')
    
    try:
        response = urllib.request.urlopen(req)
        raw_data = response.read()
        
        try:
            decoded_data = raw_data.decode('utf-8')
            if "Bad Gateway" in decoded_data:
                print(f"Error: ComfyUI proxy responded with 'Bad Gateway'. Your tunnel might be expired.", file=sys.stderr)
                return None
            return json.loads(decoded_data)
        except UnicodeDecodeError:
            return json.loads(raw_data) # Fallback for binary if needed, though here stays JSON
            
    except urllib.error.HTTPError as e:
        # Read the error body to see the specific reason from ComfyUI
        error_body = e.read().decode('utf-8')
        if "Bad Gateway" in error_body:
            print(f"Error: ComfyUI proxy at {url} responded with 'Bad Gateway' (HTTP {e.code}). Update your COMFYUI_URL.", file=sys.stderr)
        else:
            print(f"Server Error (HTTP {e.code}): {error_body}", file=sys.stderr)
        return None
    except json.JSONDecodeError:
        print(f"Error: Received invalid JSON from {url}. Check if the service is running.", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error connecting to ComfyUI at {url}: {e}", file=sys.stderr)
        return None

def send_prompt_to_colab(positive_prompt, negative_prompt="low quality, blurry, deformed hands, bad eyes", url=None, image_path=None):
    """ Helper function with automatic wait-and-download and ControlNet support! """
    """ Helper function with automatic wait-and-download! """
    comfyui_url = url if url else os.environ.get("COMFYUI_URL")
    if not comfyui_url:
        return "ERROR: COMFYUI_URL is not set."

    # Ensure output dir exists
    output_dir = "d:/contentaai/data/outputs"
    os.makedirs(output_dir, exist_ok=True)

    # --- STYLE & ACTION PRIORITY LOGIC ---
    # Detect if the user wants a non-colorful style
    dry_keywords = ["sketch", "pencil", "lineart", "monochrome", "black and white", "outline", "ink"]
    is_dry_style = "STYLE: SKETCH" in positive_prompt.upper() or any(k in positive_prompt.lower() for k in dry_keywords)
    
    # Clean up the "STYLE:" header so it doesn't confuse the AI
    clean_prompt = positive_prompt.replace("STYLE: SKETCH", "").replace("STYLE: COLOR", "").replace("STYLE: sketch", "").strip()
    
    # Handle the "Color Stripper" filter for Sketches
    if is_dry_style:
        # 1. Strip all common color words (Red, Green, Blue, Lush, Vibrant, etc.)
        forbidden_words = [
            "red", "green", "blue", "yellow", "pink", "purple", "orange", "brown", 
            "cyan", "magenta", "emerald", "azure", "vibrant", "colorful", "lush", 
            "saturated", "brightly colored", "polychromatic", "rainbow"
        ]
        
        # Use regex to replace whole words only (case-insensitive)
        import re
        for word in forbidden_words:
            # Match word with optional trailing comma/space
            clean_prompt = re.sub(rf'\b{word}\b[\s,]*', '', clean_prompt, flags=re.IGNORECASE)
        
        # 2. Inject strict monochrome/sketch tags into the lead
        final_positive_prompt = f"(monochrome:1.5), (sketch:1.2), pencil drawing, graphite texture, {clean_prompt}, score_9, score_8_up, score_7_up, rating_safe"
        
        # 3. Force color/saturation to be negative
        negative_prompt = f"color, vibrant, saturated, polychromatic, gradient, {negative_prompt}"
    else:
        # Standard high-quality anime (Keep everything)
        final_positive_prompt = f"{clean_prompt}, score_9, score_8_up, score_7_up, rating_safe, source_anime"
    
    print(f"[COMFYUI PROMPT] >>> {final_positive_prompt}")

    # --- WORKFLOW CONSTRUCTION ---
    # Default prompt-only workflow
    comfy_workflow = {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "seed": 1337,
                "steps": 25, 
                "cfg": 7.0,
                "sampler_name": "euler_ancestral",
                "scheduler": "karras",
                "denoise": 1.0,
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0]
            }
        },
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "PonyDiffusionV6XL.safetensors"}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 832, "height": 1216, "batch_size": 1}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": final_positive_prompt, "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": negative_prompt, "clip": ["4", 1]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "anime_automation_result", "images": ["8", 0]}}
    }

    # --- CONTROLNET INFUSION (If Image Provided) ---
    if image_path and os.path.exists(image_path):
        print(f"[*] ControlNet Mode: Uploading {os.path.basename(image_path)}...")
        uploaded_name = upload_image(image_path, comfyui_url)
        
        if uploaded_name:
            # Inject ControlNet Nodes (Standard SDXL Canny)
            comfy_workflow["10"] = {"class_type": "ControlNetLoader", "inputs": {"control_net_name": "diffusion_pytorch_model.fp16.safetensors"}}
            comfy_workflow["11"] = {"class_type": "LoadImage", "inputs": {"image": uploaded_name, "upload": "image"}}
            comfy_workflow["12"] = {
                "class_type": "ControlNetApply", 
                "inputs": {
                    "strength": 0.28, 
                    "start_at": 0.0,
                    "end_at": 0.50,   
                    "conditioning": ["6", 0], 
                    "control_net": ["10", 0], 
                    "image": ["11", 0]
                }
            }




            # Redirect KSampler to use ControlNet conditioning
            comfy_workflow["3"]["inputs"]["positive"] = ["12", 0]
            print("[+] ControlNet enabled for this generation.")
        else:
            print("[!] ControlNet failed (Upload Error). Falling back to Prompt-only.")
    
    result = queue_prompt(comfy_workflow, comfyui_url)
    if not result:
        return "ERROR: Failed to queue prompt."

    prompt_id = result.get('prompt_id')
    print(f"Queued on GPU (ID: {prompt_id}). Waiting for result...", flush=True)

    # --- AUTO-DOWNLOAD LOGIC ---
    # We poll the history API to see when the job is done
    max_retries = 60 # 2 minutes timeout
    url = comfyui_url.rstrip('/')
    
    for _ in range(max_retries):
        try:
            req = urllib.request.Request(f"{url}/history/{prompt_id}")
            req.add_header('Bypass-Tunnel-Reminder', 'true')
            req.add_header('User-Agent', 'localtunnel')
            
            with urllib.request.urlopen(req) as resp:
                history = json.loads(resp.read())
                if prompt_id in history:
                    # Job done! Find the image name
                    outputs = history[prompt_id].get('outputs', {})
                    if '9' in outputs: # '9' is the ID of SaveImage node in our workflow
                        images = outputs['9'].get('images', [])
                        if images:
                            filename = images[0]['filename']
                            # Download the image
                            download_url = f"{url}/view?filename={filename}&type=output"
                            local_filename = os.path.join(output_dir, f"result_{prompt_id[:8]}.png")
                            
                            req_dl = urllib.request.Request(download_url)
                            req_dl.add_header('Bypass-Tunnel-Reminder', 'true')
                            req_dl.add_header('User-Agent', 'localtunnel')
                            
                            with urllib.request.urlopen(req_dl) as img_resp:
                                with open(local_filename, "wb") as f:
                                    f.write(img_resp.read())
                            return f"SUCCESS: Downloaded to {local_filename}"
            time.sleep(2) # Polling interval
        except:
            time.sleep(2)

    return f"QUEUED: Prompt ID {prompt_id} sent, but taking too long to download."

def main():
    parser = argparse.ArgumentParser(description="Send an anime art prompt to a remote Google Colab ComfyUI instance.")
    parser.add_argument("positive", help="Positive prompt/tags for drawing.")
    parser.add_argument("--negative", default="low quality, blurry, deformed hands, bad eyes", help="Negative prompt.")
    parser.add_argument("--url", help="Override the COMFYUI_URL from .env.")
    args = parser.parse_args()

    print(f"--- DISPATCHING TO COLAB ---")
    result = send_prompt_to_colab(args.positive, args.negative, args.url)
    print(result)

if __name__ == "__main__":
    main()
