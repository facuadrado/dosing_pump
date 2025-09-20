import sqlite3
from uuid import uuid4
from datetime import datetime
from typing import List, Tuple, Optional

class SQliteClient:
    RAW_LOGS_TABLE_NAME = "raw_logs"
    LOGS_TABLE_NAME = "logs"
    SCHEDULES_TABLE_NAME = "schedules"
    REMAINING_TABLE_NAME = "remaining"

    def __init__(
            self,
            logs_path: str = "/mnt/logs.db",
            schedules_path: str = "/mnt/schedules.db",
            remaining_path: str = "/mnt/remaining.db"
            ) -> None:
        self.logs_path = logs_path
        self.schedules_path = schedules_path
        self.remaining_path = remaining_path

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
        with sqlite3.connect(self.schedules_path) as conn:
            cur = conn.cursor()
            cur.executescript(
                f"""
                CREATE TABLE IF NOT EXISTS {self.SCHEDULES_TABLE_NAME} (
                    head INTEGER PRIMARY KEY,
                    total_dose REAL,
                    doses_per_day INTEGER
                );

                INSERT OR IGNORE INTO {self.SCHEDULES_TABLE_NAME} (head, total_dose, doses_per_day)
                VALUES (1, NULL, NULL);

                INSERT OR IGNORE INTO {self.SCHEDULES_TABLE_NAME} (head, total_dose, doses_per_day)
                VALUES (2, NULL, NULL);

                """
                )
            conn.commit()

        with sqlite3.connect(self.remaining_path) as conn:
            cur = conn.cursor()
            cur.executescript(
                f"""
                CREATE TABLE IF NOT EXISTS {self.REMAINING_TABLE_NAME} (
                    head INTEGER PRIMARY KEY,
                    remaining REAL
                );

                INSERT OR IGNORE INTO {self.REMAINING_TABLE_NAME} (head, remaining)
                VALUES (1, NULL);

                INSERT OR IGNORE INTO {self.REMAINING_TABLE_NAME} (head, remaining)
                VALUES (2, NULL);

                """
                )
            conn.commit()

    def update_remaining(self, head: int, ml: float) -> None:
        with sqlite3.connect(self.remaining_path) as conn:
            cur = conn.cursor()
            cur.execute(
                f"""
                UPDATE {self.REMAINING_TABLE_NAME} SET remaining = remaining - ? WHERE head = ?
                """,
                (ml, head)
            )
            conn.commit()
        return
    
    def set_remaining(self, head: int, ml: float) -> None:
        with sqlite3.connect(self.remaining_path) as conn:
            cur = conn.cursor()
            cur.execute(
                f"""
                UPDATE {self.REMAINING_TABLE_NAME} SET remaining = ? WHERE head = ?
                """,
                (ml, head)
            )
            conn.commit()
        return
    
    def get_remaining(self) -> dict:
        result = {}
        with sqlite3.connect(self.remaining_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(f"SELECT head, remaining FROM {self.REMAINING_TABLE_NAME}")
            rows = cur.fetchall()
            for row in rows:
                result[row["head"]] = row["remaining"]
        return result

    def update_schedule(self, head: int, total_dose: float, doses_per_day: int) -> None:
        with sqlite3.connect(self.schedules_path) as conn:
            cur = conn.cursor()
            if total_dose is None and doses_per_day is None:
                cur.execute(
                    f"""
                    UPDATE {self.SCHEDULES_TABLE_NAME}
                    SET total_dose = NULL, doses_per_day = NULL
                    WHERE head = ?
                    """,
                    (head,)
                )
            else:
                cur.execute(
                    f"""
                    UPDATE {self.SCHEDULES_TABLE_NAME}
                    SET total_dose = ?, doses_per_day = ?
                    WHERE head = ?
                    """,
                    (total_dose, doses_per_day, head)
                )
            conn.commit()
        return

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
                DO UPDATE SET {column} = COALESCE({column}, 0) + excluded.{column}
                """,
                (
                    now.date().isoformat(),
                    now.strftime("%H:00"),
                    ml,
                ),
            )
            conn.commit()
        return
    
    def get_todays_total(self) -> Tuple[Optional[float], Optional[float]]:
        today = datetime.now().date().isoformat()
        result = {}
        with sqlite3.connect(self.schedules_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(f"SELECT total_dose AS head1_total FROM {self.SCHEDULES_TABLE_NAME} WHERE head = 1")
            row = cur.fetchone()
            head1_total = row["head1_total"] if row is not None else 0.0

            cur.execute(f"SELECT total_dose AS head2_total FROM {self.SCHEDULES_TABLE_NAME} WHERE head = 2")
            row = cur.fetchone()
            head2_total = row["head2_total"] if row is not None else 0.0

            result["head1"] = {"total_dose": head1_total if head1_total is not None else 0.0, "today_total": 0.0}
            result["head2"] = {"total_dose": head2_total if head2_total is not None else 0.0, "today_total": 0.0}

        with sqlite3.connect(self.logs_path) as conn:
            cur = conn.cursor()
            cur.execute(
                f"""
                SELECT 
                    SUM(head1) as total_head1,
                    SUM(head2) as total_head2
                FROM {self.LOGS_TABLE_NAME}
                WHERE date = ?
                """,
                (today,)
            )
            row = cur.fetchone()
            total_head1 = row[0] if row[0] is not None else 0.0
            total_head2 = row[1] if row[1] is not None else 0.0
            result["head1"]["today_total"] = total_head1
            result["head2"]["today_total"] = total_head2
            return result

    def fetch_all_logs(self, table_name, days = 7) -> List[Tuple[str, str, int, str, float, str]]:
        with sqlite3.connect(self.logs_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(f"SELECT * FROM {table_name} WHERE date >= date('now', '-{days} day')")
            rows = cur.fetchall()
        return [dict(r) for r in rows]
    
    def fetch_all_schedules(self, days = 7) -> List[Tuple[str, str, int, str, float, str]]:
        with sqlite3.connect(self.schedules_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(f"SELECT * FROM {self.SCHEDULES_TABLE_NAME}")
            rows = cur.fetchall()
        return {
            head: {
                "total_dose": total_dose,
                "doses_per_day": doses_per_day
            }
            for head, total_dose, doses_per_day in rows
        }