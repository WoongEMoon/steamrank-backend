import psycopg2
import requests
from datetime import datetime

# 🔹 Render PostgreSQL 설정 (정확한 값으로 수정됨)
DB_CONFIG = {
    "host": "dpg-d4i86fkhg0os73fi4keg-a",
    "dbname": "steamrank_db",
    "user": "steamrank_db_user",
    "password": "xkUGR7Y35UidHw6HooptU41A0GXXg1Jh",
    "port": 5432,
}

# ------------------------------
# 🚀 Steam API
# ------------------------------
def fetch_appdetails(appid):
    """Steam appdetails API에서 프로필 이미지, 가격 수집"""
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
    response = requests.get(url, timeout=10)
    data = response.json()

    if not data[str(appid)]["success"]:
        return None

    game = data[str(appid)]["data"]

    profile_img = game.get("header_image")
    price = None

    if "price_overview" in game:
        price = game["price_overview"].get("final")

    return profile_img, price


def fetch_current_players(appid):
    """Steam 동시 접속자 수"""
    url = f"https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={appid}"
    response = requests.get(url, timeout=10)
    data = response.json()

    try:
        return data["response"]["player_count"]
    except:
        return 0

# ------------------------------
# 🚀 DB 저장 함수
# ------------------------------
def upsert_game(name, appid, profile_img, price):
    """games 테이블 저장 또는 업데이트"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO games (name, steam_appid, profile_img, price)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (steam_appid)
        DO UPDATE SET
            name = EXCLUDED.name,
            profile_img = EXCLUDED.profile_img,
            price = EXCLUDED.price;
    """, (name, appid, profile_img, price))

    conn.commit()
    cur.close()
    conn.close()


def insert_daily_players(appid, count):
    """daily_players 기록"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    today = datetime.now().strftime("%Y-%m-%d")

    cur.execute("""
        INSERT INTO daily_players (appid, date, peak_players)
        VALUES (%s, %s, %s)
        ON CONFLICT (appid, date)
        DO UPDATE SET
            peak_players = EXCLUDED.peak_players;
    """, (appid, today, count))

    conn.commit()
    cur.close()
    conn.close()

# ------------------------------
# 🚀 메인 처리: 실패 리스트 제거됨
# ------------------------------
def process_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        if "/" not in line:
            continue

        name, appid = line.split("/")
        name = name.strip()
        appid = appid.strip()

        print(f"▶ 처리 중: {name} ({appid})")

        details = fetch_appdetails(appid)
        if details is None:
            print(f"❌ Steam API 실패: {name}")
            continue

        profile_img, price = details
        current_players = fetch_current_players(appid)

        upsert_game(name, appid, profile_img, price)
        insert_daily_players(appid, current_players)

        print(f"✔ 완료: {name}")

# ------------------------------
# 🚀 시작
# ------------------------------
if __name__ == "__main__":
    process_file("games.txt")   # ← 여기에 사용될 파일명 하나만 필요
