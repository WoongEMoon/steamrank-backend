from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2 import OperationalError
from typing import List, Optional

DB = {
    "host": "localhost",
    "dbname": "Steam_Rank",
    "user": "postgres",
    "password": "1234",
    "port": 5432
}

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB 연결 함수
def get_conn():
    try:
        return psycopg2.connect(**DB)
    except OperationalError:
        # Render에서는 DB 없을 수 있으므로 None 반환
        return None


# -------------------------------
#   API: /api/rankings
# -------------------------------
@app.get("/api/rankings")
def get_rankings(date: str):

    conn = get_conn()
    if conn is None:
        return {"error": "Database connection failed (Render 환경에서는 DB 미사용 중)"}

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

    result = []
    rank = 1
    for name, price, img, players, steam_appid in rows:
        result.append({
            "rank": rank,
            "name": name,
            "price": price,
            "profile_img": img,
            "players": players,
            "steam_appid": steam_appid
        })
        rank += 1

    return result


# -------------------------------
#   API: /api/search
# -------------------------------
@app.get("/api/search")
def search_games(q: str):

    conn = get_conn()
    if conn is None:
        return {"error": "Database connection failed (Render 환경에서는 DB 미사용 중)"}

    cur = conn.cursor()

    cur.execute("""
        SELECT steam_appid, name, profile_img
        FROM games
        WHERE LOWER(name) LIKE LOWER(%s)
        ORDER BY steam_appid
        LIMIT 15;
    """, (f"%{q}%",))

    rows = cur.fetchall()
    conn.close()

    results = []
    for r in rows:
        results.append({
            "steam_appid": r[0],
            "name": r[1],
            "profile_img": r[2]
        })

    return {"results": results}


# -------------------------------
#   홈 경로 확인용 (Render 상태 점검)
# -------------------------------
@app.get("/")
async def root():
    return {"message": "SteamRank Backend is running!"}
