"""轻量数据库迁移：SQLite 下幂等补列，不引入 Alembic。

只做"缺列则 ALTER TABLE ADD COLUMN"，保证老库平滑升级、可重复执行。
"""
import logging
from sqlalchemy import text
from app.models.database import engine

logger = logging.getLogger(__name__)

# 表 -> [(列名, 列定义)]
_ADD_COLUMNS = {
    "health_records": [
        ("elder_id", "INTEGER DEFAULT 1"),
        ("record_type", "VARCHAR(20)"),
        ("systolic", "INTEGER"),
        ("diastolic", "INTEGER"),
        ("value", "FLOAT"),
        ("unit", "VARCHAR(20)"),
        ("measured_at", "DATETIME"),
    ],
    "conversations": [
        ("parent_id", "INTEGER"),
        ("anchor_term", "VARCHAR(100)"),
    ],
    "alerts": [
        ("snapshot_url", "VARCHAR(255)"),
    ],
}


def _existing_columns(conn, table: str):
    rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return {r[1] for r in rows}  # 第2列是列名


def run_migrations():
    """启动时调用：给老表补齐新列，已存在则跳过。"""
    with engine.begin() as conn:
        for table, columns in _ADD_COLUMNS.items():
            # 表不存在则跳过（create_all 会按新模型建）
            exists = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=:t"
            ), {"t": table}).fetchone()
            if not exists:
                continue
            have = _existing_columns(conn, table)
            for col_name, col_def in columns:
                if col_name not in have:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def}"))
                    logger.info("迁移：表 %s 补列 %s", table, col_name)
