import psycopg2
import requests
import time

DB = {
    "host": "localhost",
    "dbname": "Steam_Rank",
    "user": "postgres",
    "password": "1234",
    "port": 5432
}

TXT_FILE = "../react.txt"


def get_appdetails(appid):
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
    try:
        res = requests.get(url, timeout=10)
        data = res.json().get(str(appid), {})
        if not data.get("success"):
            return None

        d = data["data"]

        img = d.get("header_image")
        price = None
        if d.get("price_overview"):
            price = d["price_overview"].get("final")
        reviews = None
        if d.get("recommendations"):
            reviews = d["recommendations"].get("total")

        return img, price, reviews

    except:
        return None


def ensure_game_exists(appid, name):
    conn = psycopg2.connect(**DB)
    cur = conn.cursor()

    cur.execute("SELECT appid FROM games WHERE steam_appid=%s;", (appid,))
    row = cur.fetchone()

    # 1) 이미 존재하면 id 반환
    if row:
        game_pk = row[0]
    else:
        # 2) 없으면 새로 삽입
        cur.execute("INSERT INTO games (name, steam_appid) VALUES (%s, %s) RETURNING appid;",
                    (name, appid))
        game_pk = cur.fetchone()[0]
        conn.commit()

    cur.close()
    conn.close()

    return game_pk


def update_game_details(appid, details):
    conn = psycopg2.connect(**DB)
    cur = conn.cursor()

    img, price, total_reviews = details

    cur.execute("""
        UPDATE games
        SET profile_img=%s,
            price=%s,
            total_reviews=%s
        WHERE steam_appid=%s;
    """, (img, price, total_reviews, appid))

    conn.commit()
    cur.close()
    conn.close()


def process():
    with open(TXT_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    fails = []

    for line in lines:
        if "/" not in line:
            continue

        name, appid = line.split("/")
        name = name.strip()
        appid = appid.strip()

        # Wetory 같이 AppID 누락된 경우 건너뜀
        if not appid.isdigit():
            fails.append(f"{name} / {appid}")
            continue

        print(f"\n▶ 처리 중: {name} ({appid})")

        # DB에 해당 게임 기록이 없으면 자동 생성
        ensure_game_exists(appid, name)

        # appdetails 호출
        details = get_appdetails(appid)
        if not details:
            print(f"❌ 실패: {name}")
            fails.append(f"{name} / {appid}")
            continue

        update_game_details(appid, details)
        print(f"✔ 완료: {name}")

        time.sleep(1)

    # 실패 로그 저장
    if fails:
        with open("thumbnail_fix_fail_log.txt", "w", encoding="utf-8") as f:
            for item in fails:
                f.write(item + "\n")

        print("\n⚠ 일부 실패. thumbnail_fix_fail_log.txt 확인!")


if __name__ == "__main__":
    process()
