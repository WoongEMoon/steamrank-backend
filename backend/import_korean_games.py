import psycopg2

TXT_FILE = r"C:\SteamRank\SteamRankKorea.txt"   # 너가 보낸 txt 파일 위치

def get_db_conn():
    return psycopg2.connect(
        dbname="Steam_Rank",
        user="postgres",
        password="1234",
        host="localhost"
    )

def insert_games():
    conn = get_db_conn()
    cur = conn.cursor()

    print("📘 한국 스팀 게임 리스트 불러오는 중...")

    with open(TXT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            name = line.strip()
            if not name:
                continue

            print(f"등록 중 → {name}")

            cur.execute("INSERT INTO games (name) VALUES (%s)", (name,))
            conn.commit()

    cur.close()
    conn.close()
    print("🎉 한국 스팀 게임 DB 등록 완료!")

if __name__ == "__main__":
    insert_games()
