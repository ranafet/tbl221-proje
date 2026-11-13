import sqlite3
from model.perflog import PerfLog

def get_db_connection():
    conn = sqlite3.connect('/var/lib/tbl221-record/tbl221-record.db')
    return conn

def close_db_connection(conn):
    conn.close()

def initialize_db():
    conn = get_db_connection()
    # check presence of table perfcount
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='perfcount';")
    result = cursor.fetchone()
    # if absent, create perfcount
    if result is None:
        cursor.execute("CREATE TABLE perfcount (id INTEGER PRIMARY KEY, timestamp INTEGER, used_ram INTEGER, free_ram INTEGER, cpu_usage REAL);")

    close_db_connection(conn)

def insert_perfcount(perf_log: PerfLog):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO perfcount (timestamp, used_ram, free_ram, cpu_usage) VALUES (?, ?, ?, ?);", (perf_log.timestamp, perf_log.used_ram, perf_log.free_ram, perf_log.cpu_usage))
    conn.commit()
    close_db_connection(conn)

def get_performance_readings() -> list[PerfLog]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, used_ram, free_ram, cpu_usage FROM perfcount;")
    results = cursor.fetchall()
    close_db_connection(conn)
    return [PerfLog(timestamp=row[0], used_ram=row[1], free_ram=row[2], cpu_usage=row[3]) for row in results]
