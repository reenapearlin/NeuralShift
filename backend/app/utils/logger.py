"""Logging helpers for search and retrieval workflows."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from typing import Any, Dict, List, Optional, Sequence, Tuple

from sqlalchemy import inspect, text

from app.utils.metadata_filter import find_first_column, find_table, quote_ident


logger = logging.getLogger(__name__)


def discover_logs_table(db: Any) -> Optional[Tuple[str, List[str]]]:
    """Discover a compatible logs table for recording search activity."""
    bind = getattr(db, "bind", None) or db.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names()

    table = find_table(
        table_names=tables,
        preferred=["logs", "search_logs", "query_logs"],
        required_columns=[],
        inspector=inspector,
    )
    if not table:
        return None

    columns = [col["name"] for col in inspector.get_columns(table)]
    return table, columns


def log_search_event(
    db: Any,
    user_id: Optional[int],
    query: str,
    retrieved_case_ids: Sequence[Any],
) -> None:
    """Persist user search metadata and retrieved IDs into logs table if available."""
    discovered = discover_logs_table(db)
    if not discovered:
        logger.info(
            "Search log fallback | user_id=%s query=%s retrieved_case_ids=%s",
            user_id,
            query,
            list(retrieved_case_ids),
        )
        return

    table, columns = discovered
    cols = set(columns)

    field_map: Dict[str, Any] = {
        "user_id": user_id,
        "query": query,
        "timestamp": datetime.now(timezone.utc),
        "retrieved_case_ids": json.dumps(list(retrieved_case_ids)),
    }

    column_aliases = {
        "user_id": ["user_id"],
        "query": ["query", "search_query"],
        "timestamp": ["timestamp", "created_at", "query_time"],
        "retrieved_case_ids": ["retrieved_case_ids", "case_ids", "retrieved_ids"],
    }

    insert_cols: List[str] = []
    value_placeholders: List[str] = []
    params: Dict[str, Any] = {}

    for logical_key, aliases in column_aliases.items():
        resolved = find_first_column(cols, aliases)
        if not resolved:
            continue
        insert_cols.append(quote_ident(resolved))
        placeholder = f"v_{logical_key}"
        value_placeholders.append(f":{placeholder}")
        params[placeholder] = field_map[logical_key]

    if not insert_cols:
        logger.info(
            "Search log skipped | no compatible columns | user_id=%s query=%s retrieved_case_ids=%s",
            user_id,
            query,
            list(retrieved_case_ids),
        )
        return

    sql = (
        f"INSERT INTO {quote_ident(table)} ({', '.join(insert_cols)}) "
        f"VALUES ({', '.join(value_placeholders)})"
    )

    db.execute(text(sql), params)
    if hasattr(db, "commit"):
        db.commit()
