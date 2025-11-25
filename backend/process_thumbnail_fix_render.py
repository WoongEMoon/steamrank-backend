import psycopg2
import requests

# ===============================
# 🔵 Render PostgreSQL 설정
# ===============================
DB = {
    "host": "dpg-d4i86fkhg0os73fi4keg-a.oregon-postgres.render.com",
    "dbname": "steamrank_db",
    "user": "steamrank_db_user",
    "password": "xkUGR7Y35UidHw6HooptU41A0GXXg1Jh",
    "port": 5432,
    "sslmode": "require"
}

def get_conn():
    return psycopg2.connect(**DB)

# ===============================
# 썸네일 URL 가져오기
# ===============================
def get_thumbnail(appid):
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
    try:
        res = requests.get(url, timeout=8)
        data = res.json()

        if not data[str(appid)]["success"]:
            return None

        return data[str(appid)]["data"].get("header_image", None)

    except Exception as e:
        print(f"오류 ({appid}): {e}")
        return None

# ===============================
# DB 업데이트
# ===============================
def update_thumbnails():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT appid, steam_appid, name FROM games WHERE steam_appid IS NOT NULL;")
    games = cur.fetchall()

    print(f"총 {len(games)}개 썸네일 갱신 시작.")

    for appid, steam_appid, name in games:
        print(f"▶ {name} ({steam_appid}) 처리 중...")

        thumb = get_thumbnail(steam_appid)
        if thumb is None:
            print(f"❌ 이미지 없음\n")
            continue

        cur.execute("UPDATE games SET profile_img = %s WHERE appid = %s;",
                    (thumb, appid))
        conn.commit()

        print(f"✔ 저장됨: {thumb}\n")

    conn.close()
    print("\n🎉 모든 썸네일 갱신 완료!\n")

if __name__ == "__main__":
    update_thumbnails()
