from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import requests
from datetime import datetime

app = FastAPI()

# ---------------------------
# CORS (Netlify 프론트 연결)
# ---------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# DB 연결 함수
# ---------------------------
def get_db():
    return psycopg2.connect(
        host="dpg-ctxxxxxx8enbs73hb0kg-a.oregon-postgres.render.com",  # ← 너의 Render DB 호스트 입력
        dbname="steam_rank",
        user="steam_rank_user",
        password="너의DB비번",
        port="5432"
    )


# ---------------------------
# 홈 체크
# ---------------------------
@app.get("/")
def home():
    return {"message": "SteamRank Backend is running!"}


# ---------------------------
# rankings 테이블 생성
# ---------------------------
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


# ---------------------------
# games 테이블 생성
# ---------------------------
@app.get("/create_games_table")
def create_games_table():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS games (
            appid INTEGER PRIMARY KEY,
            name TEXT,
            release_date TEXT,
            developer TEXT,
            price TEXT,
            total_reviews INTEGER,
            players INTEGER,
            current_players INTEGER,
            peak_players INTEGER
        );
    """)
    conn.commit()
    conn.close()
    return {"status": "success", "message": "games table created!"}


# ---------------------------
# SteamCharts API에서 TOP 100 가져오기
# ---------------------------
@app.get("/update")
def update_rankings():
    # 오늘 날짜 구하기
    today = datetime.utcnow().strftime("%Y-%m-%d")

    # SteamCharts API 호출
    url = "https://api.steampowered.com/ISteamChartsService/GetMostPlayedGames/v1/?key=07AB8AE83B71291C1D92C31A292BD75F"
    res = requests.get(url).json()

    if "response" not in res or "ranks" not in res["response"]:
        return {"error": "Steam API 문제로 데이터 없음"}

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

    return {"status": "success", "message": "Database updated!"}


# ---------------------------
# 한국 게임만 필터링해서 순위 반환
# games 테이블 + rankings 테이블 JOIN
# ---------------------------
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

    result = []
    for row in rows:
        result.append({
            "rank": row[0],
            "name": row[1],
            "players": row[2],
            "appid": row[3]
        })

    return result


# ---------------------------
# 검색 자동완성 API
# ---------------------------
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


# ---------------------------
# rankings API (React용 정식 엔드포인트)
# ---------------------------
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
