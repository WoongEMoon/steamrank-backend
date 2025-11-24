import psycopg2

try:
    conn = psycopg2.connect(
        dbname="steam_rank",
        user="postgres",
        password="1234",  # 네가 설정한 비밀번호
        host="localhost",
        port=5432
    )
    print("DB connection OK")
    conn.close()
except Exception as e:
    print("DB connection FAILED")
    print("Error type:", type(e))
    print("Error repr:", repr(e))