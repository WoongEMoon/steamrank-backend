import psycopg2
import requests
import json

# DB 연결 설정
DB_CONFIG = {
    "host": "localhost",
    "dbname": "steamrank",
    "user": "postgres",
    "password": "YOUR_PASSWORD",  # ← 여기에 비밀번호 넣기
    "port": 5432
}


def fetch_appdetails(appid):
    """Steam appdetails API 조회"""
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
    response = requests.get(url, timeout=10)
    data = response.json()

    if not data[str(appid)]["success"]:
        return None

    game = data[str(appid)]["data"]

    # 필요한 정보만 추출
    profile_img = game.get("header_image")
    price = None
    if "price_overview" in game:
        price = game["price_overview"].get("final")

    total_reviews = None
    if "recommendations" in game:
        total_reviews = game["recommendations"].get("total")

    return profile_img, price, total_reviews


def update_game_in_db(name, appid, details):
    """DB 업데이트"""
    conn = psycopg2.connect(**DB_CONFIG)
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


def process_file(file_path):
    fail_list = []

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        if "/" not in line:
            continue

        name, appid = line.split("/")
        name = name.strip()
        appid = appid.strip()

        print(f"▶ 처리 중: {name} ({appid})")

        # appdetails 호출
        details = fetch_appdetails(appid)

        if details is None:
            print(f"❌ 실패: appdetails 없음 → {name} ({appid})")
            fail_list.append((name, appid))
            continue

        # DB 업데이트
        update_game_in_db(name, appid, details)
        print(f"✔ 완료: {name}")

    # 실패 목록 저장
    if fail_list:
        with open("manual_fail_log.txt", "w", encoding="utf-8") as f:
            for n, a in fail_list:
                f.write(f"{n} / {a}\n")
        print("⚠ 실패 목록 파일 생성 → manual_fail_log.txt")


if __name__ == "__main__":
    process_file("failed_list.txt")  # ← 여기에 파일명 입력
