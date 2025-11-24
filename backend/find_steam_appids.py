import psycopg2
import requests
import time


def get_db_conn():
    return psycopg2.connect(
        dbname="Steam_Rank",
        user="postgres",
        password="1234",
        host="localhost"
    )


def search_steam_appid(game_name: str):
    """ 스팀 비공식 검색 API로 AppID 찾기 """
    url = f"https://steamcommunity.com/actions/SearchApps/{game_name}"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code != 200:
            return None
        results = res.json()

        if not results:
            return None

        # 정확도 높은 방식: 이름이 정확히 일치하면 우선 선택
        for r in results:
            if r["name"].lower() == game_name.lower():
                return r["appid"]

        # 정확 일치가 없다면 첫번째 결과를 선택
        return results[0]["appid"]

    except Exception as e:
        print(f"검색 실패 ({game_name}): {e}")
        return None


def update_all_games():
    conn = get_db_conn()
    cur = conn.cursor()

    # steam_appid 비어 있는 게임만 가져오기
    cur.execute("SELECT appid, name FROM games WHERE steam_appid IS NULL;")
    games = cur.fetchall()

    print(f"\n🔍 AppID가 없는 게임 수: {len(games)}\n")

    for appid, name in games:
        print(f"▶ '{name}' 검색 중...")

        steam_id = search_steam_appid(name)
        time.sleep(0.3)  # 너무 빠르게 요청하면 스팀에서 차단될 수 있음

        if steam_id is None:
            print(f"❌ AppID 못 찾음: {name}\n")
            continue

        # DB 업데이트
        cur.execute(
            "UPDATE games SET steam_appid = %s WHERE appid = %s",
            (steam_id, appid)
        )
        conn.commit()

        print(f"✔ AppID 등록됨 → {name}: {steam_id}\n")

    conn.close()
    print("🎉 모든 게임 AppID 자동 등록 완료!")


if __name__ == "__main__":
    update_all_games()
