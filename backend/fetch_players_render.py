import psycopg2
import requests

# ===============================
# 🔵 Render PostgreSQL 설정
# ===============================
DB = {
    "host": "dpg-d4i86fkhg0os73fi4keg-a",
    "dbname": "steamrank_db",
    "user": "steamrank_db_user",
    "password": "xkUGR7Y35UidHw6HooptU41A0GXXg1Jh",
    "port": 5432,
    "sslmode": "require"
}

PLAYER_API = "https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={}"


def get_conn():
    return psycopg2.connect(**DB)


# ===============================
# 하루 기록 삽입
# ===============================
def insert_daily_record(steam_appid, players):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO daily_players (steam_appid, date, players)
        VALUES (%s, CURRENT_DATE, %s)
        ON CONFLICT (steam_appid, date) DO UPDATE
        SET players = EXCLUDED.players;
    """, (steam_appid, players))

    conn.commit()
    cur.close()
    conn.close()


# ===============================
# Steam API 호출
# ===============================
def get_players(steam_appid):
    try:
        url = PLAYER_API.format(steam_appid)
        res = requests.get(url, timeout=10)
        data = res.json()
        return data["response"].get("player_count", 0)
    except Exception as e:
        print(f"⚠ API 오류 (steam_appid={steam_appid}): {e}")
        return 0


# ===============================
# 전체 게임 처리
# ===============================
def process_all_games():
    conn = get_conn()
    cur = conn.cursor()

    # 현재 DB 구조에 100% 맞는 SELECT
    cur.execute("""
        SELECT steam_appid, name
        FROM games
        WHERE steam_appid IS NOT NULL;
    """)
    games = cur.fetchall()
    conn.close()

    print(f"\n총 {len(games)}개 게임 처리 시작\n")

    for steam_appid, name in games:
        print(f"▶ {name} ({steam_appid}) 처리 중")
        players = get_players(steam_appid)
        print(f"   현재 동접자: {players}")
        insert_daily_record(steam_appid, players)

    print("\n🎉 모든 게임 처리 완료!\n")


if __name__ == "__main__":
    process_all_games()
