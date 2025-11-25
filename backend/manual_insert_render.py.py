import psycopg2
import requests
import json
from datetime import datetime

# Render PostgreSQL
DB = {
    "host": "dpg-d4i86fkhg0os73fi4keg-a",
    "dbname": "steamrank_db",
    "user": "steamrank_db_user",
    "password": "xkUGR7Y35UidHw6HooptU41A0GXXg1Jh",
    "port": 5432,
}


def fetch_appdetails(appid):
    """Steam appdetails API 조회"""
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
    response = requests.get(url, timeout=10)
    data = response.json()

    if not data[str(appid)]["success"]:
        return None

    game = data[str(appid)]["data"]

    # 필요한 정보만 추출
    profile_img = game.get("header_image")

    price = None
    if "price_overview" in game:
        price = game["price_overview"].get("final")

    return profile_img, price


def fetch_current_players(appid):
    """동접자 API"""
    url = f"https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={appid}"
    response = requests.get(url, timeout=10)
    data = response.json()

    try:
        return data["response"]["player_count"]
    except:
        return 0


def upsert_game(name, appid, profile_img, price):
    """games 테이블 INSERT 또는 UPDATE"""
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
    """daily_players 테이블 INSERT"""
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


def process_file(file_path):
    fail_list = []

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        if "/" not in line:
            continue

        name, appid = line.split("/")
        name, appid = name.strip(), appid.strip()

        print(f"▶ 처리 중: {name} ({appid})")

        # 상세 정보 가져오기
        details = fetch_appdetails(appid)
        if details is None:
            print(f"❌ 실패: appdetails 없음 → {name} ({appid})")
            fail_list.append((name, appid))
            continue

        profile_img, price = details
        current_players = fetch_current_players(appid)

        # DB 저장
        upsert_game(name, appid, profile_img, price)
        insert_daily_players(appid, current_players)

        print(f"✔ 완료: {name}")

    # 실패 로그 저장
    if fail_list:
        with open("manual_fail_log.txt", "w", encoding="utf-8") as f:
            for n, a in fail_list:
                f.write(f"{n} / {a}\n")
        print("⚠ 실패 목록 저장 → manual_fail_log.txt")


if __name__ == "__main__":
    process_file("your_list.txt")  # ← 여기에 사용하는 파일명
