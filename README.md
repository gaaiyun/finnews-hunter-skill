# FinnewsHunter

金融新闻监控工具，基于 RSS 源与 yfinance 拉取新闻并做智能筛选与导出。

## 快速开始

```python
from src.sources import KNOWN_FEEDS, fetch_rss, fetch_yfinance_news
from src.filter_export import filter_keywords, dedupe_by_url, export_json

# 从 RSS 源拉取
items = fetch_rss(KNOWN_FEEDS["bloomberg_markets"], max_items=20)

# 从 yfinance 拉取某 ticker 的新闻
items += fetch_yfinance_news("AAPL", max_items=20)

# 关键词筛选 + 去重
items = dedupe_by_url(filter_keywords(items, ["earnings", "Fed"]))

# 导出
export_json(items, "news.json")
```

## 功能特性

- RSS 源新闻拉取（标准库解析，不依赖 feedparser）
- yfinance ticker 级新闻拉取（免费、无需 API key）
- 智能去重（按 URL + 按标题相似度）
- 关键词、来源、时间范围筛选
- JSON / JSONL / CSV 导出

## 支持的新闻源

- Bloomberg、CNBC、Reuters、WSJ、Financial Times、MarketWatch 等 RSS 源
- Yahoo Finance（通过 yfinance，ticker 级新闻）
- 也可向 `fetch_rss` 传入任意标准 RSS feed URL

## 注意事项

- 遵守各 RSS 源与数据提供方的使用条款
- 建议设置合理的拉取间隔
- 数据仅供学习研究

## 许可证

MIT License
