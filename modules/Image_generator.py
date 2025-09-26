import requests
from PIL import Image
from io import BytesIO
import os

def generate_image(prompt: str, filename: str = None) -> str:
    """
    Generates an image based on the given prompt using an external API.
    Args:
        prompt (str): The text prompt to generate the image.
        filename (str, optional): The filename to save the generated image. If not provided, a default name will be used.
    
    Returns:
        str: A message indicating the status of the image generation and saving process.
    """

    try:
        api_url='https://api.airforce/v1/imagine2'
        print("Generating image...")

        # Define the parameters for the request
        params = {'prompt': prompt}
        
        # Send the GET request
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()

        # Open the image using PIL
        image = Image.open(BytesIO(response.content))
        
        # Define a default filename if none is provided
        if not filename:
            filename = "generated_image.png"
        else:
            # Ensure the filename has a valid image extension
            if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                filename += ".png"
        
        # Save the image to the specified file
        image.save(filename)
        
        # Open the image file using the default viewer
        if os.name == 'nt':  # Windows
            os.startfile(filename)
        else:  # macOS and Linux
            opener = "open" if os.uname().sysname == "Darwin" else "xdg-open"
            os.system(f"{opener} {filename}")
    
    except requests.exceptions.RequestException as e:
        # Handle any request-related exceptions
        return f"Error during image generation request: {e}"
    
    except IOError as e:
        # Handle any image-related exceptions
        return f"Error saving or opening the image: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"
