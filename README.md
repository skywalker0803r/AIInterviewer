# AI 面試官

這是一個 AI 驅動的面試模擬應用程式，旨在幫助使用者準備職位面試。它允許使用者搜尋職位，然後由 AI 擔任面試官，提出問題並根據使用者的回答提供即時回饋和最終報告。

## 功能特色

*   **職位搜尋**: 透過關鍵字搜尋 104 人力銀行上的職位。
*   **AI 面試官**: AI 會根據所選職位生成面試問題。
*   **語音轉文字 (STT)**: 將使用者的語音回答即時轉錄為文字。
*   **文字轉語音 (TTS)**: AI 面試官的問題會以語音形式播放。
*   **即時對話**: 透過 WebSocket 實現使用者與 AI 之間的即時語音互動。
*   **面試評估**: AI 會根據預設的評估維度（如技術深度、溝通能力等）對使用者的回答進行評分。
*   **面試報告**: 面試結束後，生成一份包含總體評分和各維度評分的報告。

## 使用技術

### 後端 (Backend)

*   **FastAPI**: 用於構建高效能的 API 服務。
*   **Python**: 主要開發語言。
*   **Whisper**: 用於語音轉文字 (STT)。
*   **gTTS**: 用於文字轉語音 (TTS)。
*   **DeepFace**: (已引入但目前未啟用) 用於潛在的情緒辨識。
*   **httpx**: 非同步 HTTP 客戶端，用於呼叫外部 API (如 104 和 Gemini)。
*   **BeautifulSoup4**: 用於解析 HTML (儘管目前主要使用 104 的 JSON API)。
*   **python-dotenv**: 用於管理環境變數。
*   **Docker**: 用於容器化應用程式，提供一致的開發和部署環境。
*   **Google Gemini API**: 用於生成面試問題和評估使用者回答。

### 前端 (Frontend)

*   **HTML5**: 頁面結構。
*   **CSS3 (Bootstrap 5)**: 頁面樣式和響應式佈局。
*   **JavaScript**: 實現前端邏輯，包括與後端 API 和 WebSocket 的互動，以及麥克風錄音功能。

## 環境建置與執行

### 前置條件

*   Docker 和 Docker Compose (推薦)
*   Python 3.10+ (如果不安裝 Docker，則需要手動安裝後端依賴)
*   pip

### 步驟

1.  **複製專案**

    ```bash
    git clone https://github.com/your-username/AIInterviewer.git
    cd AIInterviewer
    ```

2.  **設定環境變數**

    在 `backend` 資料夾中建立一個 `.env` 檔案，並加入您的 Google Gemini API Key：

    ```
    GEMINI_API_KEY=YOUR_GEMINI_API_KEY
    ```

    您可以從 [Google AI Studio](https://aistudio.google.com/app/apikey) 獲取您的 Gemini API Key。

3.  **啟動後端服務 (使用 Docker Compose)**

    在專案根目錄下執行：

    ```bash
    docker-compose up --build
    ```

    這將會建置 Docker 映像檔並啟動後端服務。後端服務將在 `http://127.0.0.1:8002` 上運行。

    *   **注意**: 首次啟動時，Whisper 模型會被下載，這可能需要一些時間。

4.  **啟動前端**

    直接在瀏覽器中開啟 `frontend/index.html` 檔案即可。

    *   **注意**: 由於瀏覽器的安全限制，您可能需要使用一個本地伺服器（例如 VS Code 的 Live Server 擴充功能）來開啟 `index.html`，以確保 WebSocket 連線和麥克風權限正常運作。

## 使用說明

1.  **搜尋職位**: 在首頁的輸入框中輸入職位關鍵字（例如：「前端工程師」），然後點擊「搜尋職缺」按鈕。
2.  **選擇職位**: 從搜尋結果中點擊一個職位卡片來選擇您要面試的職位。
3.  **開始面試**: 點擊「開始面試」按鈕。AI 面試官會開始提問。
4.  **回答問題**:
    *   點擊紅色的麥克風按鈕開始錄音。
    *   說出您的回答。
    *   再次點擊麥克風按鈕停止錄音。您的回答會被轉錄並發送給 AI。
    *   AI 會處理您的回答並提出下一個問題。
5.  **結束面試**: 隨時點擊「結束面試」按鈕來結束面試並查看面試報告。
6.  **查看報告**: 面試報告會顯示您的總體評分以及各維度的評分。
7.  **重新開始**: 點擊「重新開始面試」按鈕可以回到職位搜尋頁面。

## 專案結構

```
AIInterviewer/
├── .git/
├── .gitignore
├── README.md             # 本文件
├── backend/              # 後端服務相關程式碼
│   ├── docker-compose.yml
│   ├── Dockerfile
│   ├── main.py           # FastAPI 應用程式主文件
│   ├── requirements.txt  # Python 依賴套件
│   ├── __pycache__/
│   └── static/           # 靜態檔案 (TTS 音訊)
│       └── audio/
└── frontend/             # 前端網頁程式碼
    ├── index.html        # 網頁主頁面
    └── script.js         # 前端 JavaScript 邏輯
```

## 未來增強

*   整合 DeepFace 進行情緒辨識，為面試評估提供更多維度。
*   更複雜的評分邏輯和面試流程控制。
*   支援更多語言。
*   提供面試歷史記錄和進度追蹤。
*   優化前端 UI/UX。
