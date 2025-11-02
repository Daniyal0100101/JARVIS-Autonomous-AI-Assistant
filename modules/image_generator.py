"""Image generation using api.airforce free endpoints.

Provides a single entry `generate_image` that accepts a prompt and returns the
saved filename or an error message. Handles both direct URL and base64 JSON
responses from the backend.
"""

import os
import base64
import requests
from PIL import Image
from io import BytesIO

def generate_image(prompt: str, filename: str = None, model: str = "dall-e-3", size: str = "1024x1024") -> str:
    """
    Generate an image from text using api.airforce free endpoint.

    Parameters:
    - prompt (str): Text description of the image.
    - filename (str, optional): Output filename. Defaults to generated_{model}.png
    - model (str): One of the supported image models:
        ["dall-e-3", "imagen-3", "imagen-4", "sdxl", "flux-schnell", "flux-dev", "flux-krea-dev"] default uses "dall-e-3".
    - size (str): Image size. Default Uses "1024x1024" for best compatibility.

    Returns:
    - str: Path to the saved image or error message.
    """

    api_url = "https://api.airforce/v1/images/generations"
    headers = {"Content-Type": "application/json"}
    payload = {"model": model, "prompt": prompt, "size": size, "n": 1}

    try:
        resp = requests.post(api_url, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        if "error" in data:
            return f"API error: {data['error'].get('message', 'unknown error')}"

        if "data" not in data or not data["data"]:
            return f"No image generated. Response: {data}"

        result = data["data"][0]

        # Option 1: direct URL
        if result.get("url"):
            img_url = result["url"]
            img_resp = requests.get(img_url, timeout=60)
            img_resp.raise_for_status()
            raw = img_resp.content
        # Option 2: base64 JSON
        elif result.get("b64_json"):
            raw = base64.b64decode(result["b64_json"])
        else:
            return f"Unexpected format: {result}"

        # Open and save image
        image = Image.open(BytesIO(raw)).convert("RGBA")
        if not filename:
            filename = f"generated_{model}.png"
        elif not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            filename += ".png"

        image.save(filename)

        # Open automatically
        if os.name == "nt":
            os.startfile(filename)
        else:
            # macOS vs Linux opener
            opener = "open" if (hasattr(os, "uname") and os.uname().sysname == "Darwin") else "xdg-open"
            os.system(f"{opener} {filename}")

        return f"Image saved as {filename} (model={model}, size={size})"

    except requests.exceptions.RequestException as e:
        return f"Error during request: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"

# Example usage:
# if __name__ == "__main__":
#     result = generate_image(
#         "A realistic photo of a futuristic cyberpunk city skyline at sunset, ultra-detailed, cinematic lighting",
#         filename="cyberpunk_city.png"
#     )
#     print(result)

