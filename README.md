# 抖音爬蟲工具 (Douyin Spider) 

一個功能強大的抖音視頻下載工具，支援批量下載抖音用戶的所有視頻。

## 🎯 功能特點

- **批量下載**: 自動獲取並下載指定抖音用戶的所有視頻
- **智能去重**: 自動檢測已下載的視頻，避免重複下載
- **進度追蹤**: 實時顯示下載進度和狀態
- **錯誤重試**: 自動重試失敗的下載任務
- **圖形界面**: 提供美觀的命令行風格 GUI 界面
- **歷史記錄**: 保存下載歷史，支援斷點續傳
- **環境配置**: 內建環境變數配置工具

## 📋 系統需求


- Python 3.7+
- Windows 10/11
- 穩定的網絡連接

## 🚀 安裝說明

### 1. 克隆或下載項目

```bash
git clone [項目地址]
cd 抖音爬蟲
```

### 2. 安裝依賴套件

```bash
pip install -r requirements.txt
```

或手動安裝以下套件：

```bash
pip install DrissionPage requests python-dotenv PyQt5 pynput pygetwindow
```

### 3. 配置環境變數

創建 `.env` 文件並設置以下變數：

```env
DOUYIN_COOKIE=你的抖音Cookie
DOUYIN_REFERER=你的抖音Referer
DOUYIN_UA=你的User-Agent
```

## 🔧 使用方法

### 方法一：使用圖形界面 (推薦)

```bash
python gui.py
```

啟動後會顯示一個美觀的命令行風格界面，包含以下功能：

- **輸入抖音網址**: 直接輸入目標用戶的抖音頁面網址
- **查看配置**: 輸入 `headers` 查看當前環境變數設置狀態
- **創建配置**: 輸入 `create-env` 引導式創建 `.env` 文件
- **清空重置**: 輸入 `clear` 清空界面並重置

### 方法二：使用命令行

```bash
python Drissionpage.py
```

直接運行爬蟲腳本，使用預設的抖音網址。

## 📖 詳細使用指南

### 1. 獲取必要的瀏覽器信息

#### 獲取 Cookie
1. 打開瀏覽器，訪問抖音網站並登錄
2. 按 F12 打開開發者工具
3. 切換到 Network 標籤
4. 刷新頁面，找到任意請求
5. 在請求標頭中找到 `Cookie` 字段並複製其值

#### 獲取 User-Agent
1. 在開發者工具的 Network 標籤中
2. 找到任意請求的 `User-Agent` 字段並複製

#### 獲取 Referer
1. 訪問目標抖音用戶的頁面
2. 複製瀏覽器地址欄的完整 URL

### 2. 配置環境變數

#### 方法一：使用內建工具
1. 運行 `python gui.py`
2. 輸入 `create-env`
3. 按照提示依次輸入 Cookie、Referer 和 User-Agent

#### 方法二：手動創建
1. 在項目根目錄創建 `.env` 文件
2. 添加以下內容：

```env
DOUYIN_COOKIE=sessionid=abc123; ttwid=def456; msToken=ghi789
DOUYIN_REFERER=https://www.douyin.com/user/MS4wLjABAAAA...
DOUYIN_UA=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...
```

### 3. 開始下載

1. 運行 `python gui.py`
2. 輸入目標抖音用戶的網址
3. 等待程序自動檢測用戶總視頻數量
4. 程序會自動下滑頁面加載所有視頻
5. 開始批量下載視頻到 `douyin` 文件夾

## 📁 文件結構

```
抖音爬蟲/
├── README.md              # 項目說明文件
├── Drissionpage.py        # 核心爬蟲邏輯
├── gui.py                 # 圖形界面
├── requirements.txt       # 依賴套件列表
├── .env                   # 環境變數配置 (需手動創建)
├── douyin/                # 下載文件夾
│   ├── history.json       # 下載歷史記錄
│   └── [下載的視頻文件]
└── .gitignore
```

## ⚙️ 配置說明

### 環境變數詳解

- **DOUYIN_COOKIE**: 抖音網站的 Cookie，用於身份驗證
- **DOUYIN_REFERER**: 請求來源頁面，通常是抖音用戶頁面
- **DOUYIN_UA**: 瀏覽器 User-Agent，模擬真實瀏覽器訪問

### 下載設置

- **文件命名**: 視頻按 `序號_標題.mp4` 格式命名
- **去重機制**: 自動檢測已下載的視頻，避免重複下載
- **重試機制**: 下載失敗時自動重試最多 3 次
- **歷史記錄**: 下載記錄保存在 `douyin/history.json`

## 🔍 故障排除

### 常見問題

1. **無法獲取視頻數量**
   - 檢查網絡連接
   - 確認環境變數設置正確
   - 嘗試重新獲取 Cookie

2. **下載失敗**
   - 檢查網絡穩定性
   - 確認目標視頻可正常播放
   - 嘗試重新配置環境變數

3. **界面無法啟動**
   - 確認已安裝 PyQt5
   - 檢查 Python 版本是否支援

### 調試模式

運行時會顯示詳細的日誌信息，包括：
- 頁面加載狀態
- 視頻數量檢測
- 下載進度
- 錯誤信息

## 📝 更新日誌

### v1.0.0
- 初始版本發布
- 支援批量下載抖音視頻
- 提供圖形界面
- 智能去重和錯誤重試

## 🤝 貢獻指南

歡迎提交 Issue 和 Pull Request 來改進這個項目。

## 📄 授權條款

本項目僅供學習和研究使用，請遵守相關法律法規和網站使用條款。

## ⚠️ 免責聲明

- 本工具僅供個人學習和研究使用
- 請尊重原創作者的版權
- 不得用於商業用途
- 使用者需自行承擔使用風險
---

**注意**: 使用本工具時請遵守抖音的使用條款和相關法律法規。
