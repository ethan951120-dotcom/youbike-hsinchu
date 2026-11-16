# 新竹 YouBike 資料蒐集

每 10 分鐘自動抓一次新竹市所有 YouBike 站點的可借車數和可還空位，存成 CSV。
程式在 GitHub 的伺服器上跑，**你的電腦不用一直開著**。

## 設定步驟（約 15 分鐘，一次就好）

### 1. 申請 TDX API 金鑰
1. 到 https://tdx.transportdata.tw 註冊會員（選「一般會員」）。
2. 收信驗證後，等平台審核通過（通常很快，最慢幾天）。
3. 登入 → 右上角「會員中心」→「資料服務」→「API 金鑰」→ 按「編輯」，
   把 **Client Id** 和 **Client Secret** 記下來（不要給別人看）。

### 2. 建立 GitHub repo
1. 在 GitHub 建一個新 repo，例如 `youbike-hsinchu`。
   **設成 Public**：公開 repo 的 GitHub Actions 免費、不限時數。
   每 10 分鐘跑一次，一個月約 4,300 分鐘，Private repo 的免費額度不夠。
   金鑰會放在 Secrets 裡，公開 repo 也看不到。
2. 把這個資料夾的所有檔案上傳，包含 `.github/workflows/collect.yml`。

### 3. 放入金鑰
repo 頁面 → Settings → Secrets and variables → Actions → New repository secret，新增兩個：
- `TDX_CLIENT_ID`：你的 Client Id
- `TDX_CLIENT_SECRET`：你的 Client Secret

再到 Settings → Actions → General → Workflow permissions，選 **Read and write permissions** → Save。

### 4. 啟動
repo → Actions 分頁 → 左邊點「Collect YouBike data」→「Run workflow」手動跑一次。
成功的話，`data/` 資料夾會出現 `stations.csv` 和今天日期的 CSV。
之後它就會每 10 分鐘自動執行。

## 資料格式

`data/stations.csv`：站點基本資料
| 欄位 | 意思 |
|---|---|
| station_uid | 站點代號 |
| name | 站名 |
| lat, lon | 座標 |
| capacity | 總車柱數 |

`data/YYYY-MM-DD.csv`：每 10 分鐘一筆，每站一列
| 欄位 | 意思 |
|---|---|
| collected_at | 抓取時間（台灣時間） |
| station_uid | 站點代號 |
| service_status | 1 正常、2 暫停、0 停止 |
| available_rent | 可借車數 |
| available_return | 可還空位 |
| general_bikes / electric_bikes | 一般車 / 電輔車數量 |

## 在 Colab 讀資料

```python
import pandas as pd, glob
# 先把 repo clone 下來：!git clone https://github.com/你的帳號/youbike-hsinchu
files = sorted(glob.glob("youbike-hsinchu/data/20*.csv"))
df = pd.concat(pd.read_csv(f, parse_dates=["collected_at"]) for f in files)
stations = pd.read_csv("youbike-hsinchu/data/stations.csv")
df = df.merge(stations, on="station_uid")
df[df["name"].str.contains("交大|陽明交通")].head()
```

## 在自己電腦測試（可選）

```bash
pip install requests
export TDX_CLIENT_ID=你的ID          # Windows PowerShell: $env:TDX_CLIENT_ID="你的ID"
export TDX_CLIENT_SECRET=你的Secret
python collect.py
```
