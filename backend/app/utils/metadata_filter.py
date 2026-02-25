"""Utilities for metadata-first filtering in search workflows."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from sqlalchemy import inspect, text


def quote_ident(identifier: str) -> str:
    """Quote SQL identifiers safely for dynamic SQL generation."""
    return '"' + identifier.replace('"', '""') + '"'


def find_table(
    table_names: Sequence[str],
    preferred: Sequence[str],
    required_columns: Sequence[str],
    inspector: Any,
) -> Optional[str]:
    """Find a table by preferred names and optional required column checks."""
    lower_to_original = {name.lower(): name for name in table_names}

    for name in preferred:
        candidate = lower_to_original.get(name.lower())
        if not candidate:
            continue
        if not required_columns:
            return candidate
        columns = {col["name"].lower() for col in inspector.get_columns(candidate)}
        if all(col.lower() in columns for col in required_columns):
            return candidate

    for candidate in table_names:
        columns = {col["name"].lower() for col in inspector.get_columns(candidate)}
        if all(col.lower() in columns for col in required_columns):
            return candidate

    return None


def find_first_column(columns: Iterable[str], candidates: Sequence[str]) -> Optional[str]:
    """Return the first matching column name from a list of aliases."""
    lower_map = {col.lower(): col for col in columns}
    for alias in candidates:
        match = lower_map.get(alias.lower())
        if match:
            return match
    return None


def get_case_table_config(db: Any) -> Dict[str, Any]:
    """Discover case and metadata table configuration via SQLAlchemy inspection."""
    bind = getattr(db, "bind", None) or db.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names()

    case_table = find_table(
        table_names=tables,
        preferred=["casefiles", "casefile", "cases", "case_file"],
        required_columns=[],
        inspector=inspector,
    )
    if not case_table:
        raise RuntimeError("Unable to locate case table for search service.")

    case_columns = [col["name"] for col in inspector.get_columns(case_table)]
    id_col = find_first_column(case_columns, ["case_id", "id"])
    if not id_col:
        raise RuntimeError("Unable to locate case identifier column.")

    title_col = find_first_column(case_columns, ["case_title", "title", "name"])
    court_col = find_first_column(case_columns, ["court"])
    year_col = find_first_column(case_columns, ["year", "judgment_year", "decision_year"])
    bench_col = find_first_column(case_columns, ["bench"])
    snippet_col = find_first_column(case_columns, ["short_snippet", "snippet", "headnote", "summary"])
    text_col = find_first_column(case_columns, ["full_text", "judgment_text", "text", "content", "body"])
    pdf_col = find_first_column(case_columns, ["pdf_path", "file_path", "document_path", "path"])

    metadata_table = find_table(
        table_names=tables,
        preferred=["metadata", "case_metadata", "case_meta"],
        required_columns=[],
        inspector=inspector,
    )

    metadata_config: Optional[Dict[str, Any]] = None
    if metadata_table:
        md_columns = [col["name"] for col in inspector.get_columns(metadata_table)]
        md_case_fk = find_first_column(md_columns, ["case_id", "casefile_id", "case_ref_id"])
        if md_case_fk:
            metadata_config = {
                "table": metadata_table,
                "columns": md_columns,
                "case_fk": md_case_fk,
            }

    return {
        "table": case_table,
        "columns": case_columns,
        "id_col": id_col,
        "title_col": title_col,
        "court_col": court_col,
        "year_col": year_col,
        "bench_col": bench_col,
        "snippet_col": snippet_col,
        "text_col": text_col,
        "pdf_col": pdf_col,
        "metadata": metadata_config,
    }


def build_filter_clauses(
    filters: Mapping[str, Any],
    case_cfg: Mapping[str, Any],
) -> Tuple[List[str], Dict[str, Any]]:
    """Build SQL WHERE clauses from supported search filters."""
    clauses: List[str] = []
    params: Dict[str, Any] = {}

    case_cols = set(case_cfg["columns"])
    metadata_cfg = case_cfg.get("metadata")
    md_cols = set(metadata_cfg["columns"]) if metadata_cfg else set()

    def col_ref(column_name: str) -> str:
        if column_name in case_cols:
            return f"c.{quote_ident(column_name)}"
        if metadata_cfg and column_name in md_cols:
            return f"m.{quote_ident(column_name)}"
        raise KeyError(column_name)

    mappings: List[Tuple[str, Sequence[str], str]] = [
        ("court", ["court"], "exact"),
        ("year", ["year", "judgment_year", "decision_year"], "exact"),
        ("bench", ["bench"], "ilike"),
        ("dishonor_reason", ["dishonor_reason", "bounce_reason", "return_reason"], "ilike"),
        ("nature_of_debt", ["nature_of_debt", "debt_nature", "liability_nature"], "ilike"),
        ("notice_period", ["notice_period", "notice_period_days"], "exact"),
        ("cheque_amount", ["cheque_amount", "amount"], "exact"),
    ]

    for input_key, aliases, mode in mappings:
        value = filters.get(input_key)
        if value is None or value == "":
            continue

        resolved_col = None
        for alias in aliases:
            if alias in case_cols or alias in md_cols:
                resolved_col = alias
                break

        if not resolved_col:
            continue

        param_name = f"p_{input_key}"
        if mode == "exact":
            clauses.append(f"{col_ref(resolved_col)} = :{param_name}")
            params[param_name] = value
        else:
            clauses.append(f"{col_ref(resolved_col)} ILIKE :{param_name}")
            params[param_name] = f"%{value}%"

    return clauses, params


def fetch_metadata_filtered_cases(
    db: Any,
    search_input: Mapping[str, Any],
    limit: int = 200,
) -> List[Dict[str, Any]]:
    """Fetch candidate cases by applying metadata filters before vector retrieval."""
    case_cfg = get_case_table_config(db)

    select_parts = [
        f"c.{quote_ident(case_cfg['id_col'])} AS case_id",
        (
            f"c.{quote_ident(case_cfg['title_col'])} AS case_title"
            if case_cfg.get("title_col")
            else "NULL AS case_title"
        ),
        (
            f"c.{quote_ident(case_cfg['court_col'])} AS court"
            if case_cfg.get("court_col")
            else "NULL AS court"
        ),
        (
            f"c.{quote_ident(case_cfg['year_col'])} AS year"
            if case_cfg.get("year_col")
            else "NULL AS year"
        ),
        (
            f"c.{quote_ident(case_cfg['bench_col'])} AS bench"
            if case_cfg.get("bench_col")
            else "NULL AS bench"
        ),
        (
            f"c.{quote_ident(case_cfg['snippet_col'])} AS short_snippet"
            if case_cfg.get("snippet_col")
            else "NULL AS short_snippet"
        ),
        (
            f"c.{quote_ident(case_cfg['text_col'])} AS full_text"
            if case_cfg.get("text_col")
            else "NULL AS full_text"
        ),
        (
            f"c.{quote_ident(case_cfg['pdf_col'])} AS pdf_path"
            if case_cfg.get("pdf_col")
            else "NULL AS pdf_path"
        ),
    ]

    from_clause = f"{quote_ident(case_cfg['table'])} c"
    if case_cfg.get("metadata"):
        md = case_cfg["metadata"]
        from_clause += (
            f" LEFT JOIN {quote_ident(md['table'])} m"
            f" ON m.{quote_ident(md['case_fk'])} = c.{quote_ident(case_cfg['id_col'])}"
        )

    clauses, params = build_filter_clauses(search_input, case_cfg)
    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    sql = (
        f"SELECT {', '.join(select_parts)} "
        f"FROM {from_clause} "
        f"{where_sql} "
        f"ORDER BY c.{quote_ident(case_cfg['id_col'])} DESC "
        f"LIMIT :limit"
    )
    params["limit"] = limit

    rows = db.execute(text(sql), params).mappings().all()
    return [dict(row) for row in rows]
