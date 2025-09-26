import logging, os
from ultralytics import YOLO

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_model_silently(model_path: str):
    try:
        if not os.path.isfile(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        return YOLO(model_path)  # v8/11 runtime
    except Exception as e:
        logging.error(f"Error loading YOLO model: {e}")
        return None

MODEL_PATH = os.path.join("Requirements", "yolo11n.pt")  # <- NEW file
model = load_model_silently(MODEL_PATH)
