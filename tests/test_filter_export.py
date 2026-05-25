"""filter_export.py 测试。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.filter_export import (
    _try_parse_date,
    dedupe_by_title,
    dedupe_by_url,
    export_csv,
    export_json,
    export_jsonl,
    filter_by_source,
    filter_keywords,
    filter_recent,
)
from src.sources import NewsItem


def _item(title="", url=None, source="x", date=None, summary="", ticker=None):
    return NewsItem(title=title, url=url, source=source,
                     published_at=date, summary=summary, ticker=ticker)


# --- filter_keywords ----------------------------------------------

def test_filter_any_match():
    items = [_item("Apple beats earnings"), _item("Tesla buyback")]
    out = filter_keywords(items, ["apple"])
    assert len(out) == 1
    assert "Apple" in out[0].title


def test_filter_all_requires_all_keywords():
    items = [_item("Apple beats", summary="earnings strong"),
             _item("Apple buyback")]
    out = filter_keywords(items, ["apple", "earnings"], mode="all")
    assert len(out) == 1


def test_filter_case_insensitive():
    items = [_item("APPLE INC."), _item("Tesla")]
    out = filter_keywords(items, ["apple"])
    assert len(out) == 1


def test_filter_empty_keywords_returns_all():
    items = [_item("a"), _item("b")]
    assert len(filter_keywords(items, [])) == 2


def test_filter_invalid_mode_raises():
    with pytest.raises(ValueError, match="mode"):
        filter_keywords([_item("x")], ["k"], mode="xor")


def test_filter_searches_summary_too():
    items = [_item("Generic", summary="apple stock surges")]
    out = filter_keywords(items, ["apple"])
    assert len(out) == 1


# --- filter_by_source ---------------------------------------------

def test_filter_source_exact():
    items = [_item("a", source="rss:bloomberg"),
             _item("b", source="yfinance:Reuters")]
    out = filter_by_source(items, ["rss:bloomberg"])
    assert len(out) == 1


def test_filter_source_prefix():
    items = [_item("a", source="rss:bloomberg"),
             _item("b", source="rss:cnbc"),
             _item("c", source="yfinance:Reuters")]
    out = filter_by_source(items, ["rss:"])
    assert len(out) == 2


def test_filter_source_empty_returns_all():
    items = [_item("a"), _item("b")]
    assert len(filter_by_source(items, [])) == 2


# --- filter_recent ------------------------------------------------

def test_filter_recent_basic():
    from datetime import datetime, timedelta
    old = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    new = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    items = [_item("old", date=old), _item("new", date=new)]
    out = filter_recent(items, days=7)
    titles = [it.title for it in out]
    assert "new" in titles
    assert "old" not in titles


def test_filter_recent_unparseable_kept():
    items = [_item("weird", date="not-a-date")]
    out = filter_recent(items, days=1)
    # 解析失败 → 保留
    assert len(out) == 1


def test_filter_recent_no_date_kept():
    items = [_item("no-date", date=None)]
    out = filter_recent(items, days=1)
    assert len(out) == 1


def test_filter_recent_zero_days_disabled():
    items = [_item("a", date="2020-01-01")]
    out = filter_recent(items, days=0)
    assert len(out) == 1


def test_try_parse_date_formats():
    """覆盖多个常见日期格式。"""
    formats = [
        "Mon, 15 Jan 2026 09:00:00 GMT",
        "2026-01-15T09:00:00",
        "2026-01-15 09:00:00",
        "2026-01-15",
    ]
    for f in formats:
        assert _try_parse_date(f) is not None


def test_try_parse_date_invalid():
    assert _try_parse_date("not a date") is None
    assert _try_parse_date(None) is None


# --- dedupe_by_url ------------------------------------------------

def test_dedupe_url_basic():
    items = [_item("A", url="http://x/1"), _item("B", url="http://x/1"),
             _item("C", url="http://x/2")]
    out = dedupe_by_url(items)
    assert len(out) == 2


def test_dedupe_url_none_kept():
    """URL=None 的不去重。"""
    items = [_item("a", url=None), _item("b", url=None)]
    out = dedupe_by_url(items)
    assert len(out) == 2


def test_dedupe_url_preserves_first():
    items = [_item("first", url="http://x/1"),
             _item("second", url="http://x/1")]
    out = dedupe_by_url(items)
    assert out[0].title == "first"


# --- dedupe_by_title ----------------------------------------------

def test_dedupe_title_identical():
    items = [_item("Apple beats earnings"),
             _item("Apple beats earnings")]
    out = dedupe_by_title(items, similarity_threshold=1.0)
    assert len(out) == 1


def test_dedupe_title_near_duplicate():
    items = [_item("Apple beats Q3 earnings expectations"),
             _item("Apple beats Q3 earnings predictions")]   # 4/5 words 相同
    out = dedupe_by_title(items, similarity_threshold=0.6)
    assert len(out) == 1


def test_dedupe_title_different_kept():
    items = [_item("Apple beats earnings"), _item("Tesla buyback announced")]
    out = dedupe_by_title(items, similarity_threshold=0.5)
    assert len(out) == 2


def test_dedupe_title_invalid_threshold():
    with pytest.raises(ValueError, match="similarity"):
        dedupe_by_title([_item("x")], similarity_threshold=2.0)


def test_dedupe_title_empty_title_kept():
    items = [_item(""), _item("")]
    out = dedupe_by_title(items, similarity_threshold=0.5)
    assert len(out) == 2


# --- 导出 -------------------------------------------------------

def test_export_json(tmp_path):
    items = [_item("a", url="http://x/1"), _item("b", url="http://x/2")]
    path = tmp_path / "out.json"
    n = export_json(items, str(path))
    assert n == 2
    data = json.loads(path.read_text(encoding="utf-8"))
    assert len(data) == 2


def test_export_jsonl(tmp_path):
    items = [_item("a"), _item("b"), _item("c")]
    path = tmp_path / "out.jsonl"
    n = export_jsonl(items, str(path))
    assert n == 3
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3
    json.loads(lines[0])


def test_export_csv(tmp_path):
    items = [_item("Apple", url="u1", source="rss")]
    path = tmp_path / "out.csv"
    n = export_csv(items, str(path))
    assert n == 1
    text = path.read_text(encoding="utf-8")
    assert "title" in text   # 含 header
    assert "Apple" in text


def test_export_csv_empty(tmp_path):
    path = tmp_path / "empty.csv"
    n = export_csv([], str(path))
    assert n == 0
    text = path.read_text(encoding="utf-8")
    assert "title" in text   # 只写 header


def test_export_creates_parent_dir(tmp_path):
    items = [_item("a")]
    path = tmp_path / "nested" / "out.json"
    export_json(items, str(path))
    assert path.exists()
