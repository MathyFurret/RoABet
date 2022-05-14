# Special thanks to Learn Code By Gaming

import cv2

class WinDetector:
    win_text_template = cv2.imread('img/1st_template.png', cv2.COLOR_BGR2GRAY)
    win_text_method = cv2.TM_CCOEFF_NORMED
    win_text_threshold = 0.8

    p1_template = cv2.imread('img/p1_template.png', cv2.COLOR_BGR2GRAY)
    p2_template = cv2.imread('img/p2_template.png', cv2.COLOR_BGR2GRAY)
    p_method = cv2.TM_CCOEFF_NORMED
    p_threshold = 0.9
    
    def find_win_text(self, img):
        result = cv2.matchTemplate(img, self.win_text_template, self.win_text_method)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        if max_val > self.win_text_threshold:
            result = cv2.matchTemplate(img, self.p1_template, self.p_method)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            if max_val > self.p_threshold:
                if 70 < max_loc[1] < 100:
                    return 1
                elif 220 < max_loc[1] < 250:
                    return 2
            result = cv2.matchTemplate(img, self.p2_template, self.p_method)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            if max_val > self.p_threshold:
                if 70 < max_loc[1] < 90:
                    return 2
                elif 220 < max_loc[1] < 240:
                    return 1
        return None
            
            