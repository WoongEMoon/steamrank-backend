import requests
import psycopg2
import time
from difflib import SequenceMatcher

DB = {
    "dbname": "Steam_Rank",
    "user": "postgres",
    "password": "1234",
    "host": "localhost"
}

LIST_FILE = "../SteamRankFinal.txt"

# ────────────────────────────────────────────────
# DB 연결
# ────────────────────────────────────────────────
def get_conn():
    return psycopg2.connect(**DB)


# ────────────────────────────────────────────────
# 가장 유사한 문자열 찾기
# ────────────────────────────────────────────────
def similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


# ────────────────────────────────────────────────
# Steam 검색 API
# ────────────────────────────────────────────────
def search_steam_game(name):
    url = f"https://store.steampowered.com/api/storesearch/?term={name}&cc=kr"
    try:
        res = requests.get(url, timeout=5)
        data = res.json()
        if "items" not in data:
            return None

        if len(data["items"]) == 0:
            return None

        # 가장 유사한 결과 선택
        best = None
        best_score = 0
        for item in data["items"]:
            score = similar(name, item["name"])
            if score > best_score:
                best = item
                best_score = score

        if best_score < 0.4:
            return None

        return best

    except Exception as e:
        print("검색 실패:", e)
        return None


# ────────────────────────────────────────────────
# Steam appdetails 가져오기
# ────────────────────────────────────────────────
def fetch_details(appid):
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=kr&l=korean"
    try:
        r = requests.get(url, timeout=5)
        js = r.json()

        if not js[str(appid)]["success"]:
            return None

        data = js[str(appid)]["data"]

        return {
            "price": parse_price(data),
            "header_image": data.get("header_image", ""),
            "total_reviews": data.get("recommendations", {}).get("total", 0)
        }

    except:
        return None


def parse_price(data):
    if "is_free" in data and data["is_free"]:
        return "Free"
    if "price_overview" in data:
        return data["price_overview"]["final_formatted"]
    return "?"


# ────────────────────────────────────────────────
# DB 업데이트
# ────────────────────────────────────────────────
def db_update(name, appid, details):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        UPDATE games
        SET steam_appid = %s,
            profile_img = %s,
            price = %s,
            total_reviews = %s
        WHERE name = %s
    """, (appid, details["header_image"], details["price"],
          details["total_reviews"], name))

    conn.commit()
    cur.close()
    conn.close()


# ────────────────────────────────────────────────
# MAIN
# ────────────────────────────────────────────────
print("\n===============================")
print("🔥 자동 매칭 시작")
print("===============================\n")

with open(LIST_FILE, "r", encoding="utf-8") as f:
    lines = [line.strip() for line in f.readlines()
             if line.strip() and not line.startswith("#")]

for name in lines:
    print(f"\n▶ '{name}' 검색 중...")

    result = search_steam_game(name)
    if not result:
        print("❌ 매칭 실패: 검색 결과 없음")
        continue

    appid = result["id"]
    realname = result["name"]

    print(f"✔ 검색 성공: [{appid}] {realname}")

    # 세부 정보 가져오기
    details = fetch_details(appid)
    if not details:
        print("⚠ appdetails 실패 → AppID만 저장")
        details = {"header_image": "", "price": "?", "total_reviews": 0}

    # DB 업데이트
    db_update(name, appid, details)

    print(f"✅ DB 업데이트 완료: {name} → {appid}")

    time.sleep(1.2)

print("\n🎉 모든 매칭 완료!")
