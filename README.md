# 🪐 HappyFoodTime - 全台特色景點小吃導航地圖

HappyFoodTime 是一個具備未來感 Cyberpunk 霓虹視覺風格的多主題地圖導航網站。本專案將前端網頁託管於 **Cloudflare Pages**，資料庫建立於 **Supabase (PostgreSQL)** 雲端，並透過 **GitHub Actions** 實現每日自動化數據同步與備份。

---

## ⚡ 核心特色

1. **多主題地圖入口 (Multi-Theme Portal)**
   * 整合「我想吃的（Food）」、「我想住的（Stay）」、「我想去的（Play）」及「我的露營區（Camping）」四大分類。
   * 基於 Google Maps 精準 GPS 座標導航，一鍵跳轉行動裝置地圖 App。
2. **雲端與本地雙重防護架構 (Sync & Fallback)**
   * **動態加載**：網頁啟動時，會向 Supabase 雲端發送異步請求（Fetch）取得最新店家資訊。
   * **安全降級 (Fallback)**：若 Supabase 連線異常或未配置金鑰，前端將自動無感降級使用本地的 `stores_data.js` 備用檔案，保證網站 100% 不會出現白畫面。
3. **完全自動化排程同步 (GitHub Actions)**
   * 內建 GitHub Actions 定時任務，每天凌晨自動執行 Python 爬蟲抓取 Google Maps 清單，更新經緯度並寫入 Supabase 雲端，同時將備份檔案 commit 回倉庫。

---

## 📂 專案檔案結構

* `index.html` - 網頁主入口（包含 Cyberpunk 動態 Preloader 與版面結構）
* `app.js` - 前端邏輯控制（處理 API 請求、地圖標記篩選、數據排序與統計）
* `style.css` - 全站樣式檔（Cyberpunk 霓虹色彩系統與響應式排版）
* `stores_data.js` - 本地備用資料庫（Fallback 資料源）
* `update_database.py` - Google Maps 清單自動化爬蟲與 Supabase 同步腳本
* `update.bat` - 一鍵本機同步批次檔
* `schema.sql` - Supabase 資料庫 Table 初始化腳本
* `.env.example` - 本機環境變數配置範本

---

## 🚀 快速開始

### 1. 本地運行網頁
在專案根目錄下，使用 Python 開啟一個臨時本地伺服器：
```bash
python -m http.server 8080
```
開啟瀏覽器並造訪 `http://localhost:8080` 即可預覽網站。

### 2. 資料庫初始化 (Supabase)
1. 在您的 Supabase 專案中，前往 **SQL Editor** ➔ **New Query**。
2. 複製 `schema.sql` 內的程式碼並貼上，點選 **Run** 建立資料表。

### 3. 本機同步數據
1. 將 `.env.example` 複製並重新命名為 `.env`。
2. 在 `.env` 內填入您的 Supabase 專案金鑰：
   ```env
   SUPABASE_URL=https://您的專案ID.supabase.co
   SUPABASE_SERVICE_KEY=您的ServiceRole金鑰
   ```
3. 雙擊執行 `update.bat`。此腳本將自動爬取地圖清單，更新 GPS 經緯度，並直接 Upsert 寫入您的 Supabase 資料庫，同時更新本地的 `stores_data.js`。

---

## ⚙️ 雲端自動同步排程

本專案已配置 GitHub Actions 定時工作流：
* 工作流檔案位於：`.github/workflows/sync.yml`。
* **執行時間**：每日凌晨 2:00 (台灣時間)。
* **設定方式**：請在您的 GitHub 倉庫的 **Settings ➔ Secrets and variables ➔ Actions** 中，新增以下兩個 Secrets，排程即可開始工作：
  * `SUPABASE_URL` - 您的 Supabase 專案 URL。
  * `SUPABASE_SERVICE_KEY` - 您的 Supabase `service_role` 寫入金鑰。
