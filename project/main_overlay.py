# NIKKE-Tool-AZX-Service-Time
# Copyright (C) 2025 jason19990305
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import sys
import time
import mss
import cv2
import numpy as np
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QRect
from PyQt5.QtGui import QPainter, QPen, QColor, QFont
from PyQt5.QtWidgets import QApplication, QWidget

from screen_shot import ScreenCapture
from template_matcher import TemplateMatcher
from solver import Solver

# ==========================================
# Configuration Area
# ==========================================
GAME_REGION = (720, 220, 480, 830) 
MONITOR_ID = 2
ROWS = 14
COLS = 8

class GameWorker(QThread):
    # Emit global coordinates (Global X, Global Y, W, H)
    solution_found = pyqtSignal(int, int, int, int)

    def __init__(self):
        super().__init__()
        self.running = True
        
        # Cache needed for differential updates
        self.cell_cache_img = {} 
        self.current_grid = [[0]*COLS for _ in range(ROWS)]
        self.first_run = True

    def run(self):
        cap = ScreenCapture(monitor_idx=MONITOR_ID, region=GAME_REGION)
        matcher = TemplateMatcher(templates_file='digits.pkl')
        solver = Solver(target_sum=10)
        
        cell_w = GAME_REGION[2] // COLS
        cell_h = GAME_REGION[3] // ROWS

        # Calculate absolute offset for Monitor 2
        offset_left = 0
        offset_top = 0
        with mss.mss() as sct:
            if MONITOR_ID < len(sct.monitors):
                monitor = sct.monitors[MONITOR_ID]
                offset_left = monitor["left"]
                offset_top = monitor["top"]
        base_x = offset_left + GAME_REGION[0]
        base_y = offset_top + GAME_REGION[1]

        print("差異更新模式啟動...")
        
        while self.running:
            try:
                # 1. Capture screen
                img = cap.capture()
                gray_full = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                
                updated_count = 0

                # 2. Iterate to check cell changes
                for r in range(ROWS):
                    for c in range(COLS):
                        y1, y2 = r * cell_h, (r + 1) * cell_h
                        x1, x2 = c * cell_w, (c + 1) * cell_w
                        
                        # Extract grayscale cell (for difference comparison)
                        gap_x = int(cell_w * 0.1)
                        gap_y = int(cell_h * 0.1)
                        gray_cell = gray_full[y1+gap_y:y2-gap_y, x1+gap_x:x2-gap_x]

                        need_ocr = False
                        
                        if self.first_run:
                            need_ocr = True
                        else:
                            last_img = self.cell_cache_img.get((r, c))
                            if last_img is not None:
                                diff = cv2.absdiff(gray_cell, last_img)
                                if np.mean(diff) > 5: # Change threshold
                                    need_ocr = True
                            else:
                                need_ocr = True

                        if need_ocr:
                            # === Simplified here! Directly call the new function ===
                            # Extract color cell image
                            color_cell = img[y1:y2, x1:x2]
                            
                            # Let TemplateMatcher recognize this cell
                            num = matcher.recognize_cell(color_cell)
                            
                            self.current_grid[r][c] = num
                            
                            # Update Cache
                            self.cell_cache_img[(r, c)] = gray_cell
                            updated_count += 1

                self.first_run = False
                
                # 3. Solve
                solution = solver.solve(self.current_grid)

                if solution:
                    r1, c1, r2, c2 = solution
                    
                    # Double check if the solution is valid
                    if self.current_grid[r1][c1] != 0 and self.current_grid[r2][c2] != 0:
                        min_r, max_r = min(r1, r2), max(r1, r2)
                        min_c, max_c = min(c1, c2), max(c1, c2)
                        
                        global_x = base_x + (min_c * cell_w)
                        global_y = base_y + (min_r * cell_h)
                        draw_w = (max_c - min_c + 1) * cell_w
                        draw_h = (max_r - min_r + 1) * cell_h
                        
                        self.solution_found.emit(global_x, global_y, draw_w, draw_h)
                    else:
                        self.solution_found.emit(-1, -1, 0, 0)
                else:
                    self.solution_found.emit(-1, -1, 0, 0)
                
                time.sleep(0.01)

            except Exception as e:
                print(f"Worker Error: {e}")
                time.sleep(1)

    def stop(self):
        self.running = False
        self.wait()

class GameOverlay(QWidget):
    def __init__(self):
        super().__init__()
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

        app = QApplication.instance()
        screens = app.screens()
        
        if len(screens) > MONITOR_ID - 1:
            self.target_screen_geo = screens[MONITOR_ID - 1].geometry()
            self.setGeometry(self.target_screen_geo)
        else:
            self.target_screen_geo = screens[0].geometry()
            self.setGeometry(self.target_screen_geo)

        self.target_rect = None
        self.worker = GameWorker()
        self.worker.solution_found.connect(self.update_rect)
        self.worker.start()
        self.show()

    def update_rect(self, gx, gy, w, h):
        if gx == -1:
            self.target_rect = None
        else:
            local_x = gx - self.target_screen_geo.x()
            local_y = gy - self.target_screen_geo.y()
            self.target_rect = QRect(local_x, local_y, w, h)
        self.update()

    def paintEvent(self, event):
        if self.target_rect:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            pen = QPen(QColor(255, 0, 0), 5) 
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush) 
            painter.drawRect(self.target_rect)

    def closeEvent(self, event):
        self.worker.stop()
        super().closeEvent(event)

def main():
    try:
        from PyQt5.QtWidgets import QApplication
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    except:
        pass

    app = QApplication(sys.argv)
    overlay = GameOverlay()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()