# Creative Hub Pro: AI-Powered Anime Animation Assistant

**Creative Hub Pro** is a professional-grade AI pipeline designed to bridge physical creativity (sketching on tablet/phone) with high-end Generative AI. It allows artists to draw in apps like **Ibis Paint** or **FlipaClip** and instantly see their sketches transformed into high-quality anime illustrations via a remote GPU-powered Stable Diffusion backend.

---

## 🚀 Key Features

- **Zero-Latency Monitoring**: Real-time screen capture of your Android device via ADB.
- **Vision Reasoning**: Integrated with **Google Gemini 2.0 Flash** to analyze your sketch and generate context-aware artistic prompts.
- **Cloud-GPU Rendering**: Automated bridge to **ComfyUI** running on Google Colab, utilizing the powerful **Pony Diffusion V6 XL** model.
- **Physical Triggering**: Use your phone's **Volume Up** button to instantly trigger a generation without leaving your drawing app.
- **Creative Hub UI**: A sleek, dark-mode web interface accessible directly on your phone/tablet to manage prompts and view history.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, Flask
- **Mobile Connection**: ADB (Android Debug Bridge)
- **AI Reasoning**: Google Gemini API (`google-genai`)
- **Image Generation**: ComfyUI API + Stable Diffusion XL
- **Model**: Pony Diffusion V6 XL
- **Cloud Hosting**: Google Colab + Localtunnel
- **Database**: SQLite (for prompt/image history)

---

## 📂 Project Structure & Essential Files

To run this project from start to finish, the following files are required:

### Core Orchestration
- [creative_hub_orchestrator.py](file:///d:/contentaai/creative_hub_orchestrator.py): The main entry point. Sets up the ADB bridge and starts the server.
- [requirements.txt](file:///d:/contentaai/requirements.txt): Python dependencies.
- [.env](file:///d:/contentaai/.env): Configuration file (User-provided: Gemini API Key & Colab URL).

### Backend (src/)
- [creative_hub_server.py](file:///d:/contentaai/src/creative_hub_server.py): Flask server and hardware button listener.
- [adb_utils.py](file:///d:/contentaai/src/adb_utils.py): Handles screen capture and file syncing to the phone.
- [gemini_vision.py](file:///d:/contentaai/src/gemini_vision.py): Communicates with Gemini for vision-to-prompt reasoning.
- [generate_anime_colab.py](file:///d:/contentaai/src/generate_anime_colab.py): Communicates with the remote ComfyUI API.
- [database.py](file:///d:/contentaai/src/database.py): SQLite management for generation history.

### Frontend (src/templates/ & src/static/)
- `index.html`: The Creative Hub dashboard structure.
- `app.js` / `style.css`: UI logic and premium dark-mode styling.

### Remote Setup
- [docs/colab_comfyui_setup.md](file:///d:/contentaai/docs/colab_comfyui_setup.md): Step-by-step guide to setting up the GPU server on Google Colab.

---

## 🏃 Setup & Usage

### 1. Remote GPU Setup
1. Open the [Google Colab Guide](file:///d:/contentaai/docs/colab_comfyui_setup.md).
2. Run the provided cells to start ComfyUI.
3. Copy the **Localtunnel URL** (e.g., `https://...loca.lt`) and your **Endpoint IP**.

### 2. Local Configuration
1. Create a `.env` file in the root directory:
   ```env
   GEMINI_API_KEY=your_google_gemini_key
   COMFYUI_URL=https://your-localtunnel-url.loca.lt
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### 3. Usage
1. Connect your Android phone via USB (Enable **USB Debugging**).
2. Run the orchestrator:
   ```bash
   python creative_hub_orchestrator.py
   ```
3. Open Chrome on your phone and go to `http://localhost:5000`.
4. **Start Drawing**: Open Ibis Paint or FlipaClip.
5. **Generate**: Press the **Volume Up** button on your phone. The AI will capture your screen, reason with Gemini, generate an image on Colab, and sync it back to your phone's gallery!

---

## 📝 Important Notes
- **USB Connection**: The phone must stay connected via USB for the ADB bridge to function.
- **Free Tier Limits**: Ensure your Gemini API usage is within the free tier rate limits (15 RPM).
- **ControlNet**: The system automatically uses ControlNet (Canny) if you provide a sketch, ensuring high character consistency.
