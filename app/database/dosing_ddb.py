import sqlite3
from uuid import uuid4
from datetime import datetime
from typing import List, Tuple, Optional

class DosingDDB:
    TABLE_NAME = "doser"
    SCHEMA = f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id TEXT PRIMARY KEY,
            date TEXT,
            head INTEGER,
            time TEXT,
            ml REAL,
            mode TEXT CHECK(mode IN ('Manual', 'Scheduled', 'Primer'))
        )
    """

    def __init__(self, db_path: str = "/mnt/doser.db") -> None:
        self.db_path = db_path
        self._create_table()

    def _create_table(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(self.SCHEMA)
            conn.commit()

    def insert_entry(self, head: int, ml: float, mode: str) -> str:
        entry_id = str(uuid4())
        now = datetime.now()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                INSERT INTO {self.TABLE_NAME} (id, date, head, time, ml, mode)
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

    def fetch_all(self) -> List[Tuple[str, str, int, str, float, str]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {self.TABLE_NAME}")
            entries = cursor.fetchall()
        return entries