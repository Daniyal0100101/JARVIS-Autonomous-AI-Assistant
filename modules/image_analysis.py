import base64
import os
import mimetypes
from typing import Optional
from google import genai
from dotenv import load_dotenv

# Load environment variables (expects GEMINI_API_KEY in .env or environment)
load_dotenv()

# Initialize client once (can be reused across calls)
_client: Optional[genai.Client] = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not found in environment variables.")
        _client = genai.Client(api_key=api_key)
    return _client


def _detect_mime(image_path: str) -> str:
    """Infer MIME type from file extension using mimetypes."""
    mime, _ = mimetypes.guess_type(image_path)
    if not mime:
        raise ValueError(f"Could not detect MIME type for {image_path}")
    return mime


def analyze_image(
    image_path: str,
    visual_query: Optional[str] = None,
) -> str:
    """
    Analyze an image using multimodal AI and return either a general overview or answer a specific question.

    Args:
        image_path: Path to the image file.
        visual_query: If provided, asks a specific question about the image.
                    If None, returns a brief factual overview of the image content.
    Returns:
        str: Direct answer about image from the model (no extra commentary).
    """

    model = "gemini-2.5-flash-lite" # or "gemini-2.5-flash" for more detailed responses
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")

    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")
    mime = _detect_mime(image_path)

    # Build user prompt
    if visual_query:
        user_text = (
            "You are an image analyst. Respond only with the requested information.\n\n"
            f"Question: {visual_query}\n"
            "Answer concisely with only the direct factual answer, nothing else."
        )
    else:
        user_text = (
            "You are an image analyst. Provide a concise factual overview of what is visible in the image. "
            "Limit your response to 2–3 short sentences. No elaboration."
        )

    # Get client and call Gemini
    client = _get_client()
    try:
        response = client.models.generate_content(
            model=model,
            contents=[
                {"text": user_text},
                {"inline_data": {"mime_type": mime, "data": img_b64}},
            ],
        )
    except Exception as e:
        raise RuntimeError(f"API call failed: {e}") from e

    # Extract response text
    ans = (response.text or "").strip()
    if not ans:
        raise RuntimeError("Model returned an empty response")
    return ans

# Example usage (standalone test)
# print(analyze_image(image_path='current_screen_for_analysis.png', visual_query='What is in this image?'))
