"""时间处理工具模块 — 数据库直接存储北京时间

DB 中的时间戳均为北京时间（无时区标记），前端 new Date() 解析为本地时间即可正确显示。
前端上传的 UTC ISO 时间戳在入库前转为北京时间。
"""

from datetime import UTC, datetime, timedelta, timezone

BEIJING_TZ = timezone(timedelta(hours=8))
UTC = UTC

# 日期显示格式
FMT_DATETIME = "%Y-%m-%d %H:%M"
FMT_DATE = "%Y-%m-%d"
FMT_FULL = "%Y-%m-%d %H:%M:%S"


def now_beijing():
    """当前北京时间"""
    return datetime.now(BEIJING_TZ)


def now_utc():
    """当前 UTC 时间（仅用于需要 UTC 的运算）"""
    return datetime.now(UTC)


def beijing_today_str() -> str:
    """当前北京日期字符串，用于按天查询"""
    return now_beijing().strftime(FMT_DATE)


def beijing_now_str(fmt: str = FMT_DATE) -> str:
    """当前北京时间字符串"""
    return now_beijing().strftime(fmt)


def parse_db_timestamp(value):
    """解析数据库时间戳

    DB 中已有数据为北京时间（无时区标记），如 "2026-05-28 16:12:06"。
    兼容旧的 ISO 格式（如从 game_raw_data 等残留的前端上传数据）。

    返回北京时间 aware datetime，解析失败返回 None。
    """
    if not value:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=BEIJING_TZ)
        return value.astimezone(BEIJING_TZ)

    s = str(value).strip()
    if not s:
        return None

    if "T" in s:
        # ISO 8601（前端 UTC 时间）：先解析为 UTC，再转北京时间
        s = s.replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(s)
            return dt.astimezone(BEIJING_TZ)
        except ValueError:
            pass

    # SQLite 格式：YYYY-MM-DD HH:MM:SS 或带微秒
    try:
        dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S.%f") if "." in s else datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
        return dt.replace(tzinfo=BEIJING_TZ)
    except ValueError:
        pass

    # 只有日期
    try:
        dt = datetime.strptime(s, FMT_DATE)
        return dt.replace(tzinfo=BEIJING_TZ)
    except ValueError:
        pass

    # 最后尝试
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=BEIJING_TZ)
        return dt.astimezone(BEIJING_TZ)
    except ValueError:
        return None


def to_iso_string(value) -> str | None:
    """将 DB 时间戳转为 ISO 8601 字符串（无时区后缀），供 API 返回给前端

    "2026-05-28 16:12:06" → "2026-05-28T16:12:06"
    前端 new Date() 按本地时间解析，正好是北京时间。
    """
    dt = parse_db_timestamp(value)
    if dt is None:
        return value
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def to_beijing_string(value, fmt: str = FMT_DATETIME) -> str:
    """将 DB 时间戳格式化为北京时间字符串，用于展示"""
    dt = parse_db_timestamp(value)
    if dt is None:
        return str(value) if value else ""
    return dt.astimezone(BEIJING_TZ).strftime(fmt)


def to_date_string(value) -> str:
    """从时间戳提取日期（北京日期）"""
    dt = parse_db_timestamp(value)
    if dt is None:
        return str(value) if value else ""
    return dt.strftime(FMT_DATE)


def frontend_ts_to_db(value: str) -> str:
    """前端 UTC ISO 时间戳转为北京时间的 SQLite 格式，用于存入数据库

    "2026-05-28T08:12:06.123Z" → "2026-05-28 16:12:06"
    """
    dt = parse_db_timestamp(value)
    if dt is None:
        return value
    return dt.strftime(FMT_FULL)
