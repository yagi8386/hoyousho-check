import requests
import time

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
}

# ====== 空き判定キーワード ======
KEYWORDS = ["空き状況カレンダー"]
OK_KEYWORDS = ["空き部屋がございません"]

#空き無し
status: int = 0

def send_line(message):
    data = {
        "to": USER_ID,
        "messages": [
            {"type": "text", "text": message}
        ]
    }
    requests.post(LINE_URL, headers=HEADERS, json=data)

# ====== メイン処理 ======
found = []

for name, url in URLS.items():
    print(f"チェック中: {name}")
    html = requests.get(url, timeout=10).text

    if any(word in html for word in KEYWORDS):
        found.append(f"{name}\n{url}")
        # 空きあり
        status = 1
    elif any(word in html for word in OK_KEYWORDS):
        found.append("OK_KEYWORDS")
    else:
        # アクセスエラー
        status = 2

    time.sleep(2)  # アクセス間隔（重要）

if status == 1:
    msg = "🏨 保養所に空きが出ました！\n\n" + "\n\n".join(found)
    send_line(msg)
    print("空きあり → LINE通知送信")
elif status == 2:
    msg = "アクセスエラー発生"
    send_line(msg)
    print("アクセスエラー発生 → LINE通知送信")
else:
    print("空きなし")
