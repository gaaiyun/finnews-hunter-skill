# FinnewsHunter - 金融新闻监控工具

## 描述

金融新闻实时监控和分析工具。支持多源新闻爬取、智能去重、股票相关性筛选和数据导出。

## 功能

- 📰 多源新闻爬取（新浪、腾讯、东方财富等）
- 🔍 智能去重和筛选
- 📊 股票相关性识别
- 💾 JSON/CSV/Markdown 导出
- ⏰ 定时监控
- 🎯 关键词搜索

## 使用方法

### 爬取新闻

```bash
# 爬取单个新闻源
python scripts/crawl.py --source sina

# 爬取所有新闻源
python scripts/crawl.py --all

# 定时爬取（每小时）
python scripts/crawl.py --all --interval 3600
```

### 查看新闻

```bash
# 查看最新新闻
python scripts/view.py --limit 20

# 搜索关键词
python scripts/view.py --search "新能源" --limit 10

# 查看统计
python scripts/view.py --stats
```

### 导出数据

```bash
# 导出 JSON
python scripts/export.py --format json --output news.json

# 导出 CSV
python scripts/export.py --format csv --output news.csv

# 导出 Markdown 日报
python scripts/export.py --format markdown --output report.md
```

## 安装

```bash
pip install -r requirements.txt
```

## 依赖

- requests>=2.31.0
- beautifulsoup4>=4.12.0
- pandas>=2.0.0
- lxml>=4.9.0

## 支持的新闻源

- 新浪财经
- 腾讯财经
- 东方财富
- 第一财经
- 财新网
- 证券时报
- 中国证券网
- 金融界
- 和讯网
- 凤凰财经

## 输出格式

### JSON
```json
{
  "title": "新闻标题",
  "url": "https://...",
  "source": "sina",
  "time": "2026-03-01 14:00:00",
  "summary": "新闻摘要"
}
```

### CSV
```csv
title,url,source,time,summary
"新闻标题","https://...","sina","2026-03-01 14:00:00","摘要"
```

## 注意事项

- 遵守网站爬取规则
- 建议设置合理的爬取间隔
- 数据仅供学习研究

## 作者

派蒙 (Paimon) - 基于 FinnewsHunter 二次开发

## 许可证

MIT License
