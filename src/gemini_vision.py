import os
import argparse
import sys
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Automatically look for a .env file in the current directory and load its variables
load_dotenv()

PROMPT_FILE = "d:/contentaai/prompts/reasoning"

def load_reasoning_prompt():
    """Load the reasoning logic from the prompt file."""
    if os.path.exists(PROMPT_FILE):
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return "Analyze this screenshot and reason about the next steps for anime generation."

def get_anime_prompt_from_image(image_path, model_id="gemini-flash-latest", user_context=None):
    """
    Analyzes an image and returns a prompt specifically for anime generation.
    Incorporates user_context for hybrid reasoning.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "ERROR: GEMINI_API_KEY is not set."

    client = genai.Client(api_key=api_key)

    if not os.path.exists(image_path):
        return f"ERROR: File not found at {image_path}"

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    base_prompt = load_reasoning_prompt()
    
    # Combined prompt for Gemini
    final_instruction = base_prompt
    if user_context:
        final_instruction += f"\n\nUSER EXPLICIT CONTEXT: {user_context}\nIMPORTANT: Prioritize the user's explicit intent in the final prompt while using the image for layout/style."

    try:
        response = client.models.generate_content(
            model=model_id,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                final_instruction
            ]
        )
        
        text = response.text
        if "PROMPT:" in text:
            return text.split("PROMPT:")[1].strip()
        return text.strip()

    except Exception as e:
        return f"ERROR: API call failed: {e}"

def main():
    parser = argparse.ArgumentParser(description="Gemini 1.5 Flash: Screenshot Vision & Reasoning")
    parser.add_argument("image", help="Path to the screenshot/image file.")
    parser.add_argument("--prompt", help="Override the default reasoning prompt.")
    parser.add_argument("--model", default="gemini-flash-latest", help="Gemini model to use.")
    args = parser.parse_args()

    # Reuse the function for CLI output
    result = get_anime_prompt_from_image(args.image, args.model)
    print("\n=== GEMINI REASONING OUTPUT ===")
    print(result)
    print("===============================\n")

if __name__ == "__main__":
    main()
