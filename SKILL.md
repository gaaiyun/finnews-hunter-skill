# FinnewsHunter - 金融新闻监控工具

## 描述

金融新闻实时监控和分析工具。基于 RSS 源与 yfinance 拉取新闻，支持智能去重、关键词与来源筛选、按时间过滤和数据导出。

## 功能

- RSS 源新闻拉取（Bloomberg、CNBC、Reuters、WSJ、FT、MarketWatch 等，标准库解析，不依赖 feedparser）
- yfinance ticker 级新闻拉取（Yahoo Finance，免费、无需 API key）
- 智能去重（按 URL 精确去重 + 按标题相似度去重）
- 关键词、来源、时间范围筛选
- JSON / JSONL / CSV 导出

## 使用方法

核心功能以 Python 函数形式提供在 `src/` 下，可直接调用组合。

### 拉取新闻

```python
from src.sources import KNOWN_FEEDS, fetch_rss, fetch_yfinance_news

# 从 RSS 源拉取（KNOWN_FEEDS 内置常见财经媒体）
items = fetch_rss(KNOWN_FEEDS["bloomberg_markets"], max_items=20)

# 从 yfinance 拉取某 ticker 的新闻
items += fetch_yfinance_news("AAPL", max_items=20)
```

### 筛选与去重

```python
from src.filter_export import (
    filter_keywords, filter_by_source, filter_recent,
    dedupe_by_url, dedupe_by_title,
)

items = filter_keywords(items, ["earnings", "Fed"], mode="any")
items = filter_by_source(items, ["rss:"])     # 前缀匹配所有 RSS 源
items = filter_recent(items, days=7)
items = dedupe_by_url(items)
items = dedupe_by_title(items, similarity_threshold=0.85)
```

### 导出数据

```python
from src.filter_export import export_json, export_jsonl, export_csv

export_json(items, "news.json")
export_jsonl(items, "news.jsonl")
export_csv(items, "news.csv")
```

## 安装

```bash
pip install -r requirements.txt
```

## 依赖

- RSS 拉取与解析：仅用 Python 标准库（`urllib`、`re`），无需第三方包
- yfinance 新闻拉取（可选）：`yfinance>=0.2.0`，仅在调用 `fetch_yfinance_news` 时需要

## 支持的新闻源

内置 `KNOWN_FEEDS` RSS 源：

- Bloomberg Markets / Economics
- CNBC Top News
- Reuters Business & Finance
- WSJ World News
- Financial Times
- MarketWatch Top Stories

`fetch_rss` 为通用解析器，可传入任意标准 RSS feed URL。另支持通过 `fetch_yfinance_news` 拉取 Yahoo Finance 的 ticker 级新闻。

## 输出格式

### JSON
```json
{
  "title": "新闻标题",
  "url": "https://...",
  "source": "rss:feeds.bloomberg.com",
  "published_at": "Mon, 15 Jan 2026 09:00:00 GMT",
  "summary": "新闻摘要",
  "ticker": null
}
```

### CSV
```csv
title,url,source,published_at,summary,ticker
"新闻标题","https://...","rss:feeds.bloomberg.com","Mon, 15 Jan 2026 09:00:00 GMT","摘要",""
```

## 注意事项

- 遵守各 RSS 源与数据提供方的使用条款
- 建议设置合理的拉取间隔，避免频繁请求
- 数据仅供学习研究

## 许可证

MIT License
