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

# =======================================================
#  Steam appdetails API (가격/이미지/무료 여부 정확 버전)
# =======================================================
def fetch_appdetails(appid: str):
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=kr&l=korean"

    try:
        resp = requests.get(url, timeout=8)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"✖ API 요청 실패 ({appid}): {e}")
        return None

    entry = data.get(str(appid))
    if not isinstance(entry, dict) or not entry.get("success"):
        print(f"✖ API 성공=False ({appid})")
        return None

    game = entry.get("data", {})
    profile_img = game.get("header_image")

    # -----------------------------
    # 🔥 무료 여부 체크 (완전판)
    # -----------------------------
    is_free = (
        game.get("is_free") is True
        or game.get("is_free_license") is True
        or game.get("is_free_to_play") is True
    )

    # -----------------------------
    # 🔥 가격 파싱 (완전판)
    # -----------------------------
    price_info = game.get("price_overview")
    price_str = None

    if is_free:
        price_str = "무료 플레이"

    elif isinstance(price_info, dict):
        currency = price_info.get("currency")
        final = price_info.get("final")
        formatted = price_info.get("final_formatted")

        if final is not None:
            if currency == "KRW":
                price_str = formatted                     # 예: ₩ 64,800
            elif currency == "JPY":
                price_str = f"¥{final:,}"
            elif currency == "USD":
                price_str = f"${final / 100:.2f}"
            else:
                price_str = formatted if formatted else str(final)

    return profile_img, price_str


# =======================================================
#  DB UPSERT (중복/가격/이미지 정확 반영)
# =======================================================
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


# =======================================================
#  전체 파일 처리
# =======================================================
def process_file(file_path: str):

    print(f"▶ 파일 로딩: {file_path}")
    conn = get_db_connection()

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line:
                    continue

                try:
                    appid, name = line.split("\t", 1)
                except ValueError:
                    print(f"✖ 형식 이상: {line}")
                    continue

                appid = appid.strip()
                name = name.strip()

                print(f"\n▶ 처리 중: {appid}  {name}")

                details = fetch_appdetails(appid)
                if not details:
                    print(f"✖ API 데이터 없음: {appid} {name}")
                    continue

                try:
                    update_game_in_db(conn, appid, name, details)
                    conn.commit()
                    print(f"✔ 완료: {name}")
                except Exception as e:
                    conn.rollback()
                    print(f"✖ DB 오류 ({appid} {name}): {e}")

    finally:
        conn.close()


if __name__ == "__main__":
    process_file("games.txt")
