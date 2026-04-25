# Zero-Cost Colab ComfyUI Setup Guide

This guide will set up an automated ComfyUI instance on a free Google Colab GPU. It uses `localtunnel` to expose the internal ComfyUI API to the public web so your local `generate_anime_colab.py` script can talk to it!

## Instructions
1. Go to [Google Colab](https://colab.research.google.com/) and create a **New Notebook**.
2. At the top menu, click **Runtime** > **Change runtime type**, and select **T4 GPU**.
3. Create new code cells and paste the following Python/Bash code blocks into them.

---

### Cell 1: Install ComfyUI and Dependencies
*Paste this into the first cell and click the "Play" button. This takes about 2-3 minutes to run.*

```python
# Clone the ComfyUI Repository
!git clone https://github.com/comfyanonymous/ComfyUI
%cd ComfyUI

# Install PyTorch and ComfyUI Requirements
!pip install -q torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu121
!pip install -q -r requirements.txt

# Install localtunnel to bypass Google Colab restrictions
!npm install -g localtunnel
```

---

### Cell 2: Download the Anime Model Checkpoint
*We will download `Pony Diffusion V6 XL` which is incredible at Anime / Character Consistency.*

```python
# Create directories if they don't exist
!mkdir -p models/checkpoints
!mkdir -p models/controlnet

# Download Pony Diffusion V6 XL (safetensors format)
# This is a large ~6GB file, it will take about 1 minute on Colab's fast network.
!wget -c https://civitai.com/api/download/models/290640 -O ./models/checkpoints/PonyDiffusionV6XL.safetensors

# Download ControlNet (SDXL Canny) - Required for sketch-to-image
!wget -c https://huggingface.co/diffusers/controlnet-canny-sdxl-1.0/resolve/main/diffusion_pytorch_model.fp16.safetensors -O ./models/controlnet/diffusion_pytorch_model.fp16.safetensors

```

---

### Cell 3: Start the Server and Tunnel
*This is the magic cell. It starts ComfyUI in the background and sets up a secure tunnel.*

```python
import urllib
import subprocess
import threading
import time

# 1. Provide your tunnel password (localtunnel requires this for security)
print("Password/Enpoint IP for your tunnel is:", urllib.request.urlopen('https://ipv4.icanhazip.com').read().decode('utf8').strip("\n"))

# 2. Start ComfyUI in the background
def start_comfyui():
  !python main.py --dont-print-server

threading.Thread(target=start_comfyui, daemon=True).start()

# 3. Give it a moment to boot
time.sleep(5)

# 4. Start localtunnel on Port 8188 (ComfyUI default port)
!lt --port 8188
```

## How to use it:
1. When you run **Cell 3**, it will print out an IP Address (e.g., `34.123.45.67`) and a public URL (e.g., `https://tiny-snails-run.loca.lt`).
2. Go to that `https://...loca.lt` URL in your browser.
3. It will ask for an "Endpoint IP" (this is Localtunnel's anti-phishing protection).
4. Paste the IP Address the cell gave you.
5. You are now inside your remote, GPU-powered ComfyUI!

> **CRITICAL:** Use that `loca.lt` URL in your local Python orchestration script to send it automated API generation calls.
