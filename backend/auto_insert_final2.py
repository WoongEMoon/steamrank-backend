import psycopg2
import requests

# DB 연결 설정
DB = {
    "host": "localhost",
    "dbname": "Steam_Rank",
    "user": "postgres",
    "password": "1234",  # ← 비밀번호 입력
    "port": 5432
}

def get_appdetails(appid):
    """Steam AppDetails API 조회"""
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        root = data[str(appid)]

        if not root["success"]:
            return None

        game = root["data"]
        img = game.get("header_image")
        price = None
        if game.get("price_overview"):
            price = game["price_overview"].get("final")

        total_reviews = None
        if game.get("recommendations"):
            total_reviews = game["recommendations"].get("total")

        return img, price, total_reviews

    except Exception:
        return None


def update_db(name, appid, details):
    """DB 업데이트"""
    conn = psycopg2.connect(**DB)
    cur = conn.cursor()

    img, price, reviews = details

    cur.execute("""
        UPDATE games
        SET steam_appid=%s,
            profile_img=%s,
            price=%s,
            total_reviews=%s
        WHERE name=%s;
    """, (appid, img, price, reviews, name))

    conn.commit()
    cur.close()
    conn.close()


def auto_process(filename):
    """SteamRankFinal2 파일을 읽어 자동 반영"""
    fails = []

    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        if "/" not in line:
            continue

        name, appid = line.split("/")
        name = name.strip()
        appid = appid.strip()

        print(f"\n▶ 처리 중: {name} ({appid})")

        details = get_appdetails(appid)
        if not details:
            print(f"❌ appdetails 실패 → {name}")
            fails.append(f"{name} / {appid}")
            continue

        update_db(name, appid, details)
        print(f"✔ 완료: {name}")

    # 실패한 것 로그 저장
    if fails:
        with open("SteamRank_manual_fail_log.txt", "w", encoding="utf-8") as f:
            for item in fails:
                f.write(item + "\n")

        print("\n⚠ 실패 항목 있음 → SteamRank_manual_fail_log.txt 확인")


if __name__ == "__main__":
    auto_process("../SteamRankFinal2.txt")

