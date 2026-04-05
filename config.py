# ============================================
# 配置 - 只需要修改下面这一行！
# ============================================
# 你的 Google Scholar 主页链接
# 格式: https://scholar.google.com/citations?user=XXXXX
# 或者只需要填 XXXXX 部分
SCHOLAR_URL = "https://scholar.google.com/citations?user=LYNKm_8AAAAJ"
# ============================================

# 从 URL 提取 Scholar ID
def get_scholar_id():
    url = SCHOLAR_URL.strip()
    if 'user=' in url:
        return url.split('user=')[1].split('&')[0]
    return url.strip()
