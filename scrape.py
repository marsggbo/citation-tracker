#!/usr/bin/env python3
"""
Citation Tracker - 使用 ScraperAPI（JSON 版本）
数据以 JSON 格式存储，节省空间，支持完整历史趋势。
"""
import json
import os
import sys
import re
import csv
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta

from config import get_scholar_id

JSON_FILE = "citations.json"
CSV_FILE = "citations.csv"   # 旧格式，仅用于一次性迁移

SCRAPER_API_KEY = os.environ.get("SCRAPER_API_KEY", "")

# 使用新加坡时间 (UTC+8)，保证数据日期与用户本地日期一致
SGT = timezone(timedelta(hours=8))


# ─── 数据迁移 ──────────────────────────────────────────────────────────────────

def migrate_csv_to_json():
    """将旧 CSV 数据一次性迁移为 JSON 格式。"""
    if not os.path.exists(CSV_FILE) or os.path.getsize(CSV_FILE) == 0:
        return {}

    print("📦 检测到旧 CSV 文件，正在迁移到 JSON 格式...")
    data = {}
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = row.get("title", "").strip()
            if not title:
                continue
            if title not in data:
                data[title] = {"year": row.get("year", ""), "history": {}}
            date = row.get("date", "")
            cites_str = row.get("citations", "0").strip()
            citations = int(cites_str) if cites_str.isdigit() else 0
            if date:
                data[title]["history"][date] = citations

    print(f"✅ 迁移完成：{len(data)} 篇论文")
    return data


# ─── 数据读写 ──────────────────────────────────────────────────────────────────

def load_data():
    """优先读取 JSON，不存在时从旧 CSV 迁移。"""
    if os.path.exists(JSON_FILE) and os.path.getsize(JSON_FILE) > 0:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return migrate_csv_to_json()


def save_data(data):
    """以紧凑 JSON 格式保存，节省磁盘和带宽。"""
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print(f"✅ 已保存 {len(data)} 篇论文 → {JSON_FILE}")


# ─── 爬取 ──────────────────────────────────────────────────────────────────────

def scrape(author_id):
    """使用 ScraperAPI 抓取 Google Scholar 数据并解析。"""
    if not SCRAPER_API_KEY:
        print("❌ SCRAPER_API_KEY 环境变量未设置")
        return None

    print("🔄 开始抓取...")
    target_url = (
        f"https://scholar.google.com/citations"
        f"?user={author_id}&hl=en&view_op=list_works&sortby=citation"
    )
    api_url = (
        f"http://api.scraperapi.com/?api_key={SCRAPER_API_KEY}"
        f"&url={urllib.parse.quote(target_url)}"
    )

    try:
        req = urllib.request.Request(api_url, headers={"User-Agent": "Mozilla/5.0"})
        print("  请求中（10-30 秒）...")
        resp = urllib.request.urlopen(req, timeout=120)
        html = resp.read().decode("utf-8", errors="ignore")
        print(f"  收到 {len(html)} bytes")
    except Exception as e:
        print(f"❌ 请求失败：{e}")
        return None

    # 解析 HTML
    titles = re.findall(r'class="gsc_a_at[^"]*"[^>]*>([^<]+)</a>', html)
    cites  = re.findall(r'class="gsc_a_ac[^"]*"[^>]*>([^<]+)</a>', html)
    years  = re.findall(r'class="gsc_a_h[^"]*"[^>]*>([^<]+)</span>', html)

    print(f"  解析到 {len(titles)} 篇论文")

    papers = []
    for i, title in enumerate(titles):
        c = int(cites[i]) if i < len(cites) and cites[i].isdigit() else 0
        y = years[i] if i < len(years) else ""
        papers.append({"title": title.strip(), "citations": c, "year": y})

    return papers


# ─── 主流程 ────────────────────────────────────────────────────────────────────

def main():
    # 使用新加坡时间作为日期标签，与用户所在时区一致
    today = datetime.now(SGT).strftime("%Y-%m-%d")
    author_id = get_scholar_id()
    print(f"📅 {today} (SGT) | Author: {author_id}")

    # 加载现有数据（含可能的 CSV 迁移）
    data = load_data()

    # 若已有论文且今天数据已存在，则跳过爬取
    if data and any(today in v["history"] for v in data.values()):
        print(f"✓ {today} 数据已存在，跳过爬取")
        return

    # 爬取
    papers = scrape(author_id)
    if not papers:
        print("⚠️ 抓取失败，退出")
        sys.exit(0)

    # 合并到数据字典
    for p in papers:
        title = p["title"]
        if title not in data:
            data[title] = {"year": p["year"], "history": {}}
        if not data[title].get("year") and p["year"]:
            data[title]["year"] = p["year"]
        data[title]["history"][today] = p["citations"]

    save_data(data)


if __name__ == "__main__":
    main()
