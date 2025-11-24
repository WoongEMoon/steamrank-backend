from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()

# CORS 문제 방지
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STEAM_API_KEY = "0E813F938A97F67C2C1B778C7691AF44"

@app.get("/")
def home():
    return {"message": "SteamRank Backend is running!"}

# 🔍 검색 API: Steam store 검색 API 사용
@app.get("/api/search")
def search_games(query: str):
    try:
        url = f"https://steamcommunity.com/actions/SearchApps/{query}"
        response = requests.get(url)
        return response.json()
    except:
        return {"error": "Failed to fetch from Steam API"}

# 🏆 인기 게임 랭킹: Steam top sellers API (community unofficial)
@app.get("/api/rankings")
def get_rankings():
    try:
        url = "https://api.steampowered.com/ISteamChartsService/GetMostPlayedGames/v1/?key=" + STEAM_API_KEY
        res = requests.get(url)
        data = res.json()

        if "response" in data and "ranks" in data["response"]:
            return data["response"]["ranks"]

        return {"error": "Steam Ranking API changed or returned empty"}

    except Exception as e:
        return {"error": str(e)}
