from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import requests
from datetime import datetime

app = FastAPI()

# ==============================================
# CORS
# ==============================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================================
# DB 연결
# ==============================================
def get_db():
    return psycopg2.connect(
        host="dpg-d4i86fkhg0os73fi4keg-a",
        dbname="steamrank_db",
        user="steamrank_db_user",
        password="xkUGR7Y35UidHw6HooptU41A0GXXg1Jh",
        port="5432",
        sslmode="require"
    )

# ==============================================
# 기본 홈
# ==============================================
@app.get("/")
def home():
    return {"message": "SteamRank Backend running!"}

# ==============================================
# 스팀 동접자 업데이트
# ==============================================
@app.get("/update")
def update_players():
    conn = get_db()
    cur = conn.cursor()

    today = datetime.now().strftime("%Y-%m-%d")

    # games 테이블에서 appid + steam_appid 가져오기
    cur.execute("SELECT appid, steam_appid FROM games;")
    games = cur.fetchall()

    for appid, steam_appid in games:
        url = f"https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={steam_appid}"

        try:
            data = requests.get(url, timeout=4).json()
            players = data.get("response", {}).get("player_count", 0)
        except:
            players = 0

        cur.execute("""
            INSERT INTO daily_players (appid, date, players, steam_appid)
            VALUES (%s, %s, %s, %s)
        """, (appid, today, players, steam_appid))

    conn.commit()
    cur.close()
    conn.close()

    return {"status": "success"}

# ==============================================
# 자동완성 검색
# ==============================================
@app.get("/api/search")
def search_game(q: str):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT appid, name 
        FROM games
        WHERE name ILIKE %s
        ORDER BY name ASC
        LIMIT 20;
    """, (f"%{q}%",))

    rows = cur.fetchall()
    conn.close()

    return [{"appid": r[0], "name": r[1]} for r in rows]

# ==============================================
# 날짜별 랭킹 조회
# ==============================================
@app.get("/api/rankings")
def get_rankings(date: str):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            g.name,
            g.price,
            g.profile_img,
            dp.players,
            g.steam_appid
        FROM daily_players dp
        JOIN games g ON dp.appid = g.appid
        WHERE dp.date = %s
        ORDER BY dp.players DESC;
    """, (date,))

    rows = cur.fetchall()
    conn.close()

    return [
        {
            "name": r[0],
            "price": r[1],
            "profile_img": r[2],
            "players": r[3],
            "steam_appid": r[4]
        }
        for r in rows
    ]
