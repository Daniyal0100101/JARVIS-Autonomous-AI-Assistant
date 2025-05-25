import cv2
import mediapipe as mp
import pyautogui
import random
from pynput.mouse import Button, Controller
import numpy as np
import winsound

class HandGestureDetector:
    def __init__(self):
        self.mouse = Controller()
        self.screen_width, self.screen_height = pyautogui.size()
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            model_complexity=1,
            min_detection_confidence=0.8,
            min_tracking_confidence=0.8,
            max_num_hands=1
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.CLICK_THRESHOLD = 50
        self.DOUBLE_CLICK_THRESHOLD = 50
        self.RIGHT_CLICK_ANGLE = 90

    def get_angle(self, a, b, c):
        """Calculate angle between three points."""
        radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
        angle = np.abs(np.degrees(radians))
        return angle

    def get_distance(self, point1, point2):
        """Calculate distance between two points."""
        return np.linalg.norm(np.array(point1) - np.array(point2))

    def find_finger_tip(self, hand_landmarks):
        """Find the tip of the index finger."""
        if hand_landmarks:
            index_finger_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
            return index_finger_tip.x, index_finger_tip.y
        return None, None

    def move_mouse(self, index_finger_tip):
        """Move the mouse pointer based on the index finger tip position."""
        if index_finger_tip:
            x, y = index_finger_tip
            x = int(x * self.screen_width)
            y = int(y * self.screen_height)
            pyautogui.moveTo(x, y)

    def play_sound(self, frequency=1000, duration=100):
        """Play a sound to indicate a gesture."""
        winsound.Beep(frequency, duration)

    def detect_gesture(self, frame, landmark_list, index_finger_tip):
        """Detect gestures and perform corresponding actions."""
        if len(landmark_list) >= 21:
            thumb_index_dist = self.get_distance(landmark_list[4], landmark_list[8])

            if thumb_index_dist < self.CLICK_THRESHOLD:
                self.move_mouse(index_finger_tip)

            if self.is_left_click(landmark_list, thumb_index_dist):
                self.mouse.click(Button.left)
                cv2.putText(frame, "Left Click", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                self.play_sound()

            elif self.is_right_click(landmark_list, thumb_index_dist):
                self.mouse.click(Button.right)
                cv2.putText(frame, "Right Click", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                self.play_sound()

            elif self.is_double_click(landmark_list, thumb_index_dist):
                pyautogui.doubleClick()
                cv2.putText(frame, "Double Click", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
                self.play_sound()

            elif self.is_screenshot(landmark_list, thumb_index_dist):
                screenshot = pyautogui.screenshot()
                label = random.randint(1, 1000)
                screenshot.save(f'screenshot_{label}.png')
                cv2.putText(frame, "Screenshot Taken", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
                self.play_sound()

    def is_left_click(self, landmark_list, thumb_index_dist):
        """Detect left click gesture."""
        return (self.get_angle(landmark_list[5], landmark_list[6], landmark_list[8]) < 50 and
                thumb_index_dist > self.CLICK_THRESHOLD)

    def is_right_click(self, landmark_list, thumb_index_dist):
        """Detect right click gesture."""
        return (self.get_angle(landmark_list[5], landmark_list[6], landmark_list[8]) > self.RIGHT_CLICK_ANGLE and
                thumb_index_dist > self.CLICK_THRESHOLD)

    def is_double_click(self, landmark_list, thumb_index_dist):
        """Detect double click gesture."""
        return (self.get_angle(landmark_list[5], landmark_list[6], landmark_list[8]) < 50 and
                self.get_angle(landmark_list[9], landmark_list[10], landmark_list[12]) < 50 and
                thumb_index_dist > self.DOUBLE_CLICK_THRESHOLD)

    def is_screenshot(self, landmark_list, thumb_index_dist):
        """Detect screenshot gesture."""
        return (self.get_angle(landmark_list[5], landmark_list[6], landmark_list[8]) < 50 and
                self.get_angle(landmark_list[9], landmark_list[10], landmark_list[12]) < 50 and
                thumb_index_dist < self.CLICK_THRESHOLD)

    def start_detection(self):
        """Capture video and start gesture detection."""
        cap = cv2.VideoCapture(0)
        
        # Remove fullscreen and set a custom window size
        cv2.namedWindow('Frame', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Frame', 800, 600)

        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    print("Failed to grab frame.")
                    break
                
                frame = cv2.flip(frame, 1)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                processed = self.hands.process(frame_rgb)

                landmark_list = []
                index_finger_tip = None

                if processed.multi_hand_landmarks:
                    hand_landmarks = processed.multi_hand_landmarks[0]
                    self.mp_drawing.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                    
                    for lm in hand_landmarks.landmark:
                        landmark_list.append((lm.x, lm.y))
                    
                    index_finger_tip = self.find_finger_tip(hand_landmarks)

                self.detect_gesture(frame, landmark_list, index_finger_tip)

                cv2.imshow('Frame', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            cap.release()
            cv2.destroyAllWindows()
