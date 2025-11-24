import psycopg2
import requests
from datetime import datetime

DB = {
    "host": "localhost",
    "dbname": "Steam_Rank",
    "user": "postgres",
    "password": "1234",
    "port": 5432
}

PLAYER_API = "https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={}"

# ===============================
# DB 연결 함수
# ===============================
def get_conn():
    return psycopg2.connect(**DB)

# ===============================
# 하루 기록 삽입 (중복 체크 없음 → 항상 갱신)
# ===============================
def insert_daily_record(appid, steam_appid, players):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO daily_players (appid, steam_appid, players, date)
        VALUES (%s, %s, %s, CURRENT_DATE)
        ON CONFLICT (appid, date) DO UPDATE
        SET players = EXCLUDED.players;
    """, (appid, steam_appid, players))

    conn.commit()
    cur.close()
    conn.close()

# ===============================
# Steam API로 현재 동접자 수 가져오기
# ===============================
def get_players(steam_appid):
    try:
        url = PLAYER_API.format(steam_appid)
        res = requests.get(url, timeout=10)
        data = res.json()

        return data["response"].get("player_count", 0)

    except Exception as e:
        print(f"  ⚠ API 오류 발생 (appid={steam_appid}): {e}")
        return 0

# ===============================
# 전체 게임 처리
# ===============================
def process_all_games():
    conn = get_conn()
    cur = conn.cursor()

    # steam_appid가 존재하는 게임만 불러오기
    cur.execute("""
        SELECT appid, steam_appid, name
        FROM games
        WHERE steam_appid IS NOT NULL;
    """)

    games = cur.fetchall()
    conn.close()

    print(f"\n총 {len(games)}개 게임 처리 시작\n")

    for appid, steam_appid, name in games:
        print(f"▶ 처리 중: {name} ({steam_appid})")

        # 현재 동접자 수 가져오기
        players = get_players(steam_appid)
        print(f"   현재 동접자: {players}")

        # daily_players 테이블에 하루 기록 저장
        insert_daily_record(appid, steam_appid, players)

    print("\n🎉 모든 게임 처리 완료!\n")

# ===============================
# 실행
# ===============================
if __name__ == "__main__":
    process_all_games()
