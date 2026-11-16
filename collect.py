"""
新竹市 YouBike 即時車位蒐集程式
資料來源：交通部 TDX 運輸資料流通服務平臺 (https://tdx.transportdata.tw)

每執行一次，就抓一次「新竹市所有 YouBike 站點」的即時車數，
附加到 data/YYYY-MM-DD.csv（一天一個檔案）。

需要兩個環境變數（在 TDX 會員中心 > API 金鑰 取得）：
    TDX_CLIENT_ID
    TDX_CLIENT_SECRET
"""

import csv
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

CITY = "Hsinchu"  # 新竹市（新竹縣是 HsinchuCounty）
AUTH_URL = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
API_BASE = "https://tdx.transportdata.tw/api/basic/v2/Bike"
TW = timezone(timedelta(hours=8))

DATA_DIR = Path(__file__).parent / "data"
STATIONS_FILE = DATA_DIR / "stations.csv"

FIELDS = [
    "collected_at",        # 我們抓資料的時間（台灣時間）
    "station_uid",
    "service_status",      # 0 停止營運 / 1 正常 / 2 暫停
    "available_rent",      # 可借車數
    "available_return",    # 可還空位
    "general_bikes",       # 一般車
    "electric_bikes",      # 電輔車
    "src_update_time",     # 來源資料更新時間
]


def get_token() -> str:
    cid = os.environ.get("TDX_CLIENT_ID")
    secret = os.environ.get("TDX_CLIENT_SECRET")
    if not cid or not secret:
        sys.exit("缺少 TDX_CLIENT_ID / TDX_CLIENT_SECRET 環境變數")
    r = requests.post(
        AUTH_URL,
        data={"grant_type": "client_credentials", "client_id": cid, "client_secret": secret},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def get_json(path: str, token: str):
    url = f"{API_BASE}/{path}/City/{CITY}?$format=JSON"
    for attempt in range(3):  # 網路不穩時重試
        try:
            r = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=30)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            print(f"第 {attempt + 1} 次失敗：{e}")
            time.sleep(5)
    sys.exit("連續三次失敗，放棄這一輪")


def save_stations(token: str):
    """站點基本資料（名稱、座標、總車柱數）每天更新一次就夠。"""
    today = datetime.now(TW).date().isoformat()
    if STATIONS_FILE.exists():
        mtime = datetime.fromtimestamp(STATIONS_FILE.stat().st_mtime, TW).date().isoformat()
        if mtime == today:
            return
    stations = get_json("Station", token)
    with open(STATIONS_FILE, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["station_uid", "name", "lat", "lon", "capacity", "address"])
        for s in stations:
            w.writerow([
                s.get("StationUID"),
                (s.get("StationName") or {}).get("Zh_tw"),
                (s.get("StationPosition") or {}).get("PositionLat"),
                (s.get("StationPosition") or {}).get("PositionLon"),
                s.get("BikesCapacity"),
                (s.get("StationAddress") or {}).get("Zh_tw"),
            ])
    print(f"站點資料已更新：{len(stations)} 站")


def save_availability(token: str):
    now = datetime.now(TW)
    rows = get_json("Availability", token)
    out = DATA_DIR / f"{now.date().isoformat()}.csv"
    new_file = not out.exists()
    with open(out, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(FIELDS)
        for a in rows:
            detail = a.get("AvailableRentBikesDetail") or {}
            w.writerow([
                now.strftime("%Y-%m-%d %H:%M:%S"),
                a.get("StationUID"),
                a.get("ServiceStatus"),
                a.get("AvailableRentBikes"),
                a.get("AvailableReturnBikes"),
                detail.get("GeneralBikes"),
                detail.get("ElectricBikes"),
                a.get("SrcUpdateTime"),
            ])
    print(f"{now:%Y-%m-%d %H:%M} 已記錄 {len(rows)} 站 → {out.name}")


if __name__ == "__main__":
    DATA_DIR.mkdir(exist_ok=True)
    token = get_token()
    save_stations(token)
    save_availability(token)
