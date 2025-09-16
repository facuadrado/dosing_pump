import sqlite3
from uuid import uuid4
from datetime import datetime
from typing import List, Tuple, Optional

class SQliteClient:
    RAW_LOGS_TABLE_NAME = "raw_logs"
    LOGS_TABLE_NAME = "logs"

    def __init__(
            self,
            logs_path: str = "/mnt/logs.db",
            ) -> None:
        self.logs_path = logs_path

        self._create_tables()

    def _create_tables(self) -> None:
        with sqlite3.connect(self.logs_path) as conn:
            cur = conn.cursor()
            cur.executescript(
                f"""
                CREATE TABLE IF NOT EXISTS {self.RAW_LOGS_TABLE_NAME} (
                    id TEXT PRIMARY KEY,
                    date TEXT,
                    head INTEGER,
                    time TEXT,
                    ml REAL,
                    mode TEXT CHECK(mode IN ('Manual', 'Scheduled', 'Primer'))
                );

                CREATE TABLE IF NOT EXISTS {self.LOGS_TABLE_NAME} (
                    date TEXT NOT NULL,
                    hour TEXT NOT NULL,
                    head1 REAL DEFAULT NULL,
                    head2 REAL DEFAULT NULL,
                    PRIMARY KEY (date, hour)
                );
                
                """
                )
            conn.commit()

    def insert_raw_entry(self, head: int, ml: float, mode: str) -> str:
        entry_id = str(uuid4())
        now = datetime.now()
        with sqlite3.connect(self.logs_path) as conn:
            cur = conn.cursor()
            cur.execute(
                f"""
                INSERT INTO {self.RAW_LOGS_TABLE_NAME} (id, date, head, time, ml, mode)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    entry_id,
                    now.date().isoformat(),
                    head,
                    now.isoformat(),
                    ml,
                    mode,
                ),
            )
            conn.commit()
        return entry_id
    
    def insert_entry(self, head: int, ml: float) -> None:
        now = datetime.now()
        with sqlite3.connect(self.logs_path) as conn:
            cur = conn.cursor()

            column = f"head{head}"

            cur.execute(
                f"""
                INSERT INTO {self.LOGS_TABLE_NAME} (date, hour, {column})
                VALUES (?, ?, ?)

                ON CONFLICT(date, hour)
                DO UPDATE SET {column} = {column} + excluded.{column}
                """,
                (
                    now.date().isoformat(),
                    now.strftime("%H:00"),
                    ml,
                ),
            )
            conn.commit()
        return

    def fetch_all(self, table_name) -> List[Tuple[str, str, int, str, float, str]]:
        with sqlite3.connect(self.logs_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(f"SELECT * FROM {table_name}")
            rows = cur.fetchall()
        return [dict(r) for r in rows]