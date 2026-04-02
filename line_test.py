import json
import os
import time
import asyncio
import aiohttp
import random
from bs4 import BeautifulSoup

if not os.path.exists("last_dates.json"):
    with open("last_dates.json", "w") as f:
        f.write("{}")

# ====== Slack設定 ======
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

# ====== 保養所URL ======
URLS = {
    "熱海": "https://as.its-kenpo.or.jp/apply/empty_new?s=PUVETnpJVFBrbG1KbFZuYzAxVFp5Vkhkd0YyWWZWR2JuOTJiblpTWjFKSGQ5a0hkdzFXWg%3D%3D",
    "横須賀": "https://as.its-kenpo.or.jp/apply/empty_new?s=PUlETnpJVFBrbG1KbFZuYzAxVFp5Vkhkd0YyWWZWR2JuOTJiblpTWjFKSGQ5a0hkdzFXWg%3D%3D",    
    "ラビスタ熱海": "https://as.its-kenpo.or.jp/apply/empty_new?s=PUlUTzFJVFBrbG1KbFZuYzAxVFp5Vkhkd0YyWWZWR2JuOTJiblpTWjFKSGQ5a0hkdzFXWg%3D%3D",
    "鬼怒川": "https://as.its-kenpo.or.jp/apply/empty_new?s=PU1UTzFJVFBrbG1KbFZuYzAxVFp5Vkhkd0YyWWZWR2JuOTJiblpTWjFKSGQ5a0hkdzFXWg%3D%3D",
    "和奏林": "https://as.its-kenpo.or.jp/apply/empty_new?s=PT1RTzFjVFBrbG1KbFZuYzAxVFp5Vkhkd0YyWWZWR2JuOTJiblpTWjFKSGQ5a0hkdzFXWg%3D%3D",
    "館山": "https://as.its-kenpo.or.jp/apply/empty_new?s=PT1RTTJjVFBrbG1KbFZuYzAxVFp5Vkhkd0YyWWZWR2JuOTJiblpTWjFKSGQ5a0hkdzFXWg%3D%3D",
}

OK_KEYWORDS = ["空き部屋がございません"]

# ====== User-Agent（複数でランダム）=====
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)",
]

SAVE_PATH = "last_dates.json"

# ====== Slack送信 ======
def send_slack(message):
    if not SLACK_WEBHOOK_URL:
        print("Slack Webhook 未設定")
        return

    import requests
    requests.post(SLACK_WEBHOOK_URL, json={"text": message})

# ====== HTML解析 ======
def check_hoyousho(name, html):
    soup = BeautifulSoup(html, "html.parser")
    select = soup.find("select", id="apply_join_time")

    if not select:
        return []

    return [
        opt.text.strip()
        for opt in select.find_all("option")
        if opt.get("value")
    ]

# ====== 状態保存 ======
def load_last_dates():
    try:
        with open("last_dates.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_last_dates(data):
    with open("last_dates.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ====== 非同期処理 ======
async def fetch_and_check(session, name, url, last_dates):
    try:
        headers = {
            "User-Agent": random.choice(USER_AGENTS)
        }

        async with session.get(url, headers=headers) as res:
            html = await res.text()

        if any(word in html for word in OK_KEYWORDS):
            return name, [], None

        dates = check_hoyousho(name, html)

        old = set(last_dates.get(name, []))
        new = set(dates)
        diff = sorted(new - old)

        if diff:
            msg = f"🏨 {name} に空きがあります！\n\n"
            msg += "📅 空いている日付:\n"
            msg += "\n".join(diff)
            msg += f"\n\n🔗 {url}"
            return name, dates, msg

        return name, dates, None

    except Exception as e:
        print(f"{name}: エラー {e}")
        return name, [], "ERROR"

# ====== メイン処理 ======
async def run_checks():
    last_dates = load_last_dates()
    current_dates = {}
    messages = []
    has_error = False

    timeout = aiohttp.ClientTimeout(total=10)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        tasks = []

        for name, url in URLS.items():
            tasks.append(fetch_and_check(session, name, url, last_dates))
            await asyncio.sleep(random.uniform(0.1, 0.3))  # ★分散

        results = await asyncio.gather(*tasks)

    for name, dates, result in results:
        if result == "ERROR":
            has_error = True
            continue

        current_dates[name] = dates

        if result:
            messages.append(result)

    if messages:
        send_slack("\n\n".join(messages))
        print("Slack通知送信")
    elif has_error:
        send_slack("アクセスエラー発生")
    else:
        print("空きなし")

    if not has_error:
        save_last_dates(current_dates)

# ====== 15秒ループ ======
INTERVAL = 15
LOOP_COUNT = 4

for i in range(LOOP_COUNT):
    print(f"\n===== {i+1}回目 =====")

    start = time.time()

    asyncio.run(run_checks())

    elapsed = time.time() - start
    sleep_time = INTERVAL - elapsed

    if sleep_time > 0 and i < LOOP_COUNT - 1:
        time.sleep(sleep_time)
