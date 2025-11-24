import psycopg2

def get_db_conn():
    return psycopg2.connect(
        dbname="Steam_Rank",
        user="postgres",   # 본인 pgAdmin 계정 이름
        password="1234",   # DB 비밀번호
        host="localhost",
        port=5432
    )

def import_games_from_txt(file_path):
    conn = get_db_conn()
    cur = conn.cursor()

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            name = line.strip()
            if not name:
                continue
            cur.execute("""
                INSERT INTO games (name)
                VALUES (%s)
                ON CONFLICT (name) DO NOTHING;
            """, (name,))

    conn.commit()
    cur.close()
    conn.close()
    print("✅ 게임 리스트 추가 완료")

if __name__ == "__main__":
    import_games_from_txt("C:/SteamRank/SteamRankKorea.txt")
