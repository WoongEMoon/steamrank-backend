from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
from datetime import datetime

app = FastAPI()

# -------------------------------------------------
# CORS 설정
# -------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# Render PostgreSQL 연결 정보
# -------------------------------------------------
DB = {
    "host": "dpg-d4i86fkhg0os73fi4keg-a",
    "dbname": "steamrank_db",
    "user": "steamrank_db_user",
    "password": "xkUGR7Y35UidHw6HooptU41A0GXXg1Jh",
    "port": 5432,
}

def get_db():
    return psycopg2.connect(
        host=DB["host"],
        database=DB["dbname"],
        user=DB["user"],
        password=DB["password"],
        port=DB["port"],
        cursor_factory=RealDictCursor,
    )

# -------------------------------------------------
# 루트 페이지
# -------------------------------------------------
@app.get("/")
def home():
    return {"message": "SteamRank Backend is running!"}

# -------------------------------------------------
# 테이블 자동 생성 API
# -------------------------------------------------
@app.get("/create_table")
def create_table():
    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS rankings (
                date TEXT,
                rank INTEGER,
                appid INTEGER,
                name TEXT,
                concurrent_players INTEGER,
                PRIMARY KEY(date, appid)
            )
        """
        )

        conn.commit()
        cur.close()
        conn.close()

        return {"status": "success", "message": "Table 'rankings' created."}
    except Exception as e:
        return {"error": str(e)}

# -------------------------------------------------
# 게임 검색 API (자동완성용)
# -------------------------------------------------
@app.get("/search")
def search_games(q: str):
    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT DISTINCT name
            FROM rankings
            WHERE LOWER(name) LIKE LOWER(%s)
            ORDER BY name ASC
            LIMIT 20
        """,
            (f"%{q}%",),
        )

        rows = cur.fetchall()
        cur.close()
        conn.close()

        # RealDictCursor라서 각 row는 {"name": "..."} 형태
        results = [row["name"] for row in rows]

        return {"results": results}
    except Exception as e:
        return {"error": str(e)}

# -------------------------------------------------
# /update → SteamCharts API + DB 저장
# -------------------------------------------------
@app.get("/update")
def update_database():
    try:
        conn = get_db()
        cur = conn.cursor()

        # SteamCharts API 호출
        url = "https://api.steampowered.com/ISteamChartsService/GetMostPlayedGames/v1/?key=0E813F938A97F67C2C1B778C7691AF44"
        res = requests.get(url, timeout=10)
        data = res.json()

        ranks = data.get("response", {}).get("ranks", [])
        if not ranks:
            return {"error": "No data received from SteamCharts API"}

        today = datetime.now().strftime("%Y-%m-%d")

        for game in ranks:
            rank = game.get("rank")
            appid = game.get("appid")
            # name 키가 없을 때를 대비한 방어 코드
            name = game.get("name", f"Unknown ({appid})")
            players = game.get("concurrent_players", 0)

            cur.execute(
                """
                INSERT INTO rankings (date, rank, appid, name, concurrent_players)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (date, appid)
                DO UPDATE SET
                    rank = EXCLUDED.rank,
                    name = EXCLUDED.name,
                    concurrent_players = EXCLUDED.concurrent_players;
            """,
                (today, rank, appid, name, players),
            )

        conn.commit()
        cur.close()
        conn.close()

        return {"status": "success", "message": "Database updated!"}
    except Exception as e:
        return {"error": str(e)}

# -------------------------------------------------
# /rank?date=YYYY-MM-DD → 특정 날짜 랭킹 조회
# -------------------------------------------------
@app.get("/rank")
def get_rank(date: str):
    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT rank, appid, name, concurrent_players
            FROM rankings
            WHERE date = %s
            ORDER BY rank ASC
        """,
            (date,),
        )

        rows = cur.fetchall()
        cur.close()
        conn.close()

        # RealDictCursor → rows는 [{"rank":..., "appid":..., ...}, ...]
        # React에서 Array.isArray(data)로 바로 사용할 수 있게 그대로 반환
        return rows
    except Exception as e:
        return {"error": str(e)}
