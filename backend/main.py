from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import requests
from datetime import datetime

app = FastAPI()

# ====================================================
# CORS (Netlify 프론트 연결)
# ====================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====================================================
# DB 연결
# ====================================================
def get_db():
    return psycopg2.connect(
        host="dpg-ctxxxxxx8enbs73hb0kg-a.oregon-postgres.render.com",
        dbname="steam_rank",
        user="steam_rank_user",
        password="너의DB비번",
        port="5432"
    )


# ====================================================
# 기본 체크
# ====================================================
@app.get("/")
def home():
    return {"message": "SteamRank Backend is running!"}


# ====================================================
# rankings 테이블 생성
# ====================================================
@app.get("/create_table")
def create_table():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS rankings (
            date TEXT,
            rank INTEGER,
            appid INTEGER,
            name TEXT,
            concurrent_players INTEGER,
            PRIMARY KEY(date, rank)
        );
    """)
    conn.commit()
    conn.close()
    return {"status": "success", "message": "rankings table created!"}


# ====================================================
# games 테이블 생성
# ====================================================
@app.get("/create_games_table")
def create_games_table():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS games (
            appid INTEGER PRIMARY KEY,
            name TEXT
        );
    """)
    conn.commit()
    conn.close()
    return {"status": "success", "message": "games table created!"}


# ====================================================
# ★ 한국 게임 데이터 394개 넣기 (자동)
# ====================================================
KOREAN_GAMES = [
    # appid, name 형태로 저장
    (1599340, "LOST ARK"),
    (216150, "MapleStory"),
    (340560, "던전앤파이터"),
    # ... 너의 394개 전체를 여기에 그대로 붙여넣으면 됨
]

@app.get("/update_games")
def update_games():
    conn = get_db()
    cur = conn.cursor()

    count = 0
    for appid, name in KOREAN_GAMES:
        cur.execute("""
            INSERT INTO games (appid, name)
            VALUES (%s, %s)
            ON CONFLICT (appid)
            DO NOTHING;
        """, (appid, name))
        count += 1

    conn.commit()
    conn.close()

    return {"status": "success", "inserted": count}


# ====================================================
# SteamCharts TOP100 → rankings 저장
# ====================================================
@app.get("/update")
def update_rankings():
    today = datetime.utcnow().strftime("%Y-%m-%d")

    url = "https://api.steampowered.com/ISteamChartsService/GetMostPlayedGames/v1/?key=07AB8AE83B71291C1D92C31A292BD75F"
    res = requests.get(url).json()

    if "response" not in res or "ranks" not in res["response"]:
        return {"error": "Steam API 오류"}

    game_list = res["response"]["ranks"]

    conn = get_db()
    cur = conn.cursor()

    for g in game_list:
        rank = g.get("rank")
        appid = g.get("appid")
        name = g.get("name", f"Unknown ({appid})")
        players = g.get("concurrent_players", 0)

        cur.execute("""
            INSERT INTO rankings (date, rank, appid, name, concurrent_players)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (date, rank)
            DO UPDATE SET concurrent_players = EXCLUDED.concurrent_players;
        """, (today, rank, appid, name, players))

    conn.commit()
    conn.close()

    return {"status": "success", "message": "Rankings updated!"}


# ====================================================
# 한국 게임만 JOIN해서 랭킹 반환
# ====================================================
@app.get("/rank")
def get_rank(date: str):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT r.rank, g.name, r.concurrent_players, g.appid
        FROM rankings r
        JOIN games g ON r.appid = g.appid
        WHERE r.date = %s
        ORDER BY r.rank ASC;
    """, (date,))

    rows = cur.fetchall()
    conn.close()

    return [
        {"rank": r[0], "name": r[1], "players": r[2], "appid": r[3]}
        for r in rows
    ]


# ====================================================
# 자동완성 검색
# ====================================================
@app.get("/api/search")
def search_game(q: str):
    conn = get_db()
    cur = conn.cursor()

    search_q = f"%{q}%"
    cur.execute("""
        SELECT name FROM games
        WHERE name ILIKE %s
        ORDER BY name ASC
        LIMIT 20;
    """, (search_q,))

    rows = cur.fetchall()
    conn.close()

    return {"results": [r[0] for r in rows]}


# ====================================================
# React용 rankings API
# ====================================================
@app.get("/api/rankings")
def api_rankings(date: str):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT r.rank, g.name, r.concurrent_players
        FROM rankings r
        JOIN games g ON r.appid = g.appid
        WHERE r.date = %s
        ORDER BY r.rank ASC;
    """, (date,))

    rows = cur.fetchall()
    conn.close()

    return {
        "rankings": [
            {"rank": r[0], "name": r[1], "players": r[2]}
            for r in rows
        ]
    }
