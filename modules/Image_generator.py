import requests
from PIL import Image
from io import BytesIO
import os

def get_middle_words(prompt):
    # Split the prompt into words
    words = prompt.split()
    
    # Find the middle two words
    if len(words) < 2:
        # If the prompt has fewer than 2 words, use the entire prompt
        return prompt
    elif len(words) % 2 == 0:
        # If even number of words, return the two middle words
        middle_index = len(words) // 2
        return f"{words[middle_index - 1]}_{words[middle_index]}"
    else:
        # If odd number of words, return the middle word
        middle_index = len(words) // 2
        return words[middle_index]

def generate_image(prompt, api_url='https://api.airforce/v1/imagine2'):
    try:
        print("Generating image...")

        # Get the middle two words of the prompt
        middle_words = get_middle_words(prompt)
        
        # Generate the filename using the middle two words
        filename = f'{middle_words}_generated_image.png'

        # Define the parameters for the request
        params = {'prompt': prompt}
        
        # Send the GET request
        response = requests.get(api_url, params=params)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Open the image from the response content
            image = Image.open(BytesIO(response.content))
            
            # Save the image to a file
            image.save(filename)
            
            # Open the image file using the default viewer
            if os.name == 'nt':  # Windows
                os.startfile(filename)
            else:  # macOS or Linux
                os.system(f'open {filename}' if os.name == 'posix' else f'xdg-open {filename}')
            
            return f"I've saved the image as '{filename}' for you!"
        else:
            return f"Failed to retrieve image. Status code: {response.status_code}"
    
    except requests.exceptions.RequestException as e:
        # Handle any request-related exceptions
        print(f"Error during request: {e}")
        return "I'm unable to process the image request due to an error."
    
    except IOError as e:
        # Handle any image-related exceptions
        print(f"Error saving or opening the image: {e}")
        return "An error occurred while processing the image."
