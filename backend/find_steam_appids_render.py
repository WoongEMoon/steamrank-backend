import psycopg2
import requests
import time

# ===============================
# 🔵 Render PostgreSQL 설정
# ===============================
DB = {
    "host": "dpg-d4i86fkhg0os73fi4keg-a.oregon-postgres.render.com",
    "dbname": "steamrank_db",
    "user": "steamrank_db_user",
    "password": "xkUGR7Y35UidHw6HooptU41A0GXXg1Jh",
    "port": 5432,
    "sslmode": "require"
}

def get_db_conn():
    return psycopg2.connect(**DB)

# ===============================
# 스팀 비공식 AppID 검색
# ===============================
def search_steam_appid(game_name: str):
    url = f"https://steamcommunity.com/actions/SearchApps/{game_name}"

    try:
        res = requests.get(url, timeout=5)
        if res.status_code != 200:
            return None

        results = res.json()
        if not results:
            return None

        # 정확 일치 우선
        for r in results:
            if r["name"].lower() == game_name.lower():
                return r["appid"]

        # 없으면 첫 번째
        return results[0]["appid"]

    except Exception as e:
        print(f"검색 실패 ({game_name}): {e}")
        return None

# ===============================
# steam_appid 없는 게임 자동 등록
# ===============================
def update_all_games():
    conn = get_db_conn()
    cur = conn.cursor()

    cur.execute("SELECT appid, name FROM games WHERE steam_appid IS NULL;")
    games = cur.fetchall()

    print(f"\n🔍 steam_appid 없는 게임 수: {len(games)}\n")

    for appid, name in games:
        print(f"▶ '{name}' 검색 중...")

        steam_id = search_steam_appid(name)
        time.sleep(0.3)

        if steam_id is None:
            print(f"❌ 실패: {name}\n")
            continue

        cur.execute(
            "UPDATE games SET steam_appid = %s WHERE appid = %s",
            (steam_id, appid)
        )
        conn.commit()

        print(f"✔ 등록 완료 → {name}: {steam_id}\n")

    conn.close()
    print("\n🎉 모든 AppID 자동 등록 완료!\n")

if __name__ == "__main__":
    update_all_games()
