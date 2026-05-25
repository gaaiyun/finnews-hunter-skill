"""金融新闻数据源（v2）。

v1 用 BeautifulSoup 抓 sina HTML，目标网站改版后就坏。v2 改用更稳定的入口：

1. **RSS feeds**（Bloomberg / Reuters / CNBC / WSJ 等都有公开 RSS）
2. **yfinance .news**（Yahoo Finance 的 ticker-level 新闻，免费、无 key）
3. **合成数据**（测试 / demo / 离线）

统一返回 ``NewsItem``，下游过滤 / 去重 / 导出复用同套数据结构。
"""
from __future__ import annotations

import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class NewsItem:
    title: str
    url: Optional[str]
    source: str
    published_at: Optional[str] = None
    summary: str = ""
    ticker: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "published_at": self.published_at,
            "summary": self.summary,
            "ticker": self.ticker,
        }


# --- RSS（标准库实现，不依赖 feedparser）-----------------------------

_ITEM_PAT = re.compile(r"<item[^>]*>(.*?)</item>", re.IGNORECASE | re.DOTALL)
_TAG_PAT = re.compile(r"<([a-zA-Z:]+)[^>]*>(.*?)</\1>",
                       re.IGNORECASE | re.DOTALL)
_CDATA_PAT = re.compile(r"<!\[CDATA\[(.*?)\]\]>", re.IGNORECASE | re.DOTALL)


def _strip_cdata_html(text: str) -> str:
    text = _CDATA_PAT.sub(r"\1", text or "")
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def fetch_rss(url: str, max_items: int = 20,
               timeout: float = 15.0) -> List[NewsItem]:
    """通用 RSS 解析。

    支持 Bloomberg / Reuters / CNBC / WSJ / 财新 / 经济观察报 等绝大多数
    财经媒体的 RSS feed。
    """
    req = urllib.request.Request(
        url, headers={"User-Agent": "finnews-hunter/2.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8", errors="replace")

    items_raw = _ITEM_PAT.findall(body)
    if not items_raw:
        raise RuntimeError(f"RSS 没解析出 <item>：{url}")

    host = urllib.parse.urlparse(url).hostname or "rss"
    out: List[NewsItem] = []
    for block in items_raw[:max_items]:
        fields: dict = {}
        for tag, content in _TAG_PAT.findall(block):
            fields.setdefault(tag.lower(), _strip_cdata_html(content))
        title = fields.get("title", "")
        if not title:
            continue
        out.append(NewsItem(
            title=title,
            url=fields.get("link") or fields.get("guid"),
            source=f"rss:{host}",
            published_at=fields.get("pubdate") or fields.get("published"),
            summary=fields.get("description") or fields.get("summary", ""),
        ))
    return out


# --- yfinance news -----------------------------------------------------

def fetch_yfinance_news(ticker: str, max_items: int = 20) -> List[NewsItem]:
    """从 yfinance 抓某 ticker 的新闻。"""
    try:
        import yfinance as yf
    except ImportError as e:
        raise ImportError(
            "yfinance 未装。pip install yfinance 后再用此函数。"
        ) from e

    t = yf.Ticker(ticker)
    raw = t.news or []
    out: List[NewsItem] = []
    for item in raw[:max_items]:
        title = item.get("title") or item.get("headline") or ""
        if not title:
            continue
        ts = item.get("providerPublishTime") or item.get("pubDate")
        published = (datetime.fromtimestamp(ts).isoformat()
                     if isinstance(ts, (int, float)) else
                     (str(ts) if ts else None))
        out.append(NewsItem(
            title=title,
            url=item.get("link") or item.get("url"),
            source=f"yfinance:{item.get('publisher', 'Yahoo')}",
            published_at=published,
            summary=item.get("summary", ""),
            ticker=ticker.upper(),
        ))
    return out


# --- 合成数据 ----------------------------------------------------------

_SYNTH_TEMPLATES = [
    ("Fed signals pause on rate hikes amid cooling inflation",
     "FOMC officials hint at holding the policy rate steady"),
    ("Apple beats Q3 estimates with record iPhone sales",
     "AAPL reported $89.5B revenue, exceeding analyst expectations"),
    ("China Q3 GDP grows 4.9%, beating estimates",
     "Stronger industrial output and retail sales drive growth"),
    ("Oil prices surge on Middle East tensions",
     "Brent crude jumps 3% on supply concerns"),
    ("Tesla announces $7.5B share buyback",
     "Largest buyback in company history signals confidence"),
    ("SEC opens probe into crypto exchange Binance",
     "Investigation focuses on potential securities violations"),
]


def synthetic_news(n: int = 6, seed: int = 42) -> List[NewsItem]:
    """合成新闻，给测试 / 离线 demo 用。"""
    import random
    rng = random.Random(seed)
    base = list(_SYNTH_TEMPLATES)
    out: List[NewsItem] = []
    for i in range(n):
        title, summary = rng.choice(base)
        out.append(NewsItem(
            title=title, url=None, source="synthetic",
            published_at=datetime(2026, 1, 1 + (i % 28)).isoformat(),
            summary=summary,
        ))
    return out


# --- 已知 RSS feed 注册表 ----------------------------------------------

KNOWN_FEEDS = {
    "bloomberg_markets": "https://feeds.bloomberg.com/markets/news.rss",
    "bloomberg_economics": "https://feeds.bloomberg.com/economics/news.rss",
    "cnbc_top": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "reuters_business": "https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best",
    "wsj_world": "https://feeds.a.dj.com/rss/RSSWorldNews.xml",
    "ft_main": "https://www.ft.com/?format=rss",
    "marketwatch_top": "https://feeds.content.dowjones.io/public/rss/mw_topstories",
}
