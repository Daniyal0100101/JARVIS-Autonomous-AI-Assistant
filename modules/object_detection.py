import contextlib
import io
import torch
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_model_silently(model_path):
    """Load the YOLOv5 model for object detection silently."""
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        try:
            model = torch.hub.load('ultralytics/yolov5', 'custom', path=model_path)
            return model
        except Exception as e:
            logging.error(f"Error loading YOLOv5 model: {e}")
            return None

model_path = 'C:/Users/DANIYAL/OneDrive/Documents/Program & Projacts/Hands-on Projects/AI Projacts/Jarvis AI Assistant/Requirements/yolov5s.pt'
model = load_model_silently(model_path)
