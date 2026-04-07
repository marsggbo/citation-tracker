#!/usr/bin/env python3
"""
Citation Tracker - 使用 ScraperAPI
"""
import csv
import os
import sys
import re
import urllib.request
import urllib.parse
from datetime import datetime

from config import get_scholar_id

CSV_FILE = "citations.csv"
SCRAPER_API_KEY = os.environ.get("SCRAPER_API_KEY", "")

def scrape(author_id):
    """使用 ScraperAPI 获取并解析论文数据"""
    if not SCRAPER_API_KEY:
        print("❌ SCRAPER_API_KEY 环境变量未设置")
        return None
    
    print("🔄 抓取中...")
    
    target_url = f"https://scholar.google.com/citations?user={author_id}&hl=en&view_op=list_works&sortby=citation"
    api_url = f"http://api.scraperapi.com/?api_key={SCRAPER_API_KEY}&url={urllib.parse.quote(target_url)}"
    
    try:
        req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
        print("  请求中（10-30秒）...")
        resp = urllib.request.urlopen(req, timeout=120)
        html = resp.read().decode('utf-8', errors='ignore')
        print(f"  收到 {len(html)} bytes")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return None
    
    # 解析 HTML
    titles = re.findall(r'class="gsc_a_at[^"]*"[^>]*>([^<]+)</a>', html)
    cites = re.findall(r'class="gsc_a_ac[^"]*"[^>]*>([^<]+)</a>', html)
    years = re.findall(r'class="gsc_a_h[^"]*"[^>]*>([^<]+)</span>', html)
    
    print(f"  解析: {len(titles)} 篇论文")
    
    papers = []
    for i, title in enumerate(titles):
        c = int(cites[i]) if i < len(cites) and cites[i].isdigit() else 0
        y = years[i] if i < len(years) else ''
        papers.append({'title': title.strip(), 'citations': c, 'year': y, 'venue': ''})
    
    return papers

def save_to_csv(papers, today):
    file_exists = os.path.exists(CSV_FILE) and os.path.getsize(CSV_FILE) > 0
    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['date', 'title', 'citations', 'year', 'venue'])
        if not file_exists:
            writer.writeheader()
        for p in papers:
            writer.writerow({'date': today, 'title': p['title'], 'citations': p['citations'], 'year': p['year'], 'venue': p['venue']})
    print(f"✅ 保存 {len(papers)} 篇论文")

def main():
    today = datetime.now().strftime('%Y-%m-%d')
    author_id = get_scholar_id()
    print(f"📅 {today} | Author: {author_id}")
    
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith(today + ','):
                    print(f"✓ {today} 已存在")
                    return
    
    papers = scrape(author_id)
    if papers:
        save_to_csv(papers, today)
    else:
        print("⚠️ 抓取失败")
        sys.exit(0)

if __name__ == '__main__':
    main()
