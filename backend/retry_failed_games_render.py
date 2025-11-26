import requests
import psycopg2

FAILED_FILE = "failed_games.txt"

def load_failed_games():
    failed = []
    with open(FAILED_FILE, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) >= 2:
                appid, name = parts[0], parts[1]
                failed.append((appid, name))
    return failed

def retry_failed():
    failed_games = load_failed_games()
    print(f"총 {len(failed_games)}개 실패 게임 재시도 중...")

    for appid, name in failed_games:
        # 기존의 Steam API 요청 로직 그대로 가져오기
        url = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=kr&l=english"
        response = requests.get(url)

        if response.status_code != 200:
            print(f"[RETRY FAIL] {appid} {name} → 여전히 실패")
            continue

        data = response.json().get(str(appid), {})
        if not data.get("success", False):
            print(f"[RETRY FAIL] {appid} {name} → success false")
            continue

        # DB에 삽입하기 (너의 기존 insert 함수 그대로)
        insert_game_to_db(appid, name, data["data"])
        print(f"[RETRY OK] {appid} {name}")

if __name__ == "__main__":
    retry_failed()
