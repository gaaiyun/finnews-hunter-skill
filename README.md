# FinnewsHunter

金融新闻监控工具，支持多源爬取和智能分析。

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 爬取新闻
python scripts/news.py crawl --source sina

# 查看新闻
python scripts/news.py view --limit 20

# 搜索新闻
python scripts/news.py view --search "新能源" --limit 10

# 导出数据
python scripts/news.py export --format json --output news
```

## 功能特性

- ✅ 多源新闻爬取
- ✅ 智能去重
- ✅ 关键词搜索
- ✅ 数据导出
- ✅ 轻量级存储

## 支持的新闻源

- 新浪财经
- 腾讯财经
- 东方财富
- 第一财经
- 更多新闻源持续添加中...

## 注意事项

- 遵守网站爬取规则
- 建议设置合理间隔
- 数据仅供学习研究

## 许可证

MIT License
