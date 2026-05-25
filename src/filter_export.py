"""新闻过滤 + 去重 + 导出（v2）。

v1 把所有逻辑塞在 NewsCrawler 单类里。v2 拆成独立纯函数，便于测试 + 重用。
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

from .sources import NewsItem


# --- 过滤 -------------------------------------------------------------

def filter_keywords(items: Sequence[NewsItem], keywords: Sequence[str],
                     mode: str = "any") -> List[NewsItem]:
    """按关键词过滤标题 + 摘要。

    mode: "any" 至少一个关键词命中（默认）；"all" 全部命中
    """
    if mode not in ("any", "all"):
        raise ValueError(f"mode 必须 any/all，得到 {mode}")
    if not keywords:
        return list(items)
    kws_lower = [k.lower() for k in keywords]

    def _matches(item: NewsItem) -> bool:
        text = (item.title + " " + item.summary).lower()
        hits = [k in text for k in kws_lower]
        return all(hits) if mode == "all" else any(hits)

    return [it for it in items if _matches(it)]


def filter_by_source(items: Sequence[NewsItem],
                      sources: Sequence[str]) -> List[NewsItem]:
    """只保留来自指定源的新闻。

    source 可以是 prefix（"rss:" 匹配所有 RSS 源，"yfinance:" 匹配所有
    yfinance 源）也可以是完整 source 字符串。
    """
    if not sources:
        return list(items)
    return [it for it in items
            if any(s in it.source for s in sources)]


def filter_recent(items: Sequence[NewsItem],
                   days: int) -> List[NewsItem]:
    """只保留 published_at 在最近 N 天内的。

    published_at 解析失败的条目按"未知日期" → 保留。
    """
    from datetime import datetime, timedelta
    if days <= 0:
        return list(items)
    cutoff = datetime.now() - timedelta(days=days)
    out = []
    for it in items:
        if not it.published_at:
            out.append(it)
            continue
        # 尝试解析常见日期格式
        parsed = _try_parse_date(it.published_at)
        if parsed is None or parsed >= cutoff:
            out.append(it)
    return out


def _try_parse_date(s: str) -> Optional["datetime"]:
    from datetime import datetime
    formats = [
        "%a, %d %b %Y %H:%M:%S %Z",     # RSS pubDate
        "%a, %d %b %Y %H:%M:%S %z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=None)
        except (ValueError, TypeError):
            continue
    return None


# --- 去重 -------------------------------------------------------------

def dedupe_by_url(items: Sequence[NewsItem]) -> List[NewsItem]:
    """按 URL 去重，保留第一次出现。URL 为 None 的不去重。"""
    seen_urls = set()
    out = []
    for it in items:
        if it.url is None:
            out.append(it)
            continue
        if it.url in seen_urls:
            continue
        seen_urls.add(it.url)
        out.append(it)
    return out


def dedupe_by_title(items: Sequence[NewsItem],
                     similarity_threshold: float = 0.85
                     ) -> List[NewsItem]:
    """按标题相似度去重（基于 set token Jaccard）。

    threshold ∈ [0, 1]，越高越严格（只有几乎相同才视为重复）。
    """
    if not 0 <= similarity_threshold <= 1:
        raise ValueError("similarity_threshold 必须 ∈ [0, 1]")

    def _tokens(title: str) -> set:
        return set(title.lower().split())

    out: List[NewsItem] = []
    kept_tokens: List[set] = []
    for it in items:
        toks = _tokens(it.title)
        if not toks:
            out.append(it)
            kept_tokens.append(set())
            continue
        is_dup = False
        for prev in kept_tokens:
            if not prev:
                continue
            jac = len(toks & prev) / max(len(toks | prev), 1)
            if jac >= similarity_threshold:
                is_dup = True
                break
        if not is_dup:
            out.append(it)
            kept_tokens.append(toks)
    return out


# --- 导出 -------------------------------------------------------------

def export_json(items: Sequence[NewsItem], path: str) -> int:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    payload = [it.to_dict() for it in items]
    Path(path).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return len(payload)


def export_jsonl(items: Sequence[NewsItem], path: str) -> int:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it.to_dict(), ensure_ascii=False) + "\n")
    return len(items)


def export_csv(items: Sequence[NewsItem], path: str) -> int:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    if not items:
        Path(path).write_text("title,url,source,published_at,summary,ticker\n",
                               encoding="utf-8")
        return 0
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(items[0].to_dict().keys()))
        writer.writeheader()
        for it in items:
            writer.writerow(it.to_dict())
    return len(items)
