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
import time
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

PAGE_SIZE = 100          # Google Scholar 单页最多 100 篇
MAX_PAGES = 10           # 安全上限，最多抓 1000 篇


def _fetch_page(author_id, cstart):
    """抓取 Google Scholar 作者页的一页（从 cstart 开始）。"""
    target_url = (
        f"https://scholar.google.com/citations"
        f"?user={author_id}&hl=en&view_op=list_works&sortby=citation"
        f"&cstart={cstart}&pagesize={PAGE_SIZE}"
    )
    api_url = (
        f"http://api.scraperapi.com/?api_key={SCRAPER_API_KEY}"
        f"&url={urllib.parse.quote(target_url)}"
    )
    req = urllib.request.Request(api_url, headers={"User-Agent": "Mozilla/5.0"})
    resp = urllib.request.urlopen(req, timeout=120)
    return resp.read().decode("utf-8", errors="ignore")


def scrape(author_id):
    """使用 ScraperAPI 抓取 Google Scholar 数据并解析（自动翻页，抓取全部论文）。"""
    if not SCRAPER_API_KEY:
        print("❌ SCRAPER_API_KEY 环境变量未设置")
        return None

    print("🔄 开始抓取（自动翻页）...")
    papers = []
    seen_titles = set()

    for page in range(MAX_PAGES):
        cstart = page * PAGE_SIZE
        try:
            print(f"  第 {page + 1} 页（cstart={cstart}）请求中...")
            html = _fetch_page(author_id, cstart)
            print(f"    收到 {len(html)} bytes")
        except Exception as e:
            print(f"❌ 第 {page + 1} 页请求失败：{e}")
            break  # 已抓到的部分仍会返回

        titles = re.findall(r'class="gsc_a_at[^"]*"[^>]*>([^<]+)</a>', html)
        cites  = re.findall(r'class="gsc_a_ac[^"]*"[^>]*>([^<]+)</a>', html)
        years  = re.findall(r'class="gsc_a_h[^"]*"[^>]*>([^<]+)</span>', html)

        if not titles:
            print("    本页无论文，停止翻页")
            break

        page_new = 0
        for i, title in enumerate(titles):
            t = title.strip()
            if t in seen_titles:      # 防止重复页导致重复计数
                continue
            seen_titles.add(t)
            c = int(cites[i]) if i < len(cites) and cites[i].isdigit() else 0
            y = years[i] if i < len(years) else ""
            papers.append({"title": t, "citations": c, "year": y})
            page_new += 1

        print(f"    本页新增 {page_new} 篇（累计 {len(papers)} 篇）")

        if len(titles) < PAGE_SIZE:   # 不满一页 = 已到最后一页
            break

    print(f"  共解析到 {len(papers)} 篇论文")
    return papers if papers else None


# ─── 元数据补充（Semantic Scholar）──────────────────────────────────────────────

S2_URL = "https://api.semanticscholar.org/graph/v1/paper/search/match"
S2_FIELDS = "title,year,venue,authors,tldr,abstract,externalIds,openAccessPdf,url"
S2_RETRY_DAYS = 14   # 未匹配成功的论文，多久后再重试


def _days_since(date_str, today):
    try:
        d0 = datetime.strptime(date_str, "%Y-%m-%d")
        d1 = datetime.strptime(today, "%Y-%m-%d")
        return (d1 - d0).days
    except Exception:
        return 9999


def _s2_match(title):
    """在 Semantic Scholar 上按标题匹配论文，返回精简元数据；失败返回 None。"""
    q = urllib.parse.urlencode({"query": title, "fields": S2_FIELDS})
    req = urllib.request.Request(
        f"{S2_URL}?{q}", headers={"User-Agent": "citation-tracker (github.com/marsggbo)"}
    )
    resp = urllib.request.urlopen(req, timeout=30)
    j = json.loads(resp.read().decode("utf-8"))
    arr = j.get("data") or []
    if not arr:
        return None
    p = arr[0]
    ext = p.get("externalIds") or {}
    tldr = p.get("tldr") or {}
    return {
        "authors": [a.get("name", "") for a in (p.get("authors") or [])],
        "venue": p.get("venue") or "",
        "tldr": tldr.get("text", "") if tldr else "",
        "abstract": p.get("abstract") or "",
        "arxiv": ext.get("ArXiv", ""),
        "doi": ext.get("DOI", ""),
        "s2url": p.get("url", ""),
        "pdf": (p.get("openAccessPdf") or {}).get("url", ""),
    }


def enrich_metadata(data, today):
    """为缺少元数据（作者/摘要/链接）的论文补充 Semantic Scholar 信息。
    已成功补充的论文会被缓存，不会每天重复请求。"""
    todo = []
    for title, v in data.items():
        m = v.get("meta")
        if m is None:
            todo.append(title)
        elif not m.get("tldr") and not m.get("abstract"):
            if _days_since(m.get("_tried", ""), today) >= S2_RETRY_DAYS:
                todo.append(title)

    if not todo:
        print("✓ 论文元数据已是最新")
        return

    print(f"🔎 补充元数据：{len(todo)} 篇（来源 Semantic Scholar）...")
    for title in todo:
        meta = None
        try:
            meta = _s2_match(title)
        except Exception as e:
            print(f"   ⚠️ 查询失败 {title[:42]}… → {e}")
        if meta:
            data[title]["meta"] = meta
            print(f"   ✓ {title[:42]}…")
        else:
            data[title].setdefault("meta", {})["_tried"] = today
            print(f"   – 未匹配 {title[:42]}…")
        time.sleep(1.1)   # 尊重 S2 未授权速率限制


# 同一论文的不同版本（如预印本 → 正式版），按归一化标题映射到统一条目
TITLE_ALIASES = {
    "benchmarking deep learning models and automated model design for covid 19 detection with chest ct scans":
        "automated model design and benchmarking of deep learning models for covid 19 detection with chest ct scans",
}


def _norm_title(t):
    """标题归一化：Google Scholar 会不定期改变大小写/标点，需按归一化后匹配以免重复建条目。"""
    n = re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()
    return TITLE_ALIASES.get(n, n)


def detect_new_papers(data, papers, today):
    """对比历史数据，找出本次首次出现的新论文并打印。"""
    existing = {_norm_title(k) for k in data}
    new_titles = [p["title"] for p in papers if _norm_title(p["title"]) not in existing]
    if new_titles:
        print(f"🆕 发现 {len(new_titles)} 篇新论文（{today}）:")
        for t in new_titles:
            print(f"   + {t}")
    else:
        print("✓ 本次无新论文")
    return new_titles


# ─── 主流程 ────────────────────────────────────────────────────────────────────

def main():
    # 使用新加坡时间作为日期标签，与用户所在时区一致
    today = datetime.now(SGT).strftime("%Y-%m-%d")
    author_id = get_scholar_id()
    print(f"📅 {today} (SGT) | Author: {author_id}")

    # 加载现有数据（含可能的 CSV 迁移）
    data = load_data()

    # 若已有论文且今天数据已存在，则跳过爬取（但仍补充元数据 + 保存）
    if data and any(today in v["history"] for v in data.values()):
        print(f"✓ {today} 引用数据已存在，跳过爬取")
        enrich_metadata(data, today)
        save_data(data)
        return

    # 爬取
    papers = scrape(author_id)
    if not papers:
        print("⚠️ 抓取失败；仍尝试补充元数据后退出")
        enrich_metadata(data, today)
        save_data(data)
        sys.exit(0)

    # 检测新增论文（在合并前对比历史）
    detect_new_papers(data, papers, today)

    # 合并到数据字典（按归一化标题匹配已有条目，标题写法变化时沿用旧条目）
    norm_map = {_norm_title(k): k for k in data}
    for p in papers:
        title = norm_map.get(_norm_title(p["title"]), p["title"])
        if title not in data:
            # 首次出现的论文：记录 first_seen，供前端标记 NEW
            data[title] = {"year": p["year"], "first_seen": today, "history": {}}
            norm_map[_norm_title(title)] = title
        if not data[title].get("first_seen"):
            # 为历史遗留数据补齐 first_seen（取最早的历史日期）
            hist_dates = sorted(data[title].get("history", {}).keys())
            data[title]["first_seen"] = hist_dates[0] if hist_dates else today
        if not data[title].get("year") and p["year"]:
            data[title]["year"] = p["year"]
        # 多条抓取结果映射到同一条目时（如预印本+正式版），取较大引用数
        prev = data[title]["history"].get(today, 0)
        data[title]["history"][today] = max(prev, p["citations"])

    # 补充作者/摘要/链接等元数据（新论文优先，已缓存的跳过）
    enrich_metadata(data, today)

    save_data(data)


if __name__ == "__main__":
    main()
