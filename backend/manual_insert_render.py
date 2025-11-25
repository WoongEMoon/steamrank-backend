import psycopg2
import requests
import json
import os

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        port=os.getenv("DB_PORT", 5432)
    )

def fetch_appdetails(appid):
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
    print(f"[API 요청] {url}")  # 디버그 출력
    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        if not data[str(appid)]["success"]:
            print(f"[API 실패] appid={appid}")
            return None

        game = data[str(appid)]["data"]

        profile_img = game.get("header_image")
        price = game.get("price_overview", {}).get("final")
        total_reviews = game.get("recommendations", {}).get("total")

        return profile_img, price, total_reviews

    except Exception as e:
        print(f"[API 오류] {appid}: {e}")
        return None


def update_game_in_db(name, appid, details):
    print(f"[DB 업데이트] {name} ({appid})")

    conn = get_db_connection()
    cur = conn.cursor()

    profile_img, price, total_reviews = details

    cur.execute("""
        UPDATE games
        SET steam_appid = %s,
            profile_img = %s,
            price = %s,
            total_reviews = %s
        WHERE name = %s;
    """, (appid, profile_img, price, total_reviews, name))

    conn.commit()
    cur.close()
    conn.close()

    print(f"[완료] {name}")


def process_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # ① 탭 기준 먼저 시도
        if "\t" in line:
            appid, name = line.split("\t", 1)

        # ② 탭이 없으면 공백 기준 파싱
        else:
            parts = line.split()
            appid = parts[0]
            name = " ".join(parts[1:])

        appid = appid.strip()
        name = name.strip()

        print(f"▶ 처리 중: {name} ({appid})")

        details = fetch_appdetails(appid)
        if details is None:
            print(f"❌ 실패: {name} ({appid})")
            continue

        update_game_in_db(name, appid, details)
        print(f"✔ 완료: {name}")


if __name__ == "__main__":
    process_file("games.txt")
