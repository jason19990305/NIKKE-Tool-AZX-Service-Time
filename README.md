# NIKKE Overlay Tool

這是一個專為《妮姬：勝利女神》(**NIKKE**) PC 版設計的輔助工具，透過影像辨識 (**Template Matching**) 來協助解謎或提供資訊。

## 📸 截圖預覽

載下來後執行 `main_overlay/main_overlay.exe` 即可

<img width="227" height="127" alt="image" src="https://github.com/user-attachments/assets/50a40c4e-1d72-4c2d-8608-54aa3a95b9c6" />

---

也可以到右側 Release 頁面下載執行檔

<img width="50%" alt="image" src="https://github.com/user-attachments/assets/3e3bf5a9-f7c4-4dc3-aa6e-bef05768c172" />


---

如果正常運作畫面上會出現紅框

<img width="209" height="426" alt="image" src="https://github.com/user-attachments/assets/4515c019-b217-411c-af31-a2f35394cd71" />

參考影片 : https://youtu.be/YGARDfeViOE?si=J9iWsOyhFpJ1NcRu


## ⚠️ 重要注意事項

本工具是基於**影像模板匹配**技術開發，因此對遊戲畫面設定非常敏感。為了確保工具能正常運作，請務必遵守以下設定：

1.  **平台**：必須使用 **PC 版本**。
2.  **解析度**：必須設定為 **1920x1080**。
3.  **顯示模式**：必須使用 **全螢幕 (Full Screen)** 
4.  **螢幕** : 工具預設使用副螢幕，如果有兩個螢幕須將 **NIKKE** 視窗放在副螢幕，只有一個螢幕也可以直接使用

> [!WARNING]
> 如果您的遊戲解析度、渲染比例或字體大小與開發環境不同，影像辨識極有可能失效。本工具不保證在非標準 1080p 環境下能正常運作。

## 📦 如何使用

1.  前往 `main_overlay` 資料夾。
2.  執行 `main_overlay.exe`。
3.  工具啟動後會顯示在遊戲畫面之上。

## 🛠️ 開發資訊

本工具使用 **Python** 編寫，並透過 **PyInstaller** 打包。
主要依賴：
-   **OpenCV** (影像處理)
-   **PyQt5** (介面覆蓋)
-   **MSS** (螢幕截圖)
