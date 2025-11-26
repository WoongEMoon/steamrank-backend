import psycopg2
import requests

# ---------- DB 설정 (Render) ----------
DB = {
    "host": "dpg-d4i86fkhg0os73fi4keg-a",
    "dbname": "steamrank_db",
    "user": "steamrank_db_user",
    "password": "xkUGR7Y35UidHw6HooptU41A0GXXg1Jh",
    "port": 5432,
    "sslmode": "require",
}


# ---------- DB 연결 ----------
def get_db_connection():
    return psycopg2.connect(
        host=DB["host"],
        dbname=DB["dbname"],
        user=DB["user"],
        password=DB["password"],
        port=DB["port"],
        sslmode=DB["sslmode"],
    )


# ---------- Steam appdetails 호출 ----------
def fetch_appdetails(appid: str):
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}"

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"✖ API 요청 실패 ({appid}): {e}")
        return None

    entry = data.get(str(appid))

    # entry 구조 이상 / success False 모두 여기서 컷
    if not isinstance(entry, dict):
        print(f"✖ API 응답 형식 이상 ({appid}): {entry}")
        return None

    if not entry.get("success"):
        print(f"✖ appdetails 없음 ({appid})")
        return None

    game = entry.get("data") or {}

    profile_img = game.get("header_image")

    price = None
    price_info = game.get("price_overview")
    if isinstance(price_info, dict):
        # 센트 단위 정수(예: 1599 → 15.99달러)
        price = price_info.get("final")

    return profile_img, price


# ---------- DB 업데이트 (UPDATE만) ----------
def update_game_in_db(conn, appid: str, name: str, details):
    profile_img, price = details

    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE games
               SET steam_appid = %s,
                   profile_img = %s,
                   price       = %s
             WHERE steam_appid = %s OR name = %s
            """,
            (appid, profile_img, price, appid, name),
        )

        if cur.rowcount == 0:
            # 매칭되는 행이 없으면 그냥 알려만 주고 넘어감
            print(f"   ⚠ DB에 해당 게임 없음 → appid={appid}, name={name}")


# ---------- 파일 전체 처리 ----------
def process_file(file_path: str):
    print(f"▶ 파일 로딩: {file_path}")

    conn = get_db_connection()
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line:
                    continue

                # appid<TAB>이름 형식
                try:
                    appid, name = line.split("\t", 1)
                except ValueError:
                    print(f"✖ 형식 이상, 건너뜀: {line}")
                    continue

                appid = appid.strip()
                name = name.strip()

                print(f"▶ 처리 중: {appid}   {name}")

                try:
                    details = fetch_appdetails(appid)
                    if not details:
                        print(f"✖ 처리 실패: {appid} {name} (appdetails 없음)")
                        continue

                    update_game_in_db(conn, appid, name, details)
                    conn.commit()
                    print(f"✔ 완료: {name}")
                except Exception as e:
                    conn.rollback()
                    print(f"✖ 예외 발생, 건너뜀: {appid} {name} → {e}")

    finally:
        conn.close()


if __name__ == "__main__":
    process_file("games.txt")
