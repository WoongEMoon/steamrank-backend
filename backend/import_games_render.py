import psycopg2
import csv

DB = {
    "host": "dpg-d4i86fkhg0os73fi4keg-a.oregon-postgres.render.com",
    "dbname": "steamrank_db",
    "user": "steamrank_db_user",
    "password": "xkUGR7Y35UidHw6HooptU41A0GXXg1Jh",
    "port": 5432,
    "sslmode": "require"
}

CSV_FILE = "import_games.csv"  # Render에서는 같은 폴더에 업로드해야 함


def get_db_conn():
    return psycopg2.connect(
        host=DB["host"],
        dbname=DB["dbname"],
        user=DB["user"],
        password=DB["password"],
        port=DB["port"],
        sslmode=DB["sslmode"]
    )


def import_games():
    conn = get_db_conn()
    cur = conn.cursor()

    with open(CSV_FILE, newline='', encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # 헤더 스킵

        for row in reader:
            appid, name = row
            cur.execute(
                "INSERT INTO games (appid, name) VALUES (%s, %s) ON CONFLICT (appid) DO NOTHING;",
                (appid, name)
            )

    conn.commit()
    conn.close()
    print("✅ import_games 완료")


if __name__ == "__main__":
    import_games()
