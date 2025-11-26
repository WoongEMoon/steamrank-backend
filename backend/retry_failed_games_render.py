import os
import requests
import psycopg2

# ================================
#           DB 설정
# ================================
DB = {
    "host": "dpg-d4i86fkhg0os73fi4keg-a",
    "dbname": "steamrank_db",
    "user": "steamrank_db_user",
    "password": "xkUGR7Y35UidHw6HooptU41A0GXXg1Jh",
    "port": 5432,
    "sslmode": "require",
}

def get_db_connection():
    return psycopg2.connect(
        host=DB["host"],
        dbname=DB["dbname"],
        user=DB["user"],
        password=DB["password"],
        port=DB["port"],
        sslmode=DB["sslmode"],
    )

# ================================
#      appdetails API
# ================================
def fetch_appdetails(appid: str):
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}"

    try:
        resp = requests.get(url, timeout=8)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"✖ API 실패 ({appid}): {e}")
        return None

    entry = data.get(str(appid))
    if not isinstance(entry, dict) or not entry.get("success"):
        print(f"✖ API entry 이상 ({appid})")
        return None

    game = entry.get("data", {})
    profile_img = game.get("header_image")

    # ===============================
    # 🔥 가격 처리 (최종본)
    # ===============================
    price_str = None
    price_info = game.get("price_overview")
    is_free = game.get("is_free", False)

    if is_free:
        price_str = "free"

    elif isinstance(price_info, dict):
        currency = price_info.get("currency")
        final = price_info.get("final")
        formatted = price_info.get("final_formatted")

        if final is not None:
            if currency == "KRW":
                price_str = formatted
            elif currency == "JPY":
                price_str = f"¥{final:,}"
            elif currency == "USD":
                price_str = f"${final / 100:.2f}"
            else:
                price_str = formatted if formatted else str(final)

    return profile_img, price_str

# ================================
#           DB UPDATE
# ================================
def update_game_in_db(conn, appid: str, name: str, details):
    profile_img, price = details

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO games (steam_appid, name, profile_img, price)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (steam_appid)
            DO UPDATE SET
                name = EXCLUDED.name,
                profile_img = EXCLUDED.profile_img,
                price = EXCLUDED.price;
            """,
            (appid, name, profile_img, price),
        )

# ================================
#        실패 파일 처리
# ================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FAILED_FILE = os.path.join(BASE_DIR, "games_failed.txt")

def load_failed_games():
    failed = []

    if not os.path.exists(FAILED_FILE):
        print(f"[ERROR] 파일 없음: {FAILED_FILE}")
        return failed

    with open(FAILED_FILE, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue

            parts = line.split()
            appid = parts[0]
            name = " ".join(parts[1:])
            failed.append((appid, name))

    return failed

# ================================
#           전체 처리
# ================================
def retry_failed():
    failed_games = load_failed_games()
    print(f"\n▶ 재시도 대상: {len(failed_games)}개\n")

    conn = get_db_connection()

    try:
        for appid, name in failed_games:
            print(f"\n▶ 재시도: {appid}   {name}")

            details = fetch_appdetails(appid)
            if not details:
                print(f"✖ 실패 → {appid} {name}")
                continue

            try:
                update_game_in_db(conn, appid, name, details)
                conn.commit()
                print(f"✔ 완료: {name}")
            except Exception as e:
                conn.rollback()
                print(f"✖ DB 오류: {appid} {name}: {e}")

    finally:
        conn.close()


if __name__ == "__main__":
    retry_failed()
