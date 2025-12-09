import cv2
import numpy as np
import os
import pickle
import glob
from screen_shot import ScreenCapture

class TemplateMatcher:
    def __init__(self, templates_file='digits.pkl', unknown_dir='unknowns' , dont_save_unknowns=False):
        self.templates_file = templates_file
        self.unknown_dir = unknown_dir
        self.dont_save_unknowns = dont_save_unknowns
        self.templates = {} 
        
        if not os.path.exists(self.unknown_dir):
            os.makedirs(self.unknown_dir)
            
        self.load_templates()

    def load_templates(self):
        if os.path.exists(self.templates_file):
            try:
                with open(self.templates_file, 'rb') as f:
                    data = pickle.load(f)
                
                # Automatically migrate old data format
                new_data = {}
                count = 0
                for k, v in data.items():
                    if isinstance(v, list):
                        new_data[k] = v
                        count += len(v)
                    else:
                        new_data[k] = [v]
                        count += 1
                
                self.templates = new_data
                print(f"系統: 已載入模板庫，共包含 {count} 個樣本。")
            except Exception as e:
                print(f"載入失敗: {e}，將建立新資料庫。")
                self.templates = {}
        else:
            print("系統: 尚未有模板檔案，請先進行訓練。")

    def save_templates(self):
        with open(self.templates_file, 'wb') as f:
            pickle.dump(self.templates, f)
        total = sum(len(v) for v in self.templates.values())
        print(f"系統: 模板已儲存 (目前共有 {total} 個變體樣本)。")

    def preprocess_cell_img(self, cell_img):
        """
        Convert single color cell image to binarized feature map
        Unified image processing logic to ensure consistency between Grid and Cell recognition
        """
        if len(cell_img.shape) == 3:
            gray = cv2.cvtColor(cell_img, cv2.COLOR_BGR2GRAY)
        else:
            gray = cell_img
            
        ch, cw = gray.shape
        # center crop to avoid borders
        crop_gray = gray[int(ch*0.2):int(ch*0.8), int(cw*0.25):int(cw*0.75)]
        _, thresh = cv2.threshold(crop_gray, 170, 255, cv2.THRESH_BINARY)
        return thresh

    def _match_feature(self, feature_img):
        """
        Internal method: Compare feature map with all templates, return (digit, score)
        """
        best_match_num = 0
        global_best_score = 0.0
        
        for num, template_list in self.templates.items():
            for tmpl in template_list:
                # Size correction
                if feature_img.shape != tmpl.shape:
                    resized_feature = cv2.resize(feature_img, (tmpl.shape[1], tmpl.shape[0]))
                else:
                    resized_feature = feature_img

                res = cv2.matchTemplate(resized_feature, tmpl, cv2.TM_CCOEFF_NORMED)
                score = res[0][0]
                
                if score > global_best_score:
                    global_best_score = score
                    best_match_num = num
        
        return best_match_num, global_best_score

    def recognize_cell(self, cell_img):
        """
        [New Feature] Recognize a single cell image
        img: Single cell BGR image (OpenCV format)
        return: Recognized digit (int), return 0 if low confidence
        """
        # 1. Preprocessing
        feature = self.preprocess_cell_img(cell_img)
        
        # 2. Matching
        num, score = self._match_feature(feature)
        
        # 3. Threshold check
        if score > 0.85:
            return num
        else:
            return 0

    def recognize_grid(self, img):
        """Recognize the entire large image (Grid)"""
        rows, cols = 14, 8
        grid = []
        
        h, w, _ = img.shape
        dy = h // rows
        dx = w // cols

        # print("Start multi-template recognition...") # Commented out for performance
        
        for r in range(rows):
            row_data = []
            for c in range(cols):
                # Slice
                y1, y2 = r * dy, (r + 1) * dy
                x1, x2 = c * dx, (c + 1) * dx
                cell = img[y1:y2, x1:x2]
                
                # 1. Preprocessing
                cell_feature = self.preprocess_cell_img(cell)
                
                # 2. Matching
                best_match_num, global_best_score = self._match_feature(cell_feature)
                
                # 3. Check and save
                if global_best_score > 0.9:
                    row_data.append(best_match_num)
                else:
                    # Save unknown images
                    if not self.dont_save_unknowns:
                        import time
                        timestamp = int(time.time() * 1000)
                        filename = os.path.join(self.unknown_dir, f"unknown_r{r}c{c}_{timestamp}.png")
                        cv2.imwrite(filename, cell_feature)
                    row_data.append(0)

            grid.append(row_data)
        return grid
    
    # ... (train_from_folder 保持不變) ...
    def train_from_folder(self):
        print(f"正在掃描 {self.unknown_dir} 資料夾進行增量學習...")
        image_paths = glob.glob(os.path.join(self.unknown_dir, "*.png"))
        count = 0
        for path in image_paths:
            filename = os.path.basename(path)
            name_part = filename.split('.')[0]
            digit_str = ""
            for char in name_part:
                if char.isdigit(): digit_str += char
                else: break
            
            if digit_str:
                num = int(digit_str)
                img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
                if img is None: continue
                if num not in self.templates: self.templates[num] = []
                
                is_duplicate = False
                for existing_tmpl in self.templates[num]:
                    if existing_tmpl.shape == img.shape:
                        if np.array_equal(existing_tmpl, img):
                            is_duplicate = True
                            break
                if not is_duplicate:
                    self.templates[num].append(img)
                    count += 1
                    print(f"新增模板: 數字 {num}")
                    os.remove(path)
                else:
                    os.remove(path)
            elif "unknown" in filename:
                pass
        if count > 0:
            self.save_templates()
            print(f"成功新增 {count} 個變體模板！")
        else:
            print("沒有發現新的已命名圖片。")

if __name__ == "__main__":
    # --- Configuration Area ---
    GAME_REGION = (720, 220, 480, 830) # Example values (x, y, w, h)
    MONITOR_ID = 2
    
    matcher = TemplateMatcher()
    
    print("\n[多重模板系統]")
    print("1. 辨識模式")
    print("2. 訓練模式 (增量學習)")
    
    choice = input("輸入: ").strip()
    
    if choice == '1':
        sc = ScreenCapture(monitor_idx=MONITOR_ID, region=GAME_REGION)
        print("1秒後截圖...")
        import time
        time.sleep(1)
        img = sc.capture()
        result = matcher.recognize_grid(img)
        
        print("\n結果:")
        for row in result:
            print(row)
            
        # Check if there are any 0s
        if any(0 in r for r in result):
            print("\n[!] Still unknown digits, please rename in unknowns folder and run mode 2")
        result = np.array(result)
        success_count = np.count_nonzero(result)
        total_count = result.size
        print(f"辨識完成: {success_count}/{total_count} 個數字成功辨識。")

    elif choice == '2':
        matcher.train_from_folder()
