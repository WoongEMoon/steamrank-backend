import psycopg2
import requests
import json
import os

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

    total_reviews = None
    if "recommendations" in game:
        total_reviews = game["recommendations"].get("total")

    return profile_img, price, total_reviews

def update_game_in_db(appid, name, details):
    conn = get_db_connection()
    cur = conn.cursor()

    profile_img, price, total_reviews = details

    cur.execute("""
        UPDATE games
        SET profile_img = %s,
            price = %s,
            total_reviews = %s
        WHERE steam_appid = %s OR name = %s;
    """, (profile_img, price, total_reviews, appid, name))

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

        # games.txt 형식:  appid \t name
        try:
            appid, name = line.split("\t", 1)
        except:
            print(f"⚠️ 형식 오류 → {line}")
            continue

        print(f"\n▶ 처리 중: {appid}    {name}")

        details = fetch_appdetails(appid)
        if details is None:
            print(f"❌ API 실패: {name}")
            continue

        update_game_in_db(appid, name, details)
        print(f"✔ 완료: {name}")

if __name__ == "__main__":
    process_file("games.txt")
