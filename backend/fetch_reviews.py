import psycopg2
import requests
from datetime import date

def get_db_conn():
    return psycopg2.connect(
        host="localhost",
        dbname="Steam_Rank",
        user="postgres",
        password="1234",
        port=5432
    )

STEAM_API_URL = "https://store.steampowered.com/api/appdetails?appids={appid}&cc=us&l=en"

def update_game_info(appid, steam_appid):
    """게임 상세 정보 업데이트 (이미지, 가격, 총 리뷰 수 등)"""
    url = STEAM_API_URL.format(appid=steam_appid)
    res = requests.get(url).json()

    if not res or not res.get(str(steam_appid), {}).get("success", False):
        print(f"❌ 게임 정보 불러오기 실패: appid={steam_appid}")
        return

    data = res[str(steam_appid)]["data"]

    # 이미지 URL
    profile_img = data.get("header_image", None)

    # 가격 정보
    if data.get("is_free"):
        price = "Free"
    else:
        price_data = data.get("price_overview")
        price = price_data.get("final_formatted") if price_data else "Unknown"

    # 총 리뷰 수
    total_reviews = data.get("recommendations", {}).get("total", 0)

    conn = get_db_conn()
    cur = conn.cursor()

    cur.execute("""
        UPDATE games
        SET profile_img=%s, price=%s, total_reviews=%s
        WHERE appid=%s
    """, (profile_img, price, total_reviews, appid))

    conn.commit()
    cur.close()
    conn.close()

    print(f"✔ 게임 정보 업데이트 완료: {data.get('name')}")

def update_today_counts():
    """24시간 리뷰 수 업데이트"""
    conn = get_db_conn()
    cur = conn.cursor()

    cur.execute("SELECT appid, name, steam_appid FROM games")
    games = cur.fetchall()

    for appid, name, steam_appid in games:
        print(f"▶ {name} 처리 중...")

        # 1) 게임 상세 정보(프로필, 가격, 총 리뷰수) 업데이트
        update_game_info(appid, steam_appid)

        # 2) 리뷰 수 가져와서 저장 — 기존 그대로
        review_api = f"https://store.steampowered.com/appreviews/{steam_appid}?json=1&filter=recent"
        res = requests.get(review_api).json()

        if "query_summary" not in res:
            print(f"  → 리뷰 정보 없음, 건너뜀")
            continue

        recent_positive = res["query_summary"]["total_positive"]

        cur.execute("""
            DELETE FROM daily_positive_counts 
            WHERE appid = %s AND date = %s
        """, (appid, date.today()))

        cur.execute("""
            INSERT INTO daily_positive_counts (appid, date, positive_count)
            VALUES (%s, %s, %s)
        """, (appid, date.today(), recent_positive))

        conn.commit()

        print(f"  → {date.today()} 긍정 리뷰 수 = {recent_positive} 저장 완료")

    cur.close()
    conn.close()

    print("✅ 오늘자 리뷰 정보 + 게임 정보 업데이트 완료")

if __name__ == "__main__":
    update_today_counts()
