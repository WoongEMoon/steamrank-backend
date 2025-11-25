import psycopg2
import requests
import json
import time

DB = {
    "host": "dpg-d4i86fkhg0os73fi4keg-a",
    "dbname": "steamrank_db",
    "user": "steamrank_db_user",
    "password": "xkUGR7Y35UidHw6HooptU41A0GXXg1Jh",
    "port": 5432,
    "sslmode": "require"  # Render에서는 반드시 필요함
}


# ------------------------------
# DB 연결
# ------------------------------
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB["host"],
            dbname=DB["dbname"],
            user=DB["user"],
            password=DB["password"],
            port=DB["port"],
            sslmode=DB["sslmode"]
        )
        return conn
    except Exception as e:
        print("❌ DB 연결 실패:", e)
        raise


# ------------------------------
# Steam appdetails API 호출
# ------------------------------
def fetch_appdetails(appid):
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}"

    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        if not data[str(appid)]["success"]:
            print(f"❌ API 실패: {appid}")
            return None

        game = data[str(appid)]["data"]

        # 필요한 값 추출
        profile_img = game.get("header_image")
        price = None
        if "price_overview" in game:
            price = game["price_overview"].get("final")

        total_reviews = None
        if "recommendations" in game:
            total_reviews = game["recommendations"].get("total")

        return profile_img, price, total_reviews

    except Exception as e:
        print(f"❌ API 호출 중 오류 ({appid}):", e)
        return None


# ------------------------------
# DB 업데이트
# ------------------------------
def update_game_in_db(name, appid, details):
    conn = get_db_connection()
    cur = conn.cursor()

    profile_img, price, total_reviews = details

    try:
        cur.execute("""
            UPDATE games
            SET
                steam_appid = %s,
                profile_img = %s,
                price = %s,
                total_reviews = %s
            WHERE name = %s;
        """, (appid, profile_img, price, total_reviews, name))

        conn.commit()
        print(f"✔ DB 업데이트 완료: {name}")

    except Exception as e:
        print(f"❌ DB 업데이트 실패: {name} ({appid})", e)

    finally:
        cur.close()
        conn.close()


# ------------------------------
# 파일 읽기 + 처리
# ------------------------------
def process_file(file_path):
    print(f"📂 파일 로딩: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        if ":" not in line:
            continue

        name, appid = line.split(":", 1)
        name = name.strip()
        appid = appid.strip()

        print(f"\n▶ 처리 중: {name} ({appid})")

        details = fetch_appdetails(appid)
        if details is None:
            print(f"❌ 처리 실패: {name}")
            continue

        update_game_in_db(name, appid, details)
        time.sleep(1)  # 너무 빠른 API 호출 방지


if __name__ == "__main__":
    process_file("games.txt")
