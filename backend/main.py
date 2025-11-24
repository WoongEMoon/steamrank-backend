from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
from datetime import datetime, date

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
    return {"message": "SteamRank Backend (Korean Games) is running!"}


# -------------------------------------------------
# 테이블 자동 생성 API
# games / daily_players
# -------------------------------------------------
@app.get("/create_tables")
def create_tables():
    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS games (
                appid           INTEGER PRIMARY KEY,
                name            TEXT,
                release_date    DATE,
                developer       TEXT,
                steam_appid     INTEGER,
                profile_img     TEXT,
                price           TEXT,
                total_reviews   INTEGER,
                players         INTEGER,
                current_players INTEGER,
                peak_players    INTEGER
            );
        """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_players (
                appid   INTEGER,
                date    DATE,
                players INTEGER,
                PRIMARY KEY (appid, date)
            );
        """
        )

        conn.commit()
        cur.close()
        conn.close()

        return {"status": "success", "message": "Tables 'games' and 'daily_players' created."}
    except Exception as e:
        return {"error": str(e)}


# -------------------------------------------------
# 🔎 한국 게임 검색 (자동완성)
# -------------------------------------------------
@app.get("/search")
def search_games(q: str):
    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT DISTINCT name
            FROM games
            WHERE LOWER(name) LIKE LOWER(%s)
            ORDER BY name ASC
            LIMIT 20
        """,
            (f"%{q}%",),
        )

        rows = cur.fetchall()
        cur.close()
        conn.close()

        results = [row["name"] for row in rows]
        return {"results": results}
    except Exception as e:
        return {"error": str(e)}


# -------------------------------------------------
# 📥 /update : 한국 게임 394개의 동접자 최신화
#  - public.games 에 있는 steam_appid를 기준으로
#  - GetNumberOfCurrentPlayers API 호출
#  - games.current_players + daily_players 에 반영
# -------------------------------------------------
STEAM_PLAYER_API = (
    "https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/"
)


@app.get("/update")
def update_korean_games():
    try:
        conn = get_db()
        cur = conn.cursor()

        # 1) 한국 게임 목록 가져오기 (steam_appid 있는 것만)
        cur.execute(
            """
            SELECT appid, steam_appid
            FROM games
            WHERE steam_appid IS NOT NULL
        """
        )
        games = cur.fetchall()

        if not games:
            cur.close()
            conn.close()
            return {"error": "No games found in 'games' table. Please import data first."}

        today = date.today()

        updated_count = 0

        for row in games:
            appid = row["appid"]
            steam_appid = row["steam_appid"]

            try:
                resp = requests.get(
                    STEAM_PLAYER_API, params={"appid": steam_appid}, timeout=10
                )
                data = resp.json()
                players = data.get("response", {}).get("player_count", 0)
            except Exception:
                players = 0

            # games.current_players 갱신
            cur.execute(
                """
                UPDATE games
                SET current_players = %s
                WHERE appid = %s
            """,
                (players, appid),
            )

            # daily_players upsert
            cur.execute(
                """
                INSERT INTO daily_players (appid, date, players)
                VALUES (%s, %s, %s)
                ON CONFLICT (appid, date)
                DO UPDATE SET players = EXCLUDED.players
            """,
                (appid, today, players),
            )

            updated_count += 1

        conn.commit()
        cur.close()
        conn.close()

        return {
            "status": "success",
            "message": f"Updated {updated_count} Korean games for {today}.",
        }
    except Exception as e:
        return {"error": str(e)}


# -------------------------------------------------
# 📊 /rank?date=YYYY-MM-DD
#   - 한국 게임만
#   - 해당 날짜의 동접자를 기준으로 내림차순 정렬
#   - React는 여기 결과를 그대로 카드로 그림
# -------------------------------------------------
@app.get("/rank")
def get_rank(date: str):
    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT 
                g.appid,
                g.steam_appid,
                g.name,
                g.profile_img,
                g.price,
                dp.players
            FROM daily_players dp
            JOIN games g ON dp.appid = g.appid
            WHERE dp.date = %s
            ORDER BY dp.players DESC, g.name ASC
        """,
            (date,),
        )

        rows = cur.fetchall()
        cur.close()
        conn.close()

        # rank 번호를 여기서 계산해서 붙여줌
        result = []
        for idx, row in enumerate(rows, start=1):
            result.append(
                {
                    "rank": idx,
                    "appid": row["appid"],
                    "steam_appid": row["steam_appid"],
                    "name": row["name"],
                    "profile_img": row["profile_img"],
                    "price": row["price"],
                    "players": row["players"],
                }
            )

        return result
    except Exception as e:
        return {"error": str(e)}
