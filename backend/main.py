from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import requests
from datetime import datetime

app = FastAPI()

# ==============================================
# CORS 설정
# ==============================================
# 네 Netlify 주소 넣기
origins = [
    "https://heartfelt-madeleine-62bce6.netlify.app",
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
# 오늘자 동접자 업데이트
# ==============================================
@app.get("/update")
def update_players():
    conn = get_db()
    cur = conn.cursor()

    today = datetime.now().strftime("%Y-%m-%d")

    # games 테이블에서 steam_appid만 가져오기
    cur.execute("SELECT steam_appid, name FROM games;")
    games = cur.fetchall()

    for steam_appid, name in games:
        url = f"https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={steam_appid}"

        try:
            data = requests.get(url, timeout=5).json()
            players = data.get("response", {}).get("player_count", 0)
        except:
            players = 0

        cur.execute("""
            INSERT INTO daily_players (steam_appid, date, players)
            VALUES (%s, %s, %s)
        """, (steam_appid, today, players))

    conn.commit()
    cur.close()
    conn.close()

    return {"status": "success", "date": today}

# ==============================================
# 자동완성 검색
# ==============================================
@app.get("/api/search")
def search_game(q: str):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT steam_appid, name 
        FROM games
        WHERE name ILIKE %s
        ORDER BY name ASC
        LIMIT 20;
    """, (f"%{q}%",))

    rows = cur.fetchall()
    conn.close()

    return [{"steam_appid": r[0], "name": r[1]} for r in rows]

# ==============================================
# 날짜별 랭킹 조회
# ==============================================
@app.get("/api/rankings")
def get_rankings(date: str):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            g.steam_appid,
            g.name,
            g.price,
            g.profile_img,
            dp.players
        FROM daily_players dp
        JOIN games g 
          ON dp.steam_appid = g.steam_appid
        WHERE dp.date = %s
        ORDER BY dp.players DESC;
    """, (date,))

    rows = cur.fetchall()
    conn.close()

    return [
        {
            "steam_appid": r[0],
            "name": r[1],
            "price": r[2],
            "profile_img": r[3],
            "players": r[4]
        }
        for r in rows
    ]
