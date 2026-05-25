"""sources.py 测试 —— RSS / yfinance mock + 合成。"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.sources import (
    KNOWN_FEEDS,
    NewsItem,
    _strip_cdata_html,
    fetch_rss,
    fetch_yfinance_news,
    synthetic_news,
)


# --- _strip_cdata_html ----------------------------------------------

def test_strip_cdata():
    assert _strip_cdata_html("<![CDATA[hello]]>") == "hello"


def test_strip_html_tags():
    assert _strip_cdata_html("<p>hello <b>world</b></p>") == "hello world"


def test_strip_combined():
    assert _strip_cdata_html("<![CDATA[<p>hi</p>]]>") == "hi"


def test_strip_empty():
    assert _strip_cdata_html("") == ""
    assert _strip_cdata_html(None) == ""


# --- NewsItem -------------------------------------------------------

def test_newsitem_to_dict_serializable():
    import json
    it = NewsItem(title="t", url="u", source="s",
                   published_at="2026-01-01", summary="x", ticker="AAPL")
    json.dumps(it.to_dict())


# --- synthetic_news -------------------------------------------------

def test_synthetic_default():
    items = synthetic_news()
    assert len(items) == 6
    assert all(isinstance(it, NewsItem) for it in items)


def test_synthetic_deterministic():
    a = synthetic_news(n=5, seed=1)
    b = synthetic_news(n=5, seed=1)
    assert [x.title for x in a] == [x.title for x in b]


def test_synthetic_custom_count():
    items = synthetic_news(n=3)
    assert len(items) == 3


def test_synthetic_each_has_title_and_summary():
    items = synthetic_news(n=5)
    for it in items:
        assert it.title
        assert it.summary
        assert it.source == "synthetic"


# --- fetch_rss（mock HTTP）---------------------------------------

_SAMPLE_RSS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<title>Test Financial News</title>
<item>
  <title><![CDATA[Fed signals pause on rate hikes]]></title>
  <description>FOMC officials hint at holding the policy rate steady</description>
  <link>https://example.com/article-1</link>
  <pubDate>Mon, 15 Jan 2026 09:00:00 GMT</pubDate>
</item>
<item>
  <title>Oil surges 5% on Middle East tensions</title>
  <description><![CDATA[<p>Brent crude jumps to 3-month high</p>]]></description>
  <link>https://example.com/article-2</link>
  <pubDate>Mon, 15 Jan 2026 10:30:00 GMT</pubDate>
</item>
</channel>
</rss>"""


def _fake_urlopen(data: bytes = _SAMPLE_RSS):
    class FakeResp:
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def read(self): return data
    return lambda *a, **kw: FakeResp()


def test_fetch_rss_parses_items(monkeypatch):
    monkeypatch.setattr("src.sources.urllib.request.urlopen", _fake_urlopen())
    items = fetch_rss("https://example.com/feed.xml")
    assert len(items) == 2
    assert items[0].title == "Fed signals pause on rate hikes"
    assert items[0].source.startswith("rss:")


def test_fetch_rss_strips_html_in_description(monkeypatch):
    monkeypatch.setattr("src.sources.urllib.request.urlopen", _fake_urlopen())
    items = fetch_rss("https://example.com/feed.xml")
    # 第二条 description 含 <p> 标签
    assert "<p>" not in items[1].summary


def test_fetch_rss_max_items_caps(monkeypatch):
    monkeypatch.setattr("src.sources.urllib.request.urlopen", _fake_urlopen())
    items = fetch_rss("https://example.com/feed.xml", max_items=1)
    assert len(items) == 1


def test_fetch_rss_empty_feed_raises(monkeypatch):
    monkeypatch.setattr("src.sources.urllib.request.urlopen",
                         _fake_urlopen(b"<?xml?><html><body>not rss</body></html>"))
    with pytest.raises(RuntimeError, match="<item>"):
        fetch_rss("https://example.com/empty")


def test_fetch_rss_preserves_url(monkeypatch):
    monkeypatch.setattr("src.sources.urllib.request.urlopen", _fake_urlopen())
    items = fetch_rss("https://example.com/feed.xml")
    assert items[0].url == "https://example.com/article-1"


# --- fetch_yfinance_news（mock 模块）-----------------------------

def test_fetch_yfinance_news_parses_items():
    fake_yf_news = [
        {"title": "Apple Q3 Earnings", "link": "https://x.com/1",
         "publisher": "Reuters", "providerPublishTime": 1736000000},
        {"title": "iPhone Sales Strong", "link": "https://x.com/2",
         "publisher": "Bloomberg", "providerPublishTime": 1736086400},
    ]
    mock_yf = MagicMock()
    mock_yf.Ticker.return_value.news = fake_yf_news
    with patch.dict("sys.modules", {"yfinance": mock_yf}):
        items = fetch_yfinance_news("AAPL", max_items=5)
    assert len(items) == 2
    assert items[0].title == "Apple Q3 Earnings"
    assert items[0].ticker == "AAPL"


def test_fetch_yfinance_skips_no_title():
    fake = [
        {"title": "Valid News", "providerPublishTime": 1700000000},
        {"link": "https://x.com/no-title"},
    ]
    mock_yf = MagicMock()
    mock_yf.Ticker.return_value.news = fake
    with patch.dict("sys.modules", {"yfinance": mock_yf}):
        items = fetch_yfinance_news("AAPL")
    assert len(items) == 1


def test_fetch_yfinance_not_installed_raises(monkeypatch):
    import builtins
    real = builtins.__import__

    def fake_import(name, *a, **kw):
        if name == "yfinance":
            raise ImportError("simulated")
        return real(name, *a, **kw)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(ImportError, match="yfinance"):
        fetch_yfinance_news("AAPL")


def test_known_feeds_registry():
    """注册表至少有几个知名财经源。"""
    assert len(KNOWN_FEEDS) >= 5
    for name, url in KNOWN_FEEDS.items():
        assert url.startswith("http")
