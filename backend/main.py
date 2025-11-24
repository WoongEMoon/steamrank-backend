from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from datetime import datetime
from typing import List

DB = {
    "host": "localhost",
    "dbname": "Steam_Rank",
    "user": "postgres",
    "password": "1234",
    "port": 5432
}

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_conn():
    return psycopg2.connect(**DB)

@app.get("/api/rankings")
def get_rankings(date: str):

    conn = get_conn()
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


@app.get("/api/search")
def search_games(q: str):
    conn = get_conn()
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
