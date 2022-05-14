import time
import json
import sys
from .win_detection import WinDetector
from .screenshot import WindowCapture

def win_detector_loop():
    detector = WinDetector()
    capture = WindowCapture()

    while True:
        img = capture.get_screenshot()
        result = detector.find_win_text(img)
        if result:
            json.dump({'winner': result}, sys.stdout)
            return
        time.sleep(0.04)

if __name__ == "__main__":
    win_detector_loop()
