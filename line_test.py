import json
import os
import requests
import time
from bs4 import BeautifulSoup

# ====== LINE設定 ======
CHANNEL_ACCESS_TOKEN = ""
USER_ID = ""

LINE_URL = "https://api.line.me/v2/bot/message/push"
HEADERS = {
    "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

# ====== 保養所URL（場所違い） ======
URLS = {
    "熱海": "https://as.its-kenpo.or.jp/apply/empty_new?s=PUVETnpJVFBrbG1KbFZuYzAxVFp5Vkhkd0YyWWZWR2JuOTJiblpTWjFKSGQ5a0hkdzFXWg%3D%3D",
    "横須賀": "https://as.its-kenpo.or.jp/apply/empty_new?s=PUlETnpJVFBrbG1KbFZuYzAxVFp5Vkhkd0YyWWZWR2JuOTJiblpTWjFKSGQ5a0hkdzFXWg%3D%3D",
    "河口湖": "https://as.its-kenpo.or.jp/apply/empty_new?s=PVlETzFFVFBrbG1KbFZuYzAxVFp5Vkhkd0YyWWZWR2JuOTJiblpTWjFKSGQ5a0hkdzFXWg%3D%3D",
    "館山": "https://as.its-kenpo.or.jp/apply/empty_new?s=PT1RTTJjVFBrbG1KbFZuYzAxVFp5Vkhkd0YyWWZWR2JuOTJiblpTWjFKSGQ5a0hkdzFXWg%3D%3D",
    "斑尾":"https://as.its-kenpo.or.jp/apply/empty_new?s=PT1BTjJjVFBrbG1KbFZuYzAxVFp5Vkhkd0YyWWZWR2JuOTJiblpTWjFKSGQ5a0hkdzFXWg%3D%3D",
}

# ====== 空き判定キーワード ======
KEYWORDS = ["空き状況カレンダー"]
OK_KEYWORDS = ["空き部屋がございません"]

def send_line(message):
    data = {
        "to": USER_ID,
        "messages": [
            {"type": "text", "text": message}
        ]
    }
    res = requests.post(LINE_URL, headers=HEADERS, json=data)
    if res.status_code != 200:
        print(res.text)
    
    print("LINE status:", res.status_code)
    print("LINE response:", res.text)

def check_hoyousho(name, html):
    soup = BeautifulSoup(html, "html.parser")

    select = soup.find("select", id="apply_join_time")

    if not select:
        print(f"{name}: 空きなし")
        return []

    dates = []
    for opt in select.find_all("option"):
        value = opt.get("value")
        text = opt.text.strip()
        if value:
            dates.append(text)

    print(f"{name}: 空きあり {len(dates)}日")
    return dates

def load_last_dates():
    try:
        with open("last_dates.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_last_dates(data):
    with open("last_dates.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ====== メイン処理 ======
last_dates = load_last_dates()
current_dates = {}
messages = []

has_error = False #正常

for name, url in URLS.items():
    
    print(f"チェック中: {name}")
    try:
        html = requests.get(url, timeout=10).text
        if any(word in html for word in OK_KEYWORDS):
            print(f"{name}: 空きなし")
            time.sleep(2)
            continue
    except requests.RequestException as e:
        print(f"{name}: 通信エラー {e}")
        has_error = True
        time.sleep(2)
        continue

    dates = check_hoyousho(name, html)
    current_dates[name] = dates
    
    old = set(last_dates.get(name, []))
    new = set(dates)

    # diff = sorted(new - old)
    diff = dates

    if diff:
        msg = f"🏨 {name} に空きがあります！\n\n"
        msg += "📅 空いている日付:\n"
        msg += "\n".join(diff)
        msg += f"\n\n🔗 {url}"
        messages.append(msg)
        print(f"{name} msg:", msg)

    time.sleep(2)

if messages:
    send_line("\n\n".join(messages))
    print("LINE通知送信")
elif has_error:
    msg = "アクセスエラー発生"
    send_line(msg)
    print("アクセスエラー発生 → LINE通知送信")
else:
    print("空きなし")

if not has_error:
    save_last_dates(current_dates)
else:
    print("エラーがあったため状態保存をスキップ")

# print("LINE_TOKEN exists:", bool(os.getenv("LINE_TOKEN")))
# print("LINE_USER_ID exists:", bool(os.getenv("LINE_USER_ID")))










