from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
import os

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Netlify, Localhost 등 전체 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------
# 🔥 DB 연결 설정 (로컬 + Render 자동 전환)
# -------------------------------------------------------

def get_db_config():
    """
    Render에서는 DATABASE_URL(또는 환경변수들)을 자동 사용
    로컬에서는 기존 localhost DB 사용
    """

    # 1) Render 환경에서 자동 감지
    if "RENDER" in os.environ:
        return {
            "host": os.getenv("DB_HOST"),
            "dbname": os.getenv("DB_NAME"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "port": 5432
        }

    # 2) 로컬 실행 시 기존 설정 그대로 사용
    return {
        "host": "localhost",
        "dbname": "Steam_Rank",
        "user": "postgres",
        "password": "1234",
        "port": 5432
    }


def get_connection():
    """PostgreSQL 연결 함수 (로컬/Render 공용)"""
    config = get_db_config()
    try:
        return psycopg2.connect(
            host=config["host"],
            dbname=config["dbname"],
            user=config["user"],
            password=config["password"],
            port=config["port"],
        )
    except Exception as e:
        print("DB 연결 실패:", e)
        raise HTTPException(status_code=500, detail="Database connection error")


# -------------------------------------------------------
# 🔥 API: 날짜 기준 랭킹 가져오기
# -------------------------------------------------------

@app.get("/rank/{date}")
def get_rank(date: str):
    """
    날짜 기준 게임 랭킹 조회
    예: /rank/2025-11-24
    """

    conn = get_connection()
    cursor = conn.cursor()

    try:
        query = """
        SELECT game_name, current_players, peak_players, game_id
        FROM ranks
        WHERE date = %s
        ORDER BY rank ASC;
        """

        cursor.execute(query, (date,))
        rows = cursor.fetchall()

        if not rows:
            return {"warning": f"{date} 데이터 없음"}

        data = []
        for row in rows:
            data.append({
                "game_name": row[0],
                "current_players": row[1],
                "peak_players": row[2],
                "game_id": row[3]
            })

        return {"date": date, "data": data}

    except Exception as e:
        print("조회 오류:", e)
        raise HTTPException(status_code=500, detail="Query failed")
    finally:
        cursor.close()
        conn.close()


# -------------------------------------------------------
# 기본 홈
# -------------------------------------------------------
@app.get("/")
def home():
    return {"message": "SteamRank Backend is running!"}
