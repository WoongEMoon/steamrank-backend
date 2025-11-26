import os
import requests
import psycopg2

# === 절대 경로 기반 설정 ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FAILED_FILE = os.path.join(BASE_DIR, "games_failed.txt")

# === DB 연결 ===
DB = {
    "host": "dpg-d4i86fkhg0os73fi4keg-a",
    "dbname": "steamrank_db",
    "user": "steamrank_db_user",
    "password": "xKuGR7Y35UldHw6H0optU41A0GXXg1Jh",
    "port": 5432
}

def insert_game_to_db(appid, name, data):
    conn = psycopg2.connect(
        host=DB["host"],
        dbname=DB["dbname"],
        user=DB["user"],
        password=DB["password"],
        port=DB["port"]
    )
    cur = conn.cursor()

    price = data.get("price_overview", {}).get("final", 0)
    header_img = data.get("header_image", "")

    cur.execute("""
        INSERT INTO games (appid, name, price, profile_img)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (appid)
        DO UPDATE SET
            name = EXCLUDED.name,
            price = EXCLUDED.price,
            profile_img = EXCLUDED.profile_img;
    """, (appid, name, price, header_img))

    conn.commit()
    cur.close()
    conn.close()


def load_failed_games():
    failed = []
    if not os.path.exists(FAILED_FILE):
        print(f"[ERROR] FAILED FILE NOT FOUND: {FAILED_FILE}")
        return failed

    with open(FAILED_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split("   ")
            if len(parts) >= 2:
                appid = parts[0].strip()
                name = parts[1].strip()
                failed.append((appid, name))
    return failed


def retry_failed():
    failed_games = load_failed_games()
    print(f"\n총 {len(failed_games)}개 실패 게임 재시도 중...\n")

    for appid, name in failed_games:
        print(f"[TRY] {appid} {name}")

        url = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=kr&l=english"
        response = requests.get(url)

        if response.status_code != 200:
            print(f"[RETRY FAIL] {appid} {name} → status code {response.status_code}")
            continue

        data = response.json().get(str(appid), {})
        if not data.get("success"):
            print(f"[RETRY FAIL] {appid} {name} → success false")
            continue

        try:
            insert_game_to_db(appid, name, data["data"])
            print(f"[RETRY OK] {appid} {name}")
        except Exception as e:
            print(f"[DB ERROR] {appid} {name} → {e}")


if __name__ == "__main__":
    retry_failed()
