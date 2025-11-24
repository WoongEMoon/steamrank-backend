import psycopg2
import requests
from urllib.parse import quote

# ---------------- 설정 ----------------

DB_CONFIG = dict(
    dbname="Steam_Rank",
    user="postgres",
    password="1234",
    host="localhost",
    port=5432,
)

# 네가 사용 중인 한국 스팀 텍스트 파일 경로
TXT_PATH = r"C:\SteamRank\SteamRankFinal.txt"

# --------------------------------------


def get_db_conn():
    return psycopg2.connect(**DB_CONFIG)


def clean_title(line: str):
    """
    txt 한 줄에서 '검색용 게임 이름'이랑 'DB에서 찾을 원본 문자열'을 뽑는다.
    예시:
    "Teamfight Manager | 팀파이트 매니저 ( 2021 | ... )"
      -> search_title = "Teamfight Manager"
    """
    orig = line.strip()
    if not orig:
        return None, None

    # 앞부분에 '중 >', 'ㄱ >' 같은 구분자 있으면 잘라내기
    if ">" in orig[:10]:
        orig = orig.split(">", 1)[1].strip()

    # 괄호 앞까지만 사용
    base = orig.split("(", 1)[0].strip()

    # 영어 제목이 앞에 있고, ' | ' 로 한글 제목/기타가 붙는 경우가 많음
    if "|" in base:
        base = base.split("|", 1)[0].strip()

    # 양쪽 따옴표, 공백 정리
    base = base.strip(" \"'")

    if not base:
        return None, None

    return base, orig


def search_steam_app(search_title: str):
    """
    Steam 커뮤니티 검색으로 AppID, 이름, 로고 이미지를 찾는다.
    API 키 필요 없음.
    """
    url = "https://steamcommunity.com/actions/SearchApps/" + quote(search_title)
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    data = r.json()

    if not data:
        return None

    # 일단 첫 번째 결과를 사용
    return {
        "appid": int(data[0]["appid"]),
        "name": data[0].get("name", ""),
        "logo": data[0].get("logo", ""),
    }


def fetch_store_details(appid: int):
    """
    appdetails API 로 가격 / 헤더 이미지 / 리뷰 수 등을 가져온다.
    """
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=kr&l=korean"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    data = r.json()

    info = data.get(str(appid))
    if not info or not info.get("success"):
        return {}

    d = info.get("data", {})

    header_img = d.get("header_image") or ""
    is_free = d.get("is_free")
    price_overview = d.get("price_overview") or {}
    total_reviews = d.get("recommendations", {}).get("total")  # 없을 수도 있음

    if is_free:
        price = "Free"
    elif price_overview:
        # "₩ 20,500" 같은 문자열이 있을 수도 있음
        price = price_overview.get("final_formatted") or str(price_overview.get("final", ""))
    else:
        price = ""

    return {
        "header_img": header_img,
        "price": price,
        "total_reviews": total_reviews,
    }


def main():
    conn = get_db_conn()
    cur = conn.cursor()

    with open(TXT_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    print(f"총 {len(lines)}개 줄 처리 시작")

    for line in lines:
        search_title, orig_line = clean_title(line)
        if not search_title:
            continue

        print(f"\n▶ '{orig_line}'")
        print(f"   → 검색용 제목: '{search_title}'")

        # DB에서 해당 게임 찾기 (이름에 검색용 제목이 포함된 행)
        cur.execute(
            """
            SELECT appid, name, steam_appid
            FROM games
            WHERE name ILIKE %s
            ORDER BY appid
            LIMIT 1
            """,
            (f"%{search_title}%",),
        )
        row = cur.fetchone()

        if not row:
            print("   ❌ DB에서 해당 이름을 가진 게임을 찾지 못함 (먼저 games 테이블에 잘 들어갔는지 확인 필요)")
            continue

        appid_local, db_name, db_steam_appid = row
        print(f"   → DB 매칭: appid={appid_local}, name='{db_name}'")

        if db_steam_appid:
            print(f"   ↩ 이미 steam_appid={db_steam_appid} 로 등록되어 있어서 건너뜀")
            continue

        # 스팀에서 검색
        try:
            info = search_steam_app(search_title)
        except Exception as e:
            print(f"   ❌ Steam 검색 오류: {e}")
            continue

        if not info:
            print("   ❌ Steam 검색 결과 없음")
            continue

        steam_appid = info["appid"]
        steam_name = info["name"]
        print(f"   ✔ 검색 성공: [{steam_appid}] {steam_name}")

        # 스토어 정보 가져오기 (이미지/가격/리뷰)
        try:
            details = fetch_store_details(steam_appid)
        except Exception as e:
            print(f"   ⚠ appdetails 가져오기 실패(그래도 appid는 저장함): {e}")
            details = {}

        header_img = details.get("header_img")
        price = details.get("price")
        total_reviews = details.get("total_reviews")

        # DB 업데이트
        print("   → DB 업데이트 중...")
        cur.execute(
            """
            UPDATE games
            SET steam_appid = %s,
                profile_img = COALESCE(%s, profile_img),
                price = COALESCE(%s, price),
                total_reviews = COALESCE(%s, total_reviews)
            WHERE appid = %s
            """,
            (steam_appid, header_img, price, total_reviews, appid_local),
        )
        conn.commit()
        print("   ✅ 업데이트 완료")

    cur.close()
    conn.close()
    print("\n🎉 자동 매칭 스크립트 실행 완료!")


if __name__ == "__main__":
    main()
