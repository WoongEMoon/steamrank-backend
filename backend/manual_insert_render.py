import psycopg2
import requests
import json
import re

DB = {
    "host": "dpg-d4i86fkhg0os73fi4keg-a",
    "dbname": "steamrank_db",
    "user": "steamrank_db_user",
    "password": "xkUGR7Y35UidHw6HooptU41A0GXXg1Jh",
    "port": 5432,
    "sslmode": "require"
}

def get_db_connection():
    return psycopg2.connect(
        host=DB["host"],
        dbname=DB["dbname"],
        user=DB["user"],
        password=DB["password"],
        port=DB["port"],
        sslmode=DB["sslmode"]
    )

def fetch_appdetails(appid):
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

def update_game_in_db(appid, name, details):
    conn = get_db_connection()
    cur = conn.cursor()

    profile_img, price = details

    # check existing by appid
    cur.execute("SELECT 1 FROM games WHERE steam_appid = %s", (appid,))
    exists = cur.fetchone()

    if exists:
        cur.execute("""
            UPDATE games
            SET profile_img = %s,
                price = %s
            WHERE steam_appid = %s;
        """, (profile_img, price, appid))

    else:
        # check by name
        cur.execute("SELECT 1 FROM games WHERE name = %s", (name,))
        exists_by_name = cur.fetchone()

        if exists_by_name:
            cur.execute("""
                UPDATE games
                SET steam_appid = %s,
                    profile_img = %s,
                    price = %s
                WHERE name = %s;
            """, (appid, profile_img, price, name))
        else:
            # full insert
            cur.execute("""
                INSERT INTO games (steam_appid, name, profile_img, price)
                VALUES (%s, %s, %s, %s)
            """, (appid, name, profile_img, price))

    conn.commit()
    cur.close()
    conn.close()

def process_file(file_path):
    print(f"\n📁 파일 로딩: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # ★★★ 핵심: 숫자로 시작하는 appid 추출하고 나머지 전체를 name으로 처리
        match = re.match(r"^(\d+)\s+(.*)$", line)
        if not match:
            print(f"⚠️ 파싱 실패 → {line}")
            continue

        appid, name = match.groups()

        print(f"\n▶ 처리 중: {appid}   {name}")

        details = fetch_appdetails(appid)
        if details is None:
            print(f"❌ API 실패: {name}")
            continue

        update_game_in_db(appid, name, details)
        print(f"✔ 완료: {name}")

if __name__ == "__main__":
    process_file("games.txt")
