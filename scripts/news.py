"""
FinnewsHunter - 金融新闻监控工具
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
from pathlib import Path
import argparse

class NewsSource:
    """新闻源基类"""
    
    def __init__(self, name, url):
        self.name = name
        self.url = url
    
    def fetch(self):
        """抓取新闻"""
        try:
            response = requests.get(self.url, timeout=10)
            response.encoding = 'utf-8'
            return self.parse(response.text)
        except Exception as e:
            print(f"[错误] {self.name}: {e}")
            return []
    
    def parse(self, html):
        """解析 HTML"""
        return []

class SinaFinance(NewsSource):
    """新浪财经"""
    
    def __init__(self):
        super().__init__('sina', 'https://finance.sina.com.cn/')
    
    def parse(self, html):
        soup = BeautifulSoup(html, 'lxml')
        news_list = []
        
        for item in soup.select('.news-item')[:20]:
            try:
                title = item.select_one('a').text.strip()
                url = item.select_one('a')['href']
                news_list.append({
                    'title': title,
                    'url': url,
                    'source': self.name,
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            except:
                continue
        
        return news_list

class NewsCrawler:
    """新闻爬虫"""
    
    def __init__(self, data_dir='data'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.data_file = self.data_dir / 'news.json'
        
        self.sources = {
            'sina': SinaFinance(),
        }
    
    def crawl(self, source_names=None):
        """爬取新闻"""
        if source_names is None:
            source_names = list(self.sources.keys())
        
        all_news = []
        
        for name in source_names:
            if name in self.sources:
                print(f"[爬取] {name}")
                news = self.sources[name].fetch()
                all_news.extend(news)
                print(f"[完成] {name}: {len(news)} 条")
        
        self.save_news(all_news)
        return all_news
    
    def save_news(self, news_list):
        """保存新闻"""
        existing = self.load_news()
        
        # 去重
        existing_urls = {n['url'] for n in existing}
        new_news = [n for n in news_list if n['url'] not in existing_urls]
        
        all_news = existing + new_news
        
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(all_news, f, ensure_ascii=False, indent=2)
        
        print(f"[保存] 新增 {len(new_news)} 条，总计 {len(all_news)} 条")
    
    def load_news(self):
        """加载新闻"""
        if self.data_file.exists():
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def view_news(self, limit=20, search=None):
        """查看新闻"""
        news_list = self.load_news()
        
        if search:
            news_list = [n for n in news_list if search in n['title']]
        
        news_list = news_list[-limit:]
        
        for i, news in enumerate(news_list, 1):
            print(f"\n{i}. {news['title']}")
            print(f"   来源: {news['source']} | 时间: {news['time']}")
            print(f"   链接: {news['url']}")
    
    def export(self, format='json', output='export'):
        """导出数据"""
        news_list = self.load_news()
        
        if format == 'json':
            with open(f"{output}.json", 'w', encoding='utf-8') as f:
                json.dump(news_list, f, ensure_ascii=False, indent=2)
        
        print(f"[导出] {len(news_list)} 条新闻 -> {output}.{format}")

def main():
    parser = argparse.ArgumentParser(description="FinnewsHunter")
    parser.add_argument('action', choices=['crawl', 'view', 'export'])
    parser.add_argument('--source', nargs='+', default=['sina'])
    parser.add_argument('--all', action='store_true')
    parser.add_argument('--limit', type=int, default=20)
    parser.add_argument('--search', help='搜索关键词')
    parser.add_argument('--format', choices=['json'], default='json')
    parser.add_argument('--output', default='export')
    
    args = parser.parse_args()
    
    crawler = NewsCrawler()
    
    if args.action == 'crawl':
        sources = None if args.all else args.source
        crawler.crawl(sources)
    
    elif args.action == 'view':
        crawler.view_news(args.limit, args.search)
    
    elif args.action == 'export':
        crawler.export(args.format, args.output)

if __name__ == "__main__":
    main()
