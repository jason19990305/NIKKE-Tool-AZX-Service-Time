# screen_shot.py
import cv2
import numpy as np
import mss

class ScreenCapture:
    def __init__(self, monitor_idx=1, region=None):
        """
        monitor_idx: int, Monitor index (1 for main, 2 for secondary...)
        region: tuple (x, y, w, h), Coordinates relative to the screen's top-left corner.
                If not provided, capture the full screen.
        """
        self.sct = mss.mss()
        self.monitor_idx = monitor_idx
        self.region = region
        
        # Check if monitor exists
        if len(self.sct.monitors) <= self.monitor_idx:
            print(f"警告: 找不到螢幕 {self.monitor_idx}，將使用主螢幕 (1)")
            self.monitor_idx = 1

    def capture(self):
        """
        Capture specified region of specified monitor, return OpenCV BGR image
        """
        # Get specified monitor info (including left, top offsets)
        monitor = self.sct.monitors[self.monitor_idx]
        
        if self.region:
            # region = (x, y, w, h) -> Coordinates relative to that screen
            # mss requires absolute coordinates (top, left, width, height)
            capture_area = {
                "top": monitor["top"] + self.region[1],
                "left": monitor["left"] + self.region[0],
                "width": self.region[2],
                "height": self.region[3],
                "mon": self.monitor_idx,
            }
        else:
            # Capture entire screen
            capture_area = monitor

        # Capture screen
        sct_img = self.sct.grab(capture_area)
        
        # Convert to Numpy array (mss returns BGRA, including alpha)
        frame = np.array(sct_img)
        
        # Remove Alpha channel (BGRA -> BGR), OpenCV usually doesn't need transparency
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        
        return frame

if __name__ == "__main__":
    # --- Test Block ---
    
    # List all monitor info
    with mss.mss() as sct:
        print("偵測到的螢幕列表:")
        for i, m in enumerate(sct.monitors):
            if i == 0: continue # 0 represents the sum of all screens, skip
            print(f"螢幕 {i}: {m}")

    # Set the monitor you want to test (1 or 2...)
    TARGET_MONITOR = 2 
    
    # Set region (x, y, w, h) -> Distance relative to top-left of that screen
    # e.g. Capture a middle block of the secondary screen:
    TEST_REGION = (500, 100, 400, 400) 

    sc = ScreenCapture(monitor_idx=TARGET_MONITOR, region=TEST_REGION)
    
    print(f"\n正在擷取螢幕 {TARGET_MONITOR} 的區域 {TEST_REGION}...")
    img = sc.capture()
    
    cv2.imshow(f"Monitor {TARGET_MONITOR} Capture", img)
    print("按任意鍵關閉視窗...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()