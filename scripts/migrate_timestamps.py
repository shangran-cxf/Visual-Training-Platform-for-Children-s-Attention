"""一次性迁移：将数据库中所有 UTC 时间戳转为北京时间（+8小时）。
处理两种格式：SQLite 格式 (YYYY-MM-DD HH:MM:SS) 和 ISO 格式 (带 T 和 Z)。
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from database.db import get_db_connection

TIMESTAMP_COLUMNS = [
    # (table, column)
    ("training_sessions", "start_time"),
    ("training_sessions", "end_time"),
    ("training_sessions", "last_activity"),
    ("session_summaries", "created_at"),
    ("game_raw_data", "timestamp"),
    ("vision_raw_data", "timestamp"),
    ("detection_data", "timestamp"),
    ("parents", "created_at"),
    ("children", "created_at"),
    ("forum_posts", "created_at"),
    ("forum_posts", "updated_at"),
    ("forum_comments", "created_at"),
    ("forum_votes", "created_at"),
    ("user_badges", "earned_at"),
    ("favorites", "created_at"),
    ("child_reports", "period_start"),
    ("child_reports", "period_end"),
    ("child_reports", "report_date"),
    ("child_reports", "created_at"),
    ("processed_requests", "processed_at"),
]


def shift_iso_timestamp(val: str) -> str | None:
    """将 ISO 格式的 UTC 时间字符串加 8 小时，返回 SQLite 格式"""
    if not val:
        return None

    # ISO 格式: 2026-05-28T08:12:06.123Z 或 2026-05-28T08:12:06Z
    if "T" in val:
        from datetime import datetime, timedelta, timezone

        s = val.replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(s)
        except ValueError:
            return None
        dt = dt.astimezone(timezone(timedelta(hours=8)))
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    # SQLite 格式: 2026-05-28 08:12:06 或 2026-05-28 08:12:06.123456
    # 直接用 SQLite 的 datetime() 函数处理
    return None  # 返回 None 表示用 SQL 处理


def main():
    conn = get_db_connection()
    conn.execute("PRAGMA busy_timeout = 5000")

    total_updated = 0

    for table, col in TIMESTAMP_COLUMNS:
        # 先检查列是否存在
        cols = conn.execute(f"PRAGMA table_info({table})").fetchall()
        col_names = [c[1] for c in cols]
        if col not in col_names:
            print(f"跳过 {table}.{col}（列不存在）")
            continue

        # 查非空行数
        total = conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} IS NOT NULL AND {col} != ''").fetchone()[0]
        if total == 0:
            print(f"跳过 {table}.{col}（无数据）")
            continue

        # 取一个样本判断格式
        sample = conn.execute(f"SELECT {col} FROM {table} WHERE {col} IS NOT NULL AND {col} != '' LIMIT 1").fetchone()
        if not sample:
            continue

        sample_val = sample[0]

        if "T" in str(sample_val):
            # ISO 格式 — 用 Python 逐行转换
            rows = conn.execute(f"SELECT rowid, {col} FROM {table} WHERE {col} IS NOT NULL AND {col} != ''").fetchall()
            updated = 0
            for rowid, val in rows:
                new_val = shift_iso_timestamp(val)
                if new_val:
                    conn.execute(
                        f"UPDATE {table} SET {col} = ? WHERE rowid = ?",
                        (new_val, rowid),
                    )
                    updated += 1
            print(f"{table}.{col}: ISO格式, 更新 {updated}/{total}")
            total_updated += updated
        else:
            # SQLite 格式 — 用 SQL 批量转换
            conn.execute(
                f"UPDATE {table} SET {col} = datetime({col}, '+8 hours') WHERE {col} IS NOT NULL AND {col} != ''"
            )
            print(f"{table}.{col}: SQLite格式, 批量更新 {total}")
            total_updated += total

    conn.commit()
    conn.close()

    print(f"\n迁移完成，共更新 {total_updated} 条记录")


if __name__ == "__main__":
    main()
